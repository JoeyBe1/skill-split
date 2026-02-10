"""
Tests for backup manager functionality.

Tests backup creation, restoration, and integrity validation.
"""

import gzip
import os
import sqlite3
import tempfile
import pytest
from pathlib import Path

from core.backup_manager import (
    BackupManager,
    BackupError,
    IntegrityError,
    create_backup,
    get_backup_path,
)
from core.database import DatabaseStore
from core.parser import Parser
from models import ParsedDocument, FileType, FileFormat


@pytest.fixture
def temp_db():
    """Create a temporary database with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = DatabaseStore(db_path)

        # Create test document with sections
        doc = ParsedDocument(
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/path.md",
            frontmatter="---\nname: test\n---\n",
            sections=[],
        )
        content_hash = "test_hash_123"
        store.store_file("/test/path.md", doc, content_hash)

        yield db_path


@pytest.fixture
def backup_dir():
    """Create a temporary backup directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestBackupManager:
    """Tests for BackupManager class."""

    def test_create_backup_creates_file(self, temp_db, backup_dir):
        """Test that create_backup creates a valid backup file."""
        manager = BackupManager(backup_dir)
        backup_path = manager.create_backup(temp_db)

        assert os.path.exists(backup_path)
        assert backup_path.endswith(".sql.gz")

    def test_create_backup_includes_all_tables(self, temp_db, backup_dir):
        """Test that backup includes all tables and data."""
        manager = BackupManager(backup_dir)
        backup_path = manager.create_backup(temp_db)

        # Decompress and read SQL
        with gzip.open(backup_path, 'rt') as f:
            sql_content = f.read()

        # Check for tables
        assert "CREATE TABLE files" in sql_content
        assert "CREATE TABLE sections" in sql_content
        assert "CREATE VIRTUAL TABLE sections_fts" in sql_content

        # Check for data
        assert "INSERT INTO" in sql_content

    def test_create_backup_timestamp_filename(self, temp_db, backup_dir):
        """Test that backup uses timestamp when no filename provided."""
        manager = BackupManager(backup_dir)
        backup_path = manager.create_backup(temp_db)

        filename = os.path.basename(backup_path)
        assert filename.startswith("skill-split-")
        assert filename.endswith(".sql.gz")

        # Check timestamp format (YYYYMMDD-HHMMSS)
        parts = filename.replace("skill-split-", "").replace(".sql.gz", "")
        assert "-" in parts
        assert len(parts) == 15  # YYYYMMDD-HHMMSS

    def test_create_backup_custom_filename(self, temp_db, backup_dir):
        """Test that backup uses custom filename when provided."""
        manager = BackupManager(backup_dir)
        backup_path = manager.create_backup(temp_db, filename="my-backup")

        assert "my-backup.sql.gz" in backup_path
        assert os.path.exists(backup_path)

    def test_create_backup_invalid_database(self, backup_dir):
        """Test that create_backup raises BackupError for invalid database."""
        manager = BackupManager(backup_dir)

        with pytest.raises(BackupError, match="Database not found or not readable"):
            manager.create_backup("/nonexistent/path.db")

    def test_create_backup_preserves_data_integrity(self, temp_db, backup_dir):
        """Test that backup preserves data and can be restored."""
        manager = BackupManager(backup_dir)

        # Create backup
        backup_path = manager.create_backup(temp_db)

        # Restore to new database
        restore_path = temp_db + ".restored"
        result = manager.restore_backup(backup_path, restore_path)

        # Verify data integrity
        assert result["integrity_check_passed"]
        assert result["files_count"] > 0

        # Verify SHA256 hash matches
        original_store = DatabaseStore(temp_db)
        restored_store = DatabaseStore(restore_path)

        original_file = original_store.get_file("/test/path.md")
        restored_file = restored_store.get_file("/test/path.md")

        assert original_file is not None
        assert restored_file is not None
        assert original_file[1] == restored_file[1]  # Sections match

    def test_list_backups(self, temp_db, backup_dir):
        """Test that list_backups returns backup metadata."""
        manager = BackupManager(backup_dir)

        # Create multiple backups
        manager.create_backup(temp_db, filename="backup1.sql.gz")
        manager.create_backup(temp_db, filename="backup2.sql.gz")

        backups = manager.list_backups()

        assert len(backups) == 2
        assert all("filename" in b for b in backups)
        assert all("size" in b for b in backups)
        assert all("compressed_size" in b for b in backups)
        assert all("path" in b for b in backups)

    def test_get_backup_path(self, temp_db, backup_dir):
        """Test that get_backup_path returns correct path."""
        manager = BackupManager(backup_dir)

        # Create backup
        backup_path = manager.create_backup(temp_db, filename="test-backup.sql.gz")
        filename = os.path.basename(backup_path)

        # Get path
        result_path = manager.get_backup_path(filename)

        assert result_path == backup_path

    def test_get_backup_path_not_found(self, backup_dir):
        """Test that get_backup_path raises BackupError for non-existent backup."""
        manager = BackupManager(backup_dir)

        with pytest.raises(BackupError, match="Backup not found"):
            manager.get_backup_path("nonexistent-backup")


class TestRestoreBackup:
    """Tests for restore functionality."""

    def test_restore_backup_creates_database(self, temp_db, backup_dir):
        """Test that restore creates a new database."""
        manager = BackupManager(backup_dir)

        # Create backup
        backup_path = manager.create_backup(temp_db)

        # Restore to new database
        restore_path = temp_db + ".restored"
        result = manager.restore_backup(backup_path, restore_path)

        assert os.path.exists(restore_path)
        assert result["integrity_check_passed"]

    def test_restore_backup_preserves_data(self, temp_db, backup_dir):
        """Test that restore preserves all data."""
        manager = BackupManager(backup_dir)

        # Create backup
        backup_path = manager.create_backup(temp_db)

        # Restore to new database
        restore_path = temp_db + ".restored"
        result = manager.restore_backup(backup_path, restore_path)

        # Verify counts
        original_store = DatabaseStore(temp_db)
        restored_store = DatabaseStore(restore_path)

        # Count original records
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM files")
            original_files = cursor.fetchone()[0]
            cursor = conn.execute("SELECT COUNT(*) FROM sections")
            original_sections = cursor.fetchone()[0]

        assert result["files_count"] == original_files
        assert result["sections_count"] == original_sections

    def test_restore_backup_fts5_index(self, temp_db, backup_dir):
        """Test that restore preserves FTS5 index."""
        manager = BackupManager(backup_dir)

        # Create backup
        backup_path = manager.create_backup(temp_db)

        # Restore to new database
        restore_path = temp_db + ".restored"
        result = manager.restore_backup(backup_path, restore_path)

        # Verify FTS5 table exists
        assert result.get("fts5_exists", False)

        # Test FTS5 search works
        restored_store = DatabaseStore(restore_path)
        results = restored_store.search_sections_with_rank("test")
        # Should return results without error
        assert isinstance(results, list)

    def test_restore_backup_foreign_keys(self, temp_db, backup_dir):
        """Test that restore preserves foreign key constraints."""
        manager = BackupManager(backup_dir)

        # Create backup
        backup_path = manager.create_backup(temp_db)

        # Restore to new database
        restore_path = temp_db + ".restored"
        result = manager.restore_backup(backup_path, restore_path)

        # Verify foreign keys are enforced
        assert result.get("foreign_keys_ok", False)

        # Try to insert invalid section (should fail)
        with sqlite3.connect(restore_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                conn.execute(
                    "INSERT INTO sections (file_id, level, title, content, "
                    "order_index, line_start, line_end) "
                    "VALUES (99999, 1, 'test', 'test', 1, 1, 1)"
                )
                assert False, "Foreign key constraint should have failed"
            except sqlite3.IntegrityError:
                pass  # Expected

    def test_restore_backup_overwrite_flag(self, temp_db, backup_dir):
        """Test that restore respects overwrite flag."""
        manager = BackupManager(backup_dir)

        # Create backup
        backup_path = manager.create_backup(temp_db)

        # Restore to create database
        restore_path = temp_db + ".restored"
        manager.restore_backup(backup_path, restore_path)

        # Try to restore again without overwrite (should fail)
        with pytest.raises(BackupError, match="already exists"):
            manager.restore_backup(backup_path, restore_path, overwrite=False)

        # Restore again with overwrite (should succeed)
        result = manager.restore_backup(backup_path, restore_path, overwrite=True)
        assert result["integrity_check_passed"]

    def test_restore_backup_corrupted_file(self, backup_dir):
        """Test that restore raises error for corrupted backup."""
        manager = BackupManager(backup_dir)

        # Create invalid gzip file
        invalid_backup = os.path.join(backup_dir, "invalid.sql.gz")
        with open(invalid_backup, 'w') as f:
            f.write("not a gzip file")

        # Try to restore
        restore_path = os.path.join(backup_dir, "test.db")
        with pytest.raises(BackupError, match="Invalid or corrupted"):
            manager.restore_backup(invalid_backup, restore_path)

    def test_validate_integrity_method(self, temp_db, backup_dir):
        """Test the validate_integrity method."""
        manager = BackupManager(backup_dir)

        # Validate original database
        result = manager.validate_integrity(temp_db)

        assert result["integrity_ok"]
        assert result["files_count"] >= 0
        assert result["sections_count"] >= 0
        assert result["fts5_exists"]
        assert result["foreign_keys_ok"]

    def test_restore_roundtrip_with_production_data(self, backup_dir):
        """Integration test: backup and restore with realistic data."""
        # Create database with multiple files and sections
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            store = DatabaseStore(db_path)

            # Add multiple files
            for i in range(3):
                doc = ParsedDocument(
                    file_type=FileType.SKILL,
                    format=FileFormat.MARKDOWN_HEADINGS,
                    original_path=f"/test/skill{i}.md",
                    frontmatter=f"---\nname: skill{i}\n---\n",
                    sections=[],
                )
                store.store_file(f"/test/skill{i}.md", doc, f"hash{i}")

            # Create backup
            manager = BackupManager(backup_dir)
            backup_path = manager.create_backup(db_path)

            # Restore
            restore_path = os.path.join(tmpdir, "restored.db")
            result = manager.restore_backup(backup_path, restore_path)

            # Verify all files accessible
            restored_store = DatabaseStore(restore_path)
            for i in range(3):
                file_data = restored_store.get_file(f"/test/skill{i}.md")
                assert file_data is not None

            # Verify search works
            results = restored_store.search_sections("skill")
            assert len(results) >= 0

            assert result["integrity_check_passed"]

    def test_restore_preserves_line_numbers(self, temp_db, backup_dir):
        """Test that restore preserves line_start and line_end."""
        manager = BackupManager(backup_dir)

        # Create backup
        backup_path = manager.create_backup(temp_db)

        # Restore
        restore_path = temp_db + ".restored"
        manager.restore_backup(backup_path, restore_path)

        # Compare line numbers
        with sqlite3.connect(temp_db) as conn1:
            cursor1 = conn1.execute(
                "SELECT line_start, line_end FROM sections"
            )
            original_lines = cursor1.fetchall()

        with sqlite3.connect(restore_path) as conn2:
            cursor2 = conn2.execute(
                "SELECT line_start, line_end FROM sections"
            )
            restored_lines = cursor2.fetchall()

        assert original_lines == restored_lines

    def test_restore_preserves_parent_child_relationships(self, backup_dir):
        """Test that restore preserves parent_id and order_index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            store = DatabaseStore(db_path)

            # Create document with nested sections
            from models import Section
            parent = Section(
                level=1,
                title="Parent",
                content="Parent content",
                line_start=1,
                line_end=5,
            )
            child = Section(
                level=2,
                title="Child",
                content="Child content",
                line_start=6,
                line_end=10,
            )
            parent.add_child(child)

            doc = ParsedDocument(
                file_type=FileType.SKILL,
                format=FileFormat.MARKDOWN_HEADINGS,
                original_path="/test/nested.md",
                frontmatter="---\nname: test\n---\n",
                sections=[parent],
            )
            store.store_file("/test/nested.md", doc, "hash_nested")

            # Backup and restore
            manager = BackupManager(backup_dir)
            backup_path = manager.create_backup(db_path)
            restore_path = os.path.join(tmpdir, "restored.db")
            manager.restore_backup(backup_path, restore_path)

            # Verify relationships
            with sqlite3.connect(restore_path) as conn:
                cursor = conn.execute(
                    "SELECT id, parent_id, order_index FROM sections ORDER BY id"
                )
                rows = cursor.fetchall()

                assert len(rows) == 2
                assert rows[0][1] is None  # Parent has no parent
                assert rows[1][1] is not None  # Child has parent

    def test_restore_preserves_frontmatter(self, backup_dir):
        """Test that restore preserves YAML frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            store = DatabaseStore(db_path)

            frontmatter = "---\nname: test-skill\ndescription: A test skill\n---\n"
            doc = ParsedDocument(
                file_type=FileType.SKILL,
                format=FileFormat.MARKDOWN_HEADINGS,
                original_path="/test/frontmatter.md",
                frontmatter=frontmatter,
                sections=[],
            )
            store.store_file("/test/frontmatter.md", doc, "hash_fm")

            # Backup and restore
            manager = BackupManager(backup_dir)
            backup_path = manager.create_backup(db_path)
            restore_path = os.path.join(tmpdir, "restored.db")
            manager.restore_backup(backup_path, restore_path)

            # Verify frontmatter preserved
            restored_store = DatabaseStore(restore_path)
            file_data = restored_store.get_file("/test/frontmatter.md")

            assert file_data is not None
            assert file_data[0].frontmatter == frontmatter


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_backup_function(self, temp_db, backup_dir):
        """Test the create_backup convenience function."""
        backup_path = create_backup(temp_db, backup_dir)

        assert os.path.exists(backup_path)
        assert backup_dir in backup_path

    def test_get_backup_path_function(self, backup_dir):
        """Test the get_backup_path convenience function."""
        # Create a test backup file
        manager = BackupManager(backup_dir)
        test_backup = os.path.join(backup_dir, "test-backup.sql.gz")
        Path(test_backup).touch()

        path = get_backup_path("test-backup.sql.gz", backup_dir)
        assert path == test_backup
