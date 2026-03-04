"""
Wednesday - Reminders Skill
Set and list reminders stored in a JSON file.
"""

import json
import os
from datetime import datetime
import config


REMINDERS_FILE = os.path.join(config.MEMORY_DIR, "reminders.json")


def _load_reminders() -> list:
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_reminders(reminders: list):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
    except IOError:
        pass


def set_reminder(text: str) -> str:
    """Store a reminder."""
    if not text:
        return "What should I remind you about?"
    reminders = _load_reminders()
    reminders.append({
        "text": text,
        "created": datetime.now().isoformat(),
        "done": False,
    })
    _save_reminders(reminders)
    return f"Got it. I will remember: {text}"


def list_reminders() -> str:
    """List all active reminders."""
    reminders = _load_reminders()
    active = [r for r in reminders if not r.get("done", False)]
    if not active:
        return "You have no reminders."
    lines = [f"{i+1}. {r['text']}" for i, r in enumerate(active)]
    return "Your reminders: " + ". ".join(lines)
