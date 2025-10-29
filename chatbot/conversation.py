import asyncio
import logging
from typing import TypedDict, Literal, Optional
from groq import Groq

client = Groq() # api key is retrieved from GROQ_API_KEY env var by default

ConversationMessage = TypedDict("ConversationMessage", {
    "role": Literal["system", "user", "assistant"],
    "content": str,
})

class Conversation():
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.messages: list[ConversationMessage] = [
            {
                "role": "system",
                "content": "You are Clanker, a chatbot that talks inside Valorant matches. Your tone should be casual, gamer-like, and conversational, as if you’re hanging out with teammates in voice or text chat. You should engage in banter, answer questions, and chat about the game or related topics in a fun way. Do not manipulate sequences of letters (for example, spelling words backwards or rearranging letters). Do not use emojis in your responses. Stay in-character as a Valorant teammate — conversational, sometimes witty, but never overly formal. Keep answers short to medium length, like something you’d actually say in a game chat.",
            }
        ]

        # keep track of the number messages from the most recent time the api was prompted to form a response
        # this way, we can have multiple concurrent "get_response()" calls, where only one will yield a response
        self.prev_messages_count: int = len(self.messages)

    def add_user_message(self, message: str):
        self.logger.info(f"Adding message '{message}'")

        self.messages.append({
            "role": "user",
            "content": message,
        })

    def get_response(self) -> Optional[str]:
        if self.prev_messages_count == len(self.messages): return

        response = client.chat.completions.create(
            messages=self.messages,
            model="openai/gpt-oss-20b",
        ).choices[0].message.content

        self.messages.append({
            "role": "assistant",
            "content": response,
        })
        self.prev_messages_count = len(self.messages)

        return response
