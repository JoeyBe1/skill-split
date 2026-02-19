"""Integration tests for batch embedding functionality."""

import pytest
pytest.importorskip("openai")
import tempfile
import os
import sqlite3
from core.database import DatabaseStore
from core.embedding_service import EmbeddingService
from core.parser import Parser
from models import FileType, FileFormat


class TestBatchEmbeddingIntegration:
    """Test batch embedding with real database operations."""

    @pytest.fixture
    def db_store(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            store = DatabaseStore(f.name)
            yield store
            os.unlink(f.name)

    @pytest.fixture
    def mock_openai(self, mocker):
        """Mock OpenAI client for testing."""
        mock_client = mocker.MagicMock()

        def create_embedding(*args, **kwargs):
            texts = kwargs.get('input', [])
            response = mocker.MagicMock()
            response.usage.prompt_tokens = len(texts) * 10
            response.data = [
                mocker.MagicMock(embedding=[0.1] * 1536)
                for _ in texts
            ]
            return response

        mock_client.embeddings.create.side_effect = create_embedding
        return mock_client

    def get_sections_with_ids(self, db_store: DatabaseStore, file_id: int) -> list:
        """Helper to get sections with their IDs from database."""
        import hashlib
        with sqlite3.connect(db_store.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, title, content FROM sections WHERE file_id = ?",
                (file_id,)
            )
            result = []
            for row in cursor.fetchall():
                content = row['content']
                # Calculate content hash for consistency
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                result.append({
                    'id': row['id'],
                    'content': content,
                    'content_hash': content_hash,
                    'title': row['title']
                })
            return result

    def test_batch_embed_stored_sections(self, db_store, mock_openai):
        """Test batch embedding of sections stored in database."""
        # Create and store sections
        parser = Parser()
        content = "# Test\n\n" + "\n## Section {}\nContent".format("{}") * 50
        doc = parser.parse('test.md', content, FileType.SKILL, FileFormat.MARKDOWN_HEADINGS)

        file_id = db_store.store_file('test.md', doc, 'hash123')

        # Get sections from database with IDs
        section_dicts = self.get_sections_with_ids(db_store, file_id)

        # Filter out sections with empty/whitespace-only content
        # (batch_generate will reject empty strings)
        valid_sections = [s for s in section_dicts if s['content'].strip()]

        # Batch generate embeddings
        service = EmbeddingService(api_key="test")
        service.client = mock_openai

        embeddings = db_store.batch_generate_embeddings(
            valid_sections,
            service,
            force_regenerate=True
        )

        # Verify embeddings generated for valid sections
        assert len(embeddings) == len(valid_sections)

    def test_batch_handles_empty_sections(self, db_store, mock_openai):
        """Test batch with empty section list."""
        service = EmbeddingService(api_key="test")
        service.client = mock_openai

        embeddings = db_store.batch_generate_embeddings([], service)

        assert embeddings == {}

    def test_batch_generates_correct_embedding_count(self, db_store, mock_openai):
        """Test batch generates embeddings for all sections."""
        parser = Parser()
        # Create document with known number of sections
        content = """
# Root

## Section 1
Content 1

## Section 2
Content 2

## Section 3
Content 3
"""
        doc = parser.parse('test.md', content, FileType.SKILL, FileFormat.MARKDOWN_HEADINGS)
        file_id = db_store.store_file('test.md', doc, 'hash123')

        # Get sections with IDs from database
        section_dicts = self.get_sections_with_ids(db_store, file_id)

        # Filter out sections with empty/whitespace-only content
        valid_sections = [s for s in section_dicts if s['content'].strip()]

        service = EmbeddingService(api_key="test")
        service.client = mock_openai

        embeddings = db_store.batch_generate_embeddings(
            valid_sections,
            service,
            force_regenerate=True
        )

        # Should have embeddings for all valid sections
        assert len(embeddings) == len(valid_sections)

    def test_parallel_batch_with_progress(self, db_store, mock_openai):
        """Test parallel batch generation with progress tracking."""
        parser = Parser()
        content = "# Test\n\n" + "\n## Section {}\nContent".format("{}") * 20
        doc = parser.parse('test.md', content, FileType.SKILL, FileFormat.MARKDOWN_HEADINGS)
        file_id = db_store.store_file('test.md', doc, 'hash123')

        # Get sections with IDs from database
        section_dicts = self.get_sections_with_ids(db_store, file_id)

        # Filter out sections with empty/whitespace-only content
        valid_sections = [s for s in section_dicts if s['content'].strip()]

        service = EmbeddingService(api_key="test")
        service.client = mock_openai

        # Track progress
        progress_calls = []
        def track_progress(current, total):
            progress_calls.append((current, total))

        # Generate embeddings directly with progress callback
        texts = [s['content'] for s in valid_sections]
        embeddings = service.batch_generate_parallel(
            texts,
            max_workers=3,
            progress_callback=track_progress
        )

        # Verify progress was tracked
        assert len(progress_calls) > 0
        assert progress_calls[-1][0] == len(texts)  # Final count matches
        assert len(embeddings) == len(texts)
