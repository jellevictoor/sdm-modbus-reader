"""
Tests for MQTT publisher adapter
"""
import pytest
from unittest.mock import Mock, patch, call
from sdm_modbus_reader.adapters.mqtt_publisher import MQTTPublisher


class TestMQTTPublisher:
    """Tests for MQTTPublisher - testing behavior through the message publisher port"""

    @pytest.fixture
    def mqtt_publisher(self):
        """Create MQTT publisher with default settings"""
        with patch('sdm_modbus_reader.adapters.mqtt_publisher.mqtt.Client'):
            publisher = MQTTPublisher(
                broker="test.broker.com",
                port=1883,
                topic_prefix="test/meters"
            )
            return publisher

    def test_can_connect_to_broker(self, mqtt_publisher):
        """Test that connection to broker succeeds"""
        mqtt_publisher.client.connect.return_value = None

        result = mqtt_publisher.connect()

        assert result is True

    def test_returns_false_when_connection_fails(self, mqtt_publisher):
        """Test that connection failure is handled gracefully"""
        mqtt_publisher.client.connect.side_effect = Exception("Connection failed")

        result = mqtt_publisher.connect()

        assert result is False

    def test_publishes_all_meter_readings(self, mqtt_publisher):
        """Test that all meter data points are published"""
        data = {
            "Voltage": 230.5,
            "Current": 1.234,
            "Power": 150.75
        }

        mqtt_publisher.publish_meter_data("kitchen-meter", data)

        assert mqtt_publisher.client.publish.call_count == 3

    def test_formats_large_values_with_two_decimals(self, mqtt_publisher):
        """Test that values >= 10 are formatted with 2 decimal places"""
        data = {"Power": 1234.5678}

        mqtt_publisher.publish_meter_data("test", data)

        mqtt_publisher.client.publish.assert_called_once_with(
            "test/meters/test/Power",
            "1234.57",
            retain=True
        )

    def test_formats_medium_values_with_three_decimals(self, mqtt_publisher):
        """Test that values between 1 and 10 are formatted with 3 decimal places"""
        data = {"Current": 5.6789}

        mqtt_publisher.publish_meter_data("test", data)

        mqtt_publisher.client.publish.assert_called_once_with(
            "test/meters/test/Current",
            "5.679",
            retain=True
        )

    def test_formats_small_values_with_six_decimals(self, mqtt_publisher):
        """Test that values < 1 are formatted with 6 decimal places"""
        data = {"Cosphi": 0.123456789}

        mqtt_publisher.publish_meter_data("test", data)

        mqtt_publisher.client.publish.assert_called_once_with(
            "test/meters/test/Cosphi",
            "0.123457",
            retain=True
        )

    def test_does_not_publish_when_data_is_empty(self, mqtt_publisher):
        """Test that no messages are published when data is empty"""
        mqtt_publisher.publish_meter_data("test", {})

        mqtt_publisher.client.publish.assert_not_called()

    def test_uses_correct_topic_structure(self, mqtt_publisher):
        """Test that topic follows prefix/meter-name/field pattern"""
        data = {"Voltage": 230.5}

        mqtt_publisher.publish_meter_data("kitchen-meter", data)

        call_args = mqtt_publisher.client.publish.call_args[0]
        topic = call_args[0]

        assert topic == "test/meters/kitchen-meter/Voltage"

    def test_publishes_with_retain_flag(self, mqtt_publisher):
        """Test that messages are published with retain flag"""
        data = {"Voltage": 230.5}

        mqtt_publisher.publish_meter_data("test", data)

        call_kwargs = mqtt_publisher.client.publish.call_args[1]

        assert call_kwargs["retain"] is True
