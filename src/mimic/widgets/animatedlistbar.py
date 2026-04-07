from __future__ import annotations

from PyQt6.QtCore import (
    Qt, QSize, QRect, QByteArray,
    QPropertyAnimation, QEasingCurve,
    pyqtSignal, pyqtProperty,
)
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QBrush
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QListWidget, QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QStyle, QStyledItemDelegate, QStyleOptionViewItem,
    QVBoxLayout, QWidget,
)
from mimic.widgets.ui_line_separator import thinner_qframe_line_separator
from mimic.assets.csstyle import Palette, Style
from mimic.assets.theme_manager import ThemeManager

_SVG_BASE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" 
fill="none" stroke="{{c}}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">
{paths}
</svg>"""

_ICONS: dict[str, str] = {
    "collapse": _SVG_BASE.format(paths="""
        <path d="M20 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h14"/>
        <line x1="20" y1="2" x2="20" y2="22"/>
        <line x1="15" y1="12" x2="9" y2="12"/>
        <polyline points="12 9 9 12 12 15"/>
    """),
    "expand": _SVG_BASE.format(paths="""
        <path d="M4 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4"/>
        <line x1="4" y1="2" x2="4" y2="22"/>
        <line x1="9" y1="12" x2="15" y2="12"/>
        <polyline points="12 9 15 12 12 15"/>
    """),
    "devices": _SVG_BASE.format(paths="""
        <rect x="3" y="3" width="7" height="7" rx="2" ry="2"/>
        <rect x="14" y="3" width="7" height="7" rx="2" ry="2"/>
        <rect x="14" y="14" width="7" height="7" rx="2" ry="2"/>
        <rect x="3" y="14" width="7" height="7" rx="2" ry="2"/>
    """),
    "chart": _SVG_BASE.format(paths="""
        <circle cx="12" cy="12" r="10"/>
        <polygon points="10 8 16 12 10 16 10 8"/>
    """),
    "scan": _SVG_BASE.format(paths="""
        <path d="M4 3v15a2 2 0 0 0 2 2h15"/>
        <polyline points="8 14 12 10 16 13 21 6"/>
        <polyline points="16 6 21 6 21 11"/>
    """),
    "settings": _SVG_BASE.format(paths="""
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    """),
}

_ICON_CACHE: dict[tuple, QIcon] = {}


def _make_svg_icon(key: str, color: str, size: int = 20) -> QIcon:
    cache_key = (key, color, size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    icon = QIcon()

    def render_pixmap(hex_color: str) -> QPixmap:
        svg_bytes = _ICONS.get(key, _ICONS["collapse"]).replace("{c}", hex_color).encode()
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        return pixmap

    icon.addPixmap(render_pixmap(color), QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(render_pixmap("#FFFFFF"), QIcon.Mode.Selected, QIcon.State.Off)

    _ICON_CACHE[cache_key] = icon
    return icon


class _SidebarDelegate(QStyledItemDelegate):

    _ICON_SZ = 20
    _SEL_COLOR = QColor(53, 132, 228)

    def __init__(self, bar: "AnimatedListBar") -> None:
        super().__init__(bar)
        self._bar = bar

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(self._bar.width(), 40)

    def paint(
            self,
            painter: QPainter,
            option: QStyleOptionViewItem,
            index,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect: QRect = option.rect
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        is_dark = ThemeManager.get_theme() == "dark"
        is_collapsed = self._bar.width() < self._bar.COLLAPSE_THRESHOLD

        bg_rect = rect.adjusted(4, 2, -4, -2)

        painter.setPen(Qt.PenStyle.NoPen)

        if is_selected:
            painter.setBrush(QBrush(self._SEL_COLOR))
            painter.drawRoundedRect(bg_rect, 6.0, 6.0)
        elif is_hovered:
            c, a = (255, 18) if is_dark else (0, 15)
            painter.setBrush(QBrush(QColor(c, c, c, a)))
            painter.drawRoundedRect(bg_rect, 6.0, 6.0)

        if is_collapsed:
            icon: QIcon = index.data(Qt.ItemDataRole.DecorationRole) or QIcon()
            sz = self._ICON_SZ
            ix = rect.x() + (rect.width() - sz) // 2
            iy = rect.y() + (rect.height() - sz) // 2

            if not icon.isNull():
                mode = QIcon.Mode.Selected if is_selected else QIcon.Mode.Normal
                fg = index.data(Qt.ItemDataRole.ForegroundRole)
                if fg is not None and not is_selected:
                    painter.setOpacity(0.35)
                icon.paint(painter, QRect(ix, iy, sz, sz), Qt.AlignmentFlag.AlignCenter, mode)
                painter.setOpacity(1.0)

        else:
            text = index.data(Qt.ItemDataRole.DisplayRole) or ""
            tx = 16
            text_rect = QRect(rect.x() + tx, rect.y(), rect.width() - tx - 4, rect.height())

            if is_selected:
                text_color = QColor("#FFFFFF")
            else:
                fg = index.data(Qt.ItemDataRole.ForegroundRole)
                if fg is not None:
                    brush = fg if isinstance(fg, QBrush) else QBrush(QColor(fg))
                    text_color = brush.color()
                else:
                    text_color = QColor(
                        Palette.D_TEXT_MAIN if is_dark else Palette.L_TEXT_MAIN
                    )

            painter.setPen(text_color)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                text,
            )

        painter.restore()


class AnimatedListBar(QWidget):

    current_row_changed = pyqtSignal(int)

    EXPANDED_WIDTH    : int = 110
    COLLAPSED_WIDTH   : int = 40
    COLLAPSE_THRESHOLD: int = 100
    ANIM_DURATION     : int = 220

    def __init__(
        self,
        items: list[dict],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._items_data: list[dict] = items
        self._collapsed : bool       = False

        self.setMinimumWidth(self.COLLAPSED_WIDTH)
        self.setMaximumWidth(self.EXPANDED_WIDTH)
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._list = QListWidget()
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setMouseTracking(True)
        self._list.viewport().setMouseTracking(True)
        self._list.currentRowChanged.connect(self.current_row_changed)
        root.addWidget(self._list, 1)

        self._list.setItemDelegate(_SidebarDelegate(self))

        self._toggle_btn = QPushButton()
        self._toggle_btn.setFixedHeight(40)
        self._toggle_btn.setIconSize(QSize(20, 20))
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setToolTip("Toggle sidebar")
        self._toggle_btn.clicked.connect(self.toggle)
        root.addWidget(thinner_qframe_line_separator())
        root.addWidget(self._toggle_btn)

        self._anim = QPropertyAnimation(self, b"_anim_width", self)
        self._anim.setDuration(self.ANIM_DURATION)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim.valueChanged.connect(lambda _: self._list.update())

        self._populate()
        ThemeManager.instance().theme_changed.connect(lambda _: self.apply_theme())
        self.apply_theme()


    def _get_anim_width(self) -> int:
        return self.width()

    def _set_anim_width(self, w: int) -> None:
        self.setFixedWidth(w)

    _anim_width = pyqtProperty(int, _get_anim_width, _set_anim_width)


    def _icon_color(self) -> str:
        return (
            Palette.D_TEXT_MAIN
            if ThemeManager.get_theme() == "dark"
            else Palette.L_TEXT_MAIN
        )

    def _populate(self) -> None:
        color = self._icon_color()
        self._list.clear()
        for data in self._items_data:
            item = QListWidgetItem(data["label"])
            item.setIcon(_make_svg_icon(data.get("icon", "devices"), color))
            item.setSizeHint(QSize(self.EXPANDED_WIDTH, 40))
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _refresh_icons(self) -> None:
        color = self._icon_color()
        for i, data in enumerate(self._items_data):
            it = self._list.item(i)
            if it:
                it.setIcon(_make_svg_icon(data.get("icon", "devices"), color))

        toggle_icon_key = "expand" if self._collapsed else "collapse"
        self._toggle_btn.setIcon(_make_svg_icon(toggle_icon_key, color))


    def toggle(self) -> None:
        self._collapsed = not self._collapsed
        target = self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH
        self._anim.stop()
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target)
        self._anim.start()

        self._refresh_icons()

    def set_collapsed(self, collapsed: bool) -> None:
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed
        self._anim.stop()
        self.setFixedWidth(self.COLLAPSED_WIDTH if collapsed else self.EXPANDED_WIDTH)
        self._refresh_icons()
        self._list.update()

    def setCurrentRow(self, row: int) -> None:
        self._list.setCurrentRow(row)

    def currentRow(self) -> int:
        return self._list.currentRow()

    def item(self, row: int) -> QListWidgetItem | None:
        return self._list.item(row)

    def blockSignals(self, block: bool) -> bool:
        self._list.blockSignals(block)
        return super().blockSignals(block)

    def apply_theme(self) -> None:
        is_dark = ThemeManager.get_theme() == "dark"
        self.setStyleSheet(
            Style.AnimatedListBar.container_dark
            if is_dark else
            Style.AnimatedListBar.container_light
        )
        self._list.setStyleSheet(
            Style.AnimatedListBar.list_dark
            if is_dark else
            Style.AnimatedListBar.list_light
        )
        self._toggle_btn.setStyleSheet(
            Style.AnimatedListBar.toggle_dark
            if is_dark else
            Style.AnimatedListBar.toggle_light
        )
        self._refresh_icons()