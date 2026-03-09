"""
Wednesday - AI Brain
Handles all interactions with the OpenAI API.
"""

import logging

from openai import OpenAI
import config

logger = logging.getLogger("Wednesday")


SYSTEM_PROMPT = (
    "You are Wednesday, a helpful personal AI desktop assistant running on Windows. "
    "You answer questions concisely and helpfully. Keep responses short and spoken-friendly "
    "since your output will be read aloud via text-to-speech. "
    "If the user tells you personal facts (like their name), acknowledge them warmly. "
    "Do not use markdown formatting, bullet points, or code blocks in answers - "
    "speak naturally as a voice assistant would."
)


class AIBrain:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def ask(self, user_input: str, context: str = "") -> str:
        """Send a prompt to OpenAI and return the response text."""
        if context:
            message_content = f"[Context: {context}]\n{user_input}"
        else:
            message_content = user_input

        self.conversation_history.append(
            {"role": "user", "content": message_content}
        )

        # Keep conversation history manageable (last 20 messages + system)
        if len(self.conversation_history) > 21:
            self.conversation_history = (
                self.conversation_history[:1] + self.conversation_history[-20:]
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=300,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()
            self.conversation_history.append(
                {"role": "assistant", "content": reply}
            )
            return reply
        except Exception as e:
            error_message = str(e)
            logger.error("[AIBrain] OpenAI API error: %s", error_message)

            if "429" in error_message or "insufficient_quota" in error_message:
                return (
                    "Sorry, my AI brain is currently unavailable because "
                    "the API quota has been exceeded. Please try again later."
                )

            if "401" in error_message or "invalid_api_key" in error_message:
                return (
                    "Sorry, there is an issue with my API key configuration. "
                    "Please check the settings."
                )

            if "timeout" in error_message.lower() or "connection" in error_message.lower():
                return (
                    "Sorry, I could not reach my AI brain. "
                    "Please check your internet connection and try again."
                )

            return "Sorry, I had trouble contacting my AI brain. Please try again in a moment."

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
