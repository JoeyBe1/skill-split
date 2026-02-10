#!/usr/bin/env python3
"""
Vector Search Demo

Demonstrates semantic search using embeddings.

Requirements:
- OPENAI_API_KEY environment variable
- Documents stored with embeddings enabled
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import DatabaseStore
from core.query import QueryAPI
from core.embedding_service import EmbeddingService


def generate_embeddings_demo():
    """Demonstrate embedding generation."""

    print("🧠 Vector Search Demo")
    print("=" * 40)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable required")
        print("\nSet it with:")
        print("  export OPENAI_API_KEY='sk-...'")
        return

    # Initialize
    db = DatabaseStore("skill_split.db")
    api = QueryAPI(db)
    embedding_service = EmbeddingService()

    # Example queries
    queries = [
        "How do I parse markdown files?",
        "database optimization techniques",
        "authentication and authorization",
        "python class structure",
    ]

    print("\n🔍 Semantic Search Examples\n")

    for query in queries:
        print(f"Query: '{query}'")

        # Generate query embedding
        query_embedding = embedding_service.embed(query)

        # Search using vector similarity
        results = api.search_sections_vector(
            query_embedding,
            limit=3
        )

        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['id']}] {result['heading']}")
            print(f"     Similarity: {result['similarity']:.3f}")
        print()


def hybrid_search_demo():
    """Demonstrate hybrid search combining BM25 and vector."""

    print("\n🎯 Hybrid Search Demo")
    print("=" * 40)

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY required for hybrid search")
        return

    db = DatabaseStore("skill_split.db")
    api = QueryAPI(db)

    query = "search functionality"
    vector_weights = [0.0, 0.3, 0.5, 0.7, 1.0]

    print(f"Query: '{query}'\n")

    for weight in vector_weights:
        mode = "Pure BM25" if weight == 0 else (
            "Pure Vector" if weight == 1.0 else f"Hybrid ({weight})"
        )

        results = api.search_sections_hybrid(
            query=query,
            vector_weight=weight,
            limit=3
        )

        print(f"{mode}:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['heading']}")
        print()


def embedding_caching_demo():
    """Demonstrate embedding caching for performance."""

    print("\n⚡ Embedding Caching Demo")
    print("=" * 40)

    from functools import lru_cache

    class CachedEmbeddingService:
        """Embedding service with LRU cache."""

        def __init__(self, cache_size: int = 1000):
            self.cache_size = cache_size
            self._cache = {}

        @lru_cache(maxsize=1000)
        def embed(self, text: str) -> list:
            """Generate embedding with caching."""
            # Simulate API call
            print(f"  Generating embedding for: '{text[:30]}...'")
            return [0.0] * 1536  # OpenAI embedding dimension

    service = CachedEmbeddingService()

    # First call - cache miss
    print("First call (cache miss):")
    service.embed("test document")

    # Second call - cache hit
    print("\nSecond call (cache hit):")
    service.embed("test document")

    print("\n✅ Caching reduces API calls and improves performance")


def main():
    """Run all vector search demos."""

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set")
        print("\nSet it with:")
        print("  export OPENAI_API_KEY='sk-...'\n")
        print("Some demos require this key.")

    # Run demos that don't require API key
    embedding_caching_demo()

    # Run demos that require API key
    if os.getenv("OPENAI_API_KEY"):
        generate_embeddings_demo()
        hybrid_search_demo()
    else:
        print("\n⏭️  Skipping semantic search demos (no API key)")

    print("\n✅ Vector search demo complete!")


if __name__ == "__main__":
    main()
