"""
Wednesday - Confirmation System
Requires confirmation for dangerous actions.
"""

# Actions that require user confirmation before execution
DANGEROUS_ACTIONS = {
    "shutdown",
    "restart",
    "sleep",
    "delete_file",
    "send_email",
}


class ConfirmationManager:
    def __init__(self):
        self._pending = None

    def needs_confirmation(self, action: str) -> bool:
        """Check if an action requires confirmation."""
        return action in DANGEROUS_ACTIONS

    def request_confirmation(self, action: str, description: str) -> str:
        """Store pending action and return confirmation prompt."""
        self._pending = {"action": action, "description": description}
        return f"Are you sure you want to {description}? Say yes to confirm or no to cancel."

    def confirm(self, user_response: str) -> dict | None:
        """
        Check if user confirmed. Returns the pending action dict if confirmed,
        None if cancelled or nothing pending.
        """
        if not self._pending:
            return None
        lower = user_response.lower().strip()
        if lower in ("yes", "yeah", "yep", "sure", "confirm", "do it", "go ahead"):
            action = self._pending
            self._pending = None
            return action
        else:
            self._pending = None
            return None

    def has_pending(self) -> bool:
        return self._pending is not None

    def cancel(self):
        self._pending = None
