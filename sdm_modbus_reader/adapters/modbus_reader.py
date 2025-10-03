"""
Adapter - Modbus implementation of IMeterReader
"""
from pymodbus.client import ModbusSerialClient
import struct
import time
from typing import Optional, Dict

from sdm_modbus_reader.ports.meter_reader import MeterReader
from sdm_modbus_reader.domain.models import MeterType
from sdm_modbus_reader.domain.register_maps import SDM120_REGISTERS, SDM630_REGISTERS


class ModbusMeterReader(MeterReader):
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