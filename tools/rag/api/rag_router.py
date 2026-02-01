"""
RAG API Router
==============
FastAPI endpoints for RAG system.
"""

import sys
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add tools to path
tools_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, tools_dir)

from rag.generator import RAGChain
from rag.vectorstore import ChromaVectorStore
from rag.knowledge import index_test, analyze_user_result


# === Request/Response Models ===

class ChatRequest(BaseModel):
    query: str
    user_id: str = "default"
    collections: Optional[List[str]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    metadata: dict


class ExplainRequest(BaseModel):
    test_id: str
    question_id: str
    user_answer: str
    correct_answer: str
    part_number: int
    user_id: str = "default"


class SearchRequest(BaseModel):
    query: str
    collection: str = "toeic"
    top_k: int = 5


class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: dict


# === Router ===

router = APIRouter(prefix="/rag", tags=["rag"])

# Singleton instances
_chain: Optional[RAGChain] = None
_store: Optional[ChromaVectorStore] = None


def get_chain() -> RAGChain:
    global _chain
    if _chain is None:
        _chain = RAGChain()
    return _chain


def get_store() -> ChromaVectorStore:
    global _store
    if _store is None:
        _store = ChromaVectorStore()
    return _store


# === Endpoints ===

@router.post("/chat", response_model=ChatResponse)
async def rag_chat(request: ChatRequest):
    """
    Main RAG chat endpoint.
    
    Query across all knowledge bases and get AI-generated response.
    """
    try:
        chain = get_chain()
        response = chain.chat(
            query=request.query,
            user_id=request.user_id,
            collections=request.collections
        )
        
        return ChatResponse(
            answer=response.answer,
            sources=response.sources,
            metadata=response.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain", response_model=ChatResponse)
async def explain_question(request: ExplainRequest):
    """
    Get AI explanation for a specific question.
    
    Useful for showing on Result Page.
    """
    try:
        chain = get_chain()
        response = chain.explain_question(
            test_id=request.test_id,
            question_id=request.question_id,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer,
            part_number=request.part_number,
            user_id=request.user_id
        )
        
        return ChatResponse(
            answer=response.answer,
            sources=response.sources,
            metadata=response.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{user_id}", response_model=ChatResponse)
async def analyze_performance(user_id: str = "default"):
    """
    Analyze user's overall performance and generate learning plan.
    """
    try:
        chain = get_chain()
        response = chain.analyze_performance(user_id=user_id)
        
        return ChatResponse(
            answer=response.answer,
            sources=response.sources,
            metadata=response.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    """
    Search vector store directly.
    
    Returns raw search results without LLM generation.
    """
    try:
        store = get_store()
        results = store.search(
            collection=request.collection,
            query=request.query,
            top_k=request.top_k
        )
        
        return [
            SearchResult(
                id=r.id,
                content=r.content[:500] + "..." if len(r.content) > 500 else r.content,
                score=round(r.score, 3),
                metadata=r.metadata
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """
    Get vector store statistics.
    """
    try:
        store = get_store()
        return store.get_all_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/test/{test_id}")
async def index_test_endpoint(test_id: str):
    """
    Index a specific test into vector store.
    """
    try:
        count = index_test(test_id, get_store())
        return {"status": "success", "documents_indexed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/result/{result_id}")
async def index_result_endpoint(result_id: str):
    """
    Analyze and index a user result.
    Also sets rag_indexed flag in the result JSON file.
    """
    import json
    from datetime import datetime
    
    try:
        count = analyze_user_result(result_id, get_store())
        
        # Update the result JSON file with rag_indexed flag
        result_path = os.path.join("data/users/default", f"{result_id}.json")
        if os.path.exists(result_path):
            with open(result_path, "r", encoding="utf-8") as f:
                result_data = json.load(f)
            
            result_data["rag_indexed"] = True
            result_data["rag_indexed_at"] = datetime.now().isoformat()
            result_data["mistakes_count"] = count
            
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=4, ensure_ascii=False)
            
            print(f"[+] Updated {result_path} with rag_indexed=True")
        
        return {"status": "success", "mistakes_indexed": count, "rag_indexed": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexed/{result_id}")
async def check_indexed(result_id: str):
    """
    Check if a result has been indexed to RAG.
    """
    import json
    
    result_path = os.path.join("data/users/default", f"{result_id}.json")
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result not found")
    
    with open(result_path, "r", encoding="utf-8") as f:
        result_data = json.load(f)
    
    return {
        "result_id": result_id,
        "rag_indexed": result_data.get("rag_indexed", False),
        "rag_indexed_at": result_data.get("rag_indexed_at"),
        "mistakes_count": result_data.get("mistakes_count", 0)
    }


@router.delete("/reset/{collection}")
async def reset_collection(collection: str):
    """
    Reset a specific vector collection.
    collection: 'system', 'toeic', or 'user'
    """
    try:
        store = get_store()
        success = store.reset_collection(collection)
        if success:
            return {"status": "success", "message": f"Collection '{collection}' reset successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to reset collection '{collection}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

