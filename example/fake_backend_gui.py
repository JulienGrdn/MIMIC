import sys
import yaml
import random
import ast
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / 'src'))

import paho.mqtt.client as mqtt
from mimic.assets.csstyle import Style, Palette
from mimic.assets.theme_manager import ThemeManager
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QLabel, QDoubleSpinBox,
                             QSpinBox, QPushButton, QScrollArea)
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, Qt

YAML_FILE = _REPO_ROOT / 'config' / 'devices_configuration.yaml'


def _spinbox_style(theme: str) -> str:
    """Return QSpinBox stylesheet for the given theme."""
    return Style.Input.spinbox_light if theme == "light" else Style.Input.spinbox_dark


def _double_spinbox_style(theme: str) -> str:
    """Return QDoubleSpinBox stylesheet for the given theme (mirrors spinbox style)."""
    return _spinbox_style(theme).replace('QSpinBox', 'QDoubleSpinBox')


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

        fmt = self.config.get('mqtt_payload_format')
        if fmt:
            try:
                self._payload_format = ast.literal_eval(fmt)
            except Exception:
                self._payload_format = None
        else:
            self._payload_format = None

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
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(8)

        name_label = QLabel(f"<b>{self.config.get('label', self.config['key'])}</b>")
        name_label.setFixedWidth(130)
        layout.addWidget(name_label)

        params_widget = QWidget()
        params_widget.setFixedWidth(210)
        params_layout = QHBoxLayout(params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(2)

        data_type = self.config.get('type', 'float')

        self.min_input = QDoubleSpinBox() if data_type == 'float' else QSpinBox()
        self.max_input = QDoubleSpinBox() if data_type == 'float' else QSpinBox()

        self.min_input.setFixedWidth(65)
        self.max_input.setFixedWidth(65)

        if data_type in ['float', 'integer']:
            self.min_input.setValue(0)
            self.max_input.setValue(24)
            params_layout.addWidget(QLabel("Min:"))
            params_layout.addWidget(self.min_input)
            params_layout.addSpacing(5)
            params_layout.addWidget(QLabel("Max:"))
            params_layout.addWidget(self.max_input)
        else:
            self.min_input.hide()
            self.max_input.hide()
            type_label = QLabel("[Mode: Boolean]")
            type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            params_layout.addWidget(type_label)

        layout.addWidget(params_widget)

        rate_widget = QWidget()
        rate_widget.setFixedWidth(120)
        rate_layout = QHBoxLayout(rate_widget)
        rate_layout.setContentsMargins(0, 0, 0, 0)
        rate_layout.setSpacing(2)

        self.rate_input = QSpinBox()
        self.rate_input.setRange(1, 60000)
        self.rate_input.setValue(250)
        self.rate_input.setSuffix(" ms")
        self.rate_input.setFixedWidth(160)
        rate_layout.addWidget(QLabel("Rate:"))
        rate_layout.addWidget(self.rate_input)
        layout.addWidget(rate_widget)

        # Toggle Button
        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setFixedWidth(60)
        self.toggle_btn.setStyleSheet(Style.Button.suggested)
        self.toggle_btn.clicked.connect(self.toggle_publishing)
        if not self.status_topic:
            self.toggle_btn.setEnabled(False)
        layout.addWidget(self.toggle_btn)

        # Output / Input displays
        self.sent_label = QLabel("Sent: --")
        self.sent_label.setMinimumWidth(90)
        self.sent_label.setStyleSheet(f"color: {Palette.ACCENT_BLUE};")
        layout.addWidget(self.sent_label)

        self.recv_label = QLabel("Recv: --")
        self.recv_label.setMinimumWidth(90)
        self.recv_label.setStyleSheet(f"color: {Palette.STATUS_GREEN};")
        layout.addWidget(self.recv_label)

        layout.addStretch()
        self.setLayout(layout)

        theme = ThemeManager.get_theme()
        self._apply_spinbox_styles(theme)

    def _apply_spinbox_styles(self, theme: str):
        """Apply the correct spinbox stylesheet based on the current theme."""
        for widget in (self.min_input, self.max_input):
            if isinstance(widget, QDoubleSpinBox):
                widget.setStyleSheet(_double_spinbox_style(theme))
            else:
                widget.setStyleSheet(_spinbox_style(theme))
        self.rate_input.setStyleSheet(_spinbox_style(theme))

    def apply_theme(self, theme: str):
        """Slot connected to ThemeManager.theme_changed — re-applies all per-widget styles."""
        self._apply_spinbox_styles(theme)
        if self.toggle_btn.isChecked():
            self.toggle_btn.setStyleSheet(Style.Button.stop)
        else:
            self.toggle_btn.setStyleSheet(Style.Button.suggested)
        self.sent_label.setStyleSheet(f"color: {Palette.ACCENT_BLUE};")
        self.recv_label.setStyleSheet(f"color: {Palette.STATUS_GREEN};")

    def toggle_publishing(self, checked):
        if checked:
            self.toggle_btn.setText("Stop")
            self.toggle_btn.setStyleSheet(Style.Button.stop)
            self.timer.start(self.rate_input.value())
            self.rate_input.setEnabled(False)
        else:
            self.toggle_btn.setText("Start")
            self.toggle_btn.setStyleSheet(Style.Button.suggested)
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
        if self._payload_format:
            try:
                payload_type, loc = self._payload_format
                if payload_type == 'list':
                    lst = [None] * loc + [val]
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
        self.resize(850, 600)
        self.channels = []
        self._group_boxes: list[QGroupBox] = []
        self._cmd_topic_map: dict = {}
        self.all_running = False

        self.mqtt_signals = MqttSignals()
        self.mqtt_signals.message_received.connect(self.route_incoming_message)

        self.load_config()
        self.setup_mqtt()
        self.init_ui()

        tm = ThemeManager.instance()
        tm.theme_changed.connect(self._apply_window_theme)
        for ch in self.channels:
            tm.theme_changed.connect(ch.apply_theme)

    def load_config(self):
        try:
            with open(YAML_FILE, 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            print(f"Failed to load YAML: {e}")
            sys.exit(1)

    def setup_mqtt(self):
        broker_address = 'localhost' #self.config.get('broker', 'localhost')
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        print(f"Connecting to broker at {broker_address}...")
        try:
            self.client.connect(broker_address, 1883, 60)
            self.client.loop_start()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "MQTT Connection Failed",
                f"Could not connect to broker at {broker_address}:\n\n{e}\n\n"
                "The simulator will open but cannot send or receive messages.",
            )

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
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
        payload = msg.payload.decode('utf-8')
        self.mqtt_signals.message_received.emit(msg.topic, payload)

    def route_incoming_message(self, topic, payload):
        channel_widget = self._cmd_topic_map.get(topic)
        if channel_widget is not None:
            channel_widget.update_received(payload)

    def _apply_window_theme(self, theme: str):
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(Style.Default.light if theme == "light" else Style.Default.dark)

        group_style = Style.GroupBox.light if theme == "light" else Style.GroupBox.dark
        for gb in self._group_boxes:
            gb.setStyleSheet(group_style)

        btn_style = Style.Button.simple_light if theme == "light" else Style.Button.simple_dark
        self._theme_btn.setStyleSheet(btn_style)

    def toggle_all_channels(self):
        self.all_running = not self.all_running
        if self.all_running:
            self._toggle_all_btn.setText("Stop All")
            self._toggle_all_btn.setStyleSheet(Style.Button.stop)
        else:
            self._toggle_all_btn.setText("Start All")
            self._toggle_all_btn.setStyleSheet(Style.Button.suggested)

        for ch in self.channels:
            if not ch.status_topic:
                continue
            if ch.toggle_btn.isChecked() != self.all_running:
                ch.toggle_btn.setChecked(self.all_running)
                ch.toggle_publishing(self.all_running)

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        theme = ThemeManager.get_theme()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 5, 0)
        header_layout.addStretch()

        self._toggle_all_btn = QPushButton("Start All")
        self._toggle_all_btn.setStyleSheet(Style.Button.suggested)
        self._toggle_all_btn.setFixedWidth(100)
        self._toggle_all_btn.clicked.connect(self.toggle_all_channels)
        header_layout.addWidget(self._toggle_all_btn)

        self._theme_btn = QPushButton("Toggle Theme")
        self._theme_btn.setStyleSheet(Style.Button.simple_light if theme == "light" else Style.Button.simple_dark)
        self._theme_btn.setFixedWidth(100)
        self._theme_btn.clicked.connect(ThemeManager.toggle_theme)
        header_layout.addWidget(self._theme_btn)

        main_layout.addLayout(header_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        group_style = Style.GroupBox.light if theme == "light" else Style.GroupBox.dark

        for device in self.config.get('devices', []):
            group_box = QGroupBox(
                f"{device['name']} ({device.get('nickname', '')}) - {device.get('device_cat', 'Unknown')}")
            group_box.setStyleSheet(group_style)
            self._group_boxes.append(group_box)

            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(5, 15, 5, 5)
            group_layout.setSpacing(2)

            base_topic = device.get('mqtt_base_topic')

            for channel_config in device.get('channels', []):
                if channel_config.get('type') == 'ui_sep':
                    continue

                ch_widget = ChannelWidget(base_topic, channel_config, self.client)
                self.channels.append(ch_widget)
                group_layout.addWidget(ch_widget)

                if ch_widget.command_topic:
                    self._cmd_topic_map[ch_widget.command_topic] = ch_widget

            group_box.setLayout(group_layout)
            scroll_layout.addWidget(group_box)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        print("Disconnecting MQTT...")
        self.client.loop_stop()
        self.client.disconnect()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ThemeManager.instance()
    app.setStyleSheet(Style.Default.light)

    window = MQTTDeviceSimulator()
    window.show()
    sys.exit(app.exec())