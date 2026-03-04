"""
Wednesday - Main GUI Application
PySide6-based floating assistant window.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QObject, Slot, QPoint
from PySide6.QtGui import QFont

from gui.theme import MAIN_STYLESHEET, COLORS, FONT_FAMILY
from gui.animations import OrbWidget


class GUISignals(QObject):
    """Thread-safe signals for updating GUI from worker threads."""
    state_changed = Signal(str)       # "sleeping", "listening", etc.
    transcript_update = Signal(str)   # user speech text
    response_update = Signal(str)     # assistant response text
    status_update = Signal(str)       # status bar text
    mic_clicked = Signal()            # MIC button pressed


class WednesdayWindow(QMainWindow):
    """Main assistant window."""

    def __init__(self):
        super().__init__()
        self.signals = GUISignals()
        self._drag_pos = None
        self._setup_window()
        self._build_ui()
        self._connect_signals()

    def _setup_window(self):
        self.setWindowTitle("Wednesday")
        self.setFixedSize(360, 500)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(MAIN_STYLESHEET)

        # Center on screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.width() - self.width() - 30
            y = geo.height() - self.height() - 60
            self.move(x, y)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(10)

        # --- Title bar ---
        title_bar = QHBoxLayout()

        title_label = QLabel("Wednesday")
        title_label.setObjectName("titleLabel")
        title_bar.addWidget(title_label)

        title_bar.addStretch()

        close_btn = QPushButton("X")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self._on_close)
        title_bar.addWidget(close_btn)

        layout.addLayout(title_bar)

        # --- Orb animation ---
        orb_container = QHBoxLayout()
        orb_container.addStretch()
        self.orb = OrbWidget()
        orb_container.addWidget(self.orb)
        orb_container.addStretch()
        layout.addLayout(orb_container)

        # --- Status label ---
        self.status_label = QLabel("Sleeping")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # --- Transcript (what user said) ---
        self.transcript_label = QLabel("")
        self.transcript_label.setObjectName("transcriptLabel")
        self.transcript_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setMaximumHeight(60)
        layout.addWidget(self.transcript_label)

        # --- Response (what assistant said) ---
        self.response_label = QLabel("")
        self.response_label.setObjectName("responseLabel")
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.response_label)

        # --- Mic button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.mic_btn = QPushButton("MIC")
        self.mic_btn.setObjectName("micButton")
        self.mic_btn.setFixedSize(60, 60)
        self.mic_btn.clicked.connect(self._on_mic_click)
        btn_layout.addWidget(self.mic_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.signals.state_changed.connect(self._on_state_changed)
        self.signals.transcript_update.connect(self._on_transcript)
        self.signals.response_update.connect(self._on_response)
        self.signals.status_update.connect(self._on_status)

    def _on_mic_click(self):
        """Toggle listening / wake-up from the MIC button."""
        self.signals.mic_clicked.emit()
        self.signals.status_update.emit("Listening...")
        self.signals.state_changed.emit("listening")

    # --- Signal handlers (run on GUI thread) ---

    @Slot(str)
    def _on_state_changed(self, state: str):
        self.orb.set_state(state)
        state_display = {
            "sleeping": "Sleeping",
            "listening": "Listening...",
            "thinking": "Thinking...",
            "speaking": "Speaking...",
            "error": "Error",
        }
        self.status_label.setText(state_display.get(state, state))

    @Slot(str)
    def _on_transcript(self, text: str):
        display = text if len(text) <= 120 else text[:120] + "..."
        self.transcript_label.setText(f'You: "{display}"')

    @Slot(str)
    def _on_response(self, text: str):
        display = text if len(text) <= 300 else text[:300] + "..."
        self.response_label.setText(display)

    @Slot(str)
    def _on_status(self, text: str):
        self.status_label.setText(text)

    # --- Window dragging ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _on_close(self):
        self.close()

    def closeEvent(self, event):
        event.accept()
