import os
import yaml
from functools import partial
import ast, re
from src.gui.devices.frontend.instrument_base import InstrumentBase, Parameter
from src.gui.devices.frontend.universal_mqtt import UniversalMqttDevice

BROKER = None
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
        self.special = device_config.get('special_device', None)
        self.driver = None
        self.nickname = device_config.get('nickname', None)
        self.id = device_config.get('id', None)
        self.setpoint = None

        self._status_map = {}
        self._command_map = {}
        self._stability_link_map = {} # Maps stability channel name -> base channel Parameter

        for channel in device_config.get('channels', []):
            self._add_yaml_channel(channel)

        self.connect_instrument()
        self._build_suffix_maps()

    def _build_suffix_maps(self):
        """
        Pre-computes the parameter routing for O(1) MQTT lookups.
        Runs only once at startup.
        """
        self._status_map.clear()
        self._command_map.clear()
        self._stability_link_map.clear()

        for param in self.get_all_params():
            if hasattr(param, '_status_suffix') and param._status_suffix:
                if param._status_suffix not in self._status_map:
                    self._status_map[param._status_suffix] = []
                self._status_map[param._status_suffix].append(param)

            if hasattr(param, '_command_suffix') and param._command_suffix:
                self._command_map[param._command_suffix] = param

        for param in self.get_all_params():
            if hasattr(param, 'special_channel') and param.special_channel:
                if getattr(param, 'coupling_type', None) == 'stability':
                    base_channel_name = getattr(param, 'coupled_channel', None)
                    if not base_channel_name:
                        continue

                    if base_channel_name == 'self':
                        param.ui_type = 'stability_indicator'
                    else:
                        param.ui_type = 'hidden'
                        for p in self.get_all_params():
                            if p.name == base_channel_name:
                                self._stability_link_map[param.name] = p
                                break

        print(f"Mapped {len(self._status_map)} status topics (some shared), {len(self._command_map)} command topics, and {len(self._stability_link_map)} stability links for fast routing.")

    def _add_yaml_channel(self, chan_config):
        key = chan_config.get('key')
        label = chan_config.get('label', key)
        p_type = chan_config.get('type', 'str')
        unit = chan_config.get('unit', '')
        access = chan_config.get('access', 'read_write')
        payload_format = chan_config.get('mqtt_payload_format', None)
        special = chan_config.get('special_channel', None)
        passive_toggle_parameters = chan_config.get('passive_toggle_parameters', None)

        internal_ptype = 'str'
        if p_type == 'integer':
            internal_ptype = 'int'
        elif p_type == 'float':
            internal_ptype = 'float'
        elif p_type == 'boolean':
            internal_ptype = 'bool'

        setter, ui_type = None, False
        cmd_suffix = chan_config.get('command_suffix')
        if access == 'read':
            ui_type = 'input'
        if self.special == "wavemeter":
            ui_type = 'wm_freq'
        if access in ['read_write', 'write'] and cmd_suffix:
            setter = partial(self.set_value_wrapper, cmd_suffix)

        param = Parameter(
            name=key,
            label=label,
            param_type=internal_ptype,
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
        if ui_type:
            param.ui_type = ui_type
        if special:
            param.special_channel = special
            try:
                param.coupling_type, param.coupled_channel = ast.literal_eval(special)
            except Exception as e:
                print(f"[{self.name}] Could not parse special_channel '{special}' for '{key}': {e}")
        if passive_toggle_parameters:
            try:
                parsed_val = ast.literal_eval(passive_toggle_parameters)
                if not isinstance(parsed_val, list):
                    raise ValueError(f"Expected a list, got {type(parsed_val).__name__}")
                if len(parsed_val) < 4:
                    parsed_val.extend([None] * (4 - len(parsed_val)))
                elif len(parsed_val) > 4:
                    parsed_val = parsed_val[:4]
                color_regex = re.compile(r"^rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[0-9.]+\s*\)$",re.IGNORECASE)
                for i, item in enumerate(parsed_val):
                    if item is not None:
                        if not isinstance(item, str):
                            raise ValueError(f"Element at index {i} must be a string or None")
                        if i >= 2:
                            if not color_regex.match(item.strip()):
                                raise ValueError(
                                    f"Element at index {i} must match 'rgb(r,g,b,alpha)' format, got '{item}'")
                param.passive_toggle_parameters = parsed_val

            except Exception as e:
                print(f"[{self.name}] Could not parse special_channel '{passive_toggle_parameters}' for '{key}': {e}")

        if p_type == 'ui_sep':self.add_parameter(Parameter(name = param.name, ui_type = 'ui_sep', label = '', param_type = 'ui_sep'))
        else: self.add_parameter(param)

    def connect_instrument(self):
        if not self.mqtt_base:
            return

        print(f"[{self.name}] Connecting to MQTT: {self.mqtt_base}")

        try:
            self.driver = UniversalMqttDevice(self.mqtt_base, broker_address=BROKER)
            for param in self.get_all_params():
                if hasattr(param, '_status_suffix') and param._status_suffix:
                    self.driver.subscribe_param(param._status_suffix)

            self.driver.message_received_signal.connect(self.on_mqtt_message)

        except Exception as e:
            print(f"[{self.name}] Connection failed: {e}")

    def set_value_wrapper(self, suffix, value):
        if self.driver:
            # O(1) dictionary lookup instead of looping through all parameters
            param = self._command_map.get(suffix)

            if param:
                if param.ui_type == 'wm_freq':
                    self.setpoint = value
                    if hasattr(param, 'notify_readout_rich_freq'):
                        param.notify_readout_rich_freq(param.update_current_value(), stable=param.stable)

            self.driver.publish_param(suffix, value)

    def on_mqtt_message(self, suffix, payload):
        params = self._status_map.get(suffix)
        if not params:
            return

        for param in params:
            param_payload = payload
            if param.payload_format:
                param_payload = param.format_payload(payload)

            # Parse boolean payload early — covers bool params AND stability indicators
            if param.param_type == 'bool' or param.ui_type in ('stability_indicator', 'hidden'):
                if isinstance(param_payload, str):
                    bool_payload = param_payload.lower() in ['true', 'on', '1']
                else:
                    bool_payload = bool(param_payload)
                param_payload = bool_payload

            # If this is a linked stability channel, update the base param's .stable flag
            if param.name in self._stability_link_map:
                base_param = self._stability_link_map[param.name]
                base_param.stable = bool(param_payload)
                param.stable = bool(param_payload)
                if base_param.ui_type == 'wm_freq' and hasattr(base_param, 'notify_readout_rich_freq'):
                    base_param.notify_readout_rich_freq(base_param.current_value, stable=base_param.stable)
                elif hasattr(base_param, 'notify_readout_rich_parameter'):
                    base_param.notify_readout_rich_parameter(base_param.current_value)
                continue  # Use 'continue' instead of 'return' to process other shared channels

            if param.ui_type == 'stability_indicator':
                if hasattr(param, 'notify_widget'):
                    param.notify_widget(param_payload)

            elif param.ui_type == 'wm_freq':
                try:
                    val = float(param_payload)
                except (ValueError, TypeError):
                    val = 0.0
                if hasattr(param, 'notify_readout_rich_freq'):
                    param.notify_readout_rich_freq(val, stable=param.stable)

            elif param.param_type == 'bool':
                if hasattr(param, 'notify_widget'):
                    param.notify_widget(param_payload)

            else:
                if hasattr(param, 'notify_readout_rich_parameter'):
                    param.notify_readout_rich_parameter(param_payload)


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