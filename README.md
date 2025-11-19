# WhatsApp AI Bot v2.0 - Production Edition

A **production-ready** WhatsApp AI chatbot powered by **WhatsApp Business API** and **Google's Gemini AI** with advanced features including tool calling, image generation, and Google Search grounding.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://ai.google.dev/)
[![WhatsApp Business API](https://img.shields.io/badge/WhatsApp-Business%20API-25D366.svg)](https://developers.facebook.com/docs/whatsapp)

## 🚀 What's New in v2.0

### Major Architectural Changes

**From Selenium/Playwright → WhatsApp Business API**
- ✅ Official Meta API (no browser automation)
- ✅ Production-ready and scalable
- ✅ Webhook-based real-time messaging
- ✅ No QR code scanning required
- ✅ Better reliability and compliance

### Enhanced AI Capabilities

- **🎨 Image Generation**: Create and edit images with Gemini 2.5 Flash Image
- **🔧 Tool Calling**: Weather, time, calculations, and extensible custom tools
- **🔍 Google Search**: Real-time web information with Google Search grounding
- **📊 Structured Outputs**: Type-safe JSON responses with Pydantic
- **💻 Code Execution**: Run code for complex calculations
- **🌐 Multi-turn Conversations**: Advanced context management

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  WhatsApp Business API                       │
│                  (Meta Cloud API)                            │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Webhook Server                          │
│              (Async, High Performance)                       │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  Message Handler │    │  WhatsApp Client │
│  (Orchestrator)  │    │  (API Interface) │
└────────┬─────────┘    └──────────────────┘
         │
    ┌────┴────┬────────────┬──────────────┐
    ▼         ▼            ▼              ▼
┌────────┐ ┌──────┐  ┌──────────┐  ┌──────────┐
│Enhanced│ │Conv. │  │  Config  │  │  Models  │
│Gemini  │ │Mgr   │  │  Manager │  │ (Pydantic│
│AI      │ │      │  │          │  │          │
└────────┘ └──────┘  └──────────┘  └──────────┘
```

### Directory Structure

```
Web-WhatsApp-Intelligent-Bot/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── production_config.py      # Centralized configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── whatsapp_models.py        # Pydantic models for WhatsApp API
│   ├── whatsapp/
│   │   ├── __init__.py
│   │   └── business_api_client.py    # WhatsApp Business API client
│   ├── ai/
│   │   ├── __init__.py
│   │   └── enhanced_gemini_client.py # Enhanced Gemini with tools & image gen
│   ├── core/
│   │   ├── __init__.py
│   │   └── message_handler.py        # Message processing orchestrator
│   └── webhook/
│       ├── __init__.py
│       └── server.py                 # FastAPI webhook server
├── docs/
│   ├── WHATSAPP_BUSINESS_API_SETUP.md  # Complete setup guide
│   └── PRODUCTION_ARCHITECTURE.md      # Architecture details
├── main.py                           # Production entry point
├── verify_setup.py                   # Setup verification script
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── Dockerfile                        # Docker container
├── docker-compose.yml                # Docker Compose configuration
└── README.md                         # This file
```

## 📋 Prerequisites

1. **Meta Business Account** with WhatsApp Business API access
2. **Python 3.11+** installed
3. **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey)
4. **Server** with HTTPS for webhook (or ngrok for development)

## 🔧 Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/Web-WhatsApp-Intelligent-Bot.git
cd Web-WhatsApp-Intelligent-Bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up WhatsApp Business API

Follow the comprehensive guide in **[docs/WHATSAPP_BUSINESS_API_SETUP.md](docs/WHATSAPP_BUSINESS_API_SETUP.md)** which includes:

- Creating a Meta App
- Registering your phone number
- Generating access tokens
- Configuring webhooks
- Testing your setup

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```env
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_account_id
WHATSAPP_ACCESS_TOKEN=your_permanent_token
WHATSAPP_VERIFY_TOKEN=your_webhook_token
GEMINI_API_KEY=your_gemini_api_key
```

### 5. Verify Setup

```bash
python verify_setup.py
```

This will check:
- ✓ Environment variables
- ✓ Python dependencies
- ✓ WhatsApp API connection
- ✓ Gemini AI connection
- ✓ Image generation capabilities

## 🚀 Usage

### Development Mode

```bash
python main.py
```

This starts the webhook server on `http://localhost:8000`

### Using ngrok for Development

```bash
# Install ngrok from https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000

# Use the HTTPS URL provided by ngrok as your webhook URL in Meta Developer Console
```

### Production Deployment

#### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down
```

#### Manual Deployment

```bash
# Set environment to production
export ENVIRONMENT=production

# Run with multiple workers
python main.py
```

## 🎯 Features in Detail

### 1. WhatsApp Business API Integration

- **Send/Receive Messages**: Text, images, documents, audio
- **Interactive Messages**: Buttons, lists, quick replies
- **Message Templates**: Pre-approved templates for business-initiated conversations
- **Rich Media**: Upload and send media files
- **Message Status**: Delivery and read receipts
- **Rate Limiting**: Built-in protection against API limits

### 2. Enhanced Gemini AI

#### Tool Calling

The bot can execute functions to:
- **Get Current Time**: Respond to time/date queries
- **Perform Calculations**: Mathematical expressions
- **Google Search**: Real-time web information (when enabled)
- **Code Execution**: Run code for complex tasks

Example:
```
User: "What's 15% of 250?"
Bot: [Uses calculator tool] "37.5"

User: "What time is it?"
Bot: [Uses time tool] "It's 10:30 AM on Monday, January 19, 2025"
```

#### Image Generation

Generate and edit images using Gemini 2.5 Flash Image:

```
User: "Generate an image of a sunset over mountains"
Bot: [Generates and sends image]

User: "Make it more colorful"
Bot: [Edits the image with more vibrant colors]
```

Features:
- Text-to-image generation
- Image editing with prompts
- Multiple aspect ratios (1:1, 16:9, 9:16, etc.)
- High-quality output with SynthID watermark

#### Structured Outputs

Type-safe responses with JSON schema validation:

```python
from pydantic import BaseModel

class RecipeExtraction(BaseModel):
    recipe_name: str
    ingredients: List[str]
    instructions: List[str]

# Bot extracts structured data from unstructured text
```

### 3. Conversation Management

- **Context-Aware**: Maintains conversation history
- **Multi-turn**: Remembers previous exchanges
- **Context Queries**: "What did I ask earlier?"
- **Automatic Trimming**: Prevents unlimited history growth
- **Per-User History**: Separate conversations per user

### 4. Security & Rate Limiting

- **Webhook Signature Verification**: Validates requests from Meta
- **Rate Limiting**: Per-user message limits
- **Spam Detection**: Prevents abuse
- **Secure Secrets**: Environment-based configuration
- **HTTPS Only**: Encrypted communication

## 🔍 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/webhook` | GET | Webhook verification |
| `/webhook` | POST | Receive WhatsApp messages |
| `/stats` | GET | Bot statistics |

## 📊 Monitoring & Analytics

### Statistics Tracked

- Total messages received/processed
- AI responses generated
- Errors encountered
- Active conversations
- Uptime

### View Stats

```bash
curl http://localhost:8000/stats
```

### Logging

Structured JSON logging with:
- Timestamp
- Log level
- Message
- Context (user_id, message_type, etc.)

## 🔐 Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate access tokens** periodically
4. **Enable webhook signature verification** in production
5. **Use HTTPS** for webhook endpoint
6. **Implement rate limiting** to prevent abuse
7. **Monitor API usage** and costs

## 💰 Cost Estimation

### WhatsApp Business API

- Free tier: 1,000 conversations/month
- After that: $0.005 - $0.09 per conversation (varies by country)

### Gemini AI

- Gemini 2.5 Flash: $0.30/$0.075 per 1M input/output tokens
- Image generation: $30 per 1M tokens

**Example** (1,000 active users, 10,000 messages/month):
- WhatsApp: ~$50-100
- Gemini AI: ~$20-50
- Infrastructure: ~$30-100
- **Total**: ~$100-250/month

## 🐛 Troubleshooting

### Webhook Not Receiving Messages

1. Check webhook URL is publicly accessible (HTTPS)
2. Verify webhook token matches in .env
3. Check webhook subscriptions are enabled
4. Review webhook logs in Meta Developer Console

### Access Token Invalid

1. Regenerate access token in Meta Business Settings
2. Use System User token for production (never expires)
3. Verify token permissions include required scopes

### Gemini API Errors

1. Check API key is valid
2. Verify you haven't exceeded quota
3. Check model name is correct (`gemini-2.5-flash`)

### Message Send Failures

1. Verify phone number format (+1234567890)
2. Check 24-hour conversation window
3. Use approved templates for business-initiated messages
4. Review rate limits and quality rating

## 📚 Documentation

- **[WhatsApp Business API Setup](docs/WHATSAPP_BUSINESS_API_SETUP.md)**: Complete setup guide
- **[Production Architecture](docs/PRODUCTION_ARCHITECTURE.md)**: Architecture details and deployment
- **[Gemini Image Generation](https://ai.google.dev/gemini-api/docs/image-generation)**: Official image generation docs
- **[Gemini Tool Calling](https://ai.google.dev/gemini-api/docs/function-calling)**: Function calling guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini AI](https://ai.google.dev/) for the powerful AI capabilities
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp) for official messaging platform
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Pydantic](https://docs.pydantic.dev/) for data validation

## 📞 Support

For issues or questions:
1. Check the [troubleshooting section](#-troubleshooting)
2. Review the [documentation](docs/)
3. Open an [issue](https://github.com/your-username/Web-WhatsApp-Intelligent-Bot/issues)
4. Contact Meta Business Support for API-specific issues

---

**Made with ❤️ using WhatsApp Business API + Gemini AI**
