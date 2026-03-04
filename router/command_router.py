"""
Wednesday - Command Router
Routes user commands to the appropriate skill or AI brain.
"""

import re


# Each entry: (list of keyword patterns, skill_name, action)
ROUTE_TABLE = [
    # System control
    (["shut down", "shutdown", "turn off computer", "power off"],
     "system_control", "shutdown"),
    (["restart", "reboot", "restart computer"],
     "system_control", "restart"),
    (["sleep computer", "put computer to sleep", "hibernate"],
     "system_control", "sleep"),
    (["lock computer", "lock screen", "lock the pc"],
     "system_control", "lock"),
    (["increase volume", "volume up", "turn up volume"],
     "system_control", "volume_up"),
    (["decrease volume", "volume down", "turn down volume"],
     "system_control", "volume_down"),
    (["mute", "unmute", "toggle mute"],
     "system_control", "mute"),

    # App control
    (["open (.+)", "launch (.+)", "start (.+)"],
     "app_control", "open_app"),

    # Web actions
    (["search (?:for )?(.+) on google", "google (.+)", "search google for (.+)"],
     "web_actions", "google_search"),
    (["open youtube", "play youtube", "go to youtube"],
     "web_actions", "open_youtube"),
    (["search (?:for )?(.+) on youtube", "youtube (.+)"],
     "web_actions", "youtube_search"),
    (["open website (.+)", "go to (.+\.\w+)", "open (.+\.com)", "open (.+\.org)", "open (.+\.net)"],
     "web_actions", "open_website"),

    # File control
    (["create (?:a )?file (?:called |named )?(.+)", "make (?:a )?file (.+)"],
     "file_control", "create_file"),
    (["open file (.+)"],
     "file_control", "open_file"),
    (["delete file (.+)", "remove file (.+)"],
     "file_control", "delete_file"),

    # Clipboard
    (["read clipboard", "what's in (?:my )?clipboard", "paste clipboard", "clipboard content"],
     "clipboard", "read_clipboard"),
    (["summarize clipboard", "summarise clipboard"],
     "clipboard", "summarize_clipboard"),

    # Communication
    (["send (?:an )?email"],
     "communication", "send_email"),

    # Reminders
    (["remind me to (.+)", "set (?:a )?reminder (.+)", "remember to (.+)"],
     "reminders", "set_reminder"),
    (["show reminders", "list reminders", "my reminders", "what are my reminders"],
     "reminders", "list_reminders"),
]


class CommandRouter:
    def __init__(self):
        pass

    def route(self, text: str) -> dict:
        """
        Determine how to handle user input.

        Returns dict with:
            - type: "skill" or "ai"
            - skill: skill module name (if type is "skill")
            - action: action name (if type is "skill")
            - params: extracted parameters
            - original: original text
        """
        if not text:
            return {"type": "ai", "original": text, "params": {}}

        lower = text.lower().strip()

        for patterns, skill_name, action in ROUTE_TABLE:
            for pattern in patterns:
                match = re.search(pattern, lower)
                if match:
                    params = {}
                    if match.groups():
                        params["query"] = match.group(1).strip()
                    return {
                        "type": "skill",
                        "skill": skill_name,
                        "action": action,
                        "params": params,
                        "original": text,
                    }

        # No skill matched; route to AI brain
        return {"type": "ai", "original": text, "params": {}}
