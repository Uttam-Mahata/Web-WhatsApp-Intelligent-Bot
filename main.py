"""
WhatsApp AI Bot - Production Entry Point

Starts the FastAPI webhook server for WhatsApp Business API integration.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main():
    """Main entry point"""
    import uvicorn
    from src.config import get_config

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Load configuration to validate before starting
        config = get_config()

        logger.info("=" * 60)
        logger.info("WhatsApp AI Bot - Production v2.0")
        logger.info("Powered by WhatsApp Business API + Gemini AI")
        logger.info("=" * 60)
        logger.info(f"Environment: {config.environment}")
        logger.info(f"Webhook: {config.webhook.host}:{config.webhook.port}{config.webhook.path}")
        logger.info(f"AI Model: {config.gemini.model_name}")
        logger.info(f"Image Generation: {'Enabled' if config.gemini.enable_image_generation else 'Disabled'}")
        logger.info(f"Google Search: {'Enabled' if config.gemini.enable_google_search else 'Disabled'}")
        logger.info("=" * 60)

        # Start FastAPI server
        uvicorn.run(
            "src.webhook.server:app",
            host=config.webhook.host,
            port=config.webhook.port,
            workers=config.webhook.workers if not config.debug else 1,
            reload=config.debug,
            log_level=config.logging.log_level.lower(),
            access_log=config.logging.enable_access_logs,
        )

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("\nPlease check your .env file and ensure all required fields are set.")
        logger.error("See .env.example for reference.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
