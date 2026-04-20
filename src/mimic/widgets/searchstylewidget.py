import platform
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy,
                             QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QFontMetrics
from mimic.assets.csstyle import Palette

_IS_MACOS = platform.system() == "Darwin"
_IS_WINDOWS = platform.system() == "Windows"
_IS_LINUX = platform.system() == "Linux"


def _font_family() -> str:
    if _IS_MACOS:
        return "'.AppleSystemUIFont', 'Helvetica Neue', sans-serif"
    if _IS_WINDOWS:
        return "'Segoe UI', 'Verdana', sans-serif"
    return "'Cantarell', 'Inter', 'Noto Sans', sans-serif"


def _reference_font() -> QFont:
    families = {"Darwin": "Helvetica Neue", "Windows": "Segoe UI"}
    family = families.get(platform.system(), "Cantarell")
    font = QFont(family)
    font.setPixelSize(_FONT_PX)
    return font


_FONT_PX = 14
_RADIUS = 6
_BORDER_NONE = 0
_BORDER_FOCUS = 2
_PAD_V = 3
_PAD_H = 6
_BTN_PAD_H = 8


def _compute_fixed_height() -> int:
    fm = QFontMetrics(_reference_font())
    line_h = fm.height()
    return line_h + 2 * _PAD_V + 2 * _BORDER_FOCUS


def _compute_fixed_width(charlength=12) -> int:
    fm = QFontMetrics(_reference_font())
    line_w = fm.averageCharWidth()
    return line_w * charlength + 2 * _PAD_H


def _stylesheet(dark: bool = False) -> str:
    font = _font_family()
    bg = Palette.D_INPUT_BG if dark else Palette.L_BG_FRAME_2
    fg = Palette.D_TEXT_MAIN if dark else Palette.L_TEXT_MAIN
    fg_sec = Palette.D_TEXT_SEC if dark else Palette.L_TEXT_SEC
    border = Palette.D_BORDER if dark else Palette.L_BORDER
    focus = Palette.D_BORDER_FOCUS if dark else Palette.L_BORDER_FOCUS
    dis_bg = Palette.D_BG_FRAME_2 if dark else "#FAFAFA"
    dis_fg = Palette.D_TEXT_SEC if dark else "#C0C0C0"
    btn_bg = "rgba(53, 132, 228, 0.2)"
    btn_hover = "rgba(53, 132, 228, 0.3)"
    btn_pressed = Palette.ACCENT_BLUE_H
    mac_btn_extra = "border-style: solid;" if _IS_MACOS else ""

    # Adjust button radius so it fits cleanly inside the container's border
    btn_radius = max(0, _RADIUS - _BORDER_FOCUS)

    return f"""
            QFrame#input_container {{
                background-color: {bg};
                border: {_BORDER_FOCUS}px solid transparent; /* Keeps sizing consistent */
                border-radius: {_RADIUS}px;
            }}

            QFrame#input_container[focused="true"] {{
                border: {_BORDER_FOCUS}px solid {focus};
            }}

            QFrame#input_container:disabled {{
                background-color: {dis_bg};
            }}

            QLineEdit {{
                background-color: transparent;
                color: {fg};
                selection-background-color: {focus};
                selection-color: #FFFFFF;
                font-family: {font};
                font-size: {_FONT_PX}px;
                border: none;
                padding: {_PAD_V}px {_PAD_H}px;
            }}

            QLineEdit:disabled {{
                color: {dis_fg};
            }}

            QPushButton {{
                background-color: {btn_bg};
                color: {focus};
                font-family: {font};
                font-size: {_FONT_PX}px;
                font-weight: 600;
                border: none;
                {mac_btn_extra}
                padding: {_PAD_V}px {_BTN_PAD_H}px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: {btn_radius}px;
                border-bottom-right-radius: {btn_radius}px;
            }}

            QPushButton:hover {{
                background-color: {btn_hover};
            }}

            QPushButton:pressed {{
                background-color: {btn_pressed};
                color: #FFFFFF;
            }}

            QPushButton:disabled {{
                background-color: transparent;
                color: {dis_fg};
            }}
        """


class CombinedInputWidget(QFrame):
    submitted = pyqtSignal(str)
    text_changed = pyqtSignal(str)

    def __init__(self, button_text: str = "Send", placeholder_text: str = "", dark: bool = False,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setObjectName("input_container")
        self.setProperty("focused", False)

        self._dark = dark
        self._row_height = _compute_fixed_height()

        self.setFixedHeight(self._row_height)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder_text)
        self.line_edit.setMinimumWidth(_compute_fixed_width(6))
        self.line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.line_edit.returnPressed.connect(self._on_submit)
        self.line_edit.textChanged.connect(self.text_changed)

        self.line_edit.installEventFilter(self)

        self.button = QPushButton(button_text)
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
        self.button.clicked.connect(self._on_submit)

        lay.addWidget(self.line_edit)
        lay.addWidget(self.button)

        self.apply_theme()

    def eventFilter(self, obj, event):
        if obj == self.line_edit:
            if event.type() == QEvent.Type.FocusIn:
                self.setProperty("focused", True)
                self.style().unpolish(self)
                self.style().polish(self)
            elif event.type() == QEvent.Type.FocusOut:
                self.setProperty("focused", False)
                self.style().unpolish(self)
                self.style().polish(self)
        return super().eventFilter(obj, event)

    def text(self) -> str:
        return self.line_edit.text()

    def set_text(self, value: str) -> None:
        self.line_edit.setText(value)

    def clear(self) -> None:
        self.line_edit.clear()

    def set_placeholder(self, text: str) -> None:
        self.line_edit.setPlaceholderText(text)

    def set_button_text(self, text: str) -> None:
        self.button.setText(text)

    def set_enabled(self, enabled: bool) -> None:
        self.setEnabled(enabled)

    def apply_theme(self, is_dark=None) -> None:
        self.setStyleSheet(_stylesheet(is_dark if is_dark is not None else self._dark))

    def _on_submit(self) -> None:
        text = self.line_edit.text().strip()
        if text:
            self.submitted.emit(text)