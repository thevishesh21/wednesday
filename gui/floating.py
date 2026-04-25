"""
Wednesday AI Assistant — Floating Mini Window
Always-on-top circular orb that can be dragged anywhere.
Click to expand/restore the full main window.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import (
    Qt, QPoint, QTimer, pyqtSignal, pyqtProperty,
    QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QFont

from gui.theme import Colors, STATE_QCOLORS


_FLOAT_SIZE = 72


class FloatingOrb(QWidget):
    """
    Tiny always-on-top orb that floats on the desktop.
    Click → emits `clicked` signal (used to show/hide main window).
    """

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(_FLOAT_SIZE, _FLOAT_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._drag_pos = QPoint()
        self._state_color = STATE_QCOLORS["idle"]
        self._pulse = 1.0

        # Pulse animation
        self._pulse_anim = QPropertyAnimation(self, b"pulse")
        self._pulse_anim.setDuration(2000)
        self._pulse_anim.setKeyValueAt(0.0, 1.0)
        self._pulse_anim.setKeyValueAt(0.5, 1.12)
        self._pulse_anim.setKeyValueAt(1.0, 1.0)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.start()

        # Status text
        self._status_text = ""

    # ── animated property ────────────────────────────────────────

    @pyqtProperty(float)
    def pulse(self):
        return self._pulse

    @pulse.setter
    def pulse(self, v):
        self._pulse = v
        self.update()

    # ── public API ───────────────────────────────────────────────

    def set_state(self, state: str):
        self._state_color = STATE_QCOLORS.get(state, STATE_QCOLORS["idle"])
        labels = {"idle": "", "listening": "🎤", "thinking": "💭", "speaking": "🔊"}
        self._status_text = labels.get(state, "")
        self.update()

    # ── painting ─────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = _FLOAT_SIZE / 2, _FLOAT_SIZE / 2
        r = (_FLOAT_SIZE / 2 - 4) * self._pulse
        cr, cg, cb = (self._state_color.red(),
                      self._state_color.green(),
                      self._state_color.blue())

        # Outer glow
        glow = QRadialGradient(cx, cy, r * 1.3)
        glow.setColorAt(0.0, QColor(cr, cg, cb, 40))
        glow.setColorAt(1.0, QColor(cr, cg, cb, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - r * 1.3), int(cy - r * 1.3),
                       int(r * 2.6), int(r * 2.6))

        # Main circle
        grad = QRadialGradient(cx, cy, r)
        grad.setColorAt(0.0, QColor(cr, cg, cb, 200))
        grad.setColorAt(0.6, QColor(cr, cg, cb, 120))
        grad.setColorAt(1.0, QColor(cr, cg, cb, 40))
        p.setBrush(QBrush(grad))
        p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        # Core
        core = QRadialGradient(cx, cy, r * 0.3)
        core.setColorAt(0.0, QColor(255, 255, 255, 180))
        core.setColorAt(1.0, QColor(cr, cg, cb, 100))
        p.setBrush(QBrush(core))
        p.drawEllipse(int(cx - r * 0.3), int(cy - r * 0.3),
                       int(r * 0.6), int(r * 0.6))

        # Status emoji
        if self._status_text:
            p.setFont(QFont("Segoe UI Emoji", 14))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       self._status_text)

        p.end()

    # ── drag + click ─────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        # Only fire click if the mouse didn't move much (not a drag)
        if event.button() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.pos() - self._drag_pos
            if abs(delta.x()) < 5 and abs(delta.y()) < 5:
                self.clicked.emit()
