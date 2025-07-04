"""
Configuration settings for WhatsApp Gemini AI Bot
"""
import os
from typing import Optional

class Config:
    """Configuration class for the WhatsApp bot"""
    
    # API Configuration
    GEMINI_API_KEY: str = ""  # Loaded from environment variable
    
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
    MAX_RESPONSE_LENGTH: int = 4096  # Maximum AI response length
    
    # Advanced AI Features
    ENABLE_FUNCTION_CALLING: bool = True  # Enable function calling
    ENABLE_WEB_SEARCH: bool = True  # Enable web search capabilities
    ENABLE_GROUNDING: bool = True  # Enable Google Search grounding
    
    # Search Configuration
    SEARCH_TIMEOUT: int = 10  # Timeout for search operations
    MAX_SEARCH_RESULTS: int = 3  # Maximum search results to process
    
    # System Instructions
    SYSTEM_INSTRUCTION: str = """You are an advanced WhatsApp chatbot assistant with access to real-time information through Google Search and function calling capabilities.
    
    Key capabilities:
    - Use Google Search grounding to find current, accurate information
    - Call functions to get time, weather, and search for specific information
    - Provide factual, up-to-date responses based on real data
    - Be honest when you don't know something and use your tools to find answers
    
    Guidelines:
    - ALWAYS use search or functions when asked for information you don't immediately know
    - NEVER make vague promises - actually provide the requested information
    - If you can't find specific information, say so clearly with what you did find
    - Keep responses conversational but informative
    - Respond in the same language as the user (English or Bengali)
    - No emojis or special symbols - only plain text
    - When you find information through search or functions, present it clearly
    - Don't say you'll "get information" - actually get it and provide it"""
    
    @classmethod
    def load_from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        config = cls()
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        config.GEMINI_API_KEY = gemini_api_key
        config.TARGET_CONTACT = os.getenv('TARGET_CONTACT', config.TARGET_CONTACT)
        config.CHAT_DURATION_MINUTES = int(os.getenv('CHAT_DURATION_MINUTES', config.CHAT_DURATION_MINUTES))
        config.RESPONSE_DELAY = float(os.getenv('RESPONSE_DELAY', config.RESPONSE_DELAY))
        config.CHECK_INTERVAL = float(os.getenv('CHECK_INTERVAL', config.CHECK_INTERVAL))
        return config
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set")
        if not self.TARGET_CONTACT:
            raise ValueError("TARGET_CONTACT must be set")
        if self.CHAT_DURATION_MINUTES <= 0:
            raise ValueError("CHAT_DURATION_MINUTES must be positive")
        return True
