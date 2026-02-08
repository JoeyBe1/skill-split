"""
Tests for vector search functionality.

Covers:
- Embedding generation and caching
- Vector similarity search
- Text-based search
- Hybrid ranking with weighted scores
- Performance metrics tracking
- Error handling and edge cases
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from core.hybrid_search import (
    HybridSearch,
    hybrid_score,
    normalize_score,
    SearchRanker,
)


class TestHybridScore:
    """Test hybrid score calculation."""

    def test_hybrid_score_pure_vector(self):
        """Pure vector score with weight=1.0."""
        score = hybrid_score(0.9, 0.3, vector_weight=1.0)
        assert score == pytest.approx(0.9)

    def test_hybrid_score_pure_text(self):
        """Pure text score with weight=0.0."""
        score = hybrid_score(0.3, 0.9, vector_weight=0.0)
        assert score == pytest.approx(0.9)

    def test_hybrid_score_balanced(self):
        """Balanced weighting at 0.5."""
        score = hybrid_score(0.8, 0.6, vector_weight=0.5)
        expected = 0.5 * 0.8 + 0.5 * 0.6
        assert score == pytest.approx(expected)

    def test_hybrid_score_default_weight(self):
        """Default weight of 0.7 favors vector."""
        score = hybrid_score(1.0, 0.0)  # vector_weight=0.7 (default)
        expected = 0.7 * 1.0 + 0.3 * 0.0
        assert score == pytest.approx(expected)

    def test_hybrid_score_clamps_values(self):
        """Values outside [0, 1] are clamped."""
        score = hybrid_score(1.5, -0.5, vector_weight=0.7)
        expected = 0.7 * 1.0 + 0.3 * 0.0
        assert score == pytest.approx(expected)

    def test_hybrid_score_invalid_weight(self):
        """Invalid vector weight raises error."""
        with pytest.raises(ValueError):
            hybrid_score(0.5, 0.5, vector_weight=1.5)

        with pytest.raises(ValueError):
            hybrid_score(0.5, 0.5, vector_weight=-0.1)


class TestNormalizeScore:
    """Test score normalization."""

    def test_normalize_in_range(self):
        """Score within range normalizes correctly."""
        score = normalize_score(5.0, min_score=0.0, max_score=10.0)
        assert score == pytest.approx(0.5)

    def test_normalize_at_min(self):
        """Score at minimum normalizes to 0.0."""
        score = normalize_score(0.0, min_score=0.0, max_score=10.0)
        assert score == pytest.approx(0.0)

    def test_normalize_at_max(self):
        """Score at maximum normalizes to 1.0."""
        score = normalize_score(10.0, min_score=0.0, max_score=10.0)
        assert score == pytest.approx(1.0)

    def test_normalize_clamps_to_range(self):
        """Scores outside range are clamped to [0, 1]."""
        score = normalize_score(15.0, min_score=0.0, max_score=10.0)
        assert score == pytest.approx(1.0)

        score = normalize_score(-5.0, min_score=0.0, max_score=10.0)
        assert score == pytest.approx(0.0)

    def test_normalize_equal_min_max(self):
        """Equal min/max returns 0.5."""
        score = normalize_score(5.0, min_score=5.0, max_score=5.0)
        assert score == pytest.approx(0.5)


class TestHybridSearch:
    """Test HybridSearch class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.embedding_service = Mock()
        self.supabase_store = Mock()
        self.query_api = Mock()

        self.hybrid_search = HybridSearch(
            self.embedding_service,
            self.supabase_store,
            self.query_api,
        )

    def test_initialization(self):
        """HybridSearch initializes with correct metrics."""
        assert self.hybrid_search.metrics["total_searches"] == 0
        assert self.hybrid_search.metrics["vector_searches"] == 0
        assert self.hybrid_search.metrics["text_searches"] == 0
        assert self.hybrid_search.metrics["last_search_at"] is None

    def test_vector_search_success(self):
        """Vector search returns results."""
        # Mock Supabase RPC response
        self.supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {"section_id": 1, "similarity": 0.95},
                {"section_id": 2, "similarity": 0.87},
            ]
        )

        results = self.hybrid_search.vector_search([0.1] * 1536)

        assert len(results) == 2
        assert results[0] == (1, 0.95)
        assert results[1] == (2, 0.87)
        assert self.hybrid_search.metrics["vector_searches"] == 1

    def test_vector_search_empty_results(self):
        """Vector search handles empty results."""
        self.supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
            data=None
        )

        results = self.hybrid_search.vector_search([0.1] * 1536)

        assert results == []

    def test_vector_search_respects_threshold(self):
        """Vector search uses provided threshold."""
        self.supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
            data=[]
        )

        self.hybrid_search.vector_search(
            [0.1] * 1536,
            threshold=0.8,
            limit=5
        )

        # Verify RPC was called with correct parameters
        self.supabase_store.client.rpc.assert_called_once()
        call_args = self.supabase_store.client.rpc.call_args
        # call_args is a Call object, second part is kwargs dict
        assert call_args[0][0] == 'match_sections'
        assert call_args[0][1]["match_threshold"] == 0.8
        assert call_args[0][1]["match_count"] == 5

    def test_vector_search_error_handling(self):
        """Vector search raises RuntimeError on failure."""
        self.supabase_store.client.rpc.return_value.execute.side_effect = Exception("DB error")

        with pytest.raises(RuntimeError, match="Vector search failed"):
            self.hybrid_search.vector_search([0.1] * 1536)

    def test_text_search_success(self):
        """Text search returns scored results."""
        self.query_api.search_sections_with_rank.return_value = [(5, 2.5), (10, 1.5), (15, 0.5)]

        results = self.hybrid_search.text_search("authentication", limit=3)

        assert len(results) == 3
        assert results[0][0] == 5  # section_id
        assert results[0][1] == pytest.approx(1.0)  # highest score (normalized)
        assert results[2][0] == 15  # section_id
        assert results[2][1] == pytest.approx(0.0)  # lowest score (normalized)
        assert self.hybrid_search.metrics["text_searches"] == 1

    def test_text_search_empty_results(self):
        """Text search handles no results."""
        self.query_api.search_sections_with_rank.return_value = []

        results = self.hybrid_search.text_search("nonexistent")

        assert results == []

    def test_text_search_error_handling(self):
        """Text search raises RuntimeError on failure."""
        self.query_api.search_sections_with_rank.side_effect = Exception("Search error")

        with pytest.raises(RuntimeError, match="Text search failed"):
            self.hybrid_search.text_search("query")

    def test_hybrid_search_empty_query_raises_error(self):
        """Hybrid search rejects empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            self.hybrid_search.hybrid_search("")

        with pytest.raises(ValueError, match="Query cannot be empty"):
            self.hybrid_search.hybrid_search("   ")

    def test_hybrid_search_full_workflow(self):
        """Full hybrid search workflow integrates all components."""
        # Mock embedding service
        self.embedding_service.generate_embedding.return_value = [0.1] * 1536

        # Mock vector search
        self.supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {"section_id": 1, "similarity": 0.9},
                {"section_id": 2, "similarity": 0.8},
            ]
        )

        # Mock text search
        self.query_api.search_sections_with_rank.return_value = [(2, 2.0), (3, 1.0)]

        results = self.hybrid_search.hybrid_search("test query")

        # Should return merged results (1, 2, 3)
        assert len(results) <= 10  # Default limit
        section_ids = [r[0] for r in results]
        assert all(isinstance(sid, int) for sid in section_ids)

        # Verify metrics updated
        assert self.hybrid_search.metrics["total_searches"] == 1

    def test_hybrid_search_tracks_latency(self):
        """Hybrid search tracks query latency."""
        # Mock responses
        self.embedding_service.generate_embedding.return_value = [0.1] * 1536
        self.supabase_store.client.rpc.return_value.execute.return_value = MagicMock(data=[])
        self.query_api.search_sections_with_rank.return_value = []

        self.hybrid_search.hybrid_search("test")

        metrics = self.hybrid_search.get_metrics()
        assert metrics["average_latency_ms"] > 0
        assert metrics["total_latency_ms"] > 0
        assert metrics["last_search_at"] is not None

    def test_hybrid_search_respects_vector_weight(self):
        """Hybrid search uses provided vector weight."""
        # Mock responses
        self.embedding_service.generate_embedding.return_value = [0.1] * 1536
        self.supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
            data=[{"section_id": 1, "similarity": 1.0}]
        )
        self.query_api.search_sections_with_rank.return_value = [(2, 2.0)]

        # Test with different weights
        results_high = self.hybrid_search.hybrid_search("test", vector_weight=0.9)
        results_low = self.hybrid_search.hybrid_search("test", vector_weight=0.1)

        # Results should be different due to different weights
        assert results_high != results_low

    def test_merge_rankings_combines_results(self):
        """_merge_rankings combines vector and text results."""
        vector_results = [(1, 0.9), (2, 0.8), (3, 0.7)]
        text_results = [(2, 0.95), (3, 0.85), (4, 0.75)]

        combined = self.hybrid_search._merge_rankings(
            vector_results,
            text_results,
            vector_weight=0.7,
            limit=10
        )

        # Should contain all unique IDs
        ids = [r[0] for r in combined]
        assert set(ids) == {1, 2, 3, 4}

        # Results should be sorted by hybrid score
        scores = [r[1] for r in combined]
        assert scores == sorted(scores, reverse=True)

    def test_merge_rankings_respects_limit(self):
        """_merge_rankings respects result limit."""
        vector_results = [(i, 1.0 - i/100) for i in range(1, 21)]
        text_results = [(i, 0.5) for i in range(1, 21)]

        combined = self.hybrid_search._merge_rankings(
            vector_results,
            text_results,
            vector_weight=0.7,
            limit=5
        )

        assert len(combined) == 5

    def test_get_metrics_complete(self):
        """get_metrics returns all tracked metrics."""
        # Run a search to generate metrics
        self.embedding_service.generate_embedding.return_value = [0.1] * 1536
        self.supabase_store.client.rpc.return_value.execute.return_value = MagicMock(data=[])
        self.query_api.search_sections_with_rank.return_value = []

        self.hybrid_search.hybrid_search("test")

        metrics = self.hybrid_search.get_metrics()

        # Check all expected metrics are present
        assert "total_searches" in metrics
        assert "vector_searches" in metrics
        assert "text_searches" in metrics
        assert "average_latency_ms" in metrics
        assert "total_latency_ms" in metrics
        assert "embedding_cache_hits" in metrics
        assert "embedding_cache_misses" in metrics
        assert "cache_hit_rate" in metrics
        assert "last_search_at" in metrics

    def test_reset_metrics(self):
        """reset_metrics clears all tracking."""
        # Populate metrics
        self.hybrid_search.metrics["total_searches"] = 5
        self.hybrid_search.metrics["total_latency_ms"] = 100.0

        self.hybrid_search.reset_metrics()

        assert self.hybrid_search.metrics["total_searches"] == 0
        assert self.hybrid_search.metrics["total_latency_ms"] == 0
        assert self.hybrid_search.metrics["last_search_at"] is None


class TestSearchRanker:
    """Test SearchRanker utility class."""

    def test_normalize_similarity_scores(self):
        """normalize_similarity_scores normalizes vector scores."""
        scores = [0.1, 0.5, 0.9, 0.3]
        normalized = SearchRanker.normalize_similarity_scores(scores)

        assert all(0.0 <= s <= 1.0 for s in normalized)
        assert normalized[2] == pytest.approx(1.0)  # max
        assert normalized[0] == pytest.approx(0.0)  # min

    def test_normalize_similarity_empty(self):
        """normalize_similarity_scores handles empty input."""
        normalized = SearchRanker.normalize_similarity_scores([])
        assert normalized == []

    def test_rank_by_frequency(self):
        """rank_by_frequency boosts frequently appearing results."""
        results = [
            (1, 0.9),
            (2, 0.8),
            (1, 0.7),  # 1 appears twice
            (3, 0.6),
        ]

        ranked = SearchRanker.rank_by_frequency(results)

        # Should contain all unique IDs
        ids = [r[0] for r in ranked]
        assert set(ids) == {1, 2, 3}

        # ID 1 should rank higher due to frequency
        id_1_score = next(r[1] for r in ranked if r[0] == 1)
        id_2_score = next(r[1] for r in ranked if r[0] == 2)
        assert id_1_score > id_2_score

    def test_rank_by_frequency_boost(self):
        """rank_by_frequency applies frequency boost correctly."""
        # Same result appearing 3 times
        results = [(1, 0.5), (1, 0.5), (1, 0.5)]

        ranked = SearchRanker.rank_by_frequency(results)

        # Score should be boosted
        assert len(ranked) == 1
        assert ranked[0][0] == 1
        assert ranked[0][1] > 0.5  # Boosted from original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
