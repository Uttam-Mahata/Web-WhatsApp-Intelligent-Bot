"""
Package initialization for WhatsApp Gemini AI Bot
"""

# Version information
__version__ = "2.0.0"
__author__ = "WhatsApp Bot Team"
__description__ = "Modular WhatsApp AI Bot using Gemini"

# Import main classes for easy access
from .config import Config
from .models import ChatResponse, Message, ConversationMessage, BotStatus, BotStats
from .ai_client import GeminiAIClient
from .whatsapp_driver import WhatsAppDriver
from .conversation_manager import ConversationManager
from .message_processor import MessageProcessor
from .bot_new import WhatsAppGeminiBot

__all__ = [
    "Config",
    "ChatResponse",
    "Message", 
    "ConversationMessage",
    "BotStatus",
    "BotStats",
    "GeminiAIClient",
    "WhatsAppDriver",
    "ConversationManager",
    "MessageProcessor",
    "WhatsAppGeminiBot"
]
