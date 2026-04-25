"""
Wednesday AI Assistant — Fallback Engine
Rule-based response system when AI APIs are unavailable.
Pattern-matches common intents and returns step lists or spoken responses.
The assistant NEVER goes silent.
"""

import re
from utils.logger import get_logger

log = get_logger("fallback")

# ── Fallback patterns: (regex, response_func) ──────────────────
_PATTERNS = [
    # Time
    (r"(?:what|whats|what's)?\s*(?:the\s+)?time",
     lambda m: {"speak": _get_time()}),

    # Date
    (r"(?:what|whats|what's)?\s*(?:the\s+)?(?:date|day|today)",
     lambda m: {"speak": _get_date()}),

    # Who are you
    (r"(?:who are you|what are you|your name|naam kya hai)",
     lambda m: {"speak": "Main Wednesday hoon, aapki AI assistant! Aapki seva mein hazir, boss!"}),

    # How are you
    (r"(?:how are you|kaise ho|kaisi ho|kya haal)",
     lambda m: {"speak": "Main bilkul fit hoon, boss! Aap bataiye, kya help chahiye?"}),

    # Thank you
    (r"(?:thank|thanks|shukriya|dhanyawad)",
     lambda m: {"speak": "You're welcome, boss! Kabhi bhi bulao!"}),

    # Hello / Hi
    (r"(?:hello|hi|hey|namaste|namaskar)",
     lambda m: {"speak": "Hello boss! Kya haal hai? Kuch kaam hai?"}),
     
    # What is AI / General Knowledge prompt
    (r"(?:what is|who is|tell me about)\s+(.*)",
     lambda m: {"speak": f"Boss, agar main online hoti toh '{m.group(1)}' ke baare mein detail mein batati. Abhi meri internet se connection nahi ho paa rahi hai, par main aapke liye yeh Google par search kar sakti hoon. Bolenge toh search kar doongi!"}),

    # Joke
    (r"(?:tell me a joke|joke suna|joke sunao)",
     lambda m: {"speak": "Ek baar ek programmer se kisi ne poocha: 'Tumhare dost kahan hain?' Usne bola: 'Internet disconnect ho gaya, abhi koi dost nahi hai!' Haha!"}),

    # Open app (fallback if intent_router missed it)
    (r"(?:open|launch|start)\s+(.+)",
     lambda m: {"steps": [{"tool": "open_app", "args": {"name": m.group(1).strip()}}]}),

    # Search
    (r"(?:search|google)\s+(?:for\s+)?(.+)",
     lambda m: {"steps": [{"tool": "search_google", "args": {"query": m.group(1).strip()}}]}),
]


def fallback_response(command: str) -> dict:
    """
    Try to pattern-match the command and return a response.

    Returns:
        {"speak": "text"} — just speak something
        {"steps": [...]}  — execute these tool steps
        {"speak": "sorry..."} — no match found
    """
    command = command.lower().strip()

    for pattern, handler in _PATTERNS:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            result = handler(match)
            log.info(f"Fallback matched: {command} → {result}")
            return result

    log.info(f"Fallback: no pattern match for '{command}'")
    return {"speak": "Boss, main theek se samajh nahi paayi. Kya aap thoda alag tarike se bolenge?"}


def _get_time() -> str:
    """Get current time as a spoken string."""
    from datetime import datetime
    now = datetime.now()
    return f"Boss, abhi time hai {now.strftime('%I:%M %p')}"


def _get_date() -> str:
    """Get current date as a spoken string."""
    from datetime import datetime
    now = datetime.now()
    return f"Aaj {now.strftime('%A, %d %B %Y')} hai, boss."
