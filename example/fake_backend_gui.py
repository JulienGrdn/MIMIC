import sys
import yaml
import random
import ast
import paho.mqtt.client as mqtt
import InitializeMIMIC
from src.gui.assets.csstyle import Style
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QLabel, QDoubleSpinBox,
                             QSpinBox, QPushButton, QScrollArea, QFormLayout,
                             QFrame)
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, Qt

# Configuration Path
YAML_FILE = 'config/devices_configuration.yaml'

class MqttSignals(QObject):
    """
    Signals must inherit from QObject. We use this to safely transfer 
    incoming MQTT messages from Paho's background thread to the PyQt GUI thread.
    """
    message_received = pyqtSignal(str, str)  # topic, payload

class ChannelWidget(QWidget):
    def __init__(self, base_topic, channel_config, mqtt_client):
        super().__init__()
        self.base_topic = base_topic
        self.config = channel_config
        self.mqtt_client = mqtt_client
        self.is_publishing = False
        
        # Build topics
        self.status_topic = None
        if 'status_suffix' in self.config:
            self.status_topic = f"{self.base_topic}/{self.config['status_suffix']}"
            
        self.command_topic = None
        if 'command_suffix' in self.config:
            self.command_topic = f"{self.base_topic}/{self.config['command_suffix']}"

        self.init_ui()
        
        # Setup Timer for independent publish rates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.publish_data)

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)

        # Label
        name_label = QLabel(f"<b>{self.config.get('label', self.config['key'])}</b>")
        name_label.setFixedWidth(120)
        layout.addWidget(name_label)

        # Data Type specifics (Min/Max inputs)
        data_type = self.config.get('type', 'float')
        
        self.min_input = QDoubleSpinBox() if data_type == 'float' else QSpinBox()
        self.max_input = QDoubleSpinBox() if data_type == 'float' else QSpinBox()
        
        if data_type in ['float', 'integer']:
            self.min_input.setValue(0)
            self.max_input.setValue(24)
            layout.addWidget(QLabel("Min:"))
            layout.addWidget(self.min_input)
            layout.addWidget(QLabel("Max:"))
            layout.addWidget(self.max_input)
        else:
            self.min_input.hide()
            self.max_input.hide()
            type_label = QLabel("[Boolean]")
            type_label.setFixedWidth(160)
            layout.addWidget(type_label)

        # Publish Rate
        self.rate_input = QSpinBox()
        self.rate_input.setRange(10, 60000) # 10ms to 60s
        self.rate_input.setValue(1000) # Default 1 second
        self.rate_input.setSuffix(" ms")
        layout.addWidget(QLabel("Rate:"))
        layout.addWidget(self.rate_input)

        # Toggle Button
        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self.toggle_publishing)
        if not self.status_topic:
            self.toggle_btn.setEnabled(False) # Disable if no status topic to publish to
        layout.addWidget(self.toggle_btn)

        # Output / Input displays
        self.sent_label = QLabel("Sent: --")
        self.sent_label.setMinimumWidth(100)
        self.sent_label.setStyleSheet("color: blue;")
        layout.addWidget(self.sent_label)

        self.recv_label = QLabel("Recv: --")
        self.recv_label.setMinimumWidth(100)
        self.recv_label.setStyleSheet("color: green;")
        layout.addWidget(self.recv_label)

        self.setLayout(layout)
        self.setStyleSheet(Style.Default.light)

    def toggle_publishing(self, checked):
        if checked:
            self.toggle_btn.setText("Stop")
            self.timer.start(self.rate_input.value())
            self.rate_input.setEnabled(False) # Lock rate while running
        else:
            self.toggle_btn.setText("Start")
            self.timer.stop()
            self.rate_input.setEnabled(True)

    def generate_value(self):
        data_type = self.config.get('type', 'float')
        if data_type == 'float':
            return round(random.uniform(self.min_input.value(), self.max_input.value()), 2)
        elif data_type == 'integer':
            return random.randint(self.min_input.value(), self.max_input.value())
        elif data_type == 'boolean':
            return str(random.choice([True, False])).lower()
        return 0

    def format_payload(self, val):
        fmt = self.config.get('mqtt_payload_format')
        if fmt:
            try:
                payload_type, loc = ast.literal_eval(fmt)
                if payload_type == 'list':
                    lst = [None] * loc
                    lst.append(val)
                    return str(lst)
                elif payload_type == 'dict':
                    return str({loc: val})
            except Exception as e:
                print(f"Format error: {e}")
                return str(val)
        return str(val)

    def publish_data(self):
        if not self.status_topic:
            return
            
        raw_val = self.generate_value()
        payload = self.format_payload(raw_val)
        
        self.mqtt_client.publish(self.status_topic, payload)
        self.sent_label.setText(f"Sent: {payload}")

    def update_received(self, payload):
        self.recv_label.setText(f"Recv: {payload}")


class MQTTDeviceSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MQTT Device Simulator")
        self.resize(900, 700)
        self.channels = [] 
        
        self.mqtt_signals = MqttSignals()
        self.mqtt_signals.message_received.connect(self.route_incoming_message)

        self.load_config()
        self.setup_mqtt()
        self.init_ui()

    def load_config(self):
        try:
            with open(YAML_FILE, 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Failed to load YAML: {e}")
            sys.exit(1)

    def setup_mqtt(self):
        broker_address = 'localhost'
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        print(f"Connecting to broker at {broker_address}...")
        try:
            self.client.connect(broker_address, 1883, 60)
            self.client.loop_start() # Starts network loop in background thread
        except Exception as e:
            print(f"MQTT Connection failed: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            # Subscribe to all command topics
            for device in self.config.get('devices', []):
                base_topic = device.get('mqtt_base_topic')
                if not base_topic:
                    continue
                for channel in device.get('channels', []):
                    if 'command_suffix' in channel:
                        topic = f"{base_topic}/{channel['command_suffix']}"
                        self.client.subscribe(topic)
                        print(f"Subscribed to {topic}")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        # Emit signal to handle UI update safely in the main thread
        payload = msg.payload.decode('utf-8')
        self.mqtt_signals.message_received.emit(msg.topic, payload)

    def route_incoming_message(self, topic, payload):
        # Find which channel widget matches the incoming topic
        for channel_widget in self.channels:
            if channel_widget.command_topic == topic:
                channel_widget.update_received(payload)

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Parse devices and build UI blocks
        for device in self.config.get('devices', []):
            group_box = QGroupBox(f"{device['name']} ({device.get('nickname', '')}) - {device.get('device_cat', 'Unknown')}")
            group_layout = QVBoxLayout()

            base_topic = device.get('mqtt_base_topic')

            for channel_config in device.get('channels', []):
                ch_widget = ChannelWidget(base_topic, channel_config, self.client)
                self.channels.append(ch_widget)
                group_layout.addWidget(ch_widget)

                # Separator line
                line = QFrame()
                group_layout.addWidget(line)

            group_box.setLayout(group_layout)
            scroll_layout.addWidget(group_box)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        """Ensure clean disconnect when the window is closed."""
        print("Disconnecting MQTT...")
        self.client.loop_stop()
        self.client.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion") 
    
    window = MQTTDeviceSimulator()
    window.show()
    sys.exit(app.exec())
