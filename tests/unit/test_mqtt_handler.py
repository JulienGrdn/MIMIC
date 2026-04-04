"""Tests for MqttHandler connection logic and signal emission."""
import pytest
from unittest.mock import MagicMock, patch, call


@pytest.fixture()
def handler(qt_app):
    """Return a MqttHandler with a fully mocked paho client."""
    with patch("mimic.devices.frontend.mqtt_handler.mqtt.Client") as MockClient:
        mock_client = MockClient.return_value
        mock_client.connect.return_value = 0
        mock_client.is_connected.return_value = True

        from mimic.devices.frontend.mqtt_handler import MqttHandler
        h = MqttHandler(broker_address="192.168.1.1", port=1883)
        h.client = mock_client
        yield h, mock_client


class TestMqttHandlerStart:
    def test_primary_connect_succeeds(self, handler):
        h, mock_client = handler
        mock_client.connect.return_value = 0

        h.start()

        mock_client.connect.assert_called_once_with("192.168.1.1", 1883, 60)
        mock_client.loop_start.assert_called_once()

    def test_primary_fail_falls_back_to_localhost(self, handler):
        h, mock_client = handler
        mock_client.connect.side_effect = [OSError("refused"), None]

        h.start()

        assert mock_client.connect.call_count == 2
        calls = mock_client.connect.call_args_list
        assert calls[0] == call("192.168.1.1", 1883, 60)
        assert calls[1] == call("localhost", 1883, 60)
        assert h.broker == "localhost"

    def test_both_connections_fail_emits_false(self, qt_app, handler):
        h, mock_client = handler
        mock_client.connect.side_effect = OSError("refused")

        emitted = []
        h.connection_status.connect(emitted.append)

        h.start()

        assert False in emitted

    def test_primary_fail_fallback_succeeds_starts_loop(self, handler):
        h, mock_client = handler
        mock_client.connect.side_effect = [OSError("refused"), None]

        h.start()

        assert mock_client.loop_start.call_count >= 1


class TestMqttHandlerCallbacks:
    def test_on_connect_rc0_emits_true(self, qt_app, handler):
        h, _ = handler
        emitted = []
        h.connection_status.connect(emitted.append)

        h.on_connect(None, None, None, 0)

        assert emitted == [True]

    def test_on_connect_nonzero_rc_emits_false(self, qt_app, handler):
        h, _ = handler
        emitted = []
        h.connection_status.connect(emitted.append)

        h.on_connect(None, None, None, 5)

        assert emitted == [False]

    def test_on_disconnect_emits_false(self, qt_app, handler):
        h, _ = handler
        emitted = []
        h.connection_status.connect(emitted.append)

        h.on_disconnect(None, None, 0)

        assert emitted == [False]

    def test_on_message_emits_topic_and_payload(self, qt_app, handler):
        h, _ = handler
        received = []
        h.message_received.connect(lambda t, p: received.append((t, p)))

        msg = MagicMock()
        msg.topic = "lab/test/temperature"
        msg.payload = b"23.5"
        h.on_message(None, None, msg)

        assert received == [("lab/test/temperature", "23.5")]


class TestMqttHandlerSubscribePublish:
    def test_subscribe_delegates_to_client(self, handler):
        h, mock_client = handler
        h.subscribe("lab/test/#")
        mock_client.subscribe.assert_called_once_with("lab/test/#")

    def test_publish_delegates_to_client(self, handler):
        h, mock_client = handler
        h.publish("lab/test/set", "42")
        mock_client.publish.assert_called_once_with("lab/test/set", "42")
