from typing import Dict

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor, QPainter, QPalette
from PyQt5.QtWidgets import QWidget

from ..utils.color_map import state_color


class StateDistributionBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state_durations: Dict[str, float] = {}
        self._color_map = {}
        self._total = 0.0
        self._background = None
        self._text_color = None
        self.setMinimumHeight(28)
        self.setObjectName("psvStateDistribution")
        self._update_palette()

    def update_from_events(self, events, start_time=None, end_time=None):
        self._state_durations.clear()
        if not events:
            self._total = 0.0
            self.update()
            return
        if start_time is None:
            start_time = events[0].timestamp
        if end_time is None:
            end_time = events[-1].timestamp
        for idx, event in enumerate(events):
            if event.timestamp < start_time:
                continue
            next_time = end_time
            if idx + 1 < len(events):
                next_time = events[idx + 1].timestamp
            duration = max(0.0, min(next_time, end_time) - event.timestamp)
            if duration <= 0:
                continue
            self._state_durations[event.state_id] = self._state_durations.get(event.state_id, 0.0) + duration
        self._total = sum(self._state_durations.values())
        self.update()

    def set_color_map(self, color_map):
        self._color_map = color_map
        self.update()

    def _update_palette(self):
        palette = self.palette()
        self._background = palette.color(QPalette.Window)
        self._text_color = palette.color(QPalette.Text)

    def changeEvent(self, event):
        if event.type() in (QEvent.PaletteChange, QEvent.StyleChange):
            self._update_palette()
            self.update()
        super().changeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background)
        if self._total <= 0:
            return
        x = 4
        width = self.width() - 8
        height = self.height() - 8
        for state_id, duration in self._state_durations.items():
            ratio = duration / self._total
            block_width = max(2, int(width * ratio))
            painter.setBrush(state_color(state_id, self._color_map))
            painter.setPen(Qt.NoPen)
            painter.drawRect(x, 4, block_width, height)
            x += block_width
