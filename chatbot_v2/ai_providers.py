"""
Abstract AI Provider Interface
Defines the contract for all AI providers (Ollama, Anthropic, OpenAI)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class AIResponse:
    """Standard response format from AI providers"""
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    cost_cents: int = 0
    response_time_ms: int = 0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIRequest:
    """Standard request format to AI providers"""
    prompt: str
    model: str
    system_prompt: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 1000
    timeout_seconds: int = 30


class AIProvider(ABC):
    """Abstract base class for all AI providers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_available = False
        self.last_check = None
    
    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate AI response from prompt"""
        pass
    
    @abstractmethod
    def check_availability(self) -> bool:
        """Check if the provider is currently available"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get list of available models from this provider"""
        pass
    
    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> int:
        """Calculate cost in cents for the given token usage"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current provider status"""
        return {
            'name': self.name,
            'available': self.is_available,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'models': self.get_available_models() if self.is_available else []
        }


class AIProviderManager:
    """Manages multiple AI providers with fallback logic"""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.primary_provider = None
        self.fallback_order = []
    
    def register_provider(self, provider: AIProvider, is_primary: bool = False):
        """Register an AI provider"""
        self.providers[provider.name] = provider
        if is_primary:
            self.primary_provider = provider.name
        if provider.name not in self.fallback_order:
            self.fallback_order.append(provider.name)
    
    def get_provider(self, name: str) -> Optional[AIProvider]:
        """Get a specific provider by name"""
        return self.providers.get(name)
    
    async def generate(self, request: AIRequest, preferred_provider: Optional[str] = None) -> AIResponse:
        """Generate response using preferred provider or fallback chain"""
        
        # Determine provider order
        provider_order = []
        if preferred_provider and preferred_provider in self.providers:
            provider_order.append(preferred_provider)
        elif self.primary_provider:
            provider_order.append(self.primary_provider)
        
        # Add fallback providers
        for provider_name in self.fallback_order:
            if provider_name not in provider_order:
                provider_order.append(provider_name)
        
        # Try each provider in order
        last_error = None
        for provider_name in provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
                
            try:
                # Check availability first
                if not provider.check_availability():
                    continue
                
                # Generate response
                response = await provider.generate(request)
                if response.error is None:
                    return response
                else:
                    last_error = response.error
                    
            except Exception as e:
                last_error = str(e)
                continue
        
        # All providers failed
        return AIResponse(
            content="",
            model=request.model,
            provider="none",
            error=f"All AI providers failed. Last error: {last_error}"
        )
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered providers"""
        return {name: provider.get_status() for name, provider in self.providers.items()}


# Global provider manager instance
provider_manager = AIProviderManager()


# Auto-register available providers
def _initialize_providers():
    """Initialize and register all enabled AI providers"""
    from .config import (
        CHATBOT_ENABLE_GEMINI, GOOGLE_AI_API_KEY,
        CHATBOT_ENABLE_GROQ, GROQ_API_KEY,
        CHATBOT_ENABLE_OLLAMA, OLLAMA_BASE_URL
    )

    # Register Gemini (primary)
    if CHATBOT_ENABLE_GEMINI and GOOGLE_AI_API_KEY:
        try:
            from .providers.gemini import create_gemini_provider
            gemini_provider = create_gemini_provider(GOOGLE_AI_API_KEY)
            provider_manager.register_provider(gemini_provider, is_primary=True)
        except Exception as e:
            print(f"Warning: Failed to register Gemini provider: {e}")

    # Register Groq (fallback)
    if CHATBOT_ENABLE_GROQ and GROQ_API_KEY:
        try:
            from .providers.groq import create_groq_provider
            groq_provider = create_groq_provider(GROQ_API_KEY)
            provider_manager.register_provider(groq_provider, is_primary=False)
        except Exception as e:
            print(f"Warning: Failed to register Groq provider: {e}")

    # Register Ollama (if enabled)
    if CHATBOT_ENABLE_OLLAMA:
        try:
            from .providers.ollama import OllamaProvider
            ollama_provider = OllamaProvider(OLLAMA_BASE_URL)
            provider_manager.register_provider(ollama_provider, is_primary=False)
        except Exception as e:
            print(f"Warning: Failed to register Ollama provider: {e}")


# Initialize providers on module load
_initialize_providers()