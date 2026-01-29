from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem

from ..utils.time_utils import format_timestamp, format_duration


class EventLogView(QTableWidget):
    locate_event = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("psvEventLogView")
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Time", "State", "Duration", "Extra"])
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self._update_palette()

    def _update_palette(self):
        palette = self.palette()
        self.setPalette(palette)

    def changeEvent(self, event):
        if event.type() in (QEvent.PaletteChange, QEvent.StyleChange):
            self._update_palette()
        super().changeEvent(event)

    def update_from_events(self, events, base_time=None, time_mode="auto"):
        self.setRowCount(0)
        if not events:
            return
        if base_time is None:
            base_time = events[0].timestamp
        self.setRowCount(len(events))
        for idx, event in enumerate(events):
            duration = None
            if idx + 1 < len(events):
                duration = events[idx + 1].timestamp - event.timestamp
            time_item = QTableWidgetItem(format_timestamp(event.timestamp, mode=time_mode, base_time=base_time))
            state_item = QTableWidgetItem(str(event.state_id))
            dur_item = QTableWidgetItem(format_duration(duration))
            extra_item = QTableWidgetItem(str(event.extra))

            time_item.setData(Qt.UserRole, idx)
            self.setItem(idx, 0, time_item)
            self.setItem(idx, 1, state_item)
            self.setItem(idx, 2, dur_item)
            self.setItem(idx, 3, extra_item)
        self.resizeColumnsToContents()

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            item = self.item(index.row(), 0)
            if item:
                self.locate_event.emit(item.data(Qt.UserRole))
        super().mouseDoubleClickEvent(event)
