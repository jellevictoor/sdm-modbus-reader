"""
Adapter - Modbus implementation of IMeterReader
"""
from pymodbus.client import ModbusSerialClient
import struct
import time
from typing import Optional, Dict

from sdm_modbus_reader.ports.meter_reader import IMeterReader
from sdm_modbus_reader.domain.models import MeterType


# Register maps for different meter types
SDM120_REGISTERS = {
    "Voltage": 0x0000,
    "Current": 0x0006,
    "Power": 0x000C,
    "ApparentPower": 0x0012,
    "ReactivePower": 0x0018,
    "Cosphi": 0x001E,
    "PhaseAngle": 0x0024,
    "Frequency": 0x0046,
    "Import": 0x0156,
    "Export": 0x0160,
    "ReactiveImport": 0x0158,
    "ReactiveExport": 0x0162,
    "Sum": 0x0156,
    "ReactiveSum": 0x0158,
}

SDM630_REGISTERS = {
    "Voltage/L1": 0x0000,
    "Voltage/L2": 0x0002,
    "Voltage/L3": 0x0004,
    "Voltage": 0x002A,
    "Current/L1": 0x0006,
    "Current/L2": 0x0008,
    "Current/L3": 0x000A,
    "Current": 0x0030,
    "Power/L1": 0x000C,
    "Power/L2": 0x000E,
    "Power/L3": 0x0010,
    "Power": 0x0034,
    "ApparentPower/L1": 0x0012,
    "ApparentPower/L2": 0x0014,
    "ApparentPower/L3": 0x0016,
    "ApparentPower": 0x0038,
    "ReactivePower/L1": 0x0018,
    "ReactivePower/L2": 0x001A,
    "ReactivePower/L3": 0x001C,
    "ReactivePower": 0x003C,
    "Cosphi/L1": 0x001E,
    "Cosphi/L2": 0x0020,
    "Cosphi/L3": 0x0022,
    "Cosphi": 0x003E,
    "PhaseAngle/L1": 0x0024,
    "PhaseAngle/L2": 0x0026,
    "PhaseAngle/L3": 0x0028,
    "Frequency": 0x0046,
    "Import": 0x0156,
    "Export": 0x0160,
    "ReactiveImport": 0x0158,
    "ReactiveExport": 0x0162,
    "Sum": 0x0156,
    "ReactiveSum": 0x0158,
    "Voltage/L1-L2": 0x00C8,
    "Voltage/L2-L3": 0x00CA,
    "Voltage/L3-L1": 0x00CC,
    "Current/N": 0x00E0,
    "THD/VoltageL1": 0x00EA,
    "THD/VoltageL2": 0x00EC,
    "THD/VoltageL3": 0x00EE,
    "THD/CurrentL1": 0x00F0,
    "THD/CurrentL2": 0x00F2,
    "THD/CurrentL3": 0x00F4,
    "THD/VoltageAvg": 0x00F8,
    "THD/CurrentAvg": 0x00FA,
}


class ModbusMeterReader(IMeterReader):
    """Reads data from SDM meters via Modbus RTU"""

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        parity: str = "N",
        stopbits: int = 1,
        bytesize: int = 8,
        timeout: int = 1
    ):
        self.client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize,
            timeout=timeout
        )

    def connect(self) -> bool:
        """Connect to the Modbus serial port"""
        return self.client.connect()

    def disconnect(self):
        """Close the Modbus connection"""
        self.client.close()

    def _read_float32(self, device_id: int, register: int) -> Optional[float]:
        """Read IEEE754 float32 from SDM meter"""
        try:
            result = self.client.read_input_registers(
                address=register,
                count=2,
                device_id=device_id
            )

            if result.isError():
                return None

            # Convert to float32 (big-endian, high word first)
            high_word = result.registers[0]
            low_word = result.registers[1]

            byte_array = struct.pack('>HH', high_word, low_word)
            value = struct.unpack('>f', byte_array)[0]

            return value

        except Exception:
            return None

    def read_meter(self, device_id: int, meter_type: MeterType) -> Optional[Dict[str, float]]:
        """Read all available data from a meter"""
        # Select register map based on meter type
        if meter_type == MeterType.SDM630:
            registers = SDM630_REGISTERS
        else:  # SDM120, SDM220, SDM230
            registers = SDM120_REGISTERS

        data = {}
        success_count = 0

        for name, register in registers.items():
            value = self._read_float32(device_id, register)
            if value is not None:
                data[name] = value
                success_count += 1
            # Small delay between register reads for stability
            time.sleep(0.05)

        return data if success_count > 0 else None