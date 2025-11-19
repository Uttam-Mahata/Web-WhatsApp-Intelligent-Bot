# WhatsApp Business API Setup Guide

## Overview

This guide walks you through setting up the WhatsApp Business API for production use with the Intelligent Bot. The WhatsApp Business API provides a robust, scalable, and officially supported way to integrate WhatsApp messaging into your applications.

## Prerequisites

1. **Meta Business Account**: You need a Meta (Facebook) Business account
2. **WhatsApp Business Account**: Linked to your Meta Business account
3. **Phone Number**: A dedicated phone number for your WhatsApp Business account (cannot be used with regular WhatsApp)
4. **Server**: A publicly accessible server to receive webhooks (or ngrok for development)

## Setup Steps

### Step 1: Create a Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Select "Business" as the app type
4. Fill in app details:
   - App Name: `WhatsApp AI Bot` (or your preferred name)
   - App Contact Email: Your email
   - Business Account: Select your Meta Business account
5. Click "Create App"

### Step 2: Add WhatsApp Product

1. In your app dashboard, find "WhatsApp" in the products list
2. Click "Set up" to add WhatsApp to your app
3. You'll be directed to the WhatsApp setup page

### Step 3: Configure WhatsApp Business API

#### 3.1 Register Phone Number

1. In the WhatsApp section, go to "API Setup"
2. Click "Add phone number"
3. Choose your method:
   - **Option A**: Use a test number (for development)
   - **Option B**: Register your own phone number
4. Verify the phone number via SMS or voice call
5. Note down the following credentials:
   - **Phone Number ID**: Found in API Setup
   - **WhatsApp Business Account ID**: Found in API Setup
   - **App ID**: Found in App Settings → Basic
   - **App Secret**: Found in App Settings → Basic (click "Show")

#### 3.2 Generate Access Token

1. Go to "API Setup" in WhatsApp section
2. Under "Temporary access token", click "Generate token"
3. Copy the token (valid for 24 hours - for production, use System User token)

**For Production - Generate Permanent Token:**

1. Go to Meta Business Suite → Business Settings
2. Navigate to "System Users"
3. Click "Add" to create a new system user
4. Assign the system user to your app with these permissions:
   - `whatsapp_business_management`
   - `whatsapp_business_messaging`
5. Generate a token:
   - Click "Generate New Token"
   - Select your app
   - Choose permissions: `whatsapp_business_management`, `whatsapp_business_messaging`
   - Set expiration: "Never" (for production)
6. **Save this token securely** - you won't see it again

### Step 4: Set Up Webhook

Webhooks allow you to receive incoming messages and status updates.

#### 4.1 Configure Webhook URL

1. In WhatsApp section, go to "Configuration"
2. Click "Edit" next to "Webhook"
3. Enter your webhook details:
   - **Callback URL**: `https://your-domain.com/webhook` (must be HTTPS)
   - **Verify Token**: Create a random string (e.g., `my_secure_webhook_token_12345`)
4. Click "Verify and Save"

#### 4.2 Subscribe to Webhook Events

1. After webhook is verified, click "Manage"
2. Subscribe to these webhook fields:
   - `messages` (incoming messages)
   - `message_status` (delivery status, read receipts)
3. Click "Save"

**For Development (using ngrok):**

```bash
# Install ngrok
# Download from https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000

# Use the HTTPS URL provided by ngrok as your webhook URL
# Example: https://abc123.ngrok.io/webhook
```

### Step 5: Configure Environment Variables

Create a `.env` file in your project root:

```bash
# WhatsApp Business API Configuration
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token
WHATSAPP_VERIFY_TOKEN=my_secure_webhook_token_12345
WHATSAPP_API_VERSION=v21.0

# Webhook Configuration
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
WEBHOOK_PATH=/webhook

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Bot Configuration
BOT_NAME=AI Assistant
DEFAULT_LANGUAGE=en
MAX_CONVERSATION_HISTORY=50
LOG_LEVEL=INFO
```

### Step 6: Test Your Setup

#### 6.1 Send a Test Message

Use the API Setup page to send a test message:

1. In "API Setup", find "Send and receive messages"
2. Enter a recipient phone number (in international format: +1234567890)
3. Click "Send message"
4. Check if the message is received

#### 6.2 Test Incoming Messages

1. Save your WhatsApp Business number in your phone
2. Send a message to your WhatsApp Business number
3. Check if your webhook receives the message

### Step 7: Production Considerations

#### 7.1 Message Templates

For customer-initiated conversations, you can send any message. For business-initiated conversations, you must use approved message templates.

**Creating Message Templates:**

1. Go to WhatsApp Manager
2. Navigate to "Message Templates"
3. Click "Create Template"
4. Define template details:
   - Name: e.g., `welcome_message`
   - Category: Select appropriate category
   - Language: Select language(s)
   - Content: Define message with placeholders
5. Submit for approval (usually takes 24-48 hours)

#### 7.2 Rate Limits

WhatsApp Business API has tiered messaging limits:

- **Tier 1**: 1,000 business-initiated conversations per 24 hours
- **Tier 2**: 10,000 business-initiated conversations per 24 hours
- **Tier 3**: 100,000 business-initiated conversations per 24 hours
- **Tier 4**: Unlimited (requires approval)

**Quality Rating**: Maintain high quality rating to avoid restrictions
- Low quality rating can reduce your messaging limit
- Monitor your quality rating in WhatsApp Manager

#### 7.3 Security Best Practices

1. **Secure Token Storage**:
   - Never commit tokens to version control
   - Use environment variables or secret management services
   - Rotate tokens periodically

2. **Webhook Security**:
   - Validate webhook signatures
   - Use HTTPS only
   - Implement rate limiting
   - Whitelist Meta IP ranges

3. **Error Handling**:
   - Implement retry logic with exponential backoff
   - Log all API errors
   - Monitor API usage and errors

### Step 8: Verify Installation

Run the verification script:

```bash
python -m src.verify_setup
```

This will check:
- ✓ All environment variables are set
- ✓ Access token is valid
- ✓ Phone number is accessible
- ✓ Webhook is configured correctly
- ✓ Gemini API key is valid

## API Limits and Quotas

### Free Tier
- 1,000 free conversations per month
- After that: $0.005 - $0.09 per conversation (varies by country)

### Conversation Windows
- 24-hour window after last customer message
- Business can send any message within this window
- Outside window: must use approved templates

## Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Messages

**Problem**: Webhook verification fails or doesn't receive messages

**Solutions**:
- Ensure webhook URL is publicly accessible (HTTPS)
- Verify the verify token matches exactly
- Check webhook subscriptions are enabled
- Review webhook logs for errors

#### 2. Access Token Invalid

**Problem**: API calls return 401 Unauthorized

**Solutions**:
- Regenerate access token
- Check token permissions include required scopes
- Verify token hasn't expired
- Ensure token is for the correct app

#### 3. Message Send Failures

**Problem**: Messages fail to send

**Solutions**:
- Verify phone number format (international: +1234567890)
- Check phone number is registered on WhatsApp
- Ensure you're within 24-hour conversation window or using templates
- Review rate limits and quality rating

#### 4. SSL Certificate Errors

**Problem**: Webhook SSL verification fails

**Solutions**:
- Use valid SSL certificate (not self-signed)
- Ensure certificate chain is complete
- For dev: use ngrok which provides valid SSL

## Architecture Comparison

### Old Architecture (Selenium)
```
Bot → ChromeDriver → WhatsApp Web → Messages
```

**Limitations**:
- Requires browser automation
- Unstable (WhatsApp Web UI changes)
- QR code login required
- Not scalable
- Against WhatsApp Terms of Service

### New Architecture (Business API)
```
Bot → WhatsApp Business API → Messages
Webhook ← WhatsApp Business API ← Incoming Messages
```

**Advantages**:
- ✓ Official, supported by Meta
- ✓ No browser required
- ✓ Token-based authentication
- ✓ Scalable and reliable
- ✓ Production-ready
- ✓ Webhook-based real-time updates
- ✓ Rich media support (images, documents, locations)
- ✓ Message templates for business-initiated conversations

## Cost Estimation

Example pricing (varies by country):

| Country | Cost per Conversation |
|---------|----------------------|
| United States | $0.0088 |
| United Kingdom | $0.0165 |
| India | $0.0035 |
| Brazil | $0.0162 |

**Free Tier**: 1,000 conversations/month

**Example**: For 10,000 conversations/month in US: ~$80/month

## Next Steps

1. Complete the setup steps above
2. Run the installation verification script
3. Test sending and receiving messages
4. Deploy your bot to production
5. Monitor usage and quality metrics
6. Create message templates for proactive outreach

## Resources

- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Cloud API Quick Start](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Webhook Setup Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates)
- [WhatsApp Business Policy](https://www.whatsapp.com/legal/business-policy)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Meta's official documentation
3. Check the project's GitHub issues
4. Contact Meta Business Support for API-specific issues
