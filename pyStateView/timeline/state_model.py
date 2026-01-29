from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Event:
    timestamp: float
    state_id: str
    extra: Dict[str, Any] = field(default_factory=dict)


class StateTimelineModel:
    def __init__(self):
        self._events: List[Event] = []
        self._state_set = set()

    def append_event(self, timestamp: float, state_id: str, extra: Optional[Dict[str, Any]] = None) -> Event:
        event = Event(timestamp=timestamp, state_id=state_id, extra=extra or {})
        self._events.append(event)
        self._state_set.add(state_id)
        return event

    def clear(self) -> None:
        self._events.clear()
        self._state_set.clear()

    @property
    def events(self) -> List[Event]:
        return list(self._events)

    def event_count(self) -> int:
        return len(self._events)

    def states(self) -> List[str]:
        return sorted(self._state_set, key=str)

    def get_event(self, index: int) -> Optional[Event]:
        if 0 <= index < len(self._events):
            return self._events[index]
        return None

    def iter_events(self):
        return iter(self._events)

    def index_for_time(self, timestamp: float) -> int:
        if not self._events:
            return -1
        for idx in range(len(self._events) - 1, -1, -1):
            if self._events[idx].timestamp <= timestamp:
                return idx
        return 0
