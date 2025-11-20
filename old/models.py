"""
Data models and schemas for WhatsApp Gemini AI Bot
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatResponse(BaseModel):
    """Response model for chat messages"""
    message: str
    language: str  # "english" or "bengali"
    is_complete: bool

class Message(BaseModel):
    """Model for individual messages"""
    text: str
    is_incoming: bool
    timestamp: float
    
    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True

class ConversationMessage(BaseModel):
    """Model for conversation history messages"""
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: float
    
    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True

class BotStatus(BaseModel):
    """Model for bot status information"""
    is_running: bool
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    messages_processed: int = 0
    errors_count: int = 0
    last_activity: Optional[float] = None
    
class BotStats(BaseModel):
    """Model for bot statistics"""
    total_messages_received: int = 0
    total_messages_sent: int = 0
    total_errors: int = 0
    session_duration: float = 0.0
    average_response_time: float = 0.0
    languages_detected: Dict[str, int] = {}
    
    def add_language(self, language: str):
        """Add detected language to stats"""
        if language not in self.languages_detected:
            self.languages_detected[language] = 0
        self.languages_detected[language] += 1
