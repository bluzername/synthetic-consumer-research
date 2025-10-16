"""OpenRouter API manager with rate limiting, retry logic, and cost tracking."""

import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from openai import OpenAI
from pydantic import BaseModel

from .config_loader import get_config
from .models import APICallLog


class OpenRouterClient:
    """Wrapper for OpenRouter API with enhanced features."""
    
    def __init__(self):
        """Initialize OpenRouter client."""
        from .exceptions import AuthenticationError
        
        self.config = get_config()
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not self.api_key:
            raise AuthenticationError()
        
        # Initialize OpenAI client pointing to OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        
        # Cost tracking
        self.call_logs: List[APICallLog] = []
        self.total_cost = 0.0
        
        # Rate limiting
        self.call_times: List[float] = []
        self.rate_limit = self.config.api_rate_limit
        self.rate_period = self.config.api_rate_period
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = time.time()
        
        # Remove old calls outside the rate period
        self.call_times = [t for t in self.call_times if now - t < self.rate_period]
        
        # Check if we're at the limit
        if len(self.call_times) >= self.rate_limit:
            # Calculate wait time
            oldest_call = min(self.call_times)
            wait_time = self.rate_period - (now - oldest_call)
            if wait_time > 0:
                print(f"Rate limit reached. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                self.call_times = []
        
        # Record this call
        self.call_times.append(time.time())
    
    def _retry_with_backoff(self, func, max_retries: Optional[int] = None):
        """Execute function with exponential backoff retry."""
        if max_retries is None:
            max_retries = self.config.api_retry_attempts
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                wait_time = (2 ** attempt) * 1  # Exponential backoff
                print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
    
    def _log_call(self, model: str, operation: str, input_tokens: Optional[int] = None,
                  output_tokens: Optional[int] = None, success: bool = True,
                  error_message: Optional[str] = None):
        """Log API call for cost tracking."""
        log_entry = APICallLog(
            timestamp=datetime.now().isoformat(),
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=None,  # Can be calculated based on pricing
            success=success,
            error_message=error_message,
        )
        
        self.call_logs.append(log_entry)
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Call chat completion API with rate limiting and retry.
        
        Args:
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            messages: List of message dicts with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})
        
        Returns:
            API response dict
        """
        self._check_rate_limit()
        
        def _call():
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**kwargs)
            return response
        
        try:
            response = self._retry_with_backoff(_call)
            
            # Log successful call
            self._log_call(
                model=model,
                operation="chat_completion",
                input_tokens=getattr(response.usage, 'prompt_tokens', None),
                output_tokens=getattr(response.usage, 'completion_tokens', None),
                success=True,
            )
            
            return response
        
        except Exception as e:
            from .exceptions import RateLimitError, AuthenticationError, ModelNotFoundError, APIError
            
            # Log failed call
            self._log_call(
                model=model,
                operation="chat_completion",
                success=False,
                error_message=str(e),
            )
            
            # Provide helpful error messages
            error_str = str(e).lower()
            if "rate" in error_str and "limit" in error_str:
                raise RateLimitError() from e
            elif "auth" in error_str or "unauthorized" in error_str or "401" in error_str:
                raise AuthenticationError() from e
            elif "not found" in error_str or "404" in error_str:
                raise ModelNotFoundError(model) from e
            elif "timeout" in error_str:
                raise APIError(
                    f"Request timeout for model {model}. "
                    f"Try increasing 'api.timeout' in config/settings.yaml or use a faster model."
                ) from e
            else:
                raise APIError(f"API call failed: {str(e)}") from e
    
    def chat_completion_with_structured_output(
        self,
        model: str,
        messages: List[Dict[str, str]],
        response_model: type[BaseModel],
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> BaseModel:
        """
        Call chat completion with structured Pydantic output.
        
        Args:
            model: Model identifier
            messages: List of message dicts
            response_model: Pydantic model class for response
            temperature: Sampling temperature
            max_tokens: Maximum tokens
        
        Returns:
            Parsed Pydantic model instance
        """
        # Add JSON formatting instruction to system message
        system_msg = next((m for m in messages if m["role"] == "system"), None)
        
        json_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{response_model.model_json_schema()}"
        
        if system_msg:
            system_msg["content"] += json_instruction
        else:
            messages.insert(0, {
                "role": "system",
                "content": f"You are a helpful assistant.{json_instruction}"
            })
        
        response = self.chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        
        # Parse response into Pydantic model
        content = response.choices[0].message.content
        
        try:
            data = json.loads(content)
            return response_model(**data)
        except Exception as e:
            print(f"Failed to parse response as {response_model.__name__}: {e}")
            print(f"Raw response: {content}")
            raise
    
    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        size: str = "1024x1024",
        n: int = 1,
    ) -> List[str]:
        """
        Generate images using OpenRouter image models.
        
        Args:
            prompt: Image generation prompt
            model: Model to use (defaults to config)
            size: Image size
            n: Number of images
        
        Returns:
            List of image URLs
        """
        if model is None:
            model = self.config.image_generator_model
        
        self._check_rate_limit()
        
        # OpenRouter uses chat completion for image generation models
        # The model returns markdown with image URLs
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        def _call():
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
            )
            return response
        
        try:
            response = self._retry_with_backoff(_call)
            
            # Log successful call
            self._log_call(
                model=model,
                operation="image_generation",
                success=True,
            )
            
            # Extract image URLs from markdown response
            content = response.choices[0].message.content
            urls = self._extract_image_urls_from_markdown(content)
            
            if not urls:
                self.logger.log_warning(f"No image URLs found in response: {content[:200]}")
            
            return urls
        
        except Exception as e:
            from .exceptions import ImageGenerationError
            
            # Log failed call
            self._log_call(
                model=model,
                operation="image_generation",
                success=False,
                error_message=str(e),
            )
            
            # Provide helpful error message
            print(f"Image generation failed: {e}")
            print("Tip: You can disable image generation in config/settings.yaml: features.enable_image_generation = false")
            
            # Return empty list instead of raising to allow graceful degradation
            return []
    
    def _extract_image_urls_from_markdown(self, content: str) -> List[str]:
        """Extract image URLs from markdown content."""
        import re
        # Look for markdown images: ![alt](url)
        markdown_pattern = r'!\[.*?\]\((https?://[^\)]+)\)'
        urls = re.findall(markdown_pattern, content)
        
        # Also look for plain URLs
        if not urls:
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, content)
        
        return urls
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get summary of API costs.
        
        Returns:
            Dict with cost breakdown
        """
        successful_calls = [log for log in self.call_logs if log.success]
        failed_calls = [log for log in self.call_logs if not log.success]
        
        # Group by model
        calls_by_model = {}
        for log in successful_calls:
            if log.model not in calls_by_model:
                calls_by_model[log.model] = []
            calls_by_model[log.model].append(log)
        
        # Calculate token usage by model
        model_stats = {}
        for model, logs in calls_by_model.items():
            total_input = sum(log.input_tokens or 0 for log in logs)
            total_output = sum(log.output_tokens or 0 for log in logs)
            model_stats[model] = {
                "calls": len(logs),
                "input_tokens": total_input,
                "output_tokens": total_output,
            }
        
        return {
            "total_calls": len(self.call_logs),
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "model_stats": model_stats,
        }
    
    def save_logs(self, filepath: str):
        """Save API call logs to JSON file."""
        logs_data = [log.model_dump() for log in self.call_logs]
        
        with open(filepath, 'w') as f:
            json.dump(logs_data, f, indent=2)
    
    def clear_logs(self):
        """Clear API call logs."""
        self.call_logs = []
        self.total_cost = 0.0


# Global client instance
_client: Optional[OpenRouterClient] = None


def get_openrouter_client() -> OpenRouterClient:
    """Get global OpenRouter client instance."""
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client

