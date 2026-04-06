import logging
import sys
import importlib.util

logger = logging.getLogger(__name__)
from collections import defaultdict
from typing import List, Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QStackedWidget,
    QListWidgetItem
)
from mimic.assets.csstyle import Style
from mimic.assets.theme_manager import ThemeManager
from mimic.devices.frontend.instrument_base import InstrumentBase, Parameter
from mimic.widgets.smaller_toggle import AnimatedToggle
from mimic.widgets.flow_layout import FlowLayout
from mimic.assets.instance_state import InstanceState
from mimic.widgets.popups import Popups
from mimic.widgets.ui_line_separator import qframe_line_separator
from mimic.widgets.ui_passive_toggle import StabilityIndicator

class InstrumentFrame(QFrame):
    """
    A widget representing the controls for a single Instrument.
    Generates UI elements dynamically based on the instrument's parameters.
    """
    def __init__(self, instrument: InstrumentBase):
        super().__init__()
        self.instrument = instrument
        self.styled_widgets = []
        self.info_message = Popups()
        self._rate_labels: list = []

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(280)

        self._init_header()
        for param in self.instrument.get_all_params():
            if param.ui_type == 'ui_sep': self.layout.addWidget(qframe_line_separator())
            elif getattr(param, 'coupling_type', None) == 'timestamp': continue
            else:self._add_parameter_row(param)

        self._rate_timer = QTimer(self)
        self._rate_timer.timeout.connect(self._refresh_rate_labels)
        self._rate_timer.start(1000)

        self.apply_theme()

    def _init_header(self):
        title = QLabel(self.instrument.name)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.styled_widgets.append((title, "Label.title"))
        self.layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)

    def _add_parameter_row(self, param: Parameter):
        """Builds the UI row(s) for one parameter."""

        if param.ui_type == 'hidden':
            return

        if param.ui_type == 'input':
            if param.label is not None:
                title_lbl = QLabel(f"{param.label}")
                title_lbl.setObjectName(f"title_{id(param)}")
                self.styled_widgets.append((title_lbl, "Label.channel_title"))
                self.layout.addWidget(title_lbl)

            if param.param_type == 'bool':
                value_widget = QLabel("—")
                if hasattr(param, 'update_readout'):
                    param.update_readout = lambda val: value_widget.setText("ON" if val else "OFF")
                style_key = "Label.parameter"
            else:
                value_widget = QLabel("—")
                if hasattr(param, 'update_readout'):
                    param.update_readout = value_widget.setText
                if hasattr(param, 'update_readout_style'):
                    param.update_readout_style = value_widget.setStyleSheet
                if hasattr(param, 'update_readout_rich'):
                    param.update_readout_rich = value_widget.setText
                style_key = "Label.parameter"

            if style_key:
                self.styled_widgets.append((value_widget, style_key))

            rate_lbl = QLabel("")
            rate_lbl.setObjectName(f"rate_{id(param)}")
            self.styled_widgets.append((rate_lbl, "Label.rate"))
            self._rate_labels.append((param, rate_lbl))

            value_row = QHBoxLayout()
            value_row.addWidget(value_widget)
            value_row.addStretch()
            value_row.addWidget(rate_lbl)
            self.layout.addLayout(value_row)
            return

        row_layout = QHBoxLayout()
        if param.label is not None:
            row_layout.addWidget(QLabel(f"{param.label}:"))

        input_widget = self._create_input_widget(param, row_layout)

        if param.param_type != "bool" and param.ui_type != 'stability_indicator':
            btn = QPushButton("Send")
            btn.setStyleSheet(Style.Button.suggested)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            btn.clicked.connect(lambda _, p=param, w=input_widget: self.send_command(p, w.text()))
            row_layout.addWidget(btn)

        self.layout.addLayout(row_layout)

        if param.param_type != "bool" and "read" in param._access:
            readout_label = QLabel("--")
            style_key = "Label.frequency_big" if param.ui_type == 'wm_freq' else "Label.parameter"
            self.styled_widgets.append((readout_label, style_key))

            if hasattr(param, 'update_readout'):
                param.update_readout = readout_label.setText
            if hasattr(param, 'update_readout_style'):
                param.update_readout_style = readout_label.setStyleSheet
            if hasattr(param, 'update_readout_rich'):
                param.update_readout_rich = readout_label.setText

            rate_lbl = QLabel("")
            rate_lbl.setObjectName(f"rate_{id(param)}")
            self.styled_widgets.append((rate_lbl, "Label.rate"))
            self._rate_labels.append((param, rate_lbl))

            readout_row = QHBoxLayout()
            readout_row.addWidget(readout_label)
            readout_row.addStretch()
            readout_row.addWidget(rate_lbl)

            self.layout.addLayout(readout_row)

    def _create_input_widget(self, param: Parameter, parent_layout: QHBoxLayout):
        if param.ui_type == 'stability_indicator':
            if param.passive_toggle_parameters:
                widget = StabilityIndicator(None, *param.passive_toggle_parameters)
            else:
                widget = StabilityIndicator()
            parent_layout.addWidget(widget)
            if hasattr(param, 'update_widget'):
                param.update_widget = widget.set_state
            return widget

        elif param.param_type == "bool":
            widget = AnimatedToggle()
            widget.toggled.connect(lambda state: self.send_command(param, state))
            parent_layout.addWidget(widget)
            if hasattr(param, 'update_widget'):
                param.update_widget = widget.set_state
            return widget

        elif param.param_type in ["float", "int", "str"] or param.ui_type == 'wm_freq':
            widget = QLineEdit()
            widget.setObjectName(f"inst_{self.instrument.id}_{param.name}")
            self.styled_widgets.append((widget, "Input.line_edit"))
            widget.setPlaceholderText(str(param.unit))
            parent_layout.addWidget(widget)
            if hasattr(param, 'update_widget'):
                param.update_widget = widget.setText
            return widget

        elif param.ui_type == 'input':
            widget = QLabel("_")
            self.styled_widgets.append((widget, "Label.parameter"))
            parent_layout.addWidget(widget)
            if hasattr(param, 'update_widget'):
                param.update_readout_rich = widget.setText
            if hasattr(param, 'update_widget_style'):
                param.update_widget_style = widget.setStyleSheet
            return widget

        return QWidget()

    def send_command(self, param: Parameter, value):
        """
        Handles type conversion and execution of the instrument command.
        If this instance is a slave, shows an informational popup instead of sending.
        """
        if not InstanceState.is_master():
            self.info_message.read_only(self)
            return

        try:
            if param.param_type == "float":
                value = float(value)
            elif param.param_type == "int":
                value = int(value)

            if param.set_cmd:
                param.set_cmd(value)
                logger.debug("[%s] Set %s = %s", self.instrument.name, param.name, value)

        except ValueError:
            logger.warning("[%s] Invalid input for %s", self.instrument.name, param.name)

    def _refresh_rate_labels(self):
        for param, lbl in self._rate_labels:
            r = param.update_rate_ms
            if r <= 0:
                lbl.setText("")
            elif r < 1000:
                lbl.setText(f"<html>&#8635; {r:.0f} ms</html>")
            else:
                lbl.setText(f"<html>&#8635; {r / 1000:.1f} s</html>")

    def apply_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme == "dark"

        if is_dark:
            self.setStyleSheet(Style.Frame.container_dark)
        else:
            self.setStyleSheet(Style.Frame.container_light)

        for widget, style_key in self.styled_widgets:
            if style_key == "Label.title":
                widget.setStyleSheet(Style.Label.title_dark if is_dark else Style.Label.title_light)
            elif style_key == "Label.parameter":
                widget.setStyleSheet(Style.Label.parameter_dark if is_dark else Style.Label.parameter)
            elif style_key == "Label.frequency_big":
                widget.setStyleSheet(Style.Label.frequency_big_dark if is_dark else Style.Label.frequency_big)
            elif style_key == "Input.line_edit":
                widget.setStyleSheet(Style.Input.line_edit_dark if is_dark else Style.Input.line_edit_light)
            elif style_key == "Label.rate":
                color = "#555" if is_dark else "#aaa"
                widget.setStyleSheet(f"font-size: 8pt; color: {color}; font-style: italic;")
            elif style_key == "Label.channel_title":
                color = "#aaa" if is_dark else "#888"
                widget.setStyleSheet(
                    f"font-size: 8pt; color: {color}; letter-spacing: 0.5px; font-weight: bold; text-transform: uppercase;")


class InstrumentPanel(QWidget):
    """
    The Main Dashboard Panel.
    Specifically loads 'yaml_plugin.py' from the devices directory and
    arranges the resulting instruments in a categorized layout.
    """

    def __init__(self, devices_path: Optional[str] = None):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(130)
        self.sidebar.currentItemChanged.connect(self._on_category_changed)
        self.main_layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        self.content_stack.setContentsMargins(10, 10, 10, 10)
        self.main_layout.addWidget(self.content_stack)

        self.category_pages = {}
        self.loaded_instruments = []

        self._load_and_display_devices()

        if self.sidebar.count() > 0:
            self.sidebar.setCurrentRow(0)

        self.apply_theme()

    def _load_and_display_devices(self):
        """Loads the specific yaml_plugin.py and builds the UI."""
        self.loaded_instruments = self._import_yaml_instruments()
        self.sidebar.clear()
        grouped = defaultdict(list)

        for inst in self.loaded_instruments:
            cat = getattr(inst, 'category', 'Uncategorized')
            grouped[cat].append(inst)

        def category_sort_key(name):
            special_categories = ["Miscellaneous", "Divers", "Other", "Uncategorized"]
            priority = 1 if name in special_categories else 0
            return (priority, name)

        sorted_categories = sorted(grouped.keys(), key=category_sort_key)

        for category_name in sorted_categories:
            instruments = grouped[category_name]
            instruments.sort(key=lambda inst: inst.name)

            page_widget = QWidget()
            flow_layout = FlowLayout(page_widget, margin=10, spacing=10)

            for inst in instruments:
                frame = InstrumentFrame(inst)
                flow_layout.addWidget(frame)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page_widget)
            scroll.setFrameShape(QFrame.Shape.NoFrame)

            self.content_stack.addWidget(scroll)
            self.category_pages[category_name] = scroll
            self.sidebar.addItem(QListWidgetItem(category_name))

        self._create_all_devices_page()

    def _import_yaml_instruments(self) -> List[InstrumentBase]:
        """
        Targeted import: Looks specifically for 'yaml_plugin.py'
        and extracts instantiated instrument classes.
        """
        loaded = []

        try:
            yml_module = importlib.import_module("mimic.devices.yaml_plugin")
            for attr_name in dir(yml_module):
                attr = getattr(yml_module, attr_name)
                if (isinstance(attr, type) and
                        issubclass(attr, InstrumentBase) and
                        attr is not InstrumentBase and
                        attr.__name__ != "GenericYamlDevice"):
                    try:
                        inst_obj = attr()
                        loaded.append(inst_obj)
                        logger.info("Loaded instrument: %s", attr_name)
                    except Exception as e:
                        logger.exception("Failed to instantiate %s", attr_name)

        except ImportError as e:
            logger.exception("Could not find yaml_plugin module")
        except Exception as e:
            logger.exception("Critical error loading yaml_plugin")

        finally:
            sys.modules.pop("mimic.devices.yaml_plugin", None)
            if 'yml_module' in locals():
                del yml_module

        return loaded

    def _create_all_devices_page(self):
        """Creates a grid view of ALL loaded instruments."""
        page_widget = QWidget()
        grid_layout = FlowLayout(page_widget, margin=10, spacing=10)

        for inst in self.loaded_instruments:
            frame = InstrumentFrame(inst)
            grid_layout.addWidget(frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page_widget)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.content_stack.addWidget(scroll)
        self.category_pages["All Devices"] = scroll

        item = QListWidgetItem("All Devices")
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.sidebar.addItem(item)

    def _on_category_changed(self, current_item, previous_item):
        if not current_item:
            return
        category_name = current_item.text()
        if category_name in self.category_pages:
            widget = self.category_pages[category_name]
            self.content_stack.setCurrentWidget(widget)

    def apply_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme == "dark"

        if is_dark:
            self.setStyleSheet(Style.Default.dark)
            self.sidebar.setStyleSheet(Style.List.dark)
            self.content_stack.setStyleSheet(Style.Frame.content_dark)
        else:
            self.setStyleSheet(Style.Default.light)
            self.sidebar.setStyleSheet(Style.List.light)
            self.content_stack.setStyleSheet(Style.Frame.content_light)

        for scroll in self.category_pages.values():
            scroll.setStyleSheet(Style.Scroll.combined)

            page_widget = scroll.widget()
            if page_widget and page_widget.layout():
                layout = page_widget.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget():
                        frame = item.widget()
                        if hasattr(frame, 'apply_theme'):
                            frame.apply_theme()