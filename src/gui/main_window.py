import sys
import json
import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QPushButton, QApplication
)
from src.gui.assets.csstyle import Style
from src.gui.assets.theme_manager import ThemeManager
from src.gui.tabs.devices_tab import InstrumentPanel
from src.gui.tabs.live_update_tab import LiveUpdateWidget
from src.gui.tabs.scan_tab import ScanTab
from src.gui.tabs.about_tab import AboutTab
from src.gui.widgets.noscrollcombobox import NSCB
from src.gui.widgets.smaller_toggle import AnimatedToggle



CONFIG_PATH = os.path.join(os.getcwd(), "config", "ui_parameters.json")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIMIC")
        self.setup_os_identity()
        self.resize(1000, 650)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(110)
        self.sidebar.setStyleSheet(Style.List.light)
        self.sidebar.addItem("Devices")
        self.sidebar.addItem("Live Update")
        self.sidebar.addItem("Scan")
        self.sidebar.addItem("About")
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self.display_page)
        main_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)

        # Devices
        self.devices_panel = InstrumentPanel()
        self.stack.addWidget(self.devices_panel)

        # Live Update
        self.live_update_page = LiveUpdateWidget(self.devices_panel.loaded_instruments)
        self.stack.addWidget(self.live_update_page)

        # Scan
        self.scan_page = ScanTab(self.devices_panel.loaded_instruments)
        self.stack.addWidget(self.scan_page)

        # About
        self.about_page = AboutTab()
        self.stack.addWidget(self.about_page)

        # Theme
        ThemeManager.instance().theme_changed.connect(self.apply_theme)
        self.apply_theme(ThemeManager.get_theme())

        # Load UI State
        self.load_ui_state()

        # Connect all buttons to save state
        for btn in self.findChildren(QPushButton):
            btn.clicked.connect(self.save_ui_state)

    def display_page(self, index):
        self.stack.setCurrentIndex(index)

    def apply_theme(self, theme):
        is_dark = theme == "dark"
        self.setStyleSheet(Style.Default.dark if is_dark else Style.Default.light)
        self.sidebar.setStyleSheet(Style.List.dark if is_dark else Style.List.light)
        if hasattr(self.devices_panel, 'apply_theme'):
            self.devices_panel.apply_theme()

        if hasattr(self.live_update_page, 'apply_theme'):
            self.live_update_page.apply_theme()

        if hasattr(self.scan_page, 'apply_theme'):
            self.scan_page.apply_theme()

        if hasattr(self.about_page, 'apply_theme'):
            self.about_page.apply_theme()

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

        try:
            config_dir = os.path.dirname(CONFIG_PATH)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(CONFIG_PATH, 'w') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            print(f"Error saving UI state: {e}")

    def load_ui_state(self):
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, 'r') as f:
                state = json.load(f)
            for key, value in state.items():
                widgets = self.findChildren(QWidget, key)
                for widget in widgets:
                    old_block = widget.blockSignals(True)
                    try:
                        if isinstance(widget, QLineEdit):
                            widget.setText(str(value))
                        elif isinstance(widget, QComboBox) or isinstance(widget, NSCB):
                            widget.setCurrentIndex(int(value))
                        elif isinstance(widget, AnimatedToggle):
                            widget.set_state(bool(value))
                    finally:
                        widget.blockSignals(old_block)
            if state.get("settings_dark_mode"):
                ThemeManager.set_theme("dark")

        except Exception as e:
            print(f"Error loading UI state: {e}")

    def setup_os_identity(self):
        """
        Sets the application ID so the Taskbar/Dock icon groups correctly
        and doesn't show up as a generic Python launcher.
        """
        app_id = "com.github.juliengrdn.mimic"
        assets_dir = os.path.join(os.getcwd(), 'src', 'gui', 'assets')
        icon_path = os.path.join(assets_dir, 'MIMIC.ico')

        if os.path.exists(icon_path):
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))

        app = QApplication.instance()
        if app:
            app.setApplicationName("MIMIC")
            app.setApplicationDisplayName("MIMIC")
            app.setOrganizationName("JulienGrdn")
            app.setOrganizationDomain("github.com")
            
        if 'linux' in sys.platform:
            app.setDesktopFileName(app_id)

        if sys.platform == 'win32':
            import ctypes
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except (AttributeError, OSError):
                pass
