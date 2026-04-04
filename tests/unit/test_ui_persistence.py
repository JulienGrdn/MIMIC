"""Tests for UI state JSON persistence (round-trip, missing file, malformed input)."""
import json
import os
import pytest


# ---------------------------------------------------------------------------
# Helpers — exercise the same JSON logic used by MainWindow.save/load_ui_state
# without spinning up the full Qt window.
# ---------------------------------------------------------------------------

def write_ui_state(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=4)


def read_ui_state(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------

class TestJsonRoundTrip:
    def test_string_values(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        state = {"lineedit_host": "192.168.1.1", "lineedit_port": "1883"}
        write_ui_state(path, state)
        assert read_ui_state(path) == state

    def test_integer_values(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        state = {"combobox_mode": 2, "combobox_channel": 0}
        write_ui_state(path, state)
        assert read_ui_state(path) == state

    def test_boolean_values(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        state = {"checkbox_dark_mode": True, "checkbox_follow_system": False}
        write_ui_state(path, state)
        assert read_ui_state(path) == state

    def test_mixed_types(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        state = {
            "lineedit_broker": "localhost",
            "combobox_scan_axis": 1,
            "settings_dark_mode": True,
        }
        write_ui_state(path, state)
        assert read_ui_state(path) == state

    def test_empty_state(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        write_ui_state(path, {})
        assert read_ui_state(path) == {}

    def test_file_is_valid_json(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        state = {"key": "value"}
        write_ui_state(path, state)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == state


# ---------------------------------------------------------------------------
# Missing / malformed file handling
# ---------------------------------------------------------------------------

class TestMissingOrBrokenFile:
    def test_missing_file_returns_empty_dict(self, tmp_path):
        path = str(tmp_path / "config" / "nonexistent.json")
        assert read_ui_state(path) == {}

    def test_malformed_json_returns_empty_dict(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("{this is not valid json")
        assert read_ui_state(path) == {}

    def test_empty_file_returns_empty_dict(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()
        assert read_ui_state(path) == {}

    def test_partial_json_returns_empty_dict(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write('{"key": "val"')  # missing closing brace
        assert read_ui_state(path) == {}


# ---------------------------------------------------------------------------
# Idempotency — write then overwrite
# ---------------------------------------------------------------------------

class TestOverwrite:
    def test_second_write_overwrites_first(self, tmp_path):
        path = str(tmp_path / "config" / "ui_parameters.json")
        write_ui_state(path, {"a": 1})
        write_ui_state(path, {"b": 2})
        assert read_ui_state(path) == {"b": 2}

    def test_parent_dirs_created_automatically(self, tmp_path):
        path = str(tmp_path / "deep" / "nested" / "ui_parameters.json")
        state = {"x": "y"}
        write_ui_state(path, state)
        assert read_ui_state(path) == state
