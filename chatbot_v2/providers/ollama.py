"""
Ollama AI Provider Implementation
Connects to local or remote Ollama server
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

from ..ai_providers import AIProvider, AIRequest, AIResponse
from ..config import OLLAMA_BASE_URL, DEFAULT_AI_MODEL


class OllamaProvider(AIProvider):
    """Ollama AI provider for local/self-hosted models"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        super().__init__("ollama", {"base_url": base_url})
        self.base_url = base_url.rstrip('/')
        self.available_models_cache = []
        self.cache_expiry = None
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Ollama API"""
        start_time = time.time()
        
        try:
            # Prepare the prompt
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
            
            payload = {
                "model": request.model or DEFAULT_AI_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens
                }
            }
            
            # Make request to Ollama
            timeout = aiohttp.ClientTimeout(total=request.timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return AIResponse(
                            content="",
                            model=request.model,
                            provider=self.name,
                            error=f"Ollama API error: {response.status} - {error_text}"
                        )
                    
                    data = await response.json()
                    
                    # Extract response
                    content = data.get("response", "").strip()
                    
                    # Clean up common AI formatting issues
                    if content.startswith("```sql\n"):
                        content = content[6:]
                    if content.endswith("\n```"):
                        content = content[:-4]
                    
                    response_time_ms = int((time.time() - start_time) * 1000)
                    
                    return AIResponse(
                        content=content,
                        model=data.get("model", request.model),
                        provider=self.name,
                        tokens_used=0,  # Ollama doesn't return token count
                        cost_cents=0,   # Free local hosting
                        response_time_ms=response_time_ms,
                        metadata={
                            "eval_count": data.get("eval_count", 0),
                            "eval_duration": data.get("eval_duration", 0),
                            "prompt_eval_count": data.get("prompt_eval_count", 0)
                        }
                    )
                    
        except asyncio.TimeoutError:
            return AIResponse(
                content="",
                model=request.model,
                provider=self.name,
                error="Request timed out"
            )
        except Exception as e:
            return AIResponse(
                content="",
                model=request.model,
                provider=self.name,
                error=f"Ollama connection error: {str(e)}"
            )
    
    def check_availability(self) -> bool:
        """Check if Ollama server is available"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            self.is_available = response.status_code == 200
            self.last_check = datetime.now()
            return self.is_available
        except Exception:
            self.is_available = False
            self.last_check = datetime.now()
            return False
    
    def get_available_models(self) -> list[str]:
        """Get list of available models from Ollama"""
        # Return cached models if still valid
        if (self.cache_expiry and 
            datetime.now() < self.cache_expiry and 
            self.available_models_cache):
            return self.available_models_cache
        
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                
                # Cache for 5 minutes
                self.available_models_cache = models
                self.cache_expiry = datetime.now().replace(
                    minute=datetime.now().minute + 5
                )
                
                return models
        except Exception:
            pass
        
        # Return default model if API fails
        return [DEFAULT_AI_MODEL]
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> int:
        """Ollama is free, so cost is always 0"""
        return 0


# Helper function to create and configure Ollama provider
def create_ollama_provider(base_url: str = OLLAMA_BASE_URL) -> OllamaProvider:
    """Create and configure an Ollama provider"""
    provider = OllamaProvider(base_url)
    provider.check_availability()
    return provider