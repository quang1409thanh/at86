"""
Hybrid Retriever
================
Retrieves from multiple collections and merges results.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..vectorstore import ChromaVectorStore
from ..vectorstore.chroma_store import SearchResult


@dataclass
class RetrievalContext:
    """Context retrieved for a query."""
    query: str
    system_context: List[SearchResult]
    toeic_context: List[SearchResult]
    user_context: List[SearchResult]
    
    def get_all_results(self) -> List[SearchResult]:
        """Get all results merged and sorted by score."""
        all_results = (
            self.system_context + 
            self.toeic_context + 
            self.user_context
        )
        return sorted(all_results, key=lambda x: x.score, reverse=True)
    
    def get_top_k(self, k: int = 5) -> List[SearchResult]:
        """Get top K results across all collections."""
        return self.get_all_results()[:k]
    
    def to_prompt_context(self, max_items: int = 10) -> str:
        """Format context for LLM prompt."""
        sections = []
        
        # System context
        if self.system_context:
            system_texts = [
                f"- {r.content[:500]}..." if len(r.content) > 500 else f"- {r.content}"
                for r in self.system_context[:3]
            ]
            if system_texts:
                sections.append("📚 **Hướng dẫn sử dụng hệ thống:**\n" + "\n".join(system_texts))
        
        # TOEIC context
        if self.toeic_context:
            toeic_texts = []
            for r in self.toeic_context[:5]:
                meta = r.metadata
                header = f"[{meta.get('test_id', 'Unknown')} - {meta.get('question_id', 'Unknown')} - Part {meta.get('part_number', '?')}]"
                content = r.content[:400] + "..." if len(r.content) > 400 else r.content
                toeic_texts.append(f"{header}\n{content}")
            if toeic_texts:
                sections.append("📝 **Kiến thức TOEIC liên quan:**\n" + "\n\n".join(toeic_texts))
        
        # User context
        if self.user_context:
            user_texts = []
            for r in self.user_context[:5]:
                meta = r.metadata
                header = f"[Lỗi sai: {meta.get('test_id', '')} - {meta.get('question_id', '')}]"
                content = r.content[:300] + "..." if len(r.content) > 300 else r.content
                user_texts.append(f"{header}\n{content}")
            if user_texts:
                sections.append("👤 **Phân tích lỗi sai của bạn:**\n" + "\n\n".join(user_texts))
        
        return "\n\n---\n\n".join(sections) if sections else "Không tìm thấy thông tin liên quan."


class HybridRetriever:
    """
    Retrieves relevant context from multiple knowledge bases.
    
    Features:
    - Searches across system, TOEIC, and user collections
    - Configurable weights for each collection
    - Supports filtering by metadata
    """
    
    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        top_k_per_collection: int = 3
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: Optional ChromaVectorStore instance
            top_k_per_collection: Number of results per collection
        """
        self.vector_store = vector_store or ChromaVectorStore()
        self.top_k_per_collection = top_k_per_collection
    
    def retrieve(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> RetrievalContext:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            collections: Which collections to search (default: all)
            top_k: Override top_k per collection
            user_id: Filter user collection by user_id
            
        Returns:
            RetrievalContext with results from each collection
        """
        if collections is None:
            collections = ["system", "toeic", "user"]
        
        k = top_k or self.top_k_per_collection
        
        system_results = []
        toeic_results = []
        user_results = []
        
        # Search system collection
        if "system" in collections:
            try:
                system_results = self.vector_store.search(
                    collection="system",
                    query=query,
                    top_k=k
                )
            except Exception as e:
                print(f"[!] Error searching system collection: {e}")
        
        # Search TOEIC collection
        if "toeic" in collections:
            try:
                toeic_results = self.vector_store.search(
                    collection="toeic",
                    query=query,
                    top_k=k
                )
            except Exception as e:
                print(f"[!] Error searching toeic collection: {e}")
        
        # Search user collection
        if "user" in collections:
            try:
                where_filter = None
                if user_id:
                    where_filter = {"user_id": user_id}
                
                user_results = self.vector_store.search(
                    collection="user",
                    query=query,
                    top_k=k,
                    where=where_filter
                )
            except Exception as e:
                print(f"[!] Error searching user collection: {e}")
        
        return RetrievalContext(
            query=query,
            system_context=system_results,
            toeic_context=toeic_results,
            user_context=user_results
        )
    
    def retrieve_for_question(
        self,
        test_id: str,
        question_id: str,
        user_id: str = "default"
    ) -> RetrievalContext:
        """
        Retrieve context for a specific question.
        
        Useful for generating explanations for a particular question.
        
        Args:
            test_id: Test ID
            question_id: Question ID
            user_id: User ID for personalization
            
        Returns:
            RetrievalContext with relevant info
        """
        # Build query from question identifiers
        query = f"TOEIC question {question_id} from test {test_id}"
        
        # Get TOEIC content for this specific question
        toeic_results = []
        try:
            toeic_results = self.vector_store.search(
                collection="toeic",
                query=query,
                top_k=5,
                where={"test_id": test_id}
            )
        except Exception as e:
            print(f"[!] Error: {e}")
        
        # Get user mistakes for this question
        user_results = []
        try:
            user_results = self.vector_store.search(
                collection="user",
                query=f"mistake {question_id}",
                top_k=3,
                where={"question_id": question_id}
            )
        except Exception as e:
            print(f"[!] Error: {e}")
        
        return RetrievalContext(
            query=query,
            system_context=[],
            toeic_context=toeic_results,
            user_context=user_results
        )
