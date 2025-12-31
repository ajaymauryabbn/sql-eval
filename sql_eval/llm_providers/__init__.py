"""
LLM Providers for sql-eval
"""

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider, AzureOpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider, SQLCoderProvider


def get_provider(
    provider_name: str,
    model: str = None,
    **kwargs
) -> BaseLLMProvider:
    """
    Factory function to get LLM provider by name
    
    Args:
        provider_name: One of 'openai', 'anthropic', 'ollama', 'sqlcoder', 'azure'
        model: Optional model name override
        **kwargs: Additional provider-specific arguments
        
    Returns:
        Configured LLM provider instance
    """
    providers = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'claude': AnthropicProvider,  # Alias
        'ollama': OllamaProvider,
        'sqlcoder': SQLCoderProvider,
        'azure': AzureOpenAIProvider,
        'azure_openai': AzureOpenAIProvider,
    }
    
    provider_name = provider_name.lower()
    
    if provider_name not in providers:
        available = ', '.join(providers.keys())
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {available}"
        )
    
    provider_class = providers[provider_name]
    
    if model:
        return provider_class(model=model, **kwargs)
    return provider_class(**kwargs)


__all__ = [
    "BaseLLMProvider",
    "OpenAIProvider",
    "AzureOpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "SQLCoderProvider",
    "get_provider"
]
