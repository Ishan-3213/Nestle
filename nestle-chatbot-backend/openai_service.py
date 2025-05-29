import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from fastapi import HTTPException
from typing import List, Dict, Deque
from collections import deque
import json
from pathlib import Path

# Load environment variables
load_dotenv()

# Configuration
AZURE_OPENAI_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT", "https://c0903-mb86l1hp-eastus2.cognitiveservices.azure.com/")
AZURE_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME", "gpt-4.1")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")

# Initialize client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version=API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)
class MessageHistory:
    def __init__(self, max_messages: int = 3):
        self.max_messages = max_messages
        self.history: Deque[Dict] = deque(maxlen=max_messages)
        self.history_file = Path("./Scraped/chat_history.json")
        
    def add_message(self, role: str, content: str) -> None:
        """Add a message to history"""
        if self.history.__len____ >= self.max_messages:
            self.history.popleft()
        self.history.append({"role": role, "content": content})
        self._save_history()
    
    def get_history(self) -> List[Dict]:
        """Get message history as a list"""
        return list(self.history)
    
    def clear_history(self) -> None:
        """Clear the message history"""
        self.history.clear()
        self._save_history()
    
    def _save_history(self) -> None:
        """Save history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(list(self.history), f)
    
    def load_history(self) -> None:
        """Load history from file if exists"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                history = json.load(f)
                self.history.extend(history[-self.max_messages:])


def generate_response(prompt: str, context_info: str = "") -> str:
    try:
        message_history = MessageHistory(max_messages=3)
        message_history.load_history() 
        user_input = f"Context: {context_info}\n\nQuestion: {prompt}" if context_info else prompt
        message_history.add_message("user", user_input)

        messages = [
            {
  "role": "system",
  "content": "You are Smartie, a digital assistant created to provide information about Nestlé products available in Canada. Your purpose is to: \n\n1. Offer details about product ingredients, features, and availability \n2. Share approved recipes using Nestlé products \n3. Provide general nutritional information \n4. Maintain a friendly yet professional tone \n5. Give concise responses (1-2 paragraphs maximum) \n6. Always clarify when you don't have information \n\nImportant Rules:\n- Never make claims about health benefits\n- Direct users to official packaging for most accurate info\n- Use Canadian product names and measurements\n- When unsure, suggest contacting Nestlé Canada directly"
},
            {"role": "user", "content": user_input},
            message_history.get_history()
        ]

        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95
        )
        message_history.add_message("assistant", response)
        return response.choices[0].message.content

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

def generate_embeddings(text: str) -> list:
    try:
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_DEPLOYMENT
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        return []