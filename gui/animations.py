"""
Wednesday AI Assistant — GUI Animations
All animation logic: pulse, rotation, glow breathing, fade transitions.
Drives the OrbWidget properties via QPropertyAnimation.
"""

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QObject,
)


# ═════════════════════════════════════════════════════════════════
#  Animation speed presets per state
# ═════════════════════════════════════════════════════════════════

_STATE_SPEEDS = {
    "idle":      {"pulse": 3500, "rotation": 12000, "glow": 4500},
    "listening": {"pulse": 1800, "rotation": 6000,  "glow": 2200},
    "thinking":  {"pulse": 1200, "rotation": 2500,  "glow": 1600},
    "speaking":  {"pulse": 900,  "rotation": 4500,  "glow": 1100},
    "executing": {"pulse": 800,  "rotation": 2000,  "glow": 1000},
    "error":     {"pulse": 400,  "rotation": 8000,  "glow": 500},
    "complete":  {"pulse": 2000, "rotation": 5000,  "glow": 3000},
}


class OrbAnimator(QObject):
    """
    Creates and manages three looping QPropertyAnimations that target
    an OrbWidget's custom pyqtProperty values:
        scaleFactor   — pulse (breathing size oscillation)
        rotationAngle — ring rotation (0-360 continuous)
        glowIntensity — glow brightness oscillation
    """

    def __init__(self, orb_widget, parent=None):
        super().__init__(parent)
        self._orb = orb_widget
        self._group = QParallelAnimationGroup(self)
        self._anims: dict[str, QPropertyAnimation] = {}
        self._build()

    # ── build initial animations ─────────────────────────────────

    def _build(self):
        speeds = _STATE_SPEEDS["idle"]

        # Pulse (scale)
        pulse = QPropertyAnimation(self._orb, b"scaleFactor", self)
        pulse.setDuration(speeds["pulse"])
        pulse.setKeyValueAt(0.0, 1.0)
        pulse.setKeyValueAt(0.5, 1.07)
        pulse.setKeyValueAt(1.0, 1.0)
        pulse.setLoopCount(-1)
        pulse.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anims["pulse"] = pulse

        # Rotation
        rotation = QPropertyAnimation(self._orb, b"rotationAngle", self)
        rotation.setDuration(speeds["rotation"])
        rotation.setStartValue(0.0)
        rotation.setEndValue(360.0)
        rotation.setLoopCount(-1)
        self._anims["rotation"] = rotation

        # Glow
        glow = QPropertyAnimation(self._orb, b"glowIntensity", self)
        glow.setDuration(speeds["glow"])
        glow.setKeyValueAt(0.0, 0.55)
        glow.setKeyValueAt(0.5, 1.0)
        glow.setKeyValueAt(1.0, 0.55)
        glow.setLoopCount(-1)
        glow.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anims["glow"] = glow

        for a in self._anims.values():
            self._group.addAnimation(a)

    # ── public API ───────────────────────────────────────────────

    def start(self):
        """Start all animations."""
        self._group.start()

    def stop(self):
        """Stop all animations."""
        self._group.stop()

    def set_state(self, state: str):
        """
        Transition to a new orb state.
        Updates the OrbWidget color and reconfigures animation speeds.
        """
        self._orb.set_state_color(state)
        speeds = _STATE_SPEEDS.get(state, _STATE_SPEEDS["idle"])

        # Stop, reconfigure, restart
        self._group.stop()

        self._anims["pulse"].setDuration(speeds["pulse"])
        self._anims["rotation"].setDuration(speeds["rotation"])
        self._anims["glow"].setDuration(speeds["glow"])

        self._group.start()


# ═════════════════════════════════════════════════════════════════
#  Fade helper (for status label opacity transitions)
# ═════════════════════════════════════════════════════════════════

def create_fade_animation(widget, duration_ms=400, start=0.0, end=1.0):
    """Return a QPropertyAnimation that fades a widget's windowOpacity."""
    from PyQt6.QtWidgets import QGraphicsOpacityEffect

    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration_ms)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    return anim
