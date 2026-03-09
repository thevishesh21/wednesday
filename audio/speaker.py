"""
Wednesday - Text-to-Speech Speaker
Uses pyttsx3 for offline TTS on Windows.
Selects the most natural-sounding voice available.
"""

import threading
import logging
import pyttsx3
import config

logger = logging.getLogger("Wednesday")

# Voice preference order — more natural-sounding voices first
_PREFERRED_VOICES = [
    "zira",       # Microsoft Zira (female, clear)
    "david",      # Microsoft David (male, clear)
    "hazel",      # Microsoft Hazel (UK female)
    "mark",       # Microsoft Mark
    "female",     # Generic fallback
]


class Speaker:
    def __init__(self):
        self._lock = threading.Lock()
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        try:
            self._engine = pyttsx3.init()
            # Slightly slower rate for more natural feel
            self._engine.setProperty("rate", config.TTS_RATE)
            self._engine.setProperty("volume", config.TTS_VOLUME)

            # Pick the best available voice
            voices = self._engine.getProperty("voices")
            selected = False
            for pref in _PREFERRED_VOICES:
                for voice in voices:
                    if pref in voice.name.lower():
                        self._engine.setProperty("voice", voice.id)
                        logger.info("[Speaker] Using voice: %s", voice.name)
                        selected = True
                        break
                if selected:
                    break

            if not selected and voices:
                logger.info("[Speaker] Using default voice: %s", voices[0].name)

        except Exception as e:
            logger.error("[Speaker] TTS engine init failed: %s", e)
            self._engine = None

    def speak(self, text: str):
        """Speak the given text. Thread-safe."""
        if not self._engine or not text:
            return

        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except RuntimeError:
                # Engine may be in a bad state; reinitialize
                self._init_engine()
                if self._engine:
                    try:
                        self._engine.say(text)
                        self._engine.runAndWait()
                    except Exception:
                        pass
            except Exception as e:
                logger.error("[Speaker] TTS error: %s", e)

    def is_available(self) -> bool:
        return self._engine is not None
