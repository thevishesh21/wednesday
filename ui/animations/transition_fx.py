"""
WEDNESDAY AI OS — Transition FX
Provides mathematical easing functions and cross-fade support for UI elements.
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QObject

class ColorTransitionFX(QObject):
    """Animates colors with ease-in-out-cubic over 600ms."""
    
    def __init__(self, target_widget, property_name: bytes, duration: int = 600):
        super().__init__(target_widget)
        self.anim = QPropertyAnimation(target_widget, property_name, self)
        self.anim.setDuration(duration)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
    def start_transition(self, start_color, end_color):
        self.anim.stop()
        self.anim.setStartValue(start_color)
        self.anim.setEndValue(end_color)
        self.anim.start()
