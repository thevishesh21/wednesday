"""
voice/wake_word.py
-------------------
Wake word detection using Picovoice Porcupine.

Porcupine runs a tiny neural network locally in real-time.
It listens continuously for "Hey Wednesday" with <1% CPU usage.

Setup:
  1. Get free key: https://console.picovoice.ai/ → AccessKey
  2. Add to .env: PORCUPINE_ACCESS_KEY=your_key_here
  3. Set in config.yaml: voice.enable_wake_word: true

Built-in wake words (free):
  alexa, computer, hey google, hey siri, jarvis, ok google,
  picovoice, porcupine, terminator

Custom wake word ("Hey Wednesday"):
  → Go to Picovoice Console → Wake Word → Create → type "Hey Wednesday"
  → Download the .ppn file → place in assets/wake_word.ppn
  → The code auto-detects it

Without a custom .ppn, this module falls back to "computer" as the trigger word.
You say "computer" and it wakes up the same way.
"""

import struct
import threading
from pathlib import Path
from typing import Callable, Optional
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)

ASSETS_DIR = Path(__file__).parent.parent / "assets"


class WakeWordDetector:
    """
    Listens continuously on the microphone for the wake word.
    When detected, calls the provided callback function.

    Usage:
        def on_wake():
            print("Wake word detected!")

        detector = WakeWordDetector(on_wake_callback=on_wake)
        detector.start()   # Non-blocking, runs in background thread
        # ... later ...
        detector.stop()
    """

    def __init__(self, on_wake_callback: Callable[[], None]):
        self._callback = on_wake_callback
        self._porcupine = None
        self._audio_stream = None
        self._pa = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._initialized = False
        self._init_porcupine()

    def _init_porcupine(self) -> None:
        """Initialize Porcupine with the best available wake word."""
        access_key = settings.porcupine_access_key
        if not access_key:
            logger.warning(
                "No PORCUPINE_ACCESS_KEY set. Wake word detection disabled.\n"
                "  Get a free key at: https://console.picovoice.ai/"
            )
            return

        try:
            import pvporcupine

            # Check for custom "Hey Wednesday" .ppn file
            custom_ppn = ASSETS_DIR / "hey_wednesday.ppn"
            if custom_ppn.exists():
                self._porcupine = pvporcupine.create(
                    access_key=access_key,
                    keyword_paths=[str(custom_ppn)],
                    sensitivities=[settings.voice.wake_word_sensitivity],
                )
                logger.info(f"Porcupine: using custom wake word 'Hey Wednesday'")
            else:
                # Fallback to built-in "computer" keyword
                self._porcupine = pvporcupine.create(
                    access_key=access_key,
                    keywords=["computer"],
                    sensitivities=[settings.voice.wake_word_sensitivity],
                )
                logger.info(
                    "Porcupine: using built-in keyword 'computer' (say 'computer' to wake).\n"
                    "  For 'Hey Wednesday': add hey_wednesday.ppn to assets/"
                )

            self._initialized = True
            logger.info(
                f"Porcupine initialized | frame_length={self._porcupine.frame_length} "
                f"samples | sample_rate={self._porcupine.sample_rate}Hz"
            )

        except ImportError:
            logger.error("pvporcupine not installed. Run: pip install pvporcupine")
        except Exception as e:
            logger.error(f"Porcupine init error: {e}")

    def start(self) -> bool:
        """Start wake word detection in a background thread. Returns True if started."""
        if not self._initialized:
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._detection_loop,
            name="WakeWordDetector",
            daemon=True,
        )
        self._thread.start()
        logger.info("Wake word detector started — listening...")
        return True

    def stop(self) -> None:
        """Stop detection and release resources."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self._cleanup()
        logger.info("Wake word detector stopped.")

    def _detection_loop(self) -> None:
        """
        Core detection loop running in background thread.
        Opens its own PyAudio stream at Porcupine's required sample rate (16kHz).
        """
        try:
            import pyaudio
            self._pa = pyaudio.PyAudio()
            self._audio_stream = self._pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self._porcupine.frame_length,
            )

            logger.debug("Wake word audio stream open.")
            while self._running:
                pcm_bytes = self._audio_stream.read(
                    self._porcupine.frame_length,
                    exception_on_overflow=False,
                )
                # Porcupine expects a list of 16-bit signed integers
                pcm = struct.unpack_from(
                    f"{self._porcupine.frame_length}h", pcm_bytes
                )
                keyword_index = self._porcupine.process(pcm)

                if keyword_index >= 0:
                    logger.info("🎙️  Wake word detected!")
                    try:
                        self._callback()
                    except Exception as e:
                        logger.error(f"Wake word callback error: {e}")

        except Exception as e:
            if self._running:
                logger.error(f"Wake word detection loop error: {e}")
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Release audio resources."""
        try:
            if self._audio_stream:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
                self._audio_stream = None
        except Exception:
            pass
        try:
            if self._pa:
                self._pa.terminate()
                self._pa = None
        except Exception:
            pass
        try:
            if self._porcupine:
                self._porcupine.delete()
                self._porcupine = None
        except Exception:
            pass

    @property
    def is_available(self) -> bool:
        return self._initialized
