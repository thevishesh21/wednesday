"""
Wednesday AI Assistant — GUI ↔ Backend Signal Bridge
Thread-safe singleton that patches speak() to emit Qt signals,
allowing the GUI to display responses and track orb states.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class AssistantBridge(QObject):
    """
    Singleton bridge between backend functions and the GUI.

    Signals:
        assistant_spoke(str) — emitted whenever speak() is called
        state_changed(str)   — "listening" / "thinking" / "speaking" / "idle"
    """

    assistant_spoke = pyqtSignal(str)
    state_changed   = pyqtSignal(str)

    _instance = None
    _original_speak = None

    @classmethod
    def instance(cls):
        """Return (or create) the global bridge singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def patch_backend(self):
        """
        Monkey-patch speak() in both voice.speaker and main modules
        so every call also emits assistant_spoke + state_changed("speaking").
        Original TTS audio still plays.
        """
        import voice.speaker as sp_mod
        import main as main_mod

        self._original_speak = sp_mod.speak

        bridge = self  # capture for closure

        def _gui_speak(text: str):
            bridge.state_changed.emit("speaking")
            bridge.assistant_spoke.emit(text)
            bridge._original_speak(text)

        # Patch the name in both module namespaces
        sp_mod.speak = _gui_speak
        main_mod.speak = _gui_speak
