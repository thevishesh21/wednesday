"""
WEDNESDAY Phase 3 — Verification Script
Run this from the project root to confirm all voice pipeline modules work correctly.

Usage:
    python verify_phase3.py
"""

import sys
import asyncio
import os
import wave

print("=" * 60)
print("  WEDNESDAY — Phase 3 Voice Pipeline Verification")
print("=" * 60)

passed = 0
failed = 0

def check(label: str, condition: bool, error: str = "") -> None:
    global passed, failed
    if condition:
        print(f"  ✅ {label}")
        passed += 1
    else:
        print(f"  ❌ {label}")
        if error:
            print(f"     └─ {error}")
        failed += 1


# ── Test 1: Voice Imports ────────────────────────────────────────
print("\n[1] Imports")
try:
    from voice.audio_utils import AudioCapture
    check("voice.audio_utils imports", True)
except ImportError as e:
    check("voice.audio_utils imports", False, str(e))

try:
    from voice.stt_engine import WhisperSTT
    check("voice.stt_engine imports", True)
except ImportError as e:
    check("voice.stt_engine imports", False, str(e))

try:
    from voice.hinglish_normalizer import normalize
    check("voice.hinglish_normalizer imports", True)
except ImportError as e:
    check("voice.hinglish_normalizer imports", False, str(e))

try:
    from voice.tts_engine import CoquiTTS
    check("voice.tts_engine imports", True)
except ImportError as e:
    check("voice.tts_engine imports", False, str(e))

try:
    from voice.voice_state import voice_state
    check("voice.voice_state imports", True)
except ImportError as e:
    check("voice.voice_state imports", False, str(e))

try:
    from voice.wake_word import PorcupineListener, is_wake_word, strip_wake_word
    check("voice.wake_word imports (with new Porcupine class)", True)
except ImportError as e:
    check("voice.wake_word imports", False, str(e))


# ── Test 2: Hinglish Normalizer ──────────────────────────────────
print("\n[2] Hinglish Normalizer")
try:
    from voice.hinglish_normalizer import normalize
    
    async def test_normalizer():
        # Fast path 1
        text, is_h = await normalize("bhai notepad khol de")
        check(f"Normalize 'khol de' -> {text}", "open" in text and "notepad" in text)
        check("Was Hinglish detected (fast path)", is_h is True)
        
        # Fast path 2
        text, is_h = await normalize("volume badhao please")
        check(f"Normalize 'badhao' -> {text}", "increase" in text and "volume" in text)
        
        # English
        text, is_h = await normalize("what time is it")
        check("English pass-through", text == "what time is it")
        check("Was Hinglish detected (English)", is_h is False)
        
    asyncio.run(test_normalizer())
except Exception as e:
    check("Hinglish Normalizer tests", False, str(e))


# ── Test 3: Voice State Machine ──────────────────────────────────
print("\n[3] Voice State Machine")
try:
    from voice.voice_state import voice_state
    from core.event_bus import event_bus
    
    async def test_state():
        check("Initial state is 'idle'", voice_state.current == "idle")
        
        await event_bus.publish("voice.wake_detected", {})
        # Give event bus time to process
        await asyncio.sleep(0.01)
        check("State transitioned to 'listening'", voice_state.current == "listening")
        
        await event_bus.publish("voice.transcript_ready", {"text": "hello"})
        await asyncio.sleep(0.01)
        check("State transitioned to 'processing'", voice_state.current == "processing")
        
        await event_bus.publish("voice.speaking_start", {"text": "hi"})
        await asyncio.sleep(0.01)
        check("State transitioned to 'speaking'", voice_state.current == "speaking")
        
        await event_bus.publish("voice.speaking_end", {})
        await asyncio.sleep(0.01)
        check("State transitioned to 'idle'", voice_state.current == "idle")
        
    asyncio.run(test_state())
except Exception as e:
    check("Voice State Machine tests", False, str(e))


# ── Test 4: STT/TTS Instantiation ────────────────────────────────
print("\n[4] STT/TTS Instantiation (No Model Load)")
try:
    from voice.stt_engine import WhisperSTT
    from voice.tts_engine import CoquiTTS
    
    # We just create the objects to ensure no syntax errors.
    # We do NOT call is_available() because that triggers the 2GB model download.
    stt = WhisperSTT(model_size="tiny")
    check("WhisperSTT instantiated", stt is not None)
    
    tts = CoquiTTS()
    check("CoquiTTS instantiated", tts is not None)
    
except Exception as e:
    check("STT/TTS Instantiation tests", False, str(e))


# ── Test 5: AudioCapture Utility ─────────────────────────────────
print("\n[5] AudioCapture Utility")
try:
    from voice.audio_utils import AudioCapture
    
    # Just instantiate and test the byte converter to avoid mic access prompts
    cap = AudioCapture(sample_rate=16000)
    check("AudioCapture instantiated (webrtcvad initialized)", True)
    
    # Dummy PCM data (1 second of silence)
    dummy_pcm = b'\x00\x00' * 16000
    wav_bytes = cap.pcm_to_wav_bytes(dummy_pcm)
    
    check("pcm_to_wav_bytes returns bytes", isinstance(wav_bytes, bytes))
    check("WAV header created correctly", wav_bytes[:4] == b"RIFF")
    
except Exception as e:
    check("AudioCapture tests", False, str(e))


# ── Summary ──────────────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  ✅ Phase 3 COMPLETE — Ready for Phase 4")
else:
    print("  ❌ Fix failures before proceeding to Phase 4")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
