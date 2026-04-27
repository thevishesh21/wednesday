"""
WEDNESDAY AI OS — Transition FX
Precision easing and color cross-fades for the AI Orb.
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QObject, pyqtProperty
from PyQt6.QtGui import QColor
from gui.theme import STATE_QCOLORS

class OrbTransitionManager(QObject):
    """
    Manages smooth color and state transitions for the AI Orb.
    Implements 600ms ease-in-out-cubic fades as per design spec.
    """

    def __init__(self, orb_widget):
        super().__init__(orb_widget)
        self._orb = orb_widget
        self._current_color = STATE_QCOLORS["idle"]
        
        # Color transition animation
        self._anim = QPropertyAnimation(self, b"orbColor", self)
        self._anim.setDuration(600)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    @pyqtProperty(QColor)
    def orbColor(self) -> QColor:
        """Property wrapper for the orb's current transition color."""
        return self._current_color

    @orbColor.setter
    def orbColor(self, color: QColor):
        """Setter that updates the widget and repaints."""
        self._current_color = color
        self._orb.set_custom_color(color)
        self._orb.update()

    def transition_to(self, state: str):
        """
        Smoothly transition the orb to a new state color.
        
        Args:
            state: The target state (listening, processing, etc.)
        """
        target_color = STATE_QCOLORS.get(state, STATE_QCOLORS["idle"])
        
        self._anim.stop()
        self._anim.setStartValue(self._current_color)
        self._anim.setEndValue(target_color)
        self._anim.start()
