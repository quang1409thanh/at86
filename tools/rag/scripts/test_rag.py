#!/usr/bin/env python
"""
Test RAG Chat
=============
Test the RAG system with sample queries.

Usage:
    python test_rag.py
    python test_rag.py --query "Làm sao để cải thiện Part 2?"
    python test_rag.py --explain ETS_Test_01 q71 B C
"""

import argparse
import sys
import os

# Add tools directory to path
tools_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, tools_dir)

# Change to project root
project_root = os.path.dirname(tools_dir)
os.chdir(project_root)


def test_search():
    """Test vector search."""
    from rag.vectorstore import ChromaVectorStore
    
    print("=" * 60)
    print("🔍 TESTING VECTOR SEARCH")
    print("=" * 60)
    
    store = ChromaVectorStore()
    
    # Test queries
    queries = [
        "Làm sao để làm bài thi TOEIC?",
        "She's holding a piece of paper",
        "Part 2 question response listening"
    ]
    
    for query in queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 40)
        
        results = store.search_multiple_collections(
            query=query,
            top_k_per_collection=2
        )
        
        for col_name, col_results in results.items():
            if col_results:
                print(f"\n  📁 {col_name}:")
                for r in col_results:
                    preview = r.content[:80].replace('\n', ' ') + "..."
                    print(f"    - [{r.score:.3f}] {preview}")


def test_retriever():
    """Test hybrid retriever."""
    from rag.retriever import HybridRetriever
    
    print("\n" + "=" * 60)
    print("🔄 TESTING HYBRID RETRIEVER")
    print("=" * 60)
    
    retriever = HybridRetriever()
    
    query = "Tôi hay sai Part 2, làm sao để cải thiện?"
    print(f"\n📝 Query: '{query}'")
    
    context = retriever.retrieve(query)
    
    print(f"\n📊 Results:")
    print(f"  - System: {len(context.system_context)} docs")
    print(f"  - TOEIC: {len(context.toeic_context)} docs")
    print(f"  - User: {len(context.user_context)} docs")
    
    print("\n📄 Formatted context for LLM:")
    print("-" * 40)
    formatted = context.to_prompt_context()
    print(formatted[:1000] + "..." if len(formatted) > 1000 else formatted)


def test_chat(query: str = None):
    """Test RAG chat."""
    from rag.generator import RAGChain
    
    print("\n" + "=" * 60)
    print("💬 TESTING RAG CHAT")
    print("=" * 60)
    
    chain = RAGChain()
    
    if query is None:
        query = "Tôi hay sai Part 2, đặc biệt là câu hỏi về thời gian. Làm sao để cải thiện?"
    
    print(f"\n📝 Query: '{query}'")
    print("-" * 40)
    
    response = chain.chat(query)
    
    print("\n✨ Answer:")
    print(response.answer)
    
    print("\n📚 Sources:")
    for source in response.sources[:3]:
        print(f"  - [{source['score']:.3f}] {source['id']}: {source['content_preview']}")


def test_explain(test_id: str, question_id: str, user_answer: str, correct_answer: str):
    """Test question explanation."""
    from rag.generator import RAGChain
    
    print("\n" + "=" * 60)
    print("📖 TESTING QUESTION EXPLANATION")
    print("=" * 60)
    
    chain = RAGChain()
    
    print(f"\n📝 Test: {test_id}, Question: {question_id}")
    print(f"   User: {user_answer}, Correct: {correct_answer}")
    print("-" * 40)
    
    response = chain.explain_question(
        test_id=test_id,
        question_id=question_id,
        user_answer=user_answer,
        correct_answer=correct_answer
    )
    
    print("\n✨ Explanation:")
    print(response.answer)


def test_analyze():
    """Test performance analysis."""
    from rag.generator import RAGChain
    
    print("\n" + "=" * 60)
    print("📊 TESTING PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    chain = RAGChain()
    
    response = chain.analyze_performance()
    
    print("\n✨ Analysis:")
    print(response.answer)
    
    print("\n📈 Error Summary:")
    summary = response.metadata.get("error_summary", {})
    print(f"  Total mistakes: {summary.get('total_mistakes', 0)}")
    for error_type, data in summary.get('error_types', {}).items():
        print(f"  - {error_type}: {data.get('count', 0)}")


def main():
    parser = argparse.ArgumentParser(description="Test RAG system")
    parser.add_argument("--query", "-q", type=str, help="Custom query to test")
    parser.add_argument("--explain", "-e", nargs=4, 
                       metavar=("TEST_ID", "QUESTION_ID", "USER_ANS", "CORRECT_ANS"),
                       help="Test question explanation")
    parser.add_argument("--analyze", "-a", action="store_true", help="Test performance analysis")
    parser.add_argument("--search", "-s", action="store_true", help="Test vector search only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()
    
    if args.search:
        test_search()
    elif args.explain:
        test_explain(*args.explain)
    elif args.analyze:
        test_analyze()
    elif args.query:
        test_chat(args.query)
    elif args.all:
        test_search()
        test_retriever()
        test_chat()
        test_analyze()
    else:
        # Default: run search and retriever tests (no LLM call)
        test_search()
        test_retriever()
    
    print("\n✅ Tests complete!")


if __name__ == "__main__":
    main()
