"""Tests for UniversalMqttDevice publish topic construction and message routing."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture()
def device(qt_app):
    """UniversalMqttDevice with a fully mocked MqttHandler."""
    mock_handler = MagicMock()
    mock_handler.connection_status = MagicMock()
    mock_handler.connection_status.connect = MagicMock()
    mock_handler.message_received = MagicMock()
    mock_handler.message_received.connect = MagicMock()

    with patch("mimic.devices.frontend.mqtt_broker_registry.get_shared_handler",
               return_value=mock_handler):
        from mimic.devices.frontend.universal_mqtt import UniversalMqttDevice
        dev = UniversalMqttDevice("lab/test", broker_address="localhost")
        dev.mqtt = mock_handler
        yield dev


# ---------------------------------------------------------------------------
# subscribe_param — topic construction
# ---------------------------------------------------------------------------

class TestSubscribeParam:
    def test_normal_suffix(self, device):
        device.subscribe_param("/temperature")
        device.mqtt.subscribe.assert_called_with("lab/test/temperature")

    def test_suffix_without_leading_slash(self, device):
        device.subscribe_param("temperature")
        device.mqtt.subscribe.assert_called_with("lab/test/temperature")

    def test_base_topic_with_trailing_slash(self, qt_app):
        mock_handler = MagicMock()
        mock_handler.connection_status = MagicMock()
        mock_handler.connection_status.connect = MagicMock()
        mock_handler.message_received = MagicMock()
        mock_handler.message_received.connect = MagicMock()

        with patch("mimic.devices.frontend.mqtt_broker_registry.get_shared_handler",
                   return_value=mock_handler):
            from mimic.devices.frontend.universal_mqtt import UniversalMqttDevice
            dev = UniversalMqttDevice("lab/test/", broker_address="localhost")
            dev.mqtt = mock_handler
            dev.subscribe_param("/temperature")
            mock_handler.subscribe.assert_called_with("lab/test/temperature")

    def test_does_not_subscribe_twice(self, device):
        device.subscribe_param("/temperature")
        device.subscribe_param("/temperature")
        assert device.mqtt.subscribe.call_count == 1

    def test_different_suffixes_both_subscribed(self, device):
        device.subscribe_param("/temperature")
        device.subscribe_param("/humidity")
        assert device.mqtt.subscribe.call_count == 2


# ---------------------------------------------------------------------------
# publish_param — topic construction
# ---------------------------------------------------------------------------

class TestPublishParam:
    def test_publishes_to_correct_topic(self, device):
        device.publish_param("/set", "42")
        device.mqtt.publish.assert_called_once_with("lab/test//set", "42")

    def test_value_converted_to_string(self, device):
        device.publish_param("set", 3.14)
        device.mqtt.publish.assert_called_once_with("lab/test/set", "3.14")

    def test_base_slash_suffix(self, device):
        device.publish_param("command", True)
        device.mqtt.publish.assert_called_once_with("lab/test/command", "True")


# ---------------------------------------------------------------------------
# _on_global_message — routing
# ---------------------------------------------------------------------------

class TestOnGlobalMessage:
    def test_matching_topic_emits_suffix(self, device):
        received = []
        device.message_received_signal.connect(lambda s, p: received.append((s, p)))

        device._on_global_message("lab/test/temperature", "23.5")

        assert len(received) == 1
        assert received[0] == ("temperature", "23.5")

    def test_non_matching_topic_does_not_emit(self, device):
        received = []
        device.message_received_signal.connect(lambda s, p: received.append((s, p)))

        device._on_global_message("other/topic/value", "99")

        assert received == []

    def test_exact_base_topic_does_not_emit(self, device):
        """A message on exactly the base topic (no suffix) should not emit."""
        received = []
        device.message_received_signal.connect(lambda s, p: received.append((s, p)))

        device._on_global_message("lab/test", "payload")

        assert received == []

    def test_suffix_stripped_of_leading_slash(self, device):
        received = []
        device.message_received_signal.connect(lambda s, p: received.append((s, p)))

        device._on_global_message("lab/test/deep/nested", "val")

        assert received[0][0] == "deep/nested"
