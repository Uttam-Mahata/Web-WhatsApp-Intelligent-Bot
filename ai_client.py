"""
Gemini AI client handling for WhatsApp bot
"""
from google import genai
from typing import Optional, List
import time
from config import Config
from models import ConversationMessage

class GeminiAIClient:
    """Handles all Gemini AI interactions"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[genai.Client] = None
        self.system_instruction = config.SYSTEM_INSTRUCTION
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Gemini AI client"""
        try:
            self.client = genai.Client(api_key=self.config.GEMINI_API_KEY)
            print("Gemini AI client initialized successfully!")
        except Exception as e:
            print(f"Error initializing Gemini AI: {e}")
            raise
    
    def generate_response(self, user_message: str, conversation_context: str = "") -> str:
        """Generate AI response with context"""
        try:
            print(f"Generating AI response for: {user_message}")
            
            # Detect if user message contains Bengali
            has_bengali = self._detect_bengali(user_message)
            
            # Create context-aware prompt
            full_prompt = self._create_prompt(user_message, conversation_context, has_bengali)
            
            # Generate response using Gemini
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
            
            ai_response = response.text.strip()
            
            # Validate and clean response
            ai_response = self._clean_and_validate_response(ai_response, has_bengali)
            
            print(f"AI Response: {ai_response}")
            return ai_response
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self._get_fallback_response(user_message)
    
    def generate_simple_response(self, user_message: str, context: str = "") -> str:
        """Fallback method for simple response generation"""
        try:
            has_bengali = self._detect_bengali(user_message)
            
            if has_bengali:
                simple_prompt = f"""{context}
                User says: {user_message}
                Respond briefly in Bengali considering our conversation. No emojis."""
            else:
                simple_prompt = f"""{context}
                User says: {user_message}
                Respond briefly in English considering our conversation. No emojis."""
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=simple_prompt
            )
            
            ai_response = response.text.strip()
            ai_response = self._clean_response_text(ai_response)
            
            if not ai_response:
                return self._get_fallback_response(user_message)
            
            return ai_response[:self.config.MAX_RESPONSE_LENGTH]
            
        except Exception as e:
            print(f"Error in simple response generation: {e}")
            return self._get_fallback_response(user_message)
    
    def create_conversation_summary(self, conversation_history: List[ConversationMessage]) -> str:
        """Create a summary of the conversation"""
        if len(conversation_history) < 6:
            return ""
        
        try:
            # Prepare conversation text for summarization
            conversation_text = "\n".join([
                f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in conversation_history[:-2]  # Exclude last 2 messages
            ])
            
            summary_prompt = f"""Summarize this conversation in 1-2 sentences, focusing on key topics and context:
            
            {conversation_text}
            
            Summary:"""
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=summary_prompt
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error creating conversation summary: {e}")
            return ""
    
    def _detect_bengali(self, text: str) -> bool:
        """Detect if text contains Bengali characters"""
        bengali_chars = 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ'
        return any(char in text for char in bengali_chars)
    
    def _create_prompt(self, user_message: str, context: str, has_bengali: bool) -> str:
        """Create a context-aware prompt"""
        if has_bengali:
            return f"""{self.system_instruction}

{context}

Current user message: "{user_message}"

Respond naturally in Bengali, considering our conversation history.
Keep it brief (1-2 sentences), friendly, and contextually relevant.
No emojis or special symbols."""
        else:
            return f"""{self.system_instruction}

{context}

Current user message: "{user_message}"

Respond naturally in English, considering our conversation history.
Keep it brief (1-2 sentences), friendly, and contextually relevant.
No emojis or special symbols."""
    
    def _clean_and_validate_response(self, response: str, has_bengali: bool) -> str:
        """Clean and validate AI response"""
        # Clean the response
        response = self._clean_response_text(response)
        
        # Ensure response is not empty
        if not response or len(response.strip()) < 2:
            if has_bengali:
                response = "আমি বুঝতে পারছি।"
            else:
                response = "I understand."
        
        # Limit response length
        if len(response) > self.config.MAX_RESPONSE_LENGTH:
            response = response[:self.config.MAX_RESPONSE_LENGTH - 3] + "..."
        
        return response
    
    def _clean_response_text(self, text: str) -> str:
        """Remove emojis and non-BMP characters that cause ChromeDriver issues"""
        if not text:
            return ""
        
        # Remove emojis and other non-BMP characters
        import re
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
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Get fallback response when AI generation fails"""
        has_bengali = self._detect_bengali(user_message)
        if has_bengali:
            return "দুঃখিত, একটু সমস্যা হচ্ছে।"
        else:
            return "Sorry, having some trouble right now."
