"""
Tests for sync verification script.

Tests the verify_sync.py script functionality including:
- Local database loading
- Supabase connection
- File comparison logic
- Report formatting
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the sync verifier
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.verify_sync import SyncVerifier, SyncReport, load_env_config, format_report


class TestSyncReport:
    """Test SyncReport data class and properties."""

    def test_is_synced_when_all_match(self):
        """Test is_synced returns True when everything matches."""
        report = SyncReport(
            local_count=5,
            supabase_count=5,
            matching_files=5,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=[],
            errors=[],
        )
        assert report.is_synced

    def test_is_synced_false_with_mismatches(self):
        """Test is_synced returns False when there are hash mismatches."""
        report = SyncReport(
            local_count=5,
            supabase_count=5,
            matching_files=3,
            hash_mismatches=["file1.md", "file2.md"],
            missing_in_local=[],
            missing_in_supabase=[],
            errors=[],
        )
        assert not report.is_synced

    def test_is_synced_false_with_missing_files(self):
        """Test is_synced returns False when files are missing."""
        report = SyncReport(
            local_count=5,
            supabase_count=6,
            matching_files=5,
            hash_mismatches=[],
            missing_in_local=["extra_file.md"],
            missing_in_supabase=[],
            errors=[],
        )
        assert not report.is_synced

    def test_is_synced_false_with_errors(self):
        """Test is_synced returns False when there are errors."""
        report = SyncReport(
            local_count=0,
            supabase_count=0,
            matching_files=0,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=[],
            errors=["Connection failed"],
        )
        assert not report.is_synced

    def test_sync_percentage_calculation(self):
        """Test sync percentage is calculated correctly."""
        report = SyncReport(
            local_count=10,
            supabase_count=10,
            matching_files=8,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=["file1.md", "file2.md"],
            errors=[],
        )
        assert report.get_sync_percentage() == 80.0

    def test_sync_percentage_zero_files(self):
        """Test sync percentage with zero files."""
        report = SyncReport(
            local_count=0,
            supabase_count=0,
            matching_files=0,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=[],
            errors=[],
        )
        assert report.get_sync_percentage() == 0.0


class TestSyncVerifierLocalFiles:
    """Test local file loading from SQLite."""

    def test_load_local_files_success(self):
        """Test loading files from local database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")

            # Create test database
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE files (
                        id INTEGER PRIMARY KEY,
                        path TEXT UNIQUE,
                        type TEXT,
                        hash TEXT
                    )
                    """
                )
                conn.execute(
                    "INSERT INTO files VALUES (1, 'test/file1.md', 'skill', 'hash1')"
                )
                conn.execute(
                    "INSERT INTO files VALUES (2, 'test/file2.md', 'command', 'hash2')"
                )
                conn.commit()

            # Load files
            verifier = SyncVerifier(db_path, "http://example.com", "fake_key")
            files = verifier._load_local_files()

            assert files is not None
            assert len(files) == 2
            assert "test/file1.md" in files
            assert files["test/file1.md"].hash == "hash1"
            assert files["test/file2.md"].file_type == "command"

    def test_load_local_files_nonexistent_db(self):
        """Test loading from non-existent database."""
        verifier = SyncVerifier("/nonexistent/db.db", "http://example.com", "fake_key")
        files = verifier._load_local_files()

        assert files is None
        assert "Local database not found" in verifier.report.errors[0]

    def test_load_local_files_empty_database(self):
        """Test loading from empty database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")

            # Create empty database
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE files (
                        id INTEGER PRIMARY KEY,
                        path TEXT UNIQUE,
                        type TEXT,
                        hash TEXT
                    )
                    """
                )
                conn.commit()

            # Load files
            verifier = SyncVerifier(db_path, "http://example.com", "fake_key")
            files = verifier._load_local_files()

            assert files is not None
            assert len(files) == 0


class TestSyncVerifierComparison:
    """Test file comparison logic."""

    def test_compare_identical_files(self):
        """Test comparison when files are identical."""
        local_files = {
            "file1.md": MagicMock(path="file1.md", hash="hash1", file_type="skill"),
            "file2.md": MagicMock(path="file2.md", hash="hash2", file_type="command"),
        }
        supabase_files = {
            "file1.md": MagicMock(path="file1.md", hash="hash1", file_type="skill"),
            "file2.md": MagicMock(path="file2.md", hash="hash2", file_type="command"),
        }

        verifier = SyncVerifier("", "http://example.com", "fake_key")
        verifier._compare_files(local_files, supabase_files)

        assert verifier.report.matching_files == 2
        assert len(verifier.report.hash_mismatches) == 0
        assert len(verifier.report.missing_in_local) == 0
        assert len(verifier.report.missing_in_supabase) == 0

    def test_compare_hash_mismatch(self):
        """Test comparison detects hash mismatches."""
        local_files = {
            "file1.md": MagicMock(path="file1.md", hash="hash1_local", file_type="skill"),
        }
        supabase_files = {
            "file1.md": MagicMock(
                path="file1.md", hash="hash1_remote", file_type="skill"
            ),
        }

        verifier = SyncVerifier("", "http://example.com", "fake_key")
        verifier._compare_files(local_files, supabase_files)

        assert verifier.report.matching_files == 0
        assert "file1.md" in verifier.report.hash_mismatches

    def test_compare_missing_in_supabase(self):
        """Test comparison detects files missing in Supabase."""
        local_files = {
            "file1.md": MagicMock(path="file1.md", hash="hash1", file_type="skill"),
            "file2.md": MagicMock(path="file2.md", hash="hash2", file_type="command"),
        }
        supabase_files = {
            "file1.md": MagicMock(path="file1.md", hash="hash1", file_type="skill"),
        }

        verifier = SyncVerifier("", "http://example.com", "fake_key")
        verifier._compare_files(local_files, supabase_files)

        assert verifier.report.matching_files == 1
        assert "file2.md" in verifier.report.missing_in_supabase

    def test_compare_missing_in_local(self):
        """Test comparison detects files missing in local."""
        local_files = {
            "file1.md": MagicMock(path="file1.md", hash="hash1", file_type="skill"),
        }
        supabase_files = {
            "file1.md": MagicMock(path="file1.md", hash="hash1", file_type="skill"),
            "file2.md": MagicMock(path="file2.md", hash="hash2", file_type="command"),
        }

        verifier = SyncVerifier("", "http://example.com", "fake_key")
        verifier._compare_files(local_files, supabase_files)

        assert verifier.report.matching_files == 1
        assert "file2.md" in verifier.report.missing_in_local


class TestReportFormatting:
    """Test report formatting functions."""

    def test_format_synced_report(self):
        """Test formatting a fully synced report."""
        report = SyncReport(
            local_count=5,
            supabase_count=5,
            matching_files=5,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=[],
            errors=[],
        )

        output = format_report(report)
        assert "✓ FULLY SYNCED" in output
        assert "Local SQLite:     5" in output
        assert "Supabase:         5" in output

    def test_format_out_of_sync_report(self):
        """Test formatting an out-of-sync report."""
        report = SyncReport(
            local_count=5,
            supabase_count=6,
            matching_files=4,
            hash_mismatches=["file1.md"],
            missing_in_local=["file2.md"],
            missing_in_supabase=[],
            errors=[],
        )

        output = format_report(report)
        assert "✗ OUT OF SYNC" in output
        assert "Hash Mismatches (1)" in output
        assert "Missing in Local (1)" in output

    def test_format_summary_only_synced(self):
        """Test summary-only format for synced database."""
        report = SyncReport(
            local_count=10,
            supabase_count=10,
            matching_files=10,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=[],
            errors=[],
        )

        output = format_report(report, summary_only=True)
        assert "✓ SYNCED" in output
        assert "Local: 10" in output
        assert "Supabase: 10" in output
        assert "100.0%" in output

    def test_format_summary_only_out_of_sync(self):
        """Test summary-only format for out-of-sync database."""
        report = SyncReport(
            local_count=10,
            supabase_count=10,
            matching_files=8,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=["file1.md", "file2.md"],
            errors=[],
        )

        output = format_report(report, summary_only=True)
        assert "✗ OUT OF SYNC" in output
        assert "80.0%" in output

    def test_format_verbose_output(self):
        """Test verbose output includes all details."""
        report = SyncReport(
            local_count=5,
            supabase_count=6,
            matching_files=4,
            hash_mismatches=["mismatch1.md"],
            missing_in_local=["local1.md"],
            missing_in_supabase=["supabase1.md"],
            errors=[],
        )

        output = format_report(report, verbose=True)
        assert "Detailed Lists:" in output
        assert "All files with hash mismatches:" in output
        assert "mismatch1.md" in output
        assert "All files missing in Supabase:" in output
        assert "supabase1.md" in output

    def test_format_with_errors(self):
        """Test formatting report with errors."""
        report = SyncReport(
            local_count=0,
            supabase_count=0,
            matching_files=0,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=[],
            errors=["Connection failed", "Auth error"],
        )

        output = format_report(report)
        assert "Errors (2)" in output
        assert "Connection failed" in output
        assert "Auth error" in output


class TestLoadEnvConfig:
    """Test environment configuration loading."""

    @patch("scripts.ingest.verify_sync.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test_key",
            "SKILL_SPLIT_DB": "~/.claude/databases/test.db",
        },
    )
    def test_load_env_config_with_all_vars(self, mock_load_dotenv):
        """Test loading config when all environment variables are set."""
        local_db, url, key = load_env_config()

        assert "test.db" in local_db
        assert url == "https://example.supabase.co"
        assert key == "test_key"

    @patch("scripts.ingest.verify_sync.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SECRET_KEY": "secret_key",
        },
        clear=True,
    )
    def test_load_env_config_fallback_secret_key(self, mock_load_dotenv):
        """Test fallback to SUPABASE_SECRET_KEY."""
        local_db, url, key = load_env_config()

        assert url == "https://example.supabase.co"
        assert key == "secret_key"

    @patch("scripts.ingest.verify_sync.load_dotenv")
    @patch.dict(os.environ, {"SUPABASE_KEY": "test_key"}, clear=True)
    def test_load_env_config_missing_url(self, mock_load_dotenv):
        """Test error when SUPABASE_URL is missing."""
        with pytest.raises(ValueError) as exc_info:
            load_env_config()

        assert "SUPABASE_URL" in str(exc_info.value)

    @patch("scripts.ingest.verify_sync.load_dotenv")
    @patch.dict(os.environ, {"SUPABASE_URL": "https://example.supabase.co"}, clear=True)
    def test_load_env_config_missing_key(self, mock_load_dotenv):
        """Test error when both key environment variables are missing."""
        with pytest.raises(ValueError) as exc_info:
            load_env_config()

        assert "SUPABASE_KEY" in str(exc_info.value)


# Integration tests
class TestSyncVerifierIntegration:
    """Integration tests for the full sync verification flow."""

    def test_full_sync_verification_with_mock_supabase(self):
        """Test full verification flow with mocked Supabase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")

            # Create test database
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE files (
                        id INTEGER PRIMARY KEY,
                        path TEXT UNIQUE,
                        type TEXT,
                        hash TEXT
                    )
                    """
                )
                conn.execute(
                    "INSERT INTO files VALUES (1, 'test/file1.md', 'skill', 'hash1')"
                )
                conn.commit()

            # Mock Supabase
            verifier = SyncVerifier(db_path, "http://example.com", "fake_key")

            with patch.object(
                verifier, "_load_supabase_files"
            ) as mock_supabase:
                from scripts.ingest.verify_sync import FileInfo

                mock_supabase.return_value = {
                    "test/file1.md": FileInfo(
                        path="test/file1.md", hash="hash1", file_type="skill"
                    ),
                }

                report = verifier.verify()

                assert report.local_count == 1
                assert report.supabase_count == 1
                assert report.matching_files == 1
                assert report.is_synced
