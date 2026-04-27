"""
WEDNESDAY AI OS — Screen Reader
Screenshot -> vision model -> UI element analysis.
"""
import os
import time
from vision.screenshot import take_screenshot
from vision.vision_model import vision_model
from core.logger import get_logger

log = get_logger("vision.screen_reader")

class ScreenReader:
    def __init__(self):
        self.last_analysis = ""

    def read_screen(self, prompt: str = "Describe the contents of this computer screen.") -> str:
        """Capture the screen and describe it."""
        try:
            path = take_screenshot()
            if not path:
                return "Failed to capture screenshot."
            
            description = vision_model.describe_image(path, prompt)
            self.last_analysis = description
            return description
        except Exception as e:
            log.error(f"Screen reading failed: {e}")
            return str(e)

    def find_element(self, element_name: str) -> str:
        """Attempt to find a specific UI element on screen."""
        prompt = f"Where is the '{element_name}' located on this screen? Provide approximate coordinates or area."
        return self.read_screen(prompt)

screen_reader = ScreenReader()
