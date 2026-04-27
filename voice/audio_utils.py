"""
WEDNESDAY AI OS — Audio Utilities
Microphone capture and Voice Activity Detection (VAD).
Uses sounddevice for non-blocking capture and webrtcvad for silence detection.
"""

import asyncio
import io
import queue
import wave
from typing import Optional

import sounddevice as sd
import webrtcvad

from core.logger import get_logger
from core.exceptions import VoiceError

log = get_logger("voice.audio_utils")


class AudioCapture:
    """Non-blocking audio capture with VAD silence detection."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        # WebRTC VAD needs specific frame durations (10, 20, or 30 ms)
        self.frame_duration_ms = 30
        self.chunk_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        try:
            self.vad = webrtcvad.Vad(3)  # Aggressiveness: 0-3 (3 is most aggressive in filtering out non-speech)
        except Exception as e:
            log.warning(f"VAD initialization failed: {e}. Silence detection will be less accurate.")
            self.vad = None

    async def record_until_silence(self, silence_duration_sec: float = 1.5, max_duration_sec: float = 15.0) -> bytes:
        """
        Record from the microphone until silence is detected.
        
        Returns:
            Raw PCM audio bytes (16-bit, mono, 16kHz).
            
        Raises:
            VoiceError: If microphone access fails.
        """
        q: queue.Queue[bytes] = queue.Queue()
        
        def audio_callback(indata, frames, time, status):
            if status:
                log.warning(f"Audio capture status: {status}")
            q.put(bytes(indata))

        max_silence_chunks = int((silence_duration_sec * 1000) / self.frame_duration_ms)
        max_total_chunks = int((max_duration_sec * 1000) / self.frame_duration_ms)
        
        audio_chunks: list[bytes] = []
        silence_chunks = 0
        speech_started = False

        log.debug("Starting audio capture...")
        try:
            # We use 'int16' as it is required by webrtcvad
            stream = sd.RawInputStream(
                samplerate=self.sample_rate, 
                blocksize=self.chunk_size,
                channels=self.channels, 
                dtype='int16',
                callback=audio_callback
            )
            
            with stream:
                for _ in range(max_total_chunks):
                    # Non-blocking get with a timeout
                    try:
                        chunk = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: q.get(timeout=0.1)
                        )
                    except queue.Empty:
                        continue

                    audio_chunks.append(chunk)

                    if self.vad:
                        try:
                            is_speech = self.vad.is_speech(chunk, self.sample_rate)
                        except Exception:
                            # Sometimes trailing chunks might not be exact size
                            is_speech = True 
                    else:
                        # Dummy VAD fallback (volume threshold)
                        import numpy as np
                        arr = np.frombuffer(chunk, dtype=np.int16)
                        is_speech = np.abs(arr).mean() > 500

                    if is_speech:
                        speech_started = True
                        silence_chunks = 0
                    elif speech_started:
                        silence_chunks += 1
                        
                    if speech_started and silence_chunks >= max_silence_chunks:
                        log.debug("Silence detected. Stopping capture.")
                        break
                        
        except Exception as e:
            raise VoiceError(f"Microphone capture failed: {e}") from e

        if not speech_started:
            log.debug("No speech detected.")
            return b""

        # Return concatenated raw PCM bytes
        return b"".join(audio_chunks)

    def save_wav(self, pcm_data: bytes, filename: str) -> None:
        """Helper to save raw PCM bytes to a WAV file."""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_data)
            
    def pcm_to_wav_bytes(self, pcm_data: bytes) -> bytes:
        """Convert raw PCM to WAV formatted bytes in memory."""
        with io.BytesIO() as io_wav:
            with wave.open(io_wav, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(pcm_data)
            return io_wav.getvalue()
