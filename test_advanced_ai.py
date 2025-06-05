#!/usr/bin/env python3
"""
Test script for the Advanced AI Client with function calling
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from advanced_ai_client import AdvancedGeminiAIClient

def test_function_calling():
    """Test function calling capabilities"""
    print("Testing Advanced AI Client with Function Calling...")
    
    # Initialize config and client
    config = Config()
    client = AdvancedGeminiAIClient(config)
    
    # Test cases
    test_cases = [
        "What time is it now?",
        "What's the weather like in London?",
        "Tell me about the latest news in AI",
        "Search for information about Python programming",
        "Hello, how are you?",  # Simple message without function calling
    ]
    
    print(f"\nTesting with Function Calling: {config.ENABLE_FUNCTION_CALLING}")
    print(f"Testing with Grounding: {config.ENABLE_GROUNDING}")
    print(f"Testing with Web Search: {config.ENABLE_WEB_SEARCH}")
    print("-" * 60)
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_message}")
        print("-" * 40)
        
        try:
            response = client.generate_response(test_message)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 40)
    
    print("\nTesting completed!")

if __name__ == "__main__":
    test_function_calling()
