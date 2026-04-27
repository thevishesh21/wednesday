"""
Wednesday AI Assistant — Camera Preview Window
Shows webcam feed with MediaPipe hand landmark overlay.
Runs camera capture in a QThread for zero GUI lag.
"""

import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import (
    Qt, QThread, QObject, pyqtSignal, pyqtSlot, QTimer,
)
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor, QPainter

from gui.theme import Colors


# ═════════════════════════════════════════════════════════════════
#  Camera Worker — captures frames + runs hand detection off-thread
# ═════════════════════════════════════════════════════════════════

class CameraWorker(QObject):
    """Captures webcam frames in a background thread."""

    frame_ready = pyqtSignal(QImage)  # BGR→RGB QImage for display
    error       = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self._tracker = None

    @pyqtSlot()
    def run(self):
        try:
            from gesture.hand_tracker import HandTracker
            from vision.camera_capture import camera_capture
            
            self._tracker = HandTracker(max_hands=1)
            
            if not camera_capture.start():
                self.error.emit("Camera not available")
                return

            while self._running:
                raw_frame = camera_capture.get_frame()
                if raw_frame is None:
                    QThread.msleep(30)
                    continue
                
                # Copy frame to avoid modifying the shared one
                frame = raw_frame.copy()
                frame, results = self._tracker.process_frame(frame)

                # Draw hand landmarks on frame
                self._tracker.draw_landmarks(frame, results)

                # Add futuristic overlay
                frame = self._draw_overlay(frame)

                # Convert BGR → RGB → QImage
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                self.frame_ready.emit(qimg.copy())

                QThread.msleep(33)  # ~30 fps

        except Exception as e:
            self.error.emit(str(e))
        finally:
            from vision.camera_capture import camera_capture
            camera_capture.stop()
            if self._tracker:
                self._tracker.hands.close() # Close mediapipe, don't stop camera here

    def stop(self):
        self._running = False

    @staticmethod
    def _draw_overlay(frame):
        """Add a subtle futuristic HUD overlay."""
        h, w = frame.shape[:2]
        overlay = frame.copy()

        # Corner brackets (top-left)
        color = (0, 212, 255)  # Blue
        thickness = 1
        sz = 20
        cv2.line(overlay, (10, 10), (10 + sz, 10), color, thickness)
        cv2.line(overlay, (10, 10), (10, 10 + sz), color, thickness)
        # top-right
        cv2.line(overlay, (w - 10, 10), (w - 10 - sz, 10), color, thickness)
        cv2.line(overlay, (w - 10, 10), (w - 10, 10 + sz), color, thickness)
        # bottom-left
        cv2.line(overlay, (10, h - 10), (10 + sz, h - 10), color, thickness)
        cv2.line(overlay, (10, h - 10), (10, h - 10 - sz), color, thickness)
        # bottom-right
        cv2.line(overlay, (w - 10, h - 10), (w - 10 - sz, h - 10), color, thickness)
        cv2.line(overlay, (w - 10, h - 10), (w - 10, h - 10 - sz), color, thickness)

        # Label
        cv2.putText(overlay, "WEDNESDAY GESTURE", (15, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        return cv2.addWeighted(overlay, 0.8, frame, 0.2, 0)


# ═════════════════════════════════════════════════════════════════
#  Camera Preview Window
# ═════════════════════════════════════════════════════════════════

class CameraPreview(QWidget):
    """
    Floating camera preview window with hand tracking overlay.
    Opens when gesture mode is ON, closes when OFF.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wednesday — Gesture Camera")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(400, 300)
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        # Video display label
        self._display = QLabel("Starting camera…")
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px;"
            f" border: 1px solid {Colors.BLUE}33; border-radius: 4px;"
        )
        self._display.setSizePolicy(QSizePolicy.Policy.Expanding,
                                     QSizePolicy.Policy.Expanding)
        layout.addWidget(self._display)

        # Worker + thread
        self._worker = None
        self._thread = None

    def start(self):
        """Start the camera capture thread."""
        if self._thread and self._thread.isRunning():
            return

        self._worker = CameraWorker()
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.frame_ready.connect(self._update_frame)
        self._worker.error.connect(self._on_error)
        self._thread.start()
        self.show()

    def stop(self):
        """Stop the camera and close the window."""
        if self._worker:
            self._worker.stop()
        if self._thread:
            self._thread.quit()
            self._thread.wait(3000)
        self._worker = None
        self._thread = None
        self.hide()

    @pyqtSlot(QImage)
    def _update_frame(self, qimg: QImage):
        """Display a new frame."""
        pixmap = QPixmap.fromImage(qimg).scaled(
            self._display.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._display.setPixmap(pixmap)

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        self._display.setText(f"⚠️ {msg}")

    def closeEvent(self, event):
        self.stop()
        event.accept()
