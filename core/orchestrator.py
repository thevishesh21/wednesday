"""
core/orchestrator.py
---------------------
Wednesday's central brain — Phase 2 version.

Now routes SYSTEM_CMD and BROWSER_CMD to SystemAgent.
All other input goes to the LLM for conversation.
"""

import asyncio
import sys
import time
import logging
from typing import Optional

from config.settings  import settings
from core.llm_gateway import LLMGateway
from core.intent_classifier import IntentClassifier, Intent
from core.response_builder  import ResponseBuilder
from memory.short_term      import ShortTermMemory

logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(self):
        self.llm        = LLMGateway()
        self.memory     = ShortTermMemory()
        self.classifier = IntentClassifier()
        self.builder    = ResponseBuilder()

        # Phase 2 agent
        self._system_agent = None

        # Voice components
        self._listener    = None
        self._transcriber = None
        self._wake_word   = None
        self._speaker     = None

        # State
        self._running    = False
        self._muted      = False
        self._wake_event = asyncio.Event()

        logger.info("Orchestrator initialized.")

    # ── Startup ────────────────────────────────────────────────

    async def start(self) -> None:
        self._running = True
        self._print_banner()

        from utils.system_utils import get_system_info
        logger.info(f"System: {get_system_info()}")

        # Init speaker
        self._init_speaker()

        # Init Phase 2 agent
        self._init_system_agent()

        # Try voice pipeline
        voice_ok = self._init_voice_pipeline()

        if voice_ok:
            await self._voice_loop()
        else:
            logger.info("Voice not available — running in text mode.")
            await self._text_loop()

    async def stop(self) -> None:
        self._running = False
        self._wake_event.set()

        if self._speaker:
            self._speaker.shutdown()
        if self._listener:
            self._listener.shutdown()
        if self._wake_word:
            self._wake_word.stop()
        if self._system_agent:
            await self._system_agent.shutdown()

        logger.info("Wednesday stopped.")

    # ── Init helpers ───────────────────────────────────────────

    def _init_speaker(self) -> None:
        try:
            from voice.speaker import Speaker
            self._speaker = Speaker()
            logger.info("Speaker initialized ✓")
        except Exception as e:
            logger.warning(f"Speaker init failed: {e}")

    def _init_system_agent(self) -> None:
        try:
            from agents.system_agent import SystemAgent
            self._system_agent = SystemAgent()
            logger.info("SystemAgent initialized ✓")
        except Exception as e:
            logger.warning(f"SystemAgent init failed: {e}")

    def _init_voice_pipeline(self) -> bool:
        try:
            import pyaudio
        except ImportError:
            logger.warning("PyAudio not installed — text mode only.")
            return False

        try:
            from voice.listener   import MicListener
            from voice.transcriber import Transcriber
            self._listener    = MicListener()
            self._transcriber = Transcriber()
            self._listener.auto_calibrate_threshold()
        except Exception as e:
            logger.warning(f"Voice pipeline init failed: {e}")
            return False

        if settings.voice.enable_wake_word and settings.has_porcupine():
            try:
                from voice.wake_word import WakeWordDetector
                self._wake_word = WakeWordDetector(
                    on_wake_callback=self._on_wake_word
                )
                self._wake_word.start()
            except Exception as e:
                logger.warning(f"Wake word init failed: {e}")

        return True

    def _on_wake_word(self) -> None:
        asyncio.get_event_loop().call_soon_threadsafe(self._wake_event.set)

    # ── Loops ──────────────────────────────────────────────────

    async def _text_loop(self) -> None:
        greeting = await self._build_greeting()
        print(f"\nWednesday: {greeting}\n")
        self.memory.add_assistant(greeting)
        if self._speaker:
            await self._speaker.say(greeting)

        print("Commands: /memory | /clear | /stats | quit\n")

        while self._running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("You: ").strip()
                )
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "bye"):
                farewell = await self._quick_llm("Say a brief warm goodbye as Wednesday. One sentence.")
                print(f"Wednesday: {farewell}")
                if self._speaker:
                    await self._speaker.say_and_wait(farewell)
                self._running = False
                break

            response = await self.process_input(user_input)
            print(f"\nWednesday: {response}\n")

            if self._speaker and not self._muted:
                await self._speaker.say(response)

    async def _voice_loop(self) -> None:
        logger.info("Voice mode active.")
        greeting = await self._build_greeting()
        await self._speak(greeting)
        print(f"{'─'*60}")

        if self._wake_word:
            print("  Say 'Hey Wednesday' (or 'computer') to activate.")
            await self._wake_word_loop()
        else:
            print("  Listening continuously — just speak!")
            await self._always_listening_loop()

    async def _wake_word_loop(self) -> None:
        while self._running:
            self._wake_event.clear()
            try:
                await self._wake_event.wait()
            except asyncio.CancelledError:
                break
            if not self._running:
                break

            await self._speak("Yes?", skip_memory=True)
            wav = await self._capture_speech()
            if not wav:
                await self._speak("I didn't catch that.", skip_memory=True)
                continue
            await self._handle_audio(wav)

    async def _always_listening_loop(self) -> None:
        while self._running:
            await asyncio.sleep(0.3)
            print("🎙️  Listening...", flush=True)
            wav = await self._capture_speech(timeout=8.0)
            if wav:
                await self._handle_audio(wav)

    async def _capture_speech(self, timeout: float = 8.0) -> Optional[bytes]:
        try:
            wav = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._listener.capture_utterance(
                    timeout=timeout,
                    on_speech_start=lambda: print("  [Heard you...]", flush=True),
                    on_speech_end=lambda: print("  [Processing...]", flush=True),
                )
            )
            return wav
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return None

    async def _handle_audio(self, wav: bytes) -> None:
        text = await asyncio.get_event_loop().run_in_executor(
            None, self._transcriber.transcribe, wav
        )
        if not text:
            return
        print(f"You: {text}")
        response = await self.process_input(text)
        await self._speak(response)

    # ── Core pipeline ──────────────────────────────────────────

    async def process_input(self, user_input: str) -> str:
        """
        Main pipeline — routes every input correctly.

        1. Store in memory
        2. Classify intent
        3. Handle meta commands (/memory, /clear)
        4. Route to SystemAgent (SYSTEM_CMD, BROWSER_CMD)
        5. Or converse with LLM (CONVERSATION)
        6. Clean and return response
        """
        if not user_input.strip():
            return ""

        logger.info(f"Input: '{user_input}'")
        t0 = time.monotonic()

        # 1. Store
        self.memory.add_user(user_input)

        # 2. Classify
        intent = self.classifier.classify(user_input)
        logger.info(f"Intent: {intent.category} / {intent.action}")

        # 3. Meta
        if intent.category == "META":
            result = self._handle_meta(intent)
            return result

        # 4. System / Browser agent
        if intent.category in ("SYSTEM_CMD", "BROWSER_CMD") and self._system_agent:
            try:
                agent_response = await self._system_agent.handle(
                    intent.action, intent.entities, user_input
                )
                if agent_response:
                    self.memory.add_assistant(agent_response)
                    logger.info(f"Agent handled in {time.monotonic()-t0:.2f}s")
                    return agent_response
            except Exception as e:
                logger.error(f"SystemAgent error: {e}")
                # Fall through to LLM

        # 5. LLM conversation (default)
        messages = self.memory.get_messages()
        response_raw = await self.llm.chat(messages=messages)

        # 6. Clean
        response = self.builder.clean_for_voice(response_raw)
        self.memory.add_assistant(response)

        logger.info(f"Pipeline done: {time.monotonic()-t0:.2f}s")
        return response

    def _handle_meta(self, intent: Intent) -> str:
        if intent.action == "show_memory":
            dump = self.memory.summary_str()
            print(f"\n[Memory — {len(self.memory)} messages]\n{dump}\n")
            return f"I have {len(self.memory)} messages in active memory."
        if intent.action == "clear_memory":
            self.memory.clear()
            return "Memory cleared. Fresh start."
        if intent.action == "show_stats":
            s = self.llm.get_stats()
            return (f"Stats: {s['total_calls']} LLM calls, "
                    f"~{s['total_tokens']} tokens, provider: {s['provider']}.")
        return "Unknown command."

    # ── Speak helper ───────────────────────────────────────────

    async def _speak(self, text: str, skip_memory: bool = False) -> None:
        if text:
            print(f"Wednesday: {text}", flush=True)
            if self._speaker and not self._muted:
                await self._speaker.say(text)
            if not skip_memory:
                self.memory.add_assistant(text)

    # ── LLM helpers ────────────────────────────────────────────

    async def _build_greeting(self) -> str:
        text = await self._quick_llm(
            f"Greet the user as Wednesday. Start of session. "
            f"Warm, brief (1-2 sentences). Mention you can now open apps, "
            f"control the browser, and handle voice commands. "
            f"Address them as {settings.user_name}."
        )
        return self.builder.clean_for_voice(text)

    async def _quick_llm(self, prompt: str) -> str:
        return await self.llm.chat([{"role": "user", "content": prompt}])

    # ── Public controls ────────────────────────────────────────

    def mute(self)   -> None: self._muted = True;  self._speaker and self._speaker.stop()
    def unmute(self) -> None: self._muted = False
    def clear_memory(self) -> None: self.memory.clear()

    @property
    def state(self) -> str:
        return "speaking" if (self._speaker and self._speaker.is_speaking) else "idle"

    # ── Banner ─────────────────────────────────────────────────

    def _print_banner(self) -> None:
        p = settings.llm.provider
        model_map = {
            "groq":   settings.llm.groq_model,
            "gemini": settings.llm.gemini_model,
            "ollama": settings.llm.ollama_model,
            "openai": settings.llm.openai_model,
            "claude": settings.llm.claude_model,
        }
        model = model_map.get(p, "unknown")
        print(f"""
╔══════════════════════════════════════════════════════════╗
║   W E D N E S D A Y  —  Phase 2                         ║
║                                                          ║
║   LLM:  {p:<12} {model:<30}║
║   TTS:  {settings.voice.tts_engine:<12} STT: {settings.voice.whisper_model:<24}║
║   Apps: enabled      Browser: enabled                   ║
║                                                          ║
║   Try: "open notepad" | "search python on google"        ║
║   Type 'quit' to exit | Ctrl+C to stop                   ║
╚══════════════════════════════════════════════════════════╝
""")
