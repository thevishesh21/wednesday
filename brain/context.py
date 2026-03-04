"""
Wednesday - Context Manager
Extracts and stores personal facts from user input.
"""

import re


# Patterns that indicate the user is sharing a personal fact
FACT_PATTERNS = [
    (r"my name is (\w+)", "name"),
    (r"i am (\w+)", "name"),
    (r"call me (\w+)", "name"),
    (r"i live in (.+)", "location"),
    (r"i am from (.+)", "location"),
    (r"my favorite (.+?) is (.+)", None),  # handled specially
    (r"i like (.+)", "likes"),
    (r"i love (.+)", "loves"),
    (r"my age is (\d+)", "age"),
    (r"i am (\d+) years old", "age"),
    (r"my birthday is (.+)", "birthday"),
]

# Patterns that indicate the user is asking for a stored fact
RECALL_PATTERNS = [
    r"what is my (\w+)",
    r"what's my (\w+)",
    r"do you know my (\w+)",
    r"do you remember my (\w+)",
    r"who am i",
]


def extract_facts(text: str) -> dict:
    """Extract personal facts from user input. Returns dict of key->value."""
    facts = {}
    lower = text.lower().strip()

    for pattern, key in FACT_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            if key is None:
                # "my favorite X is Y"
                facts[f"favorite {match.group(1)}"] = match.group(2)
            else:
                facts[key] = match.group(1)

    return facts


def is_recall_query(text: str) -> str | None:
    """Check if user is asking about a stored fact. Returns the key or None."""
    lower = text.lower().strip()

    if "who am i" in lower:
        return "name"

    for pattern in RECALL_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            return match.group(1)

    return None
