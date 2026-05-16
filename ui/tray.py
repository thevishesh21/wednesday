"""
ui/tray.py
-----------
Windows system tray icon for Wednesday.

Shows Wednesday's status and provides a right-click menu.
Runs in its own thread (does not block the async event loop).

Right-click menu:
  ● Wednesday — Online
  ─────────────────
  Mute / Unmute
  Clear Memory
  Switch to Claude / OpenAI
  ─────────────────
  Debug: Show Logs
  ─────────────────
  Quit

Requires: pip install pystray Pillow
"""

import sys
import threading
import subprocess
from pathlib import Path
from utils.logger import setup_logger
from config.settings import settings, ASSETS_DIR

logger = setup_logger(__name__)


class TrayApp:
    """
    System tray manager — call run() in a daemon thread.

    Communicates with Orchestrator via a shared reference.
    Set tray.orchestrator = orchestrator after both are initialized.
    """

    def __init__(self):
        self._icon = None
        self._orchestrator = None  # Set externally after creation
        self._muted = False

    @property
    def orchestrator(self):
        return self._orchestrator

    @orchestrator.setter
    def orchestrator(self, orch):
        self._orchestrator = orch

    def run(self) -> None:
        """Start the tray icon. Blocks until icon.stop() is called."""
        try:
            import pystray
            from PIL import Image
        except ImportError:
            logger.warning(
                "pystray or Pillow not installed. Tray disabled.\n"
                "  Fix: pip install pystray Pillow"
            )
            return

        icon_image = self._get_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem(
                f"Wednesday  ●  Online",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Mute / Unmute", self._toggle_mute),
            pystray.MenuItem("Clear Memory", self._clear_memory),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Switch to Claude",
                lambda icon, item: self._switch_llm("claude"),
            ),
            pystray.MenuItem(
                "Switch to OpenAI",
                lambda icon, item: self._switch_llm("openai"),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Logs", self._open_logs),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit Wednesday", self._quit),
        )

        self._icon = pystray.Icon(
            name="Wednesday",
            icon=icon_image,
            title="Wednesday — AI Assistant",
            menu=menu,
        )

        logger.info("System tray started.")
        try:
            self._icon.run()
        except Exception as e:
            logger.error(f"Tray error: {e}")

    # ── Icon ──────────────────────────────────────────────────

    def _get_icon_image(self):
        """Load icon from file or generate a placeholder."""
        from PIL import Image, ImageDraw, ImageFont

        icon_path = Path(settings.ui.tray_icon_path)
        if icon_path.exists():
            try:
                return Image.open(icon_path).resize((64, 64)).convert("RGBA")
            except Exception:
                pass

        # Generate a purple 'W' icon
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Background circle
        draw.ellipse([2, 2, 62, 62], fill=(30, 10, 60, 255))
        # Border
        draw.ellipse([2, 2, 62, 62], outline=(138, 43, 226, 255), width=2)
        # Letter W
        draw.text((18, 20), "W", fill=(200, 180, 255, 255))

        # Save for future use
        icon_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            img.save(str(icon_path))
        except Exception:
            pass

        return img

    # ── Menu actions ──────────────────────────────────────────

    def _toggle_mute(self, icon, item) -> None:
        self._muted = not self._muted
        if self._orchestrator:
            if self._muted:
                self._orchestrator.mute()
            else:
                self._orchestrator.unmute()
        status = "muted" if self._muted else "unmuted"
        logger.info(f"Wednesday {status} via tray.")

    def _clear_memory(self, icon, item) -> None:
        if self._orchestrator:
            self._orchestrator.clear_memory()
            logger.info("Memory cleared via tray.")

    def _switch_llm(self, provider: str) -> None:
        if self._orchestrator:
            self._orchestrator.llm.switch_provider(provider)
            logger.info(f"Switched to {provider} via tray.")

    def _open_logs(self, icon, item) -> None:
        """Open the log file in Notepad."""
        log_file = Path(settings.log.log_dir) / "wednesday.log"
        if log_file.exists():
            try:
                subprocess.Popen(["notepad.exe", str(log_file)])
            except Exception as e:
                logger.error(f"Could not open log: {e}")
        else:
            logger.warning("No log file found yet.")

    def _quit(self, icon, item) -> None:
        logger.info("Quit requested via tray.")
        icon.stop()
        sys.exit(0)

    def stop(self) -> None:
        """Programmatically stop the tray icon."""
        if self._icon:
            self._icon.stop()
