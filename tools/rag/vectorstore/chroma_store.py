"""
ChromaDB Vector Store
=====================
Persistent vector storage using ChromaDB.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings

from ..config import get_config
from ..embeddings import get_embedding_provider, EmbeddingProvider


@dataclass
class SearchResult:
    """A single search result."""
    id: str
    content: str
    metadata: Dict[str, Any]
    distance: float
    score: float  # Similarity score (1 - distance for cosine)


class ChromaVectorStore:
    """
    ChromaDB-based vector store for RAG.
    
    Manages 3 collections:
    - system_knowledge: Platform usage guide
    - toeic_content: Test questions and explanations
    - user_analytics: User mistake patterns
    
    Example:
        ```python
        store = ChromaVectorStore()
        
        # Add documents
        store.add_documents(
            collection="toeic_content",
            documents=["She's holding a piece of paper."],
            metadatas=[{"test_id": "ETS_Test_01", "question_id": "q1"}],
            ids=["ETS_Test_01_q1"]
        )
        
        # Search
        results = store.search(
            collection="toeic_content",
            query="What is she holding?",
            top_k=5
        )
        ```
    """
    
    def __init__(
        self,
        persist_dir: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        """
        Initialize ChromaDB vector store.
        
        Args:
            persist_dir: Directory for persistent storage (default from config)
            embedding_provider: Custom embedding provider (default from config)
        """
        config = get_config()
        
        self.persist_dir = persist_dir or config.vectordb.persist_dir
        self.embedding_provider = embedding_provider or get_embedding_provider()
        
        # Ensure persist directory exists
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collection names from config
        self.collection_names = {
            "system": config.vectordb.system_collection,
            "toeic": config.vectordb.toeic_collection,
            "user": config.vectordb.user_collection
        }
        
        # Cache for collections
        self._collections: Dict[str, Any] = {}
    
    def _get_collection(self, name: str):
        """Get or create a collection."""
        if name not in self._collections:
            # Map short names to full names
            full_name = self.collection_names.get(name, name)
            
            self._collections[name] = self.client.get_or_create_collection(
                name=full_name,
                metadata={
                    "hnsw:space": "cosine",
                    "embedding_provider": self.embedding_provider.provider_name,
                    "embedding_dimensions": self.embedding_provider.dimensions
                }
            )
        return self._collections[name]
    
    def add_documents(
        self,
        collection: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to a collection.
        
        Args:
            collection: Collection name ("system", "toeic", "user")
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document (auto-generated if not provided)
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        col = self._get_collection(collection)
        
        # Generate embeddings
        embeddings = self.embedding_provider.embed_documents(documents)
        
        # Generate IDs if not provided
        if ids is None:
            import hashlib
            ids = [
                hashlib.md5(doc.encode()).hexdigest()[:16]
                for doc in documents
            ]
        
        # Ensure metadatas
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        # Add to collection
        col.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return ids
    
    def upsert_documents(
        self,
        collection: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: List[str] = None
    ) -> List[str]:
        """
        Upsert (insert or update) documents.
        
        Args:
            collection: Collection name
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: IDs for each document (required for upsert)
            
        Returns:
            List of document IDs
        """
        if not documents or not ids:
            return []
        
        col = self._get_collection(collection)
        
        # Generate embeddings
        embeddings = self.embedding_provider.embed_documents(documents)
        
        # Ensure metadatas
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        # Upsert to collection
        col.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return ids
    
    def search(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            collection: Collection name
            query: Search query text
            top_k: Number of results to return
            where: Optional metadata filter
            where_document: Optional document content filter
            
        Returns:
            List of SearchResult objects
        """
        col = self._get_collection(collection)
        
        # Generate query embedding
        query_embedding = self.embedding_provider.embed_query(query)
        
        # Search
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                search_results.append(SearchResult(
                    id=doc_id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    distance=distance,
                    score=1 - distance  # Cosine similarity
                ))
        
        return search_results
    
    def search_multiple_collections(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        top_k_per_collection: int = 3
    ) -> Dict[str, List[SearchResult]]:
        """
        Search across multiple collections.
        
        Args:
            query: Search query text
            collections: List of collection names (default: all)
            top_k_per_collection: Results per collection
            
        Returns:
            Dict mapping collection name to results
        """
        if collections is None:
            collections = ["system", "toeic", "user"]
        
        results = {}
        for col_name in collections:
            try:
                results[col_name] = self.search(
                    collection=col_name,
                    query=query,
                    top_k=top_k_per_collection
                )
            except Exception as e:
                print(f"[!] Error searching {col_name}: {e}")
                results[col_name] = []
        
        return results
    
    def delete_documents(
        self,
        collection: str,
        ids: List[str]
    ) -> bool:
        """
        Delete documents by ID.
        
        Args:
            collection: Collection name
            ids: List of document IDs to delete
            
        Returns:
            True if successful
        """
        col = self._get_collection(collection)
        col.delete(ids=ids)
        return True
    
    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Dict with collection statistics
        """
        col = self._get_collection(collection)
        return {
            "name": col.name,
            "count": col.count(),
            "metadata": col.metadata
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collections."""
        stats = {}
        for short_name in ["system", "toeic", "user"]:
            try:
                stats[short_name] = self.get_collection_stats(short_name)
            except Exception as e:
                stats[short_name] = {"error": str(e)}
        return stats
    
    def reset_collection(self, collection: str) -> bool:
        """
        Reset (delete all documents from) a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            True if successful
        """
        full_name = self.collection_names.get(collection, collection)
        try:
            self.client.delete_collection(full_name)
            # Clear cache
            if collection in self._collections:
                del self._collections[collection]
            return True
        except Exception:
            return False
    
    def __repr__(self) -> str:
        return f"ChromaVectorStore(persist_dir={self.persist_dir})"
