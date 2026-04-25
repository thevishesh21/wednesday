"""
Wednesday AI Assistant — GUI Application
Main window, backend worker threads, voice listener with wake-word
support, and full signal wiring via AssistantBridge.

Advanced features:
  - WaveformWidget    → live audio-reactive bars when listening
  - FloatingOrb       → always-on-top mini orb (click to toggle)
  - CameraPreview     → webcam + hand tracking overlay
  - Human-like delay  → randomized thinking pause before response
"""

import random
import time
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy,
)
from PyQt6.QtCore import (
    Qt, QThread, QObject, pyqtSignal, pyqtSlot, QTimer,
)
from PyQt6.QtGui import QFont

from gui.theme import Colors, MAIN_STYLESHEET
from gui.components import (
    OrbWidget, StatusLabel, ChatPanel, InputBar, SidePanel,
)
from gui.animations import OrbAnimator
from gui.bridge import AssistantBridge
from gui.waveform import WaveformWidget
from gui.floating import FloatingOrb
from gui.camera_view import CameraPreview


# ═════════════════════════════════════════════════════════════════
#  Backend Worker — runs process_command with human-like delay
# ═════════════════════════════════════════════════════════════════

class BackendWorker(QObject):
    """Executes AI commands off the GUI thread."""

    state_changed = pyqtSignal(str)
    finished      = pyqtSignal()
    error         = pyqtSignal(str)

    @pyqtSlot(str)
    def process(self, command: str):
        try:
            self.state_changed.emit("thinking")

            # ── Human-like thinking delay (0.5–1.8s) ──
            delay = random.uniform(0.5, 1.8)
            time.sleep(delay)

            from main import process_command
            process_command(command)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.state_changed.emit("idle")
            self.finished.emit()


# ═════════════════════════════════════════════════════════════════
#  Listener Worker — full wake-word voice loop in background
# ═════════════════════════════════════════════════════════════════

class ListenerWorker(QObject):
    """
    Replicates the main.py voice loop in a QThread:
      listen → wake word check → greet → extract command → emit
    """

    command_ready = pyqtSignal(str)
    state_update  = pyqtSignal(str)
    user_spoke    = pyqtSignal(str)
    energy_level  = pyqtSignal(float)   # mic energy for waveform

    _NO_COMMAND = [
        "Boss, kuch suna nahi. Ek baar phir bolo na?",
        "Main sun rahi thi, par kuch catch nahi hua. Phir se boliye?",
    ]

    def __init__(self):
        super().__init__()
        self._active = False
        self._running = True

    def set_active(self, active: bool):
        self._active = active

    @pyqtSlot()
    def run(self):
        from voice.listener import listen
        from voice.wake_word import is_wake_word, strip_wake_word
        from voice.speaker import speak, greet
        from brain.conversation import update_interaction
        import speech_recognition as sr

        # Grab the global recognizer to read energy
        recognizer = sr.Recognizer()

        while self._running:
            if not self._active:
                QThread.msleep(200)
                continue

            # ── 1. Listen for any speech ──────────────────────
            self.state_update.emit("listening")

            # Emit energy levels during listening
            try:
                self.energy_level.emit(
                    min(1.0, recognizer.energy_threshold / 4000)
                )
            except Exception:
                self.energy_level.emit(0.3)

            text = listen()

            if not text:
                self.state_update.emit("idle")
                continue

            # ── 2. Check wake word ────────────────────────────
            if not is_wake_word(text):
                self.state_update.emit("idle")
                continue

            # Wake word detected!
            update_interaction()
            greet()

            command = strip_wake_word(text)

            # ── 3. If no command attached, ask and listen again
            if not command:
                speak("Bataiye boss, kya karna hai?")
                self.state_update.emit("listening")
                command = listen(timeout=8, phrase_limit=15)

            # ── 4. Emit command or give up ────────────────────
            if command:
                self.user_spoke.emit(command)
                self.command_ready.emit(command)
            else:
                speak(random.choice(self._NO_COMMAND))

            self.state_update.emit("idle")

    def stop(self):
        self._running = False
        self._active = False


# ═════════════════════════════════════════════════════════════════
#  Main Window
# ═════════════════════════════════════════════════════════════════

class WednesdayGUI(QMainWindow):
    """JARVIS-style main window with full backend integration."""

    _dispatch_command = pyqtSignal(str)

    def __init__(self):
        # Pre-init attributes that changeEvent may access during super().__init__
        self._floating = None
        self._camera = None

        super().__init__()
        self.setWindowTitle("WEDNESDAY — AI ASSISTANT")
        self.setMinimumSize(1060, 720)
        self.setStyleSheet(MAIN_STYLESHEET)

        self._current_state = "idle"
        self._processing = False

        self._bridge = AssistantBridge.instance()

        self._build_ui()
        self._build_floating_orb()
        self._build_camera_preview()
        self._setup_workers()
        self._connect_signals()

        self._animator.start()
        QTimer.singleShot(600, self._show_welcome)

    # ── UI layout ────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left: main content ──
        main_col = QVBoxLayout()
        main_col.setContentsMargins(20, 16, 10, 0)
        main_col.setSpacing(0)

        header = QLabel("W E D N E S D A Y")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; letter-spacing: 8px; padding: 6px;"
        )
        header.setFixedHeight(36)
        main_col.addWidget(header)

        # Orb
        self._orb = OrbWidget()
        self._orb.setFixedHeight(300)
        main_col.addWidget(self._orb)

        self._animator = OrbAnimator(self._orb)

        # Status label
        self._status = StatusLabel()
        self._status.setFixedHeight(32)
        main_col.addWidget(self._status)

        # ── Waveform (below status, above chat) ──
        self._waveform = WaveformWidget()
        main_col.addWidget(self._waveform)

        main_col.addSpacing(4)

        # Chat panel
        self._chat = ChatPanel()
        self._chat.setSizePolicy(QSizePolicy.Policy.Expanding,
                                 QSizePolicy.Policy.Expanding)
        main_col.addWidget(self._chat, stretch=1)

        # Input bar
        self._input = InputBar()
        main_col.addWidget(self._input)

        root.addLayout(main_col, stretch=1)

        # ── Right: side panel ──
        self._side = SidePanel()
        root.addWidget(self._side)

    def _build_floating_orb(self):
        """Create the always-on-top mini floating orb."""
        self._floating = FloatingOrb()
        # Position it at bottom-right of screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self._floating.move(geo.width() - 90, geo.height() - 90)
        self._floating.hide()  # hidden initially, toggled via minimize

    def _build_camera_preview(self):
        """Create the camera preview window (hidden by default)."""
        self._camera = CameraPreview()

    # ── worker threads ───────────────────────────────────────────

    def _setup_workers(self):
        # Backend worker (processes commands)
        self._backend = BackendWorker()
        self._backend_thread = QThread()
        self._backend.moveToThread(self._backend_thread)
        self._dispatch_command.connect(self._backend.process)
        self._backend_thread.start()

        # Listener worker (voice recognition + wake word)
        self._listener = ListenerWorker()
        self._listener_thread = QThread()
        self._listener.moveToThread(self._listener_thread)
        self._listener_thread.started.connect(self._listener.run)
        self._listener_thread.start()

    # ── signal wiring ────────────────────────────────────────────

    def _connect_signals(self):
        # Text input → process
        self._input.command_submitted.connect(self._on_text_command)

        # Backend worker → state + done
        self._backend.state_changed.connect(self._on_state_changed)
        self._backend.finished.connect(self._on_processing_done)
        self._backend.error.connect(self._on_error)

        # Bridge → chat panel  (speak() interception)
        self._bridge.assistant_spoke.connect(self._on_assistant_spoke)
        self._bridge.state_changed.connect(self._on_state_changed)

        # Voice listener → command + state + energy
        self._listener.command_ready.connect(self._on_voice_command)
        self._listener.user_spoke.connect(self._on_user_spoke)
        self._listener.state_update.connect(self._on_listener_state)
        self._listener.energy_level.connect(self._waveform.set_energy)

        # Side panel toggles
        self._side.voice_toggled.connect(self._toggle_voice)
        self._side.gesture_toggled.connect(self._toggle_gesture)
        self._side.safe_toggled.connect(self._toggle_safe)

        # Floating orb click → toggle main window
        self._floating.clicked.connect(self._toggle_main_window)

    # ── command slots ────────────────────────────────────────────

    def _show_welcome(self):
        self._chat.add_message(
            "assistant",
            "Hello boss! Wednesday is online.\n"
            "Type a command below, or enable Voice from the side panel. 🚀",
        )

    @pyqtSlot(str)
    def _on_text_command(self, text: str):
        """User typed a command in the input bar."""
        if self._processing:
            return
        self._processing = True
        self._input.set_enabled(False)
        self._chat.add_message("user", text)
        self._dispatch_command.emit(text)

    @pyqtSlot(str)
    def _on_voice_command(self, command: str):
        """Listener extracted a command after wake-word detection."""
        if self._processing:
            return
        self._processing = True
        self._input.set_enabled(False)
        self._dispatch_command.emit(command)

    @pyqtSlot(str)
    def _on_user_spoke(self, text: str):
        """Show the user's voice command in the chat panel."""
        self._chat.add_message("user", text)

    # ── state slots ──────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_state_changed(self, state: str):
        """Update orb + status + waveform + floating orb."""
        self._current_state = state
        self._animator.set_state(state)
        self._status.set_state(state)
        self._floating.set_state(state)

        # Waveform: active only when listening
        if state == "listening":
            self._waveform.set_active(True)
            self._waveform.set_color("listening")
        elif state == "speaking":
            self._waveform.set_active(True)
            self._waveform.set_color("speaking")
        else:
            self._waveform.set_active(False)

    @pyqtSlot()
    def _on_processing_done(self):
        """Backend finished processing a command."""
        self._processing = False
        self._input.set_enabled(True)
        if self._listener._active:
            self._on_state_changed("listening")
        else:
            self._on_state_changed("idle")

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        self._chat.add_message("assistant", f"⚠️ Error: {msg}")

    @pyqtSlot(str)
    def _on_assistant_spoke(self, text: str):
        """Backend called speak() → show text in chat."""
        self._chat.add_message("assistant", text)

    @pyqtSlot(str)
    def _on_listener_state(self, state: str):
        """Voice listener changed state (listening / idle)."""
        if not self._processing:
            self._on_state_changed(state)

    # ── side panel toggle handlers ───────────────────────────────

    def _toggle_voice(self, on: bool):
        self._listener.set_active(on)
        if on:
            self._chat.add_message(
                "assistant",
                "🎤 Voice input enabled! Say 'Hey Wednesday' to activate.",
            )
            self._on_state_changed("listening")
        else:
            self._chat.add_message("assistant", "🔇 Voice input disabled.")
            self._on_state_changed("idle")

    def _toggle_gesture(self, on: bool):
        try:
            from utils.thread_manager import thread_manager
            if on:
                thread_manager.start("gesture")
                self._camera.start()
                self._chat.add_message("assistant",
                                       "✋ Gesture control + camera enabled!")
            else:
                thread_manager.stop("gesture")
                self._camera.stop()
                self._chat.add_message("assistant",
                                       "✋ Gesture control disabled.")
        except Exception as e:
            self._chat.add_message("assistant", f"⚠️ Gesture error: {e}")

    def _toggle_safe(self, on: bool):
        import config
        config.SAFE_MODE = on
        mode = "ON" if on else "OFF"
        self._chat.add_message("assistant", f"🛡️ Safe Mode: {mode}")

    # ── floating orb toggle ──────────────────────────────────────

    def _toggle_main_window(self):
        """Click on floating orb → toggle main window visibility."""
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def changeEvent(self, event):
        """When minimized → show floating orb. When restored → hide it."""
        super().changeEvent(event)
        if self._floating is None:
            return
        if self.isMinimized():
            self._floating.show()
        else:
            self._floating.hide()

    # ── cleanup ──────────────────────────────────────────────────

    def closeEvent(self, event):
        self._animator.stop()
        if self._floating:
            self._floating.close()
        if self._camera:
            self._camera.stop()
        self._listener.stop()
        self._listener_thread.quit()
        self._listener_thread.wait(2000)
        self._backend_thread.quit()
        self._backend_thread.wait(2000)
        try:
            from utils.thread_manager import thread_manager
            thread_manager.stop_all()
        except Exception:
            pass
        event.accept()
