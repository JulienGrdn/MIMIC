from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

class StabilityIndicator(QLabel):
    """A styled, pill-shaped badge indicating stability state with custom colors."""

    def __init__(
            self,
            parent=None,
            true_label="Stable",
            false_label="Unstable",
            true_color=None,
            false_color=None
    ):
        super().__init__(false_label, parent)
        self.true_label = true_label
        self.false_label = false_label
        self.true_color = true_color if true_color else "rgba(46, 204, 113, 1)" # Default Green
        self.false_color = false_color if false_color else "rgba(231, 76, 60, 1)" # Default Red

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(65, 20)
        self.set_state(False)

    def set_state(self, is_stable: bool):
        base_color = self.true_color if is_stable else self.false_color
        label_text = self.true_label if is_stable else self.false_label
        bg_color = base_color.replace(" 1)", " 0.15)").replace(",1)", ",0.15)")

        self.setText(label_text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)