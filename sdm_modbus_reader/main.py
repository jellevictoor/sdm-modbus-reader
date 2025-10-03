#!/usr/bin/env python3
"""
SDM Modbus Reader - Main CLI entry point
"""
import re
import time
import typer
import threading
import uvicorn
from typing import List, Optional
from typing_extensions import Annotated

from sdm_modbus_reader.domain.models import MeterConfig, MeterType
from sdm_modbus_reader.bootstrap import (
    bootstrap_application,
    SerialConfig,
    MqttConfig,
)

app = typer.Typer(help="SDM Modbus Meter Reader - Monitor SDM120/SDM630 energy meters")


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def parse_meter_spec(spec: str) -> MeterConfig:
    """Parse meter specification in format: type:address[:display_name]"""
    parts = spec.split(':', 2)
    if len(parts) < 2:
        raise typer.BadParameter(f"Invalid meter spec '{spec}'. Expected format: type:address[:display_name]")

    meter_type_str = parts[0].upper()
    address_str = parts[1]
    display_name = parts[2] if len(parts) == 3 else None

    if meter_type_str not in ['SDM120', 'SDM630']:
        raise typer.BadParameter(f"Invalid meter type '{meter_type_str}'. Must be one of: SDM120, SDM220, SDM230, SDM630")

    try:
        address = int(address_str)
        if not (1 <= address <= 247):
            raise typer.BadParameter(f"Address must be between 1 and 247, got {address}")
    except ValueError as e:
        raise typer.BadParameter(f"Invalid address '{address_str}': {e}")

    # If no display name provided, use meter_type + address
    if display_name is None:
        display_name = f"{meter_type_str} {address}"

    meter_type = MeterType[meter_type_str]

    return MeterConfig(
        meter_type=meter_type,
        address=address,
        display_name=display_name,
        slug=slugify(display_name)
    )


def display_meter_summary(meter_type: MeterType, data: dict):
    """Display a summary of important metrics"""
    if meter_type == MeterType.SDM630:
        # 3-phase summary
        print(f"  L1: V={data.get('Voltage/L1', 0):.1f}V, I={data.get('Current/L1', 0):.2f}A, P={data.get('Power/L1', 0):.0f}W")
        print(f"  L2: V={data.get('Voltage/L2', 0):.1f}V, I={data.get('Current/L2', 0):.2f}A, P={data.get('Power/L2', 0):.0f}W")
        print(f"  L3: V={data.get('Voltage/L3', 0):.1f}V, I={data.get('Current/L3', 0):.2f}A, P={data.get('Power/L3', 0):.0f}W")
        print(f"  Total: P={data.get('Power', 0):.0f}W, PF={data.get('Cosphi', 0):.3f}, Energy={data.get('Sum', 0):.1f}kWh")
    else:
        # Single phase summary
        voltage = data.get('Voltage', 0)
        current = data.get('Current', 0)
        power = data.get('Power', 0)
        pf = data.get('Cosphi', 0)
        energy = data.get('Sum', 0)
        print(f"  V={voltage:.1f}V, I={current:.2f}A, P={power:.0f}W, PF={pf:.3f}, Energy={energy:.1f}kWh")


@app.command()
def main(
    devices: Annotated[List[str], typer.Option(
        "--device", "-d",
        help="Meter specification (TYPE:ADDRESS[:NAME], e.g., SDM120:101 or SDM120:101:Kitchen)",
        metavar="TYPE:ADDR[:NAME]"
    )],
    # Serial configuration
    serial_port: Annotated[str, typer.Option(help="Serial port device")] = "/dev/ttyUSB0",
    baudrate: Annotated[int, typer.Option(help="Serial baudrate")] = 9600,
    parity: Annotated[str, typer.Option(help="Serial parity (N/E/O)")] = "N",
    stopbits: Annotated[int, typer.Option(help="Serial stop bits")] = 1,
    bytesize: Annotated[int, typer.Option(help="Serial byte size")] = 8,
    # MQTT configuration
    mqtt_broker: Annotated[str, typer.Option(help="MQTT broker hostname or IP")] = "localhost",
    mqtt_port: Annotated[int, typer.Option(help="MQTT broker port")] = 1883,
    mqtt_user: Annotated[Optional[str], typer.Option(help="MQTT username")] = None,
    mqtt_password: Annotated[Optional[str], typer.Option(help="MQTT password")] = None,
    mqtt_topic_prefix: Annotated[str, typer.Option(help="MQTT topic prefix")] = "home/energy/sdm",
    # Other options
    poll_interval: Annotated[int, typer.Option(help="Poll interval in seconds")] = 10,
    api_port: Annotated[int, typer.Option(help="Web API port")] = 8000,
):
    """
    SDM Modbus Meter Reader - Monitor SDM120/SDM630 energy meters.

    Examples:

        sdm-reader --device SDM120:101:Kitchen --device SDM630:100:"Main Panel"

        sdm-reader -d SDM120:101:Kitchen --mqtt-broker 192.168.1.5 --mqtt-user admin
    """
    # Validate parameters
    if parity not in ['N', 'E', 'O']:
        typer.echo("Error: Parity must be N, E, or O", err=True)
        raise typer.Exit(1)

    if stopbits not in [1, 2]:
        typer.echo("Error: Stopbits must be 1 or 2", err=True)
        raise typer.Exit(1)

    if bytesize not in [7, 8]:
        typer.echo("Error: Bytesize must be 7 or 8", err=True)
        raise typer.Exit(1)

    # Parse meter specifications
    meters = {}
    for spec in devices:
        meter = parse_meter_spec(spec)
        meters[meter.address] = meter

    # Bootstrap application - initialize all dependencies
    serial_config = SerialConfig(
        port=serial_port,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize
    )

    mqtt_config = None
    if mqtt_broker:
        mqtt_config = MqttConfig(
            broker=mqtt_broker,
            port=mqtt_port,
            username=mqtt_user,
            password=mqtt_password,
            topic_prefix=mqtt_topic_prefix
        )

    container = bootstrap_application(serial_config, mqtt_config)

    # Start API server in background thread
    def run_api():
        uvicorn.run(
            "sdm_modbus_reader.api:app",
            host="0.0.0.0",
            port=api_port,
            log_level="warning"
        )

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    typer.echo("=" * 70)
    typer.echo("SDM Meter Reader - Full Metrics Edition")
    typer.echo("=" * 70)
    typer.echo(f"Serial Port: {serial_port}")
    typer.echo(f"Baud Rate: {baudrate}")
    typer.echo(f"MQTT Broker: {mqtt_broker}:{mqtt_port}")
    if mqtt_user:
        typer.echo(f"MQTT User: {mqtt_user}")
    typer.echo(f"MQTT Topic Prefix: {mqtt_topic_prefix}")
    typer.echo(f"Poll Interval: {poll_interval}s")
    typer.echo(f"Web API: http://0.0.0.0:{api_port}")
    typer.echo()
    typer.echo("Configured Meters:")
    for address, meter in meters.items():
        typer.echo(f"  Address {address}: {meter.meter_type.value:7s} → {meter.display_name} (slug: {meter.slug})")
    typer.echo("=" * 70)
    typer.echo()

    # Connect to MQTT
    if container.message_publisher:
        if container.message_publisher.connect():
            typer.echo("✓ Connected to MQTT broker")
        else:
            typer.echo("✗ Failed to connect to MQTT")
            typer.echo("  Continuing without MQTT...")
            container.message_publisher = None

    try:
        if not container.meter_reader.connect():
            typer.echo("✗ Failed to open serial port", err=True)
            raise typer.Exit(1)
        typer.echo(f"✓ Opened serial port {serial_port}\n")

        cycle = 0
        while True:
            cycle += 1
            cycle_start = time.time()
            typer.echo(f"[Cycle {cycle}] {time.strftime('%H:%M:%S')}")
            typer.echo("-" * 70)

            success_count = 0
            error_count = 0
            total_registers = 0

            for address, meter in meters.items():
                typer.echo(f"Reading {meter.meter_type.value} @ {address} ({meter.display_name})... ", nl=False)

                reading = container.meter_service.read_and_store_meter(meter)

                if reading:
                    success_count += 1
                    data_dict = reading.data.to_dict()
                    total_registers += len(data_dict)
                    typer.echo(f"✓ {len(data_dict)} registers")

                    # Display summary
                    display_meter_summary(meter.meter_type, data_dict)
                else:
                    error_count += 1
                    typer.echo(f"✗ TIMEOUT/ERROR")

                # Delay between meters
                time.sleep(0.5)

            cycle_time = time.time() - cycle_start
            typer.echo("-" * 70)
            typer.echo(f"Summary: {success_count}/{len(meters)} meters OK, "
                  f"{total_registers} registers read, {cycle_time:.1f}s")
            typer.echo()

            # Wait for next cycle
            remaining = poll_interval - cycle_time
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        typer.echo("\n\nStopping...")
    except Exception as e:
        typer.echo(f"\n✗ Unexpected error: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)
    finally:
        container.meter_reader.disconnect()
        if container.message_publisher:
            container.message_publisher.disconnect()
        typer.echo("Disconnected")


if __name__ == "__main__":
    app()