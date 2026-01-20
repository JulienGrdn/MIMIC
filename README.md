# MIMIC - MQTT Interface for Modular Instrument Control

MIMIC is a comprehensive GUI application designed for controlling and orchestrating scientific instruments via MQTT. It provides a flexible frontend interface to interact with devices, monitor their status, and send commands, acting as a centralized hub for laboratory operations and active hardware management.

## Features

- **Dynamic Device Configuration**: Easily add and configure new devices using a YAML configuration file.
- **MQTT Integration**: Seamless communication with devices over MQTT.
- **Real-time Monitoring**: Visualize device states and parameters in real-time.
- **Control Interface**: Send commands to devices directly from the GUI.
- **Simulation Mode**: Run the application with a mock backend for testing without a real MQTT broker.

## Installation

1.  **Clone the repository**:
    ```bash
    gh repo clone JulienGrdn/MIMIC
    ```

2.  **Create and activate a virtual environment** (Mandatory):
    ```bash
    python -m venv src/venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    src/venv/bin/python -m pip install -r requirements.txt
    ```

## Usage

### Running the Application
To launch the main application (requires a running MQTT broker):

```bash
src/venv/bin/python MIMIC.py
```

### Running in Simulation Mode
To explore the interface without a real MQTT broker, use the simulation script. This mode uses a mock backend to simulate device responses.

```bash
src/venv/bin/python example/run_simulation.py
```

## Configuration Guide: Adding a Device

MIMIC allows you to define devices dynamically using the `config/devices_configuration.yaml` file. This file uses a YAML structure to define device properties and their communication channels.

### Configuration Structure

The configuration file contains a list of `devices`. Each device requires the following fields:

-   `id`: A unique identifier for the device (string).
-   `name`: The display name of the device.
-   `nickname`: A short name or abbreviation.
-   `device_cat`: The category of the device (e.g., "Power Supply", "Sensor").
-   `mqtt_base_topic`: The root MQTT topic for the device.
-   `channels`: A list of parameters or channels associated with the device.

### Channel Properties

Each channel in the `channels` list can have the following properties:

-   `key`: A unique key for the channel.
-   `label`: The label displayed in the GUI.
-   `type`: The data type (`float`, `integer`, `boolean`, `str`).
-   `access`: The access mode (`read`, `write`, `read_write`).
-   `unit`: The unit of measurement (e.g., "V", "A").
-   `status_suffix`: The MQTT topic suffix for receiving status updates.
-   `command_suffix`: The MQTT topic suffix for sending commands.

### Example Configuration

Here is an example of how to add a "Dummy Power Supply" to your configuration:

```yaml
devices:
  - id: "dummy_power_supply"
    name: "Dummy Power Supply"
    nickname: "DPS"
    device_cat: "Power Supply"
    mqtt_base_topic: "powersupply/serial_number"

    channels:
      - key: "voltage_ch1"
        label: "Voltage (Ch1)"
        description: "Output voltage for Channel 1"
        type: "float"
        access: "read_write"
        unit: "V"
        status_suffix: "voltage/1"
        command_suffix: "SET/voltage/1"

      - key: "output_state_ch1"
        label: "Output Enable"
        type: "boolean"
        access: "read_write"
        status_suffix: "output/1"
        command_suffix: "SET/output/1"
```

In this example:
- The device listens for voltage updates on `powersupply/serial_number/voltage/1`.
- You can set the voltage by publishing to `powersupply/serial_number/SET/voltage/1`.


## Credits & Licensing

**License**: GNU General Public License v3.0 (GPLv3)

This project is licensed under the GPLv3 because it relies on **PyQt6**, which is a GPL-licensed library. As a result, this entire application is strictly open-source software under the copyleft terms of the GPLv3.

See the [LICENSE](LICENSE) file for the full text.

### Third-Party Libraries

*   **PyQt6**: GPL v3
*   **paho-mqtt**: EPL 2.0 / EDLC 1.0
*   **pyqtgraph**: MIT
*   **PyYAML**: MIT
