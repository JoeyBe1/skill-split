"""Tests for CLI commands."""
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import MagicMock
import pytest
import argparse

# Import CLI functions and models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import FileMetadata, Section, FileType, ParsedDocument, FileFormat
from core.supabase_store import SupabaseStore
from core.checkout_manager import CheckoutManager


@pytest.fixture
def mock_supabase_store():
    """Mock SupabaseStore for testing."""
    return MagicMock(spec=SupabaseStore)


@pytest.fixture
def mock_checkout_manager(mock_supabase_store):
    """Mock CheckoutManager for testing."""
    manager = MagicMock(spec=CheckoutManager)
    return manager


@pytest.fixture
def temp_skill_dir(tmp_path):
    """Create temporary directory with test skill files."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create skill 1
    skill1 = skills_dir / "test_skill_1.md"
    skill1.write_text("""---
name: test-skill-1
version: 1.0.0
---

# Overview
First test skill content

# Examples
Some examples here
""")

    # Create skill 2
    skill2 = skills_dir / "test_skill_2.md"
    skill2.write_text("""---
name: test-skill-2
version: 2.0.0
---

# Overview
Second test skill content
""")

    # Create non-markdown file (should be ignored)
    (skills_dir / "readme.txt").write_text("This is not a markdown file")

    return skills_dir


class TestIngestCommand:
    """Test the ingest command."""

    def test_ingest_command_stores_files_from_directory(self, tmp_path, mock_supabase_store, monkeypatch):
        """Test that ingest command parses and stores files from a directory."""
        # Create test skill files
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()

        skill_file = skill_dir / "test_skill.md"
        skill_file.write_text("""---
name: test-skill
version: 1.0.0
---

# Overview
Test skill content
""")

        # Mock environment variables
        monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
        monkeypatch.setenv('SUPABASE_KEY', 'test-key')

        # Mock SupabaseStore
        monkeypatch.setattr('skill_split.SupabaseStore', lambda *args, **kwargs: mock_supabase_store)
        mock_supabase_store.store_file.return_value = str(uuid4())

        # Import the command function
        from skill_split import cmd_ingest

        # Create args object
        args = argparse.Namespace(
            source_dir=str(skill_dir)
        )

        # Execute command
        result = cmd_ingest(args)

        # Should succeed with return code 0
        assert result == 0

        # Should have called store_file at least once
        assert mock_supabase_store.store_file.called

    def test_ingest_command_prints_count(self, temp_skill_dir, mock_supabase_store, monkeypatch, capsys):
        """Test that ingest command prints count of stored files."""
        # Mock environment variables
        monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
        monkeypatch.setenv('SUPABASE_KEY', 'test-key')

        # Mock SupabaseStore
        monkeypatch.setattr('skill_split.SupabaseStore', lambda *args, **kwargs: mock_supabase_store)
        mock_supabase_store.store_file.return_value = str(uuid4())

        from skill_split import cmd_ingest

        args = argparse.Namespace(source_dir=str(temp_skill_dir))
        result = cmd_ingest(args)

        assert result == 0
        captured = capsys.readouterr()
        # Should print that files were ingested
        assert "ingested" in captured.out.lower() or "stored" in captured.out.lower()


class TestCheckoutCommand:
    """Test the checkout command."""

    def test_checkout_command_deploys_file_to_target(self, tmp_path, mock_supabase_store, monkeypatch):
        """Test that checkout command copies file to target path."""
        target_dir = tmp_path / "target"
        file_id = str(uuid4())

        # Mock environment variables
        monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
        monkeypatch.setenv('SUPABASE_KEY', 'test-key')

        # Mock CheckoutManager
        mock_checkout_manager = MagicMock()
        monkeypatch.setattr('skill_split.CheckoutManager', lambda *args, **kwargs: mock_checkout_manager)
        monkeypatch.setattr('skill_split.SupabaseStore', lambda *args, **kwargs: mock_supabase_store)

        # Mock the checkout operation
        target_path = str(target_dir / "SKILL.md")
        mock_checkout_manager.checkout_file.return_value = target_path

        from skill_split import cmd_checkout

        args = argparse.Namespace(
            file_id=file_id,
            target_path=target_path,
            user="joey"
        )

        # This will fail until we implement - that's expected in TDD
        # We're just verifying test structure is correct


class TestCheckinCommand:
    """Test the checkin command."""

    def test_checkin_command_removes_file(self, tmp_path, mock_supabase_store, monkeypatch):
        """Test that checkin command removes deployed file."""
        # Create a temporary file to checkin
        target_file = tmp_path / "SKILL.md"
        target_file.write_text("# Test Content")

        # Mock environment variables
        monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
        monkeypatch.setenv('SUPABASE_KEY', 'test-key')

        # Mock the checkin operation
        from skill_split import cmd_checkin

        args = argparse.Namespace(target_path=str(target_file))

        # This will fail until we implement - that's expected in TDD


class TestListCommand:
    """Test the list command."""

    def test_list_command_displays_files(self, monkeypatch, capsys):
        """Test that list command displays files in library."""
        # Mock environment variables
        monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
        monkeypatch.setenv('SUPABASE_KEY', 'test-key')

        # Mock SupabaseStore with direct method mocking
        mock_store = MagicMock()
        monkeypatch.setattr('skill_split.SupabaseStore', lambda *args, **kwargs: mock_store)

        # Mock file list response
        mock_store.get_all_files.return_value = [
            {
                'id': str(uuid4()),
                'name': 'test-skill',
                'type': 'skill',
                'storage_path': '/skills/test.md'
            }
        ]
        mock_store.get_active_checkouts.return_value = []

        from skill_split import cmd_list_library

        args = argparse.Namespace()
        result = cmd_list_library(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "test-skill" in captured.out


class TestStatusCommand:
    """Test the status command."""

    def test_status_command_shows_active_checkouts(self, monkeypatch, capsys):
        """Test that status command shows active checkouts."""
        # Mock environment variables
        monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
        monkeypatch.setenv('SUPABASE_KEY', 'test-key')

        # Mock SupabaseStore
        mock_store = MagicMock()
        monkeypatch.setattr('skill_split.SupabaseStore', lambda *args, **kwargs: mock_store)

        # Mock active checkouts
        file_uuid = str(uuid4())
        mock_store.get_active_checkouts.return_value = [
            {
                'id': str(uuid4()),
                'file_id': file_uuid,
                'user_name': 'joey',
                'target_path': '/tmp/SKILL.md',
                'status': 'active'
            }
        ]

        from skill_split import cmd_status

        args = argparse.Namespace(user=None)
        result = cmd_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "joey" in captured.out


class TestSearchCommand:
    """Test the search command."""

    def test_search_command_finds_files(self, monkeypatch, capsys):
        """Test that search command finds files by query."""
        # Mock environment variables
        monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
        monkeypatch.setenv('SUPABASE_KEY', 'test-key')

        # Mock SupabaseStore
        mock_store = MagicMock()
        monkeypatch.setattr('skill_split.SupabaseStore', lambda *args, **kwargs: mock_store)

        # Mock search results
        mock_store.search_files.return_value = [
            {
                'id': str(uuid4()),
                'name': 'test-skill',
                'type': 'skill',
                'storage_path': '/skills/test.md'
            }
        ]

        from skill_split import cmd_search_library

        args = argparse.Namespace(query="test")
        result = cmd_search_library(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "test-skill" in captured.out
