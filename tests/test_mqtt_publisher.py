"""
Integration tests for MQTT publisher adapter using testcontainers
Tests actual behavior against a real MQTT broker
"""
import pytest
import time
from threading import Event
from typing import Dict, List, Tuple
import paho.mqtt.client as mqtt
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from sdm_modbus_reader.adapters.mqtt_publisher import MQTTPublisher


class MosquittoContainer(DockerContainer):
    """Testcontainer for Mosquitto MQTT broker"""

    def __init__(self, image: str = "eclipse-mosquitto:2.0"):
        super().__init__(image)
        self.with_exposed_ports(1883)
        self.with_command("mosquitto -c /mosquitto-no-auth.conf")

    def start(self):
        """Start container and wait for it to be ready"""
        super().start()
        wait_for_logs(self, "mosquitto version", timeout=30)
        return self

    def get_broker_url(self) -> str:
        """Get the broker connection URL"""
        host = self.get_container_host_ip()
        port = self.get_exposed_port(1883)
        return host, int(port)


class MQTTTestSubscriber:
    """Helper to subscribe and collect messages from MQTT broker"""

    def __init__(self, broker: str, port: int):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client(client_id="test_subscriber")
        self.messages: List[Tuple[str, str, bool]] = []
        self.message_event = Event()

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        client.subscribe("#")  # Subscribe to all topics

    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        self.messages.append((msg.topic, msg.payload.decode(), msg.retain))
        self.message_event.set()

    def connect(self):
        """Connect to broker"""
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        time.sleep(0.5)  # Give it time to connect

    def disconnect(self):
        """Disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()

    def wait_for_messages(self, count: int, timeout: float = 5.0) -> bool:
        """Wait for a specific number of messages"""
        deadline = time.time() + timeout
        while len(self.messages) < count and time.time() < deadline:
            self.message_event.wait(timeout=0.1)
            self.message_event.clear()
        return len(self.messages) >= count

    def get_message(self, topic: str) -> Tuple[str, bool]:
        """Get message by topic, returns (payload, retain_flag)"""
        for msg_topic, payload, retain in self.messages:
            if msg_topic == topic:
                return payload, retain
        return None, False


@pytest.fixture(scope="module")
def mosquitto_container():
    """Start Mosquitto container for tests"""
    container = MosquittoContainer()
    container.start()
    yield container
    container.stop()


@pytest.fixture
def mqtt_broker(mosquitto_container):
    """Get MQTT broker connection details"""
    host, port = mosquitto_container.get_broker_url()
    return host, port


@pytest.fixture
def mqtt_publisher(mqtt_broker):
    """Create MQTT publisher connected to test broker"""
    host, port = mqtt_broker
    publisher = MQTTPublisher(
        broker=host,
        port=port,
        topic_prefix="test/meters",
        client_id="test_publisher"
    )
    connected = publisher.connect()
    assert connected, "Failed to connect to MQTT broker"
    time.sleep(0.5)  # Give connection time to establish
    yield publisher
    publisher.disconnect()


@pytest.fixture
def mqtt_subscriber(mqtt_broker):
    """Create test subscriber to verify messages"""
    host, port = mqtt_broker
    subscriber = MQTTTestSubscriber(host, port)
    subscriber.connect()
    # Wait a bit for any retained messages to arrive and then clear them
    time.sleep(1.0)
    subscriber.messages.clear()
    yield subscriber
    subscriber.disconnect()


class TestMQTTPublisherAdapter:
    """Integration tests for MQTT publisher adapter"""

    def test_can_connect_to_real_broker(self, mqtt_broker):
        """Verify adapter can connect to actual MQTT broker"""
        host, port = mqtt_broker
        publisher = MQTTPublisher(broker=host, port=port)

        result = publisher.connect()

        assert result is True
        publisher.disconnect()

    def test_publishes_messages_to_broker(self, mqtt_publisher, mqtt_subscriber):
        """Verify messages are actually published to broker"""
        data = {"Voltage": 230.5}

        mqtt_publisher.publish_meter_data("kitchen", data)

        # Wait for message to be received
        assert mqtt_subscriber.wait_for_messages(1, timeout=3.0)
        assert len(mqtt_subscriber.messages) >= 1

    def test_uses_correct_topic_structure(self, mqtt_publisher, mqtt_subscriber):
        """Verify topic format is prefix/meter-slug/metric"""
        data = {"Voltage": 230.5}

        mqtt_publisher.publish_meter_data("kitchen-meter", data)

        mqtt_subscriber.wait_for_messages(1, timeout=3.0)
        payload, _ = mqtt_subscriber.get_message("test/meters/kitchen-meter/Voltage")

        assert payload is not None
        assert payload == "230.50"

    def test_publishes_all_data_points(self, mqtt_publisher, mqtt_subscriber):
        """Verify all data points are published as separate messages"""
        data = {
            "Voltage": 230.5,
            "Current": 1.234,
            "Power": 276.6
        }

        mqtt_publisher.publish_meter_data("test-meter", data)

        mqtt_subscriber.wait_for_messages(3, timeout=3.0)

        voltage, _ = mqtt_subscriber.get_message("test/meters/test-meter/Voltage")
        current, _ = mqtt_subscriber.get_message("test/meters/test-meter/Current")
        power, _ = mqtt_subscriber.get_message("test/meters/test-meter/Power")

        assert voltage is not None
        assert current is not None
        assert power is not None

    def test_formats_large_values_with_two_decimals(self, mqtt_publisher, mqtt_subscriber):
        """Verify values >= 100 are formatted with 2 decimal places"""
        data = {"Power": 1234.5678}

        mqtt_publisher.publish_meter_data("test", data)

        mqtt_subscriber.wait_for_messages(1, timeout=3.0)
        payload, _ = mqtt_subscriber.get_message("test/meters/test/Power")

        assert payload == "1234.57"

    def test_formats_medium_values_with_three_decimals(self, mqtt_publisher, mqtt_subscriber):
        """Verify values between 1 and 100 are formatted with 3 decimal places"""
        data = {"Current": 5.6789}

        mqtt_publisher.publish_meter_data("test", data)

        mqtt_subscriber.wait_for_messages(1, timeout=3.0)
        payload, _ = mqtt_subscriber.get_message("test/meters/test/Current")

        assert payload == "5.679"

    def test_formats_small_values_with_six_decimals(self, mqtt_publisher, mqtt_subscriber):
        """Verify values < 1 are formatted with 6 decimal places"""
        data = {"Cosphi": 0.123456789}

        mqtt_publisher.publish_meter_data("test", data)

        mqtt_subscriber.wait_for_messages(1, timeout=3.0)
        payload, _ = mqtt_subscriber.get_message("test/meters/test/Cosphi")

        assert payload == "0.123457"

    def test_publishes_with_retain_flag(self, mqtt_broker):
        """Verify messages are published with retain flag set"""
        host, port = mqtt_broker
        publisher = MQTTPublisher(
            broker=host,
            port=port,
            topic_prefix="test/retain-test"
        )
        publisher.connect()

        # Publish with retain
        data = {"Voltage": 230.5}
        publisher.publish_meter_data("test", data)
        time.sleep(0.5)  # Give broker time to process

        # Create new subscriber to get retained message
        subscriber = MQTTTestSubscriber(host, port)
        subscriber.connect()

        # Wait for retained message to arrive
        assert subscriber.wait_for_messages(1, timeout=3.0)
        _, retain = subscriber.get_message("test/retain-test/test/Voltage")

        subscriber.disconnect()
        publisher.disconnect()

        assert retain is True

    def test_handles_empty_data_gracefully(self, mqtt_publisher, mqtt_subscriber):
        """Verify no messages are published for empty data"""
        mqtt_publisher.publish_meter_data("test", {})

        # Wait a bit to see if any messages arrive
        time.sleep(1.0)

        assert len(mqtt_subscriber.messages) == 0

    def test_handles_multiple_meters(self, mqtt_publisher, mqtt_subscriber):
        """Verify different meters publish to different topics"""
        mqtt_publisher.publish_meter_data("kitchen", {"Voltage": 230.0})
        mqtt_publisher.publish_meter_data("garage", {"Voltage": 231.0})

        mqtt_subscriber.wait_for_messages(2, timeout=3.0)

        kitchen_voltage, _ = mqtt_subscriber.get_message("test/meters/kitchen/Voltage")
        garage_voltage, _ = mqtt_subscriber.get_message("test/meters/garage/Voltage")

        assert kitchen_voltage == "230.00"
        assert garage_voltage == "231.00"

    def test_connection_failure_returns_false(self):
        """Verify connection to invalid broker returns False"""
        publisher = MQTTPublisher(broker="invalid-broker-that-does-not-exist", port=1883)

        result = publisher.connect()

        assert result is False