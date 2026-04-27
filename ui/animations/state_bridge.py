"""
WEDNESDAY AI OS — State Bridge
Connects the core event bus to the GUI.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from core.event_bus import event_bus
from core.logger import get_logger

log = get_logger("ui.state_bridge")

class UIStateBridge(QObject):
    """
    Subscribes to system events and translates them to GUI signals.
    """
    state_changed = pyqtSignal(str)
    message_received = pyqtSignal(str, str) # role, text
    
    _instance = None
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def __init__(self):
        super().__init__()
        # Subscribe to agent events
        event_bus.subscribe("agent.task_received", self._on_task_received)
        event_bus.subscribe("agent.step_started", self._on_step_started)
        event_bus.subscribe("agent.step_done", self._on_step_done)
        event_bus.subscribe("agent.task_complete", self._on_task_complete)
        event_bus.subscribe("agent.error", self._on_error)
        
        # We can also map old voice events to the new states
        event_bus.subscribe("voice.listening", lambda _: self.state_changed.emit("listening"))
        event_bus.subscribe("voice.processing", lambda _: self.state_changed.emit("thinking"))
        event_bus.subscribe("voice.speaking", lambda _: self.state_changed.emit("speaking"))
        event_bus.subscribe("voice.idle", lambda _: self.state_changed.emit("idle"))
        
    async def _on_task_received(self, data):
        self.state_changed.emit("thinking")
        
    async def _on_step_started(self, data):
        tool = data.get("tool", "")
        self.state_changed.emit("executing")
        self.message_received.emit("system", f"⚙️ Executing: {tool}")
        
    async def _on_step_done(self, data):
        self.state_changed.emit("complete")
        
    async def _on_task_complete(self, data):
        self.state_changed.emit("idle")
        
    async def _on_error(self, data):
        self.state_changed.emit("error")
        err = data.get("error", "Unknown error")
        self.message_received.emit("assistant", f"⚠️ Error: {err}")
