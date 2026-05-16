"""
voice/listener.py
------------------
Microphone capture with Voice Activity Detection (VAD).

This is the "ears" of Wednesday. It does NOT run continuously — it
captures exactly one utterance when called, using energy-based VAD
to detect when speech starts and ends.

Pipeline:
  1. Open mic stream
  2. Wait for speech (RMS > threshold) with timeout
  3. Record until silence (RMS < threshold for N seconds)
  4. Return WAV bytes of the utterance

Used by the Orchestrator when:
  - Wake word detected (then call capture_utterance())
  - OR always-listening mode (then loop continuously)
"""

import time
import threading
from typing import Optional
from utils.logger import setup_logger
from utils.audio_utils import calculate_rms, frames_to_wav_bytes
from config.settings import settings

logger = setup_logger(__name__)


class MicListener:
    """
    Blocking microphone listener with energy-based VAD.

    Usage:
        listener = MicListener()
        wav_bytes = listener.capture_utterance(timeout=10.0)
        # wav_bytes is ready to pass to Transcriber
    """

    def __init__(self):
        self._sample_rate  = settings.voice.sample_rate
        self._channels     = settings.voice.channels
        self._chunk_size   = settings.voice.chunk_size
        self._threshold    = settings.voice.vad_silence_threshold
        self._sil_dur      = settings.voice.vad_silence_duration
        self._min_speech   = settings.voice.vad_min_speech_duration
        self._max_speech   = settings.voice.vad_max_speech_duration
        self._sample_width = 2   # 16-bit PCM = 2 bytes per sample
        self._pa           = None
        self._stream       = None
        self._lock         = threading.Lock()
        self._init_pyaudio()

    def _init_pyaudio(self) -> None:
        """Initialize PyAudio. Called once at startup."""
        try:
            import pyaudio
            self._pa = pyaudio.PyAudio()
            self._pyaudio = pyaudio
            logger.info("PyAudio initialized ✓")
        except ImportError:
            logger.error(
                "PyAudio not installed.\n"
                "  Windows: pip install PyAudio\n"
                "  If that fails: download .whl from "
                "https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio"
            )
        except Exception as e:
            logger.error(f"PyAudio init failed: {e}")

    def capture_utterance(
        self,
        timeout: float = 8.0,
        on_speech_start: Optional[callable] = None,
        on_speech_end: Optional[callable] = None,
    ) -> Optional[bytes]:
        """
        Listen for one complete utterance and return WAV bytes.

        Blocks until:
          - Speech is detected and ends (normal flow)
          - Timeout expires without speech (returns None)
          - Max speech duration reached (returns what was captured)

        Args:
            timeout:         Seconds to wait for speech to start before giving up.
            on_speech_start: Optional callback when speech begins (e.g., play beep).
            on_speech_end:   Optional callback when speech ends (e.g., stop indicator).

        Returns:
            WAV bytes if speech captured, None if timeout or error.
        """
        if not self._pa:
            logger.error("PyAudio not available.")
            return None

        with self._lock:   # Prevent concurrent captures
            return self._capture(timeout, on_speech_start, on_speech_end)

    def _capture(
        self,
        timeout: float,
        on_speech_start: Optional[callable],
        on_speech_end: Optional[callable],
    ) -> Optional[bytes]:
        """Internal capture logic."""
        try:
            stream = self._pa.open(
                format=self._pyaudio.paInt16,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=self._chunk_size,
            )
        except Exception as e:
            logger.error(f"Failed to open microphone: {e}")
            return None

        frames = []
        speech_started = False
        silence_start: Optional[float] = None
        speech_start_time: Optional[float] = None
        listen_start = time.monotonic()
        chunks_per_second = self._sample_rate / self._chunk_size

        logger.debug(
            f"Listening... (threshold={self._threshold:.3f}, "
            f"timeout={timeout}s, max={self._max_speech}s)"
        )

        try:
            while True:
                now = time.monotonic()
                elapsed = now - listen_start

                # ── Timeout: waiting for speech to start ────────────────
                if not speech_started and elapsed > timeout:
                    logger.debug(f"Listen timeout ({timeout}s) — no speech detected.")
                    return None

                # ── Max speech duration reached ─────────────────────────
                if speech_started and speech_start_time:
                    speech_duration = now - speech_start_time
                    if speech_duration > self._max_speech:
                        logger.debug(f"Max speech duration reached ({self._max_speech}s)")
                        break

                # ── Read audio chunk ─────────────────────────────────────
                try:
                    chunk = stream.read(self._chunk_size, exception_on_overflow=False)
                except Exception as e:
                    logger.warning(f"Mic read error: {e}")
                    break

                rms = calculate_rms(chunk, self._sample_width)

                # ── Voice Activity Detection ─────────────────────────────
                if rms >= self._threshold:
                    # Sound detected
                    if not speech_started:
                        speech_started = True
                        speech_start_time = now
                        silence_start = None
                        logger.debug(f"Speech start detected (RMS={rms:.4f})")
                        if on_speech_start:
                            try:
                                on_speech_start()
                            except Exception:
                                pass
                    else:
                        silence_start = None  # Reset silence timer
                    frames.append(chunk)

                elif speech_started:
                    # Speech started but now it's quiet — count silence
                    frames.append(chunk)  # Keep recording during silence
                    if silence_start is None:
                        silence_start = now
                    elif (now - silence_start) >= self._sil_dur:
                        logger.debug(
                            f"Silence detected for {self._sil_dur}s — "
                            f"speech ended."
                        )
                        break

        finally:
            stream.stop_stream()
            stream.close()

        if on_speech_end:
            try:
                on_speech_end()
            except Exception:
                pass

        if not frames:
            return None

        # Check minimum speech duration
        speech_seconds = len(frames) * self._chunk_size / self._sample_rate
        if speech_seconds < self._min_speech:
            logger.debug(
                f"Recording too short ({speech_seconds:.2f}s < "
                f"{self._min_speech}s minimum) — discarding."
            )
            return None

        wav_bytes = frames_to_wav_bytes(
            frames, self._sample_rate, self._sample_width, self._channels
        )
        logger.debug(f"Captured {speech_seconds:.1f}s of audio ({len(wav_bytes)} bytes)")
        return wav_bytes

    def get_ambient_noise_level(self, duration: float = 1.0) -> float:
        """
        Sample ambient noise for N seconds and return average RMS.
        Use this to auto-calibrate the VAD threshold.
        """
        if not self._pa:
            return 0.015

        try:
            stream = self._pa.open(
                format=self._pyaudio.paInt16,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=self._chunk_size,
            )
            samples = []
            end_time = time.monotonic() + duration
            while time.monotonic() < end_time:
                chunk = stream.read(self._chunk_size, exception_on_overflow=False)
                samples.append(calculate_rms(chunk, self._sample_width))
            stream.stop_stream()
            stream.close()
            avg = sum(samples) / max(len(samples), 1)
            logger.info(f"Ambient noise level: {avg:.4f} RMS")
            return avg
        except Exception as e:
            logger.warning(f"Ambient noise measurement failed: {e}")
            return 0.015

    def auto_calibrate_threshold(self, multiplier: float = 2.5) -> None:
        """
        Measure ambient noise and set threshold = noise * multiplier.
        Call this once at startup for better VAD accuracy.
        """
        logger.info("Calibrating microphone — please be quiet for 1 second...")
        ambient = self.get_ambient_noise_level(1.0)
        new_threshold = max(ambient * multiplier, 0.010)
        settings.voice.vad_silence_threshold = new_threshold
        self._threshold = new_threshold
        logger.info(f"VAD threshold set to {new_threshold:.4f} (ambient={ambient:.4f})")

    def shutdown(self) -> None:
        """Release PyAudio resources."""
        try:
            if self._pa:
                self._pa.terminate()
                self._pa = None
        except Exception:
            pass
