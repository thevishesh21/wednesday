"""
Wednesday AI Assistant — Text-to-Speech (Speaker)
Converts text to spoken audio using pyttsx3.
If TTS fails entirely, falls back to printing text to console.
"""

import random
import pyttsx3
from utils.logger import get_logger
import config

log = get_logger("speaker")

# ── Initialize the TTS engine (with error handling) ──────────────
_engine = None
_tts_available = False

try:
    _engine = pyttsx3.init()
    _engine.setProperty("rate", config.VOICE_RATE)

    # Try to use a female voice (index 1) if available
    _voices = _engine.getProperty("voices")
    if len(_voices) > config.VOICE_INDEX:
        _engine.setProperty("voice", _voices[config.VOICE_INDEX].id)
        log.info(f"Voice set to: {_voices[config.VOICE_INDEX].name}")
    else:
        log.warning("Requested voice index not available, using default.")

    _tts_available = True
    log.info("TTS engine initialized successfully.")
except Exception as e:
    log.error(f"TTS engine failed to initialize: {e}")
    log.warning("Speaker will fall back to console-only output.")


def speak(text: str) -> None:
    """
    Speak the given text out loud.
    If TTS is broken, prints to console so the user still gets feedback.
    """
    global _engine, _tts_available

    log.info(f"Speaking: {text}")

    if _tts_available and _engine:
        try:
            _engine.say(text)
            _engine.runAndWait()
        except RuntimeError as e:
            # pyttsx3 "run loop already started" — reinitialize engine
            log.warning(f"TTS RuntimeError (reinitializing): {e}")
            try:
                _engine = pyttsx3.init()
                _engine.setProperty("rate", config.VOICE_RATE)
                _engine.say(text)
                _engine.runAndWait()
            except Exception as e2:
                log.error(f"TTS reinit also failed: {e2}")
                _fallback_print(text)
        except Exception as e:
            log.error(f"TTS speak error: {e}")
            _fallback_print(text)
    else:
        _fallback_print(text)


def _fallback_print(text: str) -> None:
    """Print to console when TTS is unavailable."""
    print(f"  🔇 [Wednesday]: {text}")


def greet() -> None:
    """
    Speak a random wake-word greeting from config.
    """
    greeting = random.choice(config.WAKE_RESPONSES)
    speak(greeting)


def is_tts_available() -> bool:
    """Returns True if the TTS engine is working."""
    return _tts_available
