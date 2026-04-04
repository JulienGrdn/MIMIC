import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush


class Graph(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.setBackground(QColor(0, 0, 0, 0))

        self.line_curve = self.plot(pen=pg.mkPen(QColor(70, 120, 250), width=2), symbol = 'o')
        self.dot_curve = self.plot(pen=pg.mkPen(QColor(70, 120, 250), width=0), symbol = 'o')

        self.showGrid(x=True, y=True, alpha=0.3)