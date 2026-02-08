"""
Tests for EmbeddingService.

Covers embedding generation, caching, batch operations, and cost estimation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from core.embedding_service import EmbeddingService


class TestEmbeddingServiceBasic:
    """Test basic embedding service functionality."""

    @patch('core.embedding_service.OpenAI')
    def test_init_with_api_key(self, mock_openai):
        """Test initialization with explicit API key."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key-123")

        assert service.api_key == "test-key-123"
        assert service.model == "text-embedding-3-small"
        assert service.EMBEDDING_DIMENSIONS == 1536
        assert service._token_usage == 0

    @patch('core.embedding_service.OpenAI')
    def test_init_missing_api_key(self, mock_openai):
        """Test initialization fails without API key."""
        mock_openai.return_value = MagicMock()

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not provided"):
                EmbeddingService()

    @patch('core.embedding_service.OpenAI')
    def test_generate_embedding_success(self, mock_openai):
        """Test successful embedding generation."""
        # Setup mock response
        mock_embedding = [0.1, 0.2, 0.3] * 512  # Dummy 1536-dim vector
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        mock_response.usage = MagicMock(prompt_tokens=10)

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")
        result = service.generate_embedding("test text")

        assert result == mock_embedding
        assert service.get_token_usage() == 10

    @patch('core.embedding_service.OpenAI')
    def test_generate_embedding_empty_text(self, mock_openai):
        """Test embedding generation rejects empty text."""
        mock_openai.return_value = MagicMock()

        service = EmbeddingService(api_key="test-key")

        with pytest.raises(ValueError, match="empty text"):
            service.generate_embedding("")

        with pytest.raises(ValueError, match="empty text"):
            service.generate_embedding("   ")

    @patch('core.embedding_service.OpenAI')
    def test_generate_embedding_api_error(self, mock_openai):
        """Test embedding generation handles API errors."""
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")

        with pytest.raises(RuntimeError, match="Failed to generate embedding"):
            service.generate_embedding("test text")


class TestBatchGeneration:
    """Test batch embedding generation."""

    @patch('core.embedding_service.OpenAI')
    def test_batch_generate_success(self, mock_openai):
        """Test successful batch embedding."""
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=mock_embedding),
            MagicMock(embedding=mock_embedding),
            MagicMock(embedding=mock_embedding),
        ]
        mock_response.usage = MagicMock(prompt_tokens=30)

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")
        texts = ["text1", "text2", "text3"]
        results = service.batch_generate(texts)

        assert len(results) == 3
        assert all(r == mock_embedding for r in results)
        assert service.get_token_usage() == 30

    @patch('core.embedding_service.OpenAI')
    def test_batch_generate_empty_list(self, mock_openai):
        """Test batch generation rejects empty list."""
        mock_openai.return_value = MagicMock()

        service = EmbeddingService(api_key="test-key")

        with pytest.raises(ValueError, match="empty list"):
            service.batch_generate([])

    @patch('core.embedding_service.OpenAI')
    def test_batch_generate_with_empty_text(self, mock_openai):
        """Test batch generation rejects empty strings."""
        mock_openai.return_value = MagicMock()

        service = EmbeddingService(api_key="test-key")

        with pytest.raises(ValueError, match="empty"):
            service.batch_generate(["text1", "", "text3"])

    @patch('core.embedding_service.OpenAI')
    def test_batch_generate_large_batch(self, mock_openai):
        """Test batch generation handles large batches correctly."""
        mock_embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding) for _ in range(50)]
        mock_response.usage = MagicMock(prompt_tokens=100)

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")
        texts = [f"text{i}" for i in range(50)]
        results = service.batch_generate(texts, max_batch_size=50)

        assert len(results) == 50
        assert mock_client.embeddings.create.call_count >= 1


class TestCaching:
    """Test embedding caching functionality."""

    @patch('core.embedding_service.OpenAI')
    def test_get_or_generate_cache_hit(self, mock_openai):
        """Test returning cached embedding."""
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        mock_response.usage = MagicMock(prompt_tokens=10)

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")

        # First call generates
        result1 = service.get_or_generate_embedding(1, "test content", "hash123")
        assert result1 == mock_embedding

        # Second call with same hash returns cached
        result2 = service.get_or_generate_embedding(1, "test content", "hash123")
        assert result2 == mock_embedding

        # Only one API call should have been made
        assert mock_client.embeddings.create.call_count == 1

    @patch('core.embedding_service.OpenAI')
    def test_get_or_generate_force_regenerate(self, mock_openai):
        """Test force regeneration ignores cache."""
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        mock_response.usage = MagicMock(prompt_tokens=10)

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")

        # First call
        service.get_or_generate_embedding(1, "test content", "hash123")

        # Force regenerate
        service.get_or_generate_embedding(1, "test content", "hash123", force_regenerate=True)

        # Both calls should hit the API
        assert mock_client.embeddings.create.call_count == 2

    @patch('core.embedding_service.OpenAI')
    def test_clear_cache(self, mock_openai):
        """Test clearing the cache."""
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        mock_response.usage = MagicMock(prompt_tokens=10)

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")

        # Generate and cache
        service.get_or_generate_embedding(1, "test content", "hash123")
        assert len(service._embedding_cache) > 0

        # Clear cache
        service.clear_cache()
        assert len(service._embedding_cache) == 0


class TestCostEstimation:
    """Test cost estimation functionality."""

    @patch('core.embedding_service.OpenAI')
    def test_estimate_cost(self, mock_openai):
        """Test cost estimation calculation."""
        mock_openai.return_value = MagicMock()

        service = EmbeddingService(api_key="test-key")

        # 1M tokens should cost $0.00002 (text-embedding-3-small pricing)
        cost = service.estimate_cost(1_000_000)
        assert cost == pytest.approx(0.00002, abs=0.000001)

        # 100k tokens should cost $0.000002
        cost = service.estimate_cost(100_000)
        assert cost == pytest.approx(0.000002, abs=0.0000001)

    @patch('core.embedding_service.OpenAI')
    def test_estimate_tokens(self, mock_openai):
        """Test token estimation."""
        mock_openai.return_value = MagicMock()

        service = EmbeddingService(api_key="test-key")

        # Rough estimate: 1000 chars ≈ 100 tokens
        tokens = service.estimate_tokens("a" * 1000)
        assert tokens > 0

        # Empty or very small text should estimate at least 1 token
        tokens = service.estimate_tokens("")
        assert tokens >= 1

    @patch('core.embedding_service.OpenAI')
    def test_token_usage_tracking(self, mock_openai):
        """Test token usage accumulation."""
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        mock_response.usage = MagicMock(prompt_tokens=10)

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test-key")

        assert service.get_token_usage() == 0

        service.generate_embedding("text1")
        assert service.get_token_usage() == 10

        service.generate_embedding("text2")
        assert service.get_token_usage() == 20

        service.reset_token_usage()
        assert service.get_token_usage() == 0


class TestMetadataManagement:
    """Test embedding metadata management."""

    @patch('core.embedding_service.OpenAI')
    def test_update_metadata(self, mock_openai):
        """Test metadata update functionality."""
        mock_openai.return_value = MagicMock()
        mock_supabase = MagicMock()
        mock_supabase.table().select().execute.return_value = MagicMock(data=[])

        service = EmbeddingService(api_key="test-key")

        # Should not raise
        service.update_metadata(
            mock_supabase,
            total_sections=100,
            embedded_sections=95,
            total_tokens=50000
        )

        # Verify supabase was called
        assert mock_supabase.table.called

    @patch('core.embedding_service.OpenAI')
    def test_get_metadata(self, mock_openai):
        """Test metadata retrieval."""
        mock_openai.return_value = MagicMock()
        mock_supabase = MagicMock()
        mock_metadata = {
            "total_sections": 100,
            "embedded_sections": 95,
            "total_tokens_used": 50000,
            "estimated_cost_usd": 1.00
        }
        mock_supabase.table().select().execute.return_value = MagicMock(
            data=[mock_metadata]
        )

        service = EmbeddingService(api_key="test-key")
        result = service.get_metadata(mock_supabase)

        assert result == mock_metadata

    @patch('core.embedding_service.OpenAI')
    def test_get_metadata_empty(self, mock_openai):
        """Test metadata retrieval when none exists."""
        mock_openai.return_value = MagicMock()
        mock_supabase = MagicMock()
        mock_supabase.table().select().execute.return_value = MagicMock(data=[])

        service = EmbeddingService(api_key="test-key")
        result = service.get_metadata(mock_supabase)

        assert result is None
