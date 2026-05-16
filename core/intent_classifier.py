"""
core/intent_classifier.py
--------------------------
Lightweight intent classifier for Wednesday.

In Phase 1, this uses keyword matching + LLM classification.
In Phase 4+, this routes to the correct agent.

Intent categories:
  CONVERSATION   → regular chat/question (handled directly by LLM)
  SYSTEM_CMD     → open app, close app, volume, etc.     (Phase 2)
  BROWSER_CMD    → search web, open URL, browse          (Phase 2)
  FILE_CMD       → find/read/write files                 (Phase 3)
  MEMORY_CMD     → "remember this", "what did I say"     (Phase 3)
  VISION_CMD     → "what's on my screen", "read this"    (Phase 4)
  WORKFLOW       → multi-step autonomous task            (Phase 5)
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Intent:
    category: str = "CONVERSATION"
    confidence: float = 1.0
    action: Optional[str] = None      # Specific sub-action
    entities: dict = field(default_factory=dict)  # Extracted params
    raw_input: str = ""


# ── Keyword rules (fast, no LLM call needed) ──────────────────
_RULES: list[tuple[str, str, Optional[str]]] = [
    # (pattern, category, action)

    # System commands
    (r"\b(open|launch|start)\s+(\w+)", "SYSTEM_CMD", "open_app"),
    (r"\b(close|kill|quit|stop)\s+(\w+)", "SYSTEM_CMD", "close_app"),
    (r"\b(volume|mute|unmute|louder|quieter)", "SYSTEM_CMD", "volume"),
    (r"\b(shutdown|restart|sleep|hibernate)\b", "SYSTEM_CMD", "power"),
    (r"\b(take\s+a?\s*screenshot|capture\s+screen)\b", "SYSTEM_CMD", "screenshot"),
    (r"\b(what\s+time|current\s+time|what\s+day)\b", "SYSTEM_CMD", "time"),

    # Browser / web
    (r"\b(search|google|look\s+up|find)\s+.+\s+(on|online|web|internet)", "BROWSER_CMD", "web_search"),
    (r"\b(open|go\s+to)\s+(https?://\S+|www\.\S+)", "BROWSER_CMD", "open_url"),
    (r"\b(browse|navigate\s+to)\b", "BROWSER_CMD", "browse"),

    # Memory
    (r"\b(remember\s+this|save\s+this|don'?t\s+forget)\b", "MEMORY_CMD", "save"),
    (r"\b(what\s+did\s+(i|we)\s+say|recall|remind\s+me|what\s+do\s+you\s+know)\b", "MEMORY_CMD", "recall"),

    # Vision / screen
    (r"\b(what('?s)?\s+(on|in)\s+(my\s+)?(screen|display)|read\s+(this|the\s+screen))\b", "VISION_CMD", "describe_screen"),
    (r"\b(click|find)\s+(the\s+)?\w+\s+(button|link|icon)\b", "VISION_CMD", "find_element"),

    # Workflow
    (r"\b(every\s+(day|morning|hour)|schedule|remind\s+me\s+in)\b", "WORKFLOW", "schedule"),
    (r"\b(automate|do\s+this\s+(for\s+me|automatically)|every\s+time)\b", "WORKFLOW", "automate"),
]

_COMPILED_RULES = [(re.compile(p, re.IGNORECASE), cat, act) for p, cat, act in _RULES]


class IntentClassifier:
    """
    Fast rule-based intent classifier.

    Returns an Intent object. If category is CONVERSATION,
    the orchestrator handles it directly with the LLM.
    Otherwise, it routes to the appropriate agent.
    """

    def classify(self, text: str) -> Intent:
        """
        Classify the user's intent from their text.
        Currently keyword-based; LLM classification added in Phase 4.
        """
        if not text:
            return Intent(raw_input=text)

        text_lower = text.lower().strip()

        # ── Special commands ──────────────────────────────────
        if text_lower in ("/memory", "show memory", "show conversation"):
            return Intent(category="META", action="show_memory", raw_input=text)
        if text_lower in ("/clear", "clear memory", "forget everything"):
            return Intent(category="META", action="clear_memory", raw_input=text)
        if text_lower in ("/stats", "show stats", "your stats"):
            return Intent(category="META", action="show_stats", raw_input=text)

        # ── Keyword rule matching ─────────────────────────────
        for pattern, category, action in _COMPILED_RULES:
            match = pattern.search(text)
            if match:
                entities = {}
                try:
                    entities["match_groups"] = list(match.groups())
                except Exception:
                    pass

                intent = Intent(
                    category=category,
                    action=action,
                    entities=entities,
                    raw_input=text,
                    confidence=0.85,
                )
                logger.debug(
                    f"Intent: {category}/{action} (pattern match) "
                    f"— '{text[:40]}'"
                )
                return intent

        # ── Default: conversation ─────────────────────────────
        return Intent(
            category="CONVERSATION",
            action=None,
            raw_input=text,
            confidence=1.0,
        )
