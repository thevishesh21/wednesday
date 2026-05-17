"""
control/apps.py
----------------
Open, close, focus, and manage Windows applications.

Wednesday uses this to execute commands like:
  "Open Chrome"
  "Close Notepad"
  "Open File Explorer"
  "Launch Spotify"
"""

import os
import subprocess
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Common app name aliases → executable or launch command
APP_MAP = {
    # Browsers
    "chrome":          "chrome.exe",
    "google chrome":   "chrome.exe",
    "firefox":         "firefox.exe",
    "edge":            "msedge.exe",
    "microsoft edge":  "msedge.exe",
    "brave":           "brave.exe",

    # Microsoft Office
    "word":            "winword.exe",
    "excel":           "excel.exe",
    "powerpoint":      "powerpnt.exe",
    "outlook":         "outlook.exe",
    "teams":           "teams.exe",

    # Windows built-in
    "notepad":         "notepad.exe",
    "calculator":      "calc.exe",
    "paint":           "mspaint.exe",
    "explorer":        "explorer.exe",
    "file explorer":   "explorer.exe",
    "task manager":    "taskmgr.exe",
    "control panel":   "control.exe",
    "settings":        "ms-settings:",
    "cmd":             "cmd.exe",
    "command prompt":  "cmd.exe",
    "powershell":      "powershell.exe",
    "terminal":        "wt.exe",

    # Media
    "spotify":         "spotify.exe",
    "vlc":             "vlc.exe",
    "photos":          "ms-photos:",

    # Dev tools
    "vscode":          "code",
    "vs code":         "code",
    "visual studio code": "code",
    "github":          "https://github.com",

    # Communication
    "whatsapp":        "WhatsApp.exe",
    "discord":         "discord.exe",
    "zoom":            "zoom.exe",

    # Utilities
    "snipping tool":   "SnippingTool.exe",
    "sticky notes":    "stikynot.exe",
    "clock":           "ms-clock:",
}


class AppController:
    """
    Controls Windows applications — open, close, focus.
    """

    def open(self, app_name: str) -> tuple[bool, str]:
        """
        Open an application by name.

        Returns:
            (success: bool, message: str)
        """
        name = app_name.lower().strip()
        exe  = APP_MAP.get(name, app_name)

        logger.info(f"Opening app: '{app_name}' → '{exe}'")

        # Handle ms- protocol URIs (Windows Settings, Photos, etc.)
        if exe.startswith("ms-") or exe.startswith("http"):
            return self._open_uri(exe, app_name)

        # Try subprocess
        try:
            subprocess.Popen(
                exe,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if os.name == "nt" else 0,
            )
            time.sleep(0.5)
            return True, f"Opening {app_name}."
        except FileNotFoundError:
            return self._try_start(exe, app_name)
        except Exception as e:
            logger.error(f"Failed to open '{app_name}': {e}")
            return False, f"I couldn't open {app_name}. It may not be installed."

    def _open_uri(self, uri: str, label: str) -> tuple[bool, str]:
        """Open a URI via Windows shell (ms- protocols, URLs)."""
        try:
            os.startfile(uri)
            return True, f"Opening {label}."
        except Exception as e:
            logger.error(f"URI open failed: {e}")
            return False, f"Couldn't open {label}."

    def _try_start(self, exe: str, label: str) -> tuple[bool, str]:
        """Try os.startfile as fallback."""
        try:
            os.startfile(exe)
            return True, f"Opening {label}."
        except Exception as e:
            logger.error(f"startfile fallback failed: {e}")
            return False, f"I couldn't find {label} on your system."

    def close(self, app_name: str) -> tuple[bool, str]:
        """
        Close an application by name using taskkill.
        """
        name = app_name.lower().strip()
        exe  = APP_MAP.get(name, app_name)

        # Ensure .exe suffix
        if not exe.endswith(".exe"):
            exe = exe + ".exe"

        logger.info(f"Closing: {exe}")
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", exe],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return True, f"Closed {app_name}."
            else:
                return False, f"{app_name} doesn't appear to be running."
        except Exception as e:
            logger.error(f"Close failed: {e}")
            return False, f"Couldn't close {app_name}."

    def focus(self, app_name: str) -> tuple[bool, str]:
        """Bring a running application window to the foreground."""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(app_name)
            if windows:
                win = windows[0]
                win.activate()
                return True, f"Switched to {app_name}."
            return False, f"No window found for {app_name}."
        except ImportError:
            logger.warning("pygetwindow not installed.")
            return False, "Window focus not available."
        except Exception as e:
            logger.error(f"Focus failed: {e}")
            return False, f"Couldn't focus {app_name}."

    def is_running(self, app_name: str) -> bool:
        """Check if an application process is currently running."""
        name = app_name.lower().strip()
        exe  = APP_MAP.get(name, app_name)
        if not exe.endswith(".exe"):
            exe += ".exe"
        try:
            import psutil
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] and proc.info["name"].lower() == exe.lower():
                    return True
            return False
        except ImportError:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {exe}"],
                capture_output=True, text=True,
            )
            return exe.lower() in result.stdout.lower()

    def list_running(self) -> list[str]:
        """Return list of currently running application names."""
        try:
            import psutil
            names = set()
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"]:
                    names.add(proc.info["name"])
            return sorted(names)
        except ImportError:
            return []
