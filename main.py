"""
Wednesday — Phase 2
====================
Voice assistant with desktop + browser control.

Run:
    python main.py           # Auto voice/text
    python main.py --text    # Text only (no mic)
    python main.py --debug   # Verbose logs
    python main.py --devices # List audio devices
"""

import asyncio
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(description="Wednesday AI Assistant — Phase 2")
    p.add_argument("--text",    action="store_true", help="Text mode (no mic)")
    p.add_argument("--debug",   action="store_true", help="Debug logging")
    p.add_argument("--devices", action="store_true", help="List audio devices")
    p.add_argument("--no-tray", action="store_true", help="Disable system tray")
    return p.parse_args()


async def main(args):
    from utils.logger    import setup_logger
    from config.settings import settings

    logger = setup_logger("main")

    if args.debug:
        settings.log.level = "DEBUG"
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    if args.devices:
        from utils.audio_utils import list_audio_devices
        list_audio_devices()
        return

    # Validate API key
    if not settings.has_any_llm():
        print("\n" + "="*60)
        print("  No AI provider configured!")
        print()
        print("  FREE OPTIONS — add ONE to your .env file:")
        print()
        print("  Groq (fastest, recommended):")
        print("    GROQ_API_KEY=gsk_...")
        print("    Get key: https://console.groq.com")
        print()
        print("  Google Gemini:")
        print("    GEMINI_API_KEY=AIza...")
        print("    Get key: https://aistudio.google.com/app/apikey")
        print()
        print("  Ollama (local, no internet):")
        print("    Install: https://ollama.com/download")
        print("    Run: ollama pull llama3")
        print("    Set config.yaml: llm.provider: ollama")
        print("="*60 + "\n")
        sys.exit(1)

    logger.info(f"Provider: {settings.llm.provider}")

    # System tray
    tray = None
    if settings.ui.enable_tray and not args.no_tray:
        import threading
        from ui.tray import TrayApp
        tray = TrayApp()
        t = threading.Thread(target=tray.run, name="Tray", daemon=True)
        t.start()

    # Orchestrator
    from core.orchestrator import Orchestrator
    orch = Orchestrator()
    if tray:
        tray.orchestrator = orch

    # Force text mode
    if args.text:
        async def _text_only():
            orch._running = True
            orch._print_banner()
            orch._init_speaker()
            orch._init_system_agent()
            await orch._text_loop()
        orch.start = _text_only

    try:
        await orch.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.exception(f"Fatal: {e}")
    finally:
        await orch.stop()


def run():
    args = parse_args()
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args))


if __name__ == "__main__":
    run()
