from datetime import datetime


def format_timestamp(ts, mode="auto", base_time=None):
    if ts is None:
        return "-"
    if not isinstance(ts, (int, float)):
        return str(ts)
    if mode == "relative" or (mode == "auto" and abs(ts) < 10_000_000):
        origin = base_time if base_time is not None else 0.0
        seconds = ts - origin
        return f"t={seconds:.3f}s"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def format_duration(seconds):
    if seconds is None:
        return "-"
    if seconds < 0:
        return "-"
    if seconds < 1:
        return f"{seconds * 1000.0:.0f} ms"
    if seconds < 60:
        return f"{seconds:.2f} s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{minutes:.2f} min"
    hours = minutes / 60.0
    return f"{hours:.2f} h"
