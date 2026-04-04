"""
Wednesday AI Assistant — Automation Tool
Mouse movements, clicks, keyboard typing, and key presses via pyautogui.
"""

import pyautogui
import time
from utils.logger import get_logger

log = get_logger("automation")

# ── Safety: prevent pyautogui from locking up ───────────────────
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.3      # Small delay between actions


def type_text(text: str) -> str:
    """
    Type text using the keyboard (simulates key presses).

    Args:
        text: The text to type
    """
    log.info(f"Typing: {text}")
    try:
        # Small delay before typing to let user switch focus
        time.sleep(0.5)
        pyautogui.typewrite(text, interval=0.03) if text.isascii() else pyautogui.write(text)
        log.info("Text typed successfully.")
        return f"Typed: '{text}'"
    except Exception as e:
        log.error(f"Type failed: {e}")
        return f"Typing failed: {e}"


def hotkey(*keys) -> str:
    """
    Press a keyboard shortcut (e.g. hotkey('ctrl', 'c')).

    Args:
        keys: Key names to press together
    """
    log.info(f"Hotkey: {'+'.join(keys)}")
    try:
        pyautogui.hotkey(*keys)
        return f"Pressed: {'+'.join(keys)}"
    except Exception as e:
        log.error(f"Hotkey failed: {e}")
        return f"Hotkey failed: {e}"


def press_key(key: str) -> str:
    """
    Press a single key (e.g. 'enter', 'escape', 'tab').

    Args:
        key: Key name
    """
    log.info(f"Key press: {key}")
    try:
        pyautogui.press(key)
        return f"Pressed: {key}"
    except Exception as e:
        log.error(f"Key press failed: {e}")
        return f"Key press failed: {e}"


def mouse_click(x: int = None, y: int = None, button: str = "left") -> str:
    """
    Click the mouse at a position (or current position if x,y not given).

    Args:
        x: X coordinate (optional)
        y: Y coordinate (optional)
        button: 'left', 'right', or 'middle'
    """
    log.info(f"Mouse click: ({x}, {y}) button={button}")
    try:
        if x is not None and y is not None:
            pyautogui.click(x=int(x), y=int(y), button=button)
        else:
            pyautogui.click(button=button)
        return f"Clicked at ({x}, {y}) with {button} button"
    except Exception as e:
        log.error(f"Click failed: {e}")
        return f"Click failed: {e}"


def move_mouse(x: int, y: int) -> str:
    """
    Move mouse cursor to position.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    log.info(f"Move mouse to: ({x}, {y})")
    try:
        pyautogui.moveTo(int(x), int(y), duration=0.3)
        return f"Mouse moved to ({x}, {y})"
    except Exception as e:
        log.error(f"Mouse move failed: {e}")
        return f"Mouse move failed: {e}"


def scroll(amount: int) -> str:
    """
    Scroll the mouse wheel.

    Args:
        amount: Positive = up, negative = down
    """
    log.info(f"Scroll: {amount}")
    try:
        pyautogui.scroll(int(amount))
        return f"Scrolled {'up' if amount > 0 else 'down'} by {abs(amount)}"
    except Exception as e:
        log.error(f"Scroll failed: {e}")
        return f"Scroll failed: {e}"


def screenshot_position() -> str:
    """Get the current mouse position (useful for debugging)."""
    pos = pyautogui.position()
    result = f"Mouse is at ({pos.x}, {pos.y})"
    log.info(result)
    return result
