from PyQt6.QtWidgets import QScrollArea, QScrollBar
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPainterPath

class ScrollBar(QScrollBar):
    def __init__(self, orientation=Qt.Orientation.Vertical, parent=None):
        super().__init__(orientation, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        self._is_vertical = orientation == Qt.Orientation.Vertical
        self._thickness = 4.0
        self._handle_opacity = 0.0
        self._target_opacity = 0.0
        self._hovered = False
        self._pressed = False
        self._handle_color = QColor(255, 255, 255)
        self._gap = 3
        self._end_margin = 4
        self._min_handle = 40

        if self._is_vertical:
            self.setFixedWidth(16)
        else:
            self.setFixedHeight(16)

        self.setStyleSheet("""
            QScrollBar {
                background: transparent;
                border: none;
            }
            QScrollBar::handle {
                background: transparent;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
                border: none;
                width: 0px;
                height: 0px;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
                border: none;
            }
        """)

        self._thickness_anim = QPropertyAnimation(self, b"thickness")
        self._thickness_anim.setDuration(150)
        self._thickness_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._opacity_anim = QPropertyAnimation(self, b"handleOpacity")
        self._opacity_anim.setDuration(250)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.valueChanged.connect(self._on_activity)
        self.rangeChanged.connect(self._on_activity)

    @pyqtProperty(float)
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, value):
        self._thickness = value
        self.update()

    @pyqtProperty(float)
    def handleOpacity(self):
        return self._handle_opacity

    @handleOpacity.setter
    def handleOpacity(self, value):
        self._handle_opacity = value
        self.update()

    def _fade_to(self, opacity):
        if self._target_opacity == opacity:
            return
        self._target_opacity = opacity
        self._opacity_anim.stop()
        self._opacity_anim.setStartValue(self._handle_opacity)
        self._opacity_anim.setEndValue(opacity)
        self._opacity_anim.start()

    def _on_activity(self):
        if self.maximum() == self.minimum():
            self._fade_to(0.0)
        elif not self._hovered:
            self._fade_to(0.5)

    def enterEvent(self, event):
        self._hovered = True
        self._animate_thickness(6.0)
        self._fade_to(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self._animate_thickness(4.0)
        self._fade_to(0.5)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def _animate_thickness(self, target):
        self._thickness_anim.stop()
        self._thickness_anim.setStartValue(self._thickness)
        self._thickness_anim.setEndValue(target)
        self._thickness_anim.start()

    def paintEvent(self, event):
        if self.maximum() == self.minimum():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        extent = self.height() if self._is_vertical else self.width()
        usable = extent - 2 * self._end_margin

        page = self.pageStep()
        range_total = self.maximum() - self.minimum() + page
        handle_len = max(self._min_handle, usable * page / range_total)
        remaining = usable - handle_len

        if self.maximum() == self.minimum():
            pos = 0.0
        else:
            pos = remaining * (self.value() - self.minimum()) / (self.maximum() - self.minimum())

        handle_start = self._end_margin + pos
        t = self._thickness
        radius = t / 2.0

        if self._is_vertical:
            x = self.width() - t - self._gap
            rect = (x, handle_start, t, handle_len)
        else:
            y = self.height() - t - self._gap
            rect = (handle_start, y, handle_len, t)

        if self._pressed:
            alpha = 0.65
        elif self._hovered:
            alpha = 0.5
        else:
            alpha = 0.3

        color = QColor(self._handle_color)
        color.setAlphaF(alpha * self._handle_opacity)

        path = QPainterPath()
        path.addRoundedRect(*rect, radius, radius)
        painter.fillPath(path, color)
        painter.end()


class CustomScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._v_bar = ScrollBar(Qt.Orientation.Vertical, self)
        self._h_bar = ScrollBar(Qt.Orientation.Horizontal, self)

        self.setVerticalScrollBar(self._v_bar)
        self.setHorizontalScrollBar(self._h_bar)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 14px;
                background: transparent;
                margin: 0px;
            }
            QScrollBar:horizontal {
                height: 14px;
                background: transparent;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: transparent;
            }
            QScrollBar::add-line, QScrollBar::sub-line, 
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
                border: none;
                width: 0px;
                height: 0px;
            }
        """)

    def setHandleColor(self, color: QColor):
        self._v_bar._handle_color = color
        self._h_bar._handle_color = color
        self._v_bar.update()
        self._h_bar.update()

    def apply_theme(self, is_dark: bool):
        self.setHandleColor(QColor(255, 255, 255) if is_dark else QColor(0, 0, 0))