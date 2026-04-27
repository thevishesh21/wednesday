"""
WEDNESDAY AI OS — System Permissions
Checks access to Mic, Camera, and Network.
"""

import sys
from core.logger import get_logger

log = get_logger("system.permissions")

class SystemPermissions:
    
    @staticmethod
    def check_mic_access() -> bool:
        try:
            import sounddevice as sd
            # Just querying the default device is usually enough to trigger a permission request on MacOS
            # On Windows, it just checks if a device exists.
            devices = sd.query_devices()
            return len(devices) > 0
        except Exception as e:
            log.warning(f"Microphone access check failed: {e}")
            return False
            
    @staticmethod
    def check_camera_access() -> bool:
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap is None or not cap.isOpened():
                return False
            cap.release()
            return True
        except ImportError:
            log.warning("OpenCV not installed, cannot check camera.")
            return False
        except Exception as e:
            log.warning(f"Camera access check failed: {e}")
            return False

    @staticmethod
    def check_network_access() -> bool:
        import urllib.request
        try:
            urllib.request.urlopen('http://8.8.8.8', timeout=1)
            return True
        except Exception:
            return False

permissions = SystemPermissions()
