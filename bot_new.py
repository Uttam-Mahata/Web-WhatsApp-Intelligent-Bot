"""
Main WhatsApp Gemini AI Bot orchestrator
"""
import time
from typing import Set, List, Optional
from config import Config
from models import BotStatus, BotStats, Message
from advanced_ai_client import AdvancedGeminiAIClient
from whatsapp_driver import WhatsAppDriver
from conversation_manager import ConversationManager
from message_processor import MessageProcessor

class WhatsAppGeminiBot:
    """Main bot class that orchestrates all components"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.config.validate()
        
        # Initialize components
        self.ai_client = AdvancedGeminiAIClient(self.config)
        self.whatsapp_driver = WhatsAppDriver(self.config)
        self.conversation_manager = ConversationManager(self.config)
        self.message_processor = MessageProcessor()
        
        # Bot state
        self.status = BotStatus(is_running=False)
        self.stats = BotStats()
        self.processed_messages: Set[str] = set()
    
    def initialize(self) -> bool:
        """Initialize the bot and login to WhatsApp"""
        try:
            print("Initializing WhatsApp Gemini AI Bot...")
            
            # Login to WhatsApp
            if not self.whatsapp_driver.login_whatsapp():
                print("Failed to login to WhatsApp")
                return False
            
            # Open target chat
            if not self.whatsapp_driver.open_chat(self.config.TARGET_CONTACT):
                print(f"Failed to open chat with {self.config.TARGET_CONTACT}")
                return False
            
            print("Bot initialized successfully!")
            return True
            
        except Exception as e:
            print(f"Error during initialization: {e}")
            return False
    
    def start_chat_session(self) -> None:
        """Start the main chat bot session"""
        print(f"Starting WhatsApp AI Chat Bot for {self.config.CHAT_DURATION_MINUTES} minutes...")
        print("The bot will respond to new messages using Gemini AI")
        
        # Update bot status
        self.status.is_running = True
        self.status.start_time = time.time()
        end_time = self.status.start_time + (self.config.CHAT_DURATION_MINUTES * 60)
        
        # Initialize message tracking
        self._initialize_message_tracking()
        
        # Send initial greeting
        self._send_initial_greeting()
        
        # Main chat loop
        self._run_chat_loop(end_time)
        
        # Update final status
        self.status.is_running = False
        self.status.end_time = time.time()
        self.stats.session_duration = self.status.end_time - self.status.start_time
        
        print("Chat bot session ended")
    
    def _initialize_message_tracking(self) -> None:
        """Initialize message tracking by getting existing messages"""
        initial_messages = self.whatsapp_driver.get_latest_messages()
        
        # Add all initial messages to processed set
        for msg in initial_messages:
            self.processed_messages.add(msg.text)
        
        print(f"Found {len(initial_messages)} existing messages in chat")
    
    def _send_initial_greeting(self) -> None:
        """Send initial greeting message"""
        try:
            greeting = self.ai_client.generate_response("Say hello briefly as an AI assistant")
            clean_greeting = self.message_processor.clean_text_for_whatsapp(greeting)
            
            if self.whatsapp_driver.send_message(clean_greeting):
                self.processed_messages.add(clean_greeting)
                self.conversation_manager.add_message(clean_greeting, role="assistant")
                self.stats.total_messages_sent += 1
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error sending initial greeting: {e}")
    
    def _run_chat_loop(self, end_time: float) -> None:
        """Main chat monitoring and response loop"""
        message_check_counter = 0
        
        while time.time() < end_time and self.status.is_running:
            try:
                # Check for new messages
                current_messages = self.whatsapp_driver.get_latest_messages()
                
                # Filter new incoming messages
                new_messages = self.message_processor.filter_new_messages(
                    current_messages, self.processed_messages
                )
                
                # Process each new message
                for msg in new_messages:
                    self._process_new_message(msg)
                
                # Update stats
                self.stats.total_messages_received += len(new_messages)
                
                # Sleep before next check
                time.sleep(self.config.CHECK_INTERVAL)
                
                # Periodic status update
                message_check_counter += 1
                if message_check_counter % 60 == 0:  # Every 30 seconds
                    self._log_status_update(len(current_messages))
                
            except KeyboardInterrupt:
                print("\nBot stopped by user")
                self.status.is_running = False
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                self.stats.total_errors += 1
                time.sleep(1)
    
    def _process_new_message(self, message: Message) -> None:
        """Process a single new message"""
        try:
            print(f"Received: {message.text}")
            
            # Add to processed set
            self.processed_messages.add(message.text)
            
            # Check if it's a context query first
            context_response = self.conversation_manager.handle_context_query(message.text)
            
            if context_response:
                response = context_response
                # Add to conversation history
                self.conversation_manager.add_message(message.text, role="user")
                self.conversation_manager.add_message(response, role="assistant")
            else:
                # Add user message to conversation
                self.conversation_manager.add_message(message.text, role="user")
                
                # Get conversation context
                context = self.conversation_manager.get_conversation_context()
                
                # Generate AI response
                response = self.ai_client.generate_response(message.text, context)
                
                # Add AI response to conversation
                self.conversation_manager.add_message(response, role="assistant")
            
            # Clean and validate response
            clean_response = self.message_processor.validate_response(
                response, self.config.MAX_RESPONSE_LENGTH
            )
            
            if clean_response:
                # Wait before responding
                time.sleep(self.config.RESPONSE_DELAY)
                
                # Send response
                if self.whatsapp_driver.send_message(clean_response):
                    self.processed_messages.add(clean_response)
                    self.stats.total_messages_sent += 1
                    print(f"✓ Responded to: {self.message_processor.truncate_message(message.text)}")
                else:
                    print("✗ Failed to send response")
                    self.stats.total_errors += 1
            else:
                print("✗ Generated response was invalid or empty")
                self.stats.total_errors += 1
            
            # Update last activity
            self.status.last_activity = time.time()
            
        except Exception as e:
            print(f"Error processing message: {e}")
            self.stats.total_errors += 1
    
    def _log_status_update(self, total_messages: int) -> None:
        """Log periodic status updates"""
        print(f"Monitoring... Messages: {total_messages}, "
              f"Processed: {len(self.processed_messages)}, "
              f"Sent: {self.stats.total_messages_sent}, "
              f"Errors: {self.stats.total_errors}")
    
    def stop(self) -> None:
        """Stop the bot"""
        self.status.is_running = False
        print("Bot stop requested")
    
    def get_status(self) -> BotStatus:
        """Get current bot status"""
        return self.status
    
    def get_stats(self) -> BotStats:
        """Get bot statistics"""
        return self.stats
    
    def show_conversation_history(self) -> None:
        """Display conversation history"""
        self.conversation_manager.display_conversation_history()
    
    def cleanup(self) -> None:
        """Clean up all resources"""
        try:
            self.whatsapp_driver.cleanup()
            print("Cleanup completed successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def is_healthy(self) -> bool:
        """Check if bot is healthy and running properly"""
        return (self.status.is_running and 
                self.whatsapp_driver.is_driver_alive() and
                self.ai_client.client is not None)
