"""
Wednesday AI Assistant — App Launcher Tool
Opens desktop applications on Windows.
"""

import subprocess
import os
from utils.logger import get_logger

log = get_logger("app_launcher")

# ── Known app mappings (name → executable / command) ────────────
_APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "chrome": "chrome.exe",
    "brave": "brave.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "vs code": "code",
    "vscode": "code",
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "telegram": "telegram.exe",
    "whatsapp": "whatsapp:",
    "snipping tool": "snippingtool.exe",
    "screen snip": "ms-screenclip:",
}


def open_app(name: str) -> str:
    """
    Open an application by name.

    Args:
        name: App name (case-insensitive, matched against known apps)

    Returns:
        Status message string
    """
    name_lower = name.lower().strip()
    log.info(f"Opening app: {name_lower}")

    # ── Check known apps ─────────────────────────────────────
    executable = _APP_MAP.get(name_lower)

    if executable:
        try:
            # URI-style launches (ms-settings:, whatsapp:, etc.)
            if ":" in executable and not executable.endswith(".exe"):
                os.startfile(executable)
            else:
                subprocess.Popen(executable, shell=True)
            log.info(f"Launched: {executable}")
            return f"{name} opened successfully!"
        except FileNotFoundError:
            log.error(f"App not found: {executable}")
            return f"Sorry, {name} not found on this system."
        except Exception as e:
            log.error(f"Failed to open {name}: {e}")
            return f"Error opening {name}: {e}"

    # ── Try direct launch (user might say exact exe name) ────
    try:
        subprocess.Popen(name_lower, shell=True)
        log.info(f"Direct launch: {name_lower}")
        return f"{name} opened!"
    except Exception as e:
        log.error(f"Could not open '{name}': {e}")
        return f"Sorry boss, '{name}' nahi mila system mein."


def close_app(name: str) -> str:
    """
    Close an application by process name.

    Args:
        name: App name to close
    """
    name_lower = name.lower().strip()
    executable = _APP_MAP.get(name_lower, name_lower)

    # Remove path, keep just filename
    if "\\" in executable or "/" in executable:
        executable = os.path.basename(executable)

    try:
        subprocess.run(["taskkill", "/f", "/im", executable],
                       capture_output=True, check=True)
        log.info(f"Closed: {executable}")
        return f"{name} closed!"
    except subprocess.CalledProcessError:
        log.warning(f"Could not close {executable} — may not be running.")
        return f"{name} is not running or couldn't be closed."
    except Exception as e:
        log.error(f"Error closing {name}: {e}")
        return f"Error closing {name}: {e}"
