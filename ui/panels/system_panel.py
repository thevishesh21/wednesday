"""
WEDNESDAY AI OS — System Panel
Left panel showing real-time CPU, RAM, Network stats.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from gui.theme import Colors

class SystemPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 20, 10, 20)
        self.layout.setSpacing(15)
        
        # Header
        header = QLabel("SYSTEM METRICS")
        header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {Colors.TEXT_MUTED}; letter-spacing: 2px;")
        self.layout.addWidget(header)
        
        # CPU
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setStyleSheet(f"QProgressBar {{ background: {Colors.BG_SECONDARY}; border-radius: 4px; height: 8px; }} QProgressBar::chunk {{ background: {Colors.BLUE}; border-radius: 4px; }}")
        
        self.layout.addWidget(self.cpu_label)
        self.layout.addWidget(self.cpu_bar)
        
        # RAM
        self.ram_label = QLabel("RAM: 0%")
        self.ram_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self.ram_bar = QProgressBar()
        self.ram_bar.setTextVisible(False)
        self.ram_bar.setStyleSheet(f"QProgressBar {{ background: {Colors.BG_SECONDARY}; border-radius: 4px; height: 8px; }} QProgressBar::chunk {{ background: {Colors.PURPLE}; border-radius: 4px; }}")
        
        self.layout.addWidget(self.ram_label)
        self.layout.addWidget(self.ram_bar)
        
        self.layout.addStretch()
        
        # Update Timer (every 2s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_metrics)
        self.timer.start(2000)
        
    def _update_metrics(self):
        try:
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            
            self.cpu_label.setText(f"CPU: {cpu}%")
            self.cpu_bar.setValue(int(cpu))
            
            self.ram_label.setText(f"RAM: {mem}%")
            self.ram_bar.setValue(int(mem))
        except ImportError:
            pass
