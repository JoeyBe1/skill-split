"""
Backup manager for skill-split databases.

This module provides the BackupManager class which handles automated
database backups using SQLite dump functionality with gzip compression.
"""

from __future__ import annotations

import gzip
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class BackupError(Exception):
    """Exception raised for backup-related errors."""
    pass


class IntegrityError(BackupError):
    """Exception raised when database integrity validation fails."""
    pass


class BackupManager:
    """
    Manages database backups and restoration for skill-split.

    Creates timestamped, gzip-compressed SQL dumps of SQLite databases
    with support for integrity validation during restoration.
    """

    def __init__(self, backup_dir: Optional[str] = None) -> None:
        """
        Initialize the backup manager.

        Args:
            backup_dir: Directory to store backups (default: ~/.claude/backups/)
        """
        if backup_dir is None:
            home = os.path.expanduser("~")
            backup_dir = os.path.join(home, ".claude", "backups")

        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        db_path: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Create a backup of the database.

        Generates a complete SQL dump using sqlite3's iterdump() method,
        compressed with gzip. Validates the database is readable before backup.

        Args:
            db_path: Path to the source database
            filename: Optional filename for the backup (default: auto-generated timestamp)

        Returns:
            Full path to the created backup file

        Raises:
            BackupError: If database not found, not readable, or backup fails
        """
        # Validate database exists and is readable
        if not self._validate_database(db_path):
            raise BackupError(f"Database not found or not readable: {db_path}")

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"skill-split-{timestamp}.sql.gz"
        elif not filename.endswith(".sql.gz"):
            filename = f"{filename}.sql.gz"

        backup_path = self.backup_dir / filename

        try:
            # Create SQL dump and compress
            with sqlite3.connect(db_path) as conn:
                # Enable foreign keys for proper dump
                conn.execute("PRAGMA foreign_keys = ON")

                # Generate SQL dump
                sql_dump = '\n'.join(conn.iterdump())

            # Write compressed backup
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                f.write(sql_dump)

            return str(backup_path)

        except sqlite3.OperationalError as e:
            raise BackupError(f"Database operation failed: {e}")
        except (OSError, IOError) as e:
            raise BackupError(f"Failed to write backup file: {e}")

    def restore_backup(
        self,
        backup_file: str,
        target_db_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Restore a database from a backup file.

        Decompresses the gzip backup and executes the SQL script to recreate
        the database. Validates integrity after restoration.

        Args:
            backup_file: Path to the backup file (.sql.gz)
            target_db_path: Path where the database should be restored
            overwrite: If True, overwrite existing database

        Returns:
            Dict with restoration statistics:
                - records_restored: Number of records restored
                - tables_restored: Number of tables restored
                - integrity_check_passed: Whether integrity validation passed
                - files_count: Number of files in restored database
                - sections_count: Number of sections in restored database

        Raises:
            BackupError: If backup file is invalid or restore fails
            IntegrityError: If integrity validation fails after restore
        """
        # Validate backup file
        if not self._validate_backup_file(backup_file):
            raise BackupError(f"Invalid or corrupted backup file: {backup_file}")

        # Check if target exists
        target_path = Path(target_db_path)
        if target_path.exists() and not overwrite:
            raise BackupError(
                f"Target database already exists: {target_db_path}. "
                "Use --overwrite to replace existing database."
            )

        # Create target directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # If overwrite is True, delete existing database first
        if overwrite and target_path.exists():
            target_path.unlink()

        # Decompress backup to temp file
        decompressed_sql = self._decompress_backup(backup_file)

        try:
            # Read SQL dump from temp file
            with open(decompressed_sql, 'r', encoding='utf-8') as f:
                sql_dump = f.read()

            # Filter out problematic statements
            # iterdump() produces SQL meant for sqlite3 CLI, not Python API
            filtered_lines = []
            skip_fts5_insert = False
            skip_fts_data_insert = False
            for line in sql_dump.split('\n'):
                stripped = line.strip()

                # Skip PRAGMA writable_schema lines (requires special handling)
                if stripped.startswith('PRAGMA writable_schema'):
                    continue

                # Skip DELETE FROM sqlite_sequence (auto-managed)
                if stripped.startswith('DELETE FROM sqlite_sequence'):
                    continue

                # Skip INSERT INTO sqlite_sequence (auto-managed)
                if stripped.startswith('INSERT INTO "sqlite_sequence"') or stripped.startswith('INSERT INTO sqlite_sequence'):
                    continue

                # Skip FTS5 shadow table creation and data inserts
                # We'll recreate FTS5 from scratch after the main restore
                if any(name in stripped for name in [
                    'sections_fts_config', 'sections_fts_data',
                    'sections_fts_docsize', 'sections_fts_idx'
                ]):
                    continue

                # Skip INSERT INTO "sections_fts" (the FTS5 content table)
                if 'INSERT INTO "sections_fts"' in stripped:
                    skip_fts_data_insert = True
                    continue

                # Skip continuation of FTS5 data insert (multi-line values)
                if skip_fts_data_insert:
                    if stripped.endswith(");"):
                        skip_fts_data_insert = False
                    continue

                # Skip multi-line INSERT INTO sqlite_master for FTS5
                if 'INSERT INTO sqlite_master' in stripped and 'sections_fts' in stripped:
                    skip_fts5_insert = True
                    continue

                if skip_fts5_insert:
                    if stripped.endswith("');"):
                        skip_fts5_insert = False
                    continue

                filtered_lines.append(line)

            filtered_sql = '\n'.join(filtered_lines)

            # Execute the filtered SQL
            with sqlite3.connect(target_db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.executescript(filtered_sql)
                conn.commit()

                # Recreate FTS5 virtual table from scratch
                # (we filtered out all FTS5-related statements)
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
                        title,
                        content,
                        content=sections,
                        content_rowid=id
                    )
                    """
                )
                # Populate FTS5 with existing sections
                conn.execute(
                    """
                    INSERT INTO sections_fts(rowid, title, content)
                    SELECT id, title, content FROM sections
                    """
                )
                conn.commit()

                # Count records for statistics
                cursor = conn.execute("SELECT COUNT(*) FROM files")
                files_count = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM sections")
                sections_count = cursor.fetchone()[0]

                # Count tables
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                )
                tables_count = cursor.fetchone()[0]

            # Connection is closed when exiting the with block

            # Validate integrity (uses a fresh connection)
            integrity_result = self.validate_integrity(target_db_path)

            return {
                "records_restored": files_count + sections_count,
                "tables_restored": tables_count,
                "integrity_check_passed": integrity_result["integrity_ok"],
                "files_count": files_count,
                "sections_count": sections_count,
                "fts5_exists": integrity_result.get("fts5_exists", False),
                "foreign_keys_ok": integrity_result.get("foreign_keys_ok", False),
            }

        except sqlite3.OperationalError as e:
            # Clean up failed restore
            if target_path.exists():
                target_path.unlink()
            raise BackupError(f"Database restoration failed: {e}")
        finally:
            # Clean up decompressed file
            temp_sql = Path(decompressed_sql)
            if temp_sql.exists():
                temp_sql.unlink()

    def validate_integrity(self, db_path: str) -> Dict[str, Any]:
        """
        Validate database integrity after restoration.

        Runs SQLite's built-in integrity check and verifies the schema
        is correct for skill-split.

        Args:
            db_path: Path to the database to validate

        Returns:
            Dict with validation results:
                - integrity_ok: Whether PRAGMA integrity_check passed
                - files_count: Number of files in database
                - sections_count: Number of sections in database
                - fts5_exists: Whether FTS5 virtual table exists
                - foreign_keys_ok: Whether foreign key constraints are enforced

        Raises:
            IntegrityError: If any validation check fails
        """
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")

                # Run SQLite integrity check
                cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()

                # Check result (should be "ok")
                integrity_ok = integrity_result[0] == "ok"

                # Count records
                cursor = conn.execute("SELECT COUNT(*) FROM files")
                files_count = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM sections")
                sections_count = cursor.fetchone()[0]

                # Check for FTS5 table
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master "
                    "WHERE type='table' AND name='sections_fts'"
                )
                fts5_exists = cursor.fetchone()[0] > 0

                # Test foreign key enforcement
                fk_ok = True
                try:
                    # Try to insert invalid section (should fail)
                    conn.execute(
                        "INSERT INTO sections (file_id, level, title, content, "
                        "order_index, line_start, line_end) "
                        "VALUES (99999, 1, 'test', 'test', 1, 1, 1)"
                    )
                    # If we got here, foreign keys are not enforced
                    fk_ok = False
                    conn.rollback()
                except sqlite3.IntegrityError:
                    # Expected - foreign key constraint worked
                    conn.rollback()

                result = {
                    "integrity_ok": integrity_ok,
                    "files_count": files_count,
                    "sections_count": sections_count,
                    "fts5_exists": fts5_exists,
                    "foreign_keys_ok": fk_ok,
                }

                # Raise error if integrity check failed
                if not integrity_ok:
                    raise IntegrityError(
                        f"Integrity check failed: {integrity_result[0]}"
                    )

                return result

        except sqlite3.OperationalError as e:
            raise IntegrityError(f"Failed to validate database: {e}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups with metadata.

        Returns:
            List of dicts with backup metadata:
                - filename: Name of the backup file
                - size: Uncompressed size in bytes
                - compressed_size: Compressed size in bytes
                - created_at: Creation timestamp (from filename)
                - path: Full path to backup file
        """
        backups = []

        for backup_file in self.backup_dir.glob("*.sql.gz"):
            try:
                # Get file stats
                stat = backup_file.stat()

                # Extract timestamp from filename
                filename = backup_file.name
                created_at = None

                # Parse timestamp from "skill-split-YYYYMMDD-HHMMSS.sql.gz"
                parts = filename.replace("skill-split-", "").replace(".sql.gz", "")
                if "-" in parts:
                    try:
                        created_at = datetime.strptime(parts, "%Y%m%d-%H%M%S")
                    except ValueError:
                        pass

                # Get uncompressed size
                compressed_size = stat.st_size
                size = self._get_uncompressed_size(backup_file)

                backups.append({
                    "filename": filename,
                    "size": size,
                    "compressed_size": compressed_size,
                    "created_at": created_at,
                    "path": str(backup_file),
                })
            except (OSError, IOError):
                # Skip files we can't read
                continue

        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b["created_at"] or datetime.min, reverse=True)
        return backups

    def get_backup_path(self, filename: str) -> str:
        """
        Get the full path to a backup file.

        Args:
            filename: Name of the backup file

        Returns:
            Full path to the backup file

        Raises:
            BackupError: If backup file not found
        """
        # Ensure filename has correct extension
        if not filename.endswith(".sql.gz"):
            filename = f"{filename}.sql.gz"

        backup_path = self.backup_dir / filename

        if not backup_path.exists():
            # Try to find by pattern if exact match fails
            matching = list(self.backup_dir.glob(f"{filename}*.sql.gz"))
            if not matching:
                raise BackupError(f"Backup not found: {filename}")
            backup_path = matching[0]

        return str(backup_path)

    def _validate_database(self, db_path: str) -> bool:
        """
        Validate that a database file exists and is readable.

        Args:
            db_path: Path to the database file

        Returns:
            True if database is valid, False otherwise
        """
        db_file = Path(db_path)

        # Check file exists
        if not db_file.exists():
            return False

        # Check if file is readable and is a valid SQLite database
        try:
            with sqlite3.connect(db_path) as conn:
                # Try to query the files table
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='files'"
                )
                return cursor.fetchone() is not None
        except sqlite3.OperationalError:
            return False

    def _validate_backup_file(self, backup_file: str) -> bool:
        """
        Validate that a backup file exists and is a valid gzip file.

        Args:
            backup_file: Path to the backup file

        Returns:
            True if backup file is valid, False otherwise
        """
        backup_path = Path(backup_file)

        if not backup_path.exists():
            return False

        # Try to read gzip header
        try:
            with gzip.open(backup_path, 'rt') as f:
                # Read first line to verify it's SQL
                first_line = f.readline()
                # SQLite dumps start with "SQLite format" or "BEGIN TRANSACTION"
                return "SQLite" in first_line or "BEGIN" in first_line or "CREATE" in first_line
        except (OSError, IOError, gzip.BadGzipFile):
            return False

    def _decompress_backup(self, backup_file: str) -> str:
        """
        Decompress a backup file to a temporary location.

        Args:
            backup_file: Path to the compressed backup file

        Returns:
            Path to the decompressed SQL file

        Raises:
            BackupError: If decompression fails
        """
        import tempfile

        backup_path = Path(backup_file)

        # Create temp file for decompressed content
        temp_fd, temp_path = tempfile.mkstemp(suffix=".sql", text=True)

        try:
            with os.fdopen(temp_fd, 'w') as temp_file:
                with gzip.open(backup_path, 'rt', encoding='utf-8') as gz_file:
                    # Copy content
                    temp_file.write(gz_file.read())

            return temp_path
        except (OSError, IOError, gzip.BadGzipFile) as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise BackupError(f"Failed to decompress backup: {e}")

    def _get_uncompressed_size(self, backup_file: Path) -> int:
        """
        Get the uncompressed size of a backup file.

        Args:
            backup_file: Path to the compressed backup file

        Returns:
            Uncompressed size in bytes
        """
        try:
            with gzip.open(backup_file, 'rb') as f:
                # Read all content to get size
                return len(f.read())
        except (OSError, IOError, gzip.BadGzipFile):
            return 0


def create_backup(
    db_path: str,
    backup_dir: Optional[str] = None,
    filename: Optional[str] = None
) -> str:
    """
    Convenience function to create a database backup.

    Args:
        db_path: Path to the source database
        backup_dir: Optional directory for backups (default: ~/.claude/backups/)
        filename: Optional filename for the backup

    Returns:
        Full path to the created backup file
    """
    manager = BackupManager(backup_dir)
    return manager.create_backup(db_path, filename)


def get_backup_path(
    filename: str,
    backup_dir: Optional[str] = None
) -> str:
    """
    Convenience function to get the full path to a backup file.

    Args:
        filename: Name of the backup file
        backup_dir: Optional directory for backups (default: ~/.claude/backups/)

    Returns:
        Full path to the backup file
    """
    manager = BackupManager(backup_dir)
    return manager.get_backup_path(filename)
