"""
RAG System Configuration
========================
Loads configuration from environment variables with sensible defaults.
"""

import os
from typing import Literal
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()


@dataclass
class EmbeddingConfig:
    """Configuration for embedding providers."""
    provider: Literal["openai", "google", "local"] = "openai"
    
    # OpenAI
    openai_model: str = "text-embedding-3-small"
    openai_dimensions: int = 1536
    openai_api_key: str = ""
    openai_base_url: str = ""
    
    # Google
    google_model: str = "text-embedding-004"
    google_api_key: str = ""
    
    # Local (sentence-transformers)
    local_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


@dataclass
class VectorDBConfig:
    """Configuration for vector database."""
    db_type: Literal["chromadb", "qdrant", "pinecone"] = "chromadb"
    persist_dir: str = "data/rag/chroma_db"
    
    # Collection names
    system_collection: str = "system_knowledge"
    toeic_collection: str = "toeic_content"
    user_collection: str = "user_analytics"


@dataclass
class RetrievalConfig:
    """Configuration for retrieval settings."""
    top_k: int = 5
    similarity_threshold: float = 0.7
    rerank_enabled: bool = False


@dataclass
class RAGConfig:
    """Main RAG configuration container."""
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vectordb: VectorDBConfig = field(default_factory=VectorDBConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    
    # LLM settings (reuse from pipeline)
    llm_provider: str = "google"
    
    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Load configuration from environment variables."""
        config = cls()
        
        # Embedding config
        config.embedding.provider = os.getenv("RAG_EMBEDDING_PROVIDER", "openai")
        config.embedding.openai_model = os.getenv("RAG_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        config.embedding.openai_dimensions = int(os.getenv("RAG_OPENAI_EMBEDDING_DIMENSIONS", "1536"))
        config.embedding.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        config.embedding.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        config.embedding.google_model = os.getenv("RAG_GOOGLE_EMBEDDING_MODEL", "text-embedding-004")
        config.embedding.google_api_key = os.getenv("GEMINI_API_KEY", "")
        config.embedding.local_model = os.getenv("RAG_LOCAL_EMBEDDING_MODEL", 
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
        
        # VectorDB config
        config.vectordb.db_type = os.getenv("RAG_VECTOR_DB", "chromadb")
        config.vectordb.persist_dir = os.getenv("RAG_CHROMA_PERSIST_DIR", "data/rag/chroma_db")
        
        # Retrieval config
        config.retrieval.top_k = int(os.getenv("RAG_TOP_K", "5"))
        config.retrieval.similarity_threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
        
        # LLM provider
        config.llm_provider = os.getenv("LLM_PROVIDER", "google")
        
        return config


# Global config instance
rag_config = RAGConfig.from_env()


def get_config() -> RAGConfig:
    """Get the global RAG configuration."""
    return rag_config


def reload_config() -> RAGConfig:
    """Reload configuration from environment."""
    global rag_config
    load_dotenv(override=True)
    rag_config = RAGConfig.from_env()
    return rag_config
