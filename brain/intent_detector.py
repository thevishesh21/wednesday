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
    "file_action", "clipboard_action", "communication", "reminder",
    "screen_awareness", "dictation", "workflow", "contact",
    "chat",
}

INTENT_PROMPT = """\
You are an intent classifier for a Windows desktop AI assistant named Wednesday.

Classify the user command into ONE of these intents:

open_app          - Open or launch a desktop application (e.g. open Chrome, launch Notepad)
open_website      - Open a website or web service like YouTube, GitHub, Google
search_web        - Search for information on the internet
system_command    - System operation: shutdown, restart, sleep, lock, volume up/down, mute, brightness up/down, open task manager
file_action       - Create, open, delete, rename, or find a file or folder
clipboard_action  - Read, summarize, explain, rewrite, or translate clipboard contents
communication     - Send an email or message
reminder          - Set or list reminders
screen_awareness  - Describe, read, or analyze what is on the screen
dictation         - Start or stop voice typing / dictation mode
workflow          - Start a workflow or automation mode (e.g. work mode, study mode)
contact           - Find, add, remove, or list contacts; send email to a contact by name
chat              - General conversation, questions, or anything else

Return ONLY valid JSON with no extra text:
{"intent": "<intent>", "target": "<extracted object or null>"}

Examples:
User: open chrome                -> {"intent":"open_app","target":"chrome"}
User: open my browser            -> {"intent":"open_app","target":"chrome"}
User: open youtube               -> {"intent":"open_website","target":"youtube"}
User: search python tutorials    -> {"intent":"search_web","target":"python tutorials"}
User: search the internet for AI -> {"intent":"search_web","target":"AI"}
User: shutdown computer          -> {"intent":"system_command","target":"shutdown"}
User: increase the volume        -> {"intent":"system_command","target":"volume up"}
User: increase brightness        -> {"intent":"system_command","target":"brightness up"}
User: open task manager          -> {"intent":"system_command","target":"task manager"}
User: create file notes.txt      -> {"intent":"file_action","target":"create notes.txt"}
User: find my resume             -> {"intent":"file_action","target":"find resume"}
User: open downloads folder      -> {"intent":"file_action","target":"open_folder downloads"}
User: read my clipboard          -> {"intent":"clipboard_action","target":"read"}
User: explain this               -> {"intent":"clipboard_action","target":"explain"}
User: rewrite this               -> {"intent":"clipboard_action","target":"rewrite"}
User: translate this             -> {"intent":"clipboard_action","target":"translate"}
User: remind me to buy milk      -> {"intent":"reminder","target":"buy milk"}
User: list my reminders          -> {"intent":"reminder","target":"list"}
User: what is on my screen       -> {"intent":"screen_awareness","target":"describe"}
User: read the text on screen    -> {"intent":"screen_awareness","target":"read text"}
User: summarize this page        -> {"intent":"screen_awareness","target":"summarize"}
User: start dictation            -> {"intent":"dictation","target":"start"}
User: stop dictation             -> {"intent":"dictation","target":"stop"}
User: start work mode            -> {"intent":"workflow","target":"work mode"}
User: send email to john         -> {"intent":"contact","target":"email john"}
User: message mom                -> {"intent":"contact","target":"message mom"}
User: add contact sarah          -> {"intent":"contact","target":"add sarah"}
User: list contacts              -> {"intent":"contact","target":"list"}
User: what is machine learning   -> {"intent":"chat","target":null}"""

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

        # --- Screen awareness ---
        if any(p in lower for p in (
            "what is on my screen", "what's on my screen",
            "read the text on the screen", "read my screen",
            "summarize this page", "what website is this",
            "describe my screen", "look at my screen",
        )):
            return {"intent": "screen_awareness", "target": lower}

        # --- Dictation ---
        if lower in ("start dictation", "begin dictation", "dictation mode",
                      "start typing", "type for me"):
            return {"intent": "dictation", "target": "start"}
        if lower in ("stop dictation", "end dictation", "stop typing"):
            return {"intent": "dictation", "target": "stop"}

        # --- Workflows ---
        for keyword in ("work mode", "study mode", "chill mode"):
            if keyword in lower:
                return {"intent": "workflow", "target": keyword}

        # --- Contacts ---
        if lower.startswith("send email to "):
            name = lower[len("send email to "):].strip()
            return {"intent": "contact", "target": f"email {name}"}
        if lower.startswith("message "):
            name = lower[len("message "):].strip()
            return {"intent": "contact", "target": f"message {name}"}
        if lower == "list contacts" or lower == "show contacts":
            return {"intent": "contact", "target": "list"}

        # --- Clipboard quick-detect ---
        if lower in ("explain this", "explain clipboard"):
            return {"intent": "clipboard_action", "target": "explain"}
        if lower in ("rewrite this", "rewrite clipboard", "improve this"):
            return {"intent": "clipboard_action", "target": "rewrite"}
        if lower in ("translate this", "translate clipboard"):
            return {"intent": "clipboard_action", "target": "translate"}

        # --- System commands quick-detect ---
        if "brightness up" in lower or "increase brightness" in lower:
            return {"intent": "system_command", "target": "brightness up"}
        if "brightness down" in lower or "decrease brightness" in lower:
            return {"intent": "system_command", "target": "brightness down"}
        if lower in ("open task manager", "task manager"):
            return {"intent": "system_command", "target": "task manager"}

        # --- File quick-detect ---
        if lower.startswith("find ") or lower.startswith("find my "):
            target = lower.replace("find my ", "").replace("find ", "").strip()
            return {"intent": "file_action", "target": f"find {target}"}
        if "downloads folder" in lower or "open my downloads" in lower:
            return {"intent": "file_action", "target": "open_folder downloads"}
        if "documents folder" in lower or "open my documents" in lower:
            return {"intent": "file_action", "target": "open_folder documents"}
        if "desktop folder" in lower or "open my desktop" in lower:
            return {"intent": "file_action", "target": "open_folder desktop"}

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
        for prefix in ("search ", "google ", "search the internet for ",
                        "search internet for ", "look up "):
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
            error_msg = str(e)
            if "429" in error_msg or "insufficient_quota" in error_msg:
                logger.warning("[IntentDetector] API quota exceeded, falling back to chat.")
            else:
                logger.warning("[IntentDetector] AI classification failed: %s", e)
            return None
