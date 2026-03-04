"""
Wednesday - AI Brain
Handles all interactions with the OpenAI API.
"""

from openai import OpenAI
import config


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
            return f"Sorry, I encountered an error contacting OpenAI: {e}"

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
