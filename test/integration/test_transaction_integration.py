"""Integration tests for transaction safety in checkout/checkin operations."""
import os
import pytest
import tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
from core.checkout_manager import CheckoutManager
from core.supabase_store import SupabaseStore
from core.recomposer import Recomposer
from models import FileMetadata, Section, FileType


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_supabase_store():
    """Create mock SupabaseStore for integration testing."""
    store = MagicMock(spec=SupabaseStore)

    # Setup default behaviors
    store.checkout_file.return_value = str(uuid4())
    store.checkin_file.return_value = None
    store.get_checkout_info.return_value = None
    store.get_file_by_path.return_value = None
    store.list_files_by_prefix.return_value = []

    return store


class TestCheckoutTransactionIntegration:
    """End-to-end integration tests for checkout transaction safety."""

    def test_successful_single_file_checkout(self, mock_supabase_store, temp_dir):
        """Test complete successful checkout workflow for single file."""
        file_id = str(uuid4())

        # Setup: Mock file retrieval
        section = Section(
            level=1,
            title="Test Section",
            content="# Test Section\n\nTest content here.",
            line_start=1,
            line_end=3
        )
        metadata = FileMetadata(
            path="/skills/test.md",
            type=FileType.SKILL,
            frontmatter="name: test\nversion: 1.0",
            hash="abc123"
        )
        mock_supabase_store.get_file.return_value = (metadata, [section])

        manager = CheckoutManager(mock_supabase_store)
        target_path = temp_dir / "deployed" / "test.md"

        # Execute checkout
        result = manager.checkout_file(
            file_id=file_id,
            user="testuser",
            target_path=str(target_path)
        )

        # Verify file was deployed
        assert target_path.exists()
        content = target_path.read_text()
        assert "Test Section" in content
        assert "name: test" in content

        # Verify database was updated
        mock_supabase_store.checkout_file.assert_called_once_with(
            file_id=file_id,
            user="testuser",
            target_path=str(target_path),
            notes=""
        )

        assert result == str(target_path)

    def test_checkout_rollback_on_database_timeout(self, mock_supabase_store, temp_dir):
        """Test that checkout rolls back when database times out."""
        file_id = str(uuid4())

        # Setup: Mock file retrieval
        section = Section(
            level=1,
            title="Test",
            content="Content",
            line_start=1,
            line_end=2
        )
        metadata = FileMetadata(
            path="/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_supabase_store.get_file.return_value = (metadata, [section])

        # Mock database timeout
        mock_supabase_store.checkout_file.side_effect = TimeoutError("Database connection timeout")

        manager = CheckoutManager(mock_supabase_store)
        target_path = temp_dir / "test.md"

        # Execute checkout (should fail and rollback)
        with pytest.raises(IOError) as exc_info:
            manager.checkout_file(
                file_id=file_id,
                user="testuser",
                target_path=str(target_path)
            )

        # Verify file was rolled back
        assert not target_path.exists()
        assert "roll back" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()

        # Verify database was attempted
        mock_supabase_store.checkout_file.assert_called_once()

    def test_multi_file_plugin_checkout_rolls_back_completely(self, mock_supabase_store, temp_dir):
        """Test that multi-file plugin checkout rolls back all files on failure."""
        import json

        file_id = str(uuid4())

        # Setup: Plugin with 3 related files
        plugin_json = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "Test plugin"
        }
        plugin_content = json.dumps(plugin_json)

        mcp_json = {"mcpServers": {"server1": {"command": "node"}}}
        mcp_content = json.dumps(mcp_json)

        hooks_json = {"pre-commit": {"description": "Pre-commit hook"}}
        hooks_content = json.dumps(hooks_json)

        # Mock primary file
        section = Section(
            level=-1,
            title="plugin.json",
            content=plugin_content,
            line_start=1,
            line_end=len(plugin_content.splitlines())
        )
        metadata = FileMetadata(
            path="/plugins/test-plugin/plugin.json",
            type=FileType.PLUGIN,
            frontmatter=plugin_content,
            hash="plugin123"
        )
        mock_supabase_store.get_file.return_value = (metadata, [section])

        # Mock related files listing
        mock_supabase_store.list_files_by_prefix.return_value = [
            {"storage_path": "/plugins/test-plugin/plugin.json"},
            {"storage_path": "/plugins/test-plugin/test-plugin.mcp.json"},
            {"storage_path": "/plugins/test-plugin/hooks.json"},
        ]

        # Mock related file retrieval
        def mock_get_by_path(path):
            if "mcp.json" in path:
                return (
                    FileMetadata(path, FileType.CONFIG, mcp_content, "mcp123"),
                    []
                )
            elif "hooks.json" in path:
                return (
                    FileMetadata(path, FileType.HOOK, hooks_content, "hooks123"),
                    []
                )
            return None

        mock_supabase_store.get_file_by_path.side_effect = mock_get_by_path

        # Mock database failure
        mock_supabase_store.checkout_file.side_effect = Exception("Connection lost")

        manager = CheckoutManager(mock_supabase_store)
        target_dir = temp_dir / "plugins" / "test-plugin"
        target_path = target_dir / "plugin.json"

        # Execute checkout (should fail)
        with pytest.raises(IOError):
            manager.checkout_file(
                file_id=file_id,
                user="testuser",
                target_path=str(target_path)
            )

        # Verify ALL files were rolled back
        assert not target_path.exists(), "plugin.json should not exist"
        assert not (target_dir / "test-plugin.mcp.json").exists(), ".mcp.json should not exist"
        assert not (target_dir / "hooks.json").exists(), "hooks.json should not exist"

        # Verify no partial deployment
        if target_dir.exists():
            remaining = list(target_dir.iterdir())
            assert len(remaining) == 0, f"Found unexpected files: {[f.name for f in remaining]}"

    def test_checkout_with_nested_directories_rolls_back(self, mock_supabase_store, temp_dir):
        """Test rollback with deeply nested directory structure."""
        file_id = str(uuid4())

        # Setup simple file
        section = Section(
            level=1,
            title="Test",
            content="Content",
            line_start=1,
            line_end=2
        )
        metadata = FileMetadata(
            path="/deep/nested/path/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_supabase_store.get_file.return_value = (metadata, [section])
        mock_supabase_store.checkout_file.side_effect = Exception("DB error")

        manager = CheckoutManager(mock_supabase_store)
        target_path = temp_dir / "a" / "b" / "c" / "d" / "test.md"

        # Execute checkout (should fail)
        with pytest.raises(IOError):
            manager.checkout_file(
                file_id=file_id,
                user="testuser",
                target_path=str(target_path)
            )

        # Verify file and directories were cleaned up
        assert not target_path.exists()
        # Parent directories may or may not exist (best-effort cleanup)

    def test_checkin_after_successful_checkout(self, mock_supabase_store, temp_dir):
        """Test complete checkout -> checkin workflow."""
        file_id = str(uuid4())
        checkout_uuid = str(uuid4())

        # Setup: Mock file and checkout info
        section = Section(
            level=1,
            title="Test",
            content="Content",
            line_start=1,
            line_end=2
        )
        metadata = FileMetadata(
            path="/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_supabase_store.get_file.return_value = (metadata, [section])
        mock_supabase_store.checkout_file.return_value = checkout_uuid

        # Create file manually
        target_path = temp_dir / "test.md"
        target_path.write_text("# Test\n\nContent")

        manager = CheckoutManager(mock_supabase_store)

        # Checkout (success)
        deployed = manager.checkout_file(
            file_id=file_id,
            user="testuser",
            target_path=str(target_path)
        )
        assert deployed == str(target_path)

        # Mock checkout info for checkin
        mock_supabase_store.get_checkout_info.return_value = {
            "id": checkout_uuid,
            "target_path": str(target_path)
        }

        # Checkin
        manager.checkin(str(target_path))

        # Verify file deleted
        assert not target_path.exists()

        # Verify database updated
        mock_supabase_store.checkin_file.assert_called_once_with(checkout_uuid)

    def test_checkin_database_failure_leaves_file_deleted(self, mock_supabase_store, temp_dir):
        """Test that checkin database error still results in file deletion."""
        checkout_uuid = str(uuid4())

        # Create file manually
        target_path = temp_dir / "test.md"
        target_path.write_text("# Test")

        # Mock checkout info
        mock_supabase_store.get_checkout_info.return_value = {
            "id": checkout_uuid,
            "target_path": str(target_path)
        }

        # Mock database failure
        mock_supabase_store.checkin_file.side_effect = Exception("Database unavailable")

        manager = CheckoutManager(mock_supabase_store)

        # Checkin should fail but delete file
        with pytest.raises(IOError) as exc_info:
            manager.checkin(str(target_path))

        # File should be deleted despite database failure
        assert not target_path.exists()

        # Error should mention the issue
        assert "deleted" in str(exc_info.value).lower() or "database" in str(exc_info.value).lower()


class TestTransactionErrorRecovery:
    """Test error recovery and logging scenarios."""

    def test_invalid_file_id_no_filesystem_changes(self, mock_supabase_store, temp_dir):
        """Test that invalid file_id doesn't create any files."""
        mock_supabase_store.get_file.return_value = None

        manager = CheckoutManager(mock_supabase_store)
        target_path = temp_dir / "should_not_exist.md"

        with pytest.raises(ValueError):
            manager.checkout_file(
                file_id="invalid-uuid",
                user="testuser",
                target_path=str(target_path)
            )

        assert not target_path.exists()
        assert not temp_dir.exists() or not any(temp_dir.iterdir())

    def test_filesystem_write_error_before_database(self, mock_supabase_store, temp_dir):
        """Test filesystem write error prevents database call."""
        import pytest

        file_id = str(uuid4())

        # Setup mock file
        section = Section(
            level=1,
            title="Test",
            content="Content",
            line_start=1,
            line_end=2
        )
        metadata = FileMetadata(
            path="/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_supabase_store.get_file.return_value = (metadata, [section])

        manager = CheckoutManager(mock_supabase_store)

        # Create a file at target path (will block directory creation)
        target_path = temp_dir / "blocker"
        target_path.write_text("existing file")

        # Now try to checkout to a path that requires blocker to be a directory
        # This will fail because blocker exists as a file, not a directory
        actual_target = temp_dir / "blocker" / "subdir" / "file.md"

        with pytest.raises((IOError, OSError)):
            manager.checkout_file(
                file_id=file_id,
                user="testuser",
                target_path=str(actual_target)
            )

        # Database should not have been called
        mock_supabase_store.checkout_file.assert_not_called()

    def test_concurrent_checkout_same_file(self, mock_supabase_store, temp_dir):
        """Test handling of concurrent checkout attempts (simulated)."""
        file_id = str(uuid4())

        section = Section(
            level=1,
            title="Test",
            content="Content",
            line_start=1,
            line_end=2
        )
        metadata = FileMetadata(
            path="/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_supabase_store.get_file.return_value = (metadata, [section])

        # Simulate concurrent attempts by using same target
        manager = CheckoutManager(mock_supabase_store)
        target_path = temp_dir / "test.md"

        # First checkout succeeds
        result1 = manager.checkout_file(
            file_id=file_id,
            user="user1",
            target_path=str(target_path)
        )
        assert result1 == str(target_path)

        # Second checkout to same path would overwrite
        # (real concurrency would need locking, this tests idempotency)
        result2 = manager.checkout_file(
            file_id=file_id,
            user="user2",
            target_path=str(target_path)
        )
        assert result2 == str(target_path)

        # File should exist (last write wins)
        assert target_path.exists()

    def test_recovery_from_partial_deployment(self, mock_supabase_store, temp_dir):
        """Test manual recovery scenario from partial deployment."""
        import json

        # Simulate state where files exist but no checkout record
        target_dir = temp_dir / "plugins" / "test-plugin"
        target_dir.mkdir(parents=True)

        plugin_file = target_dir / "plugin.json"
        plugin_file.write_text(json.dumps({"name": "test"}))

        mcp_file = target_dir / "test.mcp.json"
        mcp_file.write_text(json.dumps({"mcpServers": {}}))

        # Mock returns no active checkout
        mock_supabase_store.get_checkout_info.return_value = None

        manager = CheckoutManager(mock_supabase_store)

        # Attempting checkin should fail gracefully
        with pytest.raises(ValueError):
            manager.checkin(str(plugin_file))

        # Files should still exist (no checkout record to verify deletion)
        assert plugin_file.exists()
