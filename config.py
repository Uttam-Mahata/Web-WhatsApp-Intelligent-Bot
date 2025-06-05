"""
Configuration settings for WhatsApp Gemini AI Bot
"""
import os
from typing import Optional

class Config:
    """Configuration class for the WhatsApp bot"""
    
    # API Configuration
    GEMINI_API_KEY: str = "AIzaSyATBM5NBOiJyrr8gNUbsU8H7jy37S3fEMg"  # Replace with your actual API key
    
    # WhatsApp Configuration
    TARGET_CONTACT: str = "Uttam"  # Change this to the name of your contact
    
    # Bot Behavior Configuration
    CHAT_DURATION_MINUTES: int = 60  # How long to run the chat bot
    RESPONSE_DELAY: float = 0.5  # Seconds to wait before responding to messages
    CHECK_INTERVAL: float = 0.5  # How often to check for new messages
    
    # WebDriver Configuration
    WEBDRIVER_TIMEOUT: int = 60  # WebDriver timeout in seconds
    
    # Conversation Configuration
    MAX_CONVERSATION_HISTORY: int = 15  # Maximum messages to keep in history
    RECENT_MESSAGES_CONTEXT: int = 5  # Number of recent messages for context
    MAX_RESPONSE_LENGTH: int = 400  # Maximum AI response length
    
    # System Instructions
    SYSTEM_INSTRUCTION: str = """You are a friendly WhatsApp chatbot assistant. 
    Keep your responses conversational, brief (1-2 sentences), and natural.
    Remember our conversation context and refer to previous messages when relevant.
    Respond in the same language as the user (English or Bengali).
    No emojis or special symbols - only plain text.
    Be helpful, engaging, and maintain conversational flow."""
    
    @classmethod
    def load_from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        config = cls()
        config.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', config.GEMINI_API_KEY)
        config.TARGET_CONTACT = os.getenv('TARGET_CONTACT', config.TARGET_CONTACT)
        config.CHAT_DURATION_MINUTES = int(os.getenv('CHAT_DURATION_MINUTES', config.CHAT_DURATION_MINUTES))
        config.RESPONSE_DELAY = float(os.getenv('RESPONSE_DELAY', config.RESPONSE_DELAY))
        config.CHECK_INTERVAL = float(os.getenv('CHECK_INTERVAL', config.CHECK_INTERVAL))
        return config
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.GEMINI_API_KEY or self.GEMINI_API_KEY == "your_api_key_here":
            raise ValueError("GEMINI_API_KEY must be set")
        if not self.TARGET_CONTACT:
            raise ValueError("TARGET_CONTACT must be set")
        if self.CHAT_DURATION_MINUTES <= 0:
            raise ValueError("CHAT_DURATION_MINUTES must be positive")
        return True
