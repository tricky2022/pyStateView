from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem


class StateTransitionTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["From", "To", "Count"])
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setObjectName("psvStateTransitionTable")
        self._update_palette()

    def _update_palette(self):
        palette = self.palette()
        self.setPalette(palette)

    def changeEvent(self, event):
        if event.type() in (QEvent.PaletteChange, QEvent.StyleChange):
            self._update_palette()
        super().changeEvent(event)

    def update_from_events(self, events):
        transitions = {}
        for idx in range(len(events) - 1):
            src = events[idx].state_id
            dst = events[idx + 1].state_id
            key = (src, dst)
            transitions[key] = transitions.get(key, 0) + 1
        self.setRowCount(len(transitions))
        for row, ((src, dst), count) in enumerate(transitions.items()):
            self.setItem(row, 0, QTableWidgetItem(str(src)))
            self.setItem(row, 1, QTableWidgetItem(str(dst)))
            self.setItem(row, 2, QTableWidgetItem(str(count)))
        self.resizeColumnsToContents()
