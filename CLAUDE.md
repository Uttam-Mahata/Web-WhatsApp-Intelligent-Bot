# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modular WhatsApp AI chatbot powered by Google's Gemini AI with advanced features including Google Search grounding, function calling, and multi-language support (English and Bengali). The bot automates WhatsApp Web interactions using Selenium and provides context-aware conversational responses.

## Development Commands

### Running the Bot
```bash
python main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Required Environment Variable
The bot requires `GEMINI_API_KEY` to be set as an environment variable:
```bash
# Linux/macOS
export GEMINI_API_KEY="your_api_key_here"

# Windows PowerShell
$Env:GEMINI_API_KEY="your_api_key_here"
```

### Optional Environment Variables
- `TARGET_CONTACT`: WhatsApp contact name (default: "Uttam")
- `CHAT_DURATION_MINUTES`: Session duration (default: 60)
- `RESPONSE_DELAY`: Delay before responding in seconds (default: 0.5)
- `CHECK_INTERVAL`: Message checking frequency in seconds (default: 0.5)

## Architecture

### Component Flow
The bot follows a clear orchestration pattern:

1. **main.py** → Entry point that initializes config and creates WhatsAppGeminiBot instance
2. **WhatsAppGeminiBot** (bot_new.py) → Main orchestrator that coordinates all components:
   - Manages the chat loop and message processing
   - Coordinates between WhatsApp driver, AI client, conversation manager, and message processor
   - Tracks bot status and statistics
3. **Component Modules** → Specialized modules with single responsibilities

### Key Components

**config.py**
- Centralized configuration using the `Config` class
- Loads settings from environment variables via `Config.load_from_env()`
- Validates required settings with `validate()`
- Contains system instructions for the AI

**bot_new.py** (Main Orchestrator)
- `WhatsAppGeminiBot`: Main bot class that ties all components together
- Key methods:
  - `initialize()`: Login to WhatsApp and open target chat
  - `start_chat_session()`: Main chat loop that monitors and responds to messages
  - `_process_new_message()`: Handles individual message processing
  - `cleanup()`: Resource cleanup

**advanced_ai_client.py**
- `AdvancedGeminiAIClient`: Handles all AI interactions using Google's Gemini 2.0 Flash model
- Features:
  - Google Search grounding for current information
  - Function calling (time, weather, search)
  - Automatic language detection (English/Bengali)
  - Intelligent routing based on query type
- Key methods:
  - `generate_response()`: Main entry point for AI responses
  - `_generate_with_google_search()`: Uses Google Search tool for current info
  - `_generate_with_functions()`: Uses function calling for structured queries
  - `_process_function_response()`: Executes functions and generates final response

**whatsapp_driver.py**
- `WhatsAppDriver`: Selenium-based WhatsApp Web automation
- Key methods:
  - `login_whatsapp()`: Opens WhatsApp Web and waits for QR scan
  - `open_chat()`: Searches for and opens contact's chat
  - `send_message()`: Sends text to current chat
  - `get_latest_messages()`: Retrieves messages with incoming/outgoing detection
- Uses multiple XPath selectors for robustness against WhatsApp UI changes

**conversation_manager.py**
- `ConversationManager`: Manages conversation history and context
- Automatically trims history to prevent unlimited growth (configured via MAX_CONVERSATION_HISTORY)
- Key methods:
  - `add_message()`: Adds message to history with automatic trimming
  - `get_conversation_context()`: Formats recent messages for AI context
  - `handle_context_query()`: Handles meta-conversation queries (e.g., "what did I ask earlier?")

**message_processor.py**
- `MessageProcessor`: Text cleaning, validation, and filtering utilities
- Handles language detection
- Filters new vs processed messages
- Cleans text for WhatsApp compatibility (removes emojis, non-BMP characters)

**models.py**
- Pydantic models for type safety:
  - `Message`: Individual WhatsApp messages
  - `ConversationMessage`: Conversation history entries
  - `BotStatus`: Bot runtime status
  - `BotStats`: Session statistics

### AI Response Generation Flow

1. User message received → `bot_new.py:_process_new_message()`
2. Check if it's a context query → `conversation_manager.handle_context_query()`
3. If not, add to conversation → `conversation_manager.add_message()`
4. Get recent context → `conversation_manager.get_conversation_context()`
5. Route to appropriate AI generation:
   - If needs web search → `_generate_with_google_search()` (uses Google Search tool)
   - If needs function call → `_generate_with_functions()` (e.g., time/weather)
   - Otherwise → `_generate_simple_response()`
6. Clean and validate response → `message_processor.validate_response()`
7. Send via WhatsApp → `whatsapp_driver.send_message()`

### Message Tracking Pattern

The bot uses a set-based approach to track processed messages:
- `processed_messages: Set[str]` stores all seen message texts
- On startup, loads existing messages to avoid re-processing
- Each new message checked against this set
- Both incoming and outgoing messages added to prevent loops

## Important Implementation Details

### WhatsApp Web Automation Challenges
- WhatsApp Web's UI frequently changes; the driver uses multiple fallback XPath selectors
- The driver disables webdriver detection: `navigator.webdriver = undefined`
- Message direction detection relies on parent container CSS classes
- QR code login timeout is 60 seconds (configurable via WEBDRIVER_TIMEOUT)

### AI Model Configuration
- Uses `gemini-2.0-flash` model (stable version)
- System instruction in config.py guides AI behavior
- Google Search grounding uses `types.Tool(google_search=types.GoogleSearch())`
- Function declarations follow OpenAPI-like schema format
- Response cleaning removes emojis to prevent ChromeDriver issues

### Language Handling
- Automatic Bengali/English detection using character set matching
- Bengali characters: 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ'
- AI responds in the same language as user input
- Context queries support both languages

### Configuration Patterns
- NEVER hardcode API keys; always use environment variables
- Config validation happens in `Config.validate()`
- All timeouts/delays configurable for different network conditions
- MAX_CONVERSATION_HISTORY prevents unbounded memory growth

## Testing Individual Components

Since components are decoupled, you can test them independently:

```python
# Test AI client
from config import Config
from advanced_ai_client import AdvancedGeminiAIClient

config = Config.load_from_env()
ai_client = AdvancedGeminiAIClient(config)
response = ai_client.generate_response("What is the weather today?")
print(response)

# Test conversation manager
from conversation_manager import ConversationManager

conv_mgr = ConversationManager(config)
conv_mgr.add_message("Hello", role="user")
conv_mgr.add_message("Hi there!", role="assistant")
context = conv_mgr.get_conversation_context()
print(context)
```

## Common Issues and Solutions

**"Failed to login to WhatsApp"**
- QR code scan timeout (increase WEBDRIVER_TIMEOUT)
- WhatsApp Web UI changed (update XPath selectors in whatsapp_driver.py)

**"Could not find message input box"**
- WhatsApp Web UI changed (add new selector to `get_message_input()`)

**"Response contains emojis/special characters"**
- ChromeDriver cannot handle non-BMP Unicode
- Ensure `_clean_response_text()` is applied to all AI responses

**Bot processes its own messages**
- Check `processed_messages` set is properly maintained
- Verify `is_incoming` detection logic in `get_latest_messages()`

## File Organization

The codebase follows a flat structure with clear module separation:
- **Entry point**: main.py
- **Orchestrator**: bot_new.py
- **Core modules**: config.py, models.py
- **Feature modules**: advanced_ai_client.py, whatsapp_driver.py, conversation_manager.py, message_processor.py
- **Legacy/alternative**: enhanced_ai_client.py (empty, can be removed)
