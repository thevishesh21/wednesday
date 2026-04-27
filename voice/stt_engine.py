"""
WEDNESDAY AI OS — Speech-to-Text Engine
Uses faster-whisper for local, offline transcription.
"""

import io
import os
from typing import Optional

from core.interfaces import IVoiceSTT
from core.exceptions import STTError
from core.logger import get_logger
from voice.audio_utils import AudioCapture

log = get_logger("voice.stt_engine")


class WhisperSTT(IVoiceSTT):
    """
    Local STT using faster-whisper.
    Requires CTranslate2 and downloads model weights on first run.
    """

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
        self._available = False

    async def _load_model(self):
        """Lazy load the Whisper model."""
        if self._model is not None:
            return

        try:
            # We import here to avoid blocking startup if the library isn't installed
            from faster_whisper import WhisperModel
            
            log.info(f"Loading faster-whisper model '{self.model_size}'...")
            # Use CPU for now to ensure maximum compatibility. 
            # In a production setup, we'd detect CUDA/CoreML.
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            self._available = True
            log.info("Whisper model loaded successfully.")
        except ImportError:
            log.warning("faster-whisper is not installed. WhisperSTT unavailable.")
            self._available = False
        except Exception as e:
            log.error(f"Failed to load Whisper model: {e}")
            self._available = False

    async def is_available(self) -> bool:
        await self._load_model()
        return self._available

    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe raw PCM audio bytes.
        """
        if not await self.is_available() or not self._model:
            raise STTError("Whisper model is not available")

        if not audio_bytes:
            return ""

        try:
            # faster-whisper can read from a file-like object containing WAV data
            wav_bytes = AudioCapture().pcm_to_wav_bytes(audio_bytes)
            audio_io = io.BytesIO(wav_bytes)

            # Transcribe (this is CPU intensive, so we run it in an executor)
            import asyncio
            loop = asyncio.get_event_loop()
            
            def _do_transcribe():
                segments, info = self._model.transcribe(
                    audio_io, 
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                return " ".join([segment.text for segment in segments]).strip()

            text = await loop.run_in_executor(None, _do_transcribe)
            log.debug(f"Transcribed text: '{text}'")
            return text
            
        except Exception as e:
            raise STTError(f"Transcription failed: {e}") from e
