"""Tests for the Parameter dataclass callback system and payload parsing."""
import json
import pytest
from mimic.devices.frontend.instrument_base import Parameter


def make_param(**kwargs):
    defaults = dict(name="test_param", label="Test", param_type="float")
    defaults.update(kwargs)
    return Parameter(**defaults)


# ---------------------------------------------------------------------------
# Callback registration and notification
# ---------------------------------------------------------------------------

class TestNotifyWidget:
    def test_fires_single_callback(self):
        received = []
        p = make_param()
        p.update_widget = received.append
        p.notify_widget(42.0)
        assert received == [42.0]

    def test_fires_multiple_callbacks(self):
        a, b = [], []
        p = make_param()
        p.update_widget = a.append
        p.update_widget = b.append
        p.notify_widget(7)
        assert a == [7] and b == [7]

    def test_no_callbacks_does_not_raise(self):
        p = make_param()
        p.notify_widget(1.0)  # should not raise

    def test_string_true_converted_to_bool(self):
        received = []
        p = make_param(param_type="bool")
        p.update_widget = received.append
        for truthy in ("true", "True", "TRUE", "on", "1"):
            p.notify_widget(truthy)
        assert all(v is True for v in received)

    def test_string_false_converted_to_bool(self):
        received = []
        p = make_param(param_type="bool")
        p.update_widget = received.append
        for falsy in ("false", "False", "FALSE", "off", "0"):
            p.notify_widget(falsy)
        assert all(v is False for v in received)

    def test_updates_current_value(self):
        p = make_param()
        p.notify_widget(99.9)
        assert p.current_value == 99.9


class TestNotifyReadout:
    def test_fires_callback(self):
        received = []
        p = make_param()
        p.update_readout = received.append
        p.notify_readout("hello")
        assert received == ["hello"]

    def test_updates_current_value(self):
        p = make_param()
        p.notify_readout("3.14")
        assert p.current_value == "3.14"


class TestNotifyReadoutRichParameter:
    def test_float_param_formatted(self):
        received = []
        p = make_param(param_type="float", unit="MHz")
        p.update_readout_rich = received.append
        p.notify_readout_rich_parameter(1.5)
        assert len(received) == 1
        assert "1.5000" in received[0]
        assert "MHz" in received[0]

    def test_invalid_value_returns_early_no_callback(self):
        received = []
        p = make_param(param_type="float")
        p.update_readout_rich = received.append
        p.notify_readout_rich_parameter("not_a_number")
        assert received == []

    def test_stable_flag_changes_color(self):
        received = []
        p = make_param(param_type="float")
        p.update_readout_rich = received.append

        p.stable = False
        p.notify_readout_rich_parameter(1.0)
        unstable_text = received[-1]

        p.stable = True
        p.notify_readout_rich_parameter(1.0)
        stable_text = received[-1]

        assert "#2ecc71" in stable_text
        assert "#2ecc71" not in unstable_text


# ---------------------------------------------------------------------------
# Scannable property
# ---------------------------------------------------------------------------

class TestScannable:
    @pytest.mark.parametrize("access,expected", [
        ("read", False),
        ("write", True),
        ("read_write", True),
        ("", False),
    ])
    def test_scannable(self, access, expected):
        p = make_param()
        p._access = access
        assert p.scannable is expected


# ---------------------------------------------------------------------------
# Payload format extraction
# ---------------------------------------------------------------------------

class TestFormatPayload:
    def test_plain_payload_passthrough(self):
        p = make_param()
        assert p.format_payload("42") == "42"

    def test_dict_payload_extracts_key(self):
        p = make_param(payload_format="('dict', 'temp')")
        payload = json.dumps({"temp": 23.5, "humidity": 60})
        assert p.format_payload(payload) == 23.5

    def test_dict_payload_missing_key_returns_current(self):
        p = make_param(payload_format="('dict', 'missing_key')")
        p.current_value = 0.0
        payload = json.dumps({"other": 1})
        result = p.format_payload(payload)
        assert result == p.current_value

    def test_list_payload_extracts_index(self):
        p = make_param(payload_format="('list', 0)")
        payload = json.dumps([10, 20, 30])
        assert p.format_payload(payload) == 10

    def test_list_payload_second_index(self):
        p = make_param(payload_format="('list', 2)")
        payload = json.dumps([10, 20, 30])
        assert p.format_payload(payload) == 30

    def test_list_payload_out_of_bounds_returns_raw(self):
        p = make_param(payload_format="('list', 99)")
        payload = json.dumps([1, 2])
        assert p.format_payload(payload) == payload

    def test_malformed_json_handled_gracefully(self):
        p = make_param(payload_format="('dict', 'key')")
        result = p.format_payload("{not valid json}")
        # Should not raise; returns the raw payload
        assert result is not None


# ---------------------------------------------------------------------------
# update_current_value
# ---------------------------------------------------------------------------

class TestUpdateCurrentValue:
    def test_set_and_get(self):
        p = make_param()
        p.update_current_value(3.14)
        assert p.current_value == 3.14

    def test_none_returns_current(self):
        p = make_param()
        p.current_value = 7.0
        result = p.update_current_value(None)
        assert result == 7.0
