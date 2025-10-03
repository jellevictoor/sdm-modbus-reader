"""
Port - Interface for storing meter readings
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict
from sdm_modbus_reader.domain.models import MeterReading


class ReadingRepository(ABC):
    """Interface for storing and retrieving meter readings"""

    @abstractmethod
    def save(self, reading: MeterReading):
        """
        Save a meter reading

        Args:
            reading: The meter reading to save
        """
        pass

    @abstractmethod
    def get_by_meter_id(self, meter_id: int) -> Optional[MeterReading]:
        """
        Get the latest reading for a specific meter

        Args:
            meter_id: The meter ID

        Returns:
            The latest reading, or None if not found
        """
        pass

    @abstractmethod
    def get_all(self) -> Dict[int, MeterReading]:
        """
        Get the latest readings for all meters

        Returns:
            Dictionary mapping meter IDs to their latest readings
        """
        pass