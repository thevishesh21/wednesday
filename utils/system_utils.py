"""
utils/system_utils.py
----------------------
Windows-specific system utilities for Wednesday.

Provides:
  - Windows startup registration (run on boot)
  - Process management helpers
  - System info retrieval
"""

import os
import sys
import subprocess
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

IS_WINDOWS = sys.platform == "win32"


def register_startup(app_name: str = "Wednesday") -> bool:
    """
    Register Wednesday to auto-start on Windows login via the Registry.

    MANUAL STEP: This requires running as Administrator OR
    the current user's HKCU registry (no admin needed).

    Returns True on success, False on failure.
    """
    if not IS_WINDOWS:
        logger.warning("Startup registration only supported on Windows.")
        return False

    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        exe_path = sys.executable  # python.exe in venv
        script_path = str(Path(__file__).parent.parent / "main.py")
        command = f'"{exe_path}" "{script_path}"'

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path,
            0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)

        logger.info(f"Startup registered: {command}")
        return True
    except ImportError:
        logger.warning("winreg not available (not on Windows).")
        return False
    except Exception as e:
        logger.error(f"Failed to register startup: {e}")
        return False


def unregister_startup(app_name: str = "Wednesday") -> bool:
    """Remove Wednesday from Windows startup registry."""
    if not IS_WINDOWS:
        return False
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path,
            0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, app_name)
        logger.info(f"Startup unregistered: {app_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to unregister startup: {e}")
        return False


def get_system_info() -> dict:
    """Return basic system information for logging/debugging."""
    import platform
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        freq_str = f"{cpu_freq.max/1000:.1f}GHz" if cpu_freq else "unknown"
    except ImportError:
        ram_gb = "unknown"
        cpu_count = os.cpu_count()
        freq_str = "unknown"

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python": platform.python_version(),
        "cpu": f"{cpu_count} cores @ {freq_str}",
        "ram": f"{ram_gb}GB",
        "machine": platform.machine(),
    }


def open_application(app_name_or_path: str) -> bool:
    """
    Open an application by name or full path on Windows.
    Phase 2 will expand this with more robust app detection.
    """
    try:
        if IS_WINDOWS:
            os.startfile(app_name_or_path)
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open",
                              app_name_or_path])
        logger.info(f"Opened: {app_name_or_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to open '{app_name_or_path}': {e}")
        return False
