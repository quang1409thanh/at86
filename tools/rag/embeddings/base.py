"""
Base Embedding Provider
=======================
Abstract interface for embedding providers.
Implement this to add new embedding providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmbeddingResult:
    """Result from an embedding operation."""
    embeddings: List[List[float]]
    model: str
    dimensions: int
    token_usage: Optional[int] = None
    
    def __len__(self) -> int:
        return len(self.embeddings)
    
    def __getitem__(self, idx: int) -> List[float]:
        return self.embeddings[idx]


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    
    To add a new provider:
    1. Create a new file (e.g., my_provider.py)
    2. Implement this interface
    3. Register in factory.py
    
    Example:
    ```python
    class MyProvider(EmbeddingProvider):
        def __init__(self, api_key: str, model: str):
            self.api_key = api_key
            self.model = model
        
        @property
        def provider_name(self) -> str:
            return "my_provider"
        
        @property
        def dimensions(self) -> int:
            return 768
        
        def embed_texts(self, texts: List[str]) -> EmbeddingResult:
            # Your implementation here
            pass
        
        def embed_query(self, query: str) -> List[float]:
            return self.embed_texts([query])[0]
    ```
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider (e.g., 'openai', 'google', 'local')."""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions for this provider/model."""
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """
        Embed multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            EmbeddingResult with embeddings for each text
        """
        pass
    
    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        result = self.embed_texts([query])
        return result[0]
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.
        
        Args:
            documents: List of documents to embed
            
        Returns:
            List of embedding vectors
        """
        result = self.embed_texts(documents)
        return result.embeddings
