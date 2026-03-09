"""
Wednesday - Context Memory
Tracks session context so the assistant understands conversational flow.
Stores last app opened, last website, last command, etc.
"""

import logging

logger = logging.getLogger("Wednesday")


class ContextMemory:
    """In-session context that helps the assistant understand follow-up commands."""

    def __init__(self):
        self._context = {
            "last_app": None,
            "last_website": None,
            "last_command": None,
            "last_response": None,
            "last_search_query": None,
            "last_file": None,
            "last_contact": None,
            "dictation_active": False,
            "browser_open": False,
        }

    def update(self, key: str, value):
        """Set a context value."""
        if key in self._context:
            self._context[key] = value
            logger.debug("[ContextMemory] %s = %s", key, value)

    def get(self, key: str, default=None):
        """Get a context value."""
        return self._context.get(key, default)

    def record_command(self, command: str, response: str):
        """Record the latest exchange."""
        self._context["last_command"] = command
        self._context["last_response"] = response

    def record_app(self, app_name: str):
        """Record that an app was opened."""
        self._context["last_app"] = app_name
        if app_name and app_name.lower() in ("chrome", "firefox", "edge", "msedge",
                                               "google chrome", "microsoft edge", "brave"):
            self._context["browser_open"] = True

    def record_website(self, url_or_name: str):
        """Record that a website was opened."""
        self._context["last_website"] = url_or_name
        self._context["browser_open"] = True

    def record_search(self, query: str):
        self._context["last_search_query"] = query

    def record_file(self, filename: str):
        self._context["last_file"] = filename

    def record_contact(self, name: str):
        self._context["last_contact"] = name

    @property
    def is_browser_open(self) -> bool:
        return self._context.get("browser_open", False)

    @property
    def is_dictating(self) -> bool:
        return self._context.get("dictation_active", False)

    @is_dictating.setter
    def is_dictating(self, value: bool):
        self._context["dictation_active"] = value

    def get_summary(self) -> str:
        """Return a short text summary of current context for AI prompts."""
        parts = []
        if self._context["last_app"]:
            parts.append(f"Last app opened: {self._context['last_app']}")
        if self._context["last_website"]:
            parts.append(f"Last website: {self._context['last_website']}")
        if self._context["browser_open"]:
            parts.append("Browser is currently open")
        if self._context["last_search_query"]:
            parts.append(f"Last search: {self._context['last_search_query']}")
        return "; ".join(parts) if parts else ""

    def reset(self):
        """Reset all context."""
        for key in self._context:
            if isinstance(self._context[key], bool):
                self._context[key] = False
            else:
                self._context[key] = None
