"""
WEDNESDAY AI OS — Widget Bar
Bottom panel showing time, weather placeholder, and reminders.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from gui.theme import Colors

class WidgetBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {Colors.BG_SECONDARY}; border-top: 1px solid {Colors.BORDER};")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Clock
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        self.clock_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.clock_label)
        
        layout.addStretch()
        
        # Info
        info_label = QLabel("WEDNESDAY OS v6.0")
        info_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: none; font-weight: bold;")
        layout.addWidget(info_label)
        
        # Timer for clock
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        self._update_time()
        
    def _update_time(self):
        self.clock_label.setText(datetime.now().strftime("%I:%M %p | %b %d, %Y"))
