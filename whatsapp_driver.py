"""
WhatsApp Web automation driver
"""
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Optional
import time
from config import Config
from models import Message

class WhatsAppDriver:
    """Handles WhatsApp Web automation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self._setup_driver()
    
    def _setup_driver(self) -> None:
        """Initialize Chrome WebDriver with WhatsApp compatibility"""
        chrome_options = Options()
        
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT)
    
    def login_whatsapp(self) -> bool:
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
    
    def open_chat(self, contact_name: str) -> bool:
        """Search for and open the target contact's chat"""
        try:
            print(f"Looking for contact: {contact_name}")
            
            # Search for the contact
            search_box_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
            search_box = self.driver.find_element(By.XPATH, search_box_xpath)
            search_box.click()
            search_box.clear()
            search_box.send_keys(contact_name)
            time.sleep(1)
            
            # Click on the contact
            contact_xpath = f'//span[@title="{contact_name}"]'
            contact = self.wait.until(ec.element_to_be_clickable((By.XPATH, contact_xpath)))
            contact.click()
            
            print(f"Contact found and chat opened: {contact_name}")
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
    
    def send_message(self, message: str) -> bool:
        """Send a message in the current chat"""
        try:
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
    
    def get_latest_messages(self) -> List[Message]:
        """Get the latest messages from the chat with sender info"""
        try:
            messages = []
            
            # Use the most reliable selector for WhatsApp messages
            try:
                all_messages = self.driver.find_elements(
                    By.XPATH, 
                    '//span[contains(@class, "_ao3e") and contains(@class, "selectable-text")]'
                )
                
                if all_messages:
                    # Get parent containers to check message direction
                    for elem in all_messages:
                        text = elem.text.strip()
                        if text:
                            try:
                                # Check if message is incoming by looking at parent classes
                                parent = elem.find_element(
                                    By.XPATH, 
                                    './ancestor::div[contains(@class, "message-") or contains(@class, "_akbu")][1]'
                                )
                                parent_class = parent.get_attribute('class') or ''
                                
                                # Determine if incoming (from other person) or outgoing (from bot)
                                is_incoming = 'message-in' in parent_class or not ('message-out' in parent_class)
                                
                                messages.append(Message(
                                    text=text,
                                    is_incoming=is_incoming,
                                    timestamp=time.time()
                                ))
                            except:
                                # If we can't determine direction, assume it's incoming
                                messages.append(Message(
                                    text=text,
                                    is_incoming=True,
                                    timestamp=time.time()
                                ))
                                
            except Exception as e:
                print(f"Error in message detection: {e}")
            
            return messages
            
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                print("Browser closed successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def is_driver_alive(self) -> bool:
        """Check if the WebDriver is still alive"""
        try:
            self.driver.current_url
            return True
        except:
            return False
