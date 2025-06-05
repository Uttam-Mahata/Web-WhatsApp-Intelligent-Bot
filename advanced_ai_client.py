"""
Advanced Gemini AI client with Google Search grounding, function calling, and web context
"""
import json
import time
from typing import Optional, List, Dict, Any, Callable
from google import genai
from google.genai import types
from config import Config
from models import ConversationMessage

class AdvancedGeminiAIClient:
    """Advanced Gemini AI client with Google Search grounding and function calling"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[genai.Client] = None
        self.system_instruction = config.SYSTEM_INSTRUCTION
        self.function_registry = {}
        self._initialize_client()
        self._register_functions()
    
    def _initialize_client(self) -> None:
        """Initialize Gemini AI client"""
        try:
            self.client = genai.Client(api_key=self.config.GEMINI_API_KEY)
            print("Advanced Gemini AI client initialized successfully!")
        except Exception as e:
            print(f"Error initializing Gemini AI: {e}")
            raise
    
    def _register_functions(self):
        """Register available functions for the AI to call"""
        
        # Get current time function
        self.function_registry['get_current_time'] = self._get_current_time
        
        # Get weather function (placeholder)
        self.function_registry['get_weather'] = self._get_weather
        
        # Search information function (using Google Search grounding)
        self.function_registry['search_information'] = self._search_information
    
    def generate_response(self, user_message: str, conversation_context: str = "") -> str:
        """Generate AI response with advanced capabilities"""
        try:
            print(f"Generating advanced AI response for: {user_message}")
            
            # Detect if user message contains Bengali
            has_bengali = self._detect_bengali(user_message)
            
            # Check if this requires function calling or web search
            if self._requires_search_or_function(user_message):
                return self._generate_with_grounding_and_functions(user_message, conversation_context, has_bengali)
            else:
                return self._generate_simple_response(user_message, conversation_context, has_bengali)
            
        except Exception as e:
            print(f"Error generating advanced AI response: {e}")
            return self._get_fallback_response(user_message)
    
    def _requires_search_or_function(self, user_message: str) -> bool:
        """Determine if the message requires search or function calling"""
        # Keywords that typically require search or functions
        search_keywords = [
            'weather', 'current', 'today', 'now', 'search', 'find', 'look up',
            'information about', 'tell me about', 'what is', 'who is',
            'latest', 'recent', 'update', 'news', 'time', 'date',
            'details about', 'more about', 'explain', 'describe'
        ]
        
        # Bengali equivalents
        bengali_keywords = [
            'আবহাওয়া', 'বর্তমান', 'আজ', 'এখন', 'খুঁজ', 'তথ্য', 'সম্পর্কে বল',
            'কি', 'কে', 'সর্বশেষ', 'সাম্প্রতিক', 'সময়', 'তারিখ', 'বিস্তারিত'
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in search_keywords + bengali_keywords)
    
    def _generate_with_grounding_and_functions(self, user_message: str, context: str, has_bengali: bool) -> str:
        """Generate response using Google Search grounding OR function calling"""
        try:
            # Determine the best approach based on the query
            if self._needs_web_search(user_message):
                return self._generate_with_google_search(user_message, context, has_bengali)
            elif self.config.ENABLE_FUNCTION_CALLING and self._needs_function_call(user_message):
                return self._generate_with_functions(user_message, context, has_bengali)
            else:
                return self._generate_simple_response(user_message, context, has_bengali)
            
        except Exception as e:
            print(f"Error in advanced response generation: {e}")
            return self._generate_simple_response(user_message, context, has_bengali)
    
    def _needs_web_search(self, user_message: str) -> bool:
        """Check if message needs web search"""
        search_indicators = [
            'latest', 'recent', 'current', 'today', 'news', 'update', 'now',
            'who is', 'what is', 'tell me about', 'information about',
            'সর্বশেষ', 'সাম্প্রতিক', 'বর্তমান', 'আজ', 'এখন', 'সংবাদ', 'তথ্য'
        ]
        message_lower = user_message.lower()
        return any(indicator in message_lower for indicator in search_indicators)
    
    def _needs_function_call(self, user_message: str) -> bool:
        """Check if message needs function call"""
        function_indicators = [
            'time', 'date', 'weather', 'temperature', 'forecast',
            'সময়', 'তারিখ', 'আবহাওয়া', 'তাপমাত্রা'
        ]
        message_lower = user_message.lower()
        return any(indicator in message_lower for indicator in function_indicators)
    
    def _generate_with_google_search(self, user_message: str, context: str, has_bengali: bool) -> str:
        """Generate response using Google Search grounding"""
        try:
            full_prompt = self._create_enhanced_prompt(user_message, context, has_bengali)
            
            # Use Google Search tool for Gemini 2.0
            tools = [types.Tool(google_search=types.GoogleSearch())]
            
            generate_config = types.GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"],
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",  # Use stable version
                contents=full_prompt,
                config=generate_config
            )
            
            # Process grounded response
            response_text = ""
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
            
            # Check for grounding metadata
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    print("✓ Response includes grounded web search results")
            
            return self._clean_and_validate_response(response_text, has_bengali) if response_text else self._get_fallback_response(user_message)
            
        except Exception as e:
            print(f"Error in Google Search generation: {e}")
            return self._generate_simple_response(user_message, context, has_bengali)
    
    def _generate_with_functions(self, user_message: str, context: str, has_bengali: bool) -> str:
        """Generate response using function calling"""
        try:
            full_prompt = self._create_enhanced_prompt(user_message, context, has_bengali)
            
            # Define function declarations
            function_declarations = [
                {
                    "name": "get_current_time",
                    "description": "Gets the current date and time",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_weather",
                    "description": "Gets weather information for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city or location name"
                            }
                        },
                        "required": ["location"]
                    }
                },
            ]
            
            # Use function calling tool
            tools = [types.Tool(function_declarations=function_declarations)]
            
            generate_config = types.GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"]
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",  # Use stable version
                contents=full_prompt,
                config=generate_config
            )
            
            # Process the response with function calls
            return self._process_function_response(response, user_message, has_bengali)
            
        except Exception as e:
            print(f"Error in function calling generation: {e}")
            return self._generate_simple_response(user_message, context, has_bengali)
    
    def _process_function_response(self, response, user_message: str, has_bengali: bool) -> str:
        """Process response with function calls"""
        try:
            # Check if there are function calls
            response_text = ""
            function_calls = []
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Handle text parts
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
                    
                    # Handle function call parts
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
            
            # Execute function calls if any
            if function_calls:
                function_results = []
                for function_call in function_calls:
                    function_name = function_call.name
                    function_args = {}
                    
                    # Extract function arguments
                    if hasattr(function_call, 'args') and function_call.args:
                        for key, value in function_call.args.items():
                            function_args[key] = value
                    
                    print(f"✓ Executing function: {function_name} with args: {function_args}")
                    
                    # Execute the function
                    if function_name in self.function_registry:
                        try:
                            function_result = self.function_registry[function_name](**function_args)
                            function_results.append(function_result)
                        except Exception as e:
                            print(f"Error executing function {function_name}: {e}")
                            function_results.append(f"Error: Unable to execute {function_name}")
                
                # If we have function results, generate a final response
                if function_results:
                    all_results = "\n".join(function_results)
                    final_prompt = self._create_final_prompt(user_message, all_results, has_bengali)
                    
                    final_response = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=final_prompt
                    )
                    
                    return self._clean_and_validate_response(final_response.text.strip(), has_bengali)
            
            # Return the text response if no function calls
            if response_text:
                return self._clean_and_validate_response(response_text, has_bengali)
            else:
                return self._get_fallback_response(user_message)
            
        except Exception as e:
            print(f"Error processing function response: {e}")
            return self._get_fallback_response(user_message)
    
    def _generate_simple_response(self, user_message: str, context: str, has_bengali: bool) -> str:
        """Generate simple response without advanced features"""
        try:
            full_prompt = self._create_simple_prompt(user_message, context, has_bengali)
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",  # Use stable version
                contents=full_prompt
            )
            
            return self._clean_and_validate_response(response.text.strip(), has_bengali)
            
        except Exception as e:
            print(f"Error in simple response generation: {e}")
            return self._get_fallback_response(user_message)
    
    def _create_enhanced_prompt(self, user_message: str, context: str, has_bengali: bool) -> str:
        """Create enhanced prompt for advanced features"""
        if has_bengali:
            return f"""{self.system_instruction}

{context}

User message: "{user_message}"

You have access to:
- Google Search for current information
- Functions for time, weather, and information search
- Use these tools when the user asks for specific information

Be helpful and provide accurate, up-to-date information.
Respond in Bengali naturally and conversationally.
No emojis or special symbols."""
        else:
            return f"""{self.system_instruction}

{context}

User message: "{user_message}"

You have access to:
- Google Search for current information  
- Functions for time, weather, and information search
- Use these tools when the user asks for specific information

Be helpful and provide accurate, up-to-date information.
Respond in English naturally and conversationally.
No emojis or special symbols."""
    
    def _create_simple_prompt(self, user_message: str, context: str, has_bengali: bool) -> str:
        """Create simple prompt without advanced features"""
        if has_bengali:
            return f"""{self.system_instruction}

{context}

User message: "{user_message}"

Respond naturally in Bengali, considering our conversation history.
Keep it helpful and conversational.
No emojis or special symbols."""
        else:
            return f"""{self.system_instruction}

{context}

User message: "{user_message}"

Respond naturally in English, considering our conversation history.
Keep it helpful and conversational.
No emojis or special symbols."""
    
    def _create_final_prompt(self, user_message: str, function_result: str, has_bengali: bool) -> str:
        """Create final prompt after function execution"""
        if has_bengali:
            return f"""User asked: "{user_message}"

Function result: {function_result}

Based on this information, provide a helpful response in Bengali.
Be conversational and natural. Present the information clearly.
No emojis or special symbols."""
        else:
            return f"""User asked: "{user_message}"

Function result: {function_result}

Based on this information, provide a helpful response in English.
Be conversational and natural. Present the information clearly.
No emojis or special symbols."""
    
    def _get_current_time(self) -> str:
        """Get current date and time"""
        import datetime
        now = datetime.datetime.now()
        return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A, %B %d, %Y')})"
    
    def _get_weather(self, location: str) -> str:
        """Get weather information using a simple approach"""
        try:
            # This is a placeholder that provides a realistic response
            # In a production system, you'd integrate with a weather API like OpenWeatherMap
            import random
            
            # Simulate basic weather conditions
            conditions = ["sunny", "cloudy", "partly cloudy", "overcast", "light rain", "clear"]
            temperatures = list(range(15, 35))  # Celsius
            
            condition = random.choice(conditions)
            temp = random.choice(temperatures)
            
            return f"Weather in {location}: {condition.title()}, approximately {temp}°C. Note: This is simulated data. For accurate weather, please check a reliable weather service."
            
        except Exception as e:
            return f"Unable to get weather information for {location}. Please check a weather app or website for current conditions."
    
    def _search_information(self, query: str) -> str:
        """Search for information - this will work with Google Search grounding"""
        # This function mainly serves as a trigger for the AI to use grounding
        # The actual search results will come from Google Search grounding
        return f"Searching for current information about: {query}. Please provide accurate and up-to-date information based on available sources."
    
    def _detect_bengali(self, text: str) -> bool:
        """Detect if text contains Bengali characters"""
        bengali_chars = 'আঅইউএওকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ'
        return any(char in text for char in bengali_chars)
    
    def _clean_and_validate_response(self, response: str, has_bengali: bool) -> str:
        """Clean and validate AI response"""
        # Clean the response
        response = self._clean_response_text(response)
        
        # Ensure response is not empty
        if not response or len(response.strip()) < 2:
            if has_bengali:
                response = "আমি বুঝতে পারছি।"
            else:
                response = "I understand."
        
        # Limit response length
        if len(response) > self.config.MAX_RESPONSE_LENGTH:
            response = response[:self.config.MAX_RESPONSE_LENGTH - 3] + "..."
        
        return response
    
    def _clean_response_text(self, text: str) -> str:
        """Remove emojis and non-BMP characters that cause ChromeDriver issues"""
        if not text:
            return ""
        
        import re
        # Remove emojis and other non-BMP characters
        text = re.sub(r'[^\x00-\x7F\u00A0-\uFFFF]', '', text)
        # Remove common emoji patterns
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # emoticons
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # symbols & pictographs
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # transport & map
        text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # flags
        text = re.sub(r'[\U00002702-\U000027B0]', '', text)  # dingbats
        text = re.sub(r'[\U000024C2-\U0001F251]', '', text)  # enclosed characters
        # Clean up extra spaces
        text = ' '.join(text.split())
        return text.strip()
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Get fallback response when AI generation fails"""
        has_bengali = self._detect_bengali(user_message)
        if has_bengali:
            return "দুঃখিত, একটু সমস্যা হচ্ছে।"
        else:
            return "Sorry, having some trouble right now."
    
    def create_conversation_summary(self, conversation_history: List[ConversationMessage]) -> str:
        """Create a summary of the conversation"""
        if len(conversation_history) < 6:
            return ""
        
        try:
            # Prepare conversation text for summarization
            conversation_text = "\n".join([
                f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in conversation_history[:-2]  # Exclude last 2 messages
            ])
            
            summary_prompt = f"""Summarize this conversation in 1-2 sentences, focusing on key topics and context:
            
            {conversation_text}
            
            Summary:"""
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",  # Use stable version
                contents=summary_prompt
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error creating conversation summary: {e}")
            return ""
