#!/usr/bin/env python3
"""
SDM Meter Reader - Full Metrics
Reads all available data from SDM120/SDM220/SDM230/SDM630 meters
"""
from pymodbus.client import ModbusSerialClient
import paho.mqtt.client as mqtt
import struct
import time
from typing import Dict, Optional

# Serial Configuration
SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 9600
PARITY = 'N'
STOPBITS = 1
BYTESIZE = 8

# MQTT Configuration
MQTT_BROKER = "192.168.1.5"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "klskmp/metering/sdm"

# Poll interval in seconds
POLL_INTERVAL = 10

# Meter Configuration
METERS = {
    100: {"type": "SDM630", "name": "sdm630_main"},
    101: {"type": "SDM120", "name": "sdm120_101"},
    102: {"type": "SDM120", "name": "sdm120_102"},
    103: {"type": "SDM120", "name": "sdm120_103"},
    104: {"type": "SDM120", "name": "sdm120_104"},
    105: {"type": "SDM120", "name": "sdm120_105"},
    106: {"type": "SDM120", "name": "sdm120_106"},
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
            slave=device_id
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

def publish_data(mqtt_client, meter_id: int, meter_name: str, data: Dict):
    """Publish meter data to MQTT in mbmd-compatible format"""
    base_topic = f"{MQTT_TOPIC_PREFIX}/{meter_name}"

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

def main():
    print("=" * 70)
    print("SDM Meter Reader - Full Metrics Edition")
    print("=" * 70)
    print(f"Serial Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUDRATE}")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print()
    print("Configured Meters:")
    for meter_id, config in METERS.items():
        print(f"  ID {meter_id}: {config['type']:7s} → {config['name']}")
    print("=" * 70)
    print()

    # Connect to MQTT
    mqtt_client = mqtt.Client(client_id="sdm_reader")
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("✓ Connected to MQTT broker")
    except Exception as e:
        print(f"✗ Failed to connect to MQTT: {e}")
        print("  Continuing without MQTT...")
        mqtt_client = None

    # Connect to Modbus Serial
    serial_client = ModbusSerialClient(
        port=SERIAL_PORT,
        baudrate=BAUDRATE,
        parity=PARITY,
        stopbits=STOPBITS,
        bytesize=BYTESIZE,
        timeout=1
    )

    try:
        if not serial_client.connect():
            print("✗ Failed to open serial port")
            return
        print(f"✓ Opened serial port {SERIAL_PORT}\n")

        cycle = 0
        while True:
            cycle += 1
            cycle_start = time.time()
            print(f"[Cycle {cycle}] {time.strftime('%H:%M:%S')}")
            print("-" * 70)

            success_count = 0
            error_count = 0
            total_registers = 0

            for meter_id, config in METERS.items():
                meter_type = config["type"]
                meter_name = config["name"]

                print(f"Reading {meter_type} (ID {meter_id})... ", end="", flush=True)

                data = read_meter(serial_client, meter_id, meter_type)

                if data:
                    success_count += 1
                    total_registers += len(data)
                    print(f"✓ {len(data)} registers")

                    # Display summary
                    display_meter_summary(meter_id, meter_type, data)

                    # Publish to MQTT
                    if mqtt_client:
                        publish_data(mqtt_client, meter_id, meter_name, data)
                else:
                    error_count += 1
                    print(f"✗ TIMEOUT/ERROR")

                # Delay between meters
                time.sleep(0.5)

            cycle_time = time.time() - cycle_start
            print("-" * 70)
            print(f"Summary: {success_count}/{len(METERS)} meters OK, "
                  f"{total_registers} registers read, {cycle_time:.1f}s")
            print()

            # Wait for next cycle
            remaining = POLL_INTERVAL - cycle_time
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        print("\n\nStopping...")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        serial_client.close()
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    main()