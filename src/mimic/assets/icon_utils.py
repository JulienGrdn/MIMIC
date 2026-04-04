from PyQt6.QtWidgets import QApplication, QStyle
from PyQt6.QtGui import QIcon, QPainter, QColor

class CustomIcon:
    """
    A utility class to generate recolored icons on the fly.
    """
    @staticmethod
    def _recolor(icon, color_input):
        """
        Internal helper: Takes a QIcon and returns a recolored QIcon.
        """
        size = 32
        pixmap = icon.pixmap(size, size)
        if isinstance(color_input, str):
            color = QColor(color_input)
        else:
            color = color_input
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()

        return QIcon(pixmap)

    @staticmethod
    def trash(color="white"):
        """
        Returns a system Trash icon in the specified color.
        """
        base_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        return CustomIcon._recolor(base_icon, color)

    @staticmethod
    def save(color="white"):
        """Example: Returns a Save icon."""
        base_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        return CustomIcon._recolor(base_icon, color)

    @staticmethod
    def close(color="white"):
        """Example: Returns a Close/X icon."""
        base_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)
        return CustomIcon._recolor(base_icon, color)