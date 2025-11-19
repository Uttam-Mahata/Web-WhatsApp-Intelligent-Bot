"""
Setup Verification Script

Verifies that the WhatsApp AI Bot is properly configured and ready to run.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_header(title: str):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_check(name: str, passed: bool, message: str = ""):
    """Print check result"""
    status = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {name}")
    if message:
        print(f"  → {message}")


async def main():
    """Run verification checks"""
    print("\n" + "=" * 60)
    print(" WhatsApp AI Bot - Setup Verification")
    print("=" * 60)

    all_checks_passed = True

    # ========================================================================
    # 1. Environment Variables
    # ========================================================================
    print_header("1. Environment Variables")

    required_env_vars = [
        ("WHATSAPP_PHONE_NUMBER_ID", "WhatsApp Phone Number ID"),
        ("WHATSAPP_BUSINESS_ACCOUNT_ID", "WhatsApp Business Account ID"),
        ("WHATSAPP_ACCESS_TOKEN", "WhatsApp Access Token"),
        ("WHATSAPP_VERIFY_TOKEN", "Webhook Verify Token"),
        ("GEMINI_API_KEY", "Gemini API Key"),
    ]

    for var_name, description in required_env_vars:
        value = os.getenv(var_name)
        passed = bool(value and value != f"your_{var_name.lower()}_here")
        print_check(description, passed,
                   "Set" if passed else f"Missing or not configured (set {var_name})")
        if not passed:
            all_checks_passed = False

    # ========================================================================
    # 2. Python Dependencies
    # ========================================================================
    print_header("2. Python Dependencies")

    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("httpx", "HTTPX"),
        ("google.genai", "Google GenAI", "google-genai"),
        ("PIL", "Pillow"),
    ]

    for module_name, display_name, *package_name in dependencies:
        pkg_name = package_name[0] if package_name else module_name
        try:
            __import__(module_name)
            print_check(display_name, True, f"{pkg_name} installed")
        except ImportError:
            print_check(display_name, False, f"Install with: pip install {pkg_name}")
            all_checks_passed = False

    # ========================================================================
    # 3. Configuration Loading
    # ========================================================================
    print_header("3. Configuration Loading")

    try:
        from src.config import get_config

        config = get_config()
        print_check("Configuration loaded", True, f"Environment: {config.environment}")

        # Validate required fields
        try:
            config.validate_required_fields()
            print_check("All required fields set", True)
        except ValueError as e:
            print_check("Required fields validation", False, str(e))
            all_checks_passed = False

    except Exception as e:
        print_check("Configuration loading", False, f"Error: {e}")
        all_checks_passed = False
        config = None

    # ========================================================================
    # 4. WhatsApp Business API Connection
    # ========================================================================
    if config:
        print_header("4. WhatsApp Business API")

        try:
            from src.whatsapp import WhatsAppBusinessAPIClient

            async with WhatsAppBusinessAPIClient(config.whatsapp) as whatsapp_client:
                # Try to get phone number info (simple API call)
                try:
                    url = f"{config.whatsapp.base_url}/{config.whatsapp.phone_number_id}"
                    response = await whatsapp_client._make_request("GET", url)
                    phone_number = response.get("display_phone_number", "Unknown")
                    print_check("WhatsApp API Connection", True,
                              f"Connected - Phone: {phone_number}")
                except Exception as e:
                    print_check("WhatsApp API Connection", False,
                              f"Failed to connect: {str(e)[:100]}")
                    all_checks_passed = False

        except Exception as e:
            print_check("WhatsApp Client Initialization", False, f"Error: {e}")
            all_checks_passed = False

    # ========================================================================
    # 5. Gemini AI Connection
    # ========================================================================
    if config:
        print_header("5. Gemini AI")

        try:
            from google import genai

            client = genai.Client(api_key=config.gemini.api_key)

            # Try a simple generation
            try:
                response = client.models.generate_content(
                    model=config.gemini.model_name,
                    contents="Say 'Hello' if you can read this.",
                )
                text = response.candidates[0].content.parts[0].text
                print_check("Gemini API Connection", True,
                          f"Model: {config.gemini.model_name}")
                print_check("Test Generation", True, f"Response: {text[:50]}...")

            except Exception as e:
                print_check("Gemini API Connection", False,
                          f"Failed: {str(e)[:100]}")
                all_checks_passed = False

        except Exception as e:
            print_check("Gemini Client Initialization", False, f"Error: {e}")
            all_checks_passed = False

    # ========================================================================
    # 6. Image Generation (Optional)
    # ========================================================================
    if config and config.gemini.enable_image_generation:
        print_header("6. Image Generation (Optional)")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=config.gemini.api_key)

            # Try a simple image generation
            try:
                response = client.models.generate_content(
                    model=config.gemini.image_model_name,
                    contents=["A small red circle"],
                    config=types.GenerateContentConfig(
                        response_modalities=["Image"]
                    ),
                )

                # Check if image was generated
                has_image = any(
                    part.inline_data for part in response.parts
                )

                print_check("Image Generation", has_image,
                          f"Model: {config.gemini.image_model_name}" if has_image
                          else "Failed to generate image")

            except Exception as e:
                print_check("Image Generation", False, f"Error: {str(e)[:100]}")

        except Exception as e:
            print_check("Image Generation Setup", False, f"Error: {e}")

    # ========================================================================
    # Summary
    # ========================================================================
    print_header("Verification Summary")

    if all_checks_passed:
        print("\n✓ All critical checks passed!")
        print("\nYour WhatsApp AI Bot is properly configured and ready to run.")
        print("\nNext steps:")
        print("1. Start the webhook server: python main.py")
        print("2. Expose your webhook URL (use ngrok for testing)")
        print("3. Configure webhook in Meta Developer Console")
        print("4. Send a test message to your WhatsApp Business number")
    else:
        print("\n✗ Some checks failed.")
        print("\nPlease fix the issues above before running the bot.")
        print("\nFor help, see:")
        print("- docs/WHATSAPP_BUSINESS_API_SETUP.md")
        print("- .env.example")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
