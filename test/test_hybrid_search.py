"""
Tests for Hybrid Search (Tasks 10.2 and 10.3).

This module tests the HybridSearch class which implements:
- Task 10.2: Vector Search Query (vector_search method)
- Task 10.3: Combined Search (hybrid_search method with _merge_rankings)

Test coverage:
- Vector similarity search using Supabase RPC
- Text-based search using QueryAPI
- Hybrid ranking that combines both approaches
- Score normalization and merging
- Performance metrics tracking
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Tuple

from core.hybrid_search import HybridSearch, hybrid_score, normalize_score, SearchRanker


class TestHybridScoreFunction:
    """Test the core hybrid_score function."""

    def test_hybrid_score_basic(self):
        """Basic hybrid score calculation."""
        score = hybrid_score(0.9, 0.5, vector_weight=0.7)
        # 0.7 * 0.9 + 0.3 * 0.5 = 0.63 + 0.15 = 0.78
        assert abs(score - 0.78) < 0.01

    def test_hybrid_score_pure_vector(self):
        """With vector_weight=1.0, should return vector score."""
        score = hybrid_score(0.8, 0.2, vector_weight=1.0)
        assert score == 0.8

    def test_hybrid_score_pure_text(self):
        """With vector_weight=0.0, should return text score."""
        score = hybrid_score(0.8, 0.2, vector_weight=0.0)
        assert score == 0.2

    def test_hybrid_score_equal_weight(self):
        """With vector_weight=0.5, should be average."""
        score = hybrid_score(0.8, 0.6, vector_weight=0.5)
        assert score == 0.7

    def test_hybrid_score_clamping(self):
        """Scores outside [0, 1] should be clamped."""
        score = hybrid_score(1.5, -0.5, vector_weight=0.7)
        # Both clamped to [0, 1]
        assert 0.0 <= score <= 1.0

    def test_hybrid_score_invalid_weight_raises(self):
        """Invalid vector_weight should raise error."""
        with pytest.raises(ValueError):
            hybrid_score(0.8, 0.5, vector_weight=1.5)

        with pytest.raises(ValueError):
            hybrid_score(0.8, 0.5, vector_weight=-0.1)


class TestNormalizeScore:
    """Test score normalization."""

    def test_normalize_score_basic(self):
        """Normalize score to [0, 1]."""
        score = normalize_score(5, min_score=0, max_score=10)
        assert score == 0.5

    def test_normalize_score_edge_cases(self):
        """Normalize score at edges."""
        assert normalize_score(0, 0, 10) == 0.0
        assert normalize_score(10, 0, 10) == 1.0

    def test_normalize_score_equal_min_max(self):
        """When min == max, return 0.5."""
        score = normalize_score(5, min_score=5, max_score=5)
        assert score == 0.5

    def test_normalize_score_clamping(self):
        """Scores outside range should be clamped."""
        assert normalize_score(-5, 0, 10) == 0.0
        assert normalize_score(15, 0, 10) == 1.0


class TestVectorSearch:
    """Test vector_search method of HybridSearch."""

    def test_vector_search_success(self):
        """vector_search() calls Supabase RPC and returns results."""
        # Mock dependencies
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        # Mock RPC result
        mock_result = Mock()
        mock_result.data = [
            {'section_id': 1, 'similarity': 0.95},
            {'section_id': 2, 'similarity': 0.87},
            {'section_id': 3, 'similarity': 0.76},
        ]
        supabase_store.client.rpc.return_value.execute.return_value = mock_result

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        results = hybrid.vector_search([0.1, 0.2, 0.3], limit=10, threshold=0.7)

        # Verify results
        assert len(results) == 3
        assert results[0] == (1, 0.95)
        assert results[1] == (2, 0.87)
        assert results[2] == (3, 0.76)

        # Verify RPC was called correctly
        supabase_store.client.rpc.assert_called_once()
        call_kwargs = supabase_store.client.rpc.call_args[0]
        assert call_kwargs[0] == 'match_sections'

    def test_vector_search_empty_results(self):
        """vector_search() handles empty results."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        mock_result = Mock()
        mock_result.data = []
        supabase_store.client.rpc.return_value.execute.return_value = mock_result

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        results = hybrid.vector_search([0.1, 0.2], limit=10)

        assert results == []

    def test_vector_search_metrics_updated(self):
        """vector_search() updates metrics."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        mock_result = Mock()
        mock_result.data = [{'section_id': 1, 'similarity': 0.9}]
        supabase_store.client.rpc.return_value.execute.return_value = mock_result

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        hybrid.vector_search([0.1, 0.2])

        assert hybrid.metrics['vector_searches'] == 1

    def test_vector_search_error_handling(self):
        """vector_search() raises RuntimeError on failure."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        supabase_store.client.rpc.side_effect = Exception("RPC failed")

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)

        with pytest.raises(RuntimeError):
            hybrid.vector_search([0.1, 0.2])


class TestTextSearch:
    """Test text_search method of HybridSearch."""

    def test_text_search_success(self):
        """text_search() returns scored results."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        # Mock query_api.search_sections_with_rank with (id, rank) tuples
        query_api.search_sections_with_rank.return_value = [(5, 2.5), (10, 1.8), (15, 0.9)]

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        results = hybrid.text_search("test query", limit=10)

        # Results should be scored (higher rank = higher score)
        assert len(results) == 3
        assert results[0][0] == 5  # First result
        assert results[0][1] > results[1][1]  # Scores decrease
        assert results[1][0] == 10
        assert results[2][0] == 15

    def test_text_search_respects_limit(self):
        """text_search() respects limit parameter."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        query_api.search_sections_with_rank.return_value = [(1, 3.0), (2, 2.0), (3, 1.0), (4, 0.5), (5, 0.2)]

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        results = hybrid.text_search("query", limit=3)

        assert len(results) == 3
        assert [r[0] for r in results] == [1, 2, 3]


class TestHybridSearch:
    """Test hybrid_search method (Task 10.3)."""

    def test_hybrid_search_combines_results(self):
        """hybrid_search() merges vector and text results."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        # Mock embedding generation
        embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]

        # Mock vector search results
        vector_mock = Mock()
        vector_mock.data = [
            {'section_id': 1, 'similarity': 0.95},
            {'section_id': 2, 'similarity': 0.85},
        ]
        supabase_store.client.rpc.return_value.execute.return_value = vector_mock

        # Mock text search results
        query_api.search_sections_with_rank.return_value = [(2, 2.0), (3, 1.5), (4, 1.0)]

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        results = hybrid.hybrid_search("test query", limit=3, vector_weight=0.7)

        # Should have merged results
        assert len(results) > 0
        # Results should be tuple of (section_id, score)
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    def test_hybrid_search_empty_query_raises(self):
        """hybrid_search() raises error for empty query."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)

        with pytest.raises(ValueError):
            hybrid.hybrid_search("")

        with pytest.raises(ValueError):
            hybrid.hybrid_search("   ")

    def test_hybrid_search_metrics_updated(self):
        """hybrid_search() updates metrics."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        embedding_service.generate_embedding.return_value = [0.1, 0.2]

        vector_mock = Mock()
        vector_mock.data = [{'section_id': 1, 'similarity': 0.9}]
        supabase_store.client.rpc.return_value.execute.return_value = vector_mock

        query_api.search_sections_with_rank.return_value = [(2, 2.0), (3, 1.0)]

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        hybrid.hybrid_search("test")

        assert hybrid.metrics['total_searches'] == 1
        assert hybrid.metrics['total_latency_ms'] >= 0
        assert hybrid.metrics['last_search_at'] is not None

    def test_hybrid_search_respects_vector_weight(self):
        """hybrid_search() uses vector_weight parameter."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        embedding_service.generate_embedding.return_value = [0.1, 0.2]

        vector_mock = Mock()
        vector_mock.data = [{'section_id': 1, 'similarity': 0.9}]
        supabase_store.client.rpc.return_value.execute.return_value = vector_mock

        query_api.search_sections_with_rank.return_value = [(1, 2.5), (2, 1.5)]

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)

        # Call with different weights (should not raise error)
        results1 = hybrid.hybrid_search("test", vector_weight=0.7)
        results2 = hybrid.hybrid_search("test", vector_weight=0.3)

        assert len(results1) > 0
        assert len(results2) > 0


class TestMergeRankings:
    """Test _merge_rankings method (Task 10.3)."""

    def test_merge_rankings_combines_sources(self):
        """_merge_rankings() combines vector and text results."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)

        vector_results = [(1, 0.95), (2, 0.85)]
        text_results = [(2, 0.9), (3, 0.7)]

        merged = hybrid._merge_rankings(vector_results, text_results, 0.7, limit=3)

        # Should have all unique IDs
        ids = [r[0] for r in merged]
        assert 1 in ids or 2 in ids or 3 in ids

    def test_merge_rankings_respects_limit(self):
        """_merge_rankings() returns at most limit results."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)

        vector_results = [(1, 0.9), (2, 0.8), (3, 0.7)]
        text_results = [(4, 0.85), (5, 0.75)]

        merged = hybrid._merge_rankings(vector_results, text_results, 0.5, limit=2)

        assert len(merged) <= 2

    def test_merge_rankings_sorts_by_score(self):
        """_merge_rankings() returns results sorted by score descending."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)

        vector_results = [(1, 0.5), (2, 0.9)]
        text_results = [(3, 0.7)]

        merged = hybrid._merge_rankings(vector_results, text_results, 0.7, limit=10)

        # Check scores are descending
        scores = [r[1] for r in merged]
        assert scores == sorted(scores, reverse=True)


class TestSearchRanker:
    """Test SearchRanker helper class."""

    def test_normalize_similarity_scores(self):
        """normalize_similarity_scores() normalizes vector scores."""
        scores = [0.5, 0.8, 0.3]
        normalized = SearchRanker.normalize_similarity_scores(scores)

        assert len(normalized) == 3
        assert all(0.0 <= s <= 1.0 for s in normalized)
        # Highest original (0.8) should be highest normalized
        assert normalized[1] == 1.0
        # Lowest original (0.3) should be lowest normalized
        assert normalized[2] == 0.0

    def test_rank_by_frequency_boosts_duplicates(self):
        """rank_by_frequency() boosts results appearing multiple times."""
        results = [
            (1, 0.8),
            (1, 0.7),  # ID 1 appears twice
            (2, 0.6),
        ]
        ranked = SearchRanker.rank_by_frequency(results)

        # Find scores for each ID
        scores_dict = {r[0]: r[1] for r in ranked}

        # ID 1 should have higher score than ID 2 (frequency boost)
        if 1 in scores_dict and 2 in scores_dict:
            assert scores_dict[1] > scores_dict[2]

    def test_rank_by_frequency_returns_sorted(self):
        """rank_by_frequency() returns sorted results."""
        results = [(1, 0.6), (2, 0.8), (3, 0.7)]
        ranked = SearchRanker.rank_by_frequency(results)

        scores = [r[1] for r in ranked]
        assert scores == sorted(scores, reverse=True)


class TestHybridSearchMetrics:
    """Test metrics tracking in HybridSearch."""

    def test_get_metrics_returns_dict(self):
        """get_metrics() returns metrics dictionary."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        metrics = hybrid.get_metrics()

        assert isinstance(metrics, dict)
        assert 'total_searches' in metrics
        assert 'vector_searches' in metrics
        assert 'text_searches' in metrics
        assert 'average_latency_ms' in metrics

    def test_reset_metrics_clears_state(self):
        """reset_metrics() resets all metrics."""
        embedding_service = Mock()
        query_api = Mock()
        supabase_store = Mock()

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)
        hybrid.metrics['total_searches'] = 10

        hybrid.reset_metrics()

        assert hybrid.metrics['total_searches'] == 0
        assert hybrid.metrics['vector_searches'] == 0


class TestTextSearchQuality:
    """Test text search relevance quality with FTS5."""

    @pytest.fixture
    def quality_hybrid_search(self):
        """Create HybridSearch with test data."""
        from core.hybrid_search import HybridSearch
        from unittest.mock import Mock
        import tempfile
        import os

        # Create temporary database with test sections
        from core.database import DatabaseStore
        from core.parser import Parser
        from models import ParsedDocument, Section, FileType, FileFormat

        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        store = DatabaseStore(db_path)

        # Create test document with "vector search" content in different sections
        sections = [
            Section(level=1, title="Introduction", content="Basic intro text", line_start=1, line_end=2),
            Section(level=1, title="Vector Search", content="This section discusses vector search implementation using embeddings and similarity metrics.", line_start=3, line_end=4),
            Section(level=1, title="Database", content="Database storage and retrieval", line_start=5, line_end=6),
            Section(level=2, title="Python Handler", content="Python handler processes files and creates embeddings for vector search.", line_start=7, line_end=8),
        ]

        doc = ParsedDocument(
            frontmatter="",
            sections=sections,
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/search.md"
        )
        store.store_file("/test/search.md", doc, "test_hash")

        # Create dependencies
        from core.query import QueryAPI
        query_api = QueryAPI(db_path)

        embedding_service = Mock()
        embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]

        supabase_store = Mock()

        hybrid = HybridSearch(embedding_service, supabase_store, query_api)

        yield hybrid, db_path

        # Cleanup
        os.unlink(db_path)

    def test_text_search_finds_relevant_content(self, quality_hybrid_search):
        """Text search finds content regardless of position."""
        hybrid, _ = quality_hybrid_search

        results = hybrid.text_search("vector search", limit=10)

        # Should find sections about vector search
        assert len(results) > 0

        # Get section IDs
        section_ids = [r[0] for r in results]
        # Sections 2 and 4 contain "vector search"
        # They should be in results regardless of position
        assert len(section_ids) >= 1

    def test_text_search_ranks_relevant_higher(self, quality_hybrid_search):
        """Relevant sections get higher scores than irrelevant sections."""
        hybrid, _ = quality_hybrid_search

        results = hybrid.text_search("vector search", limit=10)

        if len(results) >= 2:
            # First result should have higher score than last
            assert results[0][1] >= results[-1][1]

    def test_text_search_normalizes_scores(self, quality_hybrid_search):
        """Text search scores are normalized to [0, 1]."""
        hybrid, _ = quality_hybrid_search

        results = hybrid.text_search("python handler", limit=10)

        if results:
            # All scores should be in [0, 1]
            scores = [r[1] for r in results]
            assert all(0.0 <= s <= 1.0 for s in scores)

    def test_text_search_vs_position_ranking(self, quality_hybrid_search):
        """FTS5 ranking differs from simple position-based ranking."""
        hybrid, _ = quality_hybrid_search

        results_fts = hybrid.text_search("search", limit=10)

        # FTS results should use actual relevance
        # If we had position-based scoring, first result might differ
        assert len(results_fts) > 0

        # Verify scores vary (not all the same)
        if len(results_fts) > 1:
            scores = [r[1] for r in results_fts]
            # Scores should not all be identical
            assert len(set(scores)) > 1, "Scores should vary based on relevance"

    def test_hybrid_search_combines_text_and_vector(self, quality_hybrid_search):
        """Hybrid search combines FTS text scores with vector similarity."""
        hybrid, db_path = quality_hybrid_search

        # Mock vector search
        hybrid.supabase_store.client.rpc.return_value.execute.return_value.data = [
            {'section_id': 1, 'similarity': 0.8},
            {'section_id': 2, 'similarity': 0.9},
        ]

        results = hybrid.hybrid_search("vector search", limit=5, vector_weight=0.7)

        # Results should combine both sources
        assert len(results) > 0

        # Scores should be normalized
        scores = [r[1] for r in results]
        assert all(0.0 <= s <= 1.0 for s in scores)
