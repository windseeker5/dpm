"""
Groq AI Provider Implementation
Connects to Groq API for super-fast LLM inference
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

from ..ai_providers import AIProvider, AIRequest, AIResponse
from ..config import DEFAULT_AI_MODEL


class GroqProvider(AIProvider):
    """Groq AI provider for fast, free-tier cloud models"""

    # Groq API pricing (free tier = $0)
    PRICING = {
        'llama-3.3-70b-versatile': {'input': 0, 'output': 0},  # Free tier: 14,400 RPD, 30 RPM
        'llama-3.1-70b-versatile': {'input': 0, 'output': 0},  # Free tier
        'llama-3.1-8b-instant': {'input': 0, 'output': 0},  # Free tier (fastest)
        'llama-3.2-90b-text-preview': {'input': 0, 'output': 0},  # Free tier
        'mixtral-8x7b-32768': {'input': 0, 'output': 0},  # Free tier
        'gemma2-9b-it': {'input': 0, 'output': 0},  # Free tier
    }

    # Rate limits (free tier)
    RATE_LIMITS = {
        'requests_per_minute': 30,
        'requests_per_day': 14400,
        'tokens_per_minute': 30000,
    }

    def __init__(self, api_key: str, model: str = 'llama-3.3-70b-versatile'):
        super().__init__("groq", {"api_key": api_key, "model": model})
        self.api_key = api_key
        self.default_model = model
        self.base_url = "https://api.groq.com/openai/v1"

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Groq API"""
        start_time = time.time()

        if not self.api_key:
            return AIResponse(
                content="",
                model=request.model,
                provider=self.name,
                error="Groq API key not configured"
            )

        try:
            # Determine which model to use
            model = request.model if request.model and 'llama' in request.model.lower() or 'mixtral' in request.model.lower() or 'gemma' in request.model.lower() else self.default_model

            # Build messages array
            messages = []
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            messages.append({
                "role": "user",
                "content": request.prompt
            })

            # Prepare request payload (OpenAI-compatible format)
            payload = {
                "model": model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

            # Make async HTTP request
            endpoint = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=request.timeout_seconds)
                ) as response:
                    response_time_ms = int((time.time() - start_time) * 1000)

                    # Handle rate limiting
                    if response.status == 429:
                        error_data = await response.json()
                        error_msg = error_data.get('error', {}).get('message', 'Rate limit exceeded')
                        return AIResponse(
                            content="",
                            model=model,
                            provider=self.name,
                            response_time_ms=response_time_ms,
                            error=f"Groq API rate limit (429): {error_msg}"
                        )

                    # Handle other errors
                    if response.status != 200:
                        error_text = await response.text()
                        return AIResponse(
                            content="",
                            model=model,
                            provider=self.name,
                            response_time_ms=response_time_ms,
                            error=f"Groq API error ({response.status}): {error_text}"
                        )

                    # Parse successful response
                    data = await response.json()

                    # Extract content from OpenAI-compatible response
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

                    # Extract token usage
                    usage = data.get('usage', {})
                    input_tokens = usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0)
                    total_tokens = usage.get('total_tokens', input_tokens + output_tokens)

                    # Calculate cost (free tier = $0)
                    cost_cents = self.calculate_cost(input_tokens, output_tokens, model)

                    return AIResponse(
                        content=content,
                        model=model,
                        provider=self.name,
                        tokens_used=total_tokens,
                        cost_cents=cost_cents,
                        response_time_ms=response_time_ms,
                        metadata={
                            'input_tokens': input_tokens,
                            'output_tokens': output_tokens,
                            'rate_limits': self.RATE_LIMITS
                        }
                    )

        except asyncio.TimeoutError:
            return AIResponse(
                content="",
                model=request.model,
                provider=self.name,
                error="Groq API request timed out"
            )
        except aiohttp.ClientError as e:
            return AIResponse(
                content="",
                model=request.model,
                provider=self.name,
                error=f"Groq API connection error: {str(e)}"
            )
        except Exception as e:
            return AIResponse(
                content="",
                model=request.model,
                provider=self.name,
                error=f"Groq API unexpected error: {str(e)}"
            )

    def check_availability(self) -> bool:
        """Check if Groq API is available"""
        if not self.api_key:
            self.is_available = False
            return False

        try:
            # Simple synchronous check - just verify we have an API key
            # Full availability is checked async during actual requests
            self.is_available = True
            self.last_check = datetime.now()
            return True
        except Exception:
            self.is_available = False
            return False

    def get_available_models(self) -> list[str]:
        """Get list of available Groq models"""
        if not self.check_availability():
            return []

        # Return supported free-tier models
        return [
            'llama-3.3-70b-versatile',  # Best for general use
            'llama-3.1-70b-versatile',
            'llama-3.1-8b-instant',  # Fastest
            'llama-3.2-90b-text-preview',
            'mixtral-8x7b-32768',
            'gemma2-9b-it',
        ]

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> int:
        """Calculate cost in cents (free tier = $0)"""
        # All Groq free tier models are $0
        return 0


def create_groq_provider(api_key: str, model: str = 'llama-3.3-70b-versatile') -> GroqProvider:
    """Factory function to create and initialize Groq provider"""
    provider = GroqProvider(api_key, model)
    provider.check_availability()
    return provider
