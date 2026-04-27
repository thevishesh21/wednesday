"""
WEDNESDAY AI OS — Context Manager
Manages the LLM conversation context window. Tracks message history and trims
oldest messages when approaching the token limit.
"""

from typing import List
from core.interfaces import LLMMessage
from core.logger import get_logger

log = get_logger("brain.context_manager")

class ContextManager:
    """Manages a rolling window of conversation history."""
    
    def __init__(self, system_prompt: str = ""):
        self._system_prompt = system_prompt
        self._messages: List[LLMMessage] = []
        if system_prompt:
            self._messages.append(LLMMessage(role="system", content=system_prompt))
            
    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the history."""
        self._messages.append(LLMMessage(role=role, content=content))
        
    def get_messages(self) -> List[LLMMessage]:
        """Return the current conversation history."""
        return list(self._messages)
        
    def clear(self) -> None:
        """Clear all messages except the system prompt."""
        self._messages = []
        if self._system_prompt:
            self._messages.append(LLMMessage(role="system", content=self._system_prompt))
        log.debug("Context history cleared")
            
    def token_estimate(self) -> int:
        """Rough estimate of total tokens (chars / 4)."""
        total_chars = sum(len(m.content) for m in self._messages)
        return total_chars // 4
        
    def trim(self, max_tokens: int = 4096) -> None:
        """
        Trim the oldest messages if the total token count exceeds max_tokens.
        Preserves the system prompt.
        """
        if self.token_estimate() <= max_tokens:
            return
            
        system_msg = None
        if self._messages and self._messages[0].role == "system":
            system_msg = self._messages.pop(0)
            
        # Keep removing oldest messages until under limit
        # Ensure we remove user/assistant pairs if possible
        while self._messages and self.token_estimate() > max_tokens:
            removed = self._messages.pop(0)
            log.debug(f"Trimmed old message (role: {removed.role})")
            
        if system_msg:
            self._messages.insert(0, system_msg)
            
        log.info(f"Context trimmed. Current estimate: {self.token_estimate()} tokens")
