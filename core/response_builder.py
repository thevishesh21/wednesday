"""
core/response_builder.py
-------------------------
Post-processes LLM responses before sending to the speaker.

Responsibilities:
  - Strip markdown formatting (voice can't say "*bold*")
  - Normalize whitespace
  - Truncate if too long for voice output
  - Handle special response codes (e.g., [ACTION:open_app:Chrome])
  - Add personality touches when appropriate
"""

import re
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Max chars before truncation for voice output
VOICE_MAX_CHARS = 600

# Markdown patterns to remove for clean speech
# Each entry: (pattern, replacement, flags)
_MARKDOWN_PATTERNS = [
    (r"\*\*(.+?)\*\*",          r"\1",   0),     # **bold** → bold
    (r"\*(.+?)\*",              r"\1",   0),     # *italic* → italic
    (r"__(.+?)__",              r"\1",   0),     # __bold__
    (r"`(.+?)`",                r"\1",   0),     # `code`
    (r"```[\s\S]+?```",         r"",     0),     # ```code blocks```
    (r"#{1,6}\s+",              r"",     0),     # ## headers
    (r"^\s*[-*+]\s+",           r"",     re.M),  # - bullet points
    (r"^\s*\d+\.\s+",           r"",     re.M),  # 1. numbered lists
    (r"\[([^\]]+)\]\([^)]+\)",  r"\1",   0),     # [text](url) → text
    (r"\n{3,}",                 r"\n\n", 0),     # Collapse excess newlines
]

# Compile all patterns — simple explicit loop, no clever unpacking
_COMPILED_MD = []
for _item in _MARKDOWN_PATTERNS:
    _pattern = _item[0]
    _replace = _item[1]
    _flags   = _item[2] if len(_item) > 2 else 0
    _COMPILED_MD.append((re.compile(_pattern, _flags), _replace))


class ResponseBuilder:
    """
    Cleans and prepares LLM responses for voice output.
    """

    def clean_for_voice(self, text: str) -> str:
        """
        Remove markdown, normalize text for text-to-speech.
        Returns clean, speakable text.
        """
        if not text:
            return ""

        result = text

        # Remove markdown
        for pattern, replacement in _COMPILED_MD:
            result = pattern.sub(replacement, result)

        # Normalize whitespace
        result = re.sub(r"[ \t]+", " ", result)
        result = result.strip()

        # Replace common symbols with spoken equivalents
        result = result.replace("&", "and")
        result = result.replace("%", " percent")
        result = result.replace("@", "at")
        result = result.replace("→", "to")
        result = result.replace("←", "from")
        result = result.replace("≈", "approximately")

        # Truncate for voice if too long
        if len(result) > VOICE_MAX_CHARS:
            truncated = result[:VOICE_MAX_CHARS]
            last_period = max(
                truncated.rfind(". "),
                truncated.rfind("! "),
                truncated.rfind("? "),
            )
            if last_period > VOICE_MAX_CHARS // 2:
                result = truncated[:last_period + 1]
                result += " I can elaborate further if you'd like."
            else:
                result = truncated.rsplit(" ", 1)[0] + "..."

            logger.debug("Response truncated for voice output.")

        return result

    def extract_action_tags(self, text: str) -> tuple:
        """
        Extract [ACTION:type:param] tags from LLM response.
        Used in Phase 4+ when LLM decides to call tools.

        Example:
            Input:  "Opening Chrome. [ACTION:open_app:chrome]"
            Output: ("Opening Chrome.", [{"type": "open_app", "param": "chrome"}])
        """
        actions = []
        pattern = re.compile(r"\[ACTION:([^:]+):([^\]]*)\]")
        for match in pattern.finditer(text):
            actions.append({"type": match.group(1), "param": match.group(2)})

        clean_text = pattern.sub("", text).strip()
        return clean_text, actions

    def format_for_display(self, text: str) -> str:
        """
        Format response for optional text display (not voice).
        Keeps markdown, just normalizes spacing.
        """
        return re.sub(r"\n{3,}", "\n\n", text).strip()
