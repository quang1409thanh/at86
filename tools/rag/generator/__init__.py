"""
Generator Package
==================
LLM generation with RAG context.
"""

from .prompts import SYSTEM_PROMPT, build_chat_prompt, build_explanation_prompt
from .rag_chain import RAGChain

__all__ = [
    "SYSTEM_PROMPT",
    "build_chat_prompt",
    "build_explanation_prompt",
    "RAGChain"
]
