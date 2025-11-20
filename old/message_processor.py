"""
Message processing utilities
"""
import re
from typing import List, Set
from models import Message

class MessageProcessor:
    """Handles message processing and filtering"""
    
    @staticmethod
    def clean_text_for_whatsapp(text: str) -> str:
        """Remove emojis and non-BMP characters that cause ChromeDriver issues"""
        if not text:
            return ""
        
        # Remove emojis and other non-BMP characters
        text = re.sub(r'[^\x00-\x7F\u00A0-\uFFFF]', '', text)
        # Remove common emoji patterns
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # emoticons
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # symbols & pictographs
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # transport & map
        text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # flags
        text = re.sub(r'[\U00002702-\U000027B0]', '', text)  # dingbats
        text = re.sub(r'[\U000024C2-\U0001F251]', '', text)  # enclosed characters
        # Clean up extra spaces
        text = ' '.join(text.split())
        return text.strip()
    
    @staticmethod
    def is_typing_indicator(message_text: str) -> bool:
        """Check if message is a typing indicator"""
        return "typing" in message_text.lower() and "…" in message_text
    
    @staticmethod
    def should_skip_message(message_text: str) -> bool:
        """Determine if a message should be skipped"""
        if not message_text or len(message_text.strip()) < 2:
            return True
        
        if MessageProcessor.is_typing_indicator(message_text):
            return True
        
        # Skip system messages or notifications
        system_indicators = [
            "joined using this group's invite link",
            "left",
            "added",
            "removed",
            "changed the group description",
            "changed their phone number"
        ]
        
        return any(indicator in message_text.lower() for indicator in system_indicators)
    
    @staticmethod
    def filter_new_messages(current_messages: List[Message], processed_messages: Set[str]) -> List[Message]:
        """Filter out already processed messages and return only new incoming messages"""
        new_messages = []
        
        for msg in current_messages:
            # Only process truly new incoming messages
            if (msg.text not in processed_messages and 
                msg.is_incoming and 
                not MessageProcessor.should_skip_message(msg.text)):
                new_messages.append(msg)
        
        return new_messages
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect the language of the text (English or Bengali)"""
        bengali_chars = 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ'
        
        if any(char in text for char in bengali_chars):
            return "bengali"
        else:
            return "english"
    
    @staticmethod
    def truncate_message(message: str, max_length: int = 100) -> str:
        """Truncate message for display purposes"""
        if len(message) <= max_length:
            return message
        return message[:max_length] + "..."
    
    @staticmethod
    def validate_response(response: str, max_length: int = 400) -> str:
        """Validate and clean AI response"""
        if not response or len(response.strip()) < 2:
            return ""
        
        # Clean the response
        response = MessageProcessor.clean_text_for_whatsapp(response)
        
        # Limit response length
        if len(response) > max_length:
            response = response[:max_length - 3] + "..."
        
        return response
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Extract keywords from text for analysis"""
        # Simple keyword extraction - can be enhanced
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]  # Return top 10 keywords
