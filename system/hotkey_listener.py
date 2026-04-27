"""
WEDNESDAY AI OS — Global Hotkey Listener
Allows the user to trigger the assistant via a global keyboard shortcut (e.g. Win+W)
even when the app is in the background.
"""

import threading
import keyboard
from typing import Callable, Optional

from core.logger import get_logger
from core.event_bus import publish_sync

log = get_logger("system.hotkey")

class HotkeyListener(threading.Thread):
    def __init__(self, hotkey: str = "windows+w"):
        super().__init__(daemon=True, name="wednesday-hotkey")
        self.hotkey = hotkey
        self._running = False
        
    def run(self):
        log.info(f"Registering global hotkey: {self.hotkey}")
        self._running = True
        
        try:
            # We add a hook that emits a wake event when pressed
            keyboard.add_hotkey(self.hotkey, self._on_hotkey)
            # This blocks forever until the thread dies
            keyboard.wait()
        except ImportError:
            log.warning("keyboard module not installed. Hotkey listener disabled.")
        except Exception as e:
            # Note: The keyboard module requires Administrator privileges on some versions of Windows!
            log.error(f"Failed to register hotkey (try running as Administrator): {e}")
            
    def _on_hotkey(self):
        log.info(f"Hotkey '{self.hotkey}' pressed! Emitting wake event.")
        # Trigger the same event as the voice wake word
        publish_sync("voice.wake_detected", {"source": "hotkey"})
        
    def stop(self):
        if self._running:
            try:
                import keyboard
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass
            self._running = False

# Global instance
hotkey_listener = HotkeyListener()
