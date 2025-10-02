#!/usr/bin/env python3
"""
SDM Meter Reader - Full Metrics
Reads all available data from SDM120/SDM220/SDM230/SDM630 meters
"""
from pymodbus.client import ModbusSerialClient
import paho.mqtt.client as mqtt
import struct
import time
import re
import typer
import threading
import uvicorn
from typing import Dict, Optional, List
from typing_extensions import Annotated
from .data_store import meter_store

app = typer.Typer(help="SDM Modbus Meter Reader - Monitor SDM120/SDM630 energy meters")


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def parse_meter_spec(spec: str) -> Dict:
    """Parse meter specification in format: type:address[:display_name]"""
    parts = spec.split(':', 2)
    if len(parts) < 2:
        raise typer.BadParameter(f"Invalid meter spec '{spec}'. Expected format: type:address[:display_name]")

    meter_type = parts[0].upper()
    address_str = parts[1]
    display_name = parts[2] if len(parts) == 3 else None

    if meter_type not in ['SDM120', 'SDM220', 'SDM230', 'SDM630']:
        raise typer.BadParameter(f"Invalid meter type '{meter_type}'. Must be one of: SDM120, SDM220, SDM230, SDM630")

    try:
        address = int(address_str)
        if not (1 <= address <= 247):
            raise typer.BadParameter(f"Address must be between 1 and 247, got {address}")
    except ValueError as e:
        raise typer.BadParameter(f"Invalid address '{address_str}': {e}")

    # If no display name provided, use meter_type + address
    if display_name is None:
        display_name = f"{meter_type} {address}"

    return {
        "type": meter_type,
        "address": address,
        "display_name": display_name,
        "slug": slugify(display_name)
    }

# Complete register maps
SDM120_REGISTERS = {
    # Basic measurements
    "Voltage": 0x0000,
    "Current": 0x0006,
    "Power": 0x000C,
    "ApparentPower": 0x0012,
    "ReactivePower": 0x0018,
    "Cosphi": 0x001E,
    "PhaseAngle": 0x0024,
    "Frequency": 0x0046,

    # Energy
    "Import": 0x0156,
    "Export": 0x0160,
    "ReactiveImport": 0x0158,
    "ReactiveExport": 0x0162,

    # Totals
    "Sum": 0x0156,  # Total kWh
    "ReactiveSum": 0x0158,  # Total kvarh
}

SDM630_REGISTERS = {
    # Phase voltages
    "Voltage/L1": 0x0000,
    "Voltage/L2": 0x0002,
    "Voltage/L3": 0x0004,
    "Voltage": 0x002A,  # Average

    # Phase currents
    "Current/L1": 0x0006,
    "Current/L2": 0x0008,
    "Current/L3": 0x000A,
    "Current": 0x0030,  # Average or sum

    # Phase power
    "Power/L1": 0x000C,
    "Power/L2": 0x000E,
    "Power/L3": 0x0010,
    "Power": 0x0034,  # Total system power

    # Phase apparent power
    "ApparentPower/L1": 0x0012,
    "ApparentPower/L2": 0x0014,
    "ApparentPower/L3": 0x0016,
    "ApparentPower": 0x0038,  # Total

    # Phase reactive power
    "ReactivePower/L1": 0x0018,
    "ReactivePower/L2": 0x001A,
    "ReactivePower/L3": 0x001C,
    "ReactivePower": 0x003C,  # Total

    # Phase power factor
    "Cosphi/L1": 0x001E,
    "Cosphi/L2": 0x0020,
    "Cosphi/L3": 0x0022,
    "Cosphi": 0x003E,  # Total

    # Phase angles
    "PhaseAngle/L1": 0x0024,
    "PhaseAngle/L2": 0x0026,
    "PhaseAngle/L3": 0x0028,

    # Frequency
    "Frequency": 0x0046,

    # Energy counters
    "Import": 0x0156,
    "Export": 0x0160,
    "ReactiveImport": 0x0158,
    "ReactiveExport": 0x0162,

    # Totals
    "Sum": 0x0156,
    "ReactiveSum": 0x0158,

    # Line to line voltages
    "Voltage/L1-L2": 0x00C8,
    "Voltage/L2-L3": 0x00CA,
    "Voltage/L3-L1": 0x00CC,

    # Neutral current
    "Current/N": 0x00E0,

    # THD (Total Harmonic Distortion)
    "THD/VoltageL1": 0x00EA,
    "THD/VoltageL2": 0x00EC,
    "THD/VoltageL3": 0x00EE,
    "THD/CurrentL1": 0x00F0,
    "THD/CurrentL2": 0x00F2,
    "THD/CurrentL3": 0x00F4,

    # Average line to neutral THD
    "THD/VoltageAvg": 0x00F8,
    "THD/CurrentAvg": 0x00FA,
}

def read_float32(client, device_id: int, register: int) -> Optional[float]:
    """
    Read IEEE754 float32 from SDM meter
    SDM meters use input registers (function code 0x04)
    """
    try:
        result = client.read_input_registers(
            address=register,
            count=2,
            device_id=device_id  # Changed to 'device_id' for pymodbus 3.11.x
        )

        if result.isError():
            return None

        # Convert to float32 (big-endian, high word first)
        high_word = result.registers[0]
        low_word = result.registers[1]

        byte_array = struct.pack('>HH', high_word, low_word)
        value = struct.unpack('>f', byte_array)[0]

        return value

    except Exception as e:
        # Silently fail for optional registers
        return None

def read_meter(client, device_id: int, meter_type: str) -> Optional[Dict]:
    """Read all available data from a meter"""

    # Select register map based on meter type
    if meter_type == "SDM630":
        registers = SDM630_REGISTERS
    else:  # SDM120, SDM220, SDM230
        registers = SDM120_REGISTERS

    data = {}
    success_count = 0

    for name, register in registers.items():
        value = read_float32(client, device_id, register)
        if value is not None:
            data[name] = value
            success_count += 1
        # Small delay between register reads for stability
        time.sleep(0.05)

    return data if success_count > 0 else None

def publish_data(mqtt_client, meter_slug: str, data: Dict, topic_prefix: str):
    """Publish meter data to MQTT in mbmd-compatible format"""
    base_topic = f"{topic_prefix}/{meter_slug}"

    for key, value in data.items():
        topic = f"{base_topic}/{key}"
        # Format based on magnitude
        if abs(value) >= 100:
            formatted = f"{value:.2f}"
        elif abs(value) >= 1:
            formatted = f"{value:.3f}"
        else:
            formatted = f"{value:.6f}"

        mqtt_client.publish(topic, formatted, retain=True)

def display_meter_summary(meter_id: int, meter_type: str, data: Dict):
    """Display a summary of important metrics"""
    if meter_type == "SDM630":
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
    # Validate parity
    if parity not in ['N', 'E', 'O']:
        typer.echo("Error: Parity must be N, E, or O", err=True)
        raise typer.Exit(1)

    # Validate stopbits and bytesize
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
        meters[meter['address']] = meter

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
        typer.echo(f"  Address {address}: {meter['type']:7s} → {meter['display_name']} (slug: {meter['slug']})")
    typer.echo("=" * 70)
    typer.echo()

    # Connect to MQTT
    mqtt_client = mqtt.Client(client_id="sdm_reader")
    if mqtt_user and mqtt_password:
        mqtt_client.username_pw_set(mqtt_user, mqtt_password)

    try:
        mqtt_client.connect(mqtt_broker, mqtt_port, 60)
        mqtt_client.loop_start()
        typer.echo("✓ Connected to MQTT broker")
    except Exception as e:
        typer.echo(f"✗ Failed to connect to MQTT: {e}")
        typer.echo("  Continuing without MQTT...")
        mqtt_client = None

    # Connect to Modbus Serial
    serial_client = ModbusSerialClient(
        port=serial_port,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize,
        timeout=1
    )

    try:
        if not serial_client.connect():
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
                meter_type = meter["type"]
                display_name = meter["display_name"]
                slug = meter["slug"]

                typer.echo(f"Reading {meter_type} @ {address} ({display_name})... ", nl=False)

                data = read_meter(serial_client, address, meter_type)

                if data:
                    success_count += 1
                    total_registers += len(data)
                    typer.echo(f"✓ {len(data)} registers")

                    # Store data for API access
                    meter_store.update_meter(address, meter_type, display_name, data)

                    # Display summary
                    display_meter_summary(address, meter_type, data)

                    # Publish to MQTT
                    if mqtt_client:
                        publish_data(mqtt_client, slug, data, mqtt_topic_prefix)
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
        serial_client.close()
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        typer.echo("Disconnected")


if __name__ == "__main__":
    app()