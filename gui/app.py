"""
Wednesday - Main GUI Application
PySide6-based floating assistant window with chat interface.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QTextEdit, QLineEdit,
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
    text_submitted = Signal(str)      # text typed in GUI


class WednesdayWindow(QMainWindow):
    """Main assistant window with chat interface."""

    def __init__(self):
        super().__init__()
        self.signals = GUISignals()
        self._drag_pos = None
        self._setup_window()
        self._build_ui()
        self._connect_signals()

    def _setup_window(self):
        self.setWindowTitle("Wednesday")
        self.setFixedSize(420, 620)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(MAIN_STYLESHEET)

        # Position at bottom-right of screen
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

        # --- Orb + Status row ---
        orb_row = QHBoxLayout()
        orb_row.addStretch()

        self.orb = OrbWidget()
        self.orb.setFixedSize(80, 80)
        orb_row.addWidget(self.orb)

        self.status_label = QLabel("Sleeping")
        self.status_label.setObjectName("statusLabel")
        orb_row.addWidget(self.status_label)

        orb_row.addStretch()
        layout.addLayout(orb_row)

        # --- Chat history ---
        self.chat_history = QTextEdit()
        self.chat_history.setObjectName("chatHistory")
        self.chat_history.setReadOnly(True)
        self.chat_history.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.chat_history)

        # --- Input row ---
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Type a command...")
        self.input_field.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_field)

        self.mic_btn = QPushButton("MIC")
        self.mic_btn.setObjectName("micButton")
        self.mic_btn.setFixedSize(45, 38)
        self.mic_btn.clicked.connect(self._on_mic_click)
        input_row.addWidget(self.mic_btn)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setFixedSize(60, 38)
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)

    def _connect_signals(self):
        self.signals.state_changed.connect(self._on_state_changed)
        self.signals.transcript_update.connect(self._on_transcript)
        self.signals.response_update.connect(self._on_response)
        self.signals.status_update.connect(self._on_status)

    def _on_send(self):
        """Handle text submission from input field."""
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._append_chat("You", text)
        self.signals.text_submitted.emit(text)

    def _on_mic_click(self):
        """Toggle listening / wake-up from the MIC button."""
        self.signals.mic_clicked.emit()
        self.signals.status_update.emit("Listening...")
        self.signals.state_changed.emit("listening")

    def _append_chat(self, sender, message):
        """Append a message to the chat history."""
        if sender == "You":
            color = COLORS["text_primary"]
        else:
            color = COLORS["accent_light"]
        self.chat_history.append(
            f'<span style="color:{color};"><b>{sender}:</b> {message}</span>'
        )
        # Auto-scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

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
        """Handle mic-captured user speech — append to chat."""
        self._append_chat("You", text)

    @Slot(str)
    def _on_response(self, text: str):
        """Handle assistant response — append to chat."""
        self._append_chat("Wednesday", text)

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
