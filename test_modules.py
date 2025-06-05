#!/usr/bin/env python3
"""
Test script for the modular WhatsApp bot architecture
"""

def test_imports():
    """Test that all modules can be imported correctly"""
    print("Testing module imports...")
    
    try:
        from config import Config
        print("✓ config.py imported successfully")
        
        from models import ChatResponse, Message, ConversationMessage, BotStatus, BotStats
        print("✓ models.py imported successfully")
        
        from message_processor import MessageProcessor
        print("✓ message_processor.py imported successfully")
        
        from conversation_manager import ConversationManager
        print("✓ conversation_manager.py imported successfully")
        
        # Test AI client (may fail without API key)
        try:
            from ai_client import GeminiAIClient
            print("✓ ai_client.py imported successfully")
        except Exception as e:
            print(f"⚠ ai_client.py import warning: {e}")
        
        # Test WhatsApp driver (may fail without Chrome)
        try:
            from whatsapp_driver import WhatsAppDriver
            print("✓ whatsapp_driver.py imported successfully")
        except Exception as e:
            print(f"⚠ whatsapp_driver.py import warning: {e}")
        
        from bot_new import WhatsAppGeminiBot
        print("✓ bot_new.py imported successfully")
        
        print("\n✅ All critical modules imported successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration functionality"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        
        # Test basic config
        config = Config()
        config.validate()
        print("✓ Config validation passed")
        
        # Test config properties
        assert hasattr(config, 'GEMINI_API_KEY')
        assert hasattr(config, 'TARGET_CONTACT')
        assert hasattr(config, 'CHAT_DURATION_MINUTES')
        print("✓ Config properties exist")
        
        print("✅ Configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_models():
    """Test data models"""
    print("\nTesting data models...")
    
    try:
        from models import Message, ConversationMessage, BotStatus, BotStats
        import time
        
        # Test Message model
        message = Message(text="Hello", is_incoming=True, timestamp=time.time())
        assert message.text == "Hello"
        assert message.is_incoming == True
        print("✓ Message model works")
        
        # Test ConversationMessage model
        conv_msg = ConversationMessage(role="user", content="Test", timestamp=time.time())
        assert conv_msg.role == "user"
        assert conv_msg.content == "Test"
        print("✓ ConversationMessage model works")
        
        # Test BotStatus model
        status = BotStatus(is_running=False)
        assert status.is_running == False
        print("✓ BotStatus model works")
        
        # Test BotStats model
        stats = BotStats()
        stats.add_language("english")
        assert "english" in stats.languages_detected
        print("✓ BotStats model works")
        
        print("✅ Model tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def test_message_processor():
    """Test message processing utilities"""
    print("\nTesting message processor...")
    
    try:
        from message_processor import MessageProcessor
        
        # Test text cleaning
        dirty_text = "Hello 😀 World! 🌟"
        clean_text = MessageProcessor.clean_text_for_whatsapp(dirty_text)
        print(f"✓ Text cleaning: '{dirty_text}' -> '{clean_text}'")
        
        # Test typing indicator detection
        typing_msg = "typing..."
        is_typing = MessageProcessor.is_typing_indicator(typing_msg)
        assert is_typing == False  # Our logic looks for "…"
        print("✓ Typing indicator detection works")
        
        # Test language detection
        english_text = "Hello world"
        bengali_text = "আমি বাংলায় কথা বলি"
        
        eng_lang = MessageProcessor.detect_language(english_text)
        ben_lang = MessageProcessor.detect_language(bengali_text)
        
        assert eng_lang == "english"
        assert ben_lang == "bengali"
        print("✓ Language detection works")
        
        # Test message validation
        valid_response = MessageProcessor.validate_response("Hello there!")
        assert valid_response == "Hello there!"
        print("✓ Message validation works")
        
        print("✅ Message processor tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Message processor error: {e}")
        return False

def test_conversation_manager():
    """Test conversation management"""
    print("\nTesting conversation manager...")
    
    try:
        from conversation_manager import ConversationManager
        from config import Config
        
        config = Config()
        conv_manager = ConversationManager(config)
        
        # Test adding messages
        conv_manager.add_message("Hello", "user")
        conv_manager.add_message("Hi there!", "assistant")
        
        history = conv_manager.get_conversation_history()
        assert len(history) == 2
        assert history[0].content == "Hello"
        assert history[1].content == "Hi there!"
        print("✓ Message addition works")
        
        # Test context generation
        context = conv_manager.get_conversation_context()
        assert "Hello" in context
        assert "Hi there!" in context
        print("✓ Context generation works")
        
        # Test stats
        stats = conv_manager.get_stats()
        assert stats["total_messages"] == 2
        assert stats["user_messages"] == 1
        assert stats["ai_messages"] == 1
        print("✓ Stats generation works")
        
        print("✅ Conversation manager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Conversation manager error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🧪 Starting modular architecture tests...\n")
    
    tests = [
        test_imports,
        test_config,
        test_models,
        test_message_processor,
        test_conversation_manager,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The modular architecture is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
