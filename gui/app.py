"""
Wednesday - Main GUI Application
PySide6-based floating assistant window with chat interface.
Includes sound effects for state changes and message bubbles.
"""

import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QTextEdit, QLineEdit,
)
from PySide6.QtCore import Qt, Signal, QObject, Slot, QUrl

try:
    from PySide6.QtMultimedia import QSoundEffect
    _HAS_AUDIO = True
except ImportError:
    _HAS_AUDIO = False

from gui.theme import MAIN_STYLESHEET, COLORS, FONT_FAMILY
from gui.animations import OrbWidget
import config


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
        self._sounds = {}
        self._last_state = "sleeping"
        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._load_sounds()

    def _setup_window(self):
        self.setWindowTitle("Wednesday")
        self.setFixedSize(440, 660)
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
        layout.setContentsMargins(22, 16, 22, 20)
        layout.setSpacing(12)

        # --- Title bar ---
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)

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

        # --- Orb + Status (centered column) ---
        orb_container = QHBoxLayout()
        orb_container.addStretch()

        orb_col = QVBoxLayout()
        orb_col.setSpacing(4)
        orb_col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.orb = OrbWidget()
        self.orb.setFixedSize(90, 90)
        orb_col.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Sleeping")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orb_col.addWidget(self.status_label)

        orb_container.addLayout(orb_col)
        orb_container.addStretch()
        layout.addLayout(orb_container)

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
        self.mic_btn.setFixedSize(48, 40)
        self.mic_btn.clicked.connect(self._on_mic_click)
        input_row.addWidget(self.mic_btn)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setFixedSize(64, 40)
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)

    def _connect_signals(self):
        self.signals.state_changed.connect(self._on_state_changed)
        self.signals.transcript_update.connect(self._on_transcript)
        self.signals.response_update.connect(self._on_response)
        self.signals.status_update.connect(self._on_status)

    def _load_sounds(self):
        """Load WAV sound effects from sounds/ directory (if available)."""
        if not _HAS_AUDIO:
            return

        # Map state transitions to sound file names
        sound_map = {
            "listening": "wake.wav",
            "thinking":  "thinking.wav",
            "speaking":  "confirm.wav",
        }

        sounds_dir = getattr(config, "SOUNDS_DIR", "")
        if not sounds_dir or not os.path.isdir(sounds_dir):
            return

        for state_name, filename in sound_map.items():
            path = os.path.join(sounds_dir, filename)
            if os.path.isfile(path):
                try:
                    effect = QSoundEffect()
                    effect.setSource(QUrl.fromLocalFile(path))
                    effect.setVolume(0.3)
                    self._sounds[state_name] = effect
                except Exception:
                    pass

    def _play_sound(self, state: str):
        """Play a sound effect for a state transition (if loaded)."""
        effect = self._sounds.get(state)
        if effect:
            try:
                effect.play()
            except Exception:
                pass

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
        """Append a styled message bubble to the chat history."""
        if sender == "You":
            bubble_bg = "#1e1b4b"
            text_color = COLORS["user_msg"]
            label_color = COLORS["text_muted"]
            align = "left"
        else:
            bubble_bg = "#0a2e1a"
            text_color = COLORS["assistant_msg"]
            label_color = COLORS["text_muted"]
            align = "left"

        html = (
            f'<div style="margin: 4px 0;">'
            f'<span style="color:{label_color}; font-size:11px; font-weight:600;">'
            f'{sender}</span><br>'
            f'<div style="background-color:{bubble_bg}; border-radius:10px; '
            f'padding:8px 12px; margin-top:2px; display:inline-block;">'
            f'<span style="color:{text_color}; font-size:13px;">{message}</span>'
            f'</div></div>'
        )
        self.chat_history.append(html)
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
            "dictating": "Dictating...",
            "error": "Error",
        }
        self.status_label.setText(state_display.get(state, state))

        # Update status label color based on state
        color = COLORS.get(state, COLORS["text_secondary"])
        self.status_label.setStyleSheet(
            f"color: {color}; font-family: {FONT_FAMILY}; font-size: 12px; "
            f"font-weight: 500; letter-spacing: 0.5px;"
        )

        # Play sound effect on state transitions
        if state != self._last_state:
            self._play_sound(state)
            self._last_state = state

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
