"""
Wednesday AI Assistant — App Launcher Tool
Opens desktop applications on Windows.
Detects website names and redirects to browser automatically.
"""

import subprocess
import os
import shutil
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

# ── Names that are websites, NOT desktop apps ───────────────────
# If the user says "open youtube", they mean the website, not an .exe
_WEBSITE_NAMES = {
    "youtube", "google", "gmail", "github", "stackoverflow",
    "stack overflow", "chatgpt", "twitter", "x", "instagram",
    "facebook", "linkedin", "reddit", "whatsapp web", "netflix",
    "amazon", "flipkart", "wikipedia", "spotify web",
}

# ── Common filler words to strip ────────────────────────────────
_FILLER_WORDS = {"the", "a", "an", "my", "please", "now", "up"}


def _clean_name(name: str) -> str:
    """Strip filler words from app name. 'the notepad' → 'notepad'."""
    words = name.lower().strip().split()
    cleaned = [w for w in words if w not in _FILLER_WORDS]
    return " ".join(cleaned) if cleaned else name.lower().strip()


def open_app(name: str) -> str:
    """
    Open an application by name.
    If the name is a known website, opens it in the browser instead.

    Args:
        name: App name (case-insensitive, matched against known apps)

    Returns:
        Status message string (contains 'FAILED' on error for executor)
    """
    name_lower = _clean_name(name)
    log.info(f"Opening app: {name_lower}")

    # ── Redirect websites to browser ─────────────────────────
    if name_lower in _WEBSITE_NAMES:
        log.info(f"'{name_lower}' is a website — redirecting to browser.")
        from tools.browser import open_website
        return open_website(name_lower)

    # ── Check known apps ─────────────────────────────────────
    executable = _APP_MAP.get(name_lower)

    if executable:
        return _launch(executable, name_lower)

    # ── Try to find the executable on PATH ────────────────────
    # Only attempt if it looks like a real app name (not a sentence)
    if len(name_lower.split()) <= 2:
        # Check if the exe actually exists on the system
        exe_name = name_lower.replace(" ", "") + ".exe"
        if shutil.which(exe_name) or shutil.which(name_lower):
            return _launch(exe_name if shutil.which(exe_name) else name_lower,
                           name_lower)

    # ── Nothing found ─────────────────────────────────────────
    log.warning(f"App not found: '{name_lower}'")
    return f"FAILED: Sorry boss, '{name}' nahi mila system mein."


def _launch(executable: str, display_name: str) -> str:
    """Launch an executable and validate it actually started."""
    try:
        # URI-style launches (ms-settings:, whatsapp:, etc.)
        if ":" in executable and not executable.endswith(".exe"):
            os.startfile(executable)
            log.info(f"Launched URI: {executable}")
            return f"{display_name} opened successfully!"

        # Normal executable — use subprocess and check it starts
        proc = subprocess.Popen(executable, shell=True,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE)
        # Give it a moment to fail
        try:
            proc.wait(timeout=2)
            # If it exited quickly with error code, it probably failed
            if proc.returncode and proc.returncode != 0:
                stderr = proc.stderr.read().decode(errors="ignore").strip()
                log.error(f"App exited with code {proc.returncode}: {stderr}")
                return f"FAILED: Could not open {display_name}."
        except subprocess.TimeoutExpired:
            # Still running after 2s = good, it launched successfully
            pass

        log.info(f"Launched: {executable}")
        return f"{display_name} opened successfully!"

    except FileNotFoundError:
        log.error(f"App not found: {executable}")
        return f"FAILED: '{display_name}' not found on this system."
    except Exception as e:
        log.error(f"Failed to open {display_name}: {e}")
        return f"FAILED: Error opening {display_name}: {e}"


def close_app(name: str) -> str:
    """
    Close an application by process name.

    Args:
        name: App name to close
    """
    name_lower = _clean_name(name)
    executable = _APP_MAP.get(name_lower, name_lower)

    # Remove path, keep just filename
    if "\\" in executable or "/" in executable:
        executable = os.path.basename(executable)

    try:
        result = subprocess.run(["taskkill", "/f", "/im", executable],
                                capture_output=True, text=True)
        if result.returncode == 0:
            log.info(f"Closed: {executable}")
            return f"{name} closed!"
        else:
            log.warning(f"Could not close {executable}: {result.stderr}")
            return f"FAILED: {name} is not running or couldn't be closed."
    except Exception as e:
        log.error(f"Error closing {name}: {e}")
        return f"FAILED: Error closing {name}: {e}"
