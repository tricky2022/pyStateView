from PyQt5.QtGui import QColor


DEFAULT_STATE_COLORS = [
    "#2E86AB",
    "#F6C85F",
    "#6F4E7C",
    "#9FD356",
    "#CA3C25",
    "#1E555C",
    "#C3B59F",
    "#3D5A80",
    "#EE6C4D",
    "#98C1D9",
]

ALARM_COLOR = "#D7263D"
FAULT_COLOR = "#A30015"
CURRENT_OUTLINE = "#F8F32B"


def is_alarm_state(state_id, alarm_keywords=None):
    if state_id is None:
        return False
    if alarm_keywords:
        return any(keyword.lower() in str(state_id).lower() for keyword in alarm_keywords)
    state_upper = str(state_id).upper()
    return "ALARM" in state_upper or "FAULT" in state_upper or "ERROR" in state_upper


def state_color(state_id, color_map=None, alarm_keywords=None):
    if is_alarm_state(state_id, alarm_keywords=alarm_keywords):
        if "FAULT" in str(state_id).upper() or "ERROR" in str(state_id).upper():
            return QColor(FAULT_COLOR)
        return QColor(ALARM_COLOR)
    if color_map and state_id in color_map:
        return QColor(color_map[state_id])
    if state_id is None:
        return QColor("#666666")
    index = abs(hash(str(state_id))) % len(DEFAULT_STATE_COLORS)
    return QColor(DEFAULT_STATE_COLORS[index])
