import sys
import importlib.util
from collections import defaultdict
from typing import List, Optional
from PyQt6.QtCore import Qt
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
from src.gui.assets.csstyle import Style
from src.gui.assets.theme_manager import ThemeManager
from src.gui.devices.frontend.instrument_base import InstrumentBase, Parameter
from src.gui.widgets.smaller_toggle import AnimatedToggle
from src.gui.widgets.flow_layout import FlowLayout
from src.gui.assets.instance_state import InstanceState
from src.gui.widgets.popups import Popups

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

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(280)

        self._init_header()

        for param in self.instrument.get_all_params():
            self._add_parameter_row(param)

        self.apply_theme()

    def _init_header(self):
        """Creates the bold title and horizontal divider line."""
        title = QLabel(self.instrument.name)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.styled_widgets.append((title, "Label.title"))
        self.layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)

    def _add_parameter_row(self, param: Parameter):
        """Creates a labeled row with an input widget (Toggle or LineEdit)."""
        row_layout = QHBoxLayout()
        if param.label is not None:
            label = QLabel(f"{param.label}:")
            row_layout.addWidget(label)

        input_widget = self._create_input_widget(param, row_layout)
        if param.param_type != "bool" and param.param_type != 'input':  # a bit messy this func
            btn = QPushButton("Send")
            btn.setStyleSheet(Style.Button.suggested)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: self.send_command(param, input_widget.text()))
            row_layout.addWidget(btn)

            if "read" in param._access:
                readout_label = QLabel("--")
                if param.param_type == 'wm_freq':
                    style_key = "Label.frequency_big"
                else:
                    style_key = "Label.parameter"

                self.styled_widgets.append((readout_label, style_key))
                self.layout.addWidget(readout_label)

                if hasattr(param, 'update_readout'):
                    param.update_readout = readout_label.setText
                if hasattr(param, 'update_readout_style'):
                    param.update_readout_style = readout_label.setStyleSheet
                if hasattr(param, 'update_readout_rich'):
                    param.update_readout_rich = readout_label.setText

        self.layout.addLayout(row_layout)

    def _create_input_widget(self, param: Parameter, parent_layout: QHBoxLayout):
        """Helper to create the correct widget type."""
        if param.param_type == "bool":
            widget = AnimatedToggle()
            widget.toggled.connect(lambda state: self.send_command(param, state))
            parent_layout.addWidget(widget)
            if hasattr(param, 'update_widget'):
                param.update_widget = widget.set_state

            return widget

        elif param.param_type in ["float", "int", "str", 'wm_freq']:
            widget = QLineEdit()
            widget.setObjectName(f"inst_{self.instrument.id}_{param.name}")
            self.styled_widgets.append((widget, "Input.line_edit"))
            widget.setPlaceholderText(str(param.unit))
            parent_layout.addWidget(widget)
            if hasattr(param, 'update_widget'):
                param.update_widget = widget.setText
            return widget

        elif param.param_type == 'input':
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
                print(f"[{self.instrument.name}] Set {param.name} = {value}")

        except ValueError:
            print(f"[{self.instrument.name}] Error: Invalid input for {param.name}")


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
            yml_module = importlib.import_module("src.gui.devices.yaml_plugin")
            for attr_name in dir(yml_module):
                attr = getattr(yml_module, attr_name)
                if (isinstance(attr, type) and
                        issubclass(attr, InstrumentBase) and
                        attr is not InstrumentBase and
                        attr.__name__ != "GenericYamlDevice"):
                    try:
                        inst_obj = attr()
                        loaded.append(inst_obj)
                        print(f">> [InstrumentPanel] Successfully loaded {attr_name}")
                    except Exception as e:
                        print(f">> [InstrumentPanel] Failed to instantiate {attr_name}: {e}")

        except ImportError as e:
            print(f">> [InstrumentPanel] Could not find module: {e}")
        except Exception as e:
            print(f">> [InstrumentPanel] Critical error loading yaml_plugin: {e}")

        finally:
            sys.modules.pop("src.gui.devices.yaml_plugin", None)
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