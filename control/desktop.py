"""
control/desktop.py
-------------------
Full desktop automation — keyboard, mouse, typing, hotkeys.

Wednesday uses this to execute commands like:
  "Type hello world"
  "Press Ctrl+C"
  "Take a screenshot"
  "Scroll down"
  "Click the center of the screen"
"""

import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Screenshot save location
SCREENSHOT_DIR = Path(__file__).parent.parent / "data" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


class DesktopController:
    """
    Controls keyboard, mouse, and screen using pyautogui.
    All methods return (success, message) tuples.
    """

    def __init__(self):
        try:
            import pyautogui
            # Safety: move mouse to corner to abort if needed
            pyautogui.FAILSAFE = True
            # Small pause between actions to be reliable
            pyautogui.PAUSE = 0.05
            self._pg = pyautogui
            logger.info("DesktopController ready ✓")
        except ImportError:
            logger.error("pyautogui not installed. Run: pip install pyautogui")
            self._pg = None

    # ── Typing ────────────────────────────────────────────────

    def type_text(self, text: str, interval: float = 0.03) -> tuple[bool, str]:
        """Type text at the current cursor position."""
        if not self._pg:
            return False, "Desktop control not available."
        try:
            self._pg.write(text, interval=interval)
            logger.info(f"Typed: '{text[:40]}'")
            return True, f"Typed: {text[:40]}"
        except Exception as e:
            logger.error(f"Type error: {e}")
            return False, "Failed to type text."

    def type_and_enter(self, text: str) -> tuple[bool, str]:
        """Type text and press Enter."""
        ok, msg = self.type_text(text)
        if ok:
            self._pg.press("enter")
        return ok, msg

    # ── Keyboard shortcuts ────────────────────────────────────

    def hotkey(self, *keys: str) -> tuple[bool, str]:
        """
        Press a keyboard shortcut.
        Usage: hotkey('ctrl', 'c')  → Ctrl+C
               hotkey('ctrl', 'alt', 'delete')
        """
        if not self._pg:
            return False, "Desktop control not available."
        try:
            self._pg.hotkey(*keys)
            combo = "+".join(keys)
            logger.info(f"Hotkey: {combo}")
            return True, f"Pressed {combo}."
        except Exception as e:
            logger.error(f"Hotkey error: {e}")
            return False, "Hotkey failed."

    def press_key(self, key: str) -> tuple[bool, str]:
        """Press a single key."""
        if not self._pg:
            return False, "Desktop control not available."
        try:
            self._pg.press(key)
            return True, f"Pressed {key}."
        except Exception as e:
            return False, f"Key press failed: {e}"

    # ── Common shortcuts (convenience methods) ─────────────────

    def copy(self)  -> tuple[bool, str]: return self.hotkey("ctrl", "c")
    def paste(self) -> tuple[bool, str]: return self.hotkey("ctrl", "v")
    def cut(self)   -> tuple[bool, str]: return self.hotkey("ctrl", "x")
    def undo(self)  -> tuple[bool, str]: return self.hotkey("ctrl", "z")
    def redo(self)  -> tuple[bool, str]: return self.hotkey("ctrl", "y")
    def save(self)  -> tuple[bool, str]: return self.hotkey("ctrl", "s")
    def select_all(self) -> tuple[bool, str]: return self.hotkey("ctrl", "a")

    def volume_up(self)   -> tuple[bool, str]: return self.press_key("volumeup")
    def volume_down(self) -> tuple[bool, str]: return self.press_key("volumedown")
    def mute(self)        -> tuple[bool, str]: return self.press_key("volumemute")

    def minimize_all(self) -> tuple[bool, str]:
        return self.hotkey("win", "d")

    def lock_screen(self) -> tuple[bool, str]:
        return self.hotkey("win", "l")

    # ── Mouse ─────────────────────────────────────────────────

    def click(self, x: int, y: int, button: str = "left") -> tuple[bool, str]:
        """Click at screen coordinates."""
        if not self._pg:
            return False, "Desktop control not available."
        try:
            self._pg.click(x, y, button=button)
            return True, f"Clicked at ({x}, {y})."
        except Exception as e:
            return False, f"Click failed: {e}"

    def double_click(self, x: int, y: int) -> tuple[bool, str]:
        """Double-click at screen coordinates."""
        if not self._pg:
            return False, "Desktop control not available."
        try:
            self._pg.doubleClick(x, y)
            return True, f"Double-clicked at ({x}, {y})."
        except Exception as e:
            return False, f"Double-click failed: {e}"

    def scroll(self, direction: str = "down", clicks: int = 3) -> tuple[bool, str]:
        """Scroll up or down."""
        if not self._pg:
            return False, "Desktop control not available."
        amount = -clicks if direction == "down" else clicks
        try:
            self._pg.scroll(amount)
            return True, f"Scrolled {direction}."
        except Exception as e:
            return False, f"Scroll failed: {e}"

    def get_screen_size(self) -> tuple[int, int]:
        """Return (width, height) of the primary monitor."""
        if not self._pg:
            return 1920, 1080
        return self._pg.size()

    # ── Screenshot ────────────────────────────────────────────

    def screenshot(self, filename: Optional[str] = None) -> tuple[bool, str]:
        """
        Take a screenshot and save it to data/screenshots/.
        Returns (success, filepath_or_error).
        """
        if not self._pg:
            return False, "Desktop control not available."
        try:
            if not filename:
                ts = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{ts}.png"

            filepath = SCREENSHOT_DIR / filename
            img = self._pg.screenshot()
            img.save(str(filepath))
            logger.info(f"Screenshot saved: {filepath}")
            return True, str(filepath)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False, f"Screenshot failed: {e}"

    # ── Window management ─────────────────────────────────────

    def get_active_window_title(self) -> Optional[str]:
        """Return the title of the currently focused window."""
        try:
            import pygetwindow as gw
            win = gw.getActiveWindow()
            return win.title if win else None
        except Exception:
            return None

    def minimize_window(self) -> tuple[bool, str]:
        return self.hotkey("win", "down")

    def maximize_window(self) -> tuple[bool, str]:
        return self.hotkey("win", "up")
