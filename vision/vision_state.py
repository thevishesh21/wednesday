"""
WEDNESDAY AI OS — Vision State
Tracks the current visual context and user presence.
"""
from core.event_bus import event_bus
from core.logger import get_logger
import asyncio

log = get_logger("vision.state")

class VisionState:
    def __init__(self):
        self.user_present = False
        self.last_screen_context = ""
        self.monitoring = False

    async def start_monitoring(self):
        """Periodically check for user presence and screen changes."""
        self.monitoring = True
        log.info("Vision monitoring started.")
        
        while self.monitoring:
            try:
                from vision.face_detect import face_detector
                is_present = face_detector.detect_presence()
                
                if is_present != self.user_present:
                    self.user_present = is_present
                    event = "vision.user_present" if is_present else "vision.user_absent"
                    await event_bus.publish(event, {"present": is_present})
                    log.info(f"User presence changed: {is_present}")
                
                await asyncio.sleep(2) # Check every 2s
            except Exception as e:
                log.error(f"Vision monitoring loop error: {e}")
                await asyncio.sleep(5)

    def stop_monitoring(self):
        self.monitoring = False

vision_state = VisionState()
