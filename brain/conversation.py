"""
Wednesday AI Assistant — Proactive Conversation System
Speaks idle-time tips, fun facts, or check-ins when user hasn't
interacted for a while. Runs in a background thread.
"""

import time
import random
from datetime import datetime
from utils.logger import get_logger
from voice.speaker import speak
import config

log = get_logger("conversation")

# ── Last interaction timestamp ──────────────────────────────────
_last_interaction_time = time.time()

# ── Proactive messages pool ─────────────────────────────────────
_IDLE_MESSAGES = [
    "Boss, sab theek hai? Kuch kaam hai toh bolo!",
    "Main yahan hoon boss, koi kaam ho toh bataiye.",
    "Bohot time ho gaya, boss. Kuch help chahiye?",
    "Boss, break le lo! Thoda pani pi lo.",
    "Tip of the day: Ctrl+Shift+Esc se Task Manager khulta hai!",
    "Boss, aaj ka kya plan hai? Kuch schedule karna hai?",
    "Fun fact: Python ka naam Monty Python se aaya hai, snake se nahi!",
    "Boss, kuch naya seekhna hai? YouTube pe tutorial dhoondun?",
]

_TIME_BASED_MESSAGES = {
    "morning": [
        "Good morning boss! Aaj ka din shandar hone wala hai!",
        "Subah ho gayi, boss! Chai pi li? Kaam shuru karein?",
    ],
    "afternoon": [
        "Lunch time, boss! Khana kha liya?",
        "Dopahar ho gayi, boss. Break le lo!",
    ],
    "evening": [
        "Shaam ho gayi, boss. Aaj ka kaam khatam kar ke rest karo!",
        "Evening, boss! Kuch aur kaam baaki hai?",
    ],
    "night": [
        "Boss, raat ho gayi. Thoda rest karo!",
        "Late night coding, boss? Don't forget to rest!",
    ],
}


def update_interaction() -> None:
    """Call this whenever the user interacts (refreshes the idle timer)."""
    global _last_interaction_time
    _last_interaction_time = time.time()


def _get_time_period() -> str:
    """Get current time period."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    return "night"


def _pick_message() -> str:
    """Pick a proactive message based on time of day."""
    period = _get_time_period()
    time_messages = _TIME_BASED_MESSAGES.get(period, [])
    all_messages = _IDLE_MESSAGES + time_messages
    return random.choice(all_messages)


# ═════════════════════════════════════════════════════════════════
#  Background Loop (runs via ThreadManager)
# ═════════════════════════════════════════════════════════════════

def conversation_loop(stop_event) -> None:
    """
    Background loop that occasionally speaks if the user is idle.
    Called by ThreadManager with a stop_event.
    """
    log.info("Proactive conversation loop started.")
    idle_threshold = config.IDLE_TIMEOUT_MINUTES * 60  # Convert to seconds

    while not stop_event.is_set():
        try:
            elapsed = time.time() - _last_interaction_time

            if elapsed >= idle_threshold and config.PROACTIVE_ENABLED:
                message = _pick_message()
                speak(message)
                log.info(f"Proactive message: {message}")
                # Reset timer so we don't spam
                update_interaction()

        except Exception as e:
            log.error(f"Conversation loop error: {e}")

        # Check every 60 seconds
        stop_event.wait(60)

    log.info("Proactive conversation loop stopped.")
