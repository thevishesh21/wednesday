"""
Wednesday AI Assistant — Voice Waveform Widget
Animated audio-reactive bars that visualize microphone energy.
Shows futuristic frequency-bar style animation when listening,
collapses to flat when idle.
"""

import math
import random
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QLinearGradient

from gui.theme import Colors, STATE_QCOLORS


# Number of bars in the waveform
BAR_COUNT = 32


class WaveformWidget(QWidget):
    """
    Animated audio waveform bars.

    Usage:
        waveform.set_active(True)   → bars start animating
        waveform.set_energy(0.6)    → external energy level [0-1]
        waveform.set_active(False)  → bars shrink to min height
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)

        self._active = False
        self._energy = 0.0          # external energy [0-1]
        self._opacity = 0.0         # fade in/out
        self._color = STATE_QCOLORS["listening"]

        # Each bar has a current height ratio [0-1]
        self._bars = [0.05] * BAR_COUNT
        # Target heights (randomized each tick)
        self._targets = [0.05] * BAR_COUNT

        # Animation timer (~60 fps)
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 fps for smooth but light CPU
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        # Opacity animation
        self._opacity_anim = QPropertyAnimation(self, b"opacity")
        self._opacity_anim.setDuration(400)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    # ── properties ───────────────────────────────────────────────

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, v):
        self._opacity = v
        self.update()

    # ── public API ───────────────────────────────────────────────

    def set_active(self, active: bool):
        """Show or hide the waveform with a fade transition."""
        self._active = active
        self._opacity_anim.stop()
        self._opacity_anim.setStartValue(self._opacity)
        self._opacity_anim.setEndValue(1.0 if active else 0.0)
        self._opacity_anim.start()

    def set_energy(self, energy: float):
        """Set current mic energy level [0.0 – 1.0]."""
        self._energy = max(0.0, min(1.0, energy))

    def set_color(self, state: str):
        """Set bar color from orb state name."""
        self._color = STATE_QCOLORS.get(state, STATE_QCOLORS["listening"])

    # ── animation tick ───────────────────────────────────────────

    def _tick(self):
        if self._opacity < 0.01:
            return  # invisible, skip

        if self._active:
            # Generate random targets biased by energy level
            base = 0.08
            amp = 0.3 + self._energy * 0.65
            for i in range(BAR_COUNT):
                # Create a wave pattern + randomness
                wave = math.sin(i * 0.5 + random.random() * 2) * 0.5 + 0.5
                self._targets[i] = base + wave * amp * random.uniform(0.5, 1.0)
        else:
            self._targets = [0.05] * BAR_COUNT

        # Smooth interpolation toward targets
        for i in range(BAR_COUNT):
            self._bars[i] += (self._targets[i] - self._bars[i]) * 0.25

        self.update()

    # ── painting ─────────────────────────────────────────────────

    def paintEvent(self, event):
        if self._opacity < 0.01:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self._opacity)

        w = self.width()
        h = self.height()
        bar_w = max(2, (w - BAR_COUNT * 2) / BAR_COUNT)
        gap = 2
        total_w = BAR_COUNT * (bar_w + gap) - gap
        x_start = (w - total_w) / 2

        r, g, b = self._color.red(), self._color.green(), self._color.blue()

        for i in range(BAR_COUNT):
            bar_h = max(2, self._bars[i] * h)
            x = x_start + i * (bar_w + gap)
            y = (h - bar_h) / 2  # centered vertically

            # Gradient: bright center → transparent edges
            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0.0, QColor(r, g, b, int(60 * self._opacity)))
            grad.setColorAt(0.5, QColor(r, g, b, int(200 * self._opacity)))
            grad.setColorAt(1.0, QColor(r, g, b, int(60 * self._opacity)))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(grad)
            p.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 2, 2)

        p.end()
