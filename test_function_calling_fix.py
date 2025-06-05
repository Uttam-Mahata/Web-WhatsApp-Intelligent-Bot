#!/usr/bin/env python3
"""
Test script to verify the function calling fix works
"""

import os
from config import Config
from advanced_ai_client import AdvancedGeminiAIClient

def test_function_calling():
    """Test function calling with weather request"""
    try:
        print("Testing function calling fix...")
        
        # Load config
        config = Config()
        
        # Initialize AI client
        ai_client = AdvancedGeminiAIClient(config)
        
        # Test weather function calling
        print("\n1. Testing weather function calling:")
        weather_response = ai_client.generate_response("What's the weather in Mumbai?")
        print(f"Response: {weather_response}")
        
        # Test time function calling
        print("\n2. Testing time function calling:")
        time_response = ai_client.generate_response("What time is it now?")
        print(f"Response: {time_response}")
        
        # Test Google Search grounding
        print("\n3. Testing Google Search grounding:")
        search_response = ai_client.generate_response("Who is the current Prime Minister of India?")
        print(f"Response: {search_response}")
        
        # Test simple response (should not trigger functions)
        print("\n4. Testing simple response:")
        simple_response = ai_client.generate_response("Hello, how are you?")
        print(f"Response: {simple_response}")
        
        print("\n✓ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_function_calling()
