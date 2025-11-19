"""
Enhanced Gemini AI Client

Advanced AI capabilities with:
- Tool calling (weather, time, search, calculator)
- Image generation and editing
- Structured outputs
- Google Search grounding
- Code execution
"""

import base64
import logging
import io
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from PIL import Image

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.config.production_config import GeminiConfig


logger = logging.getLogger(__name__)


# ============================================================================
# Tool Response Models
# ============================================================================

class WeatherInfo(BaseModel):
    """Weather information"""
    temperature: float = Field(description="Temperature in Celsius")
    conditions: str = Field(description="Weather conditions")
    location: str = Field(description="Location name")
    humidity: Optional[int] = None
    wind_speed: Optional[float] = None


class TimeInfo(BaseModel):
    """Time information"""
    current_time: str = Field(description="Current time")
    current_date: str = Field(description="Current date")
    timezone: str = Field(description="Timezone")
    day_of_week: str = Field(description="Day of the week")


class CalculationResult(BaseModel):
    """Calculation result"""
    expression: str = Field(description="Mathematical expression")
    result: Union[float, int, str] = Field(description="Calculation result")
    steps: Optional[List[str]] = None


class ImageGenerationResult(BaseModel):
    """Image generation result"""
    image_data: bytes = Field(description="Generated image as bytes")
    prompt: str = Field(description="Prompt used for generation")
    model: str = Field(description="Model used")
    aspect_ratio: Optional[str] = None


# ============================================================================
# Tool Definitions
# ============================================================================

def get_current_time() -> TimeInfo:
    """Get current time and date information"""
    now = datetime.now()
    return TimeInfo(
        current_time=now.strftime("%H:%M:%S"),
        current_date=now.strftime("%Y-%m-%d"),
        timezone="UTC",  # Configure based on user location
        day_of_week=now.strftime("%A"),
    )


def calculate(expression: str) -> CalculationResult:
    """
    Perform mathematical calculations safely.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        CalculationResult with result
    """
    try:
        # Safe evaluation (no exec, only eval with limited scope)
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        }

        # Remove any dangerous characters
        if any(char in expression for char in ["__", "import", "exec", "eval", "open", "file"]):
            raise ValueError("Invalid expression")

        result = eval(expression, {"__builtins__": {}}, allowed_names)

        return CalculationResult(
            expression=expression,
            result=result,
        )

    except Exception as e:
        logger.error(f"Calculation error for '{expression}': {e}")
        return CalculationResult(
            expression=expression,
            result=f"Error: {str(e)}",
        )


# ============================================================================
# Enhanced Gemini AI Client
# ============================================================================

class EnhancedGeminiAIClient:
    """
    Enhanced Gemini AI Client

    Features:
    - Tool calling for extended capabilities
    - Image generation and editing
    - Structured outputs
    - Google Search grounding
    - Code execution
    - Multi-turn conversations
    """

    def __init__(self, config: GeminiConfig, system_instruction: str):
        """
        Initialize Enhanced Gemini AI Client.

        Args:
            config: Gemini configuration
            system_instruction: System instruction for the bot
        """
        self.config = config
        self.system_instruction = system_instruction

        # Initialize Gemini client
        self.client = genai.Client(api_key=config.api_key)

        # Tool declarations for function calling
        self.tools = self._setup_tools() if config.enable_tools else []

        logger.info(
            f"Enhanced Gemini AI Client initialized with model {config.model_name}"
        )

    def _setup_tools(self) -> List[types.Tool]:
        """
        Set up available tools for function calling.

        Returns:
            List of tool configurations
        """
        tools = []

        # Google Search tool
        if self.config.enable_google_search:
            tools.append(types.Tool(google_search=types.GoogleSearch()))
            logger.info("Google Search tool enabled")

        # Code execution tool
        if self.config.enable_code_execution:
            tools.append(types.Tool(code_execution=types.CodeExecution()))
            logger.info("Code Execution tool enabled")

        # Custom function tools
        time_function = types.FunctionDeclaration(
            name="get_current_time",
            description="Get current time and date information including timezone and day of week",
            parameters={
                "type": "object",
                "properties": {},
            },
        )

        calculator_function = types.FunctionDeclaration(
            name="calculate",
            description="Perform mathematical calculations. Supports basic arithmetic, power, min, max, sum, round, abs.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'pow(2, 3)', 'round(3.14, 1)')",
                    }
                },
                "required": ["expression"],
            },
        )

        # Create function calling tool
        function_tool = types.Tool(
            function_declarations=[time_function, calculator_function]
        )
        tools.append(function_tool)

        logger.info(f"Configured {len(tools)} tools")
        return tools

    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        enable_tools: bool = True,
    ) -> str:
        """
        Generate AI response with tool calling support.

        Args:
            user_message: User's message
            conversation_history: Previous conversation messages
            enable_tools: Enable tool calling for this request

        Returns:
            AI response text
        """
        try:
            # Build contents from conversation history
            contents = self._build_contents(user_message, conversation_history)

            # Configure generation
            config_dict = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_output_tokens": self.config.max_output_tokens,
            }

            # Add tools if enabled
            if enable_tools and self.tools:
                config_dict["tools"] = self.tools

            # Generate response
            response = await self._generate_with_retry(
                model=self.config.model_name,
                contents=contents,
                config=types.GenerateContentConfig(**config_dict),
                system_instruction=self.system_instruction,
            )

            # Handle function calls
            if response.candidates[0].content.parts:
                first_part = response.candidates[0].content.parts[0]

                # Check if response contains function calls
                if hasattr(first_part, "function_call") and first_part.function_call:
                    return await self._handle_function_calls(response, contents)

            # Extract text response
            text_response = self._extract_text_from_response(response)

            logger.info(f"Generated response: {text_response[:100]}...")
            return text_response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    async def _generate_with_retry(
        self,
        model: str,
        contents: List[types.Content],
        config: types.GenerateContentConfig,
        system_instruction: str,
        max_retries: int = 3,
    ) -> types.GenerateContentResponse:
        """Generate content with retry logic"""
        import asyncio

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                    system_instruction=system_instruction,
                )
                return response

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Generation failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise

    async def _handle_function_calls(
        self, response: types.GenerateContentResponse, contents: List[types.Content]
    ) -> str:
        """
        Handle function calls from model response.

        Args:
            response: Model response with function calls
            contents: Original conversation contents

        Returns:
            Final text response after function execution
        """
        # Extract function calls
        function_responses = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                function_call = part.function_call
                function_name = function_call.name
                function_args = dict(function_call.args)

                logger.info(f"Executing function: {function_name} with args: {function_args}")

                # Execute function
                try:
                    if function_name == "get_current_time":
                        result = get_current_time()
                        function_response = result.model_dump()

                    elif function_name == "calculate":
                        result = calculate(function_args.get("expression", ""))
                        function_response = result.model_dump()

                    else:
                        function_response = {"error": f"Unknown function: {function_name}"}

                    logger.info(f"Function result: {function_response}")

                except Exception as e:
                    logger.error(f"Function execution error: {e}")
                    function_response = {"error": str(e)}

                # Create function response part
                function_responses.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=function_name, response=function_response
                        )
                    )
                )

        # Add function responses to conversation
        contents.append(types.Content(parts=function_responses, role="function"))

        # Generate final response with function results
        final_response = await self._generate_with_retry(
            model=self.config.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_output_tokens=self.config.max_output_tokens,
            ),
            system_instruction=self.system_instruction,
        )

        return self._extract_text_from_response(final_response)

    def _build_contents(
        self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[types.Content]:
        """
        Build contents list from conversation history.

        Args:
            user_message: Current user message
            conversation_history: Previous messages

        Returns:
            List of Content objects
        """
        contents = []

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                text = msg.get("content", "")

                # Map roles to Gemini format
                gemini_role = "user" if role in ["user", "human"] else "model"

                contents.append(types.Content(parts=[types.Part(text=text)], role=gemini_role))

        # Add current user message
        contents.append(types.Content(parts=[types.Part(text=user_message)], role="user"))

        return contents

    def _extract_text_from_response(self, response: types.GenerateContentResponse) -> str:
        """Extract text from Gemini response"""
        try:
            text_parts = []
            for part in response.candidates[0].content.parts:
                if part.text:
                    text_parts.append(part.text)

            return "\n".join(text_parts) if text_parts else "No response generated"

        except Exception as e:
            logger.error(f"Error extracting text from response: {e}")
            return "Error processing response"

    # =========================================================================
    # Image Generation
    # =========================================================================

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        num_images: int = 1,
    ) -> List[ImageGenerationResult]:
        """
        Generate images from text prompt.

        Args:
            prompt: Text description of image to generate
            aspect_ratio: Image aspect ratio (e.g., "16:9", "1:1", "9:16")
            num_images: Number of images to generate (1-4)

        Returns:
            List of ImageGenerationResult objects

        Raises:
            ValueError: If invalid parameters
        """
        if not self.config.enable_image_generation:
            raise ValueError("Image generation is not enabled")

        if num_images < 1 or num_images > self.config.max_images_per_request:
            raise ValueError(
                f"num_images must be between 1 and {self.config.max_images_per_request}"
            )

        logger.info(f"Generating {num_images} image(s) with prompt: {prompt[:100]}...")

        try:
            # Configure image generation
            config = types.GenerateContentConfig(
                response_modalities=["Image"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio or self.config.default_aspect_ratio
                ),
            )

            # Generate image
            response = self.client.models.generate_content(
                model=self.config.image_model_name, contents=[prompt], config=config
            )

            # Extract generated images
            results = []
            for part in response.parts:
                if part.inline_data:
                    # Convert to PIL Image
                    image = part.as_image()

                    # Convert to bytes
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format="PNG")
                    img_byte_arr.seek(0)

                    results.append(
                        ImageGenerationResult(
                            image_data=img_byte_arr.getvalue(),
                            prompt=prompt,
                            model=self.config.image_model_name,
                            aspect_ratio=aspect_ratio or self.config.default_aspect_ratio,
                        )
                    )

            logger.info(f"Successfully generated {len(results)} image(s)")
            return results

        except Exception as e:
            logger.error(f"Image generation error: {e}")
            raise

    async def edit_image(
        self,
        base_image: Union[str, bytes, Image.Image],
        edit_prompt: str,
        aspect_ratio: Optional[str] = None,
    ) -> ImageGenerationResult:
        """
        Edit an existing image using text prompt.

        Args:
            base_image: Input image (file path, bytes, or PIL Image)
            edit_prompt: Description of edits to make
            aspect_ratio: Output aspect ratio

        Returns:
            ImageGenerationResult with edited image

        Raises:
            ValueError: If image generation is not enabled
        """
        if not self.config.enable_image_generation:
            raise ValueError("Image generation is not enabled")

        logger.info(f"Editing image with prompt: {edit_prompt[:100]}...")

        try:
            # Load image
            if isinstance(base_image, str):
                pil_image = Image.open(base_image)
            elif isinstance(base_image, bytes):
                pil_image = Image.open(io.BytesIO(base_image))
            else:
                pil_image = base_image

            # Configure generation
            config = types.GenerateContentConfig(
                response_modalities=["Image"],
            )

            if aspect_ratio:
                config.image_config = types.ImageConfig(aspect_ratio=aspect_ratio)

            # Generate edited image
            response = self.client.models.generate_content(
                model=self.config.image_model_name,
                contents=[edit_prompt, pil_image],
                config=config,
            )

            # Extract edited image
            for part in response.parts:
                if part.inline_data:
                    edited_image = part.as_image()

                    # Convert to bytes
                    img_byte_arr = io.BytesIO()
                    edited_image.save(img_byte_arr, format="PNG")
                    img_byte_arr.seek(0)

                    logger.info("Image edited successfully")

                    return ImageGenerationResult(
                        image_data=img_byte_arr.getvalue(),
                        prompt=edit_prompt,
                        model=self.config.image_model_name,
                        aspect_ratio=aspect_ratio,
                    )

            raise ValueError("No image generated in response")

        except Exception as e:
            logger.error(f"Image editing error: {e}")
            raise

    # =========================================================================
    # Structured Outputs
    # =========================================================================

    async def generate_structured_output(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured output conforming to JSON schema.

        Args:
            prompt: User prompt
            response_schema: JSON schema for response
            conversation_history: Previous messages

        Returns:
            Parsed JSON object matching schema
        """
        try:
            contents = self._build_contents(prompt, conversation_history)

            # Configure structured output
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=response_schema,
                temperature=self.config.temperature,
            )

            # Generate response
            response = await self._generate_with_retry(
                model=self.config.model_name,
                contents=contents,
                config=config,
                system_instruction=self.system_instruction,
            )

            # Parse JSON response
            import json

            json_text = self._extract_text_from_response(response)
            result = json.loads(json_text)

            logger.info(f"Generated structured output: {json.dumps(result, indent=2)[:200]}...")
            return result

        except Exception as e:
            logger.error(f"Structured output error: {e}")
            raise

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def detect_intent(self, message: str) -> Dict[str, Any]:
        """
        Detect user intent from message.

        Returns:
            Dictionary with intent classification
        """
        message_lower = message.lower()

        intents = {
            "image_generation": any(
                keyword in message_lower
                for keyword in [
                    "generate image",
                    "create image",
                    "draw",
                    "picture of",
                    "make an image",
                    "ছবি তৈরি",
                    "ছবি বানাও",
                ]
            ),
            "calculation": any(
                keyword in message_lower
                for keyword in ["calculate", "compute", "what is", "গণনা কর"]
            ),
            "time_query": any(
                keyword in message_lower
                for keyword in [
                    "time",
                    "date",
                    "what day",
                    "কটা বাজে",
                    "আজ কি দিন",
                ]
            ),
            "web_search": any(
                keyword in message_lower
                for keyword in [
                    "search",
                    "find",
                    "latest",
                    "current",
                    "news",
                    "খুঁজে দাও",
                ]
            ),
        }

        detected_intent = "general" if not any(intents.values()) else max(
            intents, key=lambda k: intents[k]
        )

        return {"intent": detected_intent, "confidence": 0.8 if detected_intent != "general" else 0.5}
