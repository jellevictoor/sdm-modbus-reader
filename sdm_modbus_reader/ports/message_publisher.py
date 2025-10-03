"""
Port - Interface for publishing messages
"""
from abc import ABC, abstractmethod
from typing import Dict


class MessagePublisher(ABC):
    """Interface for publishing meter data to message brokers"""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the message broker"""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the message broker"""
        pass

    @abstractmethod
    def publish_meter_data(self, meter_slug: str, data: Dict[str, float]):
        """
        Publish meter data

        Args:
            meter_slug: Slug identifier for the meter
            data: Dictionary of metric names to values
        """
        pass