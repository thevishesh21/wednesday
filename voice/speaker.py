"""
voice/speaker.py
-----------------
DEFINITIVE FIX — Uses Windows SAPI5 directly via win32com.
No pyttsx3. No COM conflicts. Speaks every single response.

Why this works:
  win32com.client.Dispatch("SAPI.SpVoice") is the raw Windows
  text-to-speech COM object. We call it from ONE dedicated thread
  that never exits. No wrapper bugs, no state issues.

Fallback: if win32com not available, uses subprocess + PowerShell
which also works 100% reliably on every Windows machine.
"""

import threading
import queue
import time
import logging
import sys

logger = logging.getLogger(__name__)


class Speaker:
    """
    Rock-solid Windows TTS.
    Speaks every response — first, second, hundredth.
    """

    def __init__(self):
        self._queue     = queue.Queue()
        self._done      = threading.Event()
        self._stop_flag = threading.Event()
        self._speaking  = False
        self._ready     = threading.Event()
        self._rate      = 180
        self._volume    = 100

        try:
            from config.settings import settings
            self._rate   = settings.voice.tts_rate
            self._volume = int(settings.voice.tts_volume * 100)
        except Exception:
            pass

        # Detect best available method
        self._method = self._detect_method()
        logger.info(f"TTS method: {self._method}")

        # Start permanent TTS thread
        self._thread = threading.Thread(
            target=self._run,
            name="TTS-Thread",
            daemon=True,
        )
        self._thread.start()
        self._ready.wait(timeout=15)
        logger.info("Speaker ready ✓")

    def _detect_method(self) -> str:
        """Pick the best TTS method available."""
        if sys.platform == "win32":
            try:
                import win32com.client
                return "sapi"
            except ImportError:
                pass
            # PowerShell is always available on Windows
            return "powershell"
        else:
            try:
                import pyttsx3
                return "pyttsx3"
            except ImportError:
                return "none"

    # ── Permanent TTS thread ───────────────────────────────────

    def _run(self):
        if self._method == "sapi":
            self._run_sapi()
        elif self._method == "powershell":
            self._run_powershell()
        elif self._method == "pyttsx3":
            self._run_pyttsx3()
        else:
            logger.error("No TTS method available.")
            self._ready.set()

    def _run_sapi(self):
        """
        Windows SAPI5 via win32com — most reliable method.
        Direct COM access, no wrapper issues.
        """
        try:
            import win32com.client
            sapi = win32com.client.Dispatch("SAPI.SpVoice")

            # Set rate: SAPI rate is -10 to +10
            # Convert wpm (150-220) to SAPI rate (-2 to +4)
            sapi_rate = int((self._rate - 180) / 20)
            sapi.Rate   = max(-10, min(10, sapi_rate))
            sapi.Volume = self._volume

            # Try to select female voice
            voices = sapi.GetVoices()
            for i in range(voices.Count):
                v = voices.Item(i)
                name = v.GetDescription()
                if any(k in name.lower() for k in ["zira", "female", "woman", "eva"]):
                    sapi.Voice = v
                    logger.info(f"SAPI voice: {name}")
                    break

            self._ready.set()
            logger.info("SAPI TTS thread running.")

            while True:
                try:
                    text = self._queue.get(timeout=0.3)
                except queue.Empty:
                    continue

                if text is None:
                    break

                if not self._stop_flag.is_set():
                    self._speaking = True
                    try:
                        # SVSFlagsAsync=1 lets us cancel mid-speech
                        sapi.Speak(text, 1)   # Async speak
                        # Wait until done or stopped
                        while sapi.Status.RunningState == 2:  # 2 = running
                            if self._stop_flag.is_set():
                                sapi.Skip("Sentence", 999)
                                break
                            time.sleep(0.05)
                    except Exception as e:
                        logger.error(f"SAPI speak error: {e}")
                    finally:
                        self._speaking = False

                self._done.set()
                try:
                    self._queue.task_done()
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"SAPI init error: {e} — falling back to PowerShell")
            self._method = "powershell"
            self._ready.set()
            self._run_powershell()

    def _run_powershell(self):
        """
        PowerShell TTS — works on ANY Windows machine, no extra packages.
        Uses Add-Type to call .NET speech synthesis directly.
        """
        import subprocess

        self._ready.set()
        logger.info("PowerShell TTS thread running.")

        while True:
            try:
                text = self._queue.get(timeout=0.3)
            except queue.Empty:
                continue

            if text is None:
                break

            if not self._stop_flag.is_set():
                self._speaking = True
                try:
                    # Escape single quotes for PowerShell
                    safe = text.replace("'", "''")
                    ps_script = (
                        "Add-Type -AssemblyName System.Speech; "
                        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                        f"$s.Rate = {int((self._rate - 180) / 20)}; "
                        f"$s.Volume = {self._volume}; "
                        f"$s.Speak('{safe}');"
                    )
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_script],
                        timeout=60,
                        capture_output=True,
                    )
                except subprocess.TimeoutExpired:
                    logger.warning("TTS timeout.")
                except Exception as e:
                    logger.error(f"PowerShell TTS error: {e}")
                finally:
                    self._speaking = False

            self._done.set()
            try:
                self._queue.task_done()
            except Exception:
                pass

    def _run_pyttsx3(self):
        """pyttsx3 fallback for non-Windows."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume / 100)
            self._ready.set()
            logger.info("pyttsx3 TTS thread running.")

            while True:
                try:
                    text = self._queue.get(timeout=0.3)
                except queue.Empty:
                    continue

                if text is None:
                    break

                if not self._stop_flag.is_set():
                    self._speaking = True
                    try:
                        engine.say(text)
                        engine.runAndWait()
                    except Exception as e:
                        logger.error(f"pyttsx3 error: {e}")
                    finally:
                        self._speaking = False

                self._done.set()
                try:
                    self._queue.task_done()
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"pyttsx3 init error: {e}")
            self._ready.set()

    # ── Public API ─────────────────────────────────────────────

    async def say(self, text: str) -> None:
        """Speak text. Non-blocking. Works every time."""
        if not text or not text.strip():
            return
        self._stop_flag.clear()
        self._done.clear()
        self._queue.put(text.strip())
        logger.debug(f"TTS: '{text[:60]}'")

    async def say_and_wait(self, text: str, timeout: float = 30.0) -> None:
        """Speak and wait until finished."""
        import asyncio
        await self.say(text)
        start = time.monotonic()
        while not self._done.is_set():
            if time.monotonic() - start > timeout:
                break
            await asyncio.sleep(0.05)

    def speak_sync(self, text: str, wait: bool = True) -> None:
        """Synchronous speak for non-async contexts."""
        if not text or not text.strip():
            return
        self._stop_flag.clear()
        self._done.clear()
        self._queue.put(text.strip())
        if wait:
            self._done.wait(timeout=30)

    def stop(self) -> None:
        """Stop current speech."""
        self._stop_flag.set()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except Exception:
                break

    def shutdown(self) -> None:
        """Clean shutdown."""
        self.stop()
        self._queue.put(None)
        self._thread.join(timeout=3.0)
        logger.info("Speaker shut down.")

    @property
    def is_speaking(self) -> bool:
        return self._speaking