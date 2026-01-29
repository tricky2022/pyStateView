import math
from typing import Dict, Optional

from PyQt5.QtCore import Qt, QRectF, QPointF, QEvent
from PyQt5.QtGui import QColor, QBrush, QPen, QPainter, QFont, QPalette, QFontMetricsF
from PyQt5.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QToolTip,
    QSizePolicy,
    QFrame,
)

from .state_model import StateTimelineModel, Event
from ..utils.color_map import state_color, CURRENT_OUTLINE, is_alarm_state
from ..utils.time_utils import format_timestamp, format_duration


class PhaseFlow(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.model = StateTimelineModel()
        self.color_map: Dict[str, str] = {}
        self.state_order: Optional[list] = None
        self.alarm_keywords = ["ALARM", "FAULT", "ERROR"]

        self._row_height = 36
        self._lane_margin = 14
        self._time_scale = 120.0
        self._label_width = 120
        self._label_padding = 18
        self._left_padding = 140
        self._top_padding = 16
        self._axis_height = 26
        self._current_index = -1
        self._last_time = 0.0
        self._current_time = None
        self._base_time = None
        self._time_label_mode = "relative"
        # disable auto follow-tail by default to keep left Y-axis and labels always visible
        self._follow_tail = False
        self._window_duration = 12.0

        self._items = []
        self._state_labels = []
        self._background = None
        self._grid_color = None
        self._text_color = None
        self._axis_color = None
        self._label_font = QFont("Consolas", 9)
        self._tick_font = QFont("Consolas", 8)

        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(180)
        self.setObjectName("psvPhaseFlow")
        self._update_palette()

    def clear(self):
        self.model.clear()
        self._scene.clear()
        self._items.clear()
        self._state_labels.clear()
        self._current_index = -1
        self._base_time = None
        self._current_time = None

    def append_event(self, timestamp: float, state_id: str, extra: Optional[dict] = None):
        event = self.model.append_event(timestamp, state_id, extra=extra)
        if self._base_time is None:
            self._base_time = timestamp
        self._last_time = max(self._last_time, timestamp)
        self._current_time = self._last_time
        self._refresh_states()
        self._draw_axes()
        self._append_item(len(self.model.events) - 1, event)
        self._update_scene_rect()
        self._apply_follow_tail()
        self.ensureVisible(QRectF(self._scene.sceneRect().right() - 10, 0, 10, self._scene.height()))
        return event

    def set_current_index(self, index: int):
        self._current_index = index
        self._update_current_highlight()

    def set_color_map(self, color_map: Dict[str, str]):
        self.color_map = color_map
        self._rebuild_items()

    def set_state_order(self, states):
        self.state_order = list(states) if states else None
        self._refresh_states()
        self._draw_axes()
        self._rebuild_items()

    def set_time_scale(self, pixels_per_second: float):
        self._time_scale = max(10.0, pixels_per_second)
        self._rebuild_items()

    def set_follow_tail(self, enabled: bool):
        self._follow_tail = bool(enabled)

    def set_window_duration(self, seconds: float):
        self._window_duration = max(1.0, seconds)
        self._apply_follow_tail()

    def set_current_time(self, timestamp: float):
        self._current_time = max(self._last_time, timestamp)
        self._last_time = max(self._last_time, timestamp)
        if self._items:
            last_item = self._items[-1]
            last_rect = last_item.rect()
            end_x = self._left_padding + self._current_time * self._time_scale
            last_item.setRect(QRectF(last_rect.left(), last_rect.top(), max(2.0, end_x - last_rect.left()), last_rect.height()))
        self._update_scene_rect()
        self._apply_follow_tail()
        self.viewport().update()

    def set_time_label_mode(self, mode: str):
        if mode not in ("relative", "absolute", "auto"):
            return
        self._time_label_mode = mode
        self.viewport().update()

    @property
    def base_time(self):
        return self._base_time

    def zoom_in(self):
        self.set_time_scale(self._time_scale * 1.25)

    def zoom_out(self):
        self.set_time_scale(self._time_scale / 1.25)

    def _refresh_states(self):
        states = self.state_order or self.model.states()
        self._state_labels = states
        self._update_label_width()

    def _state_index(self, state_id: str) -> int:
        states = self._state_labels
        if state_id in states:
            return states.index(state_id)
        states.append(state_id)
        return states.index(state_id)

    def _append_item(self, index: int, event: Event):
        state_index = self._state_index(event.state_id)
        lane_y = self._top_padding + state_index * self._row_height
        start_x = self._left_padding + event.timestamp * self._time_scale
        end_time = self._current_time if self._current_time is not None else self._last_time
        end_x = self._left_padding + end_time * self._time_scale
        height = self._row_height - self._lane_margin

        rect = QRectF(start_x, lane_y, max(2.0, end_x - start_x), height)
        color = state_color(event.state_id, self.color_map, alarm_keywords=self.alarm_keywords)
        item = QGraphicsRectItem(rect)
        item.setBrush(QBrush(color))
        item.setPen(QPen(Qt.NoPen))
        item.setData(0, index)
        item.setToolTip(" ")
        self._scene.addItem(item)
        self._items.append(item)

        if is_alarm_state(event.state_id, self.alarm_keywords):
            item.setPen(QPen(QColor("#F5E663"), 1))

        if index > 0:
            prev_item = self._items[index - 1]
            prev_rect = prev_item.rect()
            prev_item.setRect(QRectF(prev_rect.left(), prev_rect.top(), start_x - prev_rect.left(), prev_rect.height()))

    def _rebuild_items(self):
        events = self.model.events
        self._scene.clear()
        self._items.clear()
        self._draw_axes()
        for idx, event in enumerate(events):
            self._append_item(idx, event)
        self._update_current_highlight()
        self._update_scene_rect()

    def _update_label_width(self):
        if not self._state_labels:
            self._label_width = 80
            self._left_padding = self._label_width + self._label_padding * 2
            return
        metrics = QFontMetricsF(self._label_font)
        width = max(metrics.horizontalAdvance(str(state)) for state in self._state_labels)
        self._label_width = max(80, int(width) + self._label_padding * 2)
        self._left_padding = self._label_width + self._label_padding

    def _update_current_highlight(self):
        for idx, item in enumerate(self._items):
            pen = QPen(Qt.NoPen)
            if idx == self._current_index:
                pen = QPen(QColor(CURRENT_OUTLINE), 2)
            item.setPen(pen)

    def _draw_axes(self):
        for label_item in self._scene.items():
            if isinstance(label_item, QGraphicsSimpleTextItem):
                self._scene.removeItem(label_item)

        for idx, state in enumerate(self._state_labels):
            y = self._top_padding + idx * self._row_height
            text_item = QGraphicsSimpleTextItem(state)
            text_item.setFont(self._label_font)
            text_item.setBrush(QBrush(self._text_color))
            text_item.setPos(self._label_padding, y)
            self._scene.addItem(text_item)

    def _update_scene_rect(self):
        height = self._top_padding + max(1, len(self._state_labels)) * self._row_height + self._axis_height + 20
        timeline_width = self._left_padding + max(self._last_time * self._time_scale, 120)
        view_width = max(self.viewport().width(), 1)
        width = max(timeline_width, view_width)
        self._scene.setSceneRect(0, 0, width, height)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        item = self._scene.itemAt(pos, self.transform())
        if isinstance(item, QGraphicsRectItem):
            index = item.data(0)
            event_info = self.model.get_event(index)
            if event_info:
                duration = None
                if index + 1 < self.model.event_count():
                    duration = self.model.events[index + 1].timestamp - event_info.timestamp
                tooltip = (
                    f"State: {event_info.state_id}\n"
                    f"Time: {format_timestamp(event_info.timestamp, mode=self._time_label_mode, base_time=self._base_time)}\n"
                    f"Duration: {format_duration(duration)}\n"
                    f"Extra: {event_info.extra}"
                )
                QToolTip.showText(event.globalPos(), tooltip, self)
        super().mouseMoveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scene_rect()

    def set_model(self, model: StateTimelineModel):
        self.model = model
        self._refresh_states()
        self._draw_axes()
        self._rebuild_items()

    def _draw_background(self, painter, rect):
        painter.fillRect(rect, self._background)

        # subtle horizontal lane separators
        grid_pen = QPen(self._grid_color)
        grid_pen.setWidthF(0.0)
        painter.setPen(grid_pen)
        for idx, _ in enumerate(self._state_labels):
            y = self._top_padding + idx * self._row_height
            lane_y = y + self._row_height - self._lane_margin
            painter.drawLine(QPointF(self._left_padding, lane_y), QPointF(rect.right(), lane_y))

        axis_y = self._top_padding + max(1, len(self._state_labels)) * self._row_height + 6
        axis_pen = QPen(self._axis_color)
        axis_pen.setWidthF(1.2)
        painter.setPen(axis_pen)
        painter.drawLine(QPointF(self._left_padding, axis_y), QPointF(rect.right(), axis_y))

        tick_step = self._time_tick_step()
        start_time = max(0.0, (rect.left() - self._left_padding) / self._time_scale)
        end_time = (rect.right() - self._left_padding) / self._time_scale
        tick = math.floor(start_time / tick_step) * tick_step
        painter.setFont(self._tick_font)
        while tick <= end_time:
            x = self._left_padding + tick * self._time_scale
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(x, self._top_padding), QPointF(x, axis_y))
            painter.setPen(axis_pen)
            painter.drawLine(QPointF(x, axis_y), QPointF(x, axis_y + 6))
            label = format_timestamp(
                (self._base_time or 0.0) + tick,
                mode=self._time_label_mode,
                base_time=self._base_time,
            )
            painter.drawText(QPointF(x + 2, axis_y + 18), label)
            tick += tick_step

        if self._current_time is not None:
            current_x = self._left_padding + self._current_time * self._time_scale
            marker_pen = QPen(self._axis_color)
            marker_pen.setWidthF(1.4)
            painter.setPen(marker_pen)
            painter.drawLine(QPointF(current_x, self._top_padding), QPointF(current_x, axis_y))

    def _apply_follow_tail(self):
        if not self._follow_tail or self._current_time is None:
            return
        window_width = self._window_duration * self._time_scale
        right_x = self._left_padding + self._current_time * self._time_scale
        left_x = max(self._left_padding, right_x - window_width)
        self.ensureVisible(QRectF(left_x, 0, window_width, self._scene.height()), 0, 0)

    def _update_palette(self):
        palette = self.palette()
        window = palette.color(QPalette.Window)
        text = palette.color(QPalette.Text)

        # background直接用窗口色，保证与主题一致
        self._background = window
        self._text_color = text

        # 根据亮度选择网格和轴线的对比度（偏淡的工业风）
        lightness = window.lightness()
        grid = QColor(text)
        axis = QColor(text)
        if lightness > 128:
            # 浅色主题：网格更淡，轴线略深
            grid.setAlpha(55)
            axis.setAlpha(180)
        else:
            # 深色主题：网格稍亮，轴线更亮
            grid.setAlpha(90)
            axis.setAlpha(220)

        self._grid_color = grid
        self._axis_color = axis

    def changeEvent(self, event):
        if event.type() in (QEvent.PaletteChange, QEvent.StyleChange):
            self._update_palette()
            self._rebuild_items()
        super().changeEvent(event)

    def _time_tick_step(self):
        target_px = 110.0
        seconds = max(0.001, target_px / self._time_scale)
        steps = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 60, 120, 300, 600]
        for step in steps:
            if step >= seconds:
                return step
        return steps[-1]

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        self._draw_background(painter, rect)
