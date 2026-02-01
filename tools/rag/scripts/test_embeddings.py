#!/usr/bin/env python
"""
Test Embedding Providers
========================
Quick test to verify embedding providers are working correctly.

Usage:
    python test_embeddings.py
    python test_embeddings.py --provider openai
    python test_embeddings.py --provider google
    python test_embeddings.py --provider local
"""

import argparse
import sys
import os

# Add tools directory to path
tools_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, tools_dir)

from rag.embeddings import get_embedding_provider
from rag.config import get_config, EmbeddingConfig


def test_embedding_provider(provider_name: str = None):
    """Test embedding provider."""
    
    print("=" * 60)
    print("🧪 TESTING EMBEDDING PROVIDER")
    print("=" * 60)
    
    config = get_config()
    
    if provider_name:
        # Override provider
        config.embedding.provider = provider_name
        print(f"📌 Using provider: {provider_name}")
    else:
        print(f"📌 Using default provider from .env: {config.embedding.provider}")
    
    print()
    
    try:
        # Get provider
        print("[*] Loading embedding provider...")
        provider = get_embedding_provider(config.embedding)
        print(f"[+] Provider loaded: {provider}")
        print(f"    - Provider name: {provider.provider_name}")
        print(f"    - Dimensions: {provider.dimensions}")
        
        # Test single query
        print()
        print("[*] Testing single query embedding...")
        test_query = "What is the correct answer for Part 2 question about meeting location?"
        embedding = provider.embed_query(test_query)
        print(f"[+] Query: '{test_query[:50]}...'")
        print(f"    - Embedding length: {len(embedding)}")
        print(f"    - First 5 values: {embedding[:5]}")
        
        # Test batch embedding
        print()
        print("[*] Testing batch embedding...")
        test_texts = [
            "She's holding a piece of paper.",
            "There's a clock in the tower.",
            "The meeting is in the conference room.",
            "Due to adverse weather conditions, the flight is delayed."
        ]
        result = provider.embed_texts(test_texts)
        print(f"[+] Embedded {len(result)} texts")
        print(f"    - Model: {result.model}")
        print(f"    - Dimensions: {result.dimensions}")
        if result.token_usage:
            print(f"    - Token usage: {result.token_usage}")
        
        # Verify dimensions match
        for i, emb in enumerate(result.embeddings):
            assert len(emb) == result.dimensions, f"Dimension mismatch at index {i}"
        print("[+] All embeddings have correct dimensions ✓")
        
        # Test similarity (simple cosine)
        print()
        print("[*] Testing semantic similarity...")
        
        def cosine_similarity(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x ** 2 for x in a) ** 0.5
            norm_b = sum(x ** 2 for x in b) ** 0.5
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0
        
        # Embed similar and different texts
        similar_texts = ["The flight is delayed.", "The airplane departure is postponed."]
        different_text = "She's reading a magazine in the park."
        
        similar_embs = provider.embed_texts(similar_texts)
        diff_emb = provider.embed_query(different_text)
        
        sim_same = cosine_similarity(similar_embs[0], similar_embs[1])
        sim_diff = cosine_similarity(similar_embs[0], diff_emb)
        
        print(f"    - Similar texts: {sim_same:.4f}")
        print(f"    - Different texts: {sim_diff:.4f}")
        
        if sim_same > sim_diff:
            print("[+] Semantic similarity working correctly ✓")
        else:
            print("[!] Warning: Similar texts should have higher similarity")
        
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test embedding providers")
    parser.add_argument(
        "--provider", "-p",
        choices=["openai", "google", "local"],
        help="Override embedding provider"
    )
    args = parser.parse_args()
    
    success = test_embedding_provider(args.provider)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
