#!/usr/bin/env python
"""
Index All Data
==============
Index all knowledge sources into the RAG vector store.

Usage:
    python index_all.py              # Index everything
    python index_all.py --system     # Only system docs
    python index_all.py --toeic      # Only TOEIC content
    python index_all.py --user       # Only user analytics
    python index_all.py --reset      # Reset and re-index
"""

import argparse
import sys
import os

# Add tools directory to path
tools_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, tools_dir)

# Change to project root for relative paths
project_root = os.path.dirname(tools_dir)
os.chdir(project_root)

from rag.vectorstore import ChromaVectorStore
from rag.knowledge import (
    generate_system_knowledge,
    index_all_tests,
    UserMistakeAnalyzer
)


def index_system_docs(store: ChromaVectorStore) -> int:
    """Index system documentation."""
    print("\n" + "=" * 60)
    print("📚 INDEXING SYSTEM KNOWLEDGE")
    print("=" * 60)
    
    docs = generate_system_knowledge()
    
    if not docs:
        print("[!] No system documents generated")
        return 0
    
    ids = [d["id"] for d in docs]
    contents = [d["content"] for d in docs]
    metadatas = [d["metadata"] for d in docs]
    
    store.upsert_documents(
        collection="system",
        documents=contents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"[+] Indexed {len(docs)} system documents")
    return len(docs)


def index_toeic_content(store: ChromaVectorStore) -> int:
    """Index all TOEIC tests."""
    print("\n" + "=" * 60)
    print("📝 INDEXING TOEIC CONTENT")
    print("=" * 60)
    
    count = index_all_tests(
        data_dir="data/tests",
        vector_store=store
    )
    
    return count


def index_user_analytics(store: ChromaVectorStore) -> int:
    """Index user mistake patterns."""
    print("\n" + "=" * 60)
    print("👤 INDEXING USER ANALYTICS")
    print("=" * 60)
    
    results_dir = "data/users/default"
    
    if not os.path.exists(results_dir):
        print("[!] No user results found")
        return 0
    
    analyzer = UserMistakeAnalyzer(
        results_dir=results_dir,
        tests_dir="data/tests"
    )
    
    total = 0
    
    for file_name in os.listdir(results_dir):
        if file_name.endswith(".json"):
            result_path = os.path.join(results_dir, file_name)
            
            try:
                import json
                with open(result_path, "r") as f:
                    result_data = json.load(f)
                
                mistakes = analyzer.analyze_result(result_data)
                
                if mistakes:
                    ids = [m.doc_id for m in mistakes]
                    contents = [m.to_content() for m in mistakes]
                    metadatas = [m.to_metadata() for m in mistakes]
                    
                    store.upsert_documents(
                        collection="user",
                        documents=contents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    
                    total += len(mistakes)
                    print(f"  [+] {file_name}: {len(mistakes)} mistakes")
                    
            except Exception as e:
                print(f"  [!] Error processing {file_name}: {e}")
    
    print(f"[+] Total user mistakes indexed: {total}")
    return total


def main():
    parser = argparse.ArgumentParser(description="Index all RAG data")
    parser.add_argument("--system", action="store_true", help="Only index system docs")
    parser.add_argument("--toeic", action="store_true", help="Only index TOEIC content")
    parser.add_argument("--user", action="store_true", help="Only index user analytics")
    parser.add_argument("--reset", action="store_true", help="Reset collections before indexing")
    args = parser.parse_args()
    
    # Determine what to index
    index_all = not (args.system or args.toeic or args.user)
    
    print("=" * 60)
    print("🚀 RAG INDEXING PIPELINE")
    print("=" * 60)
    
    # Initialize store
    store = ChromaVectorStore()
    print(f"[*] Vector store: {store}")
    
    # Reset if requested
    if args.reset:
        print("\n[!] Resetting collections...")
        if index_all or args.system:
            store.reset_collection("system")
        if index_all or args.toeic:
            store.reset_collection("toeic")
        if index_all or args.user:
            store.reset_collection("user")
        print("[+] Collections reset")
    
    # Index
    totals = {}
    
    if index_all or args.system:
        totals["system"] = index_system_docs(store)
    
    if index_all or args.toeic:
        totals["toeic"] = index_toeic_content(store)
    
    if index_all or args.user:
        totals["user"] = index_user_analytics(store)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INDEXING SUMMARY")
    print("=" * 60)
    
    for collection, count in totals.items():
        print(f"  {collection}: {count} documents")
    
    print(f"\n  Total: {sum(totals.values())} documents")
    
    # Show stats
    print("\n" + "=" * 60)
    print("📈 COLLECTION STATS")
    print("=" * 60)
    
    stats = store.get_all_stats()
    for name, stat in stats.items():
        if "error" not in stat:
            print(f"  {name}: {stat.get('count', 0)} documents")
        else:
            print(f"  {name}: {stat.get('error', 'N/A')}")
    
    print("\n✅ Indexing complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
