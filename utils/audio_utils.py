"""
utils/audio_utils.py
---------------------
Audio helper utilities for Wednesday.

Provides:
  - RMS energy calculation (for VAD silence detection)
  - Audio normalization
  - Device enumeration for debugging
  - WAV save/load helpers
"""

import io
import wave
import struct
import numpy as np
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_rms(audio_data: bytes, sample_width: int = 2) -> float:
    """
    Calculate Root Mean Square (RMS) energy of a raw PCM audio chunk.

    Used by the VAD (Voice Activity Detector) to distinguish speech from silence.
    Higher RMS = louder audio.

    Args:
        audio_data:   Raw PCM bytes from PyAudio
        sample_width: Bytes per sample (1=8bit, 2=16bit, 4=32bit)

    Returns:
        RMS value as float (0.0 = silence, ~0.1+ = speech)
    """
    if not audio_data:
        return 0.0

    fmt = {1: "B", 2: "h", 4: "i"}.get(sample_width, "h")
    count = len(audio_data) // sample_width

    try:
        samples = struct.unpack(f"{count}{fmt}", audio_data[:count * sample_width])
        if not samples:
            return 0.0
        max_val = 32768.0 if sample_width == 2 else (128.0 if sample_width == 1 else 2147483648.0)
        normalized = [s / max_val for s in samples]
        rms = (sum(s ** 2 for s in normalized) / len(normalized)) ** 0.5
        return rms
    except Exception as e:
        logger.debug(f"RMS calculation error: {e}")
        return 0.0


def audio_bytes_to_numpy(audio_data: bytes, sample_width: int = 2) -> np.ndarray:
    """Convert raw PCM bytes to a normalized float32 numpy array."""
    fmt = {1: np.int8, 2: np.int16, 4: np.int32}.get(sample_width, np.int16)
    arr = np.frombuffer(audio_data, dtype=fmt).astype(np.float32)
    max_val = np.iinfo(fmt).max
    return arr / max_val


def save_wav(audio_frames: list, sample_rate: int, sample_width: int,
             channels: int, filepath: str) -> None:
    """Save raw PCM frames to a WAV file (useful for debugging STT)."""
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(audio_frames))
    logger.debug(f"Saved WAV: {filepath}")


def frames_to_wav_bytes(audio_frames: list, sample_rate: int,
                         sample_width: int, channels: int) -> bytes:
    """Convert raw PCM frames to an in-memory WAV byte stream."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(audio_frames))
    return buf.getvalue()


def list_audio_devices() -> None:
    """Print all available audio input/output devices. Useful for debugging."""
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        count = pa.get_device_count()
        logger.info(f"Found {count} audio devices:")
        for i in range(count):
            info = pa.get_device_info_by_index(i)
            direction = []
            if info["maxInputChannels"] > 0:
                direction.append("INPUT")
            if info["maxOutputChannels"] > 0:
                direction.append("OUTPUT")
            logger.info(
                f"  [{i:2d}] {info['name'][:50]:50s} | "
                f"{'/'.join(direction)} | "
                f"SR={int(info['defaultSampleRate'])}Hz"
            )
        pa.terminate()
    except ImportError:
        logger.error("PyAudio not installed.")
    except Exception as e:
        logger.error(f"Error listing devices: {e}")


def get_default_input_device_index() -> Optional[int]:
    """Return the index of the system's default microphone."""
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        info = pa.get_default_input_device_info()
        pa.terminate()
        return int(info["index"])
    except Exception as e:
        logger.warning(f"Could not get default input device: {e}")
        return None
