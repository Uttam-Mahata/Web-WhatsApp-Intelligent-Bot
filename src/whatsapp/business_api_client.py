"""
WhatsApp Business API Client

Production-ready client for WhatsApp Cloud API with retry logic,
rate limiting, and comprehensive error handling.
"""

import httpx
import logging
import asyncio
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta

from src.config.production_config import WhatsAppConfig
from src.models.whatsapp_models import (
    OutgoingTextMessage,
    OutgoingImageMessage,
    OutgoingAudioMessage,
    OutgoingDocumentMessage,
    OutgoingInteractiveMessage,
    OutgoingTemplateMessage,
    OutgoingReaction,
    MessageResponse,
    ErrorResponse,
    MediaUrlResponse,
    MarkAsReadRequest,
)


logger = logging.getLogger(__name__)


class WhatsAppAPIError(Exception):
    """WhatsApp API specific errors"""

    def __init__(self, message: str, code: int, error_subcode: Optional[int] = None):
        self.message = message
        self.code = code
        self.error_subcode = error_subcode
        super().__init__(self.message)


class RateLimitError(WhatsAppAPIError):
    """Rate limit exceeded error"""
    pass


class WhatsAppBusinessAPIClient:
    """
    WhatsApp Business API Client

    Provides methods to send messages, manage media, and interact with
    WhatsApp Cloud API.

    Features:
    - Async HTTP requests
    - Automatic retry with exponential backoff
    - Rate limiting
    - Comprehensive error handling
    - Type-safe with Pydantic models
    """

    def __init__(self, config: WhatsAppConfig, max_retries: int = 3, timeout: int = 30):
        """
        Initialize WhatsApp Business API Client.

        Args:
            config: WhatsApp configuration
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.config = config
        self.max_retries = max_retries
        self.timeout = timeout

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            headers={
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json",
            },
        )

        # Rate limiting (simple in-memory, use Redis for production)
        self._rate_limit_requests: Dict[str, list] = {}
        self._rate_limit_window = 60  # seconds
        self._rate_limit_max_requests = 80  # per phone number per window

        logger.info("WhatsApp Business API Client initialized")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("WhatsApp Business API Client closed")

    def _check_rate_limit(self, phone_number: str) -> bool:
        """
        Check if rate limit allows sending message.

        Args:
            phone_number: Target phone number

        Returns:
            True if within rate limit, False otherwise
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self._rate_limit_window)

        # Clean old requests
        if phone_number in self._rate_limit_requests:
            self._rate_limit_requests[phone_number] = [
                ts for ts in self._rate_limit_requests[phone_number] if ts > cutoff
            ]
        else:
            self._rate_limit_requests[phone_number] = []

        # Check limit
        if len(self._rate_limit_requests[phone_number]) >= self._rate_limit_max_requests:
            return False

        # Record request
        self._rate_limit_requests[phone_number].append(now)
        return True

    async def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            json_data: JSON payload
            files: Files to upload
            retry_count: Current retry attempt

        Returns:
            Response JSON

        Raises:
            WhatsAppAPIError: On API errors
            RateLimitError: On rate limit errors
        """
        try:
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                if files:
                    # For file uploads, don't set Content-Type (httpx will set it with boundary)
                    response = await self.client.post(
                        url,
                        files=files,
                        headers={"Authorization": f"Bearer {self.config.access_token}"},
                    )
                else:
                    response = await self.client.post(url, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Handle errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error = ErrorResponse(**error_data)
                    error_msg = error.error.message
                    error_code = error.error.code
                    error_subcode = error.error.error_subcode

                    logger.error(
                        f"WhatsApp API error: {error_msg} (code: {error_code}, subcode: {error_subcode})"
                    )

                    # Rate limit errors (code 130497 or 80007)
                    if error_code in [130497, 80007] or error_subcode == 2494055:
                        if retry_count < self.max_retries:
                            wait_time = 2 ** retry_count
                            logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            return await self._make_request(
                                method, url, json_data, files, retry_count + 1
                            )
                        raise RateLimitError(error_msg, error_code, error_subcode)

                    raise WhatsAppAPIError(error_msg, error_code, error_subcode)

                except Exception as e:
                    # If error parsing fails, raise generic error
                    logger.error(f"Failed to parse error response: {e}")
                    raise WhatsAppAPIError(
                        f"HTTP {response.status_code}: {response.text}",
                        response.status_code,
                    )

            return response.json()

        except httpx.TimeoutException:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                logger.warning(f"Request timeout. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, url, json_data, files, retry_count + 1)
            raise WhatsAppAPIError("Request timeout", 408)

        except httpx.NetworkError as e:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                logger.warning(f"Network error: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, url, json_data, files, retry_count + 1)
            raise WhatsAppAPIError(f"Network error: {e}", 503)

    # =========================================================================
    # Message Sending Methods
    # =========================================================================

    async def send_text_message(
        self, to: str, text: str, preview_url: bool = False
    ) -> MessageResponse:
        """
        Send text message.

        Args:
            to: Recipient's WhatsApp ID (phone number with country code)
            text: Message text
            preview_url: Enable URL previews

        Returns:
            MessageResponse with sent message details

        Raises:
            WhatsAppAPIError: On API errors
            RateLimitError: On rate limit errors
        """
        # Check rate limit
        if not self._check_rate_limit(to):
            raise RateLimitError(
                f"Rate limit exceeded for {to}. Max {self._rate_limit_max_requests} requests per {self._rate_limit_window}s",
                429,
            )

        message = OutgoingTextMessage.create(to=to, body=text, preview_url=preview_url)

        logger.info(f"Sending text message to {to}: {text[:50]}...")

        response_data = await self._make_request(
            "POST",
            self.config.send_message_url,
            json_data=message.model_dump(exclude_none=True),
        )

        response = MessageResponse(**response_data)
        logger.info(f"Message sent successfully. Message ID: {response.message_id}")
        return response

    async def send_image_message(
        self,
        to: str,
        media_id: Optional[str] = None,
        image_url: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> MessageResponse:
        """
        Send image message.

        Args:
            to: Recipient's WhatsApp ID
            media_id: Media ID from upload (either media_id or image_url required)
            image_url: Public image URL (either media_id or image_url required)
            caption: Optional image caption

        Returns:
            MessageResponse

        Raises:
            ValueError: If neither media_id nor image_url provided
            WhatsAppAPIError: On API errors
        """
        if not media_id and not image_url:
            raise ValueError("Either media_id or image_url must be provided")

        if not self._check_rate_limit(to):
            raise RateLimitError(f"Rate limit exceeded for {to}", 429)

        message = OutgoingImageMessage.create(
            to=to, media_id=media_id, link=image_url, caption=caption
        )

        logger.info(f"Sending image message to {to}")

        response_data = await self._make_request(
            "POST",
            self.config.send_message_url,
            json_data=message.model_dump(exclude_none=True),
        )

        response = MessageResponse(**response_data)
        logger.info(f"Image sent successfully. Message ID: {response.message_id}")
        return response

    async def send_interactive_message(
        self, to: str, body: str, buttons: list[Dict[str, str]]
    ) -> MessageResponse:
        """
        Send interactive message with buttons.

        Args:
            to: Recipient's WhatsApp ID
            body: Message body text
            buttons: List of buttons (max 3), format: [{"id": "btn1", "title": "Button 1"}, ...]

        Returns:
            MessageResponse

        Raises:
            ValueError: If buttons > 3 or invalid format
            WhatsAppAPIError: On API errors
        """
        if len(buttons) > 3:
            raise ValueError("Maximum 3 buttons allowed")

        if not all("id" in btn and "title" in btn for btn in buttons):
            raise ValueError("Each button must have 'id' and 'title'")

        if not self._check_rate_limit(to):
            raise RateLimitError(f"Rate limit exceeded for {to}", 429)

        message = OutgoingInteractiveMessage.create(to=to, body=body, buttons=buttons)

        logger.info(f"Sending interactive message to {to} with {len(buttons)} buttons")

        response_data = await self._make_request(
            "POST",
            self.config.send_message_url,
            json_data=message.model_dump(exclude_none=True),
        )

        response = MessageResponse(**response_data)
        logger.info(f"Interactive message sent. Message ID: {response.message_id}")
        return response

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[list] = None,
    ) -> MessageResponse:
        """
        Send approved template message.

        Args:
            to: Recipient's WhatsApp ID
            template_name: Name of approved template
            language_code: Language code (e.g., "en_US", "bn_IN")
            components: Template components with variables

        Returns:
            MessageResponse

        Raises:
            WhatsAppAPIError: On API errors
        """
        if not self._check_rate_limit(to):
            raise RateLimitError(f"Rate limit exceeded for {to}", 429)

        message = OutgoingTemplateMessage.create(
            to=to, template_name=template_name, language_code=language_code, components=components
        )

        logger.info(f"Sending template message '{template_name}' to {to}")

        response_data = await self._make_request(
            "POST",
            self.config.send_message_url,
            json_data=message.model_dump(exclude_none=True),
        )

        response = MessageResponse(**response_data)
        logger.info(f"Template message sent. Message ID: {response.message_id}")
        return response

    async def send_reaction(self, to: str, message_id: str, emoji: str) -> MessageResponse:
        """
        Send reaction to a message.

        Args:
            to: Recipient's WhatsApp ID
            message_id: Message ID to react to
            emoji: Emoji to react with (e.g., "👍", "❤️")

        Returns:
            MessageResponse

        Raises:
            WhatsAppAPIError: On API errors
        """
        message = OutgoingReaction.create(to=to, message_id=message_id, emoji=emoji)

        logger.info(f"Sending reaction {emoji} to message {message_id}")

        response_data = await self._make_request(
            "POST",
            self.config.send_message_url,
            json_data=message.model_dump(exclude_none=True),
        )

        return MessageResponse(**response_data)

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark message as read.

        Args:
            message_id: Message ID to mark as read

        Returns:
            API response

        Raises:
            WhatsAppAPIError: On API errors
        """
        request = MarkAsReadRequest(message_id=message_id)

        logger.debug(f"Marking message {message_id} as read")

        response_data = await self._make_request(
            "POST",
            self.config.send_message_url,
            json_data=request.model_dump(),
        )

        return response_data

    # =========================================================================
    # Media Methods
    # =========================================================================

    async def upload_media(self, file_path: str, mime_type: str) -> str:
        """
        Upload media file.

        Args:
            file_path: Path to media file
            mime_type: MIME type (e.g., "image/jpeg", "application/pdf")

        Returns:
            Media ID

        Raises:
            WhatsAppAPIError: On API errors
        """
        logger.info(f"Uploading media: {file_path} ({mime_type})")

        with open(file_path, "rb") as f:
            files = {
                "file": (file_path.split("/")[-1], f, mime_type),
                "messaging_product": (None, "whatsapp"),
            }

            response_data = await self._make_request(
                "POST",
                self.config.media_url,
                files=files,
            )

        media_id = response_data.get("id")
        logger.info(f"Media uploaded successfully. Media ID: {media_id}")
        return media_id

    async def get_media_url(self, media_id: str) -> MediaUrlResponse:
        """
        Get media download URL.

        Args:
            media_id: Media ID

        Returns:
            MediaUrlResponse with download URL

        Raises:
            WhatsAppAPIError: On API errors
        """
        url = f"{self.config.base_url}/{media_id}"

        logger.debug(f"Getting media URL for {media_id}")

        response_data = await self._make_request("GET", url)

        return MediaUrlResponse(**response_data)

    async def download_media(self, media_url: str) -> bytes:
        """
        Download media content.

        Args:
            media_url: Media download URL

        Returns:
            Media content as bytes

        Raises:
            WhatsAppAPIError: On API errors
        """
        logger.debug(f"Downloading media from {media_url}")

        response = await self.client.get(media_url)

        if response.status_code != 200:
            raise WhatsAppAPIError(
                f"Failed to download media: HTTP {response.status_code}",
                response.status_code,
            )

        return response.content

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook during setup.

        Args:
            mode: Verification mode (should be "subscribe")
            token: Verification token
            challenge: Challenge string from webhook verification

        Returns:
            Challenge string if verification successful, None otherwise
        """
        if mode == "subscribe" and token == self.config.verify_token:
            logger.info("Webhook verification successful")
            return challenge

        logger.warning(f"Webhook verification failed. Mode: {mode}, Token match: {token == self.config.verify_token}")
        return None
