"""
voice/transcriber.py
---------------------
Speech-to-Text using faster-whisper (runs 100% locally, no API cost).

faster-whisper is a re-implementation of OpenAI's Whisper model using
CTranslate2, which is 2-4x faster than original Whisper and uses less RAM.

Model sizes (English-only .en variants are faster):
  tiny.en   ~40MB  fastest  lower accuracy
  base.en   ~80MB  fast     good accuracy    ← default
  small.en  ~240MB medium   better accuracy
  medium.en ~770MB slower   best accuracy

First run: model is auto-downloaded to ~/.cache/huggingface/hub/
"""

import io
import time
import numpy as np
from pathlib import Path
from typing import Optional
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class Transcriber:
    """
    Converts audio bytes (WAV format) to text using faster-whisper.

    Usage:
        transcriber = Transcriber()
        text = transcriber.transcribe(wav_bytes)
    """

    def __init__(self):
        self._model = None
        self._model_name = settings.voice.whisper_model
        self._device = settings.voice.whisper_device
        self._compute_type = settings.voice.whisper_compute_type
        self._load_model()

    def _load_model(self) -> None:
        """Load the Whisper model. Called once at startup."""
        try:
            from faster_whisper import WhisperModel
            logger.info(
                f"Loading Whisper model '{self._model_name}' "
                f"on {self._device} ({self._compute_type}) ..."
            )
            t0 = time.monotonic()
            self._model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type=self._compute_type,
                download_root=None,          # Uses HuggingFace cache
                local_files_only=False,      # Download if not cached
            )
            elapsed = time.monotonic() - t0
            logger.info(f"Whisper model loaded in {elapsed:.1f}s ✓")
        except ImportError:
            logger.error(
                "faster-whisper not installed. Run: pip install faster-whisper"
            )
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")

    def transcribe(self, wav_bytes: bytes) -> Optional[str]:
        """
        Transcribe WAV audio bytes to text.

        Args:
            wav_bytes: Complete WAV file as bytes (including header).

        Returns:
            Transcribed text string, or None if transcription failed/empty.
        """
        if not self._model:
            logger.error("Whisper model not loaded.")
            return None

        if len(wav_bytes) < 100:
            logger.debug("Audio too short to transcribe.")
            return None

        try:
            t0 = time.monotonic()

            # faster-whisper accepts a file path or numpy array.
            # We use a BytesIO buffer to avoid writing temp files.
            audio_buffer = io.BytesIO(wav_bytes)

            segments, info = self._model.transcribe(
                audio_buffer,
                language="en",
                beam_size=5,
                best_of=5,
                temperature=0.0,         # Greedy decoding (fastest, consistent)
                vad_filter=True,         # Built-in VAD — skip silent segments
                vad_parameters={
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400,
                },
                condition_on_previous_text=False,  # Don't hallucinate continuations
            )

            # Collect all segment texts
            text_parts = []
            for segment in segments:
                cleaned = segment.text.strip()
                if cleaned:
                    text_parts.append(cleaned)

            if not text_parts:
                logger.debug("Transcription returned empty result.")
                return None

            full_text = " ".join(text_parts).strip()

            elapsed = time.monotonic() - t0
            logger.info(
                f"Transcribed ({elapsed:.2f}s, lang={info.language}, "
                f"prob={info.language_probability:.2f}): '{full_text}'"
            )

            # Filter out whisper hallucinations
            if self._is_hallucination(full_text):
                logger.debug(f"Filtered hallucination: '{full_text}'")
                return None

            return full_text

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return None

    @staticmethod
    def _is_hallucination(text: str) -> bool:
        """
        Detect common Whisper hallucinations — phrases it generates for silence.
        These appear when the model gets low-energy noise and makes something up.
        """
        HALLUCINATIONS = {
            "thank you",
            "thanks for watching",
            "thanks for watching!",
            "you",
            ".",
            "",
            "bye",
            "bye!",
            "please subscribe",
            "subscribe",
        }
        return text.lower().strip().rstrip(".,!?") in {h.lower() for h in HALLUCINATIONS}

    def reload_model(self, model_name: Optional[str] = None) -> None:
        """Hot-reload the model (e.g., switch from base.en to small.en)."""
        if model_name:
            self._model_name = model_name
        self._model = None
        self._load_model()
