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
def mock_store():
    """Mock SupabaseStore for testing."""
    return MagicMock(spec=SupabaseStore)


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

    def test_checkout_preserves_or_strips_headings_by_flag(self, mock_store, tmp_path):
        """Default preserves markdown headings; opt-out strips them."""
        test_file_id = str(uuid4())
        target_dir = tmp_path / "target"

        # Simulate parser output: headings are NOT in section.content
        child = Section(
            level=2,
            title="Child",
            content="Child body.\n",
            line_start=4,
            line_end=5,
        )
        parent = Section(
            level=1,
            title="Parent",
            content="Intro line.\n\n",
            line_start=1,
            line_end=5,
            children=[child],
        )
        metadata = FileMetadata(
            path="/tmp/source.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123",
        )
        mock_store.get_file.return_value = (metadata, [parent])
        mock_store.checkout_file.return_value = str(uuid4())

        manager = CheckoutManager(mock_store)

        default_out = target_dir / "default.md"
        strip_out = target_dir / "strip.md"

        manager.checkout_file(
            file_id=test_file_id,
            user="joey",
            target_path=str(default_out),
        )
        manager.checkout_file(
            file_id=test_file_id,
            user="joey",
            target_path=str(strip_out),
            preserve_headings=False,
        )

        assert default_out.read_text() == "# Parent\nIntro line.\n\n## Child\nChild body.\n"
        assert strip_out.read_text() == "Intro line.\n\nChild body.\n"


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


class TestCheckoutPluginDeployment:
    """Test checking out plugins deploys all related files."""

    def test_checkout_plugin_deploys_related_files(self, mock_store, tmp_path):
        """Test that checking out a plugin deploys plugin.json, .mcp.json, and hooks.json."""
        import json
        from handlers.plugin_handler import PluginHandler

        # Create temporary plugin directory with all related files
        plugin_dir = tmp_path / "storage" / "test-plugin"
        plugin_dir.mkdir(parents=True)

        # Create plugin.json
        plugin_path = plugin_dir / "plugin.json"
        plugin_data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "mcpServers": {"server1": {}},
            "hooks": ["pre-commit"]
        }
        plugin_path.write_text(json.dumps(plugin_data, indent=2))

        # Create .mcp.json
        mcp_path = plugin_dir / "test-plugin.mcp.json"
        mcp_data = {
            "mcpServers": {
                "server1": {"command": "node", "args": ["server.js"]}
            }
        }
        mcp_path.write_text(json.dumps(mcp_data, indent=2))

        # Create hooks.json
        hooks_path = plugin_dir / "hooks.json"
        hooks_data = {
            "pre-commit": {"description": "Runs before commit"}
        }
        hooks_path.write_text(json.dumps(hooks_data, indent=2))

        # Mock store.get_file() to return plugin content
        plugin_content = plugin_path.read_text()
        section = Section(
            level=-1,
            title="plugin.json",
            content=plugin_content,
            line_start=1,
            line_end=len(plugin_content.splitlines())
        )
        metadata = FileMetadata(
            path=str(plugin_path),
            type=FileType.PLUGIN,
            frontmatter=plugin_content,
            hash="abc123"
        )
        mock_store.get_file.return_value = (metadata, [section])

        # Mock Supabase related file listing and retrieval
        mock_store.list_files_by_prefix.return_value = [
            {"storage_path": str(plugin_path)},
            {"storage_path": str(mcp_path)},
            {"storage_path": str(hooks_path)},
        ]

        mcp_metadata = FileMetadata(
            path=str(mcp_path),
            type=FileType.CONFIG,
            frontmatter=mcp_path.read_text(),
            hash="mcp123"
        )
        hooks_metadata = FileMetadata(
            path=str(hooks_path),
            type=FileType.HOOK,
            frontmatter=hooks_path.read_text(),
            hash="hooks123"
        )
        mock_store.get_file_by_path.side_effect = lambda p: {
            str(mcp_path): (mcp_metadata, []),
            str(hooks_path): (hooks_metadata, []),
        }.get(p)

        # Mock checkout tracking
        checkout_uuid = str(uuid4())
        mock_store.checkout_file.return_value = checkout_uuid

        # Create CheckoutManager
        manager = CheckoutManager(mock_store)

        # Checkout plugin to target directory
        target_dir = tmp_path / "target" / "plugins" / "test-plugin"
        deployed_path = manager.checkout_file(
            file_id="test-plugin-id",
            user="joey",
            target_path=str(target_dir / "plugin.json")
        )

        # Verify all 3 files were deployed
        assert Path(deployed_path).exists(), "plugin.json not deployed"
        assert (target_dir / "test-plugin.mcp.json").exists(), ".mcp.json not deployed"
        assert (target_dir / "hooks.json").exists(), "hooks.json not deployed"

        # Verify plugin.json content
        deployed_plugin = json.loads(Path(deployed_path).read_text())
        assert deployed_plugin["name"] == "test-plugin"

        # Verify .mcp.json content
        deployed_mcp = json.loads((target_dir / "test-plugin.mcp.json").read_text())
        assert "server1" in deployed_mcp["mcpServers"]

        # Verify hooks.json content
        deployed_hooks = json.loads((target_dir / "hooks.json").read_text())
        assert "pre-commit" in deployed_hooks


class TestTransactionSafety:
    """Test transaction safety and rollback behavior."""

    def test_checkout_rolls_back_on_database_failure(self, mock_store, tmp_path):
        """Test that filesystem writes are rolled back when database checkout fails."""
        from uuid import uuid4
        import json

        # Setup: Mock successful file retrieval
        test_file_id = str(uuid4())
        section = Section(
            level=1,
            title="Test Content",
            content="# Test Content\n\nThis is a test file.",
            line_start=1,
            line_end=3
        )
        metadata = FileMetadata(
            path="/test/path/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_store.get_file.return_value = (metadata, [section])

        # Mock database failure during checkout
        mock_store.checkout_file.side_effect = Exception("Database connection lost")

        manager = CheckoutManager(mock_store)
        target_dir = tmp_path / "target"
        target_path = target_dir / "test" / "SKILL.md"

        # Attempt checkout (should fail and rollback)
        with pytest.raises(IOError) as exc_info:
            manager.checkout_file(
                file_id=test_file_id,
                user="joey",
                target_path=str(target_path)
            )

        # Verify error message mentions rollback or failure
        assert "roll back" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()

        # Verify file was NOT deployed (rolled back)
        assert not target_path.exists(), "File should not exist after failed checkout"

        # Verify database was called
        mock_store.checkout_file.assert_called_once()

    def test_multi_file_checkout_rolls_back_all_files(self, mock_store, tmp_path):
        """Test that all related files are rolled back on database failure."""
        from uuid import uuid4
        import json

        test_file_id = str(uuid4())

        # Setup: Plugin with related files
        plugin_dir = tmp_path / "storage" / "test-plugin"
        plugin_dir.mkdir(parents=True)

        plugin_path = plugin_dir / "plugin.json"
        plugin_data = {"name": "test-plugin", "version": "1.0.0"}
        plugin_content = json.dumps(plugin_data)
        plugin_path.write_text(plugin_content)

        mcp_path = plugin_dir / "test-plugin.mcp.json"
        mcp_data = {"mcpServers": {"server1": {}}}
        mcp_path.write_text(json.dumps(mcp_data))

        hooks_path = plugin_dir / "hooks.json"
        hooks_data = {"pre-commit": {}}
        hooks_path.write_text(json.dumps(hooks_data))

        # Mock primary file
        section = Section(
            level=-1,
            title="plugin.json",
            content=plugin_content,
            line_start=1,
            line_end=len(plugin_content.splitlines())
        )
        metadata = FileMetadata(
            path=str(plugin_path),
            type=FileType.PLUGIN,
            frontmatter=plugin_content,
            hash="abc123"
        )
        mock_store.get_file.return_value = (metadata, [section])

        # Mock related files
        mock_store.list_files_by_prefix.return_value = [
            {"storage_path": str(plugin_path)},
            {"storage_path": str(mcp_path)},
            {"storage_path": str(hooks_path)},
        ]

        mcp_metadata = FileMetadata(
            path=str(mcp_path),
            type=FileType.CONFIG,
            frontmatter=json.dumps(mcp_data),
            hash="mcp123"
        )
        hooks_metadata = FileMetadata(
            path=str(hooks_path),
            type=FileType.HOOK,
            frontmatter=json.dumps(hooks_data),
            hash="hooks123"
        )
        mock_store.get_file_by_path.side_effect = lambda p: {
            str(mcp_path): (mcp_metadata, []),
            str(hooks_path): (hooks_metadata, []),
        }.get(p)

        # Mock database failure
        mock_store.checkout_file.side_effect = Exception("Database timeout")

        manager = CheckoutManager(mock_store)
        target_dir = tmp_path / "target" / "plugins" / "test-plugin"
        target_path = target_dir / "plugin.json"

        # Attempt checkout
        with pytest.raises(IOError):
            manager.checkout_file(
                file_id=test_file_id,
                user="joey",
                target_path=str(target_path)
            )

        # Verify ALL files were rolled back
        assert not target_path.exists(), "plugin.json should not exist"
        assert not (target_dir / "test-plugin.mcp.json").exists(), ".mcp.json should not exist"
        assert not (target_dir / "hooks.json").exists(), "hooks.json should not exist"

    def test_checkin_succeeds_after_filesystem_delete(self, mock_store, tmp_path):
        """Test that checkin handles database errors after successful file deletion."""
        from uuid import uuid4

        # Create a checked-out file
        target_file = tmp_path / "test" / "SKILL.md"
        target_file.parent.mkdir(parents=True)
        target_file.write_text("# Test Content")

        checkout_uuid = str(uuid4())
        mock_store.get_checkout_info.return_value = {
            "id": checkout_uuid,
            "target_path": str(target_file)
        }

        # Mock database failure
        mock_store.checkin_file.side_effect = Exception("Database connection lost")

        manager = CheckoutManager(mock_store)

        # Checkin should fail but file should be deleted
        with pytest.raises(IOError) as exc_info:
            manager.checkin(str(target_file))

        # Verify file was deleted despite database failure
        assert not target_file.exists(), "File should be deleted even if database fails"

        # Verify error message mentions the inconsistency
        assert "deleted" in str(exc_info.value).lower() or "database" in str(exc_info.value).lower()

    def test_checkout_with_invalid_file_id_raises_error(self, mock_store, tmp_path):
        """Test that checkout with invalid file_id raises ValueError without filesystem changes."""
        mock_store.get_file.return_value = None

        manager = CheckoutManager(mock_store)
        target_dir = tmp_path / "target"

        with pytest.raises(ValueError) as exc_info:
            manager.checkout_file(
                file_id="invalid-id",
                user="joey",
                target_path=str(target_dir / "test.md")
            )

        assert "not found" in str(exc_info.value).lower()

        # Verify no files were created
        assert not target_dir.exists(), "No files should be created for invalid file_id"

    def test_rollback_handles_permission_errors(self, mock_store, tmp_path):
        """Test that rollback continues even if some files cannot be deleted."""
        from uuid import uuid4
        import json

        test_file_id = str(uuid4())

        # Setup mock file
        section = Section(
            level=1,
            title="Test",
            content="Content",
            line_start=1,
            line_end=2
        )
        metadata = FileMetadata(
            path="/test/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_store.get_file.return_value = (metadata, [section])
        mock_store.checkout_file.side_effect = Exception("DB error")

        manager = CheckoutManager(mock_store)
        target_path = tmp_path / "target" / "test.md"

        # Mock unlink to raise permission error
        original_unlink = Path.unlink
        call_count = [0]

        def mock_unlink_self(self):
            call_count[0] += 1
            if call_count[0] == 1:
                raise PermissionError("Permission denied")
            return original_unlink(self)

        Path.unlink = mock_unlink_self

        try:
            # Should attempt rollback and handle permission error
            with pytest.raises(IOError):
                manager.checkout_file(
                    file_id=test_file_id,
                    user="joey",
                    target_path=str(target_path)
                )
        finally:
            Path.unlink = original_unlink

        # Verify database was still called
        mock_store.checkout_file.assert_called_once()

    def test_successful_checkout_records_in_database(self, mock_store, tmp_path):
        """Test that successful checkout records in database and deploys files."""
        from uuid import uuid4

        test_file_id = str(uuid4())

        section = Section(
            level=1,
            title="Test",
            content="# Test",
            line_start=1,
            line_end=2
        )
        metadata = FileMetadata(
            path="/test/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_store.get_file.return_value = (metadata, [section])

        checkout_uuid = str(uuid4())
        mock_store.checkout_file.return_value = checkout_uuid

        manager = CheckoutManager(mock_store)
        target_path = tmp_path / "target" / "test.md"

        result = manager.checkout_file(
            file_id=test_file_id,
            user="joey",
            target_path=str(target_path)
        )

        # Verify file was deployed
        assert target_path.exists()
        assert result == str(target_path)

        # Verify database was updated
        mock_store.checkout_file.assert_called_once_with(
            file_id=test_file_id,
            user="joey",
            target_path=str(target_path),
            notes=""
        )


class TestTransactionEdgeCases:
    """Test edge cases and boundary conditions for transaction safety."""

    def test_checkout_empty_target_path(self, mock_store, tmp_path):
        """Test checkout with empty target path uses default behavior."""
        from uuid import uuid4

        test_file_id = str(uuid4())
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
        mock_store.get_file.return_value = (metadata, [section])

        manager = CheckoutManager(mock_store)

        # Empty target path should still work (uses current directory)
        with pytest.raises((ValueError, IOError)):
            # May fail due to invalid path, but shouldn't crash
            manager.checkout_file(
                file_id=test_file_id,
                user="testuser",
                target_path=""
            )

    def test_checkout_with_symlink_target(self, mock_store, tmp_path):
        """Test checkout behavior with symlink in target path."""
        from uuid import uuid4
        import os

        test_file_id = str(uuid4())
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
        mock_store.get_file.return_value = (metadata, [section])

        # Create symlink
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link_dir = tmp_path / "link"
        try:
            link_dir.symlink_to(real_dir)
        except OSError:
            # Symlinks may not be supported on this system
            pytest.skip("Symlinks not supported")

        manager = CheckoutManager(mock_store)
        target_path = link_dir / "test.md"

        # Should work through symlink
        result = manager.checkout_file(
            file_id=test_file_id,
            user="testuser",
            target_path=str(target_path)
        )

        assert Path(result).exists()

    def test_checkin_nonexistent_checkout(self, mock_store, tmp_path):
        """Test checkin for file with no checkout record."""
        mock_store.get_checkout_info.return_value = None

        manager = CheckoutManager(mock_store)

        with pytest.raises(ValueError) as exc_info:
            manager.checkin(str(tmp_path / "nonexistent.md"))

        assert "no active checkout" in str(exc_info.value).lower()

    def test_checkout_with_large_content(self, mock_store, tmp_path):
        """Test checkout with large file content."""
        from uuid import uuid4

        test_file_id = str(uuid4())

        # Create large content (1MB)
        large_content = "# Large File\n\n" + "Content\n" * 25000

        section = Section(
            level=1,
            title="Large File",
            content=large_content,
            line_start=1,
            line_end=25002
        )
        metadata = FileMetadata(
            path="/large.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="large123"
        )
        mock_store.get_file.return_value = (metadata, [section])

        manager = CheckoutManager(mock_store)
        target_path = tmp_path / "large.md"

        result = manager.checkout_file(
            file_id=test_file_id,
            user="testuser",
            target_path=str(target_path)
        )

        # Verify large file was written
        assert target_path.exists()
        assert target_path.stat().st_size > 100_000  # > 100KB
        assert result == str(target_path)

    def test_rollback_with_open_file_handles(self, mock_store, tmp_path):
        """Test rollback when file has open handles (Windows scenario)."""
        from uuid import uuid4

        test_file_id = str(uuid4())
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
        mock_store.get_file.return_value = (metadata, [section])
        mock_store.checkout_file.side_effect = Exception("DB error")

        manager = CheckoutManager(mock_store)
        target_path = tmp_path / "test.md"

        # On Windows, open file handles prevent deletion
        # This test verifies we handle it gracefully
        with pytest.raises(IOError):
            manager.checkout_file(
                file_id=test_file_id,
                user="testuser",
                target_path=str(target_path)
            )

        # File should be rolled back (or best effort)
        # May still exist on Windows if handle held

    def test_checkout_creates_parent_directories(self, mock_store, tmp_path):
        """Test that checkout creates parent directories as needed."""
        from uuid import uuid4

        test_file_id = str(uuid4())
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
        mock_store.get_file.return_value = (metadata, [section])

        manager = CheckoutManager(mock_store)

        # Deep nested path that doesn't exist
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e" / "test.md"

        result = manager.checkout_file(
            file_id=test_file_id,
            user="testuser",
            target_path=str(deep_path)
        )

        # Verify all parent directories were created
        assert deep_path.exists()
        assert deep_path.parent.exists()

    def test_multiple_checkouts_same_target(self, mock_store, tmp_path):
        """Test multiple checkouts to same target path (idempotency)."""
        from uuid import uuid4

        file_id = str(uuid4())
        section = Section(
            level=1,
            title="Test",
            content="Content v1",
            line_start=1,
            line_end=2
        )
        metadata = FileMetadata(
            path="/test.md",
            type=FileType.SKILL,
            frontmatter=None,
            hash="abc123"
        )
        mock_store.get_file.return_value = (metadata, [section])

        manager = CheckoutManager(mock_store)
        target_path = tmp_path / "test.md"

        # First checkout
        result1 = manager.checkout_file(
            file_id=file_id,
            user="user1",
            target_path=str(target_path)
        )

        # Second checkout to same path (overwrites)
        section2 = Section(
            level=1,
            title="Test",
            content="Content v2",
            line_start=1,
            line_end=2
        )
        mock_store.get_file.return_value = (metadata, [section2])

        result2 = manager.checkout_file(
            file_id=file_id,
            user="user2",
            target_path=str(target_path)
        )

        # Both should succeed, file overwritten
        assert target_path.exists()
        content = target_path.read_text()
        assert "v2" in content
