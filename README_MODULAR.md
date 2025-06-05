# WhatsApp Gemini AI Bot - Modular Architecture

A modular WhatsApp AI chatbot powered by Google's Gemini AI, with improved architecture for maintainability and extensibility.

## 🏗️ Architecture Overview

The bot has been refactored into a modular architecture with the following components:

### Core Modules

1. **`config.py`** - Configuration management
   - Centralized configuration settings
   - Environment variable support
   - Configuration validation

2. **`models.py`** - Data models and schemas
   - Pydantic models for type safety
   - Message and conversation structures
   - Bot status and statistics models

3. **`ai_client.py`** - Gemini AI client
   - AI response generation
   - Context-aware conversations
   - Language detection and handling

4. **`whatsapp_driver.py`** - WhatsApp Web automation
   - Selenium WebDriver management
   - Message sending and receiving
   - Browser automation utilities

5. **`conversation_manager.py`** - Conversation context
   - Conversation history management
   - Context queries handling
   - Message summarization

6. **`message_processor.py`** - Message utilities
   - Text cleaning and validation
   - Message filtering
   - Language detection

7. **`bot_new.py`** - Main bot orchestrator
   - Coordinates all components
   - Main chat loop
   - Status and statistics tracking

8. **`main.py`** - Entry point
   - Application initialization
   - Error handling
   - Configuration loading

## 🚀 Features

- **Modular Design**: Clean separation of concerns
- **Type Safety**: Pydantic models for data validation
- **Context Awareness**: Maintains conversation history
- **Multi-language**: Supports English and Bengali
- **Error Handling**: Robust error recovery
- **Statistics**: Session tracking and analytics
- **Configuration**: Environment-based settings

## 📦 Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install selenium google-generativeai pydantic
   ```
3. Set up Chrome WebDriver
4. Configure your Gemini API key in `config.py`

## 🎯 Usage

### Basic Usage
```python
python main.py
```

### Advanced Usage
```python
from config import Config
from bot_new import WhatsAppGeminiBot

# Custom configuration
config = Config()
config.TARGET_CONTACT = "Your Contact"
config.CHAT_DURATION_MINUTES = 60

# Initialize and run bot
bot = WhatsAppGeminiBot(config)
if bot.initialize():
    bot.start_chat_session()
    bot.show_conversation_history()
    bot.cleanup()
```

## ⚙️ Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Gemini AI API key
- `TARGET_CONTACT`: WhatsApp contact name
- `CHAT_DURATION_MINUTES`: Session duration
- `RESPONSE_DELAY`: Delay between responses
- `CHECK_INTERVAL`: Message checking frequency

### Direct Configuration
Modify values in `config.py` for custom settings.

## 🔧 Architecture Benefits

1. **Maintainability**: Each module has a single responsibility
2. **Testability**: Components can be tested independently
3. **Extensibility**: Easy to add new features
4. **Reusability**: Modules can be used in other projects
5. **Debugging**: Easier to isolate and fix issues

## 📊 Statistics and Monitoring

The bot tracks:
- Messages sent/received
- Session duration
- Error count
- Conversation metrics
- Language usage

## 🛠️ Development

### Adding New Features
1. Create appropriate models in `models.py`
2. Implement logic in relevant modules
3. Update the main bot orchestrator
4. Add configuration options if needed

### Testing Individual Components
```python
# Test AI client
from ai_client import GeminiAIClient
from config import Config

config = Config()
ai_client = GeminiAIClient(config)
response = ai_client.generate_response("Hello")
print(response)
```

## 🔒 Security

- API keys should be stored in environment variables
- Sensitive data is not logged
- Browser automation follows best practices

## 📝 Migration from Monolithic Version

The original `bot.py` has been split into focused modules:
- Configuration moved to `config.py`
- AI logic moved to `ai_client.py`
- WhatsApp automation moved to `whatsapp_driver.py`
- Conversation logic moved to `conversation_manager.py`
- Utilities moved to `message_processor.py`

## 🚨 Error Handling

Each module includes comprehensive error handling:
- Graceful degradation
- Fallback responses
- Cleanup procedures
- Status reporting

## 📈 Performance

Optimizations include:
- Efficient message filtering
- Reduced WebDriver calls
- Smart conversation management
- Resource cleanup

## 🤝 Contributing

1. Follow the modular architecture
2. Add appropriate type hints
3. Include error handling
4. Update documentation
5. Add tests for new features

## 📄 License

This project is licensed under the MIT License.
