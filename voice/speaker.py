"""
voice/speaker.py
-----------------
Wednesday's voice output — Text-to-Speech engine.

FIX: pyttsx3 engine is now recreated fresh for each utterance.
This prevents the "speaks first but not second" bug caused by
pyttsx3's runAndWait() not resetting cleanly between calls.
"""

import time
import threading
import queue
from typing import Optional
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class Speaker:
    """
    Reliable TTS engine for Wednesday.

    Uses a dedicated background thread with a fresh pyttsx3 call
    per utterance to avoid the runAndWait() stall bug on Windows.
    """

    def __init__(self):
        self._engine_name = settings.voice.tts_engine
        self._queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._speaking = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._elevenlabs_headers: Optional[dict] = None
        self._init()

    # ── Initialization ─────────────────────────────────────────

    def _init(self) -> None:
        if self._engine_name == "elevenlabs" and settings.has_elevenlabs():
            self._init_elevenlabs()
        else:
            if self._engine_name == "elevenlabs":
                logger.warning(
                    "ElevenLabs selected but ELEVENLABS_API_KEY not found. "
                    "Falling back to pyttsx3."
                )
            self._engine_name = "pyttsx3"
            self._init_pyttsx3()

    def _init_pyttsx3(self) -> None:
        """Start the pyttsx3 worker thread."""
        try:
            import pyttsx3
            # Quick test to confirm pyttsx3 works
            test_engine = pyttsx3.init()
            voices = test_engine.getProperty("voices")
            self._selected_voice_id = None
            if voices:
                female = next(
                    (v for v in voices if any(
                        kw in v.name.lower()
                        for kw in ["zira", "female", "woman", "eva", "helen"]
                    )),
                    voices[0],
                )
                self._selected_voice_id = female.id
                logger.info(f"pyttsx3 voice: {female.name}")
            test_engine.stop()
            del test_engine

            # Start worker thread
            self._worker_thread = threading.Thread(
                target=self._pyttsx3_worker,
                name="Speaker-pyttsx3",
                daemon=True,
            )
            self._worker_thread.start()
            logger.info("pyttsx3 TTS initialized ✓")

        except ImportError:
            logger.error("pyttsx3 not installed. Run: pip install pyttsx3")
        except Exception as e:
            logger.error(f"pyttsx3 init error: {e}")

    def _init_elevenlabs(self) -> None:
        self._elevenlabs_headers = {
            "xi-api-key":   settings.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept":       "audio/mpeg",
        }
        if not settings.voice.elevenlabs_voice_id:
            settings.voice.elevenlabs_voice_id = "21m00Tcm4TlvDq8ikWAM"

        self._worker_thread = threading.Thread(
            target=self._elevenlabs_worker,
            name="Speaker-ElevenLabs",
            daemon=True,
        )
        self._worker_thread.start()
        logger.info(f"ElevenLabs TTS initialized ✓")

    # ── Public API ─────────────────────────────────────────────

    async def say(self, text: str) -> None:
        """
        Queue text for speaking. Returns immediately.
        The background thread plays it reliably.
        """
        if not text or not text.strip():
            return
        self._stop_event.clear()
        self._queue.put(text.strip())
        logger.debug(f"Queued: '{text[:60]}'")

    async def say_and_wait(self, text: str, timeout: float = 30.0) -> None:
        """Speak and block until finished."""
        import asyncio
        await self.say(text)
        await asyncio.sleep(0.2)
        start = time.monotonic()
        while self._speaking.is_set() or not self._queue.empty():
            if time.monotonic() - start > timeout:
                break
            await asyncio.sleep(0.1)

    def stop(self) -> None:
        """Stop speaking immediately and clear the queue."""
        self._stop_event.set()
        # Drain queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def shutdown(self) -> None:
        """Shut down the worker thread cleanly."""
        self.stop()
        self._queue.put(None)  # Sentinel
        if self._worker_thread:
            self._worker_thread.join(timeout=3.0)
        logger.info("Speaker shut down.")

    @property
    def is_speaking(self) -> bool:
        return self._speaking.is_set()

    # ── pyttsx3 Worker ─────────────────────────────────────────

    def _pyttsx3_worker(self) -> None:
        """
        Background thread that speaks each queued item.

        KEY FIX: We create a FRESH pyttsx3 engine for every single
        utterance. This is slightly slower but 100% reliable on Windows.
        The alternative (reusing the engine) causes silent failures after
        the first speak() call due to how pyttsx3 wraps SAPI5 on Windows.
        """
        import pyttsx3

        while True:
            try:
                text = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            # Shutdown sentinel
            if text is None:
                return

            # Skip if stop was requested
            if self._stop_event.is_set():
                self._queue.task_done()
                continue

            self._speaking.set()
            try:
                # Fresh engine every time — this is the fix
                engine = pyttsx3.init()
                engine.setProperty("rate", settings.voice.tts_rate)
                engine.setProperty("volume", settings.voice.tts_volume)
                if self._selected_voice_id:
                    engine.setProperty("voice", self._selected_voice_id)

                engine.say(text)
                engine.runAndWait()
                engine.stop()

            except Exception as e:
                logger.error(f"pyttsx3 speak error: {e}")
            finally:
                self._speaking.clear()
                try:
                    self._queue.task_done()
                except Exception:
                    pass

    # ── ElevenLabs Worker ──────────────────────────────────────

    def _elevenlabs_worker(self) -> None:
        """Background thread for ElevenLabs TTS."""
        while True:
            try:
                text = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if text is None:
                return

            if self._stop_event.is_set():
                self._queue.task_done()
                continue

            self._speaking.set()
            try:
                audio_bytes = self._elevenlabs_request(text)
                if audio_bytes and not self._stop_event.is_set():
                    self._play_audio(audio_bytes)
            except Exception as e:
                logger.error(f"ElevenLabs error: {e} — falling back to pyttsx3")
                self._pyttsx3_fallback(text)
            finally:
                self._speaking.clear()
                try:
                    self._queue.task_done()
                except Exception:
                    pass

    def _elevenlabs_request(self, text: str) -> Optional[bytes]:
        import httpx
        voice_id = settings.voice.elevenlabs_voice_id
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }
        with httpx.Client(timeout=20) as client:
            response = client.post(url, headers=self._elevenlabs_headers, json=payload)
            response.raise_for_status()
            return response.content

    def _play_audio(self, audio_bytes: bytes) -> None:
        import io
        try:
            import pygame
            pygame.mixer.init()
            sound = pygame.mixer.Sound(io.BytesIO(audio_bytes))
            channel = sound.play()
            while channel.get_busy():
                if self._stop_event.is_set():
                    channel.stop()
                    break
                time.sleep(0.05)
        except ImportError:
            logger.error("pygame not installed. Run: pip install pygame")
        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    def _pyttsx3_fallback(self, text: str) -> None:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", settings.voice.tts_rate)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            logger.error(f"pyttsx3 fallback error: {e}")