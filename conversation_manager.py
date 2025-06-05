"""
Conversation management and context handling
"""
from typing import List, Optional, Dict, Any
import time
from models import ConversationMessage
from config import Config

class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self, config: Config):
        self.config = config
        self.conversation_history: List[ConversationMessage] = []
    
    def add_message(self, content: str, role: str = "user") -> None:
        """Add message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=time.time()
        )
        self.conversation_history.append(message)
        
        # Manage conversation length
        if len(self.conversation_history) > self.config.MAX_CONVERSATION_HISTORY:
            self._summarize_and_trim()
    
    def _summarize_and_trim(self) -> None:
        """Summarize old conversation and keep recent messages"""
        # This would need AI client to create summary
        # For now, just keep recent messages
        recent_messages = self.conversation_history[-self.config.RECENT_MESSAGES_CONTEXT:]
        self.conversation_history = recent_messages
    
    def get_conversation_context(self) -> str:
        """Get formatted conversation context for AI responses"""
        if not self.conversation_history:
            return ""
        
        context = "\nRecent conversation:\n"
        for msg in self.conversation_history[-self.config.RECENT_MESSAGES_CONTEXT:]:
            role = "User" if msg.role == "user" else "You"
            context += f"{role}: {msg.content}\n"
        return context
    
    def handle_context_query(self, user_message: str) -> Optional[str]:
        """Handle queries about previous conversation"""
        context_keywords = [
            "what did i ask", "what was my question", "earlier", "before", "previous",
            "first question", "last question", "আগে", "প্রথম", "আগের", "কি জিজ্ঞেস",
            "কি প্রশ্ন", "er aage", "aage", "prothom", "jiggesh", "jiggsh"
        ]
        
        summary_keywords = [
            "summarize", "summary", "conversation", "chat", "talk", "discuss",
            "সামারি", "সারসংক্ষেপ", "আলোচনা", "কথাবার্তা"
        ]
        
        is_context_query = any(keyword in user_message.lower() for keyword in context_keywords)
        is_summary_query = any(keyword in user_message.lower() for keyword in summary_keywords)
        
        if is_summary_query and self.conversation_history:
            return self._create_conversation_summary(user_message)
        
        if is_context_query and self.conversation_history:
            return self._handle_previous_question_query(user_message)
        
        return None
    
    def _create_conversation_summary(self, user_message: str) -> str:
        """Create a summary of the conversation"""
        try:
            conversation_text = "\n".join([
                f"{'You' if msg.role == 'user' else 'I'}: {msg.content}"
                for msg in self.conversation_history[-10:]  # Last 10 messages
            ])
            
            has_bengali = self._detect_bengali(user_message)
            
            if has_bengali:
                return f"আমাদের কথোপকথনের মূল বিষয়গুলি: {conversation_text[:200]}..."
            else:
                return f"Our conversation summary: {conversation_text[:200]}..."
                
        except Exception as e:
            print(f"Error creating summary: {e}")
            return "Sorry, I couldn't create a summary right now."
    
    def _handle_previous_question_query(self, user_message: str) -> str:
        """Handle queries about previous questions"""
        user_messages = [msg for msg in self.conversation_history if msg.role == "user"]
        
        if len(user_messages) >= 2:  # Current + at least one previous
            if "first" in user_message.lower() or "প্রথম" in user_message or "prothom" in user_message:
                return f"Your first question was: '{user_messages[0].content}'"
            elif "last" in user_message.lower() or "আগের" in user_message or "aage" in user_message:
                return f"Your previous question was: '{user_messages[-2].content}'"
            else:
                return f"You asked: '{user_messages[-2].content}'"
        elif len(user_messages) == 1:
            return "This is your first message in our conversation."
        else:
            return "I don't have any previous questions in our conversation."
    
    def _detect_bengali(self, text: str) -> bool:
        """Detect if text contains Bengali characters"""
        bengali_chars = 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ'
        return any(char in text for char in bengali_chars)
    
    def get_conversation_history(self) -> List[ConversationMessage]:
        """Get the full conversation history"""
        return self.conversation_history.copy()
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        total_messages = len(self.conversation_history)
        user_messages = len([msg for msg in self.conversation_history if msg.role == "user"])
        ai_messages = len([msg for msg in self.conversation_history if msg.role == "assistant"])
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "ai_messages": ai_messages,
            "conversation_duration": (
                self.conversation_history[-1].timestamp - self.conversation_history[0].timestamp
                if self.conversation_history else 0
            )
        }
    
    def display_conversation_history(self) -> None:
        """Display the conversation history"""
        print("\n" + "="*50)
        print("CONVERSATION HISTORY")
        print("="*50)
        
        try:
            if self.conversation_history:
                for msg in self.conversation_history:
                    role = "USER" if msg.role == "user" else "AI"
                    content = msg.content[:100] + ("..." if len(msg.content) > 100 else "")
                    print(f"{role}: {content}")
            else:
                print("No conversation history available")
                
        except Exception as e:
            print(f"Error getting chat history: {e}")
