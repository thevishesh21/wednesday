"""
WEDNESDAY AI OS — Hinglish Normalizer
Translates Hinglish (Hindi in English script) to English commands.
Uses a fast rule-based path first, then LLM if needed.
"""

import re
from typing import Tuple

from core.logger import get_logger
from brain.llm_client import get_llm_client
from brain.prompt_templates import HINGLISH_NORMALIZER_PROMPT
from core.interfaces import LLMMessage

log = get_logger("voice.hinglish_normalizer")

# Simple rule-based transliterations for common commands
_RULES = {
    r"\b(khol de|khol do|kholo)\b": "open",
    r"\b(band kar|band karo|band kar de)\b": "close",
    r"\b(chala|chalao|chala de)\b": "play",
    r"\b(bata|batao|bata de)\b": "tell me",
    r"\b(le|lelo|le lo)\b": "take",
    r"\b(badha|badhao)\b": "increase",
    r"\b(ghata|ghataao)\b": "decrease",
    r"\b(on kar|on karo)\b": "turn on",
    r"\b(off kar|off karo)\b": "turn off",
    r"\b(dhundh|dhundo|dhoondho)\b": "search",
    r"\b(bhai|yaar|please)\b": "", # Filler words
    r"\b(kya|kaisa|kaun)\b": "what",
    r"\b(hai)\b": "is",
}

async def normalize(text: str) -> Tuple[str, bool]:
    """
    Normalize Hinglish input to clean English intent.
    
    Returns:
        (normalized_text, was_hinglish)
    """
    original_text = text.lower().strip()
    
    # ── 1. Fast Path (Regex) ──────────────────────────────────────
    normalized = original_text
    was_hinglish = False
    
    for pattern, replacement in _RULES.items():
        if re.search(pattern, normalized):
            was_hinglish = True
            normalized = re.sub(pattern, replacement, normalized)
            
    # Clean up extra spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()
    
    # If the text changed significantly, return the fast path result
    # (Checking if it changed isn't a perfect heuristic for "is this Hinglish",
    # but it's a good start for common commands)
    if was_hinglish and len(normalized) > 0:
        log.debug(f"Hinglish fast path: '{original_text}' -> '{normalized}'")
        return normalized, True

    # ── 2. LLM Path ───────────────────────────────────────────────
    # If it wasn't matched by our rules, but we suspect it might be Hinglish
    # (e.g., based on some heuristic, though for now we might just ask the LLM
    # if it's complex enough). For Phase 3, we'll just return the original text 
    # if it's simple, or let the intent parser handle it.
    
    # In a full implementation, we might call the LLM here to translate
    # complex Hinglish that our regex missed.
    # For now, to save latency, we only use the LLM path if specifically asked.
    
    # Let's add a basic heuristic: if it contains common Hindi words not in our rules
    hindi_keywords = ["mera", "tumhara", "kaise", "kahan", "kab", "kyun"]
    if any(k in original_text for k in hindi_keywords):
        try:
            llm = await get_llm_client()
            messages = [
                LLMMessage(role="system", content=HINGLISH_NORMALIZER_PROMPT),
                LLMMessage(role="user", content=original_text)
            ]
            response = await llm.chat(messages)
            translated = response.text.strip()
            log.debug(f"Hinglish LLM path: '{original_text}' -> '{translated}'")
            return translated, True
        except Exception as e:
            log.warning(f"Hinglish normalizer LLM fallback failed: {e}")
            
    return original_text, False
