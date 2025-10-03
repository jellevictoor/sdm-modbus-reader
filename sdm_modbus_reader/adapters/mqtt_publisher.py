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
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            return True
        except Exception:
            return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_meter_data(self, meter_slug: str, data: Dict[str, float]):
        """Publish meter data to MQTT"""
        base_topic = f"{self.topic_prefix}/{meter_slug}"

        for key, value in data.items():
            topic = f"{base_topic}/{key}"
            # Format based on magnitude
            if abs(value) >= 100:
                formatted = f"{value:.2f}"
            elif abs(value) >= 1:
                formatted = f"{value:.3f}"
            else:
                formatted = f"{value:.6f}"

            self.client.publish(topic, formatted, retain=True)