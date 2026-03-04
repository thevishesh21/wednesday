"""
Wednesday - App Control Skill
Opens Windows applications by name.
"""

import os
import subprocess


# Common app name -> executable or command mapping for Windows
APP_MAP = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "file explorer": "explorer",
    "explorer": "explorer",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings": "ms-settings:",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "windows terminal": "wt",
    "powershell": "powershell",
    "spotify": "spotify",
    "discord": "discord",
    "steam": "steam",
    "vscode": "code",
    "visual studio code": "code",
    "vs code": "code",
    "snipping tool": "snippingtool",
}


def open_app(app_name: str) -> str:
    """Open an application by name."""
    if not app_name:
        return "Please tell me which application to open."

    normalized = app_name.lower().strip()

    # Check our mapping first
    if normalized in APP_MAP:
        target = APP_MAP[normalized]
        try:
            if target.startswith("ms-settings"):
                os.startfile(target)
            else:
                subprocess.Popen(target, shell=True)
            return f"Opening {app_name}."
        except Exception as e:
            return f"Failed to open {app_name}: {e}"

    # If not in map, try to launch directly via shell
    try:
        os.startfile(normalized)
        return f"Opening {app_name}."
    except OSError:
        pass

    # Try Start Menu search via shell
    try:
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        return f"Trying to open {app_name}."
    except Exception as e:
        return f"Sorry, I could not find or open {app_name}."
