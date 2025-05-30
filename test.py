from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Configuration
MESSAGE = "Hello ! This is an automated message from Tapas."  # Change this to your desired message
TARGET_CONTACT = "Sibu Bhai"  # Change this to the name of your contact
NUMBER_OF_MESSAGES = 1000  # Change this to the number of times you want to send the message

# Set up Chrome options for better compatibility
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Initialize the WebDriver
driver = webdriver.Chrome(options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

baseurl = "https://web.whatsapp.com/"

try:
    # Open WhatsApp Web
    driver.get(baseurl)
    wait = WebDriverWait(driver, 600)  # 10 minutes timeout for QR scan
    
    print(f"Please scan the QR code to login to WhatsApp Web...")
    print(f"Waiting for WhatsApp to load completely...")
    
    # Wait for WhatsApp to load completely by waiting for the search box
    search_box_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
    wait.until(ec.presence_of_element_located((By.XPATH, search_box_xpath)))
    
    print(f"WhatsApp loaded successfully!")
    print(f"Looking for contact: {TARGET_CONTACT}")
    
    # Search for the contact first
    search_box = driver.find_element(By.XPATH, search_box_xpath)
    search_box.click()
    search_box.send_keys(TARGET_CONTACT)
    time.sleep(2)  # Wait for search results
    
    # Click on the contact from search results
    contact_xpath = f'//span[@title="{TARGET_CONTACT}"]'
    contact = wait.until(ec.element_to_be_clickable((By.XPATH, contact_xpath)))
    contact.click()
    
    print(f"Contact found and selected: {TARGET_CONTACT}")
    
    # Wait for the chat to load and find the message input box
    print("Waiting for chat to load...")
    time.sleep(3)
    
    # Try multiple selectors for the message input box based on the actual HTML structure
    message_input_selectors = [
        '//div[@contenteditable="true"][@data-tab="10"][@role="textbox"]',  # Most specific
        '//div[@aria-label="Type a message"][@contenteditable="true"]',     # Using aria-label
        '//div[@contenteditable="true"][@role="textbox"][@spellcheck="true"]', # Alternative
        '//div[contains(@class, "x1hx0egp")][@contenteditable="true"]',     # Using class from HTML
        '//div[@data-lexical-editor="true"][@contenteditable="true"]',      # Using data attribute
        '//div[@contenteditable="true"][@data-tab="10"]',                   # Fallback
    ]
    
    message_input = None
    for selector in message_input_selectors:
        try:
            message_input = wait.until(ec.element_to_be_clickable((By.XPATH, selector)))
            print(f"Found message input using selector: {selector}")
            break
        except:
            continue
    
    if not message_input:
        raise Exception("Could not find message input box")
    
    print(f"Sending message '{MESSAGE}' {NUMBER_OF_MESSAGES} times...")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Send the message multiple times
    for i in range(NUMBER_OF_MESSAGES):
        try:
            # Click on the input box to ensure it's focused
            message_input.click()
            time.sleep(0.1)
            
            # Clear any existing text and send new message
            message_input.clear()
            message_input.send_keys(MESSAGE)
            message_input.send_keys(Keys.ENTER)
            
            print(f"Message {i+1}/{NUMBER_OF_MESSAGES} sent")
            
            # Small delay between messages
            time.sleep(0.5)
            
            # Every 50 messages, wait a bit longer to avoid being flagged
            if (i + 1) % 50 == 0:
                print(f"Pausing for 5 seconds after {i+1} messages...")
                time.sleep(5)
                
        except Exception as e:
            print(f"Error sending message {i+1}: {e}")
            # Try to find the input box again using the most reliable selector
            try:
                message_input = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"][@role="textbox"]')
            except:
                try:
                    message_input = driver.find_element(By.XPATH, '//div[@aria-label="Type a message"][@contenteditable="true"]')
                except:
                    print("Could not relocate message input box")
                    break
    
    print("All messages sent successfully!")
    print("Waiting 10 seconds before closing...")
    time.sleep(10)

except Exception as e:
    print(f"An error occurred: {e}")
    print("Make sure you:")
    print("1. Scanned the QR code properly")
    print("2. Have a stable internet connection")
    print("3. The contact name is spelled correctly")
    print("4. WhatsApp Web is fully loaded")

finally:
    # Close the WebDriver
    driver.quit()
    print("Browser closed.")