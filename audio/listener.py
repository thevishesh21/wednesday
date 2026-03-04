"""
Wednesday - Speech-to-Text Listener
Uses SpeechRecognition with Google Web Speech API.
"""

import speech_recognition as sr
import config


class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = config.ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = None
        self._init_microphone()

    def _init_microphone(self):
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise on startup
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except (OSError, AttributeError) as e:
            print(f"[Listener] Microphone not available: {e}")
            self.microphone = None

    def listen(self) -> str | None:
        """Listen for speech and return recognized text, or None on failure."""
        if self.microphone is None:
            return None

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=config.LISTEN_TIMEOUT,
                    phrase_time_limit=config.PHRASE_TIME_LIMIT,
                )
            text = self.recognizer.recognize_google(audio)
            return text.strip()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[Listener] Speech recognition service error: {e}")
            return None
        except Exception as e:
            print(f"[Listener] Unexpected error: {e}")
            return None

    def is_available(self) -> bool:
        return self.microphone is not None
