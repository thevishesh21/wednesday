"""
WEDNESDAY AI OS — Abstract Interfaces + Core Data Classes
Defines the contracts every major component must fulfill.

The agent loop, brain, memory, voice, and skills are all wired together
through these interfaces — concrete implementations can be swapped
(Ollama ↔ OpenAI, ChromaDB ↔ flat JSON, pyttsx3 ↔ Coqui) without
changing any code that depends on them.

Usage:
    from core.interfaces import ILLMClient, ISkill, SkillResult, LLMMessage
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ═════════════════════════════════════════════════════════════════
#  Core Data Classes
# ═════════════════════════════════════════════════════════════════

@dataclass
class SkillResult:
    """
    The standard return type for every skill/tool execution.

    Attributes:
        success: True if the skill completed its task without error.
        result:  The output value (string message, dict, list, etc.).
        error:   Error message if success is False; None otherwise.
        tool:    Name of the skill that produced this result.
    """
    success: bool
    result: Any
    error: str | None
    tool: str

    @classmethod
    def ok(cls, tool: str, result: Any) -> "SkillResult":
        """Convenience constructor for a successful result."""
        return cls(success=True, result=result, error=None, tool=tool)

    @classmethod
    def fail(cls, tool: str, error: str) -> "SkillResult":
        """Convenience constructor for a failed result."""
        return cls(success=False, result=None, error=error, tool=tool)


@dataclass
class LLMMessage:
    """
    A single message in an LLM conversation.

    Attributes:
        role:    "system" | "user" | "assistant"
        content: The message text.
    """
    role: str
    content: str

    def to_dict(self) -> dict:
        """Serialize to the format expected by most LLM APIs."""
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """
    The standardized response from any LLM backend.

    Attributes:
        text:    The generated text content.
        model:   Which model produced the response (e.g. "mistral", "gpt-4o").
        tokens:  Approximate token count used.
        source:  Which backend answered: "ollama"|"openai"|"anthropic"|
                 "openrouter"|"huggingface"|"fallback".
        latency: Response time in seconds.
    """
    text: str
    model: str
    tokens: int
    source: str
    latency: float = 0.0


@dataclass
class ParsedIntent:
    """
    The result of intent parsing from the brain layer.

    Attributes:
        raw_text:   The original input text (pre-normalization).
        normalized: Text after Hinglish normalization.
        intent:     High-level intent label (e.g. "open_app", "search_web").
        entities:   Extracted parameters (e.g. {"app_name": "notepad"}).
        confidence: 0.0–1.0 confidence in the parse.
        hinglish:   True if the input contained Hinglish.
    """
    raw_text: str
    normalized: str
    intent: str
    entities: dict = field(default_factory=dict)
    confidence: float = 1.0
    hinglish: bool = False


@dataclass
class StepSchema:
    """
    A single executable step in a TaskPlan.

    Attributes:
        step_id:    1-indexed position in the plan.
        tool:       Registered skill name to execute.
        args:       Arguments for the skill (may reference {prev_output}).
        depends_on: List of step_ids whose output this step needs.
        output_key: Key under which to store this step's result for binding.
    """
    step_id: int
    tool: str
    args: dict = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)
    output_key: str = ""


@dataclass
class TaskPlan:
    """
    A complete, ordered execution plan produced by the task planner.

    Attributes:
        task_id:    UUID string identifying this task.
        raw_input:  Original user text (post-normalization).
        intent:     High-level intent label.
        steps:      Ordered list of StepSchema objects.
        memory_ctx: Relevant memories retrieved before planning.
        created_at: ISO 8601 timestamp string.
    """
    task_id: str
    raw_input: str
    intent: str
    steps: list[StepSchema] = field(default_factory=list)
    memory_ctx: list[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class MemoryRecord:
    """
    A single record stored in the long-term memory (ChromaDB).

    Attributes:
        id:        UUID string.
        content:   The text content being stored.
        metadata:  Dict with type, timestamp, task_id, etc.
        source:    Where this memory came from.
    """
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    source: str = "task_result"


# ═════════════════════════════════════════════════════════════════
#  Abstract Base Classes (Interfaces)
# ═════════════════════════════════════════════════════════════════

class ISkill(ABC):
    """
    Contract that every callable skill must implement.

    A Skill is an atomic capability WEDNESDAY can invoke (open an app,
    search the web, read the clipboard, etc.). The agent loop calls
    skills by name through the SkillRegistry.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique snake_case identifier for this skill (e.g. 'open_app')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """One-sentence description used in LLM function-call prompts."""

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        JSON Schema object describing the skill's parameters.

        Example:
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "App name"}
                },
                "required": ["name"]
            }
        """

    @abstractmethod
    def execute(self, **kwargs: Any) -> SkillResult:
        """
        Run the skill with the provided arguments.

        Args:
            **kwargs: Arguments matching the parameters schema.

        Returns:
            SkillResult with success/failure and result data.

        Raises:
            SkillExecutionError: On unrecoverable skill failure.
        """

    def to_llm_schema(self) -> dict:
        """
        Return an OpenAI-compatible function-call schema for this skill.

        This is what gets passed to the LLM so it knows how to call tools.

        Returns:
            Dict in the format:
            {"name": ..., "description": ..., "parameters": {...}}
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ILLMClient(ABC):
    """
    Contract for any LLM backend (Ollama, OpenAI, Anthropic, etc.).

    The brain layer calls this interface — the concrete implementation
    (which model/provider) is decided at runtime based on availability.
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """
        Send a conversation to the LLM and receive a response.

        Args:
            messages: Conversation history (system + user + assistant turns).
            tools:    Optional list of function-call schemas for tool use.

        Returns:
            LLMResponse with the generated text and metadata.

        Raises:
            LLMUnavailableError: If the backend cannot be reached.
            LLMResponseError:    If the response is malformed.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check whether this LLM backend is currently reachable.

        Returns:
            True if the backend responds to a health check; False otherwise.
        """


class IMemoryStore(ABC):
    """
    Contract for the long-term memory backend.

    The agent loop queries this before planning and stores outcomes after
    task completion. The concrete implementation uses ChromaDB + embeddings.
    """

    @abstractmethod
    async def store(self, content: str, metadata: dict | None = None) -> str:
        """
        Embed and store a text memory.

        Args:
            content:  The text to remember.
            metadata: Optional dict (type, task_id, timestamp, etc.).

        Returns:
            The unique ID of the stored memory record.

        Raises:
            MemoryStoreError: If the write fails.
        """

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> list[MemoryRecord]:
        """
        Retrieve the most semantically relevant memories for a query.

        Args:
            query:  The search string (embedded on the fly).
            top_k:  Maximum number of results to return.

        Returns:
            List of MemoryRecord objects, most relevant first.

        Raises:
            MemoryRetrieveError: If the query fails.
        """


class IVoiceSTT(ABC):
    """
    Contract for speech-to-text engines.

    Concrete implementations: faster-whisper (local), Google STT (fallback).
    """

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Convert raw audio bytes to a text string.

        Args:
            audio_bytes: Raw PCM audio data (16kHz, 16-bit, mono).

        Returns:
            Transcribed text string (lowercase, stripped).

        Raises:
            STTError: If transcription fails.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this STT engine is ready to use."""


class IVoiceTTS(ABC):
    """
    Contract for text-to-speech engines.

    Concrete implementations: Coqui XTTS v2 (primary), pyttsx3 (fallback).
    """

    @abstractmethod
    async def speak(self, text: str) -> None:
        """
        Synthesize and play the given text aloud.

        Args:
            text: The text to speak.

        Raises:
            TTSError: If synthesis or playback fails.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this TTS engine is ready to use."""


class IAgentLoop(ABC):
    """
    Contract for the autonomous agent execution loop.

    The agent loop drives the full UNDERSTAND→PLAN→EXECUTE→OBSERVE→IMPROVE
    cognitive cycle for every user command.
    """

    @abstractmethod
    async def handle(self, raw_input: str) -> None:
        """
        Process a single user command through the full agent cycle.

        Args:
            raw_input: The raw text from STT or text input (may be Hinglish).
        """

    @abstractmethod
    async def start(self) -> None:
        """Initialize and start the agent loop's background tasks."""

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down the agent loop."""
