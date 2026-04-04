"""
Wednesday AI Assistant — State Manager
Tracks the last command, last app, last result, and a rolling buffer
of the last N commands for short-term conversational context.
"""

from collections import deque
from utils.logger import get_logger
import config

log = get_logger("state")


class StateManager:
    """
    Singleton-style state tracker.
    Keeps short-term context of the assistant's activity.
    """

    def __init__(self):
        self.last_command: str = ""
        self.last_tool: str = ""
        self.last_result: str = ""
        self.last_app: str = ""
        self.context: dict = {}

        # Rolling buffer of recent commands (for conversational context)
        self._history = deque(maxlen=config.CONTEXT_HISTORY_SIZE)

        log.info(f"State manager initialized (history size: {config.CONTEXT_HISTORY_SIZE})")

    def update(self, command: str, tool: str = "", result: str = "",
               app: str = "") -> None:
        """Update state after a command is processed."""
        self.last_command = command
        self.last_tool = tool or self.last_tool
        self.last_result = result or self.last_result
        self.last_app = app or self.last_app

        self._history.append({
            "command": command,
            "tool": tool,
            "result": result,
        })

        log.debug(f"State updated: cmd='{command}', tool='{tool}'")

    def get_history(self) -> list[dict]:
        """Return the last N commands as a list."""
        return list(self._history)

    def get_context_summary(self) -> str:
        """Return a one-line summary of recent commands (for AI prompts)."""
        if not self._history:
            return "No previous commands."
        recent = [h["command"] for h in self._history]
        return "Recent commands: " + " → ".join(recent)

    def clear(self) -> None:
        """Reset all state."""
        self.last_command = ""
        self.last_tool = ""
        self.last_result = ""
        self.last_app = ""
        self.context = {}
        self._history.clear()
        log.info("State cleared.")


# ── Global instance ─────────────────────────────────────────────
state = StateManager()
