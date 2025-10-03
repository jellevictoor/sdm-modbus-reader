"""
Domain - Meter Data Models

Strongly-typed dataclasses representing meter readings with proper context.
Each meter type has its own dataclass with appropriate fields.
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict


@dataclass
class PhaseData:
    """Data for a single phase"""
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    apparent_power: Optional[float] = None
    reactive_power: Optional[float] = None
    power_factor: Optional[float] = None  # Cosphi
    phase_angle: Optional[float] = None
    thd_voltage: Optional[float] = None
    thd_current: Optional[float] = None


@dataclass
class EnergyTotals:
    """Energy accumulation totals"""
    import_active: Optional[float] = None  # kWh imported
    export_active: Optional[float] = None  # kWh exported
    import_reactive: Optional[float] = None  # kVArh imported
    export_reactive: Optional[float] = None  # kVArh exported
    total_active: Optional[float] = None  # Total kWh (sum)
    total_reactive: Optional[float] = None  # Total kVArh (sum)


@dataclass
class SDM120Data:
    """
    Single-phase meter data (SDM120/SDM220/SDM230)

    All measurements are instantaneous values except energy totals.
    """
    # Instantaneous measurements
    voltage: Optional[float] = None  # V
    current: Optional[float] = None  # A
    power: Optional[float] = None  # W (active power)
    apparent_power: Optional[float] = None  # VA
    reactive_power: Optional[float] = None  # VAR
    power_factor: Optional[float] = None  # Cosphi (dimensionless, -1 to 1)
    phase_angle: Optional[float] = None  # degrees
    frequency: Optional[float] = None  # Hz

    # Energy totals
    energy: Optional[EnergyTotals] = None

    def to_dict(self) -> Dict[str, float]:
        """
        Convert to flat dictionary for backward compatibility.
        Returns only non-None values with appropriate keys.
        """
        result = {}

        # Add instantaneous measurements
        if self.voltage is not None:
            result['Voltage'] = self.voltage
        if self.current is not None:
            result['Current'] = self.current
        if self.power is not None:
            result['Power'] = self.power
        if self.apparent_power is not None:
            result['ApparentPower'] = self.apparent_power
        if self.reactive_power is not None:
            result['ReactivePower'] = self.reactive_power
        if self.power_factor is not None:
            result['Cosphi'] = self.power_factor
        if self.phase_angle is not None:
            result['PhaseAngle'] = self.phase_angle
        if self.frequency is not None:
            result['Frequency'] = self.frequency

        # Add energy totals
        if self.energy:
            if self.energy.import_active is not None:
                result['Import'] = self.energy.import_active
            if self.energy.export_active is not None:
                result['Export'] = self.energy.export_active
            if self.energy.import_reactive is not None:
                result['ReactiveImport'] = self.energy.import_reactive
            if self.energy.export_reactive is not None:
                result['ReactiveExport'] = self.energy.export_reactive
            if self.energy.total_active is not None:
                result['Sum'] = self.energy.total_active
            if self.energy.total_reactive is not None:
                result['ReactiveSum'] = self.energy.total_reactive

        return result


@dataclass
class SDM630Data:
    """
    Three-phase meter data (SDM630)

    Includes per-phase measurements, averages/totals, and additional metrics.
    """
    # Per-phase measurements
    phase_l1: Optional[PhaseData] = None
    phase_l2: Optional[PhaseData] = None
    phase_l3: Optional[PhaseData] = None

    # System averages/totals
    voltage_average: Optional[float] = None  # V
    current_total: Optional[float] = None  # A
    power_total: Optional[float] = None  # W
    apparent_power_total: Optional[float] = None  # VA
    reactive_power_total: Optional[float] = None  # VAR
    power_factor_total: Optional[float] = None  # Cosphi
    frequency: Optional[float] = None  # Hz

    # Line-to-line voltages
    voltage_l1_l2: Optional[float] = None  # V
    voltage_l2_l3: Optional[float] = None  # V
    voltage_l3_l1: Optional[float] = None  # V

    # Neutral current
    current_neutral: Optional[float] = None  # A

    # THD averages
    thd_voltage_avg: Optional[float] = None  # %
    thd_current_avg: Optional[float] = None  # %

    # Energy totals
    energy: Optional[EnergyTotals] = None

    def to_dict(self) -> Dict[str, float]:
        """
        Convert to flat dictionary for backward compatibility.
        Returns only non-None values with appropriate keys.
        """
        result = {}

        # Add per-phase measurements
        if self.phase_l1:
            if self.phase_l1.voltage is not None:
                result['Voltage/L1'] = self.phase_l1.voltage
            if self.phase_l1.current is not None:
                result['Current/L1'] = self.phase_l1.current
            if self.phase_l1.power is not None:
                result['Power/L1'] = self.phase_l1.power
            if self.phase_l1.apparent_power is not None:
                result['ApparentPower/L1'] = self.phase_l1.apparent_power
            if self.phase_l1.reactive_power is not None:
                result['ReactivePower/L1'] = self.phase_l1.reactive_power
            if self.phase_l1.power_factor is not None:
                result['Cosphi/L1'] = self.phase_l1.power_factor
            if self.phase_l1.phase_angle is not None:
                result['PhaseAngle/L1'] = self.phase_l1.phase_angle
            if self.phase_l1.thd_voltage is not None:
                result['THD/VoltageL1'] = self.phase_l1.thd_voltage
            if self.phase_l1.thd_current is not None:
                result['THD/CurrentL1'] = self.phase_l1.thd_current

        if self.phase_l2:
            if self.phase_l2.voltage is not None:
                result['Voltage/L2'] = self.phase_l2.voltage
            if self.phase_l2.current is not None:
                result['Current/L2'] = self.phase_l2.current
            if self.phase_l2.power is not None:
                result['Power/L2'] = self.phase_l2.power
            if self.phase_l2.apparent_power is not None:
                result['ApparentPower/L2'] = self.phase_l2.apparent_power
            if self.phase_l2.reactive_power is not None:
                result['ReactivePower/L2'] = self.phase_l2.reactive_power
            if self.phase_l2.power_factor is not None:
                result['Cosphi/L2'] = self.phase_l2.power_factor
            if self.phase_l2.phase_angle is not None:
                result['PhaseAngle/L2'] = self.phase_l2.phase_angle
            if self.phase_l2.thd_voltage is not None:
                result['THD/VoltageL2'] = self.phase_l2.thd_voltage
            if self.phase_l2.thd_current is not None:
                result['THD/CurrentL2'] = self.phase_l2.thd_current

        if self.phase_l3:
            if self.phase_l3.voltage is not None:
                result['Voltage/L3'] = self.phase_l3.voltage
            if self.phase_l3.current is not None:
                result['Current/L3'] = self.phase_l3.current
            if self.phase_l3.power is not None:
                result['Power/L3'] = self.phase_l3.power
            if self.phase_l3.apparent_power is not None:
                result['ApparentPower/L3'] = self.phase_l3.apparent_power
            if self.phase_l3.reactive_power is not None:
                result['ReactivePower/L3'] = self.phase_l3.reactive_power
            if self.phase_l3.power_factor is not None:
                result['Cosphi/L3'] = self.phase_l3.power_factor
            if self.phase_l3.phase_angle is not None:
                result['PhaseAngle/L3'] = self.phase_l3.phase_angle
            if self.phase_l3.thd_voltage is not None:
                result['THD/VoltageL3'] = self.phase_l3.thd_voltage
            if self.phase_l3.thd_current is not None:
                result['THD/CurrentL3'] = self.phase_l3.thd_current

        # Add system totals/averages
        if self.voltage_average is not None:
            result['Voltage'] = self.voltage_average
        if self.current_total is not None:
            result['Current'] = self.current_total
        if self.power_total is not None:
            result['Power'] = self.power_total
        if self.apparent_power_total is not None:
            result['ApparentPower'] = self.apparent_power_total
        if self.reactive_power_total is not None:
            result['ReactivePower'] = self.reactive_power_total
        if self.power_factor_total is not None:
            result['Cosphi'] = self.power_factor_total
        if self.frequency is not None:
            result['Frequency'] = self.frequency

        # Line-to-line voltages
        if self.voltage_l1_l2 is not None:
            result['Voltage/L1-L2'] = self.voltage_l1_l2
        if self.voltage_l2_l3 is not None:
            result['Voltage/L2-L3'] = self.voltage_l2_l3
        if self.voltage_l3_l1 is not None:
            result['Voltage/L3-L1'] = self.voltage_l3_l1

        # Neutral current
        if self.current_neutral is not None:
            result['Current/N'] = self.current_neutral

        # THD averages
        if self.thd_voltage_avg is not None:
            result['THD/VoltageAvg'] = self.thd_voltage_avg
        if self.thd_current_avg is not None:
            result['THD/CurrentAvg'] = self.thd_current_avg

        # Add energy totals
        if self.energy:
            if self.energy.import_active is not None:
                result['Import'] = self.energy.import_active
            if self.energy.export_active is not None:
                result['Export'] = self.energy.export_active
            if self.energy.import_reactive is not None:
                result['ReactiveImport'] = self.energy.import_reactive
            if self.energy.export_reactive is not None:
                result['ReactiveExport'] = self.energy.export_reactive
            if self.energy.total_active is not None:
                result['Sum'] = self.energy.total_active
            if self.energy.total_reactive is not None:
                result['ReactiveSum'] = self.energy.total_reactive

        return result


# Type alias for meter data union
MeterData = SDM120Data | SDM630Data
