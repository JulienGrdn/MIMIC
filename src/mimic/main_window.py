import logging
import sys
import json
import os
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLineEdit, QComboBox, QCheckBox, QPushButton, QApplication
from PyQt6.QtGui import QColor
from mimic.assets.csstyle import Style
from mimic.assets.theme_manager import ThemeManager
from mimic.tabs.devices_tab import InstrumentPanel
from mimic.tabs.live_update_tab import LiveUpdateWidget
from mimic.tabs.scan_tab import ScanTab
from mimic.tabs.about_tab import AboutTab
from mimic.widgets.animatedlistbar import AnimatedListBar
from mimic.widgets.noscrollcombobox import NSCB
from mimic.widgets.smaller_toggle import AnimatedToggle
from mimic.devices.frontend.mqtt_broker_registry import get_shared_handler, stop_all_brokers
from mimic.assets.instance_state import STATE_SLAVE, InstanceState

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.getcwd(), "config", "ui_parameters.json")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIMIC")
        self.setup_os_identity()
        self.resize(1420, 690)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)

        self.sidebar = AnimatedListBar([
            {"label": "Devices",     "icon": "devices"},
            {"label": "Live Update", "icon": "chart"},
            {"label": "Scan",        "icon": "scan"},
            {"label": "Settings",    "icon": "settings"},
        ])
        self.sidebar.setCurrentRow(0)
        self.sidebar.current_row_changed.connect(self.display_page)
        main_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)

        # Devices
        self.devices_panel = InstrumentPanel()
        self.stack.addWidget(self.devices_panel)

        # Infer broker from config
        broker = self._infer_broker()

        # Live Update
        self.live_update_page = LiveUpdateWidget(self.devices_panel.loaded_instruments)
        self.stack.addWidget(self.live_update_page)

        # Scan
        self.scan_page = ScanTab(self.devices_panel.loaded_instruments)
        self.stack.addWidget(self.scan_page)

        # About
        self.about_page = AboutTab(
            broker_address=broker,
            on_reconnect=self._reconnect_broker,
            on_reload=self._reload_devices,
            loaded_instruments = self.devices_panel.loaded_instruments
        )
        self.stack.addWidget(self.about_page)

        InstanceState.changed.connect(self._on_master_state_changed)
        QTimer.singleShot(0, lambda: self._on_master_state_changed(InstanceState.state))

        # Theme
        ThemeManager.instance().theme_changed.connect(self.apply_theme)
        self.apply_theme(ThemeManager.get_theme())

        # Load UI State
        self.load_ui_state()

        # Connect all buttons to save state
        for btn in self.findChildren(QPushButton):
            btn.clicked.connect(self.save_ui_state)


    def _infer_broker(self) -> str:
        """Best-effort: read broker from devices config."""
        try:
            import yaml
            cfg_path = os.path.join(os.getcwd(), "config", "devices_configuration.yaml")
            if os.path.exists(cfg_path):
                with open(cfg_path) as f:
                    return yaml.safe_load(f).get("broker", "")
        except Exception:
            pass
        if self.devices_panel.loaded_instruments:
            return getattr(self.devices_panel.loaded_instruments[0], "broker", "")
        return ""

    def display_page(self, index: int):
        if index == 2 and not self._scan_unlocked:
            from mimic.widgets.popups import Popups
            Popups.read_only(self)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._restore_sidebar(self.stack.currentIndex()))
            return
        self.stack.setCurrentIndex(index)

    def _restore_sidebar(self, index: int):
        self.sidebar.blockSignals(True)
        self.sidebar.setCurrentRow(index)
        self.sidebar.blockSignals(False)

    def _reconnect_broker(self):
        try:
            broker = self._infer_broker() or "localhost"
            handler = get_shared_handler(broker)
            handler.stop()
            handler.start()
            logger.info("Broker reconnection requested.")
        except Exception as e:
            logger.exception("Broker reconnect failed")

    def _reload_devices(self):
        try:
            logger.info("Reloading devices…")
            self.devices_panel._load_and_display_devices()
            instruments = self.devices_panel.loaded_instruments
            if hasattr(self.live_update_page, 'set_instruments'):
                self.live_update_page.set_instruments(instruments)
            if hasattr(self.scan_page, 'set_instruments'):
                self.scan_page.set_instruments(instruments)
            logger.info("Devices reloaded (%d instruments).", len(instruments))
            return len(instruments)
        except Exception as e:
            logger.exception("Device reload failed")


    def _on_master_state_changed(self, state: str):
        """
        Dim the Scan sidebar item when slave.
        Clicks still fire so display_page can show the popup.
        """
        self._scan_unlocked = (state != STATE_SLAVE)

        scan_item = self.sidebar.item(2)
        if scan_item:
            if self._scan_unlocked:
                scan_item.setData(Qt.ItemDataRole.ForegroundRole, None)
            else:
                scan_item.setForeground(QColor("#555" if ThemeManager.get_theme() == "dark" else "#bbb"))
                if self.stack.currentIndex() == 2:
                    self.sidebar.setCurrentRow(3)

    def apply_theme(self, theme: str = None):
        theme   = theme or ThemeManager.get_theme()
        is_dark = theme == "dark"
        self.setStyleSheet(Style.Default.dark if is_dark else Style.Default.light)
        self.sidebar.apply_theme()
        self._on_master_state_changed(InstanceState.state)
        for page in (self.devices_panel, self.live_update_page,
                     self.scan_page, self.about_page):
            if hasattr(page, 'apply_theme'):
                page.apply_theme()

    def save_ui_state(self):
        state = {}
        for widget in self.findChildren(QLineEdit):
            if widget.objectName():
                state[widget.objectName()] = widget.text()
        for widget in self.findChildren(QComboBox):
            if widget.objectName():
                state[widget.objectName()] = widget.currentIndex()
        for widget in self.findChildren(QCheckBox):
            if widget.objectName():
                state[widget.objectName()] = widget.isChecked()

        state["sidebar_collapsed"] = self.sidebar._collapsed

        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.exception("Error saving UI state")

    def load_ui_state(self):
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, 'r') as f:
                state = json.load(f)
            for key, value in state.items():
                for widget in self.findChildren(QWidget, key):
                    widget.blockSignals(True)
                    try:
                        if isinstance(widget, QLineEdit):
                            widget.setText(str(value))
                        elif isinstance(widget, (QComboBox, NSCB)):
                            widget.setCurrentIndex(int(value))
                        elif isinstance(widget, AnimatedToggle):
                            widget.set_state(bool(value))
                    finally:
                        widget.blockSignals(False)

            if state.get("sidebar_collapsed"):
                self.sidebar.set_collapsed(True)
            if state.get("settings_dark_mode"):
                ThemeManager.set_theme("dark")
            if state.get("settings_follow_system"):
                self.about_page._on_follow_toggled(True)

        except Exception as e:
            logger.exception("Error loading UI state")


    def setup_os_identity(self):
        """
        Sets the application ID so the Taskbar/Dock icon groups correctly
        and doesn't show up as a generic Python launcher.
        """
        app_id    = "com.github.juliengrdn.mimic"
        icon_path = os.path.join(os.getcwd(), "src", "mimic", "assets", "MIMIC.ico")

        if os.path.exists(icon_path):
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))

        app = QApplication.instance()
        if app:
            app.setApplicationName("MIMIC")
            app.setApplicationDisplayName("MIMIC")
            app.setOrganizationName("JulienGrdn")
            app.setOrganizationDomain("github.com")
            if sys.platform.startswith("linux"):
                app.setDesktopFileName(app_id)

        if sys.platform == "win32":
            import ctypes
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except (AttributeError, OSError):
                pass

    def closeEvent(self, event):
        self.save_ui_state()
        self.about_page.release_claim()
        try:
            stop_all_brokers()
        except Exception as e:
            logger.exception("MQTT disconnect error")


