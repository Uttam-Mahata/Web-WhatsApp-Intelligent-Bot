#!/usr/bin/env python3
"""
Test script to verify the fixed advanced AI client implementation
"""
import os
import sys
from config import Config
from advanced_ai_client import AdvancedGeminiAIClient

def test_basic_functionality():
    """Test basic functionality without advanced features"""
    print("🧪 Testing basic functionality...")
    
    try:
        config = Config()
        client = AdvancedGeminiAIClient(config)
        
        # Test simple message
        response = client.generate_response("Hello, how are you?")
        print(f"✓ Simple response: {response}")
        
        return True
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

def test_function_calling():
    """Test function calling for time/weather"""
    print("\n🧪 Testing function calling...")
    
    try:
        config = Config()
        client = AdvancedGeminiAIClient(config)
        
        # Test time request
        response = client.generate_response("What time is it now?")
        print(f"✓ Time response: {response}")
        
        # Test weather request  
        response = client.generate_response("What's the weather like in New York?")
        print(f"✓ Weather response: {response}")
        
        return True
    except Exception as e:
        print(f"❌ Function calling test failed: {e}")
        return False

def test_web_search():
    """Test Google Search grounding"""
    print("\n🧪 Testing Google Search grounding...")
    
    try:
        config = Config()
        client = AdvancedGeminiAIClient(config)
        
        # Test current information request
        response = client.generate_response("What are the latest news about AI developments?")
        print(f"✓ Search response: {response}")
        
        return True
    except Exception as e:
        print(f"❌ Web search test failed: {e}")
        return False

def test_bengali_support():
    """Test Bengali language support"""
    print("\n🧪 Testing Bengali support...")
    
    try:
        config = Config()
        client = AdvancedGeminiAIClient(config)
        
        # Test Bengali message
        response = client.generate_response("আপনি কেমন আছেন?")
        print(f"✓ Bengali response: {response}")
        
        return True
    except Exception as e:
        print(f"❌ Bengali test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Fixed Advanced AI Client")
    print("=" * 50)
    
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY environment variable not set")
        return
    
    test_results = []
    
    # Run tests
    test_results.append(test_basic_functionality())
    test_results.append(test_function_calling())
    test_results.append(test_web_search())
    test_results.append(test_bengali_support())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The AI client is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
