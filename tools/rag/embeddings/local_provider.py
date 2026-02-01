"""
Local Embedding Provider (Sentence Transformers)
=================================================
Uses HuggingFace sentence-transformers for local embedding.
No API costs, but requires ~500MB RAM.
"""

from typing import List
from .base import EmbeddingProvider, EmbeddingResult


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding provider using sentence-transformers.
    
    Recommended models:
    - sentence-transformers/paraphrase-multilingual-mpnet-base-v2 (768 dims, multilingual)
    - sentence-transformers/all-MiniLM-L6-v2 (384 dims, English, fast)
    - BAAI/bge-m3 (1024 dims, multilingual, high quality)
    
    Pros:
    - Free, no API costs
    - Works offline
    - Fast for batch processing
    
    Cons:
    - Requires ~500MB RAM per model
    - First load takes ~10 seconds
    """
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"):
        """
        Initialize local embedding provider.
        
        Args:
            model_name: HuggingFace model name
        """
        self.model_name = model_name
        self._model = None
        self._dimensions = None
    
    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
            
            print(f"[*] Loading local embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self._dimensions = self._model.get_sentence_embedding_dimension()
            print(f"[+] Model loaded. Dimensions: {self._dimensions}")
    
    @property
    def provider_name(self) -> str:
        return "local"
    
    @property
    def dimensions(self) -> int:
        if self._dimensions is None:
            self._load_model()
        return self._dimensions
    
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """
        Embed multiple texts using local model.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            EmbeddingResult with embeddings
        """
        self._load_model()
        
        if not texts:
            return EmbeddingResult(embeddings=[], model=self.model_name, dimensions=self._dimensions)
        
        # Clean texts
        cleaned_texts = [t.strip() if t.strip() else " " for t in texts]
        
        # Embed
        embeddings = self._model.encode(cleaned_texts, show_progress_bar=False)
        
        # Convert numpy to list
        embeddings_list = [emb.tolist() for emb in embeddings]
        
        return EmbeddingResult(
            embeddings=embeddings_list,
            model=self.model_name,
            dimensions=self._dimensions
        )
    
    def __repr__(self) -> str:
        return f"LocalEmbeddingProvider(model={self.model_name})"
