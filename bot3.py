from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from google import genai
from pydantic import BaseModel
import time
import re
import random

# Configuration
GEMINI_API_KEY = "AIzaSyATBM5NBOiJyrr8gNUbsU8H7jy37S3fEMg"  # Replace with your actual API key
TARGET_CONTACT = "Uttam"  # Change this to the name of your contact
CHAT_DURATION_MINUTES = 30  # How long to run the chat bot
MIN_RESPONSE_DELAY = 1  # Minimum seconds to wait before responding
MAX_RESPONSE_DELAY = 4  # Maximum seconds to wait before responding
CHECK_INTERVAL = 0.5  # How often to check for new messages

class ChatResponse(BaseModel):
    message: str
    language: str  # "english" or "bengali"
    emotion: str  # "happy", "neutral", "thoughtful", etc.
    typing_duration: float  # How long to "type" before sending

class WhatsAppGeminiBot:
    def __init__(self):
        self.setup_gemini()
        self.setup_webdriver()
        self.last_message_count = 0
        self.conversation_started = False
        
    def setup_gemini(self):
        """Initialize Gemini AI client with persistent chat session"""
        try:
            self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Create a persistent chat session
            self.chat = self.gemini_client.chats.create(
                model="gemini-2.0-flash",
                config={
                    "temperature": 0.8,  # Make responses more natural and varied
                    "max_output_tokens": 4096,  # Allow longer responses
                }
            )
            
            # Initialize the chat with personality and context
            initial_prompt = """You are chatting as a friendly, helpful human on WhatsApp. 

Key behaviors:
- Respond naturally like a real person, not an AI assistant
- Use casual, conversational language
- When someone asks for help or detailed information, provide comprehensive and useful responses
- Show personality - be friendly, sometimes playful
- Use appropriate reactions (agreement, surprise, curiosity)
- Ask follow-up questions naturally
- Respond in the same language as the user (English or Bengali)
- Never mention you're an AI or assistant
- Avoid formal language - be casual and natural
- Sometimes use common expressions and reactions
- Show interest in the conversation
- When providing examples (like email formats), give complete, detailed, and actually useful examples

Remember our conversation history and refer to it naturally when relevant."""

            # Send initial system message
            self.chat.send_message(initial_prompt)
            
            print("Gemini chat session initialized successfully!")
            
        except Exception as e:
            print(f"Error initializing Gemini AI: {e}")
            raise
    
    def setup_webdriver(self):
        """Initialize Chrome WebDriver with WhatsApp compatibility"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 60)
    
    def calculate_typing_delay(self, message):
        """Calculate realistic typing delay based on message length"""
        # Average typing speed: 40 words per minute = 0.67 words per second
        # Average word length: 5 characters
        # So roughly 3.35 characters per second
        
        char_count = len(message)
        base_typing_time = char_count / 3.5  # Slightly faster than average
        
        # Add some randomness and thinking time
        thinking_time = random.uniform(0.5, 2.0)  # Time to "think"
        typing_variation = random.uniform(0.8, 1.3)  # Typing speed variation
        
        total_delay = thinking_time + (base_typing_time * typing_variation)
        
        # Ensure reasonable bounds - increased max delay for longer messages
        return max(MIN_RESPONSE_DELAY, min(total_delay, 15))  # Increased from 4 to 15 seconds max
    
    def clean_text_for_whatsapp(self, text):
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
    
    def login_whatsapp(self):
        """Open WhatsApp Web and wait for QR code scan"""
        try:
            self.driver.get("https://web.whatsapp.com/")
            
            print("Please scan the QR code to login to WhatsApp Web...")
            print("Waiting for WhatsApp to load completely...")
            
            # Wait for WhatsApp to load completely with multiple fallback selectors
            search_selectors = [
                '//div[@contenteditable="true"][@data-tab="3"]',
                '//div[@role="textbox"][@title="Search input textbox"]',
                '//div[contains(@class, "x1hx0egp")][@contenteditable="true"]',
                '//div[@aria-label="Search input textbox"]'
            ]
            
            element_found = False
            for selector in search_selectors:
                try:
                    self.wait.until(ec.presence_of_element_located((By.XPATH, selector)))
                    element_found = True
                    break
                except:
                    continue
            
            if not element_found:
                print("Trying alternative login detection...")
                time.sleep(10)
                
            print("WhatsApp loaded successfully!")
            return True
            
        except Exception as e:
            print(f"Error logging into WhatsApp: {e}")
            return False
    
    def open_chat(self):
        """Search for and open the target contact's chat"""
        try:
            print(f"Looking for contact: {TARGET_CONTACT}")
            
            # Search for the contact
            search_box_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
            search_box = self.driver.find_element(By.XPATH, search_box_xpath)
            search_box.click()
            search_box.clear()
            search_box.send_keys(TARGET_CONTACT)
            time.sleep(1)
            
            # Click on the contact
            contact_xpath = f'//span[@title="{TARGET_CONTACT}"]'
            contact = self.wait.until(ec.element_to_be_clickable((By.XPATH, contact_xpath)))
            contact.click()
            
            print(f"Contact found and chat opened: {TARGET_CONTACT}")
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error opening chat: {e}")
            return False
    
    def get_message_input(self):
        """Find and return the message input box"""
        message_input_selectors = [
            '//div[@contenteditable="true"][@data-tab="10"][@role="textbox"]',
            '//div[@aria-label="Type a message"][@contenteditable="true"]',
            '//div[@contenteditable="true"][@role="textbox"][@spellcheck="true"]',
            '//div[contains(@class, "x1hx0egp")][@contenteditable="true"]',
            '//div[@data-lexical-editor="true"][@contenteditable="true"]',
        ]
        
        for selector in message_input_selectors:
            try:
                return self.driver.find_element(By.XPATH, selector)
            except:
                continue
        return None
    
    def simulate_typing(self, message):
        """Simulate realistic typing behavior"""
        typing_delay = self.calculate_typing_delay(message)
        
        print(f"Thinking and typing for {typing_delay:.1f} seconds...")
        
        # Split the delay into thinking time and typing time
        thinking_time = min(typing_delay * 0.4, 2.0)
        typing_time = typing_delay - thinking_time
        
        # Thinking pause
        time.sleep(thinking_time)
        
        # Simulate typing with small pauses
        if typing_time > 1:
            # For longer messages, simulate typing with multiple pauses
            pause_count = min(3, int(typing_time / 0.8))
            pause_duration = typing_time / (pause_count + 1)
            
            for i in range(pause_count):
                time.sleep(pause_duration)
                # Could add actual typing simulation here if needed
        else:
            time.sleep(typing_time)
    
    def send_message(self, message):
        """Send a message with realistic typing simulation"""
        try:
            # Clean the message
            clean_message = self.clean_text_for_whatsapp(message)
            
            if not clean_message:
                print("Message became empty after cleaning, using fallback")
                clean_message = "Sorry, had trouble with that message."
            
            # For very long messages, split them into multiple parts
            if len(clean_message) > 1000:
                parts = self.split_long_message(clean_message)
                for i, part in enumerate(parts):
                    if i > 0:
                        time.sleep(random.uniform(1, 2))  # Pause between parts
                    self.send_single_message(part)
                return True
            else:
                return self.send_single_message(clean_message)
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def split_long_message(self, message):
        """Split very long messages into reasonable chunks"""
        max_chunk_size = 1000
        if len(message) <= max_chunk_size:
            return [message]
        
        # Try to split at sentence boundaries
        sentences = message.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence + '. ') <= max_chunk_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def send_single_message(self, message):
        """Send a single message with realistic typing simulation"""
        try:
            # Simulate realistic typing delay
            self.simulate_typing(message)
            
            message_input = self.get_message_input()
            if not message_input:
                print("Could not find message input box")
                return False
            
            # Send the message
            message_input.click()
            message_input.clear()
            message_input.send_keys(message)
            message_input.send_keys(Keys.ENTER)
            
            print(f"Sent: {message}")
            return True
            
        except Exception as e:
            print(f"Error sending single message: {e}")
            return False
    
    def get_latest_messages(self):
        """Get the latest messages from the chat with sender info"""
        try:
            message_containers = []
            
            try:
                all_messages = self.driver.find_elements(By.XPATH, '//span[contains(@class, "_ao3e") and contains(@class, "selectable-text")]')
                
                if all_messages:
                    for elem in all_messages:
                        text = elem.text.strip()
                        if text:
                            try:
                                parent = elem.find_element(By.XPATH, './ancestor::div[contains(@class, "message-") or contains(@class, "_akbu")][1]')
                                parent_class = parent.get_attribute('class') or ''
                                
                                is_incoming = 'message-in' in parent_class or not ('message-out' in parent_class)
                                
                                message_containers.append({
                                    'text': text,
                                    'is_incoming': is_incoming,
                                    'timestamp': time.time()
                                })
                            except:
                                message_containers.append({
                                    'text': text,
                                    'is_incoming': True,
                                    'timestamp': time.time()
                                })
                                
            except Exception as e:
                print(f"Error in message detection: {e}")
            
            return message_containers
            
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def generate_greeting(self):
        """Generate a natural greeting based on time of day"""
        hour = time.localtime().tm_hour
        
        if 5 <= hour < 12:
            greetings = [
                "Good morning! How's it going?",
                "Morning! What's up?",
                "Hey! How are you doing today?",
                "Hi there! Hope you're having a good morning!",
                "সুপ্রভাত! কেমন আছেন?",  # Bengali good morning
                "হাই! আজকে কেমন যাচ্ছে?"  # Bengali how's today going
            ]
        elif 12 <= hour < 17:
            greetings = [
                "Good afternoon! How's your day?",
                "Hey! How are things going?",
                "Hi! What's happening?",
                "Afternoon! How's everything?",
                "হাই! দুপুরটা কেমন কাটছে?",  # Bengali afternoon greeting
                "শুভ অপরাহ্ন! কেমন আছেন?"  # Bengali good afternoon
            ]
        elif 17 <= hour < 21:
            greetings = [
                "Good evening! How was your day?",
                "Hey! How's the evening treating you?",
                "Hi there! How are you?",
                "Evening! What's up?",
                "শুভ সন্ধ্যা! দিনটা কেমন ছিল?",  # Bengali good evening
                "সন্ধ্যা হলো! কেমন আছেন?"  # Bengali evening greeting
            ]
        else:
            greetings = [
                "Hey! Still up?",
                "Hi there! How's the night going?",
                "Evening! What are you up to?",
                "Hey! Hope you're doing well!",
                "হাই! এখনো জেগে আছেন?",  # Bengali still awake
                "রাতটা কেমন কাটছে?"  # Bengali how's the night
            ]
        
        return random.choice(greetings)
    
    def generate_ai_response(self, user_message):
        """Generate AI response using persistent chat session"""
        try:
            print(f"Generating AI response for: {user_message}")
            
            # Add some context about natural conversation flow
            contextual_message = f"""User says: "{user_message}"

Respond naturally as a human would in a WhatsApp chat. Be conversational and engaging. When providing information like email formats, give complete, detailed examples that are actually useful. Don't worry about being brief if the user needs detailed information - provide full, comprehensive responses when helpful."""
            
            # Send message to the persistent chat session
            response = self.chat.send_message(contextual_message)
            ai_response = response.text.strip()
            
            # Clean and validate response
            ai_response = self.clean_text_for_whatsapp(ai_response)
            
            # Remove any AI-like phrases that might slip through
            ai_phrases_to_remove = [
                "as an ai", "i'm an ai", "as a language model", "i'm a chatbot",
                "i'm an assistant", "as your assistant", "i don't have personal",
                "i don't actually", "i can't actually", "i'm not able to"
            ]
            
            ai_response_lower = ai_response.lower()
            for phrase in ai_phrases_to_remove:
                if phrase in ai_response_lower:
                    # Generate a more natural fallback
                    return self.generate_fallback_response(user_message)
            
            # Ensure response is not empty and not too long
            if not ai_response or len(ai_response.strip()) < 2:
                return self.generate_fallback_response(user_message)
            
            if len(ai_response) > 1500:  # Increased from 300 to 1500 characters
                ai_response = ai_response[:1497] + "..."
            
            print(f"AI Response: {ai_response}")
            return ai_response
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self.generate_fallback_response(user_message)
    
    def generate_fallback_response(self, user_message):
        """Generate simple fallback responses when AI fails"""
        has_bengali = any(char in user_message for char in 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ')
        
        if has_bengali:
            fallbacks = [
                "হ্যাঁ, ঠিক বলেছেন।",
                "আমিও তাই মনে করি।",
                "ইন্টারেস্টিং!",
                "বুঝতে পারছি।",
                "হুম, সত্যি তো।",
                "একটু বুঝিয়ে বলুন তো?",
                "ও আচ্ছা।"
            ]
        else:
            fallbacks = [
                "That's interesting!",
                "I see what you mean.",
                "Really? Tell me more.",
                "That makes sense.",
                "Oh, I get it.",
                "Hmm, that's cool.",
                "Yeah, totally!",
                "What do you think about it?",
                "That's pretty neat."
            ]
        
        return random.choice(fallbacks)
    
    def start_chat_bot(self):
        """Main chat bot loop with human-like behavior"""
        print(f"Starting WhatsApp AI Chat Bot for {CHAT_DURATION_MINUTES} minutes...")
        print("The bot will respond naturally like a human using Gemini AI")
        
        start_time = time.time()
        end_time = start_time + (CHAT_DURATION_MINUTES * 60)
        
        # Get initial messages
        initial_messages = self.get_latest_messages()
        processed_messages = set()
        
        # Add all initial messages to processed set
        for msg in initial_messages:
            processed_messages.add(msg['text'])
        
        print(f"Found {len(initial_messages)} existing messages in chat")
        
        # Send natural greeting if no recent conversation
        if not self.conversation_started:
            greeting = self.generate_greeting()
            if self.send_message(greeting):
                processed_messages.add(greeting)
                self.conversation_started = True
        
        message_check_counter = 0
        
        while time.time() < end_time:
            try:
                current_messages = self.get_latest_messages()
                
                # Find new incoming messages
                new_messages = []
                for msg in current_messages:
                    if (msg['text'] not in processed_messages and msg['is_incoming']):
                        new_messages.append(msg)
                        processed_messages.add(msg['text'])
                
                # Process new messages with human-like delays
                for msg in new_messages:
                    message_text = msg['text']
                    print(f"Received: {message_text}")
                    
                    # Skip typing indicators
                    if "typing" in message_text.lower() and "…" in message_text:
                        print("Skipping typing indicator")
                        continue
                    
                    # Add small random delay before starting to respond (reading time)
                    reading_delay = random.uniform(0.3, 1.2)
                    time.sleep(reading_delay)
                    
                    # Generate response
                    ai_response = self.generate_ai_response(message_text)
                    
                    if ai_response and len(ai_response.strip()) > 1:
                        # Send response with typing simulation
                        if self.send_message(ai_response):
                            processed_messages.add(ai_response)
                            print(f"✓ Responded to: {message_text[:30]}...")
                        else:
                            print("✗ Failed to send response")
                    else:
                        print("✗ Generated response was invalid")
                
                time.sleep(CHECK_INTERVAL)
                
                message_check_counter += 1
                if message_check_counter % 60 == 0:
                    print(f"Monitoring... Messages: {len(current_messages)}, Processed: {len(processed_messages)}")
                
            except KeyboardInterrupt:
                print("\nBot stopped by user")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(2)
        
        print("Chat bot session ended")
    
    def show_chat_history(self):
        """Display the conversation history from Gemini chat"""
        print("\n" + "="*50)
        print("CONVERSATION HISTORY")
        print("="*50)
        
        try:
            history = self.chat.get_history()
            for message in history:
                role = "USER" if message.role == "user" else "AI"
                content = message.parts[0].text[:100] + ("..." if len(message.parts[0].text) > 100 else "")
                print(f"{role}: {content}")
                
        except Exception as e:
            print(f"Error getting chat history: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.driver.quit()
            print("Browser closed successfully")
        except:
            pass

# Main execution
def main():
    bot = None
    try:
        print("Initializing WhatsApp Gemini AI Bot...")
        bot = WhatsAppGeminiBot()
        
        if not bot.login_whatsapp():
            return
        
        if not bot.open_chat():
            return
        
        bot.start_chat_bot()
        bot.show_chat_history()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        print("Make sure you:")
        print("1. Have set your GEMINI_API_KEY correctly")
        print("2. Scanned the QR code properly")
        print("3. Have a stable internet connection")
        print("4. The contact name is spelled correctly")
        
    finally:
        if bot:
            bot.cleanup()

if __name__ == "__main__":
    main()