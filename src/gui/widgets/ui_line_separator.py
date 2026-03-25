from PyQt6.QtWidgets import QFrame

def qframe_line_separator():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    line.setStyleSheet("""
        QFrame {
            background-color: rgba(130, 130, 130, 0.2); /* Couleur grise discrète */
            border: none;
            max-height: 1px;
            min-height: 1px;
            margin-top: 1px;
            margin-bottom: 1px;
        }
    """)
    return line