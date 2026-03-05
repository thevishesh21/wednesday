"""
Wednesday - Command Router
Routes user commands using AI intent detection.
Maps broad intents from IntentDetector to specific skill actions.
"""

import logging

from openai import OpenAI
import config
from brain.intent_detector import IntentDetector

logger = logging.getLogger("Wednesday")

# Normalize AI target text to internal system_control action names
SYSTEM_ACTION_MAP = {
    "shutdown": "shutdown",
    "shut down": "shutdown",
    "power off": "shutdown",
    "turn off": "shutdown",
    "restart": "restart",
    "reboot": "restart",
    "sleep": "sleep",
    "hibernate": "sleep",
    "lock": "lock",
    "lock screen": "lock",
    "lock computer": "lock",
    "volume up": "volume_up",
    "volume_up": "volume_up",
    "increase volume": "volume_up",
    "louder": "volume_up",
    "volume down": "volume_down",
    "volume_down": "volume_down",
    "decrease volume": "volume_down",
    "quieter": "volume_down",
    "mute": "mute",
    "unmute": "mute",
    "toggle mute": "mute",
}

# Map file action verbs to internal action names
FILE_ACTION_MAP = {
    "create": "create_file",
    "make": "create_file",
    "new": "create_file",
    "open": "open_file",
    "delete": "delete_file",
    "remove": "delete_file",
}


class CommandRouter:
    def __init__(self):
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.intent_detector = IntentDetector(client)

    def route(self, text: str) -> dict:
        """
        Determine how to handle user input via AI intent detection.

        Returns dict with:
            - type: "skill" or "ai"
            - skill: skill module name (if type is "skill")
            - action: action name (if type is "skill")
            - params: extracted parameters
            - original: original text
        """
        if not text:
            return {"type": "ai", "original": text, "params": {}}

        intent_data = self.intent_detector.detect(text)
        intent = intent_data.get("intent", "chat")
        target = intent_data.get("target") or ""

        return self._build_route(intent, target, text)

    # ------------------------------------------------------------------
    # Intent-to-route mapping
    # ------------------------------------------------------------------

    def _build_route(self, intent, target, text):
        """Convert a broad intent + target into a route dict."""

        if intent == "open_app":
            return self._skill("app_control", "open_app", target, text)

        if intent == "open_website":
            return self._route_website(target, text)

        if intent == "search_web":
            return self._route_search(target, text)

        if intent == "system_command":
            action = SYSTEM_ACTION_MAP.get(target.lower().strip(), target.lower().strip())
            return self._skill("system_control", action, "", text)

        if intent == "file_action":
            return self._route_file(target, text)

        if intent == "clipboard_action":
            if target and "summar" in target.lower():
                return self._skill("clipboard", "summarize_clipboard", "", text)
            return self._skill("clipboard", "read_clipboard", "", text)

        if intent == "communication":
            return self._skill("communication", "send_email", target, text)

        if intent == "reminder":
            return self._route_reminder(target, text)

        # chat or unknown intent → AI brain
        return {"type": "ai", "original": text, "params": {}}

    def _route_website(self, target, text):
        """Route open_website intent with YouTube special handling."""
        lower = target.lower().strip()
        if lower == "youtube":
            return self._skill("web_actions", "open_youtube", "", text)
        if "youtube" in lower:
            query = lower.replace("youtube", "").strip()
            if query:
                return self._skill("web_actions", "youtube_search", query, text)
            return self._skill("web_actions", "open_youtube", "", text)
        return self._skill("web_actions", "open_website", target, text)

    def _route_search(self, target, text):
        """Route search_web intent; detect YouTube searches."""
        lower_text = text.lower()
        if "youtube" in lower_text:
            query = target
            # Strip "on youtube" from the query if present
            for suffix in (" on youtube", " youtube"):
                if query.lower().endswith(suffix):
                    query = query[:-len(suffix)].strip()
            return self._skill("web_actions", "youtube_search", query, text)
        return self._skill("web_actions", "google_search", target, text)

    def _route_file(self, target, text):
        """Route file_action by parsing verb + filename from target."""
        parts = target.strip().split(None, 1)
        if len(parts) == 2:
            verb, filename = parts
            action = FILE_ACTION_MAP.get(verb.lower(), "open_file")
            return self._skill("file_control", action, filename, text)
        # Single word — treat as filename to open
        return self._skill("file_control", "open_file", target, text)

    def _route_reminder(self, target, text):
        """Route reminder intent: list vs set."""
        lower = (target or "").lower().strip()
        if lower in ("list", "show", "all", "my reminders"):
            return self._skill("reminders", "list_reminders", "", text)
        return self._skill("reminders", "set_reminder", target, text)

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _skill(self, skill, action, query, text):
        """Build a skill route dict."""
        params = {}
        if query:
            params["query"] = query
        return {
            "type": "skill",
            "skill": skill,
            "action": action,
            "params": params,
            "original": text,
        }
