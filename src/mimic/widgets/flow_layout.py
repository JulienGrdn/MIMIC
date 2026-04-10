from PyQt6.QtWidgets import QLayout, QSizePolicy
from PyQt6.QtCore import Qt, QRect, QSize, QPoint

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _doLayout(self, rect, testOnly):
        if not self.itemList:
            return 0

        first_item = self.itemList[0]
        itemWidth = first_item.sizeHint().width()
        spacing = self.spacing()

        wid = first_item.widget()
        if spacing >= 0:
            spaceX = spacing
            spaceY = spacing
        elif wid:
            spaceX = wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton,
                                               QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal)
            spaceY = wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton,
                                               QSizePolicy.ControlType.PushButton, Qt.Orientation.Vertical)
        else:
            spaceX = 10
            spaceY = 10

        effective_width = itemWidth + spaceX
        if effective_width <= 0:
            effective_width = 1

        num_cols = max(1, (rect.width() + spaceX) // effective_width)

        col_heights = [rect.y()] * num_cols

        for item in self.itemList:
            min_col_idx = col_heights.index(min(col_heights))

            x = rect.x() + min_col_idx * effective_width
            y = col_heights[min_col_idx]

            itemHeight = item.sizeHint().height()

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), QSize(itemWidth, itemHeight)))

            col_heights[min_col_idx] = y + itemHeight + spaceY

        return max(col_heights) - rect.y()