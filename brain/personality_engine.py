"""
Wednesday - Personality Engine
Generates natural, conversational responses instead of robotic output.
Makes Wednesday feel like a real assistant (Siri / Jarvis style).
"""

import random


# ---------------------------------------------------------------------------
# Conversational prefixes grouped by intent type
# ---------------------------------------------------------------------------

_ACKNOWLEDGE = [
    "Sure thing.",
    "Alright.",
    "Got it.",
    "On it.",
    "Right away.",
    "No problem.",
    "You got it.",
    "Absolutely.",
    "Of course.",
    "Sure.",
]

_WORKING = [
    "Working on it.",
    "Give me a moment.",
    "Let me handle that.",
    "One sec.",
    "Hang tight.",
]

_DONE = [
    "Done.",
    "All set.",
    "There you go.",
    "That's done.",
    "Finished.",
]

_GREETING = [
    "Yes?",
    "Hey! What can I do for you?",
    "I'm here.",
    "What's up?",
    "Listening.",
    "How can I help?",
]

_FAREWELL = [
    "Alright, going to sleep. Say Hey Wednesday when you need me.",
    "Okay, I'll be here if you need me. Just say Hey Wednesday.",
    "Going quiet. Wake me up anytime.",
]

_ERROR = [
    "Hmm, something went wrong.",
    "Sorry, I ran into an issue.",
    "That didn't work out.",
    "Oops, something failed.",
]

_CONFIRM_ASK = [
    "Are you sure you want to {action}? Say yes to confirm.",
    "Just to be safe — do you really want to {action}?",
    "I want to make sure: {action}? Yes or no?",
]

_THINKING = [
    "Let me think about that.",
    "Hmm, let me figure this out.",
    "Give me a moment to think.",
]


class PersonalityEngine:
    """Wraps skill responses in natural, conversational phrasing."""

    def style_response(self, raw_response: str, category: str = "action") -> str:
        """Add a conversational prefix/style to a raw skill response.

        Categories:
            action   - performing a task (open app, search, etc.)
            done     - task completed
            thinking - processing / AI query
            error    - something failed
            greeting - wake word detected
            farewell - sleep command
        """
        if category == "greeting":
            return random.choice(_GREETING)

        if category == "farewell":
            return random.choice(_FAREWELL)

        if category == "error":
            prefix = random.choice(_ERROR)
            return f"{prefix} {raw_response}"

        if category == "thinking":
            return raw_response  # AI responses are already natural

        if category == "done":
            prefix = random.choice(_DONE)
            return f"{prefix} {raw_response}" if raw_response else prefix

        # Default: action — prepend a friendly acknowledgement
        prefix = random.choice(_ACKNOWLEDGE)
        return f"{prefix} {raw_response}"

    def confirm_prompt(self, action_description: str) -> str:
        """Generate a natural confirmation prompt."""
        template = random.choice(_CONFIRM_ASK)
        return template.format(action=action_description)

    def working_message(self) -> str:
        """Return a short 'working on it' message."""
        return random.choice(_WORKING)
