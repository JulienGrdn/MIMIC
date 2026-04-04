import logging
import os
import socket
import uuid
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QFrame, QPushButton, QMessageBox, QGridLayout
from PyQt6.QtGui import QPixmap
from mimic.assets.csstyle import Style, Palette
from mimic.assets.theme_manager import ThemeManager
from mimic.widgets.smaller_toggle import AnimatedToggle
from mimic.devices.frontend.mqtt_broker_registry import get_shared_handler
from mimic.assets.instance_state import InstanceState, STATE_MASTER, STATE_SLAVE
from mimic.assets.os_theme import get_system_theme
from mimic.widgets.popups import Popups

logger = logging.getLogger(__name__)

ASSETS_DIR   = os.path.join(os.getcwd(), "src", "gui", "assets")
MASTER_TOPIC = "MIMICsoftware/Master"
_CLAIM_DELAY_MS = 500


class _Card(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("about_card")
        self._vbox = QVBoxLayout(self)
        self._vbox.setContentsMargins(16, 14, 16, 14)
        self._vbox.setSpacing(1)

        if title:
            self._title_lbl = QLabel(title.upper())
            self._title_lbl.setObjectName("card_section_title")
            self._vbox.addWidget(self._title_lbl)
            self._vbox.addWidget(_hline())

    def body(self) -> QVBoxLayout:
        return self._vbox

    def apply_theme(self, is_dark: bool):
        self.setStyleSheet(
            Style.Frame.container_dark if is_dark else Style.Frame.container_light
        )
        if hasattr(self, '_title_lbl'):
            color = "#888" if is_dark else "#aaa"
            self._title_lbl.setStyleSheet(
                f"font-size:9pt; letter-spacing:1.5px; color:{color}; font-weight:bold;"
            )


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


def _labeled_row(label_text: str, right: QWidget) -> QHBoxLayout:
    h = QHBoxLayout()
    h.setSpacing(10)
    lbl = QLabel(label_text)
    lbl.setMinimumWidth(100)
    h.addWidget(lbl)
    h.addWidget(right, 1)
    return h


class AboutTab(QWidget):
    def __init__(self,
                 broker_address: str = "",
                 on_reconnect=None,
                 on_reload=None,
                 loaded_instruments = None
                 ):
        super().__init__()
        self.num_instr = len(loaded_instruments)
        self._broker_address = broker_address
        self._on_reconnect   = on_reconnect
        self._on_reload      = on_reload

        self._client_id    = uuid.uuid4().hex[:10]
        self._hostname     = socket.gethostname()
        self._prompt       = f"{self._hostname}@{self._client_id}"
        self._master_topic = MASTER_TOPIC.format(hostname=self._hostname)

        self._claim_timer = QTimer(self)
        self._claim_timer.setSingleShot(True)
        self._claim_timer.timeout.connect(self._publish_claim)

        self._follow_system = False
        self._system_timer  = QTimer(self)
        self._system_timer.setInterval(3000)
        self._system_timer.timeout.connect(self._check_system_theme)

        self._cards: list[_Card] = []

        self._init_ui()
        self._connect_master_mqtt()
        self.apply_theme()

        self.info_message = Popups()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(Style.Scroll.transparent)
        outer.addWidget(scroll)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(14)
        cl.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(content)

        c_info = _Card()
        self._cards.append(c_info)

        self.lbl_title = QLabel("MIMIC Control Software")
        self.lbl_title.setObjectName("about_title")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_info.body().addWidget(self.lbl_title)

        accent = "#7BD6C4"
        self.lbl_desc = QLabel(
            f"<p style='text-align:center; font-family:Segoe UI,sans-serif; "
            f"font-size:14pt; margin:0;'>"
            f"<b style='color:{accent}'>M</b>QTT&nbsp;"
            f"<b style='color:{accent}'>I</b>nterface for&nbsp;"
            f"<b style='color:{accent}'>M</b>odular&nbsp;"
            f"<b style='color:{accent}'>I</b>nstrument&nbsp;"
            f"<b style='color:{accent}'>C</b>ontrol</p>"
        )
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_info.body().addWidget(self.lbl_desc)

        self._logo_label = QLabel()
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_logo()
        c_info.body().addWidget(self._logo_label)

        cl.addWidget(c_info)

        grid = QGridLayout()
        grid.setSpacing(14)

        button_width = 150

        # Row 0, Col 0
        c_conn = _Card("Connection")
        self._cards.append(c_conn)
        self.lbl_broker = QLabel(self._broker_address or "—")
        self.lbl_broker.setObjectName("about_value")
        c_conn.body().addLayout(_labeled_row("Broker", self.lbl_broker))

        self.btn_reconnect = QPushButton("Reconnect")
        self.btn_reconnect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reconnect.setFixedWidth(button_width)
        self.btn_reconnect.clicked.connect(self._do_reconnect)

        conn_btn_row = QHBoxLayout()
        conn_btn_row.addStretch()
        conn_btn_row.addWidget(self.btn_reconnect)
        c_conn.body().addLayout(conn_btn_row)

        grid.addWidget(c_conn, 0, 0)

        # Row 0, Col 1
        c_inst = _Card("Instance")
        self._cards.append(c_inst)
        lbl_host = QLabel(self._hostname)
        lbl_host.setObjectName("about_value")
        c_inst.body().addLayout(_labeled_row("Host", lbl_host))
        self.lbl_master = QLabel("connecting…")
        self.lbl_master.setObjectName("about_value")
        c_inst.body().addLayout(_labeled_row("Role", self.lbl_master))

        self.btn_take_master = QPushButton("Take Master")
        self.btn_take_master.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_take_master.setFixedWidth(button_width)
        self.btn_take_master.setVisible(False)
        self.btn_take_master.clicked.connect(self._publish_claim)

        inst_btn_row = QHBoxLayout()
        inst_btn_row.addStretch()
        inst_btn_row.addWidget(self.btn_take_master)
        c_inst.body().addLayout(inst_btn_row)

        grid.addWidget(c_inst, 0, 1)

        # Row 1, Col 0
        c_dev = _Card("Devices")
        self._cards.append(c_dev)

        self.lbl_instr = QLabel(f"Config file loaded with {str(self.num_instr)} devices.")
        c_dev.body().addLayout(_labeled_row("Info", self.lbl_instr))

        self.btn_reload = QPushButton("Reload Devices")
        self.btn_reload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reload.setFixedWidth(button_width)
        self.btn_reload.clicked.connect(self._do_reload)

        dev_btn_row = QHBoxLayout()
        dev_btn_row.addStretch()
        dev_btn_row.addWidget(self.btn_reload)
        c_dev.body().addLayout(dev_btn_row)

        grid.addWidget(c_dev, 1, 0)

        c_app = _Card("Appearance")
        self._cards.append(c_app)
        self.toggle_dark = AnimatedToggle()
        self.toggle_dark.setObjectName("settings_dark_mode")
        self.toggle_dark.setChecked(ThemeManager.get_theme() == "dark")
        self.toggle_dark.toggled.connect(self._on_dark_toggled)
        c_app.body().addLayout(_labeled_row("Dark Mode", self.toggle_dark))
        self.toggle_follow = AnimatedToggle()
        self.toggle_follow.setObjectName("settings_follow_system")
        self.toggle_follow.toggled.connect(self._on_follow_toggled)
        c_app.body().addLayout(_labeled_row("Follow System", self.toggle_follow))

        grid.addWidget(c_app, 1, 1)

        cl.addLayout(grid)

        cl.addStretch()

        footer_text = (
            "<div style='text-align:center;'>"
            "Created by <b>Julien Grondin</b> | Licensed under the <b>GNU GPLv3</b><br>"
            "Third-Party: PyQt6 (GPLv3) &bull; paho-mqtt (EPL/EDLC) &bull; pyqtgraph (MIT) &bull; "
            "PyYAML (MIT) &bull; NumPy (BSD-3) &bull; QtPy (MIT)"
            "</div>"
        )
        self.lbl_footer = QLabel(footer_text)
        self.lbl_footer.setWordWrap(True)
        self.lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_footer.setObjectName("about_footer")
        cl.addWidget(self.lbl_footer)


    def _load_logo(self):
        for ext in ("MIMIC.png", "MIMIC.ico", "MIMIC.svg"):
            path = os.path.join(ASSETS_DIR, ext)
            if os.path.exists(path):
                pix = QPixmap(path).scaledToHeight(
                    72, Qt.TransformationMode.SmoothTransformation)
                self._logo_label.setPixmap(pix)
                return
        self._logo_label.setText(
            "<span style='font-size:30px; font-weight:bold;'>MIMIC</span>")

    def _connect_master_mqtt(self):
        try:
            self._mqtt = get_shared_handler(self._broker_address or "localhost")
            self._mqtt.connection_status.connect(self._on_connection_status)
            self._mqtt.message_received.connect(self._on_mqtt_message)
            is_connected = False
            if hasattr(self._mqtt, 'is_connected'):
                is_connected = self._mqtt.is_connected() if callable(
                    self._mqtt.is_connected) else self._mqtt.is_connected
            elif hasattr(self._mqtt, 'client') and hasattr(self._mqtt.client, 'is_connected'):
                is_connected = self._mqtt.client.is_connected()
            self._refresh_broker_label(is_connected)
            if is_connected:
                self._mqtt.subscribe(self._master_topic)
                self._claim_timer.start(_CLAIM_DELAY_MS)

        except Exception as e:
            logger.exception("Master MQTT init failed")
            self._apply_state(STATE_SLAVE)

    def _on_connection_status(self, connected: bool):
        self._refresh_broker_label(connected)
        if connected:
            self._mqtt.subscribe(self._master_topic)
            self._claim_timer.start(_CLAIM_DELAY_MS)

    def _refresh_broker_label(self, connection = False):
        actual = getattr(self._mqtt, 'broker', None)
        configured = self._broker_address or "—"

        if connection:
            if actual and actual != configured:
                self.lbl_broker.setText(
                    f"{actual} "
                    f"<span style='font-size:9pt; color:#e67e22;'>"
                    f"(fallback, configured: {configured})</span>"
                )
            elif actual:
                self.lbl_broker.setText(actual)
        else:
            self.lbl_broker.setText(
                f"<span style='color:#e74c3c;'>disconnected</span> "
                f"<span style='font-size:9pt; color:#888;'>(configured: {configured})</span>"
            )

    def _publish_claim(self):
        """Publish our client_id as a retained claim."""
        self._claim_timer.stop()
        try:
            self._mqtt.client.publish(
                self._master_topic,
                self._prompt,
                qos=1,
                retain=True
            )
        except Exception as e:
            logger.exception("Failed to publish master claim")

    def release_claim(self):
        """release our client_id if claimed."""
        if InstanceState.is_master():
            try:
                self._mqtt.client.publish(
                    self._master_topic,
                    "",
                    qos=1,
                    retain=True
                )
            except Exception as e:
                logger.exception("Failed to release master claim")

    def _on_mqtt_message(self, topic: str, payload: str):
        if topic != self._master_topic:
            return
        self._claim_timer.stop()
        if payload == self._prompt:
            self._apply_state(STATE_MASTER)
        elif payload == "":
            pass
        else:
            was_master = InstanceState.state == STATE_MASTER
            self._apply_state(STATE_SLAVE)
            if was_master:
                self.info_message.master_taken(self, payload)

    def _apply_state(self, state: str):
        InstanceState.state = state

        if state == STATE_MASTER:
            self.lbl_master.setText(
                "<div style='text-align:left;'>"
                f"<b style='color:#2ecc71;'>MASTER</b>"
                f"<span style='font-size:9pt; color:#888;'>&nbsp;&nbsp;{self._client_id}</span>"
                "</div>"
            )
            self.btn_take_master.setVisible(False)

        elif state == STATE_SLAVE:
            self.lbl_master.setText(
                "<div style='text-align:left;'>"
                "<b style='color:#e67e22;'>LISTENER</b>"
                "<span style='font-size:9pt; color:#888;'>&nbsp;&nbsp;read-only</span>"
                "</div>"
            )
            self.btn_take_master.setVisible(True)

        else:
            self.lbl_master.setText("connecting…")
            self.btn_take_master.setVisible(False)


    def _do_reconnect(self):
        self.btn_reconnect.setEnabled(False)
        self.btn_reconnect.setText("Reconnecting…")
        try:
            if self._on_reconnect:
                self._on_reconnect()
            QTimer.singleShot(1500, self._after_reconnect)
        except Exception as e:
            logger.exception("Reconnect error")
            self._after_reconnect()

    def _after_reconnect(self):
        self.btn_reconnect.setEnabled(True)
        self.btn_reconnect.setText("Reconnect")
        try:
            self._mqtt.subscribe(self._master_topic)
            self._claim_timer.start(_CLAIM_DELAY_MS)
        except Exception:
            pass

    def _do_reload(self):
        self.btn_reload.setEnabled(False)
        self.btn_reload.setText("Reloading…")
        try:
            if self._on_reload:
                count = self._on_reload()
                self.lbl_instr.setText(f"Config file loaded with {count} devices.")
                logger.debug("Device reload returned %s instruments.", count)
        except Exception as e:
            logger.exception("Reload error")
        QTimer.singleShot(1500, lambda: (
            self.btn_reload.setEnabled(True),
            self.btn_reload.setText("Reload Devices")
        ))

    def _on_dark_toggled(self, checked: bool):
        if not self._follow_system:
            ThemeManager.set_theme("dark" if checked else "light")

    def _on_follow_toggled(self, checked: bool):
        self._follow_system = checked
        if checked:
            self._system_timer.start()
            self._check_system_theme()
        else:
            self._system_timer.stop()

    def _check_system_theme(self):
        try:
            theme = get_system_theme()
            if ThemeManager.get_theme() != theme:
                ThemeManager.set_theme(theme)
                self.toggle_dark.blockSignals(True)
                self.toggle_dark.set_state(True if theme == "dark" else False)
                self.toggle_dark.blockSignals(False)
        except Exception as e:
            logger.debug("OS theme detection error: %s", e)

    def apply_theme(self):
        theme   = ThemeManager.get_theme()
        is_dark = theme == "dark"

        self.setStyleSheet(Style.Default.dark if is_dark else Style.Default.light)

        title_color = Palette.D_TEXT_MAIN if is_dark else Palette.L_TEXT_MAIN
        self.lbl_title.setStyleSheet( f"font-size:20px; font-weight:bold; color:{title_color};")

        desc_s = Style.Label.frequency_big_dark if is_dark else Style.Label.frequency_big
        self.lbl_desc.setStyleSheet(desc_s)

        val_s = Style.Label.parameter_dark if is_dark else Style.Label.parameter
        self.lbl_broker.setStyleSheet(val_s)
        self.lbl_master.setStyleSheet(val_s)

        footer_color = "#999999" if is_dark else "#555555"
        self.lbl_footer.setStyleSheet(f"font-size: 10px; color: {footer_color};")

        btn_s = Style.Button.suggested if hasattr(Style.Button, 'suggested') else ""
        for btn in (self.btn_reconnect, self.btn_reload, self.btn_take_master):
            btn.setStyleSheet(btn_s)

        for card in self._cards:
            card.apply_theme(is_dark)

        self.toggle_dark.blockSignals(True)
        self.toggle_dark.set_state(is_dark)
        self.toggle_dark.blockSignals(False)
