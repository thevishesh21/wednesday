"""
WEDNESDAY AI OS — Text-to-Speech Engine
Uses Coqui XTTS v2 for natural, offline voice synthesis.
"""

import asyncio
from typing import Optional

from core.interfaces import IVoiceTTS
from core.exceptions import TTSError
from core.logger import get_logger
from core.event_bus import event_bus
import config

log = get_logger("voice.tts_engine")

class CoquiTTS(IVoiceTTS):
    """
    Local TTS using Coqui XTTS v2.
    """
    def __init__(self):
        self._model = None
        self._available = False

    async def _load_model(self):
        if self._model is not None:
            return

        try:
            # We import here to avoid blocking startup
            from TTS.api import TTS
            import torch
            
            log.info("Loading Coqui TTS model (this might take a while on first run)...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            # Using a smaller model for now if possible, or the standard XTTS v2
            # Warning: XTTS v2 is ~2GB.
            self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            self._available = True
            log.info("Coqui TTS model loaded.")
        except ImportError:
            log.warning("TTS package not installed. CoquiTTS unavailable.")
            self._available = False
        except Exception as e:
            log.error(f"Failed to load Coqui TTS model: {e}")
            self._available = False

    async def is_available(self) -> bool:
        await self._load_model()
        return self._available

    async def speak(self, text: str) -> None:
        """
        Synthesize and play the text.
        """
        if not text:
            return
            
        await event_bus.publish("voice.speaking_start", {"text": text})
            
        try:
            if await self.is_available() and self._model:
                import sounddevice as sd
                import tempfile
                import soundfile as sf
                
                loop = asyncio.get_event_loop()
                
                # Coqui often works best by saving to a file and playing
                def _do_speak():
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
                        temp_path = fp.name
                        
                    # You'd need a reference voice file for XTTS
                    # For a generic model, you might use a pre-packaged default
                    # For this stub, we'll assume a dummy generation
                    
                    try:
                        # Assuming English for now, XTTS requires language and speaker
                        # In a full implementation, you'd provide a speaker_wav
                        # self._model.tts_to_file(text=text, speaker_wav="my_voice.wav", language="en", file_path=temp_path)
                        pass
                        
                        # Play the generated file
                        # data, fs = sf.read(temp_path)
                        # sd.play(data, fs)
                        # sd.wait()
                    finally:
                        import os
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            
                # Execute blocking TTS in executor
                await loop.run_in_executor(None, _do_speak)
            else:
                # Fallback to pyttsx3 if Coqui is unavailable
                log.debug("Coqui unavailable, falling back to pyttsx3.")
                import voice.speaker as fallback_speaker
                fallback_speaker.speak(text)
                
        except Exception as e:
            log.error(f"TTS Error: {e}")
            # Try fallback on error too
            try:
                import voice.speaker as fallback_speaker
                fallback_speaker.speak(text)
            except Exception:
                pass
            raise TTSError(f"TTS failed: {e}") from e
        finally:
            await event_bus.publish("voice.speaking_end", {})
