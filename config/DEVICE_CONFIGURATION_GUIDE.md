# MIMIC - Device Configuration Reference

This document is the complete reference for `config/devices_configuration.yaml`.
No Python code changes are needed to add, remove, or modify instruments - the YAML file alone drives everything.



## File Structure

```yaml
broker: "192.168.1.100"
virtual_lab: "ion_trap"

devices:
  - id: "my_device"
    ...
    channels:
      - key: "my_channel"
        ...
```



## Root-Level Parameters

These appear once at the top of the file, outside any device block.

| Parameter | Type | Required | Description                                                                                                                                                                        |
|---|---|---|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `broker` | string | Yes | Hostname or IP address of the MQTT broker (e.g. `"192.168.1.100"` or `"localhost"`).                                                                                               |
| `virtual_lab` | string | No | This string is used to separate instances that run through a same network but runs different divices. Set this string to use more than one instance of MIMIC over the same network |



## Device-Level Parameters

Each entry under `devices:` defines one instrument card in the UI.

| Parameter | Type | Required | Description                                                                                                                                                                            |
|---|---|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `id` | string | Yes | Unique machine-readable identifier for the device. Used internally to name the generated Python class. Must be unique across all devices. No spaces (use underscores).                 |
| `name` | string | Yes | Human-readable name shown as the device card title in the UI.                                                                                                                          |
| `nickname` | string | No | Short abbreviation displayed for compact UI views (e.g. `"DPS"`).                                                                                                                      |
| `device_cat` | string | No | Category label used for grouping/filtering devices in the UI (e.g. `"Power Supply"`, `"Sensor"`, `"Environment"`). Defaults to `"Uncategorized"` if omitted.                           |
| `mqtt_base_topic` | string | Yes | The base MQTT topic for this device. All channel suffixes are appended to this string.                            |
| `special_device` | string | No | Opt-in to a specialised rendering mode for the entire device. Currently only `"wavemeter"` is supported, which renders all channels as rich frequency readouts. |

### Example

```yaml
- id: "dummy_power_supply"
  name: "Dummy Power Supply"
  nickname: "DPS"
  device_cat: "Power Supply"
  mqtt_base_topic: "powersupply/sn42"
  channels:
    - ...
```



## Channel-Level Parameters

Each entry under `channels:` defines one parameter (row) inside a device card.

### Core Fields

| Parameter | Type | Required | Description |
|---|---|---|---|
| `key` | string | Yes | Unique identifier for the channel within this device. Used to link `special_channel` couplings. No spaces. |
| `label` | string | No | Display label shown next to the widget. Defaults to `key` if omitted. |
| `description` | string | No | Tooltip or descriptive text for the channel. Not currently rendered in the UI but useful for documentation. |
| `type` | string | Yes | Data type and rendering mode. See [Type Values](#type-values) below. |
| `access` | string | No | Controls which widgets are rendered. See [Access Values](#access-values) below. Defaults to `"read_write"`. |
| `unit` | string | No | Unit string appended to the displayed value (e.g. `"V"`, `"MHz"`, `"mbar"`). |

### MQTT Fields

| Parameter | Type | Required | Description |
|---|---|---|---|
| `status_suffix` | string | Conditional | MQTT topic suffix appended to `mqtt_base_topic` for **subscribing** (reading values). Required for any channel with `access: read` or `access: read_write`. Full topic = `mqtt_base_topic/status_suffix`. |
| `command_suffix` | string | Conditional | MQTT topic suffix appended to `mqtt_base_topic` for **publishing** (sending commands). Required for any channel with `access: write` or `access: read_write`. Full topic = `mqtt_base_topic/command_suffix`. |
| `mqtt_payload_format` | string | No | If your device publishes structured payloads (JSON dict or list), use this to extract a single value. See [Payload Formats](#payload-formats). |

### Special Behaviour Fields

| Parameter | Type | Required | Description |
|---|---|---|---|
| `special_channel` | string | No | Couples this channel to special UI behaviour. See [Special Channels](#special-channels). |
| `passive_toggle_parameters` | string | No | Customises the visual appearance of a boolean stability indicator. See [Customising Stability Badges](#customising-stability-badges). |



## Type Values

The `type` field controls both the data type used internally and the widget rendered.

| `type` value | Internal type | Widget rendered | Notes                                                                                                              |
|---|---------------|---|--------------------------------------------------------------------------------------------------------------------|
| `"float"` | `float`       | Numeric readout and/or line-edit input | Use for voltages, frequencies, temperatures, etc.                                                                  |
| `"integer"` | `int`         | Integer readout and/or line-edit input | Use for counts, RPM, relay indices, etc.                                                                           |
| `"boolean"` | `bool`        | Toggle button | Renders as an animated toggle.                                                                                     |
| `"str"` | `str`         | Text readout and/or line-edit input | Use for free-form strings (e.g. timestamps, status messages).                                                      |
| `"ui_sep"` | -             | Visual separator | Inserts a horizontal divider line in the device card. No MQTT interaction. Only `key` is required; all other fields are ignored. |

> **Note:** When `special_device: "wavemeter"` is set at the device level, all channels of type `"float"` or `"integer"` are rendered as rich wavemeter frequency readouts regardless of their individual `type` field.



## Access Values

The `access` field controls which widgets appear for a channel.

| `access` value | Subscribe (read) | Publish (write) | Typical widget |
|---|---|---|---|
| `"read"` | Yes | No | Readout label only (no user input) |
| `"write"` | No | Yes | Input widget only (no live readout) |
| `"read_write"` | Yes | Yes | Both readout and input widget |


## Payload Formats

By default, MIMIC expects the MQTT payload to be a plain scalar value (e.g. `"3.14"` or `"true"`). If your instrument publishes structured payloads, use `mqtt_payload_format` to extract a single value.

The value must be a Python tuple literal encoded as a string:

### Dictionary payload

```yaml
mqtt_payload_format: "('dict', 'key_name')"
```

Extracts `payload["key_name"]` from a JSON-like dict payload.

**Example:** If the broker publishes `{"voltage": 3.14, "timestamp": "2026-04-06T10:00:00"}` on the topic, two channels can share the same `status_suffix` and each extract their own key:

```yaml
- key: "voltage_ch1"
  status_suffix: "voltage/1"
  mqtt_payload_format: "('dict', 'voltage')"

- key: "voltage_ch1_timestamp"
  status_suffix: "voltage/1"
  mqtt_payload_format: "('dict', 'timestamp')"
  special_channel: "('timestamp', 'voltage_ch1')"
```

### List payload

```yaml
mqtt_payload_format: "('list', 1)"
```

Extracts `payload[1]` (zero-indexed) from a JSON array payload.

**Example:** If the broker publishes `[0.5, 1.2, 3.7]`:

```yaml
- key: "current_ch1"
  status_suffix: "current/1"
  mqtt_payload_format: "('list', 1)"   # extracts 1.2
```



## Special Channels

The `special_channel` field couples a channel to specialised UI behaviour. The value is always a two-element Python tuple literal encoded as a string: `"('coupling_type', 'target')"`.

### Stability Indicator - self

```yaml
special_channel: "('stability', 'self')"
```

This channel **is** the stability indicator. It must be of `type: "boolean"` and `access: "read"`. It is rendered as a coloured badge (e.g. green/red or blue/grey) directly on the device card. No separate readout is shown.

**Use case:** A device that publishes its own lock/stability state on a dedicated topic.

```yaml
- key: "locked"
  label: "Rb Lock Status"
  type: "boolean"
  access: "read"
  status_suffix: "lock"
  special_channel: "('stability', 'self')"
```

### Stability Indicator - coupled to another channel

```yaml
special_channel: "('stability', 'other_channel_key')"
```

This channel is **hidden** in the UI. Its boolean value drives the stability badge of the channel identified by `other_channel_key`. The base channel gains a coloured stability indicator without needing its own dedicated stability topic.

**Use case:** A device publishes a compound payload with both the measurement value and a stability flag under the same topic. Two channels share the same `status_suffix`; one extracts the value, the other extracts the flag and silently updates the first channel's badge.

```yaml
- key: "chnl2"
  label: "Channel 2"
  type: "float"
  access: "read_write"
  mqtt_payload_format: "('dict', 'freq')"
  status_suffix: "frequency/2"
  command_suffix: "SET/frequency/2"

- key: "wl_stable_chnl2"
  type: "boolean"
  access: "read"
  mqtt_payload_format: "('dict', 'stable')"
  status_suffix: "frequency/2"
  special_channel: "('stability', 'chnl2')"
```

### Timestamp Coupling

```yaml
special_channel: "('timestamp', 'other_channel_key')"
```

This channel's string value is stored as the **last-updated timestamp** of the channel identified by `other_channel_key`. The timestamp channel itself renders as a small text readout. Both channels must share the same `status_suffix` (or at least arrive in the same MQTT message via `mqtt_payload_format` extraction).

**Use case:** An instrument publishes both a measurement and its acquisition timestamp in the same payload.

```yaml
- key: "voltage_ch1"
  label: "Voltage (Ch1)"
  type: "float"
  access: "read_write"
  mqtt_payload_format: "('dict', 'voltage')"
  status_suffix: "voltage/1"
  command_suffix: "SET/voltage/1"

- key: "voltage_ch1_timestamp"
  label: "Timestamp V Chnl1"
  type: "str"
  access: "read"
  mqtt_payload_format: "('dict', 'timestamp')"
  status_suffix: "voltage/1"
  special_channel: "('timestamp', 'voltage_ch1')"
```



## Customising Stability Badges

By default, stability indicators use built-in colors (theme-dependent). You can override the labels and colors for a `('stability', 'self')` channel using `passive_toggle_parameters`:

```yaml
passive_toggle_parameters: "['locked', 'unlocked', 'rgba(70, 120, 250, 1)', 'rgba(130, 130, 130, 1)']"
```

The value is a Python list literal encoded as a string with exactly four elements:

| Index | Meaning | Example |
|---|---|---|
| `0` | Label when `true` (stable/on) | `"locked"` |
| `1` | Label when `false` (unstable/off) | `"unlocked"` |
| `2` | Badge color when `true` | `"rgba(70, 120, 250, 1)"` |
| `3` | Badge color when `false` | `"rgba(130, 130, 130, 1)"` |

Colors must be in `rgba(r, g, b, alpha)` or `rgb(r, g, b, alpha)` format. Any element can be `None` to fall back to the default.



## Full Annotated Example

```yaml
broker: "192.168.1.100"    # MQTT broker address
virtual_lab: "ion_trap"    # All topics become ion_trap/<mqtt_base_topic>/...

devices:

  # --- Multi-channel power supply ---
  - id: "dummy_power_supply"
    name: "Dummy Power Supply"
    nickname: "DPS"
    device_cat: "Power Supply"
    mqtt_base_topic: "powersupply/sn42"
    channels:

      # Read/write float: topic ion_trap/powersupply/sn42/voltage/1
      # Payload is a dict; extract key "voltage"
      - key: "voltage_ch1"
        label: "Voltage (Ch1)"
        type: "float"
        access: "read_write"
        unit: "V"
        mqtt_payload_format: "('dict', 'voltage')"
        status_suffix: "voltage/1"
        command_suffix: "SET/voltage/1"

      # Timestamp coupled to voltage_ch1; shares same topic, extracts "timestamp"
      - key: "voltage_ch1_timestamp"
        label: "Timestamp V Chnl1"
        type: "str"
        access: "read"
        mqtt_payload_format: "('dict', 'timestamp')"
        status_suffix: "voltage/1"
        special_channel: "('timestamp', 'voltage_ch1')"

      # Boolean toggle: read/write
      - key: "output_state_ch1"
        label: "Output Enable"
        type: "boolean"
        access: "read_write"
        status_suffix: "output/1"
        command_suffix: "SET/output/1"

      # Visual separator - no MQTT
      - key: "sep1"
        type: "ui_sep"

      # Write-only float (no status topic needed)
      - key: "pulse_width"
        label: "Pulse Width"
        type: "float"
        access: "write"
        unit: "ms"
        command_suffix: "SET/pulse"

  # --- Laser lock system with self-stability indicator ---
  - id: "laser_lock"
    name: "Laser Locking System"
    nickname: "LLS"
    device_cat: "Sensor"
    mqtt_base_topic: "LLS/sn01"
    channels:

      - key: "locksetpoint"
        label: "Lock Setpoint"
        type: "float"
        access: "write"
        unit: "THz"
        command_suffix: "SET/frequency/1"

      # Stability indicator rendered as a badge; custom labels and colors
      - key: "stab_chnl_locksetpoint"
        label: "Locked"
        type: "boolean"
        access: "read"
        status_suffix: "stab"
        special_channel: "('stability', 'self')"
        passive_toggle_parameters: "['locked', 'unlocked', 'rgba(70, 120, 250, 1)', 'rgba(130, 130, 130, 1)']"

  # --- Wavemeter with per-channel stability coupling ---
  - id: "dummy_wavemeter"
    name: "Dummy Wavemeter"
    nickname: "DWM"
    device_cat: "Sensor"
    special_device: "wavemeter"          # All channels rendered as rich frequency readouts
    mqtt_base_topic: "DWM/sn01"
    channels:

      - key: "chnl2"
        label: "Channel 2"
        type: "float"
        access: "read_write"
        unit: "THz"
        mqtt_payload_format: "('dict', 'freq')"
        status_suffix: "frequency/2"
        command_suffix: "SET/frequency/2"

      # Hidden channel: drives the stability badge of chnl2
      - key: "wl_stable_chnl2"
        type: "boolean"
        access: "read"
        mqtt_payload_format: "('dict', 'stable')"
        status_suffix: "frequency/2"
        special_channel: "('stability', 'chnl2')"
```



## Quick-Reference Summary

```
Root
├── broker           required  MQTT broker hostname or IP
└── virtual_lab      optional  Topic namespace prefix

Device
├── id               required  Unique machine ID (no spaces)
├── name             required  Display name in UI
├── nickname         optional  Short badge label
├── device_cat       optional  Category for grouping
├── mqtt_base_topic  required  Base MQTT topic
└── special_device   optional  "wavemeter" for rich freq display

Channel
├── key              required  Unique ID within device
├── label            optional  Display label
├── description      optional  Tooltip / documentation note
├── type             required  float | integer | boolean | str | ui_sep
├── access           optional  read | write | read_write  (default: read_write)
├── unit             optional  Display unit string
├── status_suffix    cond.     Subscribe topic suffix (needed for read/read_write)
├── command_suffix   cond.     Publish topic suffix (needed for write/read_write)
├── mqtt_payload_format  opt.  ('dict','key') | ('list', index)
├── special_channel  optional  ('stability','self') | ('stability','key') | ('timestamp','key')
└── passive_toggle_parameters  optional  ['true_label','false_label','rgba(...)','rgba(...)']
```
