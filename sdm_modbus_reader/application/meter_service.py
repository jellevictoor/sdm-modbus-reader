"""
Application service - Orchestrates meter reading operations
"""
from datetime import datetime
from typing import Optional, Dict

from sdm_modbus_reader.ports.meter_reader import IMeterReader
from sdm_modbus_reader.ports.message_publisher import IMessagePublisher
from sdm_modbus_reader.ports.reading_repository import IReadingRepository
from sdm_modbus_reader.domain.models import MeterConfig, MeterReading, MeterType


class MeterService:
    """Orchestrates meter reading, storage, and publishing"""

    def __init__(
        self,
        meter_reader: IMeterReader,
        reading_repository: IReadingRepository,
        message_publisher: Optional[IMessagePublisher] = None
    ):
        self.meter_reader = meter_reader
        self.reading_repository = reading_repository
        self.message_publisher = message_publisher

    def read_and_store_meter(self, meter_config: MeterConfig) -> Optional[MeterReading]:
        """
        Read a meter, store the reading, and optionally publish to MQTT

        Args:
            meter_config: Configuration for the meter to read

        Returns:
            The meter reading if successful, None otherwise
        """
        # Read meter data
        data = self.meter_reader.read_meter(meter_config.address, meter_config.meter_type)

        if data is None:
            return None

        # Create reading
        reading = MeterReading(
            meter_id=meter_config.address,
            meter_type=meter_config.meter_type,
            meter_name=meter_config.display_name,
            data=data,
            timestamp=datetime.now()
        )

        # Store reading
        self.reading_repository.save(reading)

        # Publish to MQTT if available
        if self.message_publisher:
            self.message_publisher.publish_meter_data(meter_config.slug, data)

        return reading

    def get_meter_reading(self, meter_id: int) -> Optional[MeterReading]:
        """Get the latest reading for a specific meter"""
        return self.reading_repository.get_by_meter_id(meter_id)

    def get_all_readings(self) -> Dict[int, MeterReading]:
        """Get the latest readings for all meters"""
        return self.reading_repository.get_all()