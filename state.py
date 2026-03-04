"""
Wednesday — Application State
Thread-safe global state for the assistant.
"""

import threading
from enum import Enum, auto


class AssistantState(Enum):
    SLEEPING = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    ERROR = auto()


class AppState:
    """Thread-safe state container for the assistant."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = AssistantState.SLEEPING
        self._running = True
        self._listeners = []

    @property
    def state(self) -> AssistantState:
        with self._lock:
            return self._state

    @state.setter
    def state(self, new_state: AssistantState):
        with self._lock:
            old = self._state
            self._state = new_state
        # Notify listeners outside lock to avoid deadlock
        for callback in self._listeners:
            try:
                callback(old, new_state)
            except Exception:
                pass

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    @running.setter
    def running(self, value: bool):
        with self._lock:
            self._running = value

    def on_state_change(self, callback):
        """Register a callback for state changes: callback(old_state, new_state)."""
        self._listeners.append(callback)

    def remove_listener(self, callback):
        """Remove a state change listener."""
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass


# Global singleton
app_state = AppState()
