"""
NestleBOT Chatbot - Azure OpenAI-based Assistant for Nestlé Canada

This module defines a FastAPI-compatible chatbot service that interacts with 
Azure OpenAI services to provide contextual answers about Nestlé products 
available in Canada. It uses chat history (user + assistant messages) 
for context retention and embeds basic prompt management and file-based history storage.

Author: Ishan Pansuriya
License: MIT
"""

import os
import json
from pathlib import Path
from collections import deque
from typing import List, Dict, Deque

from dotenv import load_dotenv
from fastapi import HTTPException
from openai import AzureOpenAI

# Load environment variables from .env
load_dotenv()

# Configuration for Azure OpenAI
AZURE_OPENAI_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT", "")
AZURE_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME", "gpt-4.1")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version=API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

class MessageHistory:
    """
    Manages the chat history to retain context over interactions with the assistant.
    Saves and loads history from a JSON file.
    """

    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.history: Deque[Dict] = deque(maxlen=max_messages)
        self.history_file = Path("./Scraped/chat_history.json")

    def add_message(self, role: str, content: str) -> None:
        """Adds a message to the history and saves it to disk."""
        self.history.append({"role": role, "content": content})
        self._trim_history()
        self._save_history()

    def get_history(self) -> List[Dict]:
        """Returns the message history."""
        return list(self.history)

    def clear_history(self) -> None:
        """Clears the message history."""
        self.history.clear()
        self._save_history()

    def _save_history(self) -> None:
        """Saves the message history to a JSON file."""
        with open(self.history_file, 'w') as f:
            json.dump(list(self.history), f)

    def load_history(self) -> None:
        """Loads history from a JSON file, if it exists."""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                history = json.load(f)
                self.history.extend(history[-self.max_messages:])

    def _trim_history(self):
        """Keeps only the latest 10 messages (5 user-assistant pairs)."""
        while len(self.history) > self.max_messages:
            self.history.popleft()


def generate_response(prompt: str, context_info: str = "") -> str:
    """
    Generates a response from the assistant based on the provided prompt and optional context.

    Args:
        prompt (str): The user question or instruction.
        context_info (str): Optional additional context to prepend.

    Returns:
        str: The assistant's reply.
    """
    try:
        message_history = MessageHistory(max_messages=10)
        message_history.load_history()

        user_input = f"Context: {context_info}\n\nQuestion: {prompt}" if context_info else prompt
        message_history.add_message("user", user_input)

        # System prompt to guide assistant behavior
        messages = [
            {
                "role": "system",
                "content": (
                    "You are NestleBOT, a digital assistant created to provide information "
                    "about Nestlé products available in Canada. Your purpose is to:\n"
                    "1. Offer details about product ingredients, features, and availability\n"
                    "2. Share approved recipes using Nestlé products\n"
                    "3. Provide general nutritional information\n"
                    "4. Maintain a friendly yet professional tone\n"
                    "5. Give concise responses (1-2 paragraphs maximum)\n"
                    "6. Always clarify when you don't have information\n\n"
                    "Important Rules:\n"
                    "- Never make claims about health benefits\n"
                    "- Direct users to official packaging for most accurate info\n"
                    "- Use Canadian product names and measurements\n"
                    "- When unsure, suggest contacting Nestlé Canada directly"
                )
            }
        ]

        messages.extend(message_history.get_history())

        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95
        )

        assistant_reply = response.choices[0].message.content
        message_history.add_message("assistant", assistant_reply)
        return assistant_reply

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


def generate_embeddings(text: str) -> list:
    """
    Generates text embeddings using Azure OpenAI.

    Args:
        text (str): The input text.

    Returns:
        list: Embedding vector.
    """
    try:
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_DEPLOYMENT
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        return []
