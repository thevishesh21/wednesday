"""
Wednesday AI Assistant — Screenshot Tool
Captures the full screen using Pillow.
"""

import os
from datetime import datetime
from PIL import ImageGrab
from utils.logger import get_logger
import config

log = get_logger("screenshot")


def take_screenshot(save: bool = True) -> str:
    """
    Capture a full screenshot.

    Args:
        save: If True, saves to screenshots/ directory

    Returns:
        File path to the saved screenshot, or "captured" if not saved.
    """
    log.info("Taking screenshot...")
    try:
        img = ImageGrab.grab()

        if save:
            os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(config.SCREENSHOT_DIR, f"screenshot_{timestamp}.png")
            img.save(path)
            log.info(f"Screenshot saved: {path}")
            return path
        else:
            return "captured"

    except Exception as e:
        log.error(f"Screenshot failed: {e}")
        return f"Error: {e}"


def get_screenshot_image():
    """
    Capture and return the PIL Image object directly (for OCR use).
    Does not save to disk.
    """
    try:
        return ImageGrab.grab()
    except Exception as e:
        log.error(f"Screenshot grab failed: {e}")
        return None
