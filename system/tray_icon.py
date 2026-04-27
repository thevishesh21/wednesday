"""
WEDNESDAY AI OS — System Tray Icon
Creates a background tray icon for Wednesday.
"""

import threading
import sys
import os

from core.logger import get_logger
from core.event_bus import publish_sync
from system.startup_manager import startup_manager

log = get_logger("system.tray_icon")

class TrayIcon(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="wednesday-tray")
        self.icon = None
        
    def run(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Create a simple W icon if no icon file exists
            def create_image():
                image = Image.new('RGB', (64, 64), color=(30, 30, 30))
                dc = ImageDraw.Draw(image)
                dc.text((20, 15), "W", fill=(0, 255, 255))
                return image

            menu = pystray.Menu(
                pystray.MenuItem("Wake Assistant", self._on_wake),
                pystray.MenuItem("Settings", self._on_settings),
                pystray.MenuItem("Run on Startup", self._toggle_startup, checked=lambda item: startup_manager.is_registered()),
                pystray.MenuItem("Exit", self._on_exit)
            )
            
            self.icon = pystray.Icon("Wednesday", create_image(), "Wednesday AI", menu)
            log.info("Starting System Tray Icon...")
            self.icon.run()
            
        except ImportError:
            log.warning("pystray or Pillow not installed. Tray icon disabled.")
        except Exception as e:
            log.error(f"Tray icon failed: {e}")
            
    def _on_wake(self, icon, item):
        publish_sync("voice.wake_detected", {"source": "tray"})
        
    def _on_settings(self, icon, item):
        publish_sync("system.open_settings", {})
        
    def _toggle_startup(self, icon, item):
        if startup_manager.is_registered():
            startup_manager.disable()
        else:
            startup_manager.enable()
            
    def _on_exit(self, icon, item):
        self.icon.stop()
        # In a real app, this should trigger a graceful shutdown event
        import os
        os._exit(0)

# Global instance
tray_icon = TrayIcon()
