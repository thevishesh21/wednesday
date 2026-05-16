"""
control/desktop.py
------------------
Desktop automation via pyautogui.
STUB — Full implementation in Phase 4.
"""
from utils.logger import setup_logger
logger = setup_logger(__name__)

class DesktopController:
    """Phase 4: Mouse, keyboard, window control."""
    async def open_app(self, app_name: str): pass
    async def type_text(self, text: str): pass
    async def click(self, x: int, y: int): pass
