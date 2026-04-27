"""
WEDNESDAY AI OS — Face Detection
Presence sensing using OpenCV Haar Cascades.
"""
import cv2
import os
from vision.camera_capture import camera_capture
from core.logger import get_logger

log = get_logger("vision.face")

class FaceDetector:
    def __init__(self):
        # Load pre-trained Haar Cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.last_face_count = 0

    def detect_presence(self) -> bool:
        """Return True if at least one face is detected."""
        frame = camera_capture.get_frame()
        if frame is None:
            return False
            
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            self.last_face_count = len(faces)
            return len(faces) > 0
        except Exception as e:
            log.error(f"Face detection error: {e}")
            return False

face_detector = FaceDetector()
