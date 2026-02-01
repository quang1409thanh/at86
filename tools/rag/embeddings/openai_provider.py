"""
OpenAI Embedding Provider
=========================
Uses OpenAI's text-embedding models (text-embedding-3-small, text-embedding-3-large, etc.)
"""

import requests
from typing import List, Optional
from .base import EmbeddingProvider, EmbeddingResult


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI embedding provider using the embeddings API.
    
    Supports:
    - text-embedding-3-small (1536 dims, recommended)
    - text-embedding-3-large (3072 dims)
    - text-embedding-ada-002 (legacy, 1536 dims)
    
    Features:
    - Configurable dimensions for text-embedding-3-* models
    - Batch embedding support
    - Compatible with OpenAI-compatible APIs (e.g., Azure, local proxies)
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
        dimensions: Optional[int] = None
    ):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (text-embedding-3-small recommended)
            base_url: API base URL (for custom endpoints)
            dimensions: Output dimensions (only for text-embedding-3-* models)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        
        # Default dimensions based on model
        if dimensions:
            self._dimensions = dimensions
        elif "3-small" in model:
            self._dimensions = 1536
        elif "3-large" in model:
            self._dimensions = 3072
        else:
            self._dimensions = 1536  # ada-002 and others
        
        self._supports_dimensions = "text-embedding-3" in model
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def dimensions(self) -> int:
        return self._dimensions
    
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """
        Embed multiple texts using OpenAI API.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            EmbeddingResult with embeddings
        """
        if not texts:
            return EmbeddingResult(embeddings=[], model=self.model, dimensions=self._dimensions)
        
        # Clean texts (OpenAI doesn't like empty strings)
        cleaned_texts = [t.strip() if t.strip() else " " for t in texts]
        
        # Prepare request
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": cleaned_texts,
            "model": self.model
        }
        
        # Add dimensions if supported
        if self._supports_dimensions and self._dimensions:
            payload["dimensions"] = self._dimensions
        
        # Make request
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            error_msg = response.text
            raise Exception(f"OpenAI Embedding API error ({response.status_code}): {error_msg}")
        
        data = response.json()
        
        # Extract embeddings (sorted by index to ensure order)
        embedding_data = sorted(data["data"], key=lambda x: x["index"])
        embeddings = [item["embedding"] for item in embedding_data]
        
        # Token usage
        token_usage = data.get("usage", {}).get("total_tokens")
        
        return EmbeddingResult(
            embeddings=embeddings,
            model=self.model,
            dimensions=len(embeddings[0]) if embeddings else self._dimensions,
            token_usage=token_usage
        )
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a single query."""
        result = self.embed_texts([query])
        return result[0] if result.embeddings else []
    
    def __repr__(self) -> str:
        return f"OpenAIEmbeddingProvider(model={self.model}, dimensions={self._dimensions})"
