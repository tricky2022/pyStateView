from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QColor, QPainter, QPalette
from PyQt5.QtWidgets import QWidget

from ..utils.color_map import state_color, is_alarm_state


class StateIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state_id = None
        self._color_map = {}
        self._alarm_keywords = ["ALARM", "FAULT", "ERROR"]
        self._blink = False
        self._blink_on = True
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self.setMinimumSize(90, 50)
        self.setObjectName("psvStateIndicator")
        self._background = None
        self._blink_off = None
        self._update_palette()

    def set_state(self, state_id, blink=False):
        self._state_id = state_id
        self._blink = blink or is_alarm_state(state_id, self._alarm_keywords)
        if self._blink:
            self._blink_timer.start(400)
        else:
            self._blink_timer.stop()
            self._blink_on = True
        self.update()

    def set_color_map(self, color_map):
        self._color_map = color_map
        self.update()

    def _toggle_blink(self):
        self._blink_on = not self._blink_on
        self.update()

    def _update_palette(self):
        palette = self.palette()
        self._background = palette.color(QPalette.Window)
        self._blink_off = palette.color(QPalette.Base).darker(120)

    def changeEvent(self, event):
        if event.type() in (QEvent.PaletteChange, QEvent.StyleChange):
            self._update_palette()
            self.update()
        super().changeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self._background)
        if self._state_id is None:
            return
        if self._blink and not self._blink_on:
            color = self._blink_off
        else:
            color = state_color(self._state_id, self._color_map, alarm_keywords=self._alarm_keywords)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        rect = self.rect().adjusted(8, 8, -8, -8)
        painter.drawRoundedRect(rect, 6, 6)
