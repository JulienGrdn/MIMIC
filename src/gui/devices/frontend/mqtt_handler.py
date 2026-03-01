from PyQt6.QtCore import QObject, pyqtSignal
import paho.mqtt.client as mqtt
import uuid

class MqttHandler(QObject):
    """
    A unified MQTT Handler that runs in a non-blocking way.
    It manages subscriptions and emits signals when messages arrive.
    """
    message_received = pyqtSignal(str, str) # topic, payload
    connection_status = pyqtSignal(bool)

    def __init__(self, broker_address="localhost", port=1883):
        super().__init__()
        self.broker = broker_address
        self.port = port
        self.client = mqtt.Client(client_id=f"MIMIC_Frontend_{uuid.uuid4().hex[:6]}")

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def start(self):
        """Connects and starts the non-blocking loop with a localhost fallback."""
        try:
            # First attempt: Connect to the primary configured broker
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()  # Run in a background thread
            print(f"[MQTT] Connected successfully to {self.broker}")

        except Exception as primary_error:
            print(f"[MQTT] Primary connection to {self.broker} failed: {primary_error}")
            print("[MQTT] Attempting fallback connection to localhost...")

            try:
                # Fallback attempt: Connect to localhost
                self.broker = "localhost"
                self.client.connect("localhost", self.port, 60)
                self.client.loop_start()
                print("[MQTT] Connected successfully to localhost fallback")

            except Exception as fallback_error:
                # Both attempts failed
                print(f"[MQTT] Fallback connection Error: {fallback_error}")
                self.connection_status.emit(False)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic):
        self.client.subscribe(topic)
        # print(f"[MQTT] Subscribed to {topic}")

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[MQTT] Connected to {self.broker} with on connect code {rc}")
            self.connection_status.emit(True)
        else:
            print(f"[MQTT] Connect failed with code {rc}")
            self.connection_status.emit(False)

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        self.message_received.emit(msg.topic, payload)

    def on_disconnect(self, client, userdata, rc, properties=None):
        print("[MQTT] Disconnected")
        self.connection_status.emit(False)
