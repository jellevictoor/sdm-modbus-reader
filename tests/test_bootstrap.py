"""
Tests for bootstrap module - verifying dependency initialization
"""
import pytest
from sdm_modbus_reader.bootstrap import (
    bootstrap_application,
    SerialConfig,
    MqttConfig,
    ApplicationContainer,
)
from sdm_modbus_reader.adapters.modbus_reader import ModbusMeterReader
from sdm_modbus_reader.adapters.mqtt_publisher import MQTTPublisher
from sdm_modbus_reader.adapters.memory_repository import InMemoryReadingRepository
from sdm_modbus_reader.application.meter_service import MeterService


class TestBootstrap:
    """Tests for application bootstrap"""

    def test_bootstrap_returns_application_container(self):
        """Verify bootstrap returns an ApplicationContainer"""
        serial_config = SerialConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8
        )

        container = bootstrap_application(serial_config)

        assert isinstance(container, ApplicationContainer)

    def test_bootstrap_creates_meter_reader(self):
        """Verify bootstrap creates a meter reader"""
        serial_config = SerialConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8
        )

        container = bootstrap_application(serial_config)

        assert container.meter_reader is not None
        assert isinstance(container.meter_reader, ModbusMeterReader)

    def test_bootstrap_creates_repository(self):
        """Verify bootstrap creates a repository"""
        serial_config = SerialConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8
        )

        container = bootstrap_application(serial_config)

        assert container.repository is not None
        assert isinstance(container.repository, InMemoryReadingRepository)

    def test_bootstrap_creates_meter_service(self):
        """Verify bootstrap creates a meter service"""
        serial_config = SerialConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8
        )

        container = bootstrap_application(serial_config)

        assert container.meter_service is not None
        assert isinstance(container.meter_service, MeterService)

    def test_bootstrap_creates_mqtt_publisher_when_config_provided(self):
        """Verify MQTT publisher is created when config is provided"""
        serial_config = SerialConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8
        )
        mqtt_config = MqttConfig(
            broker="localhost",
            port=1883,
            topic_prefix="test/meters"
        )

        container = bootstrap_application(serial_config, mqtt_config)

        assert container.message_publisher is not None
        assert isinstance(container.message_publisher, MQTTPublisher)

    def test_bootstrap_without_mqtt_config(self):
        """Verify message publisher is None when no MQTT config provided"""
        serial_config = SerialConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8
        )

        container = bootstrap_application(serial_config)

        assert container.message_publisher is None

    def test_bootstrap_wires_dependencies_correctly(self):
        """Verify dependencies are wired together correctly"""
        serial_config = SerialConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8
        )

        container = bootstrap_application(serial_config)

        # Verify meter service has the correct dependencies injected
        assert container.meter_service.meter_reader is container.meter_reader
        assert container.meter_service.reading_repository is container.repository
