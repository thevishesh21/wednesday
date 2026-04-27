"""
WEDNESDAY AI OS — Custom Exception Hierarchy
Every module raises typed exceptions from this file.
Never catch bare Exception — always catch the most specific type.

Hierarchy:
    WednesdayError
    ├── ConfigError
    ├── LLMError
    │   ├── LLMUnavailableError
    │   └── LLMResponseError
    ├── SkillError
    │   ├── ToolNotFoundError
    │   └── SkillExecutionError
    ├── VoiceError
    │   ├── STTError
    │   └── TTSError
    ├── AgentError
    │   ├── PlanningError
    │   └── StepExecutionError
    └── MemoryError
        ├── MemoryStoreError
        └── MemoryRetrieveError
"""


# ═════════════════════════════════════════════════════════════════
#  Base Exception
# ═════════════════════════════════════════════════════════════════

class WednesdayError(Exception):
    """
    Base exception for all WEDNESDAY AI OS errors.

    All custom exceptions inherit from this, allowing callers to catch
    either a specific type or any WEDNESDAY error with one clause.
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        """
        Args:
            message: Human-readable error description.
            details: Optional structured data for logging (e.g. tool name, step id).
        """
        super().__init__(message)
        self.message: str = message
        self.details: dict = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, details={self.details!r})"


# ═════════════════════════════════════════════════════════════════
#  Config Errors
# ═════════════════════════════════════════════════════════════════

class ConfigError(WednesdayError):
    """
    Raised when configuration values are missing, invalid, or out of range.

    Example:
        raise ConfigError("VOICE_RATE must be between 50 and 400",
                          details={"field": "VOICE_RATE", "value": -1})
    """


# ═════════════════════════════════════════════════════════════════
#  LLM Errors
# ═════════════════════════════════════════════════════════════════

class LLMError(WednesdayError):
    """Base class for all LLM-related errors."""


class LLMUnavailableError(LLMError):
    """
    Raised when no LLM backend is reachable.

    Example:
        raise LLMUnavailableError("Ollama is not running and no API keys configured")
    """


class LLMResponseError(LLMError):
    """
    Raised when the LLM returns an unparseable or unexpected response.

    Example:
        raise LLMResponseError("Expected JSON array, got plain text",
                               details={"raw": response[:200]})
    """


# ═════════════════════════════════════════════════════════════════
#  Skill Errors
# ═════════════════════════════════════════════════════════════════

class SkillError(WednesdayError):
    """Base class for skill execution errors."""


class ToolNotFoundError(SkillError):
    """
    Raised when a tool/skill name is not registered in the registry.

    Example:
        raise ToolNotFoundError("Skill 'fly_to_moon' is not registered",
                                details={"skill": "fly_to_moon"})
    """


class SkillExecutionError(SkillError):
    """
    Raised when a skill's execute() method fails.

    Example:
        raise SkillExecutionError("open_app failed: notepad not found",
                                  details={"skill": "open_app", "args": {"name": "notepad"}})
    """


# ═════════════════════════════════════════════════════════════════
#  Voice Errors
# ═════════════════════════════════════════════════════════════════

class VoiceError(WednesdayError):
    """Base class for voice pipeline errors."""


class STTError(VoiceError):
    """
    Raised when speech-to-text transcription fails.

    Example:
        raise STTError("faster-whisper model not loaded",
                       details={"model": "base", "audio_length_s": 3.2})
    """


class TTSError(VoiceError):
    """
    Raised when text-to-speech synthesis fails.

    Example:
        raise TTSError("Coqui XTTS engine failed to initialize")
    """


class WakeWordError(VoiceError):
    """
    Raised when the wake word detector encounters a fatal error.

    Example:
        raise WakeWordError("Porcupine API key invalid")
    """


# ═════════════════════════════════════════════════════════════════
#  Agent Errors
# ═════════════════════════════════════════════════════════════════

class AgentError(WednesdayError):
    """Base class for agent loop errors."""


class PlanningError(AgentError):
    """
    Raised when the task planner cannot produce a valid plan.

    Example:
        raise PlanningError("LLM returned empty step list for command",
                            details={"command": "do something impossible"})
    """


class StepExecutionError(AgentError):
    """
    Raised when a specific step in a task plan fails after all recovery attempts.

    Example:
        raise StepExecutionError("Step 2 failed after 2 retries",
                                 details={"step": 2, "tool": "open_app", "error": "not found"})
    """


# ═════════════════════════════════════════════════════════════════
#  Memory Errors
# ═════════════════════════════════════════════════════════════════

class MemoryError(WednesdayError):
    """Base class for memory system errors."""


class MemoryStoreError(MemoryError):
    """
    Raised when storing a memory record fails.

    Example:
        raise MemoryStoreError("ChromaDB write failed",
                               details={"content_length": 512})
    """


class MemoryRetrieveError(MemoryError):
    """
    Raised when semantic retrieval fails.

    Example:
        raise MemoryRetrieveError("Embedding model not loaded")
    """
