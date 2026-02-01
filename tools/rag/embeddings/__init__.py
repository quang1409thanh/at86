"""
Embedding Providers
===================
Extensible embedding interface with multiple provider implementations.
"""

from .base import EmbeddingProvider, EmbeddingResult
from .factory import get_embedding_provider

__all__ = ["EmbeddingProvider", "EmbeddingResult", "get_embedding_provider"]
