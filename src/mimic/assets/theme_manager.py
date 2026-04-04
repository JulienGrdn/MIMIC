from PyQt6.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    _instance = None
    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._theme = "light"

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_theme(cls):
        return cls.instance()._theme

    @classmethod
    def set_theme(cls, theme: str):
        if theme not in ["light", "dark"]:
            return
        if cls.instance()._theme != theme:
            cls.instance()._theme = theme
            cls.instance().theme_changed.emit(theme)

    @classmethod
    def toggle_theme(cls):
        new_theme = "dark" if cls.instance()._theme == "light" else "light"
        cls.set_theme(new_theme)
