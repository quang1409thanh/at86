"""
Embedding Provider Factory
==========================
Factory function to create embedding providers based on configuration.
"""

from typing import Optional
from ..config import get_config, EmbeddingConfig
from .base import EmbeddingProvider


def get_embedding_provider(config: Optional[EmbeddingConfig] = None) -> EmbeddingProvider:
    """
    Create an embedding provider based on configuration.
    
    Args:
        config: Optional EmbeddingConfig. If None, uses global config from .env
        
    Returns:
        EmbeddingProvider instance
        
    Raises:
        ValueError: If provider is not supported
        
    Example:
        ```python
        # Use default config from .env
        provider = get_embedding_provider()
        embedding = provider.embed_query("Hello world")
        
        # Use custom config
        from tools.rag.config import EmbeddingConfig
        config = EmbeddingConfig(provider="openai", openai_api_key="sk-...")
        provider = get_embedding_provider(config)
        ```
    """
    if config is None:
        config = get_config().embedding
    
    provider_name = config.provider.lower()
    
    if provider_name == "openai":
        from .openai_provider import OpenAIEmbeddingProvider
        
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set. Check your .env file.")
        
        return OpenAIEmbeddingProvider(
            api_key=config.openai_api_key,
            model=config.openai_model,
            base_url=config.openai_base_url,
            dimensions=config.openai_dimensions
        )
    
    elif provider_name == "google":
        from .google_provider import GoogleEmbeddingProvider
        
        if not config.google_api_key:
            raise ValueError("GEMINI_API_KEY not set. Check your .env file.")
        
        return GoogleEmbeddingProvider(
            api_key=config.google_api_key,
            model=config.google_model
        )
    
    elif provider_name == "local":
        from .local_provider import LocalEmbeddingProvider
        
        return LocalEmbeddingProvider(
            model_name=config.local_model
        )
    
    else:
        raise ValueError(
            f"Unknown embedding provider: '{provider_name}'. "
            f"Supported providers: 'openai', 'google', 'local'. "
            f"Set RAG_EMBEDDING_PROVIDER in .env file."
        )


# Singleton instance (lazy loaded)
_provider_instance: Optional[EmbeddingProvider] = None


def get_default_provider() -> EmbeddingProvider:
    """
    Get the default embedding provider (singleton).
    
    Use this for convenience when you don't need custom config.
    
    Returns:
        EmbeddingProvider instance
    """
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = get_embedding_provider()
    return _provider_instance


def reset_provider():
    """Reset the singleton provider (useful after config change)."""
    global _provider_instance
    _provider_instance = None
