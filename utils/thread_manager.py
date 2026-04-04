"""
Wednesday AI Assistant — Thread Manager
Safe start/stop/health-check for named daemon threads.
Used by reminders, gesture control, and proactive conversation.
"""

import threading
from utils.logger import get_logger

log = get_logger("thread_mgr")


class ThreadManager:
    """Manages named background threads with clean start/stop."""

    def __init__(self):
        self._threads: dict[str, dict] = {}
        self._stop_events: dict[str, threading.Event] = {}

    def register(self, name: str, target, args: tuple = (),
                 daemon: bool = True) -> None:
        """
        Register a thread (does not start it yet).

        Args:
            name:   Unique thread name (e.g. 'reminder', 'gesture')
            target: The function the thread will run
            args:   Arguments to pass to the function
            daemon: If True, thread dies when main thread exits
        """
        stop_event = threading.Event()
        self._stop_events[name] = stop_event

        # The target function receives the stop_event as its first argument
        thread = threading.Thread(
            target=target,
            args=(stop_event, *args),
            name=f"wednesday-{name}",
            daemon=daemon,
        )
        self._threads[name] = {"thread": thread, "running": False}
        log.debug(f"Thread registered: {name}")

    def start(self, name: str) -> bool:
        """Start a registered thread. Returns True if started."""
        info = self._threads.get(name)
        if not info:
            log.error(f"Thread '{name}' not registered.")
            return False

        if info["running"] and info["thread"].is_alive():
            log.warning(f"Thread '{name}' is already running.")
            return True

        # If thread was already used, re-create it (threads can't restart)
        stop_event = self._stop_events[name]
        stop_event.clear()

        if not info["thread"].is_alive():
            old = info["thread"]
            new_thread = threading.Thread(
                target=old._target,
                args=old._args,
                name=old.name,
                daemon=old.daemon,
            )
            info["thread"] = new_thread

        info["thread"].start()
        info["running"] = True
        log.info(f"Thread '{name}' started.")
        return True

    def stop(self, name: str) -> bool:
        """Signal a thread to stop. Returns True if signaled."""
        if name not in self._stop_events:
            log.error(f"Thread '{name}' not registered.")
            return False

        self._stop_events[name].set()
        info = self._threads.get(name)
        if info:
            info["running"] = False
        log.info(f"Thread '{name}' stop signal sent.")
        return True

    def stop_all(self) -> None:
        """Signal all threads to stop."""
        for name in self._stop_events:
            self._stop_events[name].set()
            if name in self._threads:
                self._threads[name]["running"] = False
        log.info("All threads signaled to stop.")

    def is_running(self, name: str) -> bool:
        """Check if a thread is alive."""
        info = self._threads.get(name)
        if not info:
            return False
        return info["thread"].is_alive()

    def status(self) -> dict[str, bool]:
        """Return status of all threads."""
        return {name: self.is_running(name) for name in self._threads}


# ── Global instance ─────────────────────────────────────────────
thread_manager = ThreadManager()
