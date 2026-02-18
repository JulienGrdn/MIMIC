import os
import yaml
import math
from collections import deque
from functools import partial
from src.gui.devices.frontend.instrument_base import InstrumentBase, Parameter
from src.gui.devices.frontend.universal_mqtt import UniversalMqttDevice

BROKER = None
# CONFIG_PATH = 'example/devices_configuration.yaml' #For test with fake backend
CONFIG_PATH = 'config/devices_configuration.yaml'

def load_yaml_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Config file not found at {CONFIG_PATH}")
        return {}
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


class GenericYamlDevice(InstrumentBase):
    def __init__(self, device_config):
        name = device_config.get('name', 'Unknown Device')
        super().__init__(name)
        self.broker = device_config.get('broker', '')
        self.config = device_config
        self.category = device_config.get('device_cat', 'Uncategorized')
        self.mqtt_base = device_config.get('mqtt_base_topic', '')
        self.driver = None
        self.nickname = device_config.get('nickname', None)
        self.id = device_config.get('id', None)
        self.setpoint = None

        # Storage for Wavemeter stability analysis
        self.wm_history = {}      # param.name -> deque of recent values
        self.wm_stds = {}         # param.name -> last calculated std
        self.wm_last_values = {}  # param.name -> last received value

        for channel in device_config.get('channels', []):
            self._add_yaml_channel(channel)

        self.connect_instrument()

    def _add_yaml_channel(self, chan_config):
        key = chan_config.get('key')
        label = chan_config.get('label', key)
        p_type = chan_config.get('type', 'str')
        unit = chan_config.get('unit', '')
        access = chan_config.get('access', 'read_write')
        payload_format = chan_config.get('mqtt_payload_format', None)

        internal_type = 'str'
        if p_type == 'integer': internal_type = 'int'
        elif p_type == 'float': internal_type = 'float'
        elif p_type == 'boolean': internal_type = 'bool'

        setter = None
        cmd_suffix = chan_config.get('command_suffix')
        ui_type = internal_type
        if access == 'read':
            ui_type = 'input'
        if 'WM' in  self.mqtt_base:
            ui_type = 'wm_freq'
        if access in ['read_write', 'write'] and cmd_suffix:
            setter = partial(self.set_value_wrapper, cmd_suffix)

        param = Parameter(
            name=key,
            label=label,
            param_type=ui_type,
            unit=unit,
            set_cmd=setter,
            get_cmd=None,
            payload_format=payload_format
        )

        status_suffix = chan_config.get('status_suffix')
        command_suffix = chan_config.get('command_suffix')
        if status_suffix:
            param._status_suffix = status_suffix
        if command_suffix:
            param._command_suffix = command_suffix
        if access:
            param._access = access

        self.add_parameter(param)

    def connect_instrument(self):
        if not self.mqtt_base:
            return

        print(f"[{self.name}] Connecting to MQTT: {self.mqtt_base}")

        try:
            self.driver = UniversalMqttDevice(self.mqtt_base, broker_address=BROKER)
            for param in self.get_all_params():
                if hasattr(param, '_status_suffix') and param._status_suffix:
                    #print(param._status_suffix)
                    self.driver.subscribe_param(param._status_suffix)

            self.driver.message_received_signal.connect(self.on_mqtt_message)
            self.driver.mqtt.start()

        except Exception as e:
            print(f"[{self.name}] Connection failed: {e}")

    def set_value_wrapper(self, suffix, value):
        if self.driver:
            for param in self.get_all_params():
                if hasattr(param, '_command_suffix') and param._command_suffix == suffix:
                    if  'SET/frequency' in suffix:
                        self.setpoint = value
                        if hasattr(param, 'notify_readout_rich_freq'):
                            param.notify_readout_rich_freq(param.update_current_value(), stable=False)
                            self.wm_history[param.name] = deque(maxlen=10) #hardreset

            self.driver.publish_param(suffix, value)

    def on_mqtt_message(self, suffix, payload):
        for param in self.get_all_params():
            if hasattr(param, '_status_suffix') and param._status_suffix == suffix:
                if param.payload_format:
                    payload = param.format_payload(payload)

                if param.param_type == 'wm_freq':
                    try:
                        val = float(payload)
                    except ValueError:
                        val = 0.0

                    if param.name not in self.wm_history:
                        self.wm_history[param.name] = deque(maxlen=10)

                    self.wm_history[param.name].append(val)
                    self.wm_last_values[param.name] = val

                    hist = list(self.wm_history[param.name])
                    if len(hist) > 1:
                        avg = sum(hist) / len(hist)
                        variance = sum((x - avg) ** 2 for x in hist) / len(hist)
                        std = math.sqrt(variance)
                    else:
                        std = 1.0 # Default high std if insufficient data

                    self.wm_stds[param.name] = std

                    # Determine Stability Criteria
                    # Filter std values < 10 MHz (0.00001 THz)
                    threshold_thz = 0.00005
                    filtered_stds = [s for s in self.wm_stds.values() if s < threshold_thz]

                    if filtered_stds:
                        averaged_std = sum(filtered_stds) / len(filtered_stds)
                    else:
                        averaged_std = 0.0

                    p_std = self.wm_stds.get(param.name, 1.0)
                    if self.setpoint is not None: is_stable = p_std < averaged_std*2 and  val*1e6 in range(int((val-averaged_std*2)*1e6), int((val+averaged_std*2)*1e6))
                    else:is_stable = p_std < averaged_std*2

                    param.stable = is_stable

                    if hasattr(param, 'notify_readout_rich_freq'):
                        param.notify_readout_rich_freq(val, stable=is_stable)

                elif param.param_type == 'bool':
                    if hasattr(param, 'notify_widget'):
                        param.notify_widget(payload)

                # If param is read_write, update READOUT label
                else:
                    if hasattr(param, 'notify_readout'):
                        param.notify_readout_rich_parameter(payload)






config_data = load_yaml_config()
if config_data:
    BROKER = config_data.get('broker', '')
    for i, dev_conf in enumerate(config_data.get('devices', [])):
        dev_id = dev_conf.get('id')

        class_name = f"GenDevice_{dev_id}"

        def make_class(conf):
            class DynamicDevice(GenericYamlDevice):
                def __init__(self):
                    super().__init__(conf)
            return DynamicDevice

        vars()[class_name] = make_class(dev_conf)
