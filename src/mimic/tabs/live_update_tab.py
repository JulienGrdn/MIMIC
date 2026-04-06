import logging
import time
import numpy as np

logger = logging.getLogger(__name__)
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
from mimic.assets.csstyle import Style, HTMLValueFormatter
from mimic.assets.theme_manager import ThemeManager
from mimic.devices.frontend.instrument_base import InstrumentBase, Parameter
from mimic.widgets.qtgraph import Graph
from mimic.widgets.noscrollcombobox import NSCB
import math

_LOG_MS_MIN = math.log(16)      # 60 Hz
_LOG_MS_MAX = math.log(1000)    # 1 Hz
_LOG_S_MIN = math.log(6)        # 0.1 min
_LOG_S_MAX = math.log(3600)     # 60 min
_SLOPE = (_LOG_MS_MAX - _LOG_MS_MIN) / (_LOG_S_MAX - _LOG_S_MIN)  # ~0.647


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

        # numpy pre-allocated ring buffer
        self._buf_size = 100_000
        self._buf_x = np.empty(self._buf_size, dtype=np.float64)
        self._buf_y = np.empty(self._buf_size, dtype=np.float64)
        self._buf_head = 0
        self._buf_count = 0

        self.start_time = time.time()
        self.needs_redraw = False
        self.latest_value = 0.0
        self.live_value_label_format = None

        self.active_hook_param = None
        self.active_original_callback = None
        self._timestamp_hook_param = None
        self._timestamp_original_callback = None
        self._latest_timestamp_x: float | None = None
        self.max_window_seconds = 60
        self.paused = False
        self.init_ui()

        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._update_plot)
        # self.render_timer.start(33) #Update rate ~30Hz

        # self.cleanup_timer = QTimer()
        # self.cleanup_timer.timeout.connect(self._cleanup_data)
        # self.cleanup_timer.start(1000)

    def init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(self)

        controls_frame = QFrame()
        controls_frame.setFixedWidth(200)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        controls_layout.addWidget(QLabel("Sensor Parameter:"))
        self.combo = NSCB()
        self.combo.addItem("Select Parameter...")
        self._populate_combo()
        self.combo.currentIndexChanged.connect(self._on_param_selected)
        controls_layout.addWidget(self.combo)

        self.lbl_current_value = QLabel("-")
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
            # Frequency-related
            "frequency", "Frequency", "freq", "Freq", "f", "measured_frequency",
            # Amplitude / signal
            "amplitude", "Amplitude", "amp", "Amp", "signal", "Signal",
            "intensity", "Intensity",
            # Counting / events
            "count", "Count", "counts", "Counts", "event_count", "Event_count",
            # Voltage / electrical
            "voltage", "Voltage", "volt", "Volt", "V","potential", "Potential",
            # Current
            "current", "Current", "ampere", "Ampere", "I",
            # Power / energy
            "power", "Power", "energy", "Energy", "watt", "Watt",
            # Temperature
            "temperature", "Temperature", "temp", "Temp", "T",
            # Pressure
            "pressure", "Pressure", "P",
            # Time-related
            "time", "Time", "timestamp", "Timestamp", "t",
            # Generic measurement labels
            "reading", "Reading", "measurement", "Measurement","value", "Value", "data", "Data",
            # Statistical terms
            "sigma", "Sigma", "std", "Std", "std_dev", "Std_dev","variance", "Variance", "mean", "Mean", "average", "Average",
            # Channels / indexing
            "channel", "Channel", "ch", "Ch", "index", "Index"
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
            if not self.paused:
                self.render_timer.start(self._adaptive_refresh_ms())
            logger.debug("Graph window set to %s min", minutes)
        except ValueError:
            pass

    def _on_param_selected(self, index):
        # DISCONNECT THE OLD PARAMETER FIRST
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
        self.stop_graph()
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
                    logger.exception("Error in original callback")

        # Change le function par intercepteur
        param.update_current_value = intercepteur

        # STORE ORIGINAL FONCTION ET HOOK POUR RESET LATER
        self.active_hook_param = param
        self.active_original_callback = original_callback

        self.live_value_label_format = HTMLValueFormatter(sig_digits=12, unit=param.unit)

        # Update Plot Labels
        self.graph.getPlotItem().setTitle(f"{inst.name} - {param.label or param.name}")
        self.graph.getPlotItem().setLabel('left', param.label or param.name, units=param.unit)
        self.graph.getPlotItem().setLabel('bottom', 'Time', units='s')

        # Hook a linked timestamp param if one exists, to update the X-axis label
        self._unhook_timestamp_param()
        timestamp_param = self._find_timestamp_param(inst, param)
        if timestamp_param is not None:
            ts_original = getattr(timestamp_param, 'update_current_value', None)

            def ts_intercepteur(value=None, _orig=ts_original):
                if value is not None:
                    try:
                        self._latest_timestamp_x = float(value)
                    except (ValueError, TypeError):
                        pass
                if _orig:
                    try:
                        return _orig(value)
                    except Exception:
                        logger.exception("Error in timestamp callback")

            timestamp_param.update_current_value = ts_intercepteur
            self._timestamp_hook_param = timestamp_param
            self._timestamp_original_callback = ts_original

        self.apply_theme()
        self.start_graph()

    def _record_value(self, value):
        if self.paused:
            return
        try:
            val = float(value)
        except (ValueError, TypeError) as e:
            logger.warning("Cannot record value %r: %s", value, e)
            return

        idx = self._buf_head % self._buf_size
        x = self._latest_timestamp_x if self._latest_timestamp_x is not None else time.time() - self.start_time
        self._buf_x[idx] = x
        self._buf_y[idx] = val
        self._buf_head += 1
        self._buf_count = min(self._buf_count + 1, self._buf_size)

        self.latest_value = val
        self.needs_redraw = True

    def _update_plot(self):
        if not self.needs_redraw:
            return

        self.lbl_current_value.setText(self.live_value_label_format.get_html(self.latest_value))

        try:
            x, y = self._visible_arrays()
            self.graph.line_curve.setData(x, y)
            self.needs_redraw = False
        except RuntimeError:
            pass

    def _visible_arrays(self):
        """
        Single pass: trims the ring buffer to the current time window
        (advancing the logical tail) and returns chronological numpy
        views ready for pyqtgraph. No extra copies.
        """
        if self._buf_count == 0:
            return np.empty(0), np.empty(0)

        indices = np.arange(self._buf_head - self._buf_count,
                            self._buf_head) % self._buf_size
        x_all = self._buf_x[indices]
        y_all = self._buf_y[indices]

        cutoff = x_all[-1] - self.max_window_seconds
        n_drop = int(np.searchsorted(x_all, cutoff, side='right'))
        self._buf_count = max(0, self._buf_count - n_drop)

        return x_all[n_drop:], y_all[n_drop:]

    def _adaptive_refresh_ms(self) -> int:
        if self.max_window_seconds is None: return 100
        s = max(6.0, self.max_window_seconds)  # clamp below at 0.1 min
        ms = math.exp(_LOG_MS_MIN + _SLOPE * (math.log(s) - _LOG_S_MIN))
        return int(max(16, min(ms, 1000)))

    def start_graph(self):
        self.paused = False
        self.render_timer.start(self._adaptive_refresh_ms())
        logger.debug("Graph resumed.")

    def stop_graph(self):
        self.paused = True
        self.render_timer.stop()
        logger.debug("Graph paused.")

    def reset_graph(self):
        self._buf_head  = 0
        self._buf_count = 0
        self.graph.line_curve.setData([], [])
        self.graph.dot_curve.setData([], [])
        logger.debug("Graph reset.")

    def delete_block(self):
        self.render_timer.stop()
        self._unhook_current_param()
        if self.parent_widget:
            self.parent_widget.remove_graph_block(self)

    def _find_timestamp_param(self, inst, param):
        for ts_name, related in getattr(inst, '_timestamp_link_map', {}).items():
            if related is param:
                return inst.parameters.get(ts_name)
        return None

    def _unhook_timestamp_param(self):
        if self._timestamp_hook_param is not None:
            self._timestamp_hook_param.update_current_value = self._timestamp_original_callback
            self._timestamp_hook_param = None
            self._timestamp_original_callback = None
        self._latest_timestamp_x = None

    def _unhook_current_param(self):
        self._unhook_timestamp_param()
        if self.active_hook_param is not None:
            self.active_hook_param.update_current_value = self.active_original_callback
            self.active_hook_param = None
            self.active_original_callback = None

    def apply_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme == "dark"

        if self.live_value_label_format:
            self.live_value_label_format.set_theme(is_dark=is_dark)
        if is_dark:
            self.setStyleSheet(Style.Frame.container_dark)
            self.combo.setStyleSheet(Style.ComboBox.dark)
            # self.lbl_current_value.setStyleSheet(Style.Label.live_value_big_dark)
            self.edit_window.setStyleSheet(Style.Input.line_edit_dark)
            self.btn_delete.setStyleSheet(Style.Button.simple_dark)
        else:
            self.setStyleSheet(Style.Frame.container_light)
            self.combo.setStyleSheet(Style.ComboBox.light)
            # self.lbl_current_value.setStyleSheet(Style.Label.live_value_big_light)
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