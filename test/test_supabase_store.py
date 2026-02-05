"""Tests for Supabase database store."""
import os
import pytest
from uuid import UUID, uuid4
from unittest.mock import MagicMock, Mock
from core.supabase_store import SupabaseStore
from models import ParsedDocument, FileType, FileFormat


@pytest.fixture
def mock_supabase_client(mocker):
    """Mock Supabase client for testing."""
    mock_client = MagicMock()
    mocker.patch('core.supabase_store.create_client', return_value=mock_client)
    return mock_client


class TestSupabaseConnection:
    """Test Supabase client connection."""

    def test_can_connect_to_supabase(self, mock_supabase_client):
        """Test that SupabaseStore initializes with valid credentials."""
        url = "https://test.supabase.co"
        key = "test-key"

        store = SupabaseStore(url=url, key=key)

        assert store.client is not None
        assert store.url == url
        assert store.key == key


class TestStoreFile:
    """Test storing files in Supabase."""

    def test_store_file_returns_uuid(self, mock_supabase_client):
        """Test that store_file returns a valid UUID for a simple file."""
        # Setup mock to return a UUID
        test_uuid = str(uuid4())
        mock_result = Mock()
        mock_result.data = [{"id": test_uuid}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_result

        store = SupabaseStore(url="https://test.supabase.co", key="test-key")

        # Create simple document with no sections
        doc = ParsedDocument(
            frontmatter="name: test\nversion: 1.0.0",
            sections=[],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/path.md"
        )

        file_id = store.store_file(
            storage_path="/hidden/storage/test.md",
            name="test",
            doc=doc,
            content_hash="abc123hash"
        )

        # Should return a valid UUID string
        assert file_id is not None
        assert isinstance(file_id, str)
        # Verify it's a valid UUID by converting it
        uuid_obj = UUID(file_id)
        assert str(uuid_obj) == file_id
        assert file_id == test_uuid

        # Verify the insert was called with correct data
        mock_supabase_client.table.assert_called_once_with("files")
        mock_supabase_client.table.return_value.insert.assert_called_once()

    def test_store_file_with_hierarchical_sections(self, mock_supabase_client):
        """Test that store_file stores sections with correct parent_id relationships."""
        from models import Section

        # Setup mocks
        test_file_uuid = str(uuid4())
        test_section_uuid_1 = str(uuid4())
        test_section_uuid_2 = str(uuid4())

        # Mock file insert
        mock_file_result = Mock()
        mock_file_result.data = [{"id": test_file_uuid}]

        # Mock section inserts
        mock_section_result_1 = Mock()
        mock_section_result_1.data = [{"id": test_section_uuid_1}]
        mock_section_result_2 = Mock()
        mock_section_result_2.data = [{"id": test_section_uuid_2}]

        # Setup table mock to return different results
        table_mock = mock_supabase_client.table.return_value
        insert_mock = table_mock.insert.return_value
        insert_mock.execute.side_effect = [
            mock_file_result,  # First call for file
            mock_section_result_1,  # Second call for parent section
            mock_section_result_2,  # Third call for child section
        ]

        store = SupabaseStore(url="https://test.supabase.co", key="test-key")

        # Create document with hierarchical sections
        child_section = Section(
            level=2,
            title="Subsection",
            content="Child content",
            line_start=5,
            line_end=7
        )
        parent_section = Section(
            level=1,
            title="Main Section",
            content="Parent content",
            line_start=1,
            line_end=7
        )
        parent_section.add_child(child_section)

        doc = ParsedDocument(
            frontmatter="name: test\nversion: 1.0.0",
            sections=[parent_section],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/path.md"
        )

        file_id = store.store_file(
            storage_path="/hidden/storage/test.md",
            name="test",
            doc=doc,
            content_hash="abc123hash"
        )

        # Verify file was stored
        assert file_id == test_file_uuid

        # Verify sections were stored (3 calls: 1 file + 2 sections)
        assert mock_supabase_client.table.call_count == 3


class TestGetFile:
    """Test retrieving files from Supabase."""

    def test_get_file_returns_metadata_and_sections(self, mock_supabase_client):
        """Test that get_file retrieves file metadata and reconstructs section tree."""
        test_file_uuid = str(uuid4())
        parent_section_uuid = str(uuid4())
        child_section_uuid = str(uuid4())

        # Mock file select
        mock_file_result = Mock()
        mock_file_result.data = [{
            "id": test_file_uuid,
            "name": "test",
            "storage_path": "/hidden/storage/test.md",
            "type": "skill",
            "frontmatter": "name: test\nversion: 1.0.0",
            "hash": "abc123hash"
        }]

        # Mock sections select (parent + child)
        mock_sections_result = Mock()
        mock_sections_result.data = [
            {
                "id": parent_section_uuid,
                "file_id": test_file_uuid,
                "parent_id": None,
                "level": 1,
                "title": "Main Section",
                "content": "Parent content",
                "order_index": 0,
                "line_start": 1,
                "line_end": 7
            },
            {
                "id": child_section_uuid,
                "file_id": test_file_uuid,
                "parent_id": parent_section_uuid,
                "level": 2,
                "title": "Subsection",
                "content": "Child content",
                "order_index": 0,
                "line_start": 5,
                "line_end": 7
            }
        ]

        # Setup mocks
        table_mock = mock_supabase_client.table.return_value
        select_mock = table_mock.select.return_value
        eq_mock = select_mock.eq.return_value
        eq_mock.execute.side_effect = [mock_file_result, mock_sections_result]

        store = SupabaseStore(url="https://test.supabase.co", key="test-key")

        result = store.get_file(test_file_uuid)

        # Should return tuple of (FileMetadata, List[Section])
        assert result is not None
        metadata, sections = result

        # Verify metadata
        assert metadata.path == "/hidden/storage/test.md"
        assert metadata.type == FileType.SKILL
        assert metadata.hash == "abc123hash"

        # Verify sections
        assert len(sections) == 1  # One top-level section
        assert sections[0].title == "Main Section"
        assert len(sections[0].children) == 1  # One child
        assert sections[0].children[0].title == "Subsection"


class TestCheckoutTracking:
    """Test checkout tracking operations."""

    def test_checkout_file_returns_checkout_id(self, mock_supabase_client):
        """Test that checkout_file records a checkout and returns checkout UUID."""
        test_file_uuid = str(uuid4())
        test_checkout_uuid = str(uuid4())

        # Mock checkout insert
        mock_result = Mock()
        mock_result.data = [{"id": test_checkout_uuid}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_result

        store = SupabaseStore(url="https://test.supabase.co", key="test-key")

        checkout_id = store.checkout_file(
            file_id=test_file_uuid,
            user="joey",
            target_path="/home/.claude/skills/test/",
            notes="Testing checkout"
        )

        # Should return UUID
        assert checkout_id == test_checkout_uuid
        assert isinstance(UUID(checkout_id), UUID)

        # Verify insert was called with correct data
        mock_supabase_client.table.assert_called_with("checkouts")
        call_args = mock_supabase_client.table.return_value.insert.call_args[0][0]
        assert call_args["file_id"] == test_file_uuid
        assert call_args["user_name"] == "joey"
        assert call_args["target_path"] == "/home/.claude/skills/test/"
        assert call_args["status"] == "active"

    def test_checkin_file_updates_status(self, mock_supabase_client):
        """Test that checkin_file marks checkout as returned."""
        test_checkout_uuid = str(uuid4())

        # Mock update
        mock_result = Mock()
        mock_result.data = [{"id": test_checkout_uuid, "status": "returned"}]

        update_mock = mock_supabase_client.table.return_value.update.return_value
        eq_mock = update_mock.eq.return_value
        eq_mock.execute.return_value = mock_result

        store = SupabaseStore(url="https://test.supabase.co", key="test-key")

        store.checkin_file(checkout_id=test_checkout_uuid)

        # Verify update was called
        mock_supabase_client.table.assert_called_with("checkouts")
        mock_supabase_client.table.return_value.update.assert_called_once()
        # Should update status to 'returned' and set checked_in_at

    def test_get_active_checkouts_returns_list(self, mock_supabase_client):
        """Test that get_active_checkouts retrieves active checkouts."""
        # Mock select with filter
        mock_result = Mock()
        mock_result.data = [
            {
                "id": str(uuid4()),
                "user_name": "joey",
                "target_path": "/home/.claude/skills/test/",
                "file_id": str(uuid4()),
                "status": "active"
            },
            {
                "id": str(uuid4()),
                "user_name": "joey",
                "target_path": "/home/.claude/skills/another/",
                "file_id": str(uuid4()),
                "status": "active"
            }
        ]

        # Mock the chain: table().select().eq().eq().execute()
        table_mock = mock_supabase_client.table.return_value
        select_mock = table_mock.select.return_value
        eq1_mock = select_mock.eq.return_value  # First eq (status)
        eq2_mock = eq1_mock.eq.return_value  # Second eq (user)
        eq2_mock.execute.return_value = mock_result

        store = SupabaseStore(url="https://test.supabase.co", key="test-key")

        checkouts = store.get_active_checkouts(user="joey")

        # Should return list of checkouts
        assert len(checkouts) == 2
        assert all(c["status"] == "active" for c in checkouts)
        assert all(c["user_name"] == "joey" for c in checkouts)
