import re

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import google.generativeai as genai

# Set your API key
API_KEY = "YOUR_API_KEY"

# Configure Gemini API with your API key
genai.configure(api_key=API_KEY)

# Ask for the contact name as saved in WhatsApp
contact_name = input("Enter the contact name as saved in WhatsApp: ")

# Display message options
print("Select a message type to send:")
print("1: Send a Hello")
print("2: Send a Birthday Wish")
print("3: Send a Friendly Check-in")

# Get the user choice
choice = input("Enter the number corresponding to your choice: ")

# Generate dynamic content based on user choice using Gemini API
message_prompt = ""
if choice == "1":
    message_prompt = f"Write a friendly hello message to {contact_name}."
elif choice == "2":
    message_prompt = f"Write a birthday wish to {contact_name}."
elif choice == "3":
    message_prompt = f"Write a friendly check-in message to {contact_name}."
else:
    print("Invalid choice. Defaulting to Hello message.")
    message_prompt = f"Write a friendly hello message to {contact_name}."

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("Generating message... Please wait.")
    
    # Generate the message using the selected prompt
    response = model.generate_content(message_prompt)
    
    # Check if the response is valid
    if hasattr(response, 'text') and response.text:
        message = response.text
        print("Generated Message:", message)
    else:
        raise ValueError("Failed to generate a message. Response is empty.")
    
    # Remove non-BMP characters (e.g., emojis) from the message
    message = re.sub(r'[^\u0000-\uFFFF]', '', message)
    print("Sanitized Message:", message)
    
except Exception as e:
    print("Error in generating content:", e)
    message = f"Hello {contact_name}! This is an automated message."

# Now, start Selenium operations
# Initialize the WebDriver
driver = webdriver.Chrome()
baseurl = "https://web.whatsapp.com/"

# Open WhatsApp Web
driver.get(baseurl)
wait = WebDriverWait(driver, 10000)

# Specify the target contact name
target = "Uttam"  # Change this to the name of your contact
x_arg = f'//span[contains(@title, "{target}")]'

# Wait for the target contact to appear and click on it
target = wait.until(ec.presence_of_element_located((By.XPATH, x_arg)))
target.click()

# Locate the text box where messages are typed
text_box = driver.find_element(By.CLASS_NAME, '_ak1l')

# Send the generated message multiple times
for i in range(2):
    text_box.send_keys(message + Keys.ENTER)

# Wait before closing the browser (optional)
time.sleep(10)

# Close the WebDriver
driver.quit()
