"""
Wednesday — AI Desktop Assistant
=================================
Entry point.

Run:
    python main.py              # Auto-detect voice or text mode
    python main.py --text       # Force text mode (no mic needed)
    python main.py --debug      # Verbose logging
    python main.py --devices    # List audio devices
    python main.py --calibrate  # Mic calibration tool
"""

import asyncio
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args():
    parser = argparse.ArgumentParser(description="Wednesday AI Assistant")
    parser.add_argument("--text",      action="store_true", help="Force text-only mode")
    parser.add_argument("--debug",     action="store_true", help="Enable debug logging")
    parser.add_argument("--calibrate", action="store_true", help="Run mic calibration")
    parser.add_argument("--devices",   action="store_true", help="List audio devices")
    parser.add_argument("--no-tray",   action="store_true", help="Disable system tray")
    return parser.parse_args()


def apply_args(args) -> None:
    from config.settings import settings
    if args.debug:
        settings.log.level = "DEBUG"
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    if args.no_tray:
        settings.ui.enable_tray = False


async def main(args) -> None:
    from utils.logger import setup_logger
    from config.settings import settings
    from core.orchestrator import Orchestrator

    logger = setup_logger("main")

    # ── Utility flags ───────────────────────────────────────
    if args.devices:
        from utils.audio_utils import list_audio_devices
        list_audio_devices()
        return

    if args.calibrate:
        from voice.listener import MicListener
        print("Calibrating microphone — please be quiet for 3 seconds...")
        listener = MicListener()
        ambient = listener.get_ambient_noise_level(3.0)
        print(f"\n  Ambient noise level:      {ambient:.4f} RMS")
        print(f"  Recommended threshold:    {ambient * 2.5:.4f} RMS")
        print(f"  Current config threshold: {settings.voice.vad_silence_threshold}")
        listener.shutdown()
        return

    # ── Validate at least one LLM is configured ─────────────
    if not settings.has_any_llm():
        print("\n" + "═" * 62)
        print("  ⚠️  No AI provider configured!")
        print()
        print("  You need ONE of these free options in your .env file:")
        print()
        print("  OPTION 1 — Groq (fastest, recommended):")
        print("    → https://console.groq.com  (free signup)")
        print("    → Add to .env:  GROQ_API_KEY=gsk_...")
        print("    → Set in config.yaml:  llm.provider: groq")
        print()
        print("  OPTION 2 — Google Gemini (1M tokens/day free):")
        print("    → https://aistudio.google.com/app/apikey")
        print("    → Add to .env:  GEMINI_API_KEY=AIza...")
        print("    → Set in config.yaml:  llm.provider: gemini")
        print()
        print("  OPTION 3 — Ollama (100% local, no internet):")
        print("    → https://ollama.com/download  (install the app)")
        print("    → Run:  ollama pull llama3")
        print("    → Set in config.yaml:  llm.provider: ollama")
        print("═" * 62 + "\n")
        sys.exit(1)

    # ── Log which provider is active ────────────────────────
    provider = settings.llm.provider
    logger.info(f"Using LLM provider: {provider}")

    if provider == "groq":
        logger.info(f"Groq model: {settings.llm.groq_model}")
    elif provider == "gemini":
        logger.info(f"Gemini model: {settings.llm.gemini_model}")
    elif provider == "ollama":
        logger.info(f"Ollama model: {settings.llm.ollama_model} @ {settings.llm.ollama_base_url}")

    # ── System tray ─────────────────────────────────────────
    tray = None
    if settings.ui.enable_tray:
        import threading
        from ui.tray import TrayApp
        tray = TrayApp()
        tray_thread = threading.Thread(target=tray.run, name="SystemTray", daemon=True)
        tray_thread.start()

    # ── Main orchestrator ────────────────────────────────────
    orchestrator = Orchestrator()
    if tray:
        tray.orchestrator = orchestrator

    # ── Force text mode if requested ────────────────────────
    if args.text:
        async def _text_only():
            orchestrator._running = True
            orchestrator._print_banner()
            orchestrator._init_speaker()
            await orchestrator._text_loop()
        orchestrator.start = _text_only

    # ── Run ─────────────────────────────────────────────────
    try:
        logger.info("Wednesday starting...")
        await orchestrator.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        await orchestrator.stop()
        logger.info("Wednesday stopped cleanly.")


def run():
    args = parse_args()
    apply_args(args)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(args))


if __name__ == "__main__":
    run()