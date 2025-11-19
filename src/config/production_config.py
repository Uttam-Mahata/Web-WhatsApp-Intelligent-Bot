"""
Production Configuration for WhatsApp AI Bot

This module provides production-level configuration with environment variables,
validation, and secure secrets management.
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class WhatsAppConfig(BaseModel):
    """WhatsApp Business API Configuration"""

    phone_number_id: str = Field(..., description="WhatsApp Phone Number ID")
    business_account_id: str = Field(..., description="WhatsApp Business Account ID")
    access_token: str = Field(..., description="Permanent access token")
    api_version: str = Field(default="v21.0", description="WhatsApp API version")
    verify_token: str = Field(..., description="Webhook verification token")

    @property
    def base_url(self) -> str:
        """Base URL for WhatsApp Cloud API"""
        return f"https://graph.facebook.com/{self.api_version}"

    @property
    def send_message_url(self) -> str:
        """URL for sending messages"""
        return f"{self.base_url}/{self.phone_number_id}/messages"

    @property
    def media_url(self) -> str:
        """URL for media operations"""
        return f"{self.base_url}/{self.phone_number_id}/media"


class GeminiConfig(BaseModel):
    """Gemini AI Configuration"""

    api_key: str = Field(..., description="Gemini API key")
    model_name: str = Field(default="gemini-2.5-flash", description="Primary model for text")
    image_model_name: str = Field(default="gemini-2.5-flash-image", description="Model for image generation")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Response creativity (0-2)")
    max_output_tokens: int = Field(default=2048, ge=1, le=8192, description="Max response length")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int = Field(default=40, ge=1, le=100, description="Top-k sampling parameter")

    # Tool calling configuration
    enable_tools: bool = Field(default=True, description="Enable tool calling")
    enable_google_search: bool = Field(default=True, description="Enable Google Search grounding")
    enable_code_execution: bool = Field(default=True, description="Enable code execution")
    enable_image_generation: bool = Field(default=True, description="Enable image generation")

    # Image generation configuration
    default_aspect_ratio: str = Field(default="1:1", description="Default image aspect ratio")
    max_images_per_request: int = Field(default=1, ge=1, le=4, description="Max images to generate")

    @field_validator('default_aspect_ratio')
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        """Validate aspect ratio format"""
        valid_ratios = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
        if v not in valid_ratios:
            raise ValueError(f"Invalid aspect ratio. Must be one of: {valid_ratios}")
        return v


class WebhookConfig(BaseModel):
    """Webhook Server Configuration"""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    path: str = Field(default="/webhook", description="Webhook endpoint path")
    enable_ssl: bool = Field(default=False, description="Enable SSL (use reverse proxy in production)")
    ssl_certfile: Optional[str] = Field(default=None, description="SSL certificate file path")
    ssl_keyfile: Optional[str] = Field(default=None, description="SSL key file path")

    # Security
    enable_signature_verification: bool = Field(default=True, description="Verify webhook signatures")
    allowed_ips: Optional[List[str]] = Field(default=None, description="Whitelist IPs (None = allow all)")

    # Performance
    workers: int = Field(default=4, ge=1, le=32, description="Number of worker processes")
    max_concurrent_requests: int = Field(default=100, ge=1, description="Max concurrent requests")


class BotConfig(BaseModel):
    """Bot Behavior Configuration"""

    bot_name: str = Field(default="AI Assistant", description="Bot's display name")
    default_language: str = Field(default="en", description="Default language (en, bn)")
    max_conversation_history: int = Field(default=50, ge=1, le=200, description="Max messages to keep")
    response_delay: float = Field(default=0.5, ge=0.0, le=5.0, description="Delay before responding (seconds)")

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_messages: int = Field(default=10, ge=1, description="Max messages per window")
    rate_limit_window: int = Field(default=60, ge=1, description="Rate limit window (seconds)")

    # Spam detection
    spam_detection_enabled: bool = Field(default=True, description="Enable spam detection")
    max_message_length: int = Field(default=4000, ge=100, le=10000, description="Max message length")
    min_message_interval: float = Field(default=0.5, ge=0.0, description="Min seconds between messages")

    # Context query support
    enable_context_queries: bool = Field(default=True, description="Enable context-aware queries")
    context_keywords_en: List[str] = Field(
        default=["what did i ask", "previous question", "before", "earlier", "last time"],
        description="English context keywords"
    )
    context_keywords_bn: List[str] = Field(
        default=["আমি কি জিজ্ঞাসা করেছিলাম", "আগের প্রশ্ন", "আগে", "আগে কি"],
        description="Bengali context keywords"
    )


class LoggingConfig(BaseModel):
    """Logging Configuration"""

    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json, text)")
    log_file: Optional[str] = Field(default=None, description="Log file path (None = stdout only)")
    enable_access_logs: bool = Field(default=True, description="Enable HTTP access logs")
    enable_error_tracking: bool = Field(default=False, description="Enable Sentry error tracking")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v_upper


class RedisConfig(BaseModel):
    """Redis Configuration (Optional)"""

    enabled: bool = Field(default=False, description="Enable Redis")
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    ssl: bool = Field(default=False, description="Use SSL for Redis connection")

    # TTL settings
    session_ttl: int = Field(default=3600, ge=60, description="Session TTL (seconds)")
    cache_ttl: int = Field(default=300, ge=10, description="Cache TTL (seconds)")


class ProductionConfig(BaseSettings):
    """
    Production Configuration

    Loads all configuration from environment variables with validation.
    """

    # Component configurations
    whatsapp: WhatsAppConfig
    gemini: GeminiConfig
    webhook: WebhookConfig
    bot: BotConfig
    logging: LoggingConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())

    # Environment
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False

    @classmethod
    def from_env(cls) -> "ProductionConfig":
        """
        Load configuration from environment variables.

        Environment variables should be prefixed with component name:
        - WHATSAPP__PHONE_NUMBER_ID
        - GEMINI__API_KEY
        - WEBHOOK__PORT
        - BOT__BOT_NAME
        - LOGGING__LOG_LEVEL
        - REDIS__ENABLED

        Returns:
            ProductionConfig instance
        """
        return cls(
            whatsapp=WhatsAppConfig(
                phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
                business_account_id=os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
                access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
                api_version=os.getenv("WHATSAPP_API_VERSION", "v21.0"),
                verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN", ""),
            ),
            gemini=GeminiConfig(
                api_key=os.getenv("GEMINI_API_KEY", ""),
                model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
                image_model_name=os.getenv("GEMINI_IMAGE_MODEL_NAME", "gemini-2.5-flash-image"),
                temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
                enable_tools=os.getenv("GEMINI_ENABLE_TOOLS", "true").lower() == "true",
                enable_google_search=os.getenv("GEMINI_ENABLE_GOOGLE_SEARCH", "true").lower() == "true",
                enable_image_generation=os.getenv("GEMINI_ENABLE_IMAGE_GENERATION", "true").lower() == "true",
            ),
            webhook=WebhookConfig(
                host=os.getenv("WEBHOOK_HOST", "0.0.0.0"),
                port=int(os.getenv("WEBHOOK_PORT", "8000")),
                path=os.getenv("WEBHOOK_PATH", "/webhook"),
                workers=int(os.getenv("WEBHOOK_WORKERS", "4")),
            ),
            bot=BotConfig(
                bot_name=os.getenv("BOT_NAME", "AI Assistant"),
                default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
                max_conversation_history=int(os.getenv("MAX_CONVERSATION_HISTORY", "50")),
            ),
            logging=LoggingConfig(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_format=os.getenv("LOG_FORMAT", "json"),
                log_file=os.getenv("LOG_FILE"),
                sentry_dsn=os.getenv("SENTRY_DSN"),
            ),
            redis=RedisConfig(
                enabled=os.getenv("REDIS_ENABLED", "false").lower() == "true",
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD"),
            ),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

    def validate_required_fields(self) -> None:
        """
        Validate that all required fields are set.

        Raises:
            ValueError: If required fields are missing
        """
        errors = []

        # WhatsApp required fields
        if not self.whatsapp.phone_number_id:
            errors.append("WHATSAPP_PHONE_NUMBER_ID is required")
        if not self.whatsapp.business_account_id:
            errors.append("WHATSAPP_BUSINESS_ACCOUNT_ID is required")
        if not self.whatsapp.access_token:
            errors.append("WHATSAPP_ACCESS_TOKEN is required")
        if not self.whatsapp.verify_token:
            errors.append("WHATSAPP_VERIFY_TOKEN is required")

        # Gemini required fields
        if not self.gemini.api_key:
            errors.append("GEMINI_API_KEY is required")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"

    def get_system_instruction(self) -> str:
        """
        Get system instruction for the AI bot.

        Returns:
            System instruction string
        """
        return f"""You are {self.bot.bot_name}, an intelligent WhatsApp assistant powered by Google's Gemini AI.

Your capabilities:
1. Answer questions using your knowledge base
2. Search the web for current information using Google Search
3. Generate and edit images based on descriptions
4. Execute code for calculations and data processing
5. Provide weather information
6. Tell current time and date
7. Support both English and Bengali languages

Guidelines:
- Be helpful, accurate, and concise
- Detect the user's language and respond in the same language
- Use tools when needed (search, image generation, calculations)
- For time-sensitive information, use Google Search
- For creative visual requests, use image generation
- Keep responses conversational and friendly
- If unsure, admit it and offer to search for information

Remember:
- You are chatting via WhatsApp
- Users expect quick, mobile-friendly responses
- Format responses with clear paragraphs
- Use emojis sparingly and appropriately
- Respect user privacy and data security
"""


# Global configuration instance
config: Optional[ProductionConfig] = None


def get_config() -> ProductionConfig:
    """
    Get or create global configuration instance.

    Returns:
        ProductionConfig instance
    """
    global config
    if config is None:
        config = ProductionConfig.from_env()
        config.validate_required_fields()
    return config


def reload_config() -> ProductionConfig:
    """
    Reload configuration from environment.

    Returns:
        New ProductionConfig instance
    """
    global config
    config = ProductionConfig.from_env()
    config.validate_required_fields()
    return config
