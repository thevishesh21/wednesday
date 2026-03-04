"""
Wednesday - Text-to-Speech Speaker
Uses pyttsx3 for offline TTS on Windows.
"""

import threading
import pyttsx3
import config


class Speaker:
    def __init__(self):
        self._lock = threading.Lock()
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", config.TTS_RATE)
            self._engine.setProperty("volume", config.TTS_VOLUME)
            # Try to select a female voice if available
            voices = self._engine.getProperty("voices")
            for voice in voices:
                if "zira" in voice.name.lower() or "female" in voice.name.lower():
                    self._engine.setProperty("voice", voice.id)
                    break
        except Exception as e:
            print(f"[Speaker] TTS engine init failed: {e}")
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
                print(f"[Speaker] TTS error: {e}")

    def is_available(self) -> bool:
        return self._engine is not None
