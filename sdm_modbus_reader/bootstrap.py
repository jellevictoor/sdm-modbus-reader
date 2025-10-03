"""
Bootstrap module - Initializes and wires up all dependencies
"""
from typing import Optional
from dataclasses import dataclass

from sdm_modbus_reader.adapters.modbus_reader import ModbusMeterReader
from sdm_modbus_reader.adapters.mqtt_publisher import MQTTPublisher
from sdm_modbus_reader.adapters.memory_repository import InMemoryReadingRepository
from sdm_modbus_reader.application.meter_service import MeterService
from sdm_modbus_reader.ports.meter_reader import MeterReader
from sdm_modbus_reader.ports.message_publisher import MessagePublisher
from sdm_modbus_reader.ports.reading_repository import ReadingRepository


@dataclass
class SerialConfig:
    """Serial port configuration"""
    port: str
    baudrate: int
    parity: str
    stopbits: int
    bytesize: int


@dataclass
class MqttConfig:
    """MQTT broker configuration"""
    broker: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    topic_prefix: str = "home/energy/sdm"


@dataclass
class ApplicationContainer:
    """Container holding all initialized application dependencies"""
    meter_reader: MeterReader
    repository: ReadingRepository
    message_publisher: Optional[MessagePublisher]
    meter_service: MeterService


def bootstrap_application(
    serial_config: SerialConfig,
    mqtt_config: Optional[MqttConfig] = None
) -> ApplicationContainer:
    """
    Bootstrap the application by initializing and wiring up all dependencies.

    This is the composition root where we create concrete implementations
    and wire them together following dependency injection principles.

    Args:
        serial_config: Configuration for the serial/Modbus connection
        mqtt_config: Optional configuration for MQTT publishing

    Returns:
        ApplicationContainer with all initialized dependencies
    """
    # Initialize adapters (infrastructure layer)
    meter_reader = ModbusMeterReader(
        port=serial_config.port,
        baudrate=serial_config.baudrate,
        parity=serial_config.parity,
        stopbits=serial_config.stopbits,
        bytesize=serial_config.bytesize
    )

    repository = InMemoryReadingRepository()

    message_publisher = None
    if mqtt_config:
        message_publisher = MQTTPublisher(
            broker=mqtt_config.broker,
            port=mqtt_config.port,
            username=mqtt_config.username,
            password=mqtt_config.password,
            topic_prefix=mqtt_config.topic_prefix
        )

    # Initialize application service (application layer)
    meter_service = MeterService(
        meter_reader=meter_reader,
        reading_repository=repository,
        message_publisher=message_publisher
    )

    # Register repository with API module (for web interface)
    from sdm_modbus_reader.api import set_repository
    set_repository(repository)

    return ApplicationContainer(
        meter_reader=meter_reader,
        repository=repository,
        message_publisher=message_publisher,
        meter_service=meter_service
    )
