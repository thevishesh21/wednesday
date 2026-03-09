"""
Wednesday - Task Parser
Breaks complex multi-step commands into individual tasks.
Example: "Open Chrome and search Python tutorials" → two tasks.
"""

import re
import logging

logger = logging.getLogger("Wednesday")

# Conjunctions / separators that split compound commands
_SPLIT_PATTERNS = [
    r"\band\s+then\b",
    r"\bthen\b",
    r"\bafter\s+that\b",
    r"\balso\b",
    r"\band\b",
]

# Compiled combined pattern
_SPLITTER = re.compile("|".join(_SPLIT_PATTERNS), re.IGNORECASE)


class TaskParser:
    """Splits a single user utterance into multiple sequential sub-commands."""

    def parse(self, text: str) -> list[str]:
        """Return a list of individual command strings.

        If the text contains conjunctions like 'and', 'then', etc. it will
        be split into multiple tasks. Single commands return a one-item list.
        """
        if not text or not text.strip():
            return []

        parts = _SPLITTER.split(text)
        tasks = [p.strip() for p in parts if p.strip()]

        # If splitting produced nothing useful, return the original
        if not tasks:
            tasks = [text.strip()]

        logger.info("[TaskParser] '%s' -> %d task(s): %s", text, len(tasks), tasks)
        return tasks
