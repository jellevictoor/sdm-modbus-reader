"""
Port - Interface for reading meters
"""
from abc import ABC, abstractmethod
from typing import Optional
from sdm_modbus_reader.domain.models import MeterType
from sdm_modbus_reader.domain.meter_data import MeterData


class MeterReader(ABC):
    """Interface for reading data from energy meters"""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the meter communication interface"""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the meter communication interface"""
        pass

    @abstractmethod
    def read_meter(self, device_id: int, meter_type: MeterType) -> Optional[MeterData]:
        """
        Read all available data from a meter

        Args:
            device_id: The Modbus address of the meter
            meter_type: The type of meter to read

        Returns:
            MeterData (SDM120Data or SDM630Data), or None if read failed
        """
        pass