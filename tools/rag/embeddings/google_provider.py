"""
Google Embedding Provider
=========================
Uses Google's text-embedding models via Generative AI API.
"""

import requests
from typing import List
from .base import EmbeddingProvider, EmbeddingResult


class GoogleEmbeddingProvider(EmbeddingProvider):
    """
    Google embedding provider using the Generative AI API.
    
    Supports:
    - text-embedding-004 (768 dims, recommended)
    - embedding-001 (legacy)
    
    Uses the same GEMINI_API_KEY as the LLM.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-004"
    ):
        """
        Initialize Google embedding provider.
        
        Args:
            api_key: Google API key (same as GEMINI_API_KEY)
            model: Model name (text-embedding-004 recommended)
        """
        self.api_key = api_key
        self.model = model
        
        # Dimensions based on model
        if "004" in model:
            self._dimensions = 768
        else:
            self._dimensions = 768  # Default
    
    @property
    def provider_name(self) -> str:
        return "google"
    
    @property
    def dimensions(self) -> int:
        return self._dimensions
    
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """
        Embed multiple texts using Google API.
        
        Note: Google API embeds one text at a time, so we loop.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            EmbeddingResult with embeddings
        """
        if not texts:
            return EmbeddingResult(embeddings=[], model=self.model, dimensions=self._dimensions)
        
        embeddings = []
        
        for text in texts:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": f"models/{self.model}",
                "content": {
                    "parts": [{"text": text.strip() or " "}]
                }
            }
            
            response = requests.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = response.text
                raise Exception(f"Google Embedding API error ({response.status_code}): {error_msg}")
            
            data = response.json()
            embedding = data.get("embedding", {}).get("values", [])
            embeddings.append(embedding)
        
        return EmbeddingResult(
            embeddings=embeddings,
            model=self.model,
            dimensions=len(embeddings[0]) if embeddings else self._dimensions
        )
    
    def __repr__(self) -> str:
        return f"GoogleEmbeddingProvider(model={self.model}, dimensions={self._dimensions})"
