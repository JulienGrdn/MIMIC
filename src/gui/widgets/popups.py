from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QWidget


class Popups:
    # Class-level list to prevent garbage collection of non-modal dialogs
    _active_popups = []

    @staticmethod
    def _apply_style(msg: QMessageBox, parent: QWidget = None):
        """Helper to force the dialog to inherit the main window's stylesheet."""
        if parent:
            top_level = parent.window()
            msg.setStyleSheet(top_level.styleSheet())

    @staticmethod
    def read_only(parent: QWidget = None) -> None:
        """
        Blocking informational dialog shown when a replica instance
        tries to send a command to an instrument.
        """
        msg = QMessageBox(parent)
        msg.setWindowTitle("Read-Only Instance")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("<b>This instance is in read-only mode.</b>")
        msg.setInformativeText(
            f"Commands cannot be sent from a replica instance.<br><br>"
            f"Go to the <i>About</i> tab and click "
            f"<b>Take Master</b> to enable control."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        Popups._apply_style(msg, parent)
        msg.exec()

    @staticmethod
    def master_taken(parent: QWidget = None,
                     new_owner_id: str = "",
                     hostname: str = "") -> None:
        """
        Non-blocking warning dialog shown to the instance that just lost
        master privilege.
        """
        msg = QMessageBox(parent)
        msg.setWindowTitle("Master Privilege Taken")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("<b>This instance is no longer the master.</b>")
        msg.setInformativeText(
            f"Instance <code>{new_owner_id}</code>"
            f"{f' on <b>{hostname}</b>' if hostname else ''} "
            f"has claimed the master role.<br><br>"
            f"Commands are now <b>read-only</b>. "
            f"Go to the <i>About</i> tab and click "
            f"<b>Take Master</b> to reclaim."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setWindowModality(Qt.WindowModality.NonModal)
        msg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        Popups._apply_style(msg, parent)
        Popups._active_popups.append(msg)
        msg.finished.connect(lambda: Popups._active_popups.remove(msg) if msg in Popups._active_popups else None)
        msg.show()