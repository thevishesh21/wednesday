"""
Wednesday - GUI Animations
Animated orb widget that changes based on assistant state.
Features a glowing 3D-style orb with state-dependent colors and animations.
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QRadialGradient, QColor, QPen


STATE_COLORS = {
    "sleeping": QColor(107, 114, 128),   # gray
    "listening": QColor(59, 130, 246),   # blue
    "thinking": QColor(139, 92, 246),    # purple
    "speaking": QColor(34, 197, 94),     # green
    "error": QColor(239, 68, 68),        # red
}

STATE_GLOW_COLORS = {
    "sleeping": QColor(107, 114, 128, 40),
    "listening": QColor(59, 130, 246, 50),
    "thinking": QColor(139, 92, 246, 60),
    "speaking": QColor(34, 197, 94, 50),
    "error": QColor(239, 68, 68, 50),
}


class OrbWidget(QWidget):
    """Animated pulsing orb that reflects assistant state with 3D-style effects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self._state = "sleeping"
        self._pulse = 0.0
        self._pulse_dir = 1
        self._angle = 0.0
        self._wave_offset = 0.0
        self._particle_angle = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)  # ~33 fps

    def set_state(self, state: str):
        self._state = state

    def _animate(self):
        # Pulse speed varies by state
        speeds = {
            "sleeping": 0.015,
            "listening": 0.04,
            "thinking": 0.05,
            "speaking": 0.06,
            "error": 0.07,
        }
        speed = speeds.get(self._state, 0.03)
        self._pulse += speed * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse_dir = 1

        # Rotation for thinking state
        if self._state == "thinking":
            self._angle += 4.0
            if self._angle >= 360:
                self._angle -= 360

        # Wave effect for speaking
        self._wave_offset += 0.12

        # Particle orbit
        self._particle_angle += 2.0
        if self._particle_angle >= 360:
            self._particle_angle -= 360

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        base_color = STATE_COLORS.get(self._state, STATE_COLORS["sleeping"])
        glow_color = STATE_GLOW_COLORS.get(self._state, STATE_GLOW_COLORS["sleeping"])

        # --- Outer ambient glow ---
        glow_radius = 55 + self._pulse * 5
        glow_grad = QRadialGradient(QPointF(cx, cy), glow_radius)
        glow_grad.setColorAt(0, glow_color)
        gc_mid = QColor(glow_color)
        gc_mid.setAlpha(15)
        glow_grad.setColorAt(0.6, gc_mid)
        gc_outer = QColor(glow_color)
        gc_outer.setAlpha(0)
        glow_grad.setColorAt(1, gc_outer)
        painter.setBrush(glow_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_radius, glow_radius)

        # --- Main orb with 3D gradient ---
        orb_radius = 28 + self._pulse * 4
        # Light source is top-left
        highlight_offset = orb_radius * 0.3
        orb_grad = QRadialGradient(
            QPointF(cx - highlight_offset, cy - highlight_offset), orb_radius * 1.4
        )
        lighter = QColor(base_color).lighter(180)
        lighter.setAlpha(255)
        orb_grad.setColorAt(0, lighter)
        orb_grad.setColorAt(0.45, base_color)
        orb_grad.setColorAt(0.85, base_color.darker(140))
        orb_grad.setColorAt(1, base_color.darker(200))
        painter.setBrush(orb_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), orb_radius, orb_radius)

        # --- Specular highlight (small white dot, top-left of orb) ---
        spec_x = cx - orb_radius * 0.3
        spec_y = cy - orb_radius * 0.3
        spec_radius = orb_radius * 0.18
        spec_grad = QRadialGradient(QPointF(spec_x, spec_y), spec_radius)
        spec_grad.setColorAt(0, QColor(255, 255, 255, 160))
        spec_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(spec_grad)
        painter.drawEllipse(QPointF(spec_x, spec_y), spec_radius, spec_radius)

        # --- State-specific effects ---

        if self._state == "listening":
            # Pulsing ring
            ring_r = orb_radius + 8 + self._pulse * 4
            ring_color = QColor(base_color.lighter(130))
            ring_color.setAlpha(int(150 - self._pulse * 80))
            ring_pen = QPen(ring_color)
            ring_pen.setWidthF(1.5)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

            # Second outer ring (fading)
            ring_r2 = orb_radius + 15 + self._pulse * 6
            ring_color2 = QColor(base_color.lighter(120))
            ring_color2.setAlpha(int(80 - self._pulse * 60))
            ring_pen2 = QPen(ring_color2)
            ring_pen2.setWidthF(1.0)
            painter.setPen(ring_pen2)
            painter.drawEllipse(QPointF(cx, cy), ring_r2, ring_r2)

        elif self._state == "thinking":
            # Rotating arc (spinner)
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self._angle)
            painter.translate(-cx, -cy)

            arc_r = orb_radius + 10
            arc_rect = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
            arc_color = QColor(base_color.lighter(150))
            arc_color.setAlpha(200)
            arc_pen = QPen(arc_color)
            arc_pen.setWidthF(2.5)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(arc_rect, 0, 240 * 16)
            painter.restore()

            # Second counter-rotating arc
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(-self._angle * 0.7)
            painter.translate(-cx, -cy)

            arc_r2 = orb_radius + 16
            arc_rect2 = QRectF(cx - arc_r2, cy - arc_r2, arc_r2 * 2, arc_r2 * 2)
            arc_color2 = QColor(base_color.lighter(120))
            arc_color2.setAlpha(100)
            arc_pen2 = QPen(arc_color2)
            arc_pen2.setWidthF(1.5)
            arc_pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen2)
            painter.drawArc(arc_rect2, 120 * 16, 180 * 16)
            painter.restore()

        elif self._state == "speaking":
            # Sound wave dots that bounce
            painter.setPen(Qt.PenStyle.NoPen)
            num_dots = 5
            for i in range(num_dots):
                phase = self._wave_offset + i * 0.8
                bounce = math.sin(phase) * 6
                dot_x = cx - (num_dots - 1) * 5 + i * 10
                dot_y = cy + orb_radius + 14 + bounce
                dot_alpha = int(220 - abs(bounce) * 15)
                dot_color = QColor(base_color.lighter(160))
                dot_color.setAlpha(max(80, dot_alpha))
                painter.setBrush(dot_color)
                dot_size = 2.5 + abs(math.sin(phase)) * 1.5
                painter.drawEllipse(QPointF(dot_x, dot_y), dot_size, dot_size)

        elif self._state == "error":
            # Warning pulse ring
            ring_r = orb_radius + 6 + self._pulse * 8
            ring_color = QColor(base_color)
            ring_color.setAlpha(int(120 * (1.0 - self._pulse)))
            ring_pen = QPen(ring_color)
            ring_pen.setWidthF(2.0)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        # --- Orbiting particles (all active states) ---
        if self._state not in ("sleeping",):
            painter.setPen(Qt.PenStyle.NoPen)
            num_particles = 3
            orbit_r = orb_radius + 12
            for i in range(num_particles):
                angle_rad = math.radians(self._particle_angle + i * (360 / num_particles))
                px = cx + math.cos(angle_rad) * orbit_r
                py = cy + math.sin(angle_rad) * orbit_r
                particle_color = QColor(base_color.lighter(170))
                particle_color.setAlpha(int(140 + self._pulse * 60))
                painter.setBrush(particle_color)
                painter.drawEllipse(QPointF(px, py), 2.0, 2.0)

        painter.end()
