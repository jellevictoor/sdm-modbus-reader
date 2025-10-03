"""
Domain models - Core business entities
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from enum import Enum

from sdm_modbus_reader.domain.meter_data import MeterData


class MeterType(Enum):
    """Supported meter types"""
    SDM120 = "SDM120"
    SDM630 = "SDM630"


@dataclass
class MeterConfig:
    """Configuration for a single meter"""
    meter_type: MeterType
    address: int
    display_name: str
    slug: str

    def __post_init__(self):
        if not (1 <= self.address <= 247):
            raise ValueError(f"Address must be between 1 and 247, got {self.address}")


@dataclass
class MeterReading:
    """A reading from a meter"""
    meter_id: int
    meter_type: MeterType
    meter_name: str
    data: MeterData
    timestamp: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "meter_id": self.meter_id,
            "meter_type": self.meter_type.value,
            "meter_name": self.meter_name,
            "data": self.data.to_dict(),  # Convert MeterData to flat dict
            "timestamp": self.timestamp.isoformat()
        }