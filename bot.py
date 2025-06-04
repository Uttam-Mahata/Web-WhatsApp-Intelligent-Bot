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

# Configuration
GEMINI_API_KEY = "AIzaSyATBM5NBOiJyrr8gNUbsU8H7jy37S3fEMg"  # Replace with your actual API key
TARGET_CONTACT = "Uttam"  # Change this to the name of your contact
CHAT_DURATION_MINUTES = 30  # How long to run the chat bot
RESPONSE_DELAY = 0.5  # Seconds to wait before responding to messages (reduced from 2)
CHECK_INTERVAL = 0.5  # How often to check for new messages (reduced from 2)

class ChatResponse(BaseModel):
    message: str
    language: str  # "english" or "bengali"
    is_complete: bool

class WhatsAppGeminiBot:
    def __init__(self):
        self.setup_gemini()
        self.setup_webdriver()
        self.last_message_count = 0
        self.conversation_history = []  # Track conversation for context
        
    def setup_gemini(self):
        """Initialize Gemini AI client with system instructions"""
        try:
            self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Define system instructions for the model
            self.system_instruction = """You are a friendly WhatsApp chatbot assistant. 
            Keep your responses conversational, brief (1-2 sentences), and natural.
            Remember our conversation context and refer to previous messages when relevant.
            Respond in the same language as the user (English or Bengali).
            No emojis or special symbols - only plain text.
            Be helpful, engaging, and maintain conversational flow."""
            
            # Store chat history for maintaining context
            self.chat_history = []
            
            print("Gemini AI client initialized successfully!")
            
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
        self.wait = WebDriverWait(self.driver, 60)  # Increased timeout to 60 seconds
    
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
                # Alternative: wait for the main WhatsApp interface
                time.sleep(10)
                
            print("WhatsApp loaded successfully!")
            return True
            
        except Exception as e:
            print(f"Error logging into WhatsApp: {e}")
            print("Please make sure to scan the QR code quickly and have a stable internet connection.")
            return False
    
    def open_chat(self):
        """Search for and open the target contact's chat - optimized"""
        try:
            print(f"Looking for contact: {TARGET_CONTACT}")
            
            # Search for the contact
            search_box_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
            search_box = self.driver.find_element(By.XPATH, search_box_xpath)
            search_box.click()
            search_box.clear()
            search_box.send_keys(TARGET_CONTACT)
            time.sleep(1)  # Reduced from 2 seconds
            
            # Click on the contact
            contact_xpath = f'//span[@title="{TARGET_CONTACT}"]'
            contact = self.wait.until(ec.element_to_be_clickable((By.XPATH, contact_xpath)))
            contact.click()
            
            print(f"Contact found and chat opened: {TARGET_CONTACT}")
            time.sleep(1)  # Reduced from 3 seconds
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
    
    def send_message(self, message):
        """Send a message in the current chat - with emoji filtering"""
        try:
            # Clean the message to remove problematic characters
            clean_message = self.clean_text_for_whatsapp(message)
            
            if not clean_message:
                print("Message became empty after cleaning, using fallback")
                clean_message = "Sorry, had trouble with that message."
            
            message_input = self.get_message_input()
            if not message_input:
                print("Could not find message input box")
                return False
            
            # Send the cleaned message
            message_input.click()
            message_input.clear()
            message_input.send_keys(clean_message)
            message_input.send_keys(Keys.ENTER)
            
            print(f"Sent: {clean_message}")
            return True
            
        except Exception as e:
            print(f"Error sending message: {e}")
            # Try sending a simple fallback message
            try:
                message_input = self.get_message_input()
                if message_input:
                    message_input.click()
                    message_input.clear()
                    message_input.send_keys("Sorry, having trouble responding right now.")
                    message_input.send_keys(Keys.ENTER)
                    print("Sent fallback message")
                    return True
            except:
                pass
            return False
    
    def get_latest_messages(self):
        """Get the latest messages from the chat with sender info - optimized"""
        try:
            message_containers = []
            
            # Use the most reliable selector first for speed
            try:
                # Try the most common WhatsApp message selector
                all_messages = self.driver.find_elements(By.XPATH, '//span[contains(@class, "_ao3e") and contains(@class, "selectable-text")]')
                
                if all_messages:
                    # Get parent containers to check message direction
                    for elem in all_messages:
                        text = elem.text.strip()
                        if text:
                            try:
                                # Check if message is incoming by looking at parent classes
                                parent = elem.find_element(By.XPATH, './ancestor::div[contains(@class, "message-") or contains(@class, "_akbu")][1]')
                                parent_class = parent.get_attribute('class') or ''
                                
                                # Determine if incoming (from other person) or outgoing (from bot)
                                is_incoming = 'message-in' in parent_class or not ('message-out' in parent_class)
                                
                                message_containers.append({
                                    'text': text,
                                    'is_incoming': is_incoming,
                                    'timestamp': time.time()
                                })
                            except:
                                # If we can't determine direction, assume it's incoming
                                message_containers.append({
                                    'text': text,
                                    'is_incoming': True,
                                    'timestamp': time.time()
                                })
                                
            except Exception as e:
                print(f"Error in optimized message detection: {e}")
            
            return message_containers
            
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def add_to_conversation_history(self, message, is_user=True):
        """Add message to conversation history for context tracking"""
        role = "user" if is_user else "assistant"
        self.conversation_history.append({
            "role": role,
            "content": message,
            "timestamp": time.time()
        })
        
        # When conversation gets too long, summarize and keep recent messages
        if len(self.conversation_history) > 15:
            summary = self.summarize_conversation()
            # Keep summary and last 5 messages
            recent_messages = self.conversation_history[-5:]
            self.conversation_history = []
            
            if summary:
                self.conversation_history.append({
                    "role": "system",
                    "content": f"Previous conversation summary: {summary}",
                    "timestamp": time.time()
                })
            
            self.conversation_history.extend(recent_messages)
    
    def get_conversation_context(self):
        """Get formatted conversation context for better responses"""
        if not self.conversation_history:
            return ""
        
        context = "\nRecent conversation:\n"
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            role = "User" if msg["role"] == "user" else "You"
            context += f"{role}: {msg['content']}\n"
        return context
    
    def handle_context_query(self, user_message):
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
            # Create a conversation summary
            try:
                conversation_text = "\n".join([
                    f"{'You' if msg['role'] == 'user' else 'I'}: {msg['content']}"
                    for msg in self.conversation_history[-10:]  # Last 10 messages
                ])
                
                has_bengali = any(char in user_message for char in 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ')
                
                if has_bengali:
                    summary_prompt = f"""আমাদের কথোপকথনের সংক্ষিপ্ত সারাংশ দাও:

{conversation_text}

বাংলায় ২-৩ বাক্যে উত্তর দাও।"""
                else:
                    summary_prompt = f"""Summarize our conversation briefly:

{conversation_text}

Respond in 2-3 sentences."""
                
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=summary_prompt
                )
                
                return self.clean_text_for_whatsapp(response.text.strip())
            except Exception as e:
                print(f"Error creating summary: {e}")
                return "Sorry, I couldn't create a summary right now."
        
        if is_context_query and self.conversation_history:
            # Find user's previous questions
            user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
            
            if len(user_messages) >= 2:  # Current + at least one previous
                if "first" in user_message.lower() or "প্রথম" in user_message or "prothom" in user_message:
                    return f"Your first question was: '{user_messages[0]['content']}'"
                elif "last" in user_message.lower() or "আগের" in user_message or "aage" in user_message:
                    return f"Your previous question was: '{user_messages[-2]['content']}'"
                else:
                    return f"You asked: '{user_messages[-2]['content']}'"
            elif len(user_messages) == 1:
                return "This is your first message in our conversation."
        
        return None  # Not a context query or no context available
    
    def summarize_conversation(self):
        """Create a summary of the conversation to maintain long-term context"""
        if len(self.conversation_history) < 6:
            return ""
        
        try:
            # Get conversation summary from Gemini
            conversation_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in self.conversation_history[:-2]  # Exclude last 2 messages
            ])
            
            summary_prompt = f"""Summarize this conversation in 1-2 sentences, focusing on key topics and context:
            
            {conversation_text}
            
            Summary:"""
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=summary_prompt
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error creating conversation summary: {e}")
            return ""
    
    def generate_ai_response(self, user_message):
        """Generate AI response using Gemini with context"""
        try:
            print(f"Generating AI response for: {user_message}")
            
            # Check if this is a context query first
            context_response = self.handle_context_query(user_message)
            if context_response:
                self.add_to_conversation_history(user_message, is_user=True)
                self.add_to_conversation_history(context_response, is_user=False)
                print(f"Context AI Response: {context_response}")
                return context_response
            
            # Add user message to conversation history
            self.add_to_conversation_history(user_message, is_user=True)
            
            # Detect if user message contains Bengali
            has_bengali = any(char in user_message for char in 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ')
            
            # Create context-aware prompt with system instruction and conversation history
            context = self.get_conversation_context()
            
            if has_bengali:
                full_prompt = f"""{self.system_instruction}

{context}

Current user message: "{user_message}"

Respond naturally in Bengali, considering our conversation history.
Keep it brief (1-2 sentences), friendly, and contextually relevant.
No emojis or special symbols."""
            else:
                full_prompt = f"""{self.system_instruction}

{context}

Current user message: "{user_message}"

Respond naturally in English, considering our conversation history.
Keep it brief (1-2 sentences), friendly, and contextually relevant.
No emojis or special symbols."""
            
            # Use the new SDK generate_content method
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
            
            ai_response = response.text.strip()
            
            # Clean and validate response
            ai_response = self.clean_text_for_whatsapp(ai_response)
            
            # Ensure response is not empty
            if not ai_response or len(ai_response.strip()) < 2:
                if has_bengali:
                    ai_response = "আমি বুঝতে পারছি।"
                else:
                    ai_response = "I understand."
            
            # Limit response length
            if len(ai_response) > 400:
                ai_response = ai_response[:397] + "..."
            
            # Add AI response to conversation history
            self.add_to_conversation_history(ai_response, is_user=False)
            
            print(f"AI Response: {ai_response}")
            return ai_response
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            # Use simple backup generation without context
            return self.generate_simple_response(user_message)
    
    def generate_simple_response(self, user_message):
        """Fallback method for simple response generation with context"""
        try:
            has_bengali = any(char in user_message for char in 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ')
            
            # Add basic context awareness even in fallback
            context = self.get_conversation_context()
            
            if has_bengali:
                simple_prompt = f"""{context}
                User says: {user_message}
                Respond briefly in Bengali considering our conversation. No emojis."""
            else:
                simple_prompt = f"""{context}
                User says: {user_message}
                Respond briefly in English considering our conversation. No emojis."""
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=simple_prompt
            )
            
            ai_response = response.text.strip()
            ai_response = self.clean_text_for_whatsapp(ai_response)
            
            if not ai_response:
                if has_bengali:
                    return "দুঃখিত, একটু সমস্যা হচ্ছে।"
                else:
                    return "Sorry, having some trouble right now."
            
            # Add to conversation history even for fallback responses
            self.add_to_conversation_history(ai_response, is_user=False)
            
            return ai_response[:400]  # Limit length
            
        except Exception as e:
            print(f"Error in simple response generation: {e}")
            # Final fallback
            if any(char in user_message for char in 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ'):
                return "দুঃখিত, একটু সমস্যা হচ্ছে।"
            else:
                return "Sorry, having some trouble right now."
    
    def start_chat_bot(self):
        """Main chat bot loop - optimized for speed"""
        print(f"Starting WhatsApp AI Chat Bot for {CHAT_DURATION_MINUTES} minutes...")
        print("The bot will respond to new messages using Gemini AI")
        
        start_time = time.time()
        end_time = start_time + (CHAT_DURATION_MINUTES * 60)
        
        # Get initial messages and store them
        initial_messages = self.get_latest_messages()
        processed_messages = set()
        
        # Add all initial messages to processed set
        for msg in initial_messages:
            processed_messages.add(msg['text'])
        
        print(f"Found {len(initial_messages)} existing messages in chat")
        
        # Send initial greeting using context-aware generation
        greeting = self.generate_ai_response("Say hello briefly as an AI assistant")
        if self.send_message(greeting):
            processed_messages.add(greeting)
        
        # Minimal delay after greeting
        time.sleep(0.5)
        
        message_check_counter = 0
        
        while time.time() < end_time:
            try:
                # Check for new messages
                current_messages = self.get_latest_messages()
                
                # Find new incoming messages
                new_messages = []
                for msg in current_messages:
                    # Only process truly new incoming messages
                    if (msg['text'] not in processed_messages and msg['is_incoming']):
                        new_messages.append(msg)
                        processed_messages.add(msg['text'])
                
                # Process new messages immediately
                for msg in new_messages:
                    message_text = msg['text']
                    print(f"Received: {message_text}")
                    
                    # Skip "typing..." messages
                    if "typing" in message_text.lower() and "…" in message_text:
                        print("Skipping typing indicator")
                        continue
                    
                    # Generate and send AI response
                    ai_response = self.generate_ai_response(message_text)
                    
                    # Verify response is complete and valid
                    if ai_response and len(ai_response.strip()) > 1:
                        # Minimal delay before responding
                        time.sleep(RESPONSE_DELAY)
                        
                        # Send response
                        if self.send_message(ai_response):
                            processed_messages.add(ai_response)
                            print(f"✓ Responded to: {message_text[:30]}...")
                        else:
                            print("✗ Failed to send response")
                    else:
                        print("✗ Generated response was invalid or empty")
                
                # Fast checking interval
                time.sleep(CHECK_INTERVAL)
                
                # Reduced debug frequency
                message_check_counter += 1
                if message_check_counter % 60 == 0:  # Every 30 seconds (60 * 0.5s)
                    print(f"Monitoring... Messages: {len(current_messages)}, Processed: {len(processed_messages)}")
                
            except KeyboardInterrupt:
                print("\nBot stopped by user")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)  # Shorter error recovery time
        
        print("Chat bot session ended")
    
    def show_chat_history(self):
        """Display the conversation history"""
        print("\n" + "="*50)
        print("CONVERSATION HISTORY")
        print("="*50)
        
        try:
            if self.conversation_history:
                for msg in self.conversation_history:
                    role = "USER" if msg["role"] == "user" else "AI"
                    content = msg["content"][:100] + ("..." if len(msg["content"]) > 100 else "")
                    print(f"{role}: {content}")
            else:
                print("No conversation history available")
                
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
        
        # Login to WhatsApp
        if not bot.login_whatsapp():
            return
        
        # Open target chat
        if not bot.open_chat():
            return
        
        # Start the chat bot
        bot.start_chat_bot()
        
        # Show chat history
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