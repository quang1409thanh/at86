"""
RAG Chain
=========
Complete RAG pipeline: Retrieve → Generate → Response.
"""

import sys
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Add pipeline to path for LLM access
tools_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(tools_dir, "pipeline"))

from ..retriever import HybridRetriever
from ..retriever.hybrid_retriever import RetrievalContext
from .prompts import SYSTEM_PROMPT, build_chat_prompt, build_explanation_prompt, build_analysis_prompt


@dataclass
class RAGResponse:
    """Response from RAG chain."""
    answer: str
    context: RetrievalContext
    sources: list
    metadata: Dict[str, Any]


class RAGChain:
    """
    Complete RAG pipeline.
    
    1. Retrieve relevant context from vector stores
    2. Build prompt with context
    3. Generate response with LLM
    4. Return with sources
    
    Example:
        ```python
        chain = RAGChain()
        response = chain.chat("Làm sao để làm Part 2 tốt hơn?")
        print(response.answer)
        ```
    """
    
    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        llm_provider: str = None
    ):
        """
        Initialize RAG chain.
        
        Args:
            retriever: Optional HybridRetriever instance
            llm_provider: LLM provider to use (default from config)
        """
        self.retriever = retriever or HybridRetriever()
        self.llm_provider = llm_provider
        
        # Import LLM module
        try:
            from common.llm import call_llm
            self._call_llm = call_llm
        except ImportError:
            # Fallback: try direct import
            try:
                from tools.pipeline.common.llm import call_llm
                self._call_llm = call_llm
            except ImportError:
                print("[!] Warning: LLM module not found. Using mock LLM.")
                self._call_llm = self._mock_llm
    
    def _mock_llm(self, prompt: str, **kwargs) -> str:
        """Mock LLM for testing."""
        return f"[Mock LLM Response]\n\nQuery received. Context loaded. This is a mock response for testing.\n\nTo enable real LLM, ensure tools/pipeline/common/llm.py is available."
    
    def chat(
        self,
        query: str,
        user_id: str = "default",
        collections: list = None
    ) -> RAGResponse:
        """
        Chat with RAG.
        
        Args:
            query: User's question
            user_id: User ID for personalization
            collections: Which collections to search
            
        Returns:
            RAGResponse with answer and sources
        """
        # 1. Retrieve context
        context = self.retriever.retrieve(
            query=query,
            collections=collections,
            user_id=user_id
        )
        
        # 2. Build prompt
        context_text = context.to_prompt_context()
        prompt = build_chat_prompt(query, context_text)
        
        # Add system prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{prompt}"
        
        # DEBUG LOGS
        print(f"\n{'='*20} RAG CHAT DEBUG {'='*20}")
        print(f"[*] Query: {query}")
        print(f"[*] Context retrieved: {len(context.system_context)} sys, {len(context.toeic_context)} toeic, {len(context.user_context)} user")
        print(f"\n--- FULL PROMPT SENT TO LLM ---\n{full_prompt}")
        print(f"{'='*60}\n")
        
        # 3. Generate
        try:
            answer = self._call_llm(full_prompt, json_mode=False)
        except Exception as e:
            print(f"[!] LLM Call failed: {e}")
            answer = f"[Lỗi khi gọi LLM: {e}]\n\nDựa trên thông tin tìm được:\n{context_text[:500]}..."
        
        # 4. Extract sources
        sources = []
        for r in context.get_top_k(5):
            sources.append({
                "id": r.id,
                "content_preview": r.content[:100] + "..." if len(r.content) > 100 else r.content,
                "score": round(r.score, 3),
                "metadata": r.metadata
            })
        
        return RAGResponse(
            answer=answer,
            context=context,
            sources=sources,
            metadata={
                "query": query,
                "user_id": user_id,
                "num_system_results": len(context.system_context),
                "num_toeic_results": len(context.toeic_context),
                "num_user_results": len(context.user_context)
            }
        )
    
    def explain_question(
        self,
        test_id: str,
        question_id: str,
        user_answer: str,
        correct_answer: str,
        part_number: int,
        user_id: str = "default"
    ) -> RAGResponse:
        """
        Generate explanation for a specific question.
        
        Args:
            test_id: Test ID
            question_id: Question ID  
            user_answer: User's answer
            correct_answer: Correct answer
            part_number: Part number
            user_id: User ID
            
        Returns:
            RAGResponse with explanation
        """
        import json
        
        # 1. Retrieve context for this question
        context = self.retriever.retrieve_for_question(
            test_id=test_id,
            question_id=question_id,
            user_id=user_id
        )
        
        # 2. Extract question content and error info
        question_content = ""
        error_analysis = ""
        correct_transcript = None
        user_transcript = None
        
        # Try to find specific question content from toeic collection
        for r in context.toeic_context:
            if question_id in r.id:
                question_content = r.content
                # In older indexing, transcripts were in metadata as dicts
                correct_transcript = r.metadata.get("transcripts")
                break
        
        # Try to find user error info
        for r in context.user_context:
            if question_id in r.metadata.get("question_id", ""):
                error_analysis = r.content
                # New indexing stores transcripts as JSON strings in metadata
                meta_correct = r.metadata.get("correct_transcript")
                meta_user = r.metadata.get("user_transcript")
                
                if meta_correct and not correct_transcript:
                    try:
                        correct_transcript = json.loads(meta_correct)
                    except:
                        correct_transcript = meta_correct
                
                if meta_user:
                    try:
                        user_transcript = json.loads(meta_user)
                    except:
                        user_transcript = meta_user
                break
        
        # 3. Build prompt (Specialized by Part)
        prompt = build_explanation_prompt(
            part_number=part_number,
            test_id=test_id,
            question_content=question_content or f"Câu hỏi {question_id} từ đề {test_id}",
            user_answer=user_answer,
            correct_answer=correct_answer,
            user_transcript=str(user_transcript) if user_transcript else None,
            correct_transcript=str(correct_transcript) if correct_transcript else None,
            error_analysis=error_analysis or None
        )
        
        full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{prompt}"
        
        # DEBUG LOGS
        print(f"\n{'='*20} RAG EXPLAIN DEBUG {'='*20}")
        print(f"[*] Test: {test_id} | Part: {part_number} | Question: {question_id}")
        print(f"[*] Context found: {bool(question_content)} (toeic), {bool(error_analysis)} (user)")
        if correct_transcript:
            print(f"[*] Transcripts available: Yes")
        
        print(f"\n--- FULL PROMPT SENT TO LLM ---\n{full_prompt}")
        print(f"{'='*60}\n")
        
        # 4. Generate
        try:
            answer = self._call_llm(full_prompt, json_mode=False)
        except Exception as e:
            print(f"[!] LLM Call failed: {e}")
            answer = f"[Lỗi: {e}]"
        
        return RAGResponse(
            answer=answer,
            context=context,
            sources=[],
            metadata={
                "test_id": test_id,
                "question_id": question_id,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "part_number": part_number,
                "has_context": bool(question_content or error_analysis)
            }
        )
    
    def analyze_performance(self, user_id: str = "default") -> RAGResponse:
        """
        Analyze user's overall performance and generate learning plan.
        
        Args:
            user_id: User ID
            
        Returns:
            RAGResponse with analysis
        """
        from ..knowledge.user_analyzer import UserMistakeAnalyzer
        
        # 1. Get error summary
        analyzer = UserMistakeAnalyzer()
        error_summary = analyzer.get_user_error_summary(user_id)
        
        # 2. Build prompt
        prompt = build_analysis_prompt(error_summary)
        full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{prompt}"
        
        # 3. Generate
        try:
            answer = self._call_llm(full_prompt, json_mode=False)
        except Exception as e:
            answer = f"[Lỗi: {e}]"
        
        # 4. Create empty context
        context = RetrievalContext(
            query="analyze performance",
            system_context=[],
            toeic_context=[],
            user_context=[]
        )
        
        return RAGResponse(
            answer=answer,
            context=context,
            sources=[],
            metadata={
                "user_id": user_id,
                "error_summary": error_summary
            }
        )
