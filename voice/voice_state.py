"""
WEDNESDAY AI OS — Voice State Machine
Tracks the current state of the voice pipeline.
"""

from core.logger import get_logger
from core.event_bus import event_bus

log = get_logger("voice.state")

class VoiceState:
    """Simple state machine for the voice pipeline."""
    
    STATES = ["idle", "wake_detected", "listening", "processing", "speaking"]
    
    def __init__(self):
        self._current = "idle"
        
        # Subscribe to relevant events to track state automatically
        event_bus.subscribe("voice.wake_detected", self._on_wake_detected)
        event_bus.subscribe("voice.transcript_ready", self._on_transcript_ready)
        event_bus.subscribe("voice.speaking_start", self._on_speaking_start)
        event_bus.subscribe("voice.speaking_end", self._on_speaking_end)
        event_bus.subscribe("agent.task_complete", self._on_task_complete)
        event_bus.subscribe("agent.error", self._on_error)
        
    @property
    def current(self) -> str:
        return self._current
        
    def _set_state(self, state: str) -> None:
        if state in self.STATES and state != self._current:
            log.debug(f"Voice state transition: {self._current} -> {state}")
            self._current = state
            event_bus.publish_nowait("system.state_changed", {"state": state})
            
    def _on_wake_detected(self, payload: dict) -> None:
        self._set_state("listening")
        
    def _on_transcript_ready(self, payload: dict) -> None:
        self._set_state("processing")
        
    def _on_speaking_start(self, payload: dict) -> None:
        self._set_state("speaking")
        
    def _on_speaking_end(self, payload: dict) -> None:
        self._set_state("idle")
        
    def _on_task_complete(self, payload: dict) -> None:
        # Agent task complete, return to idle if not speaking
        if self._current != "speaking":
            self._set_state("idle")
            
    def _on_error(self, payload: dict) -> None:
        # On error, return to idle if not speaking
        if self._current != "speaking":
            self._set_state("idle")

# Global instance
voice_state = VoiceState()
