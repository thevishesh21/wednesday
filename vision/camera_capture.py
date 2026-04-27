"""
WEDNESDAY AI OS — Camera Capture
Unified singleton for webcam access.
"""
import cv2
import threading
import time
from core.logger import get_logger

log = get_logger("vision.camera")

class CameraCapture:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraCapture, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized: return
        self.cap = None
        self.last_frame = None
        self.running = False
        self.thread = None
        self._initialized = True
        self.clients = 0

    def start(self):
        with self._lock:
            self.clients += 1
            if self.running: return
            
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                log.error("Could not open webcam.")
                return False
                
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            log.info("Camera capture started.")
            return True

    def stop(self):
        with self._lock:
            self.clients -= 1
            if self.clients <= 0:
                self.running = False
                if self.thread: self.thread.join(timeout=1)
                if self.cap: self.cap.release()
                self.cap = None
                log.info("Camera capture stopped.")

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.last_frame = frame
            time.sleep(0.03) # ~30 FPS

    def get_frame(self):
        return self.last_frame

camera_capture = CameraCapture()
