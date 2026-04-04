import logging
import sys
import subprocess
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


def get_system_theme() -> str:
    """
    Detects the operating system theme.
    Prioritizes direct OS queries over Qt to avoid startup sync lag.
    """
    try:
        if sys.platform.startswith("linux"):
            # D-Bus check
            cmd = [
                "dbus-send", "--print-reply=literal", "--reply-timeout=1000",
                "--dest=org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
                "org.freedesktop.portal.Settings.Read",
                "string:org.freedesktop.appearance", "string:color-scheme"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1)
            if "uint32 1" in result.stdout:
                return "dark"
            elif "uint32 0" in result.stdout:
                return "light"

            # Fallback to gsettings
            gsettings_cmd = ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"]
            g_result = subprocess.run(gsettings_cmd, capture_output=True, text=True)
            if "prefer-dark" in g_result.stdout:
                return "dark"

        elif sys.platform == "darwin":
            # macOS check
            result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], capture_output=True, text=True)
            if "Dark" in result.stdout:
                return "dark"
            else:
                return "light"

        elif sys.platform == "win32":
            # Windows registry check
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            with winreg.OpenKey(registry, r"...") as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            if value == 0:
                return "dark"
            else:
                return "light"

    except Exception as e:
        logger.debug("OS theme detection skipped: %s", e)

    try:
        app = QGuiApplication.instance()
        if app and hasattr(app, 'styleHints'):
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return "dark"
            elif scheme == Qt.ColorScheme.Light:
                return "light"
    except Exception:
        pass

    return "light"

if __name__ == "__main__":
    print(get_system_theme())