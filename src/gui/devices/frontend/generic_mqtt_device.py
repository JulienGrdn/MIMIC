from PyQt6.QtCore import QObject, pyqtSignal
from src.gui.devices.frontend.mqtt_broker_registry import get_shared_handler

class GenericMqttDevice(QObject):
    """
    Base class for any frontend device that needs to communicate via MQTT.
    """

    def __init__(self, topic_base, broker="localhost"):
        super().__init__()
        self.topic_base = topic_base
        self.mqtt = get_shared_handler(broker)

    def publish_set(self, subtopic, value):
        """Publishes a value to topic_base/subtopic/set"""
        topic = f"{self.topic_base}/{subtopic}/set"
        self.mqtt.publish(topic, str(value))

    def subscribe_status(self, subtopic, callback):
        """
        Subscribes to topic_base/subtopic/status
        and connects the callback to the message handler.
        """
        target_topic = f"{self.topic_base}/{subtopic}/status"
        self.mqtt.subscribe(target_topic)
        self.mqtt.message_received.connect(
            lambda t, p: callback(p) if t == target_topic else None
        )

    def close(self):
        self.mqtt.stop()