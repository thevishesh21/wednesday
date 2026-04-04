"""
Wednesday AI Assistant — Wake Word Detector
Checks if the user's speech contains the wake word.
"""

from utils.logger import get_logger
import config

log = get_logger("wake_word")


def is_wake_word(text: str | None) -> bool:
    """
    Returns True if the text starts with (or closely contains) the wake word.

    Handles common mis-hearings like:
      - "hey wednesday"
      - "hey when's day"
      - "a wednesday"
    """
    if not text:
        return False

    text = text.lower().strip()

    # Direct match
    if text.startswith(config.WAKE_WORD):
        log.info("Wake word detected!")
        return True

    # Fuzzy variants people commonly say
    variants = [
        "hey wednesday",
        "he wednesday",
        "a wednesday",
        "hay wednesday",
        "hey when's day",
        "hey wensday",
    ]
    for variant in variants:
        if text.startswith(variant):
            log.info(f"Wake word detected (variant: '{variant}')!")
            return True

    return False


def strip_wake_word(text: str) -> str:
    """
    Remove the wake word prefix from the text and return the remaining command.
    E.g. "hey wednesday open notepad" → "open notepad"
    """
    text = text.lower().strip()
    for prefix in [config.WAKE_WORD, "hey wednesday", "he wednesday",
                   "a wednesday", "hay wednesday", "hey when's day", "hey wensday"]:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return text
