"""Tests for the YAML device loader (GenericYamlDevice)."""
import pytest
import yaml
from unittest.mock import patch, MagicMock


# Patch UniversalMqttDevice at the yaml_plugin import level so no real MQTT
# connections are attempted when GenericYamlDevice is instantiated in tests.
@pytest.fixture(autouse=True)
def no_mqtt(qt_app):
    with patch("mimic.devices.yaml_plugin.UniversalMqttDevice") as MockDriver:
        instance = MockDriver.return_value
        instance.message_received_signal = MagicMock()
        instance.message_received_signal.connect = MagicMock()
        yield MockDriver


# ---------------------------------------------------------------------------
# load_yaml_config
# ---------------------------------------------------------------------------

class TestLoadYamlConfig:
    def test_missing_file_returns_empty_dict(self, tmp_path, monkeypatch):
        from mimic.devices import yaml_plugin
        monkeypatch.setattr(yaml_plugin, "CONFIG_PATH", str(tmp_path / "nonexistent.yaml"))
        result = yaml_plugin.load_yaml_config()
        assert result == {}

    def test_valid_yaml_returns_dict(self, tmp_path, monkeypatch):
        cfg = tmp_path / "devices.yaml"
        cfg.write_text("broker: localhost\ndevices: []\n")
        from mimic.devices import yaml_plugin
        monkeypatch.setattr(yaml_plugin, "CONFIG_PATH", str(cfg))
        result = yaml_plugin.load_yaml_config()
        assert result == {"broker": "localhost", "devices": []}


# ---------------------------------------------------------------------------
# GenericYamlDevice — channel construction
# ---------------------------------------------------------------------------

def make_device(config: dict):
    from mimic.devices.yaml_plugin import GenericYamlDevice
    return GenericYamlDevice(config)


MINIMAL_CONFIG = {
    "name": "Test Device",
    "mqtt_base_topic": "lab/test",
    "channels": [
        {"key": "temperature", "label": "Temperature", "type": "float",
         "status_suffix": "/temperature", "access": "read"},
    ],
}


class TestGenericYamlDeviceChannels:
    def test_device_name_set(self):
        dev = make_device(MINIMAL_CONFIG)
        assert dev.name == "Test Device"

    def test_channel_count(self):
        dev = make_device(MINIMAL_CONFIG)
        assert len(list(dev.get_all_params())) == 1

    def test_parameter_label(self):
        dev = make_device(MINIMAL_CONFIG)
        params = list(dev.get_all_params())
        assert params[0].label == "Temperature"

    def test_parameter_type_float(self):
        dev = make_device(MINIMAL_CONFIG)
        params = list(dev.get_all_params())
        assert params[0].param_type == "float"

    def test_parameter_type_mapping(self):
        for yaml_type, expected in [("integer", "int"), ("boolean", "bool"), ("str", "str")]:
            config = dict(MINIMAL_CONFIG)
            config["channels"] = [
                {"key": "ch", "label": "Ch", "type": yaml_type,
                 "status_suffix": "/ch", "access": "read"},
            ]
            dev = make_device(config)
            assert list(dev.get_all_params())[0].param_type == expected

    def test_read_only_channel_has_no_setter(self):
        dev = make_device(MINIMAL_CONFIG)
        param = list(dev.get_all_params())[0]
        assert param.set_cmd is None

    def test_read_write_channel_has_setter(self):
        config = dict(MINIMAL_CONFIG)
        config["channels"] = [
            {"key": "setpoint", "label": "Setpoint", "type": "float",
             "status_suffix": "/status", "command_suffix": "/set",
             "access": "read_write"},
        ]
        dev = make_device(config)
        param = list(dev.get_all_params())[0]
        assert param.set_cmd is not None

    def test_status_suffix_registered(self):
        dev = make_device(MINIMAL_CONFIG)
        assert "/temperature" in dev._status_map

    def test_command_suffix_registered(self):
        config = dict(MINIMAL_CONFIG)
        config["channels"] = [
            {"key": "sp", "label": "SP", "type": "float",
             "status_suffix": "/status", "command_suffix": "/set",
             "access": "read_write"},
        ]
        dev = make_device(config)
        assert "/set" in dev._command_map

    def test_ui_sep_channel_creates_ui_sep_param(self):
        config = dict(MINIMAL_CONFIG)
        config["channels"] = [
            {"key": "sep1", "label": "---", "type": "ui_sep"},
        ]
        dev = make_device(config)
        params = list(dev.get_all_params())
        assert params[0].ui_type == "ui_sep"

    def test_multiple_channels(self):
        config = dict(MINIMAL_CONFIG)
        config["channels"] = [
            {"key": "ch1", "label": "Ch1", "type": "float",
             "status_suffix": "/ch1", "access": "read"},
            {"key": "ch2", "label": "Ch2", "type": "integer",
             "status_suffix": "/ch2", "access": "read"},
        ]
        dev = make_device(config)
        assert len(list(dev.get_all_params())) == 2

    def test_mqtt_base_stored(self):
        dev = make_device(MINIMAL_CONFIG)
        assert dev.mqtt_base == "lab/test"
