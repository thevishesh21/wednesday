"""
WEDNESDAY AI OS — Hinglish Normalizer
Advanced rule-based + LLM fallback normalization for Hinglish commands.
"""

import re
from typing import Tuple, Dict, List, Optional
from core.logger import get_logger
from core.exceptions import WednesdayError
from brain.llm_client import get_llm_client

log = get_logger("voice.hinglish_normalizer")

class NormalizationError(WednesdayError):
    """Exception raised when normalization fails."""
    pass

class HinglishNormalizer:
    """
    Handles conversion of Hinglish (Hindi-English mix) commands into English intents.
    Uses a high-performance rule-based engine first, then falls back to LLM for ambiguity.
    """

    # Static map of common Hinglish patterns to English intents
    # Patterns use regex for flexibility
    RULES: Dict[str, str] = {
        r".*settings\s+(khol|open).*": "open settings",
        r".*music\s+(chala|play).*": "play my music",
        r".*bluetooth\s+(on|chalu).*": "turn on bluetooth",
        r".*files\s+(organize|samajh).*downloads.*": "organize files in Downloads folder",
        r".*weather\s+(bata|dikhao).*": "tell me today's weather",
        r".*(band|close)\s+kar.*": "close this",
        r".*screenshot\s+(le|khich).*": "take a screenshot",
        r".*volume\s+(badha|increase).*": "increase volume",
        r".*thoda\s+rest.*": "set do not disturb mode",
        r".*message\s+(aaya|check).*": "check my messages",
        r".*(khol|open)\s+de.*": "open", # Generic opener
    }

    def __init__(self):
        """Initialize the normalizer with rules and LLM fallback capabilities."""
        self._llm = None
        log.info("Hinglish Normalizer initialized with rules.")

    async def _get_llm(self):
        """Lazy load the LLM client."""
        if self._llm is None:
            self._llm = await get_llm_client()
        return self._llm

    async def normalize(self, text: str) -> Tuple[str, bool]:
        """
        Normalize the input text.

        Args:
            text: The raw input string from STT.

        Returns:
            A tuple of (normalized_text, was_hinglish_detected).

        Raises:
            NormalizationError: If the process fails critically.
        """
        raw_text = text.lower().strip()
        
        # 1. Check for Hinglish detection (simple heuristic)
        hinglish_markers = ["kar", "de", "khol", "bata", "yaar", "mera", "hoon", "chala"]
        was_hinglish = any(word in raw_text for word in hinglish_markers)

        # 2. Rule-based Fast Path
        for pattern, replacement in self.RULES.items():
            if re.match(pattern, raw_text):
                log.info(f"Rule match: '{raw_text}' -> '{replacement}'")
                return replacement, True

        # 3. LLM Fallback (only if Hinglish markers found and no rule matched)
        if was_hinglish:
            log.info(f"No rule match for Hinglish input: '{raw_text}'. Falling back to LLM.")
            llm_result = await self._llm_normalize(raw_text)
            return llm_result, True

        # 4. Pure English Pass-through
        return text, False

    async def _llm_normalize(self, text: str) -> str:
        """Use LLM to normalize complex or ambiguous Hinglish."""
        from core.interfaces import LLMMessage
        
        messages = [
            LLMMessage(role="system", content="Normalize Hinglish to English. Output only the English translation."),
            LLMMessage(role="user", content=f"Normalize: '{text}'")
        ]
        
        try:
            llm = await self._get_llm()
            response = await llm.chat(messages)
            normalized = response.text.strip().lower().replace('"', '')
            log.info(f"LLM normalized: '{text}' -> '{normalized}'")
            return normalized
        except Exception as e:
            log.error(f"LLM normalization failed: {e}")
            return text

# Global Singleton
hinglish_normalizer = HinglishNormalizer()
