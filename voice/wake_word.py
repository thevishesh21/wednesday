"""
Wednesday AI Assistant — Wake Word
Detects the wake word to activate the assistant.
Supports both always-on Porcupine streaming (offline) and legacy string matching.
"""

import threading
import time
from typing import Optional
from utils.logger import get_logger
from core.event_bus import publish_sync
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

# ═════════════════════════════════════════════════════════════════
#  Always-On Streaming Listener (Porcupine)
# ═════════════════════════════════════════════════════════════════

class PorcupineListener(threading.Thread):
    """
    Background thread that constantly listens for the wake word using pvporcupine.
    Offline, fast, and highly accurate.
    """
    def __init__(self, access_key: str = "", keyword: str = "hey wednesday"):
        super().__init__(daemon=True, name="wednesday-porcupine")
        self.access_key = access_key
        self.keyword_path = None # In a real implementation, path to custom .ppn file
        self.keyword = keyword
        self._stop_event = threading.Event()
        self._porcupine = None
        self._audio_stream = None
        self._pa = None

    def run(self):
        if not self.access_key:
            log.warning("Porcupine access key missing. Falling back to string-matching wake word only.")
            return

        try:
            import pvporcupine
            import pyaudio

            # For standard keywords, you can pass the string if it's supported,
            # or a path to a custom trained model (.ppn file).
            # For this stub, we assume we either have a path or use a built-in.
            self._porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=["computer"] if not self.keyword_path else None,
                keyword_paths=[self.keyword_path] if self.keyword_path else None
            )

            self._pa = pyaudio.PyAudio()
            self._audio_stream = self._pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self._porcupine.frame_length
            )

            log.info(f"Porcupine background listener active (Wake word: {self.keyword})")

            while not self._stop_event.is_set():
                pcm = self._audio_stream.read(self._porcupine.frame_length, exception_on_overflow=False)
                import struct
                pcm_unpacked = struct.unpack_from("h" * self._porcupine.frame_length, pcm)

                result = self._porcupine.process(pcm_unpacked)
                if result >= 0:
                    log.info("Wake word detected by Porcupine!")
                    # Signal the rest of the system
                    publish_sync("voice.wake_detected", {"source": "porcupine"})

        except ImportError:
            log.warning("pvporcupine or pyaudio not installed. Falling back to string-matching.")
        except Exception as e:
            log.error(f"Porcupine listener failed: {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        if self._audio_stream is not None:
            self._audio_stream.close()
        if self._pa is not None:
            self._pa.terminate()
        if self._porcupine is not None:
            self._porcupine.delete()

    def stop(self):
        self._stop_event.set()
