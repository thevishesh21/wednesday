"""
Wednesday AI Assistant — Reminder System
Background loop that checks reminders and speaks them at the right time.
Supports follow-up ("Kya aapne complete kiya?").
"""

import json
import os
import time
import re
from datetime import datetime, timedelta
from utils.logger import get_logger
from voice.speaker import speak
import config

log = get_logger("reminder")

_reminders: list = []


def _load() -> None:
    """Load reminders from JSON file."""
    global _reminders
    try:
        if os.path.exists(config.REMINDERS_FILE):
            with open(config.REMINDERS_FILE, "r", encoding="utf-8") as f:
                _reminders = json.load(f)
            log.info(f"Loaded {len(_reminders)} reminders.")
        else:
            _reminders = []
            _save()
    except Exception as e:
        log.error(f"Reminder load failed: {e}")
        _reminders = []


def _save() -> None:
    """Save reminders to JSON file."""
    try:
        os.makedirs(os.path.dirname(config.REMINDERS_FILE) or ".", exist_ok=True)
        with open(config.REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(_reminders, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error(f"Reminder save failed: {e}")


def set_reminder(text: str, minutes: int = 0, at_time: str = "") -> str:
    """
    Set a new reminder.

    Args:
        text: What to remind about
        minutes: Minutes from now (e.g. 5)
        at_time: Specific time string (e.g. "3:00 PM")
    """
    if minutes > 0:
        trigger_time = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")
    elif at_time:
        try:
            # Parse time like "3:00 PM" or "15:00"
            today = datetime.now().strftime("%Y-%m-%d")
            for fmt in ["%I:%M %p", "%I %p", "%H:%M"]:
                try:
                    t = datetime.strptime(f"{today} {at_time}", f"%Y-%m-%d {fmt}")
                    trigger_time = t.strftime("%Y-%m-%d %H:%M")
                    break
                except ValueError:
                    continue
            else:
                return f"Sorry boss, time format samajh nahi aaya: {at_time}"
        except Exception:
            return f"Time parse error: {at_time}"
    else:
        # Default: 5 minutes from now
        trigger_time = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")

    reminder = {
        "text": text,
        "time": trigger_time,
        "status": "pending",
        "follow_ups": 0,
    }
    _reminders.append(reminder)
    _save()
    log.info(f"Reminder set: '{text}' at {trigger_time}")
    return f"Reminder set, boss! '{text}' — {trigger_time} par yaad dilaaungi."


def list_reminders() -> str:
    """List all pending reminders."""
    pending = [r for r in _reminders if r["status"] == "pending"]
    if not pending:
        return "Koi pending reminder nahi hai, boss."
    lines = [f"• {r['text']} (at {r['time']})" for r in pending[:5]]
    return "Pending reminders:\n" + "\n".join(lines)


def clear_reminders() -> str:
    """Clear all reminders."""
    _reminders.clear()
    _save()
    return "Sab reminders clear kar diye, boss!"


def parse_reminder_command(command: str) -> str:
    """
    Parse natural language reminder commands.
    E.g. "remind me to drink water in 5 minutes"
         "remind me to call mom at 3 PM"
    """
    command = command.lower().strip()

    # Match "in X minutes"
    match = re.search(r"remind\s+(?:me\s+)?(?:to\s+)?(.+?)\s+in\s+(\d+)\s+min", command)
    if match:
        return set_reminder(match.group(1), minutes=int(match.group(2)))

    # Match "at TIME"
    match = re.search(r"remind\s+(?:me\s+)?(?:to\s+)?(.+?)\s+at\s+(.+)", command)
    if match:
        return set_reminder(match.group(1), at_time=match.group(2))

    # Just "remind me to X" → default 5 min
    match = re.search(r"remind\s+(?:me\s+)?(?:to\s+)?(.+)", command)
    if match:
        return set_reminder(match.group(1), minutes=5)

    return "Boss, reminder ka format samajh nahi aaya. Try: 'remind me to X in 5 minutes'"


# ═════════════════════════════════════════════════════════════════
#  Background Loop (runs in a thread via ThreadManager)
# ═════════════════════════════════════════════════════════════════

def reminder_loop(stop_event) -> None:
    """
    Background loop that checks reminders every REMINDER_CHECK_INTERVAL seconds.
    Called by ThreadManager with a stop_event.
    """
    log.info("Reminder loop started.")
    while not stop_event.is_set():
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            for r in _reminders:
                if r["status"] == "pending" and r["time"] <= now:
                    # Time to remind!
                    speak(f"Boss, reminder: {r['text']}")
                    speak("Kya aapne complete kiya?")
                    r["status"] = "notified"
                    r["follow_ups"] += 1
                    _save()
                    log.info(f"Reminder triggered: {r['text']}")

                elif r["status"] == "notified" and r["follow_ups"] < 3:
                    # Follow up (max 3 times)
                    if r["follow_ups"] > 0:
                        speak(f"Boss, phir se yaad dila rahi hoon: {r['text']}")
                        r["follow_ups"] += 1
                        if r["follow_ups"] >= 3:
                            r["status"] = "done"
                        _save()

        except Exception as e:
            log.error(f"Reminder loop error: {e}")

        # Wait for the interval or until stop is signaled
        stop_event.wait(config.REMINDER_CHECK_INTERVAL)

    log.info("Reminder loop stopped.")


# ── Load on import ──────────────────────────────────────────────
_load()
