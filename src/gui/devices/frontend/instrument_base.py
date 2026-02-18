from dataclasses import dataclass
from typing import Callable, Any, Optional, Iterable
from PyQt6.QtCore import QObject

@dataclass
class Parameter:
    name: str
    label: str
    param_type: str
    set_cmd: Optional[Callable[[Any], None]] = None
    get_cmd: Optional[Callable[[], Any]] = None
    unit: str = ""
    nickname: str = ""
    _access: str = ""
    payload_format: Optional[Iterable[tuple]] = None
    payload_type: Optional[str] = None
    payload_value_location: Optional = None

    update_widgets: list[Callable[[Any], None]] = None
    update_widget_styles: list[Callable[[str], None]] = None
    update_readouts: list[Callable[[str], None]] = None
    update_readout_styles: list[Callable[[str], None]] = None
    update_readout_richs: list[Callable[[str], None]] = None

    current_value: float = 0.0
    stable: bool = False

    def __post_init__(self):
        if self.payload_format: self.payload_type, self.payload_value_location = eval(self.payload_format)

    @property
    def update_widget(self):
        return self.update_widgets[0] if(self.update_widgets and len(self.update_widgets)>0) else None
    @update_widget.setter
    def update_widget(self, value):
        if self.update_widgets is None: self.update_widgets = []
        self.update_widgets.append(value)

    @property
    def update_widget_style(self):
        return self.update_widget_styles[0] if(self.update_widget_styles and len(self.update_widget_styles)>0) else None
    @update_widget_style.setter
    def update_widget_style(self, value):
        if self.update_widget_styles is None: self.update_widget_styles = []
        self.update_widget_styles.append(value)

    @property
    def update_readout(self):
        return self.update_readouts[0] if(self.update_readouts and len(self.update_readouts)>0) else None
    @update_readout.setter
    def update_readout(self, value):
        if self.update_readouts is None: self.update_readouts = []
        self.update_readouts.append(value)

    @property
    def update_readout_style(self):
        return self.update_readout_styles[0] if(self.update_readout_styles and len(self.update_readout_styles)>0) else None
    @update_readout_style.setter
    def update_readout_style(self, value):
        if self.update_readout_styles is None: self.update_readout_styles = []
        self.update_readout_styles.append(value)

    @property
    def update_readout_rich(self):
        return self.update_readout_richs[0] if(self.update_readout_richs and len(self.update_readout_richs)>0) else None
    @update_readout_rich.setter
    def update_readout_rich(self, value):
        if self.update_readout_richs is None: self.update_readout_richs = []
        self.update_readout_richs.append(value)

    def update_current_value(self, value = None):
        if value is None: return self.current_value
        else: self.current_value = value

    # Helper to call all observers
    def notify_widget(self, value):
        if isinstance(value, str):
            if value.lower() in ['true', 'on', '1']:
                value = True
            elif value.lower() in ['false', 'off', '0']:
                value = False
        #print(value, type(value))
        if self.update_widgets:
            for cb in self.update_widgets: cb(value)
        self.update_current_value(value)

    def notify_widget_style(self, value):
        if self.update_widget_styles:
            for cb in self.update_widget_styles: cb(value)
        self.update_current_value(value)

    def notify_readout(self, value):
        if self.update_readouts:
            for cb in self.update_readouts: cb(value)
        self.update_current_value(value)

    def notify_readout_style(self, value):
        if self.update_readout_styles:
            for cb in self.update_readout_styles: cb(value)
        self.update_current_value(value)

    def notify_readout_rich_freq(self, value, stable=False):
        full_str = f"{float(value):.6f}"
        main_part = full_str[:-3]
        fine_part = full_str[-3:]

        color_style = "color: #2ecc71;" if stable else ""

        text = (
            f"<html>"
            f"<span style='{color_style}'>"
            f"{main_part}"
            f"<span style='font-size: 13pt;'>{fine_part}</span>"
            f"</span>"
            f" <span style='font-size: 13pt; color: #B9BBBE; font-weight: normal;'>THz</span>"
            f"</html>"
        )
        if self.update_readout_richs:
            for cb in self.update_readout_richs: cb(text)
        self.update_current_value(value)

    def notify_readout_rich_parameter(self, value):
        full_str = f"{float(value):.4f}" if self.param_type == 'float' else value
        text = (
            f"<html>"
            f"{full_str}"
            f" <span style='font-size: 13pt; color: #B9BBBE; font-weight: normal;'>{self.unit}</span>"
            f"</html>"
        )
        if self.update_readout_richs:
            for cb in self.update_readout_richs: cb(text)
        self.update_current_value(value)

    @property
    def scannable(self) -> bool:
        return 'write' in self._access

    def format_payload(self, payload):
        if self.payload_type in ('list','dict'): return eval(payload)[self.payload_value_location]
        else: return payload

class InstrumentBase(QObject):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.parameters = {} # Dictionary to store params

    def add_parameter(self, param: Parameter):
        self.parameters[param.name] = param

    def connect_instrument(self):
        pass

    def get_all_params(self):
        return self.parameters.values()
