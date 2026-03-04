"""
Wednesday - GUI Animations
Animated orb widget that changes based on assistant state.
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QPointF
from PySide6.QtGui import QPainter, QRadialGradient, QColor, QPen


STATE_COLORS = {
    "sleeping": QColor(90, 96, 120),
    "listening": QColor(52, 152, 219),
    "thinking": QColor(243, 156, 18),
    "speaking": QColor(46, 204, 113),
    "error": QColor(231, 76, 60),
}


class OrbWidget(QWidget):
    """Animated pulsing orb that reflects assistant state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self._state = "sleeping"
        self._pulse = 0.0
        self._pulse_dir = 1
        self._angle = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)  # ~33 fps

    def set_state(self, state: str):
        self._state = state

    def _animate(self):
        # Pulse size
        speed = 0.02 if self._state == "sleeping" else 0.06
        self._pulse += speed * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse_dir = 1

        # Rotation for thinking state
        if self._state == "thinking":
            self._angle += 3.0
            if self._angle >= 360:
                self._angle = 0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        base_color = STATE_COLORS.get(self._state, STATE_COLORS["sleeping"])

        # Outer glow
        glow_radius = 50 + self._pulse * 8
        glow_gradient = QRadialGradient(QPointF(cx, cy), glow_radius)
        glow_color = QColor(base_color)
        glow_color.setAlpha(60)
        glow_gradient.setColorAt(0, glow_color)
        glow_color.setAlpha(0)
        glow_gradient.setColorAt(1, glow_color)
        painter.setBrush(glow_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_radius, glow_radius)

        # Main orb
        orb_radius = 30 + self._pulse * 5
        gradient = QRadialGradient(QPointF(cx - 5, cy - 5), orb_radius)
        lighter = QColor(base_color)
        lighter.setAlpha(255)
        gradient.setColorAt(0, lighter.lighter(150))
        gradient.setColorAt(0.7, base_color)
        gradient.setColorAt(1, base_color.darker(150))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), orb_radius, orb_radius)

        # Ring for thinking/listening
        if self._state in ("thinking", "listening"):
            ring_pen = QPen(QColor(base_color.lighter(130)))
            ring_pen.setWidth(2)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            ring_r = orb_radius + 10
            if self._state == "thinking":
                painter.translate(cx, cy)
                painter.rotate(self._angle)
                painter.translate(-cx, -cy)
                # Draw arc
                from PySide6.QtCore import QRectF
                rect = QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
                painter.drawArc(rect, 0, 270 * 16)
            else:
                # Full ring for listening
                painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        # Small dots for speaking
        if self._state == "speaking":
            dot_pen = QPen(Qt.PenStyle.NoPen)
            painter.setPen(dot_pen)
            for i in range(3):
                offset = math.sin(self._pulse * math.pi + i * 1.0) * 5
                dot_y = cy + 25 + offset
                dot_x = cx - 10 + i * 10
                dot_color = QColor(base_color.lighter(170))
                dot_color.setAlpha(200)
                painter.setBrush(dot_color)
                painter.drawEllipse(QPointF(dot_x, dot_y), 3, 3)

        painter.end()
