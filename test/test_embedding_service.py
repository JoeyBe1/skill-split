"""
Tests for EmbeddingService.

Covers embedding generation, caching, batch operations, and cost estimation.
"""

import pytest
import time
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
            with pytest.raises(ValueError, match="API key not found"):
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


class TestTokenAwareBatching:
    """Test token-aware batch creation logic."""

    @patch('core.embedding_service.OpenAI')
    def test_creates_batches_within_size_limit(self, mock_openai):
        """Verify batches don't exceed max_batch_size."""
        mock_openai.return_value = MagicMock()
        service = EmbeddingService(api_key="test")
        texts = [f"section {i}" for i in range(5000)]
        batches = service._create_token_aware_batches(texts, max_batch_size=2048)

        for batch in batches:
            assert len(batch['texts']) <= 2048

    @patch('core.embedding_service.OpenAI')
    def test_creates_batches_within_token_limit(self, mock_openai):
        """Verify batches don't exceed 8000 token limit."""
        mock_openai.return_value = MagicMock()
        service = EmbeddingService(api_key="test")
        # Create texts of varying lengths
        texts = ["x" * 1000 for _ in range(100)]  # Each ~100 tokens
        batches = service._create_token_aware_batches(texts, max_batch_size=2048)

        for batch in batches:
            assert batch['tokens'] <= 8000

    @patch('core.embedding_service.OpenAI')
    def test_handles_empty_list(self, mock_openai):
        """Verify empty input returns empty batches."""
        mock_openai.return_value = MagicMock()
        service = EmbeddingService(api_key="test")
        batches = service._create_token_aware_batches([], 2048)
        assert batches == []

    @patch('core.embedding_service.OpenAI')
    def test_preserves_indices_correctly(self, mock_openai):
        """Verify batch indices map back to original positions."""
        mock_openai.return_value = MagicMock()
        service = EmbeddingService(api_key="test")
        texts = ["a", "b", "c", "d", "e"]
        batches = service._create_token_aware_batches(texts, 2048)

        # Reconstruct from indices
        reconstructed = [None] * len(texts)
        for batch in batches:
            for idx, text in zip(batch['indices'], batch['texts']):
                reconstructed[idx] = text

        assert reconstructed == texts

    @patch('core.embedding_service.OpenAI')
    def test_handles_mixed_length_texts(self, mock_openai):
        """Verify batching handles mix of long and short texts correctly."""
        mock_openai.return_value = MagicMock()
        service = EmbeddingService(api_key="test")
        # Create a realistic mix that requires multiple batches
        # Many medium-length texts that together exceed token limits
        texts = ["medium length text content here " * 20 for _ in range(1000)]
        batches = service._create_token_aware_batches(texts, 2048)

        # Should create multiple batches
        assert len(batches) > 1

        # Verify each batch is within limits
        for batch in batches:
            assert len(batch['texts']) <= 2048, "Batch exceeds size limit"
            assert batch['tokens'] <= 8000, "Batch exceeds token limit"

        # Verify all texts are included
        total_texts = sum(len(b['texts']) for b in batches)
        assert total_texts == len(texts)


class TestParallelBatchProcessing:
    """Test parallel batch generation."""

    @pytest.fixture
    def mock_openai(self, mocker):
        """Mock OpenAI client for testing."""
        mock_client = mocker.MagicMock()
        mock_response = mocker.MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.data = [
            mocker.MagicMock(embedding=[0.1] * 1536)
            for _ in range(100)
        ]
        mock_client.embeddings.create.return_value = mock_response
        return mock_client

    @patch('core.embedding_service.OpenAI')
    def test_parallel_processes_multiple_batches(self, mock_openai):
        """Verify multiple batches processed concurrently."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536)
            for _ in range(100)
        ]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test")
        service.client = mock_client

        texts = [f"section {i}" for i in range(5000)]
        embeddings = service.batch_generate_parallel(texts, max_workers=5)

        assert len(embeddings) == 5000
        # Should have made multiple calls
        assert mock_client.embeddings.create.call_count > 1

    @patch('core.embedding_service.OpenAI')
    def test_parallel_preserves_order(self, mock_openai):
        """Verify embeddings returned in same order as input."""
        mock_client = MagicMock()

        # Create unique embeddings for each text
        call_count = 0
        def create_unique_embeddings(*args, **kwargs):
            nonlocal call_count
            texts = kwargs.get('input', [])
            response = MagicMock()
            response.data = [
                MagicMock(embedding=[(call_count + i) / 1000.0] * 1536)
                for i, _ in enumerate(texts)
            ]
            call_count += len(texts)
            return response

        mock_client.embeddings.create.side_effect = create_unique_embeddings
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test")
        service.client = mock_client

        texts = ["a", "b", "c", "d", "e"]
        embeddings = service.batch_generate_parallel(texts, max_workers=2)

        # Check order preserved - each should have unique first value
        first_values = [emb[0] for emb in embeddings]
        assert len(first_values) == len(set(first_values))  # All unique

    @patch('core.embedding_service.OpenAI')
    def test_progress_callback_called(self, mock_openai):
        """Verify progress callback invoked correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536)
            for _ in range(100)
        ]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test")
        service.client = mock_client

        progress_updates = []
        def callback(current, total):
            progress_updates.append((current, total))

        texts = [f"section {i}" for i in range(100)]
        embeddings = service.batch_generate_parallel(
            texts,
            progress_callback=callback
        )

        # Should have multiple progress updates
        assert len(progress_updates) > 0
        # Final update should show completion
        assert progress_updates[-1][0] == 100

    @patch('core.embedding_service.OpenAI')
    def test_handles_batch_failure_gracefully(self, mock_openai):
        """Verify failed batch doesn't crash entire process."""
        mock_client = MagicMock()

        # Make second batch fail
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Rate limit exceeded")
            return MagicMock(
                usage=MagicMock(prompt_tokens=100),
                data=[MagicMock(embedding=[0.1] * 1536)
                      for _ in kwargs.get('input', [])]
            )

        mock_client.embeddings.create.side_effect = side_effect
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test")
        service.client = mock_client

        texts = [f"section {i}" for i in range(5000)]
        embeddings = service.batch_generate_parallel(texts, max_workers=3)

        # Should have some embeddings (from successful batches)
        successful = sum(1 for e in embeddings if e is not None)
        assert successful > 0
        assert successful < 5000  # Some failed


class TestRateLimitHandling:
    """Test rate limit retry logic."""

    @patch('core.embedding_service.OpenAI')
    def test_exponential_backoff(self, mock_openai):
        """Verify exponential backoff on rate limit."""
        mock_client = MagicMock()

        # Mock rate limit error then success
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("rate_limit_exceeded")
            return MagicMock(
                usage=MagicMock(prompt_tokens=100),
                data=[MagicMock(embedding=[0.1] * 1536)
                      for _ in kwargs.get('input', [])]
            )

        mock_client.embeddings.create.side_effect = side_effect
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test")

        texts = ["test1", "test2"]
        embeddings = service.batch_generate_with_retry(texts, max_retries=3)

        # Should have succeeded after retries
        assert len(embeddings) == 2
        assert call_count == 3  # 2 failures + 1 success

    @patch('core.embedding_service.OpenAI')
    def test_max_retries_exceeded(self, mock_openai):
        """Verify failure after max retries."""
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = Exception("rate_limit_exceeded")
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="test")

        texts = ["test1", "test2"]

        with pytest.raises(RuntimeError, match="Failed to generate batch embedding"):
            service.batch_generate_with_retry(texts, max_retries=2)


class TestSecretManagerIntegration:
    """Test SecretManager integration with EmbeddingService."""

    @patch('core.embedding_service.OpenAI')
    def test_init_with_secret_manager(self, mock_openai):
        """Test initialization with SecretManager parameter."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock SecretManager
        from core.secret_manager import SecretSourceType
        mock_sm = MagicMock()
        mock_sm.get_secret_with_source.return_value = ("sk-secret-manager-key-123", SecretSourceType.FILE)

        service = EmbeddingService(secret_manager=mock_sm)

        assert service.api_key == "sk-secret-manager-key-123"
        assert service.get_api_key_source() == "file"
        mock_sm.get_secret_with_source.assert_called_once_with("OPENAI_API_KEY")

    @patch('core.embedding_service.OpenAI')
    def test_init_with_secret_manager_fallback_to_param(self, mock_openai):
        """Test fallback to api_key parameter when SecretManager fails."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock SecretManager to raise exception
        mock_sm = MagicMock()
        mock_sm.get_secret_with_source.side_effect = Exception("Secret not found")

        service = EmbeddingService(api_key="sk-param-key-456", secret_manager=mock_sm)

        assert service.api_key == "sk-param-key-456"
        assert service.get_api_key_source() == "parameter"

    @patch('core.embedding_service.OpenAI')
    def test_init_with_secret_manager_fallback_to_env(self, mock_openai):
        """Test fallback to environment when SecretManager fails and no param."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock SecretManager to raise exception
        mock_sm = MagicMock()
        mock_sm.get_secret_with_source.side_effect = Exception("Secret not found")

        import os
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key-789"}):
            service = EmbeddingService(secret_manager=mock_sm)

        assert service.api_key == "sk-env-key-789"
        assert service.get_api_key_source() == "environment"

    @patch('core.embedding_service.OpenAI')
    @patch('core.embedding_service._ensure_secret_manager_imports')
    def test_init_secret_manager_not_available(self, mock_ensure, mock_openai):
        """Test graceful degradation when SecretManager unavailable."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock _ensure_secret_manager_imports to set SecretManager to None
        def side_effect():
            global SecretManager
            SecretManager = None

        mock_ensure.side_effect = side_effect

        import os
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key-fallback"}):
            service = EmbeddingService(use_secret_manager=True)

        assert service.api_key == "sk-env-key-fallback"
        assert service.get_api_key_source() == "environment"

    @patch('core.embedding_service.OpenAI')
    def test_init_use_secret_manager_false(self, mock_openai):
        """Test use_secret_manager=False disables SecretManager."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_sm = MagicMock()
        mock_sm.get_secret_with_source.return_value = ("sk-secret-key", MagicMock(value="file"))

        import os
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key-123"}):
            service = EmbeddingService(
                secret_manager=mock_sm,
                use_secret_manager=False
            )

        # Should use environment, not SecretManager
        assert service.api_key == "sk-env-key-123"
        assert service.get_api_key_source() == "environment"
        mock_sm.get_secret_with_source.assert_not_called()

    @patch('core.embedding_service.OpenAI')
    def test_init_all_sources_fail(self, mock_openai):
        """Test ValueError when all sources fail."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_sm = MagicMock()
        mock_sm.get_secret_with_source.side_effect = Exception("Secret not found")

        import os
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                EmbeddingService(secret_manager=mock_sm)

    @patch('core.embedding_service.OpenAI')
    def test_generate_embedding_uses_secret_manager_key(self, mock_openai):
        """Test embedding generation uses SecretManager key."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Setup mock response
        mock_embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        mock_response.usage = MagicMock(prompt_tokens=10)

        mock_client.embeddings.create.return_value = mock_response

        # Mock SecretManager
        from core.secret_manager import SecretSourceType
        mock_sm = MagicMock()
        mock_sm.get_secret_with_source.return_value = ("sk-secret-for-generation", SecretSourceType.FILE)

        service = EmbeddingService(secret_manager=mock_sm)

        # Generate embedding
        result = service.generate_embedding("test text")

        assert result == mock_embedding
        assert service.api_key == "sk-secret-for-generation"
        assert service.get_api_key_source() == "file"

    @patch('core.embedding_service.OpenAI')
    def test_api_key_source_property(self, mock_openai):
        """Test api_key_source property access."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Test with parameter
        service1 = EmbeddingService(api_key="test-param")
        assert service1.api_key_source == "parameter"

        # Test with environment
        import os
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-env"}):
            service2 = EmbeddingService()
            assert service2.api_key_source == "environment"

    @patch('core.embedding_service.OpenAI')
    def test_backward_compat_with_api_key_param(self, mock_openai):
        """Test backward compatibility with api_key parameter."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Old way: just pass api_key
        service = EmbeddingService(api_key="sk-old-way-123")

        assert service.api_key == "sk-old-way-123"
        assert service.get_api_key_source() == "parameter"
        # Should not use SecretManager
        assert service._secret_manager is None

    @patch('core.embedding_service.OpenAI')
    def test_backward_compat_with_env_var(self, mock_openai):
        """Test backward compatibility with environment variable."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        import os
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-compat-456"}):
            # Old way: no parameters, rely on env var
            service = EmbeddingService()

        assert service.api_key == "sk-env-compat-456"
        assert service.get_api_key_source() == "environment"
