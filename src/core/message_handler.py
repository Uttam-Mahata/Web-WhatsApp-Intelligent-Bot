"""
Message Handler

Processes incoming WhatsApp messages and coordinates responses.
"""

import logging
import asyncio
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta

from src.config.production_config import ProductionConfig
from src.models.whatsapp_models import WebhookPayload, Message
from src.whatsapp import WhatsAppBusinessAPIClient, WhatsAppAPIError
from src.ai import EnhancedGeminiAIClient


logger = logging.getLogger(__name__)


class MessageHandler:
    """
    Message Handler

    Coordinates processing of incoming messages:
    - Rate limiting and spam detection
    - Conversation history management
    - AI response generation
    - WhatsApp message sending
    """

    def __init__(
        self,
        config: ProductionConfig,
        whatsapp_client: WhatsAppBusinessAPIClient,
        ai_client: EnhancedGeminiAIClient,
    ):
        """
        Initialize Message Handler.

        Args:
            config: Production configuration
            whatsapp_client: WhatsApp Business API client
            ai_client: Enhanced Gemini AI client
        """
        self.config = config
        self.whatsapp = whatsapp_client
        self.ai = ai_client

        # Message tracking
        self.processed_messages: Set[str] = set()

        # Conversation history (phone_number -> List of messages)
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}

        # Rate limiting (phone_number -> List of timestamps)
        self.user_requests: Dict[str, List[datetime]] = {}

        # Spam detection (phone_number -> last message time)
        self.last_message_time: Dict[str, datetime] = {}

        # Statistics
        self.stats = {
            "total_messages_received": 0,
            "total_messages_processed": 0,
            "total_ai_responses": 0,
            "total_errors": 0,
            "start_time": datetime.now(),
        }

        logger.info("Message Handler initialized")

    async def process_webhook(self, payload: WebhookPayload) -> None:
        """
        Process incoming webhook payload.

        Args:
            payload: Webhook payload from WhatsApp
        """
        try:
            # Extract messages
            messages = payload.get_messages()

            if not messages:
                logger.debug("No messages in webhook payload")
                return

            self.stats["total_messages_received"] += len(messages)

            # Process each message
            for message in messages:
                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(f"Error processing message {message.id}: {e}", exc_info=True)
                    self.stats["total_errors"] += 1

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            self.stats["total_errors"] += 1

    async def _process_message(self, message: Message) -> None:
        """
        Process individual incoming message.

        Args:
            message: Incoming message
        """
        # Skip if already processed
        if message.id in self.processed_messages:
            logger.debug(f"Message {message.id} already processed, skipping")
            return

        # Mark as processed
        self.processed_messages.add(message.id)

        # Extract sender and text
        sender = message.from_
        text = message.message_text

        if not text:
            logger.debug(f"Message {message.id} has no text content, skipping")
            return

        logger.info(f"Processing message from {sender}: {text[:100]}...")

        # Mark message as read
        try:
            await self.whatsapp.mark_as_read(message.id)
        except Exception as e:
            logger.warning(f"Failed to mark message as read: {e}")

        # Rate limiting
        if self.config.bot.rate_limit_enabled:
            if not self._check_rate_limit(sender):
                logger.warning(f"Rate limit exceeded for {sender}")
                await self._send_rate_limit_message(sender)
                return

        # Spam detection
        if self.config.bot.spam_detection_enabled:
            if not self._check_spam(sender):
                logger.warning(f"Spam detected from {sender}")
                return

        # Check message length
        if len(text) > self.config.bot.max_message_length:
            logger.warning(f"Message too long from {sender}: {len(text)} characters")
            await self._send_error_message(
                sender, "Sorry, your message is too long. Please keep it under 4000 characters."
            )
            return

        # Add delay before responding
        if self.config.bot.response_delay > 0:
            await asyncio.sleep(self.config.bot.response_delay)

        # Check for context queries
        if self.config.bot.enable_context_queries:
            if self._is_context_query(text):
                response = self._get_context_response(sender)
                if response:
                    await self.whatsapp.send_text_message(sender, response)
                    self.stats["total_messages_processed"] += 1
                    return

        # Get conversation history
        history = self.conversation_history.get(sender, [])

        # Check for image generation request
        intent = self.ai.detect_intent(text)

        if intent["intent"] == "image_generation" and self.config.gemini.enable_image_generation:
            await self._handle_image_generation(sender, text)
            self.stats["total_messages_processed"] += 1
            return

        # Generate AI response
        try:
            response = await self.ai.generate_response(
                user_message=text,
                conversation_history=history,
                enable_tools=self.config.gemini.enable_tools,
            )

            # Add to conversation history
            self._add_to_history(sender, "user", text)
            self._add_to_history(sender, "assistant", response)

            # Send response
            await self.whatsapp.send_text_message(sender, response)

            self.stats["total_messages_processed"] += 1
            self.stats["total_ai_responses"] += 1

            logger.info(f"Response sent to {sender}")

        except Exception as e:
            logger.error(f"Error generating/sending response: {e}", exc_info=True)
            self.stats["total_errors"] += 1

            # Send error message to user
            await self._send_error_message(
                sender, "Sorry, I encountered an error processing your request. Please try again."
            )

    async def _handle_image_generation(self, sender: str, prompt: str) -> None:
        """
        Handle image generation request.

        Args:
            sender: User's phone number
            prompt: Image generation prompt
        """
        try:
            logger.info(f"Generating image for {sender}: {prompt[:100]}...")

            # Send "generating..." message
            await self.whatsapp.send_text_message(
                sender, "🎨 Generating your image, please wait..."
            )

            # Generate image
            results = await self.ai.generate_image(prompt=prompt, num_images=1)

            if results:
                result = results[0]

                # Upload image to WhatsApp
                # Save temporarily
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False) as f:
                    f.write(result.image_data)
                    temp_path = f.name

                try:
                    # Upload to WhatsApp
                    media_id = await self.whatsapp.upload_media(temp_path, "image/png")

                    # Send image
                    await self.whatsapp.send_image_message(
                        sender, media_id=media_id, caption=f"Generated: {prompt[:100]}"
                    )

                    logger.info(f"Image sent to {sender}")

                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

            else:
                await self._send_error_message(sender, "Sorry, I couldn't generate the image.")

        except Exception as e:
            logger.error(f"Image generation error: {e}", exc_info=True)
            await self._send_error_message(
                sender, "Sorry, there was an error generating your image. Please try again."
            )

    def _check_rate_limit(self, sender: str) -> bool:
        """Check if user is within rate limit"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.config.bot.rate_limit_window)

        # Clean old requests
        if sender in self.user_requests:
            self.user_requests[sender] = [
                ts for ts in self.user_requests[sender] if ts > window_start
            ]
        else:
            self.user_requests[sender] = []

        # Check limit
        if len(self.user_requests[sender]) >= self.config.bot.rate_limit_messages:
            return False

        # Record request
        self.user_requests[sender].append(now)
        return True

    def _check_spam(self, sender: str) -> bool:
        """Check for spam (messages too frequent)"""
        now = datetime.now()

        if sender in self.last_message_time:
            time_since_last = (now - self.last_message_time[sender]).total_seconds()
            if time_since_last < self.config.bot.min_message_interval:
                return False

        self.last_message_time[sender] = now
        return True

    def _is_context_query(self, text: str) -> bool:
        """Check if message is asking about conversation history"""
        text_lower = text.lower()

        # Check English keywords
        for keyword in self.config.bot.context_keywords_en:
            if keyword in text_lower:
                return True

        # Check Bengali keywords
        for keyword in self.config.bot.context_keywords_bn:
            if keyword in text:
                return True

        return False

    def _get_context_response(self, sender: str) -> Optional[str]:
        """Get response about conversation history"""
        history = self.conversation_history.get(sender, [])

        if not history:
            return "We haven't had any previous conversation yet."

        # Format recent messages
        recent_messages = history[-5:]  # Last 5 exchanges
        formatted = ["Here's what we discussed recently:\n"]

        for msg in recent_messages:
            role = "You" if msg["role"] == "user" else "Me"
            content = msg["content"][:100]  # Truncate long messages
            formatted.append(f"{role}: {content}...")

        return "\n".join(formatted)

    def _add_to_history(self, sender: str, role: str, content: str) -> None:
        """Add message to conversation history"""
        if sender not in self.conversation_history:
            self.conversation_history[sender] = []

        self.conversation_history[sender].append({"role": role, "content": content})

        # Trim history if too long
        max_history = self.config.bot.max_conversation_history
        if len(self.conversation_history[sender]) > max_history:
            # Keep most recent messages
            self.conversation_history[sender] = self.conversation_history[sender][-max_history:]

    async def _send_rate_limit_message(self, sender: str) -> None:
        """Send rate limit message"""
        try:
            message = (
                f"You're sending messages too quickly. "
                f"Please wait a moment before sending another message. "
                f"(Limit: {self.config.bot.rate_limit_messages} messages per "
                f"{self.config.bot.rate_limit_window} seconds)"
            )
            await self.whatsapp.send_text_message(sender, message)
        except Exception as e:
            logger.error(f"Error sending rate limit message: {e}")

    async def _send_error_message(self, sender: str, message: str) -> None:
        """Send error message to user"""
        try:
            await self.whatsapp.send_text_message(sender, message)
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    def get_stats(self) -> Dict:
        """Get handler statistics"""
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "active_conversations": len(self.conversation_history),
            "processed_message_ids": len(self.processed_messages),
        }
