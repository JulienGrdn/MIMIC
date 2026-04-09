import pyqtgraph as pg
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QButtonGroup
)
from mimic.widgets.smaller_toggle import AnimatedToggle
from mimic.widgets.ui_line_separator import qframe_line_separator

ACCENT_BLUE = "#3584E4"

_PLOT_COLORS = [
    ("#4678FA", "Blue"),
    ("#00BFFF", "Cyan"),
    ("#39D353", "Green"),
    ("#FFA040", "Orange"),
    ("#FF4060", "Red"),
    ("#DDDDDD", "White"),
]

_STYLE_MAP = {
    "Default": "default",
    "Dots": "dots",
    "Line": "line",
}


class Graph(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.setBackground(QColor(0, 0, 0, 0))

        self._color = QColor(70, 120, 250)
        self._current_style = 'default'

        dark_color = self._color.darker(150)

        self.line_curve = self.plot(
            pen=pg.mkPen(self._color, width=2),
            symbol='o',
            symbolBrush=pg.mkBrush(dark_color),
            symbolPen=pg.mkPen(dark_color)
        )
        self.dot_curve = self.plot(pen=pg.mkPen(QColor(70, 120, 250), width=0), symbol='o')

        self.showGrid(x=True, y=True, alpha=0.3)

    def set_plot_style(self, style: str):
        self._current_style = style
        dark_color = self._color.darker(150)

        if style == 'dots':
            self.line_curve.setPen(pg.mkPen(None))
            self.line_curve.setSymbol('o')
            self.line_curve.setSymbolBrush(pg.mkBrush(dark_color))
            self.line_curve.setSymbolPen(pg.mkPen(dark_color))
        elif style == 'line':
            self.line_curve.setPen(pg.mkPen(self._color, width=2))
            self.line_curve.setSymbol(None)
        else:
            self.line_curve.setPen(pg.mkPen(self._color, width=2))
            self.line_curve.setSymbol('o')
            self.line_curve.setSymbolBrush(pg.mkBrush(dark_color))
            self.line_curve.setSymbolPen(pg.mkPen(dark_color))

    def set_plot_color(self, color: QColor):
        self._color = color
        self.set_plot_style(self._current_style)


class GraphWithToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.graph = Graph()
        layout.addWidget(self.graph)

        self._style_toolbar = QWidget()
        self._style_toolbar.setStyleSheet("background-color: transparent;")

        sep_layout = QVBoxLayout(self._style_toolbar)
        sep_layout.setContentsMargins(150, 6, 150, 0)
        sep_layout.setSpacing(0)
        sep_layout.addWidget(qframe_line_separator())

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 6, 0, 0)
        toolbar_layout.setSpacing(6)
        sep_layout.addLayout(toolbar_layout)

        toolbar_layout.addStretch()

        toolbar_layout.addWidget(QLabel("Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(list(_STYLE_MAP.keys()))
        self.style_combo.setFixedWidth(90)
        toolbar_layout.addWidget(self.style_combo)
        toolbar_layout.addSpacing(10)

        toolbar_layout.addWidget(QLabel("Color:"))

        self.color_btn_group = QButtonGroup(self)
        self.color_btn_group.setExclusive(True)

        for i, (hex_color, name) in enumerate(_PLOT_COLORS):
            btn = QPushButton()
            btn.setFixedSize(18, 18)
            btn.setToolTip(name)
            btn.setCheckable(True)
            self.color_btn_group.addButton(btn)

            if i == 0:
                btn.setChecked(True)

            btn.setStyleSheet(
                f"QPushButton {{ background-color: {hex_color}; border: 3px solid transparent;"
                f" border-radius: 6px; padding: 0px; }}"
                f" QPushButton:hover, QPushButton:checked {{ border: 4px solid {hex_color}; border-radius: 8px; }}"
            )
            btn.clicked.connect(lambda checked, c=hex_color: self.graph.set_plot_color(QColor(c)))
            toolbar_layout.addWidget(btn)

        toolbar_layout.addStretch()

        logy_label = QLabel("Log Y")
        self.log_y_cb = AnimatedToggle()
        self.log_y_cb.toggled.connect(lambda checked: self.graph.setLogMode(x=False, y=checked))
        toolbar_layout.addWidget(logy_label)
        toolbar_layout.addWidget(self.log_y_cb)

        toolbar_layout.addStretch()
        self._style_toolbar.setVisible(False)
        layout.addWidget(self._style_toolbar)

        self._style_toggle_btn = QPushButton(self)

        self._style_toggle_btn.setText("\u2699")
        self._style_toggle_btn.setFixedSize(22, 22)
        self._style_toggle_btn.setCheckable(True)
        self._style_toggle_btn.setVisible(False)
        self._style_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_toggle_btn.setToolTip("Plot style")

        self._style_toggle_btn.setStyleSheet(
            f"QPushButton {{ background-color: rgba(120,120,120,.7); color: rgba(250,250,250,1);"
            f" border: none; border-radius: 4px; font-size: 16px; padding: 0px; padding-bottom: 0px; }}"
            f" QPushButton:hover {{ background-color: rgba(80,80,80,0.9); color: white; }}"
            f" QPushButton:checked {{ background-color: {ACCENT_BLUE}; color: white; }}"
        )

        self._style_toggle_btn.clicked.connect(self._toggle_toolbar)
        self._style_toggle_btn.raise_()

        self._style_hide_timer = QTimer(self)
        self._style_hide_timer.setSingleShot(True)
        self._style_hide_timer.setInterval(150)
        self._style_hide_timer.timeout.connect(self._check_hide_style_btn)
        self.installEventFilter(self)
        self._style_toggle_btn.installEventFilter(self)

        self.style_combo.currentTextChanged.connect(
            lambda text: self.graph.set_plot_style(_STYLE_MAP.get(text, 'default')))

    def apply_saved_style(self):
        self.graph.set_plot_style(_STYLE_MAP.get(self.style_combo.currentText(), 'default'))

    def _toggle_toolbar(self, checked):
        self._style_toolbar.setVisible(checked)
        # QTimer.singleShot(0, self._reposition_style_btn)

    def eventFilter(self, obj, event):
        if obj is self:
            t = event.type()
            if t == QEvent.Type.Enter:
                self._style_hide_timer.stop()
                self._style_toggle_btn.setVisible(True)
                #self._reposition_style_btn()
            elif t == QEvent.Type.Leave:
                self._style_hide_timer.start()
            elif t == QEvent.Type.Resize:
                self._reposition_style_btn()
        elif obj is self._style_toggle_btn:
            if event.type() == QEvent.Type.Enter:
                self._style_hide_timer.stop()
        return super().eventFilter(obj, event)

    def _reposition_style_btn(self):
        btn = self._style_toggle_btn

        x = self.width() - btn.width() - 8

        if self._style_toolbar.isVisible():
            toolbar_y = self._style_toolbar.y()
            toolbar_h = self._style_toolbar.height()

            y = toolbar_y + (toolbar_h - btn.height()) // 2 + 1
        else:
            y = self.height() - btn.height() - 8

        btn.move(x, y)
        btn.raise_()

    def _check_hide_style_btn(self):
        if not self._style_toolbar.isVisible():
            self._style_toggle_btn.setVisible(False)