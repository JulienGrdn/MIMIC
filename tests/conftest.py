import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qt_app():
    """Single QApplication instance for the entire test session."""
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def mock_mqtt_client():
    """Patch paho-mqtt Client so no real network connections are made."""
    with patch("paho.mqtt.client.Client") as MockClient:
        instance = MockClient.return_value
        instance.connect.return_value = 0          # MQTT_ERR_SUCCESS
        instance.is_connected.return_value = True
        yield instance


@pytest.fixture()
def minimal_device_yaml(tmp_path):
    """Write a minimal devices_configuration.yaml to a temp directory."""
    config = tmp_path / "devices_configuration.yaml"
    config.write_text("""
devices:
  - name: "Test Device"
    mqtt_base_topic: "lab/test"
    channels:
      - label: "Temperature"
        status_suffix: "/temperature"
        access: "read"
        type: "float"
""")
    return config
