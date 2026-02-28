import time
from collections import deque
from typing import List, Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QPushButton,
    QLabel,
    QScrollArea,
    QLineEdit
)
from src.gui.assets.csstyle import Style
from src.gui.assets.theme_manager import ThemeManager
from src.gui.devices.frontend.instrument_base import InstrumentBase, Parameter
from src.gui.widgets.qtgraph import Graph
from src.gui.widgets.noscrollcombobox import NSCB


class GraphBlock(QFrame):
    """
    A block containing a Graph, a ComboBox to select a parameter,
    and logic to track that parameter over time.
    """
    def __init__(self, instruments: List[InstrumentBase], parent_widget=None):
        super().__init__()
        self.instruments = instruments
        self.parent_widget = parent_widget
        self.current_param: Optional[Parameter] = None
        self.data_x = deque()
        self.data_y = deque()
        self.start_time = time.time()
        self.needs_redraw = False
        self.latest_value = 0.0

        self.active_hook_param = None
        self.active_original_callback = None
        self.max_window_seconds = 60
        self.paused = False
        self.init_ui()

        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._update_plot)
        self.render_timer.start(100) #Update rate 10Hz
        # self.cleanup_timer = QTimer()
        # self.cleanup_timer.timeout.connect(self._cleanup_data)
        # self.cleanup_timer.start(1000)

    def init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(self)

        controls_frame = QFrame()
        controls_frame.setFixedWidth(170)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        controls_layout.addWidget(QLabel("Sensor Parameter:"))
        self.combo = NSCB()
        self.combo.addItem("Select Parameter...")
        self._populate_combo()
        self.combo.currentIndexChanged.connect(self._on_param_selected)
        controls_layout.addWidget(self.combo)

        self.lbl_current_value = QLabel("Value: ---")
        controls_layout.addWidget(self.lbl_current_value)

        controls_layout.addSpacing(10)

        row = QHBoxLayout()

        label = QLabel("History (min):")
        row.addWidget(label)

        self.edit_window = QLineEdit()
        self.edit_window.setPlaceholderText("Minutes")
        self.edit_window.setText("1")
        self.edit_window.returnPressed.connect(self._on_window_changed)
        self.edit_window.editingFinished.connect(self._on_window_changed)
        row.addWidget(self.edit_window)

        controls_layout.addLayout(row)

        controls_layout.addSpacing(10)

        # Start
        self.btn_start = QPushButton("Start")
        self.btn_start.setStyleSheet(Style.Button.start)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_graph)
        controls_layout.addWidget(self.btn_start)

        # Stop
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setStyleSheet(Style.Button.stop)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_graph)
        controls_layout.addWidget(self.btn_stop)

        # Reset
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet(Style.Button.reset)
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_graph)
        controls_layout.addWidget(self.btn_reset)

        controls_layout.addStretch()

        # Delete Button
        self.btn_delete = QPushButton("Delete Live Update")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.clicked.connect(self.delete_block)
        controls_layout.addWidget(self.btn_delete)

        layout.addWidget(controls_frame)

        # Graph
        self.graph = Graph()
        #self.graph.setFixedHeight(300)
        #self.graph.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.graph.line_curve.setDownsampling(auto=True, method='peak')
        self.graph.line_curve.setClipToView(True)
        layout.addWidget(self.graph)

        self.apply_theme()

    def _populate_combo(self):
        """
        Fills the combobox with 'Instrument: Parameter' options.
        Filter logic:
        1. param.param_type == 'input'
        2. param name (or label) in updated_labels list.
        """
        updated_labels = [
            "frequency", "Frequency",
            "amplitude", "Amplitude",
            "count", "Count",
            "voltage", "Voltage",
            "current", "Current",
            "power", "Power",
            "temperature", "Temperature",
            "pressure", "Pressure",
            "reading", "Reading",
            "measured_frequency",
            "sigma", 'channel'
        ]

        for inst in self.instruments:
            for param in inst.get_all_params():
                if not 'read' in param._access:
                    continue

                p_name = param.name.lower() if param.name else ""
                p_label = param.label.lower() if param.label else ""

                is_allowed = False
                for ul in updated_labels:
                    if (ul.lower() in p_name) or (p_label and ul.lower() in p_label.lower()):
                        is_allowed = True
                        break

                if is_allowed:
                    label = f"{inst.nickname}: {param.label or param.name}"
                    self.combo.addItem(label, (inst, param))

    def _on_window_changed(self):
        txt = self.edit_window.text()
        try:
            minutes = float(txt)
            self.max_window_seconds = minutes * 60.0
            print(f"Graph window set to {minutes} minutes ({self.max_window_seconds}s)")
        except ValueError:
            pass

    def _on_param_selected(self, index):
        # DISCONNECT THE OLD PARAMETER FIRST!!!!!!!
        self._unhook_current_param()

        if index <= 0:
            self.current_param = None
            self.reset_graph()
            return

        data = self.combo.itemData(index)
        if not data:
            return

        inst, param = data
        self.current_param = param
        self.reset_graph()

        # SAVE THE ORIGINAL CALLBACK
        original_callback = getattr(param, 'update_current_value', None)

        # DEFINE THE INTERCEPTEUR -- change assocated function works like a decorateur
        def intercepteur(value=None):
            if value is not None:
                self._record_value(value)
            if original_callback:
                try:
                    return original_callback(value) #Si il y a une function a la base ca lexecute
                except Exception as e:
                    print(f"Error in original callback: {e}")

        # Change le function par intercepteur
        param.update_current_value = intercepteur

        # STORE ORIGINAL FONCTION ET HOOK POUR RESET LATER
        self.active_hook_param = param
        self.active_original_callback = original_callback

        # Update Plot Labels
        self.graph.getPlotItem().setTitle(f"{inst.name} - {param.label or param.name}")
        self.graph.getPlotItem().setLabel('left', param.label or param.name, units=param.unit)
        self.graph.getPlotItem().setLabel('bottom', 'Time', units='s')

    def _record_value(self, value):
        if self.paused:
            return

        t = time.time() - self.start_time
        try:
            val = float(value)
        except (ValueError, TypeError) as e:
            print(e)
            return

        self.data_x.append(t)
        self.data_y.append(val)
        self.latest_value = val
        self.needs_redraw = True # New data is available for render cycle

    def _update_plot(self):
        if self.needs_redraw and not self.paused:
            self.lbl_current_value.setText(f"Value: {self.latest_value:.6f}")
            try:
                self.graph.line_curve.setData(list(self.data_x), list(self.data_y))
                self.needs_redraw = False
                self._cleanup_data()
            except RuntimeError:
                pass


    def _cleanup_data(self):
        if not self.data_x:
            return

        current_t = time.time() - self.start_time
        limit_t = current_t - self.max_window_seconds

        while self.data_x and self.data_x[0] < limit_t:
            self.data_x.popleft()
            self.data_y.popleft()


    def start_graph(self):
        self.paused = False
        print("Graph Resumed")

    def stop_graph(self):
        self.paused = True
        print("Graph Paused")

    def reset_graph(self):
        self.data_x.clear()
        self.data_y.clear()
        self.graph.line_curve.setData([], [])
        self.graph.dot_curve.setData([], [])
        print("Graph Reset")

    def delete_block(self):
        self._unhook_current_param()

        if self.parent_widget:
            self.parent_widget.remove_graph_block(self)

    def _unhook_current_param(self):
        """Restores the original update_widget function for the previous parameter."""
        if self.active_hook_param is not None:
            self.active_hook_param.update_current_value = self.active_original_callback
            self.active_hook_param = None
            self.active_original_callback = None

    def apply_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme == "dark"

        if is_dark:
            self.setStyleSheet(Style.Frame.container_dark)
            self.combo.setStyleSheet(Style.ComboBox.dark)
            self.lbl_current_value.setStyleSheet(Style.Label.title_dark)
            self.edit_window.setStyleSheet(Style.Input.line_edit_dark)
            self.btn_delete.setStyleSheet(Style.Button.simple_dark)
        else:
            self.setStyleSheet(Style.Frame.container_light)
            self.combo.setStyleSheet(Style.ComboBox.light)
            self.lbl_current_value.setStyleSheet(Style.Label.title_light)
            self.edit_window.setStyleSheet(Style.Input.line_edit_light)
            self.btn_delete.setStyleSheet(Style.Button.simple_light)


class LiveUpdateWidget(QWidget):
    def __init__(self, instruments: List[InstrumentBase]):
        super().__init__()
        self.instruments = instruments

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.main_frame = QFrame()
        root_layout.addWidget(self.main_frame)

        self.layout = QVBoxLayout(self.main_frame)
        self.layout.setContentsMargins(0, 0, 10, 10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet(Style.Scroll.transparent)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)

        self.layout.addWidget(self.scroll_area)

        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        self.btn_add = QPushButton("Add Live Update")
        self.btn_add.setStyleSheet(Style.Button.suggested)
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self.add_graph_block)

        bottom_bar.addWidget(self.btn_add)

        self.layout.addLayout(bottom_bar)

        self.add_graph_block()

        self.apply_theme()

    def add_graph_block(self):
        block = GraphBlock(self.instruments, parent_widget=self)
        self.scroll_layout.addWidget(block)
        if hasattr(block, 'apply_theme'):
             block.apply_theme()

    def remove_graph_block(self, block: GraphBlock):
        self.scroll_layout.removeWidget(block)
        block.deleteLater()

    def apply_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme == "dark"

        if is_dark:
             self.main_frame.setStyleSheet(Style.Frame.content_dark)
        else:
             self.main_frame.setStyleSheet(Style.Frame.content_light)

        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'apply_theme'):
                    widget.apply_theme()
