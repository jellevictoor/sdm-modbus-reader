"""
Adapter - MQTT implementation of IMessagePublisher
"""
import paho.mqtt.client as mqtt
from typing import Dict, Optional

from sdm_modbus_reader.ports.message_publisher import MessagePublisher


class MQTTPublisher(MessagePublisher):
    """Publishes meter data to MQTT broker"""

    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        topic_prefix: str = "home/energy/sdm",
        client_id: str = "sdm_reader"
    ):
        self.broker = broker
        self.port = port
        self.topic_prefix = topic_prefix
        self.client = mqtt.Client(client_id=client_id)

        if username and password:
            self.client.username_pw_set(username, password)

    def connect(self) -> bool:
        """
        Schedule a connection to the MQTT broker.

        Uses connect_async() rather than connect(): if the broker isn't
        reachable yet (e.g. this process wins a startup race against the
        broker container), the network loop thread keeps retrying with
        backoff on its own - both for that initial connection and for any
        later drop - so the caller never needs to detect a failure and
        retry connect() itself. is_connected() reports the live state.
        """
        try:
            self.client.reconnect_delay_set(min_delay=1, max_delay=60)
            self.client.connect_async(self.broker, self.port, 60)
            self.client.loop_start()
            return True
        except Exception:
            return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()

    def is_connected(self) -> bool:
        """Check whether there is currently a live connection to the broker"""
        return self.client.is_connected()

    def publish_meter_data(self, meter_slug: str, data: Dict[str, float]):
        """Publish meter data to MQTT"""
        base_topic = f"{self.topic_prefix}/{meter_slug}"

        for key, value in data.items():
            topic = f"{base_topic}/{key}"
            # Format based on magnitude
            if value == 0:
                formatted = "0.0"
            elif abs(value) >= 100:
                formatted = f"{value:.2f}"
            elif abs(value) >= 1:
                formatted = f"{value:.3f}"
            else:
                formatted = f"{value:.6f}"

            self.client.publish(topic, formatted, retain=False)