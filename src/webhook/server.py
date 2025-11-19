"""
FastAPI Webhook Server for WhatsApp Business API

Receives incoming messages and events from WhatsApp Cloud API.
"""

import logging
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException, Query
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from src.config import get_config
from src.models.whatsapp_models import WebhookPayload
from src.whatsapp import WhatsAppBusinessAPIClient
from src.ai import EnhancedGeminiAIClient
from src.core.message_handler import MessageHandler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global instances
config = None
whatsapp_client = None
ai_client = None
message_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global config, whatsapp_client, ai_client, message_handler

    # Startup
    logger.info("Starting WhatsApp AI Bot...")

    # Load configuration
    config = get_config()
    logger.info(f"Configuration loaded for environment: {config.environment}")

    # Initialize WhatsApp client
    whatsapp_client = WhatsAppBusinessAPIClient(config.whatsapp)
    logger.info("WhatsApp Business API client initialized")

    # Initialize AI client
    ai_client = EnhancedGeminiAIClient(
        config.gemini, system_instruction=config.get_system_instruction()
    )
    logger.info("Enhanced Gemini AI client initialized")

    # Initialize message handler
    message_handler = MessageHandler(config, whatsapp_client, ai_client)
    logger.info("Message handler initialized")

    logger.info("✅ WhatsApp AI Bot started successfully!")

    yield

    # Shutdown
    logger.info("Shutting down WhatsApp AI Bot...")
    if whatsapp_client:
        await whatsapp_client.close()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WhatsApp AI Bot Webhook",
    description="Production webhook server for WhatsApp Business API",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "WhatsApp AI Bot",
        "version": "2.0.0",
        "status": "running",
        "environment": config.environment if config else "unknown",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "whatsapp_client": whatsapp_client is not None,
        "ai_client": ai_client is not None,
        "message_handler": message_handler is not None,
    }

    if not all([whatsapp_client, ai_client, message_handler]):
        raise HTTPException(status_code=503, detail="Service not fully initialized")

    return health_status


@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    """
    Webhook verification endpoint.

    WhatsApp sends a GET request during webhook setup to verify the endpoint.

    Args:
        mode: Verification mode (should be "subscribe")
        token: Verification token (must match configured token)
        challenge: Challenge string to echo back

    Returns:
        Challenge string if verification successful

    Raises:
        HTTPException: If verification fails
    """
    logger.info(f"Webhook verification request: mode={mode}, token={'***' if token else None}")

    verification = await whatsapp_client.verify_webhook(mode, token, challenge)

    if verification:
        logger.info("✅ Webhook verification successful")
        return PlainTextResponse(content=verification)

    logger.error("❌ Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Receive webhook POST requests from WhatsApp.

    This endpoint receives incoming messages, status updates, and other events.

    Args:
        request: FastAPI request object

    Returns:
        200 OK response

    Raises:
        HTTPException: On processing errors
    """
    try:
        # Parse request body
        body = await request.json()

        logger.info(f"Received webhook: {body.get('object', 'unknown')}")
        logger.debug(f"Webhook payload: {body}")

        # Validate payload structure
        try:
            payload = WebhookPayload(**body)
        except Exception as e:
            logger.error(f"Invalid webhook payload: {e}")
            # Return 200 to prevent WhatsApp retries for invalid payloads
            return Response(status_code=200)

        # Process messages asynchronously (don't block webhook response)
        asyncio.create_task(message_handler.process_webhook(payload))

        # Always return 200 OK immediately
        return Response(status_code=200)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        # Still return 200 to prevent WhatsApp retries
        return Response(status_code=200)


@app.get("/stats")
async def get_stats():
    """Get bot statistics"""
    if message_handler:
        return message_handler.get_stats()
    return {"error": "Message handler not initialized"}


# Development server runner
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.webhook.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
