from PyQt6.QtWidgets import QComboBox

class NSCB(QComboBox):
    def wheelEvent(self, event):
        event.ignore()