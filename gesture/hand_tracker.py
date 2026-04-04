"""
Wednesday AI Assistant — Hand Tracker
Uses MediaPipe Hands to detect hand landmarks from webcam.
Provides finger tip positions and distance calculations.
"""

import cv2
import mediapipe as mp
from utils.logger import get_logger
import config

log = get_logger("hand_tracker")

# ── Initialize MediaPipe Hands ──────────────────────────────────
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Finger tip landmark IDs (MediaPipe convention)
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

INDEX_MCP = 5   # Base of index finger


class HandTracker:
    """
    Wraps MediaPipe Hands for real-time hand tracking.
    """

    def __init__(self, max_hands: int = 1):
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=config.GESTURE_CONFIDENCE_THRESHOLD,
            min_tracking_confidence=0.5,
        )
        self._cap = None
        log.info("HandTracker initialized.")

    def start_camera(self) -> bool:
        """Open the webcam."""
        try:
            self._cap = cv2.VideoCapture(config.GESTURE_CAMERA_INDEX)
            if self._cap.isOpened():
                log.info("Camera opened.")
                return True
            log.error("Camera failed to open.")
            return False
        except Exception as e:
            log.error(f"Camera error: {e}")
            return False

    def stop_camera(self) -> None:
        """Release the webcam."""
        if self._cap and self._cap.isOpened():
            self._cap.release()
            log.info("Camera released.")

    def get_frame(self):
        """Read a frame from the camera and detect hands."""
        if not self._cap or not self._cap.isOpened():
            return None, None

        ret, frame = self._cap.read()
        if not ret:
            return None, None

        # Flip horizontally for mirror effect
        frame = cv2.flip(frame, 1)

        # Convert BGR → RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        return frame, results

    def get_landmarks(self, results, frame_shape):
        """
        Extract hand landmarks as pixel coordinates.

        Returns:
            List of (id, x, y) tuples, or empty list.
        """
        landmarks = []
        if results and results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            h, w, _ = frame_shape
            for idx, lm in enumerate(hand.landmark):
                x, y = int(lm.x * w), int(lm.y * h)
                landmarks.append((idx, x, y))
        return landmarks

    def draw_landmarks(self, frame, results):
        """Draw hand landmarks on the frame (for debug visualization)."""
        if results and results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
        return frame

    @staticmethod
    def distance(p1, p2) -> float:
        """Euclidean distance between two (x, y) points."""
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    def cleanup(self):
        """Release all resources."""
        self.stop_camera()
        self.hands.close()
        cv2.destroyAllWindows()
        log.info("HandTracker cleaned up.")
