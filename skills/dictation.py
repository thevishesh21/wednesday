"""
Wednesday - Dictation Skill
Types user speech into the active window using pyautogui.
"""

import logging
import time

logger = logging.getLogger("Wednesday")


def type_text(text: str) -> str:
    """Type the given text into the currently active window."""
    if not text:
        return "Nothing to type."

    try:
        import pyautogui
        time.sleep(0.3)  # brief pause to ensure the target window is focused
        pyautogui.typewrite(text, interval=0.02)
        return f"Typed: {text}"
    except ImportError:
        # Fallback: use pyperclip + keyboard paste
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-command", f"Set-Clipboard -Value '{text}'"],
                capture_output=True, timeout=5,
            )
            import ctypes
            VK_CONTROL = 0x11
            VK_V = 0x56
            KEYEVENTF_KEYUP = 0x2
            user32 = ctypes.windll.user32
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_V, 0, 0, 0)
            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            return f"Typed: {text}"
        except Exception as e:
            return f"Failed to type text: {e}"
    except Exception as e:
        return f"Failed to type text: {e}"
