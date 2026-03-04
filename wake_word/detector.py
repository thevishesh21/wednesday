"""
Wednesday - Wake Word Detector
Listens in the background for the wake phrase.
"""

import config


class WakeWordDetector:
    def __init__(self):
        self.wake_phrases = config.WAKE_PHRASES
        self.sleep_phrases = config.SLEEP_PHRASES

    def is_wake_word(self, text: str) -> bool:
        """Check if the text contains a wake word."""
        if not text:
            return False
        lower = text.lower().strip()
        return any(phrase in lower for phrase in self.wake_phrases)

    def is_sleep_command(self, text: str) -> bool:
        """Check if the text contains a sleep command."""
        if not text:
            return False
        lower = text.lower().strip()
        return any(phrase in lower for phrase in self.sleep_phrases)

    def strip_wake_word(self, text: str) -> str:
        """Remove the wake word from the beginning of text."""
        if not text:
            return ""
        lower = text.lower().strip()
        for phrase in self.wake_phrases:
            if lower.startswith(phrase):
                return text[len(phrase):].strip()
        return text
