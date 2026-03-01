import json
import os
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFrame, QGridLayout, QGroupBox,
    QScrollArea, QComboBox
)
from src.gui.widgets.qtgraph import Graph
from src.gui.assets.csstyle import Style
from src.gui.assets.theme_manager import ThemeManager
from src.gui.assets.scan_controller import ScanWorker
from src.gui.assets.icon_utils import CustomIcon
from src.gui.widgets.noscrollcombobox import NSCB


SCAN_CONFIG_FILE = os.path.join(os.getcwd(), 'config', 'scan_axes.json')


class ScanTab(QWidget):
    def __init__(self, loaded_instruments=None):
        super().__init__()
        self.loaded_instruments = loaded_instruments or []
        self.worker: ScanWorker | None = None
        self.scan_data: dict | None = None

        self._loading_config = False
        self.axis_widgets: list[tuple] = []   # (combo, start, stop, steps, frame)

        self._scan_params: list[tuple] = []
        self._scan_params_long: list[tuple] = []# writable params → axis combos
        self._all_params:  list[tuple] = []   # all readable params → y-axis combo

        self._init_ui()
        self.populate_params()
        self._load_scan_axes()


    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.main_frame = QFrame()
        root_layout.addWidget(self.main_frame)

        h_layout = QHBoxLayout(self.main_frame)
        h_layout.setContentsMargins(10, 10, 10, 10)

        config_container = QFrame()
        self._config_container = config_container
        config_layout = QVBoxLayout(config_container)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_container.setMinimumWidth(320)

        # Axes group
        self.grp_axes = QGroupBox("Scan Axes")
        axes_layout = QVBoxLayout(self.grp_axes)

        self.axes_container = QFrame()
        self.axes_layout = QVBoxLayout(self.axes_container)
        self.axes_layout.setContentsMargins(0, 0, 0, 0)
        axes_layout.addWidget(self.axes_container)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_add = QPushButton("Add Axis")
        btn_add.setStyleSheet(Style.Button.suggested)
        btn_add.clicked.connect(self.add_axis_row)
        btn_row.addWidget(btn_add)
        axes_layout.addLayout(btn_row)
        config_layout.addWidget(self.grp_axes)

        # Settings group
        self.grp_settings = QGroupBox("Settings")
        settings_layout = QVBoxLayout(self.grp_settings)
        settings_layout.setContentsMargins(15, 15, 15, 15)

        delay_row = QHBoxLayout()
        delay_row.addWidget(QLabel("Delay between points (s):"))
        self.inp_delay = QLineEdit("0.5")
        self.inp_delay.setObjectName("scan_delay")
        self.inp_delay.setFixedWidth(60)
        delay_row.addWidget(self.inp_delay)
        settings_layout.addLayout(delay_row)

        repeat_row = QHBoxLayout()
        repeat_row.addWidget(QLabel("Repeats:"))
        self.inp_repeats = QLineEdit("1")
        self.inp_repeats.setObjectName("scan_repeats")
        self.inp_repeats.setFixedWidth(60)
        repeat_row.addWidget(self.inp_repeats)
        settings_layout.addLayout(repeat_row)

        settings_layout.addWidget(QLabel("Comments:"))
        self.txt_comments = QTextEdit()
        self.txt_comments.setObjectName("scan_comments")
        self.txt_comments.setFixedHeight(100)
        settings_layout.addWidget(self.txt_comments)
        config_layout.addWidget(self.grp_settings)

        config_layout.addStretch()

        # Controls group
        self.grp_controls = QGroupBox("")
        ctrl_layout = QGridLayout(self.grp_controls)

        self.btn_start = QPushButton("Start Scan")
        self.btn_start.setStyleSheet(Style.Button.start)
        self.btn_start.clicked.connect(self._start_scan)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setCheckable(True)
        self.btn_pause.setStyleSheet(Style.Button.reset)
        self.btn_pause.clicked.connect(self._toggle_pause)

        self.btn_abort = QPushButton("Abort")
        self.btn_abort.setStyleSheet(Style.Button.stop)
        self.btn_abort.setEnabled(False)
        self.btn_abort.clicked.connect(self._abort_scan)

        self.btn_save = QPushButton("Auto-Save Active")
        self.btn_save.setStyleSheet(Style.Button.disabled)
        self.btn_save.setEnabled(False)

        ctrl_layout.addWidget(self.btn_start, 0, 0)
        ctrl_layout.addWidget(self.btn_pause, 0, 1)
        ctrl_layout.addWidget(self.btn_abort, 1, 0)
        ctrl_layout.addWidget(self.btn_save,  1, 1)
        config_layout.addWidget(self.grp_controls)

        self.lbl_status = QLabel("Ready")
        config_layout.addWidget(self.lbl_status)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(config_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setFixedWidth(340)
        self._scroll = scroll
        h_layout.addWidget(scroll)

        self.graph_widget = QFrame()
        graph_layout = QVBoxLayout(self.graph_widget)
        graph_layout.setContentsMargins(10, 10, 10, 10)

        axis_sel = QHBoxLayout()
        axis_sel.addWidget(QLabel("X-Axis:"))
        self.combo_x = QComboBox()
        self.combo_x.setObjectName("scan_x_axis")
        axis_sel.addWidget(self.combo_x)
        axis_sel.addStretch()
        axis_sel.addWidget(QLabel("Y-Axis:"))
        self.combo_y = QComboBox()
        self.combo_y.setObjectName("scan_y_axis")
        axis_sel.addWidget(self.combo_y)
        graph_layout.addLayout(axis_sel)

        self.graph = Graph()
        graph_layout.addWidget(self.graph)
        h_layout.addWidget(self.graph_widget)

        self.combo_x.currentIndexChanged.connect(self._on_combo_update_graph)
        self.combo_y.currentIndexChanged.connect(self._on_combo_update_graph)

        self.apply_theme()


    def populate_params(self):
        self._scan_params.clear()
        self._all_params.clear()

        for inst in self.loaded_instruments:
            for param in inst.get_all_params():
                key      = f"{inst.name}: {param.name}"
                shortkey = f"{inst.nickname}: {param.name}"
                self._all_params.append((key, param))
                if 'write' in param._access:
                    self._scan_params.append((shortkey, param))
                    self._scan_params_long.append((key, param))

        # Rebuild graph axis combos
        self.combo_x.blockSignals(True)
        self.combo_y.blockSignals(True)
        self.combo_x.clear()
        self.combo_y.clear()
        self.combo_x.addItem("Step Index", "index")
        for name, param in self._scan_params_long:
            self.combo_x.addItem(name, param)
        for name, param in self._all_params:
            self.combo_y.addItem(name, param)
        self.combo_x.blockSignals(False)
        self.combo_y.blockSignals(False)

        for combo, *_ in self.axis_widgets:
            self._fill_param_combo(combo)

    def _fill_param_combo(self, combo: NSCB):
        combo.blockSignals(True)
        combo.clear()
        for name, param in self._scan_params:
            combo.addItem(name, param)
        combo.blockSignals(False)

    def set_instruments(self, instruments):
        self.loaded_instruments = instruments
        self.populate_params()

    def add_axis_row(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        line1 = QHBoxLayout()
        combo = NSCB()
        combo.setFixedWidth(130)
        self._fill_param_combo(combo)

        steps = QLineEdit("10")
        steps.setPlaceholderText("Steps")
        steps.setFixedWidth(60)

        btn_del = QPushButton("")
        btn_del.setIcon(CustomIcon.trash('#F44336'))
        btn_del.setStyleSheet(Style.Button.stop)
        btn_del.setFixedWidth(25)
        btn_del.clicked.connect(lambda: self.remove_axis_row(frame))

        line1.addWidget(combo)
        line1.addWidget(QLabel("Steps:"))
        line1.addWidget(steps)
        line1.addWidget(btn_del)
        line1.addStretch()

        line2 = QHBoxLayout()
        start = QLineEdit("")
        start.setFixedWidth(85)
        stop  = QLineEdit("")
        stop.setFixedWidth(85)
        line2.addWidget(QLabel("Start:"))
        line2.addWidget(start)
        line2.addWidget(QLabel("Stop:"))
        line2.addWidget(stop)
        line2.addStretch()

        layout.addLayout(line1)
        layout.addLayout(line2)
        self.axes_layout.addWidget(frame)

        entry = (combo, start, stop, steps, frame)
        self.axis_widgets.append(entry)


        combo.currentIndexChanged.connect(self._save_scan_axes)
        start.editingFinished.connect(self._save_scan_axes)
        stop.editingFinished.connect(self._save_scan_axes)
        steps.editingFinished.connect(self._save_scan_axes)

        self._apply_theme_to_axis_row(*entry)
        return entry

    def remove_axis_row(self, frame):
        self.axis_widgets = [r for r in self.axis_widgets if r[4] is not frame]
        frame.deleteLater()
        self._save_scan_axes()


    def _save_scan_axes(self):
        if self._loading_config:
            return
        axes_data = [
            {
                'param_index': combo.currentIndex(),
                'start':  start.text(),
                'stop':   stop.text(),
                'steps':  steps.text()
            }
            for combo, start, stop, steps, _ in self.axis_widgets
        ]
        try:
            os.makedirs(os.path.dirname(SCAN_CONFIG_FILE), exist_ok=True)
            with open(SCAN_CONFIG_FILE, 'w') as f:
                json.dump(axes_data, f, indent=4)
        except Exception as e:
            print(f"[ScanTab] Error saving scan axes: {e}")

    def _load_scan_axes(self):
        self._loading_config = True
        try:
            if not os.path.exists(SCAN_CONFIG_FILE):
                self.add_axis_row()
                return

            with open(SCAN_CONFIG_FILE, 'r') as f:
                axes_data = json.load(f)

            if not axes_data:
                self.add_axis_row()
                return

            for axis in axes_data:
                combo, start, stop, steps, _ = self.add_axis_row()
                if 'param_index' in axis and axis['param_index'] < combo.count():
                    combo.setCurrentIndex(axis['param_index'])
                start.setText(str(axis.get('start', '')))
                stop.setText(str(axis.get('stop',  '')))
                steps.setText(str(axis.get('steps', '10')))

        except Exception as e:
            print(f"[ScanTab] Error loading scan axes: {e}")
            if not self.axis_widgets:
                self.add_axis_row()
        finally:
            self._loading_config = False


    def _start_scan(self):
        axes_config = []
        for combo, start, stop, steps, _ in self.axis_widgets:
            param = combo.currentData()
            if not param:
                continue
            try:
                axes_config.append({
                    'param': param,
                    'start': float(start.text()),
                    'stop':  float(stop.text()),
                    'steps': int(steps.text())
                })
            except ValueError:
                self.lbl_status.setText("Error: Invalid number in axis range.")
                return

        if not axes_config:
            self.lbl_status.setText("Error: No axes defined.")
            return

        try:
            delay   = float(self.inp_delay.text())
            repeats = int(self.inp_repeats.text())
        except ValueError:
            self.lbl_status.setText("Error: Invalid delay or repeats.")
            return

        config = {
            'axes':     axes_config,
            'delay':    delay,
            'repeats':  repeats,
            'comments': self.txt_comments.toPlainText()
        }

        self.scan_data = defaultdict(list)
        self.graph.line_curve.setData([], [])
        self.graph.dot_curve.setData([], [])

        self.worker = ScanWorker(self.loaded_instruments, config)
        self.worker.data_point_ready.connect(self._on_data_point)
        self.worker.status_update.connect(self.lbl_status.setText)
        self.worker.scan_finished.connect(self._on_scan_finished)
        self.worker.progress_update.connect(self._on_progress)
        self.worker.start()

        self.btn_start.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self.btn_pause.setChecked(False)
        self.btn_pause.setText("Pause")

    def _toggle_pause(self, checked: bool):
        if not self.worker:
            return
        if checked:
            self.worker.pause()
            self.btn_pause.setText("Resume")
        else:
            self.worker.resume()
            self.btn_pause.setText("Pause")

    def _abort_scan(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self._on_scan_finished()

    def _on_scan_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)
        self.btn_pause.setChecked(False)
        self.btn_pause.setText("Pause")
        self.lbl_status.setText("Scan Finished")

    def _on_progress(self, current: int, total: int):
        self.lbl_status.setText(f"Scanning… {current}/{total}")


    def _on_data_point(self, data: dict):
        idx = len(self.scan_data["__index__"])
        self.scan_data["__index__"].append(idx)
        for key, value in data.items():
            try:
                self.scan_data[key].append(float(value))
            except (ValueError, TypeError):
                self.scan_data[key].append(value)
        self._update_graph()

    def _get_data_key(self, param) -> str | None:
        if param == "index":
            return "__index__"
        for inst in self.loaded_instruments:
            if param in inst.parameters.values():
                return f"{inst.name}_{param.name}"
        return None

    def _on_combo_update_graph(self):
        x_data = self.combo_x.currentData()
        y_data = self.combo_y.currentData()

        if y_data is None or y_data == "index":
            return

        self.graph.getPlotItem().setLabel(
            'left', y_data.label or y_data.name, units=y_data.unit)

        if x_data == "index":
            self.graph.getPlotItem().setLabel('bottom', "Step Number")
        elif x_data is not None:
            self.graph.getPlotItem().setLabel(
                'bottom', x_data.label or x_data.name, units=x_data.unit)

        self._update_graph()

    def _update_graph(self):
        if not self.scan_data:
            return

        x_key = self._get_data_key(self.combo_x.currentData())
        y_key = self._get_data_key(self.combo_y.currentData())

        if not x_key or not y_key:
            return

        x_vals = self.scan_data.get(x_key, [])
        y_vals = self.scan_data.get(y_key, [])

        n = min(len(x_vals), len(y_vals))
        if n > 0:
            self.graph.line_curve.setData(x_vals[:n], y_vals[:n])
        else:
            self.graph.line_curve.setData([], [])

    def apply_theme(self):
        is_dark = ThemeManager.get_theme() == "dark"

        self.main_frame.setStyleSheet(
            Style.Frame.content_dark if is_dark else Style.Frame.content_light)
        self._config_container.setStyleSheet(
            Style.Frame.content_dark if is_dark else Style.Frame.content_light)
        self.grp_axes.setStyleSheet(
            Style.GroupBox.dark_gray if is_dark else Style.GroupBox.light_gray)
        self.grp_settings.setStyleSheet(
            Style.GroupBox.dark if is_dark else Style.GroupBox.light)
        self.grp_controls.setStyleSheet(
            Style.GroupBox.dark_gray if is_dark else Style.GroupBox.light_gray)
        self.axes_container.setStyleSheet(
            Style.Frame.container_dark if is_dark else Style.Frame.container_light)
        self.graph_widget.setStyleSheet(
            Style.Frame.container_dark if is_dark else Style.Frame.container_light)

        inp_style = Style.Input.line_edit_dark if is_dark else Style.Input.line_edit_light
        self.inp_delay.setStyleSheet(inp_style)
        self.inp_repeats.setStyleSheet(inp_style)
        self.txt_comments.setStyleSheet(
            Style.Input.text_edit_dark if is_dark else Style.Input.text_edit_light)

        self.lbl_status.setStyleSheet(
            Style.Label.title_dark if is_dark else Style.Label.title_light)
        self._scroll.setStyleSheet(Style.Scroll.combined)

        cb_style = Style.ComboBox.dark if is_dark else Style.ComboBox.light
        self.combo_x.setStyleSheet(cb_style)
        self.combo_y.setStyleSheet(cb_style)

        for row in self.axis_widgets:
            self._apply_theme_to_axis_row(*row)

    def _apply_theme_to_axis_row(self, combo, start, stop, steps, frame):
        is_dark = ThemeManager.get_theme() == "dark"
        frame.setStyleSheet(
            Style.Frame.container_dark if is_dark else Style.Frame.container_light)
        combo.setStyleSheet(Style.ComboBox.dark if is_dark else Style.ComboBox.light)
        inp = Style.Input.line_edit_dark if is_dark else Style.Input.line_edit_light
        start.setStyleSheet(inp)
        stop.setStyleSheet(inp)
        steps.setStyleSheet(inp)