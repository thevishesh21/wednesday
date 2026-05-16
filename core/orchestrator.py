"""
core/orchestrator.py
---------------------
Wednesday's central nervous system.

This is the MAIN LOOP. Everything flows through here.

Full Phase 1 pipeline:
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │  [wake word] → [STT capture] → [transcribe] → [classify]   │
  │       ↓                                          ↓          │
  │  [memory inject] → [LLM call] → [clean response] → [TTS]   │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘

In voice mode:
  - Porcupine detects "Hey Wednesday"
  - MicListener captures the utterance
  - Transcriber converts to text
  - IntentClassifier routes to handler
  - LLMGateway generates response
  - ResponseBuilder cleans for voice
  - Speaker plays the response

In text mode (no mic):
  - User types in terminal
  - Same pipeline from IntentClassifier onwards
"""

import asyncio
import sys
import time
from typing import Optional
from utils.logger import setup_logger
from config.settings import settings
from core.llm_gateway import LLMGateway
from core.intent_classifier import IntentClassifier, Intent
from core.response_builder import ResponseBuilder
from memory.short_term import ShortTermMemory

logger = setup_logger(__name__)


class Orchestrator:
    """
    The master coordinator for Wednesday.

    State machine:
      IDLE      → waiting for wake word (or text input)
      LISTENING → mic open, capturing speech
      THINKING  → LLM processing
      SPEAKING  → TTS playing
    """

    def __init__(self):
        # Core components
        self.llm       = LLMGateway()
        self.memory    = ShortTermMemory()
        self.classifier = IntentClassifier()
        self.builder   = ResponseBuilder()

        # Voice components (initialized lazily)
        self._listener    = None
        self._transcriber = None
        self._wake_word   = None
        self._speaker     = None

        # State
        self._running = False
        self._mode    = "text"   # "text" | "voice"
        self._state   = "IDLE"
        self._muted   = False
        self._wake_event = asyncio.Event()  # Set when wake word fires

        logger.info(f"Wednesday Orchestrator initialized.")

    # ──────────────────────────────────────────────────────────
    # Startup / Shutdown
    # ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start Wednesday — detect mode and run appropriate loop."""
        self._running = True

        # Print startup banner
        self._print_banner()

        # Log system info
        from utils.system_utils import get_system_info
        info = get_system_info()
        logger.info(f"System: {info}")

        # Initialize speaker (always needed)
        self._init_speaker()

        # Determine mode
        voice_available = self._init_voice_pipeline()

        if voice_available:
            self._mode = "voice"
            await self._voice_loop()
        else:
            self._mode = "text"
            logger.info("Running in TEXT mode (voice unavailable).")
            await self._text_loop()

    async def stop(self) -> None:
        """Graceful shutdown."""
        self._running = False
        self._wake_event.set()  # Unblock any waiting coroutine

        if self._speaker:
            self._speaker.shutdown()
        if self._listener:
            self._listener.shutdown()
        if self._wake_word:
            self._wake_word.stop()

        logger.info("Wednesday stopped.")

    # ──────────────────────────────────────────────────────────
    # Initialization
    # ──────────────────────────────────────────────────────────

    def _init_speaker(self) -> None:
        """Initialize TTS speaker."""
        try:
            from voice.speaker import Speaker
            self._speaker = Speaker()
            logger.info("Speaker initialized ✓")
        except Exception as e:
            logger.warning(f"Speaker init failed: {e} — output will be text only.")

    def _init_voice_pipeline(self) -> bool:
        """
        Initialize mic listener, transcriber, and optional wake word.
        Returns True if voice pipeline is available.
        """
        # Check if PyAudio is available
        try:
            import pyaudio
        except ImportError:
            logger.warning(
                "PyAudio not installed — voice input disabled.\n"
                "  Install: pip install PyAudio\n"
                "  Windows: pip install PyAudio (may need PortAudio DLL)"
            )
            return False

        # Initialize microphone listener
        try:
            from voice.listener import MicListener
            self._listener = MicListener()
            # Auto-calibrate VAD threshold
            self._listener.auto_calibrate_threshold()
        except Exception as e:
            logger.warning(f"MicListener init failed: {e}")
            return False

        # Initialize Whisper transcriber
        try:
            from voice.transcriber import Transcriber
            self._transcriber = Transcriber()
        except Exception as e:
            logger.warning(f"Transcriber init failed: {e}")
            return False

        # Initialize wake word (optional)
        if settings.voice.enable_wake_word and settings.has_porcupine():
            try:
                from voice.wake_word import WakeWordDetector
                self._wake_word = WakeWordDetector(
                    on_wake_callback=self._on_wake_word_detected
                )
                if self._wake_word.start():
                    logger.info("Wake word detection active ✓")
                else:
                    self._wake_word = None
            except Exception as e:
                logger.warning(f"Wake word init failed: {e}")
                self._wake_word = None
        elif settings.voice.enable_wake_word:
            logger.warning(
                "Wake word enabled in config but PORCUPINE_ACCESS_KEY is missing.\n"
                "  Get free key: https://console.picovoice.ai/"
            )

        return True

    def _on_wake_word_detected(self) -> None:
        """
        Called from the wake word detector thread when trigger fires.
        We use an asyncio.Event to bridge between the thread and async loop.
        """
        logger.info("Wake word detected — activating...")
        # This runs in the wake word thread, so we use thread-safe scheduling
        asyncio.get_event_loop().call_soon_threadsafe(self._wake_event.set)

    # ──────────────────────────────────────────────────────────
    # Voice Loop
    # ──────────────────────────────────────────────────────────

    async def _voice_loop(self) -> None:
        """
        Main voice interaction loop.

        Two modes:
          1. With wake word: waits for "Hey Wednesday" then listens
          2. Without wake word: continuously listens (press-to-talk style isn't
             implemented here — it just always listens after greeting)
        """
        logger.info(f"Voice mode active.")

        # Greet user
        greeting = await self._get_greeting()
        await self._speak(greeting)
        print(f"\n{'─'*60}")

        if self._wake_word:
            print(f"  Listening for wake word — say 'Hey Wednesday' (or 'computer')")
            print(f"  Ctrl+C to exit")
            print(f"{'─'*60}\n")
            await self._wake_word_loop()
        else:
            print(f"  Listening continuously — just speak!")
            print(f"  Ctrl+C to exit | type 'text' to switch to text mode")
            print(f"{'─'*60}\n")
            await self._always_listening_loop()

    async def _wake_word_loop(self) -> None:
        """Wait for wake word → capture → process → repeat."""
        while self._running:
            # Wait for wake word event (set by _on_wake_word_detected)
            self._wake_event.clear()
            logger.debug("Waiting for wake word...")

            try:
                await asyncio.wait_for(
                    self._wake_event.wait(),
                    timeout=None  # Wait indefinitely
                )
            except asyncio.CancelledError:
                break

            if not self._running:
                break

            # Play activation sound / say "Yes?"
            await self._speak("Yes?", skip_memory=True)

            # Capture utterance
            wav_bytes = await self._capture_speech()
            if not wav_bytes:
                await self._speak("I didn't catch that. Say my name again when you're ready.", skip_memory=True)
                continue

            # Transcribe and process
            await self._handle_audio(wav_bytes)

    async def _always_listening_loop(self) -> None:
        """
        Continuously capture speech without wake word.
        After each response, immediately listen again.
        """
        while self._running:
            # Small delay between captures to avoid feedback
            await asyncio.sleep(0.3)

            print("🎙️  Listening...", flush=True)
            wav_bytes = await self._capture_speech(timeout=8.0)

            if not wav_bytes:
                continue  # No speech detected — just listen again

            await self._handle_audio(wav_bytes)

    async def _capture_speech(self, timeout: float = 8.0) -> Optional[bytes]:
        """Run mic capture in executor (blocking I/O → runs in thread pool)."""
        self._state = "LISTENING"
        try:
            wav_bytes = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._listener.capture_utterance(
                    timeout=timeout,
                    on_speech_start=self._on_speech_start,
                    on_speech_end=self._on_speech_end,
                )
            )
            return wav_bytes
        except Exception as e:
            logger.error(f"Speech capture error: {e}")
            return None
        finally:
            self._state = "IDLE"

    async def _handle_audio(self, wav_bytes: bytes) -> None:
        """Transcribe audio and process the resulting text."""
        self._state = "THINKING"

        # Transcribe in thread pool (CPU-bound)
        text = await asyncio.get_event_loop().run_in_executor(
            None, self._transcriber.transcribe, wav_bytes
        )

        if not text:
            logger.debug("Empty transcription — skipping.")
            self._state = "IDLE"
            return

        print(f"You: {text}")
        response = await self.process_input(text)
        await self._speak(response)

    # ──────────────────────────────────────────────────────────
    # Text Loop (fallback when no mic)
    # ──────────────────────────────────────────────────────────

    async def _text_loop(self) -> None:
        """Terminal REPL for testing without microphone."""
        greeting = await self._get_greeting()
        print(f"\nWednesday: {greeting}\n")
        self.memory.add_assistant(greeting)

        print("Commands: /memory | /clear | /stats | /switch openai|claude | quit\n")

        while self._running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("You: ").strip()
                )
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "bye", "goodbye"):
                farewell = await self._get_farewell()
                print(f"Wednesday: {farewell}")
                self._running = False
                break

            response = await self.process_input(user_input)
            print(f"\nWednesday: {response}\n")

            # Also speak in text mode if speaker is available
            if self._speaker and not self._muted:
                await self._speaker.say(response)

    # ──────────────────────────────────────────────────────────
    # Core processing pipeline
    # ──────────────────────────────────────────────────────────

    async def process_input(self, user_input: str) -> str:
        """
        THE MAIN PIPELINE — processes any input (voice or text).

        1. Store in memory
        2. Classify intent
        3. Handle meta commands
        4. Route to agent (Phase 4+) or answer directly
        5. Clean response
        6. Store response in memory
        7. Return

        Args:
            user_input: Transcribed speech or typed text

        Returns:
            Clean response string ready for voice output.
        """
        if not user_input.strip():
            return ""

        logger.info(f"Processing: '{user_input}'")
        self._state = "THINKING"
        t0 = time.monotonic()

        # ── 1. Store in short-term memory ────────────────────
        self.memory.add_user(user_input)

        # ── 2. Classify intent ────────────────────────────────
        intent = self.classifier.classify(user_input)

        # ── 3. Handle meta commands ────────────────────────────
        if intent.category == "META":
            result = self._handle_meta(intent)
            self._state = "IDLE"
            return result

        # ── 4. Route to agent or converse ────────────────────
        if intent.category == "CONVERSATION":
            response_raw = await self._converse(user_input)
        else:
            # Phase 4+: route to agent
            # For now, handle with LLM + note the intent
            response_raw = await self._handle_with_intent(user_input, intent)

        # ── 5. Clean for voice ────────────────────────────────
        response = self.builder.clean_for_voice(response_raw)

        # ── 6. Store in memory ────────────────────────────────
        self.memory.add_assistant(response)

        elapsed = time.monotonic() - t0
        logger.info(f"Pipeline complete: {elapsed:.2f}s")
        self._state = "IDLE"
        return response

    async def _converse(self, user_input: str) -> str:
        """Standard conversation — build messages with history and call LLM."""
        messages = self.memory.get_messages()
        # Phase 3: inject long-term memories here
        return await self.llm.chat(messages=messages)

    async def _handle_with_intent(self, user_input: str, intent: Intent) -> str:
        """
        Handle non-conversation intents.
        Phase 1: Let LLM handle everything but acknowledge the intent.
        Phase 4+: Route to specific agent handlers.
        """
        # Build a context-aware prompt for the LLM
        # Include intent info so LLM responds appropriately
        context_system = (
            f"{settings.persona}\n\n"
            f"The user's request appears to be a {intent.category} command "
            f"(action: {intent.action}). "
            f"In your current Phase 1 state, you cannot execute system commands yet, "
            f"but acknowledge you understand and explain what you'll be able to do soon. "
            f"Be honest and helpful."
        )

        messages = self.memory.get_messages()
        return await self.llm.chat(messages=messages, system_prompt=context_system)

    def _handle_meta(self, intent: Intent) -> str:
        """Handle internal meta commands (/memory, /clear, /stats)."""
        action = intent.action

        if action == "show_memory":
            dump = self.memory.summary_str()
            print(f"\n[Short-term Memory — {len(self.memory)} messages]\n{dump}\n")
            return f"I have {len(self.memory)} messages in my active memory."

        if action == "clear_memory":
            self.memory.clear()
            return "Memory cleared. Starting fresh."

        if action == "show_stats":
            stats = self.llm.get_stats()
            return (
                f"Stats: {stats['total_calls']} LLM calls, "
                f"approximately {stats['total_tokens']} tokens used, "
                f"running on {stats['provider']}."
            )

        return "Unknown meta command."

    # ──────────────────────────────────────────────────────────
    # Speech helpers
    # ──────────────────────────────────────────────────────────

    async def _speak(self, text: str, skip_memory: bool = False) -> None:
        """
        Speak and optionally print the response.
        skip_memory=True for system phrases (greetings, etc.)
        """
        if text:
            print(f"Wednesday: {text}", flush=True)
            if self._speaker and not self._muted:
                await self._speaker.say(text)
            if not skip_memory:
                self.memory.add_assistant(text)

    def _on_speech_start(self) -> None:
        """Called when VAD detects speech starting."""
        print("  [Speaking...]", flush=True)
        # Stop TTS if Wednesday is currently speaking (interruption handling)
        if self._speaker and self._speaker.is_speaking:
            self._speaker.stop()

    def _on_speech_end(self) -> None:
        """Called when VAD detects end of speech."""
        print("  [Processing...]", flush=True)

    # ──────────────────────────────────────────────────────────
    # LLM convenience calls
    # ──────────────────────────────────────────────────────────

    async def _get_greeting(self) -> str:
        prompt = (
            f"Greet the user as Wednesday. It is the start of a new session. "
            f"Be warm, brief (1-2 sentences), and mention you're ready to help. "
            f"Address them as {settings.user_name}."
        )
        text = await self.llm.chat([{"role": "user", "content": prompt}])
        return self.builder.clean_for_voice(text)

    async def _get_farewell(self) -> str:
        text = await self.llm.chat([{
            "role": "user",
            "content": "Say a brief, warm goodbye as Wednesday. 1 sentence."
        }])
        return self.builder.clean_for_voice(text)

    # ──────────────────────────────────────────────────────────
    # Public controls (used by tray, future UI)
    # ──────────────────────────────────────────────────────────

    def mute(self) -> None:
        self._muted = True
        if self._speaker:
            self._speaker.stop()
        logger.info("Wednesday muted.")

    def unmute(self) -> None:
        self._muted = False
        logger.info("Wednesday unmuted.")

    def clear_memory(self) -> None:
        self.memory.clear()

    @property
    def state(self) -> str:
        return self._state

    # ──────────────────────────────────────────────────────────
    # Startup banner
    # ──────────────────────────────────────────────────────────

    def _print_banner(self) -> None:
        banner = f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    W E D N E S D A Y   —   AI Desktop Assistant          ║
║                                                          ║
║    LLM:    {settings.llm.provider:<10}  Model: {settings.llm.openai_model if settings.llm.provider == "openai" else settings.llm.claude_model:<20}║
║    TTS:    {settings.voice.tts_engine:<10}  STT:   {settings.voice.whisper_model:<20}║
║    Wake:   {"enabled" if settings.voice.enable_wake_word else "disabled":<10}                                   ║
║                                                          ║
║    Type 'quit' to exit | Ctrl+C to interrupt             ║
╚══════════════════════════════════════════════════════════╝
"""
        print(banner)
