"""Tests for CheckoutManager file operations."""
import os
import pytest
import tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock, MagicMock
from core.checkout_manager import CheckoutManager
from core.supabase_store import SupabaseStore
from models import FileMetadata, Section, FileType


@pytest.fixture
def mock_store(mocker):
    """Mock SupabaseStore for testing."""
    store = MagicMock(spec=SupabaseStore)
    return store


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create temporary storage directory with test file."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    # Create a test file
    test_file = storage_dir / "test.md"
    test_file.write_text("# Test Content\n\nThis is a test file.")

    return storage_dir


class TestCheckoutFile:
    """Test checking out files to target paths."""

    def test_checkout_file_copies_to_target(self, mock_store, temp_storage_dir, tmp_path):
        """Test that checkout_file copies file from storage to target path."""
        test_file_id = str(uuid4())
        storage_path = str(temp_storage_dir / "test.md")
        target_dir = tmp_path / "target"

        # Mock store.get_file() to return file content
        section = Section(
            level=1,
            title="Test Content",
            content="# Test Content\n\nThis is a test file.",
            line_start=1,
            line_end=3
        )
        metadata = FileMetadata(
            path=storage_path,
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_store.get_file.return_value = (metadata, [section])

        # Mock checkout tracking
        checkout_uuid = str(uuid4())
        mock_store.checkout_file.return_value = checkout_uuid

        manager = CheckoutManager(mock_store)

        # Checkout file
        deployed_path = manager.checkout_file(
            file_id=test_file_id,
            user="joey",
            target_path=str(target_dir / "test" / "SKILL.md")
        )

        # Verify file was copied to target
        assert Path(deployed_path).exists()
        content = Path(deployed_path).read_text()
        assert "Test Content" in content

        # Verify checkout was recorded
        mock_store.checkout_file.assert_called_once()


class TestCheckin:
    """Test checking in files (removing from target)."""

    def test_checkin_removes_file_and_updates_db(self, mock_store, tmp_path):
        """Test that checkin removes file from target and updates database."""
        # Create a checked-out file
        target_file = tmp_path / "test" / "SKILL.md"
        target_file.parent.mkdir(parents=True)
        target_file.write_text("# Test Content")

        # Mock get_checkout_info to return checkout details
        checkout_uuid = str(uuid4())
        mock_store.get_checkout_info.return_value = {
            "id": checkout_uuid,
            "target_path": str(target_file)
        }

        manager = CheckoutManager(mock_store)

        # Checkin file
        manager.checkin(str(target_file))

        # Verify file was deleted
        assert not target_file.exists()

        # Verify checkout was marked as returned
        mock_store.checkin_file.assert_called_once_with(checkout_uuid)
