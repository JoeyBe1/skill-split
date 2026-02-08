"""
Hybrid search combining vector and text-based ranking.

This module implements hybrid search that merges vector similarity
and text-based search results to provide better ranking than either
approach alone.

Features:
- Adjustable vector/text weight balance
- Normalized scoring for fair comparison
- Duplicate handling from multiple sources
- Performance metrics tracking
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Optional, Any
import math
from datetime import datetime


def normalize_score(score: float, min_score: float = 0.0, max_score: float = 1.0) -> float:
    """
    Normalize a score to [0, 1] range.

    Args:
        score: Raw score to normalize
        min_score: Expected minimum score
        max_score: Expected maximum score

    Returns:
        Normalized score in [0, 1] range
    """
    if max_score == min_score:
        return 0.5
    return max(0.0, min(1.0, (score - min_score) / (max_score - min_score)))


def hybrid_score(
    vector_similarity: float,
    text_score: float,
    vector_weight: float = 0.7
) -> float:
    """
    Combine vector and text scores using weighted average.

    This is the core hybrid scoring function that combines two ranking
    signals: vector similarity (semantic) and text search (keyword).

    The vector_weight parameter controls the balance:
    - 1.0 = pure vector search
    - 0.5 = equal weight
    - 0.0 = pure text search

    Args:
        vector_similarity: Vector similarity score (typically 0-1)
        text_score: Text search score (typically 0-1)
        vector_weight: Weight for vector score (0.0 to 1.0)

    Returns:
        Hybrid score (0.0 to 1.0)

    Examples:
        >>> hybrid_score(0.9, 0.5, 0.7)  # High vector, med text, 70% vector weight
        0.78
    """
    if not (0.0 <= vector_weight <= 1.0):
        raise ValueError(f"vector_weight must be in [0, 1], got {vector_weight}")

    # Ensure scores are in valid range
    vec_score = max(0.0, min(1.0, vector_similarity))
    text_score_normalized = max(0.0, min(1.0, text_score))

    # Weighted combination
    return (vector_weight * vec_score) + ((1 - vector_weight) * text_score_normalized)


class HybridSearch:
    """
    Implements hybrid search combining vector and text rankings.

    This class manages the combination of vector similarity search
    and traditional text search to produce ranked results.
    """

    def __init__(
        self,
        embedding_service: Any,
        supabase_store: Any,
        query_api: Any,
    ):
        """
        Initialize hybrid search.

        Args:
            embedding_service: EmbeddingService instance for generating embeddings
            supabase_store: SupabaseStore for vector search queries
            query_api: QueryAPI instance for text search
        """
        self.embedding_service = embedding_service
        self.supabase_store = supabase_store
        self.query_api = query_api
        self.metrics = {
            "total_searches": 0,
            "total_latency_ms": 0,
            "vector_searches": 0,
            "text_searches": 0,
            "last_search_at": None,
            "total_embedding_time_ms": 0.0,
            "embedding_cache_hits": 0,
            "embedding_cache_misses": 0,
            "average_results_per_search": 0.0,
            "failed_searches": 0,
        }

    def vector_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Tuple[int, float]]:
        """
        Search sections by vector similarity.

        Args:
            query_embedding: Embedding vector from query
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of (section_id, similarity_score) tuples

        Raises:
            RuntimeError: If vector search fails
        """
        try:
            # Use Supabase RPC for vector search with pgvector
            # This assumes a match_sections RPC function exists
            result = self.supabase_store.client.rpc(
                'match_sections',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()

            results = []
            if result.data:
                for row in result.data:
                    section_id = row.get('section_id')
                    similarity = row.get('similarity', 0.0)
                    results.append((section_id, float(similarity)))

            self.metrics["vector_searches"] += 1
            return results

        except Exception as e:
            raise RuntimeError(f"Vector search failed: {str(e)}")

    def text_search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Search sections using text-based matching.

        Uses the QueryAPI search_sections method which performs
        substring and relevance matching.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of (section_id, relevance_score) tuples
        """
        try:
            # Use QueryAPI search_sections
            results = self.query_api.search_sections(query)

            # Convert to list of (section_id, score) tuples
            # For text search, we assign scores based on position (first = higher)
            scored_results = []
            for i, section_id in enumerate(results[:limit]):
                # Score decreases with position
                score = max(0.0, 1.0 - (i / limit))
                scored_results.append((section_id, score))

            self.metrics["text_searches"] += 1
            return scored_results

        except Exception as e:
            raise RuntimeError(f"Text search failed: {str(e)}")

    def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        vector_weight: float = 0.7
    ) -> List[Tuple[int, float]]:
        """
        Execute hybrid search combining vector and text approaches.

        Process:
        1. Generate embedding for query
        2. Run vector search in parallel
        3. Run text search in parallel
        4. Merge results with hybrid scoring
        5. Return top results

        Args:
            query: Search query string
            limit: Maximum results to return
            vector_weight: Weight for vector results (0.0-1.0)

        Returns:
            List of (section_id, score) tuples, ranked by score

        Raises:
            ValueError: If query is empty
            RuntimeError: If search fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        start_time = datetime.now()

        try:
            # Track embedding generation time
            embedding_start = datetime.now()
            query_embedding = self.embedding_service.generate_embedding(query)
            embedding_time = (datetime.now() - embedding_start).total_seconds() * 1000
            self.metrics["total_embedding_time_ms"] += embedding_time

            # Check if embedding was cached
            if hasattr(self.embedding_service, 'last_cached'):
                if self.embedding_service.last_cached:
                    self.metrics["embedding_cache_hits"] += 1
                else:
                    self.metrics["embedding_cache_misses"] += 1

            # Run both searches with expanded limits to get more candidates
            expanded_limit = limit * 2

            vector_results = self.vector_search(
                query_embedding,
                limit=expanded_limit,
                threshold=0.7
            )

            text_results = self.text_search(query, limit=expanded_limit)

            # Merge and score results
            combined = self._merge_rankings(
                vector_results,
                text_results,
                vector_weight,
                limit
            )

            # Track metrics
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["total_searches"] += 1
            self.metrics["total_latency_ms"] += elapsed
            self.metrics["last_search_at"] = datetime.now().isoformat()

            # Update average results per search
            total_results = sum(1 for _ in combined)
            if self.metrics["total_searches"] > 0:
                self.metrics["average_results_per_search"] = \
                    (self.metrics.get("total_results", 0) + total_results) / self.metrics["total_searches"]
                self.metrics["total_results"] = self.metrics.get("total_results", 0) + total_results

            return combined

        except Exception as e:
            self.metrics["failed_searches"] += 1
            raise RuntimeError(f"Hybrid search failed: {str(e)}")

    def _merge_rankings(
        self,
        vector_results: List[Tuple[int, float]],
        text_results: List[Tuple[int, float]],
        vector_weight: float,
        limit: int
    ) -> List[Tuple[int, float]]:
        """
        Merge vector and text results with hybrid scoring.

        Strategy:
        1. Normalize both result sets to [0, 1] scale
        2. For each unique section, apply hybrid_score
        3. Sort by score descending
        4. Return top N results

        Args:
            vector_results: Results from vector search
            text_results: Results from text search
            vector_weight: Weight for vector scoring
            limit: Maximum results to return

        Returns:
            List of (section_id, hybrid_score) tuples
        """
        # Build dictionaries for lookup
        vector_dict = {sid: score for sid, score in vector_results}
        text_dict = {sid: score for sid, score in text_results}

        # Collect all unique section IDs
        all_ids = set(vector_dict.keys()) | set(text_dict.keys())

        # Calculate hybrid scores
        scored_results = []
        for section_id in all_ids:
            vector_score = vector_dict.get(section_id, 0.0)
            text_score = text_dict.get(section_id, 0.0)

            combined = hybrid_score(vector_score, text_score, vector_weight)
            scored_results.append((section_id, combined))

        # Sort by score descending
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Return top N
        return scored_results[:limit]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive search metrics and performance statistics.

        Returns:
            Dictionary with detailed search statistics including latency,
            embedding times, cache hit rates, and error tracking.
        """
        avg_latency = 0.0
        if self.metrics["total_searches"] > 0:
            avg_latency = self.metrics["total_latency_ms"] / self.metrics["total_searches"]

        avg_embedding_time = 0.0
        if self.metrics["total_searches"] > 0:
            avg_embedding_time = self.metrics["total_embedding_time_ms"] / self.metrics["total_searches"]

        cache_hit_rate = 0.0
        total_cache_accesses = self.metrics["embedding_cache_hits"] + self.metrics["embedding_cache_misses"]
        if total_cache_accesses > 0:
            cache_hit_rate = self.metrics["embedding_cache_hits"] / total_cache_accesses

        return {
            "total_searches": self.metrics["total_searches"],
            "failed_searches": self.metrics["failed_searches"],
            "vector_searches": self.metrics["vector_searches"],
            "text_searches": self.metrics["text_searches"],
            "average_latency_ms": round(avg_latency, 2),
            "total_latency_ms": self.metrics["total_latency_ms"],
            "average_embedding_time_ms": round(avg_embedding_time, 2),
            "total_embedding_time_ms": self.metrics["total_embedding_time_ms"],
            "embedding_cache_hits": self.metrics["embedding_cache_hits"],
            "embedding_cache_misses": self.metrics["embedding_cache_misses"],
            "cache_hit_rate": round(cache_hit_rate, 3),
            "average_results_per_search": round(self.metrics["average_results_per_search"], 2),
            "last_search_at": self.metrics["last_search_at"],
        }

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "total_searches": 0,
            "total_latency_ms": 0,
            "vector_searches": 0,
            "text_searches": 0,
            "last_search_at": None,
        }


class SearchRanker:
    """
    Helper class for search result ranking and normalization.

    Provides utilities for normalizing scores from different search
    sources and combining them effectively.
    """

    @staticmethod
    def normalize_similarity_scores(
        scores: List[float],
    ) -> List[float]:
        """
        Normalize vector similarity scores to [0, 1].

        Args:
            scores: Raw similarity scores (e.g., from cosine similarity)

        Returns:
            Normalized scores in [0, 1] range
        """
        if not scores:
            return []

        min_score = min(scores)
        max_score = max(scores)

        return [
            normalize_score(s, min_score, max_score)
            for s in scores
        ]

    @staticmethod
    def rank_by_frequency(
        results: List[Tuple[int, float]],
    ) -> List[Tuple[int, float]]:
        """
        Boost results that appear in multiple rankings.

        Args:
            results: List of (section_id, score) tuples

        Returns:
            Adjusted scores based on frequency
        """
        id_scores = {}
        id_count = {}

        for section_id, score in results:
            if section_id not in id_scores:
                id_scores[section_id] = 0.0
                id_count[section_id] = 0

            id_scores[section_id] += score
            id_count[section_id] += 1

        # Average score for each ID, boosted by frequency
        adjusted = []
        for section_id in id_scores:
            count = id_count[section_id]
            avg_score = id_scores[section_id] / count
            # Apply frequency boost (max 1.5x)
            frequency_boost = min(1.5, 1.0 + (count - 1) * 0.25)
            final_score = min(1.0, avg_score * frequency_boost)
            adjusted.append((section_id, final_score))

        # Sort by final score
        adjusted.sort(key=lambda x: x[1], reverse=True)

        return adjusted
