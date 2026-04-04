"""
Wednesday AI Assistant — Speech-to-Text (Listener)
Captures audio from the microphone and converts it to text
using Google's free Speech Recognition API.
Falls back to keyboard text input if microphone is unavailable.
"""

import speech_recognition as sr
from utils.logger import get_logger
import config

log = get_logger("listener")

# ── Initialize the recognizer ───────────────────────────────────
_recognizer = sr.Recognizer()
_recognizer.dynamic_energy_threshold = True

# ── Check microphone availability at startup ────────────────────
_mic_available = False
try:
    mic_list = sr.Microphone.list_microphone_names()
    if mic_list:
        _mic_available = True
        log.info(f"Microphone found: {mic_list[0]} (+ {len(mic_list)-1} more)")
    else:
        log.warning("No microphones detected — will use text input mode.")
except (OSError, AttributeError) as e:
    log.warning(f"Microphone detection failed: {e} — will use text input mode.")
except Exception as e:
    log.warning(f"Unexpected error checking microphones: {e}")


def check_microphone() -> dict:
    """
    Diagnostic: returns microphone status info.
    Useful for startup health checks.
    """
    result = {"available": _mic_available, "devices": []}
    try:
        result["devices"] = sr.Microphone.list_microphone_names()
    except Exception as e:
        result["error"] = str(e)
    return result


def is_mic_available() -> bool:
    """Returns True if at least one microphone was detected."""
    return _mic_available


# ═════════════════════════════════════════════════════════════════
#  Text Input Fallback
# ═════════════════════════════════════════════════════════════════

def text_input(prompt: str = None) -> str | None:
    """
    Fallback: read command from keyboard.
    Returns the typed text (lowercase stripped), or None on empty/EOF.
    """
    prompt = prompt or config.TEXT_INPUT_PROMPT
    try:
        text = input(prompt).strip().lower()
        if text:
            log.info(f"Text input: {text}")
            return text
        return None
    except (EOFError, KeyboardInterrupt):
        return None


# ═════════════════════════════════════════════════════════════════
#  Voice Listener
# ═════════════════════════════════════════════════════════════════

def listen(timeout: int = None, phrase_limit: int = None) -> str | None:
    """
    Listen to the microphone and return recognized text.
    Falls back to text input if mic is unavailable and INPUT_MODE is 'auto'.

    Args:
        timeout:      Seconds to wait for speech to start (default from config).
        phrase_limit: Max seconds a phrase can last (default from config).

    Returns:
        Recognized text as a lowercase string, or None if nothing was understood.
    """
    # ── Text-only mode ─────────────────────────────────────────
    if config.INPUT_MODE == "text":
        return text_input()

    # ── Guard: no microphone → fallback ────────────────────────
    if not _mic_available:
        if config.INPUT_MODE == "auto":
            return text_input()
        log.error("Cannot listen — no microphone available.")
        return None

    timeout = timeout or config.LISTEN_TIMEOUT
    phrase_limit = phrase_limit or config.PHRASE_TIME_LIMIT

    try:
        with sr.Microphone() as source:
            # Show listening indicator
            print("  [🎤 Listening...]")
            log.info("Listening...")
            _recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = _recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_limit
            )

        log.info("Recognizing speech...")
        text = _recognizer.recognize_google(audio, language=config.LISTEN_LANGUAGE)
        text = text.lower().strip()
        log.info(f"Heard: {text}")
        return text

    except sr.WaitTimeoutError:
        log.debug("Listen timeout — no speech detected.")
        return None
    except sr.UnknownValueError:
        log.debug("Could not understand audio.")
        return None
    except sr.RequestError as e:
        log.error(f"Google Speech API error: {e}")
        return None
    except OSError as e:
        log.error(f"Microphone hardware error: {e}")
        # Fall back to text input on hardware error if in auto mode
        if config.INPUT_MODE == "auto":
            log.info("Switching to text input for this turn.")
            return text_input()
        return None
    except Exception as e:
        log.error(f"Unexpected listener error: {e}")
        return None

