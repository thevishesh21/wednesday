"""
Wednesday - AI Intent Detector
Uses OpenAI to classify user commands into structured intents.
Includes fast rule-based shortcuts to reduce API calls.
"""

import json
import logging

from openai import OpenAI
import config

logger = logging.getLogger("Wednesday")

VALID_INTENTS = {
    "open_app", "open_website", "search_web", "system_command",
    "file_action", "clipboard_action", "communication", "reminder", "chat",
}

INTENT_PROMPT = """\
You are an intent classifier for a Windows desktop AI assistant.

Classify the user command into ONE of these intents:

open_app        - Open or launch a desktop application
open_website    - Open a website or web service like YouTube, GitHub, Google
search_web      - Search for information on the internet
system_command  - System operation: shutdown, restart, sleep, lock, volume up, volume down, mute
file_action     - Create, open, or delete a file
clipboard_action - Read or summarize clipboard contents
communication   - Send an email or message
reminder        - Set or list reminders
chat            - General conversation, questions, or anything else

Return ONLY valid JSON with no extra text:
{"intent": "<intent>", "target": "<extracted object or null>"}

Examples:
User: open chrome       -> {"intent":"open_app","target":"chrome"}
User: open youtube      -> {"intent":"open_website","target":"youtube"}
User: search python tutorials -> {"intent":"search_web","target":"python tutorials"}
User: shutdown computer -> {"intent":"system_command","target":"shutdown"}
User: increase the volume -> {"intent":"system_command","target":"volume up"}
User: create file notes.txt -> {"intent":"file_action","target":"create notes.txt"}
User: read my clipboard -> {"intent":"clipboard_action","target":"read"}
User: remind me to buy milk -> {"intent":"reminder","target":"buy milk"}
User: list my reminders -> {"intent":"reminder","target":"list"}
User: what is machine learning -> {"intent":"chat","target":null}"""

# Sites that should be routed as open_website, not open_app
KNOWN_WEBSITES = {
    "youtube", "github", "google", "facebook", "twitter", "reddit",
    "wikipedia", "stackoverflow", "instagram", "linkedin", "twitch",
    "netflix", "spotify", "amazon", "ebay", "pinterest", "tiktok",
    "whatsapp", "telegram", "medium", "quora",
}


class IntentDetector:
    """Classifies user commands into structured intents using AI."""

    def __init__(self, openai_client):
        self.client = openai_client
        self.model = config.OPENAI_MODEL

    def detect(self, command: str) -> dict:
        """Detect the intent of a user command.

        Returns {"intent": "...", "target": "..."}.
        Falls back to chat on any failure.
        """
        if not command or not command.strip():
            return {"intent": "chat", "target": None}

        # Try fast rule-based detection first (saves API calls)
        result = self._quick_detect(command)
        if result:
            logger.info("[IntentDetector] Quick: '%s' -> %s", command, result)
            return result

        # Fall back to AI classification
        result = self._ai_detect(command)
        if result:
            logger.info("[IntentDetector] AI: '%s' -> %s", command, result)
            return result

        # Failsafe: treat as chat
        logger.info("[IntentDetector] Fallback to chat for: '%s'", command)
        return {"intent": "chat", "target": None}

    def _quick_detect(self, command):
        """Fast rule-based shortcuts for obvious commands."""
        lower = command.lower().strip()

        # --- "open ..." / "launch ..." / "start ..." ---
        for prefix in ("open ", "launch ", "start "):
            if lower.startswith(prefix):
                target = lower[len(prefix):].strip()
                if not target:
                    return None
                # Known website or domain with a dot
                if target in KNOWN_WEBSITES or "." in target:
                    return {"intent": "open_website", "target": target}
                return {"intent": "open_app", "target": target}

        # --- "search ..." / "google ..." ---
        for prefix in ("search ", "google "):
            if lower.startswith(prefix):
                target = lower[len(prefix):].strip()
                # Strip trailing "on google"
                if target.endswith(" on google"):
                    target = target[:-10].strip()
                if target:
                    return {"intent": "search_web", "target": target}

        return None

    def _ai_detect(self, command):
        """Classify intent using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INTENT_PROMPT},
                    {"role": "user", "content": command},
                ],
                max_tokens=60,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)

            # Validate the intent
            intent = result.get("intent", "")
            if intent not in VALID_INTENTS:
                logger.warning("[IntentDetector] Invalid intent: '%s'", intent)
                return None

            return result
        except Exception as e:
            logger.warning("[IntentDetector] AI classification failed: %s", e)
            return None
