"""
Adapter - In-memory implementation of IReadingRepository
"""
from typing import Dict, Optional
import threading

from sdm_modbus_reader.ports.reading_repository import ReadingRepository
from sdm_modbus_reader.domain.models import MeterReading


class InMemoryReadingRepository(ReadingRepository):
    """Thread-safe in-memory storage for meter readings"""

    def __init__(self):
        self._data: Dict[int, MeterReading] = {}
        self._lock = threading.Lock()

    def save(self, reading: MeterReading):
        """Save a meter reading"""
        with self._lock:
            self._data[reading.meter_id] = reading

    def get_by_meter_id(self, meter_id: int) -> Optional[MeterReading]:
        """Get the latest reading for a specific meter"""
        with self._lock:
            return self._data.get(meter_id)

    def get_all(self) -> Dict[int, MeterReading]:
        """Get the latest readings for all meters"""
        with self._lock:
            return self._data.copy()