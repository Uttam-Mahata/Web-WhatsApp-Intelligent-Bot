# WhatsApp Gemini AI Bot - AI Agent Instructions

## Project Architecture

This is a **modular WhatsApp chatbot** that uses Google's Gemini AI with advanced features like function calling and Google Search grounding. The bot automates WhatsApp Web via Selenium to have AI-powered conversations.

### Core Component Flow
```
main.py → bot_new.py (orchestrator) → {
  whatsapp_driver.py (Selenium automation)
  advanced_ai_client.py (Gemini AI + functions)
  conversation_manager.py (history/context)
  message_processor.py (text cleaning/validation)
}
```

**Key architectural pattern**: `bot_new.py` is the orchestrator that coordinates all components. Never implement business logic directly in `bot_new.py` - delegate to specialized modules.

## Critical Setup Requirements

### Environment Configuration
- **GEMINI_API_KEY** must be set as environment variable (never hardcoded)
- `Config.load_from_env()` is the standard initialization pattern in `main.py`
- WhatsApp contact name in `TARGET_CONTACT` must match exactly (case-sensitive)

### Chrome WebDriver Specifics
- Uses `webdriver_manager` for automatic ChromeDriver setup
- **Critical**: WhatsApp Web requires disabling webdriver detection via `driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")`
- XPath selectors in `whatsapp_driver.py` have multiple fallbacks due to frequent WhatsApp UI changes

## Development Patterns

### Adding AI Capabilities
When extending `advanced_ai_client.py`:
1. Register new functions in `_register_functions()` method
2. Add function implementation as private method (e.g., `_get_weather`)
3. Add detection keywords in `_needs_function_call()` or `_needs_web_search()`
4. Function signatures must match Google Gemini's function calling schema

**Example from codebase**:
```python
# In _register_functions:
self.function_registry['get_current_time'] = self._get_current_time

# Implementation:
def _get_current_time(self) -> str:
    """Function callable by AI"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

### Message Processing Pipeline
1. `whatsapp_driver.get_latest_messages()` → raw messages with sender info
2. `message_processor.filter_new_messages()` → removes duplicates, system messages
3. `message_processor.clean_text_for_whatsapp()` → strips emojis/non-BMP chars (ChromeDriver limitation)
4. `conversation_manager.add_message()` → maintains rolling history

**Important**: Always use `clean_text_for_whatsapp()` before sending messages via Selenium - emojis cause ChromeDriver crashes.

### Bilingual Support Pattern
Detect language using `_detect_bengali()` checking for Bengali Unicode range (U+0980-U+09FF), then:
- Create language-specific prompts in `_create_enhanced_prompt()`
- Both English and Bengali supported throughout conversation flow
- Keywords for context queries exist in both languages (see `conversation_manager.py` line 52-60)

### Pydantic Models Usage
All data structures use Pydantic for validation:
- `Message`: WhatsApp message (text, is_incoming, timestamp)
- `ConversationMessage`: History entry (role, content, timestamp)
- `BotStatus`/`BotStats`: Runtime tracking

Always use these models instead of dicts to ensure type safety.

## Common Integration Points

### Modifying AI Behavior
- **System instruction**: Edit `SYSTEM_INSTRUCTION` in `config.py` (currently emphasizes real-time search/function use)
- **Response length**: Adjust `MAX_RESPONSE_LENGTH` in config (default: 4096 chars)
- **Context window**: `MAX_CONVERSATION_HISTORY` (15) and `RECENT_MESSAGES_CONTEXT` (5) control memory

### WhatsApp Automation Troubleshooting
If message detection fails, check:
1. XPath selectors in `whatsapp_driver.py` lines 156-188 (WhatsApp updates UI frequently)
2. Fallback selectors array in `get_message_input()` line 107-114
3. `processed_messages` Set tracks message IDs to prevent duplicates

### Conversation Context Queries
Users can ask meta-questions about conversation:
- Keywords: "what did i ask", "earlier", "summary" (English + Bengali variants)
- Handled in `conversation_manager.handle_context_query()` before AI generation
- Returns direct string response, bypassing AI to save tokens

## Testing Individual Components

```python
# Test AI client without WhatsApp
from advanced_ai_client import AdvancedGeminiAIClient
from config import Config
config = Config.load_from_env()
ai = AdvancedGeminiAIClient(config)
response = ai.generate_response("What time is it?", "")

# Test message processing
from message_processor import MessageProcessor
clean = MessageProcessor.clean_text_for_whatsapp("Hello 😊")  # Removes emoji
```

## Running the Bot

```bash
export GEMINI_API_KEY="your_key_here"
python main.py
```

Expected flow:
1. Opens Chrome with WhatsApp Web
2. Wait for QR code scan (60s timeout)
3. Searches for `TARGET_CONTACT` and opens chat
4. Polls for new messages every 0.5s (configurable)
5. Generates AI response with context
6. Sends cleaned response via Selenium

**Interruption**: Ctrl+C triggers cleanup (`bot.cleanup()`) - always ensure resources are freed.

## Key Files Reference

- `config.py` - All configurable behavior (15+ settings)
- `advanced_ai_client.py` - AI logic, function calling, search grounding (440 lines)
- `bot_new.py` - Main orchestration loop (238 lines)
- `whatsapp_driver.py` - All Selenium automation with fallback selectors
- `message_processor.py` - Text sanitization utilities (critical for Selenium stability)

## Anti-Patterns to Avoid

❌ Don't send messages without `clean_text_for_whatsapp()` - will crash ChromeDriver
❌ Don't bypass `Config.validate()` - ensures API key and contact name are set
❌ Don't add business logic to `bot_new.py` - use specialized modules
❌ Don't use single XPath selectors for WhatsApp elements - always provide fallbacks
❌ Don't modify `processed_messages` Set outside main loop - causes duplicate responses
