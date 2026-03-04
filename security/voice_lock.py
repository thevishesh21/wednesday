"""
Wednesday - Voice Lock
Placeholder for voice-based authentication.
Currently always unlocked (authentication not enforced).
"""


class VoiceLock:
    def __init__(self):
        self._locked = False

    def is_locked(self) -> bool:
        return self._locked

    def lock(self):
        self._locked = True

    def unlock(self):
        self._locked = False
