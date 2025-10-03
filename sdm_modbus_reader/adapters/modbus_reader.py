"""
Adapter - Modbus implementation of IMeterReader
"""
from pymodbus.client import ModbusSerialClient
import struct
import time
from typing import Optional

from sdm_modbus_reader.ports.meter_reader import MeterReader
from sdm_modbus_reader.domain.models import MeterType
from sdm_modbus_reader.domain.register_maps import SDM120_REGISTERS, SDM630_REGISTERS
from sdm_modbus_reader.domain.meter_data import (
    SDM120Data,
    SDM630Data,
    MeterData,
    EnergyTotals,
    PhaseData,
)


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

    def read_meter(self, device_id: int, meter_type: MeterType) -> Optional[MeterData]:
        """Read all available data from a meter"""
        # Select register map based on meter type
        if meter_type == MeterType.SDM630:
            return self._read_sdm630(device_id)
        else:  # SDM120, SDM220, SDM230
            return self._read_sdm120(device_id)

    def _read_sdm120(self, device_id: int) -> Optional[SDM120Data]:
        """Read SDM120 (single-phase) meter data"""
        data = {}
        success_count = 0

        for name, register in SDM120_REGISTERS.items():
            value = self._read_float32(device_id, register)
            if value is not None:
                data[name] = value
                success_count += 1
            time.sleep(0.05)

        if success_count == 0:
            return None

        # Build energy totals if any energy data available
        energy = None
        if any(key in data for key in ['Import', 'Export', 'ReactiveImport', 'ReactiveExport', 'Sum', 'ReactiveSum']):
            energy = EnergyTotals(
                import_active=data.get('Import'),
                export_active=data.get('Export'),
                import_reactive=data.get('ReactiveImport'),
                export_reactive=data.get('ReactiveExport'),
                total_active=data.get('Sum'),
                total_reactive=data.get('ReactiveSum'),
            )

        return SDM120Data(
            voltage=data.get('Voltage'),
            current=data.get('Current'),
            power=data.get('Power'),
            apparent_power=data.get('ApparentPower'),
            reactive_power=data.get('ReactivePower'),
            power_factor=data.get('Cosphi'),
            phase_angle=data.get('PhaseAngle'),
            frequency=data.get('Frequency'),
            energy=energy,
        )

    def _read_sdm630(self, device_id: int) -> Optional[SDM630Data]:
        """Read SDM630 (three-phase) meter data"""
        data = {}
        success_count = 0

        for name, register in SDM630_REGISTERS.items():
            value = self._read_float32(device_id, register)
            if value is not None:
                data[name] = value
                success_count += 1
            time.sleep(0.05)

        if success_count == 0:
            return None

        # Build phase data
        phase_l1 = None
        if any(key in data for key in ['Voltage/L1', 'Current/L1', 'Power/L1']):
            phase_l1 = PhaseData(
                voltage=data.get('Voltage/L1'),
                current=data.get('Current/L1'),
                power=data.get('Power/L1'),
                apparent_power=data.get('ApparentPower/L1'),
                reactive_power=data.get('ReactivePower/L1'),
                power_factor=data.get('Cosphi/L1'),
                phase_angle=data.get('PhaseAngle/L1'),
                thd_voltage=data.get('THD/VoltageL1'),
                thd_current=data.get('THD/CurrentL1'),
            )

        phase_l2 = None
        if any(key in data for key in ['Voltage/L2', 'Current/L2', 'Power/L2']):
            phase_l2 = PhaseData(
                voltage=data.get('Voltage/L2'),
                current=data.get('Current/L2'),
                power=data.get('Power/L2'),
                apparent_power=data.get('ApparentPower/L2'),
                reactive_power=data.get('ReactivePower/L2'),
                power_factor=data.get('Cosphi/L2'),
                phase_angle=data.get('PhaseAngle/L2'),
                thd_voltage=data.get('THD/VoltageL2'),
                thd_current=data.get('THD/CurrentL2'),
            )

        phase_l3 = None
        if any(key in data for key in ['Voltage/L3', 'Current/L3', 'Power/L3']):
            phase_l3 = PhaseData(
                voltage=data.get('Voltage/L3'),
                current=data.get('Current/L3'),
                power=data.get('Power/L3'),
                apparent_power=data.get('ApparentPower/L3'),
                reactive_power=data.get('ReactivePower/L3'),
                power_factor=data.get('Cosphi/L3'),
                phase_angle=data.get('PhaseAngle/L3'),
                thd_voltage=data.get('THD/VoltageL3'),
                thd_current=data.get('THD/CurrentL3'),
            )

        # Build energy totals
        energy = None
        if any(key in data for key in ['Import', 'Export', 'ReactiveImport', 'ReactiveExport', 'Sum', 'ReactiveSum']):
            energy = EnergyTotals(
                import_active=data.get('Import'),
                export_active=data.get('Export'),
                import_reactive=data.get('ReactiveImport'),
                export_reactive=data.get('ReactiveExport'),
                total_active=data.get('Sum'),
                total_reactive=data.get('ReactiveSum'),
            )

        return SDM630Data(
            phase_l1=phase_l1,
            phase_l2=phase_l2,
            phase_l3=phase_l3,
            voltage_average=data.get('Voltage'),
            current_total=data.get('Current'),
            power_total=data.get('Power'),
            apparent_power_total=data.get('ApparentPower'),
            reactive_power_total=data.get('ReactivePower'),
            power_factor_total=data.get('Cosphi'),
            frequency=data.get('Frequency'),
            voltage_l1_l2=data.get('Voltage/L1-L2'),
            voltage_l2_l3=data.get('Voltage/L2-L3'),
            voltage_l3_l1=data.get('Voltage/L3-L1'),
            current_neutral=data.get('Current/N'),
            thd_voltage_avg=data.get('THD/VoltageAvg'),
            thd_current_avg=data.get('THD/CurrentAvg'),
            energy=energy,
        )