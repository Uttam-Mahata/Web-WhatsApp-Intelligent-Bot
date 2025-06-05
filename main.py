"""
Main entry point for WhatsApp Gemini AI Bot
"""
import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config import Config
from bot_new import WhatsAppGeminiBot

def main():
    """Main function to run the WhatsApp bot"""
    bot = None
    
    try:
        print("="*60)
        print("WhatsApp Gemini AI Bot - Modular Version")
        print("="*60)
        
        # Load configuration
        config = Config.load_from_env()
        print(f"Target Contact: {config.TARGET_CONTACT}")
        print(f"Chat Duration: {config.CHAT_DURATION_MINUTES} minutes")
        print(f"Response Delay: {config.RESPONSE_DELAY} seconds")
        
        # Initialize bot
        bot = WhatsAppGeminiBot(config)
        
        # Initialize WhatsApp connection
        if not bot.initialize():
            print("Failed to initialize bot. Exiting...")
            return
        
        # Start chat session
        bot.start_chat_session()
        
        # Show final statistics
        print("\n" + "="*50)
        print("SESSION SUMMARY")
        print("="*50)
        stats = bot.get_stats()
        print(f"Session Duration: {stats.session_duration:.1f} seconds")
        print(f"Messages Received: {stats.total_messages_received}")
        print(f"Messages Sent: {stats.total_messages_sent}")
        print(f"Total Errors: {stats.total_errors}")
        
        # Show conversation history
        bot.show_conversation_history()
        
    except KeyboardInterrupt:
        print("\n\nBot interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nMake sure you:")
        print("1. Have set your GEMINI_API_KEY correctly")
        print("2. Scanned the QR code properly")
        print("3. Have a stable internet connection")
        print("4. The contact name is spelled correctly")
        print("5. Chrome browser is installed and updated")
        
    finally:
        if bot:
            try:
                bot.cleanup()
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
        
        print("\nBot session ended. Thank you for using WhatsApp Gemini AI Bot!")

if __name__ == "__main__":
    main()
