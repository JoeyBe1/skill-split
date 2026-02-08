#!/usr/bin/env python3
"""
Sync verification script for skill-split.

Compares local SQLite database with Supabase to verify synchronization status.
Reports file counts, hash mismatches, and missing files in either location.

Usage:
    ./verify_sync.py
    ./verify_sync.py --db ~/.claude/databases/skill-split.db
    ./verify_sync.py --verbose
    ./verify_sync.py --summary-only
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv


@dataclass
class FileInfo:
    """Information about a file in database."""
    path: str
    hash: str
    file_type: str


@dataclass
class SyncReport:
    """Detailed sync verification report."""
    local_count: int
    supabase_count: int
    matching_files: int
    hash_mismatches: List[str]
    missing_in_local: List[str]
    missing_in_supabase: List[str]
    errors: List[str]

    @property
    def is_synced(self) -> bool:
        """Check if databases are fully synced."""
        return (
            self.local_count == self.supabase_count
            and len(self.hash_mismatches) == 0
            and len(self.missing_in_local) == 0
            and len(self.missing_in_supabase) == 0
            and len(self.errors) == 0
        )

    def get_sync_percentage(self) -> float:
        """Calculate sync percentage."""
        if self.local_count == 0:
            return 0.0
        matching = self.local_count - len(self.missing_in_supabase)
        return (matching / self.local_count) * 100


class SyncVerifier:
    """Verifies synchronization between local and Supabase databases."""

    def __init__(self, local_db: str, supabase_url: str, supabase_key: str):
        """
        Initialize the sync verifier.

        Args:
            local_db: Path to local SQLite database
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.local_db = local_db
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.report = SyncReport(
            local_count=0,
            supabase_count=0,
            matching_files=0,
            hash_mismatches=[],
            missing_in_local=[],
            missing_in_supabase=[],
            errors=[],
        )

    def verify(self) -> SyncReport:
        """
        Run full sync verification.

        Returns:
            SyncReport with detailed comparison results
        """
        try:
            # Load local files
            local_files = self._load_local_files()
            if local_files is None:
                self.report.errors.append("Failed to load local database")
                return self.report

            self.report.local_count = len(local_files)

            # Load Supabase files
            supabase_files = self._load_supabase_files()
            if supabase_files is None:
                self.report.errors.append("Failed to connect to Supabase")
                return self.report

            self.report.supabase_count = len(supabase_files)

            # Compare files
            self._compare_files(local_files, supabase_files)

            return self.report

        except Exception as e:
            self.report.errors.append(f"Verification failed: {str(e)}")
            return self.report

    def _load_local_files(self) -> Optional[Dict[str, FileInfo]]:
        """
        Load all files from local SQLite database.

        Returns:
            Dict mapping file paths to FileInfo, or None on error
        """
        try:
            if not os.path.exists(self.local_db):
                self.report.errors.append(f"Local database not found: {self.local_db}")
                return None

            with sqlite3.connect(self.local_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT path, hash, type FROM files ORDER BY path"
                )
                rows = cursor.fetchall()

                files = {}
                for row in rows:
                    files[row["path"]] = FileInfo(
                        path=row["path"],
                        hash=row["hash"] or "",
                        file_type=row["type"],
                    )
                return files

        except sqlite3.Error as e:
            self.report.errors.append(f"SQLite error: {str(e)}")
            return None

    def _load_supabase_files(self) -> Optional[Dict[str, FileInfo]]:
        """
        Load all files from Supabase.

        Returns:
            Dict mapping file paths to FileInfo, or None on error
        """
        try:
            from supabase import create_client

            client = create_client(self.supabase_url, self.supabase_key)
            result = client.table("files").select("*").execute()

            files = {}
            for row in result.data:
                path = row.get("storage_path", "")
                files[path] = FileInfo(
                    path=path,
                    hash=row.get("hash", ""),
                    file_type=row.get("type", ""),
                )
            return files

        except ImportError:
            self.report.errors.append("supabase package not installed")
            return None
        except Exception as e:
            self.report.errors.append(f"Supabase error: {str(e)}")
            return None

    def _compare_files(
        self, local_files: Dict[str, FileInfo], supabase_files: Dict[str, FileInfo]
    ) -> None:
        """
        Compare files between local and Supabase.

        Args:
            local_files: Files from local database
            supabase_files: Files from Supabase
        """
        local_paths = set(local_files.keys())
        supabase_paths = set(supabase_files.keys())

        # Find matching files and check hashes
        for path in local_paths & supabase_paths:
            local_hash = local_files[path].hash
            supabase_hash = supabase_files[path].hash

            if local_hash == supabase_hash:
                self.report.matching_files += 1
            else:
                self.report.hash_mismatches.append(path)

        # Find missing files
        self.report.missing_in_supabase = sorted(local_paths - supabase_paths)
        self.report.missing_in_local = sorted(supabase_paths - local_paths)


def load_env_config() -> Tuple[str, str, str]:
    """
    Load configuration from environment variables.

    Returns:
        Tuple of (local_db_path, supabase_url, supabase_key)

    Raises:
        ValueError: If required environment variables are missing
    """
    load_dotenv()

    local_db = os.getenv("SKILL_SPLIT_DB")
    if not local_db:
        # Try default location
        local_db = os.path.expanduser("~/.claude/databases/skill-split.db")

    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable not set")

    # Try SUPABASE_KEY first, then SUPABASE_SECRET_KEY
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SECRET_KEY")
    if not supabase_key:
        raise ValueError(
            "Neither SUPABASE_KEY nor SUPABASE_SECRET_KEY environment variable set"
        )

    return local_db, supabase_url, supabase_key


def format_report(
    report: SyncReport, verbose: bool = False, summary_only: bool = False
) -> str:
    """
    Format sync report for display.

    Args:
        report: The sync report to format
        verbose: Include detailed information
        summary_only: Only show summary line

    Returns:
        Formatted report string
    """
    lines = []

    if summary_only:
        if report.is_synced:
            status = "✓ SYNCED"
        else:
            status = "✗ OUT OF SYNC"
        lines.append(
            f"{status} | Local: {report.local_count} | "
            f"Supabase: {report.supabase_count} | "
            f"Sync: {report.get_sync_percentage():.1f}%"
        )
        return "\n".join(lines)

    # Header
    lines.append("=" * 70)
    lines.append("SYNC VERIFICATION REPORT")
    lines.append("=" * 70)

    # Status
    if report.is_synced:
        lines.append("Status: ✓ FULLY SYNCED")
    else:
        lines.append("Status: ✗ OUT OF SYNC")

    # Counts
    lines.append("")
    lines.append("File Counts:")
    lines.append(f"  Local SQLite:     {report.local_count}")
    lines.append(f"  Supabase:         {report.supabase_count}")
    lines.append(f"  Matching:         {report.matching_files}")
    lines.append(f"  Sync percentage:  {report.get_sync_percentage():.1f}%")

    # Hash mismatches
    if report.hash_mismatches:
        lines.append("")
        lines.append(f"Hash Mismatches ({len(report.hash_mismatches)}):")
        for path in report.hash_mismatches[:10]:
            lines.append(f"  - {path}")
        if len(report.hash_mismatches) > 10:
            lines.append(f"  ... and {len(report.hash_mismatches) - 10} more")

    # Missing in Supabase
    if report.missing_in_supabase:
        lines.append("")
        lines.append(f"Missing in Supabase ({len(report.missing_in_supabase)}):")
        for path in report.missing_in_supabase[:10]:
            lines.append(f"  - {path}")
        if len(report.missing_in_supabase) > 10:
            lines.append(f"  ... and {len(report.missing_in_supabase) - 10} more")

    # Missing in Local
    if report.missing_in_local:
        lines.append("")
        lines.append(f"Missing in Local ({len(report.missing_in_local)}):")
        for path in report.missing_in_local[:10]:
            lines.append(f"  - {path}")
        if len(report.missing_in_local) > 10:
            lines.append(f"  ... and {len(report.missing_in_local) - 10} more")

    # Errors
    if report.errors:
        lines.append("")
        lines.append(f"Errors ({len(report.errors)}):")
        for error in report.errors:
            lines.append(f"  - {error}")

    # Verbose details
    if verbose and (
        report.hash_mismatches or report.missing_in_supabase or report.missing_in_local
    ):
        lines.append("")
        lines.append("Detailed Lists:")

        if report.hash_mismatches:
            lines.append("")
            lines.append("All files with hash mismatches:")
            for path in report.hash_mismatches:
                lines.append(f"  {path}")

        if report.missing_in_supabase:
            lines.append("")
            lines.append("All files missing in Supabase:")
            for path in report.missing_in_supabase:
                lines.append(f"  {path}")

        if report.missing_in_local:
            lines.append("")
            lines.append("All files missing in Local:")
            for path in report.missing_in_local:
                lines.append(f"  {path}")

    lines.append("=" * 70)
    return "\n".join(lines)


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 if synced, 1 if out of sync or error)
    """
    parser = argparse.ArgumentParser(
        description="Verify sync status between local SQLite and Supabase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run verification with default config
  %(prog)s --verbose          # Show detailed mismatch lists
  %(prog)s --summary-only     # Show only one-line summary
  %(prog)s --db ~/.my-db.db   # Use custom database path
        """,
    )

    parser.add_argument(
        "--db",
        type=str,
        help="Path to local SQLite database (default: from .env or ~/.claude/databases/skill-split.db)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed mismatch information",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show one-line summary",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        local_db, supabase_url, supabase_key = load_env_config()

        # Override with command-line args if provided
        if args.db:
            local_db = os.path.expanduser(args.db)

        # Expand home directory
        local_db = os.path.expanduser(local_db)

        # Run verification
        verifier = SyncVerifier(local_db, supabase_url, supabase_key)
        report = verifier.verify()

        # Display report
        output = format_report(report, verbose=args.verbose, summary_only=args.summary_only)
        print(output)

        # Return appropriate exit code
        return 0 if report.is_synced else 1

    except ValueError as e:
        print(f"Configuration error: {str(e)}", file=sys.stderr)
        print("Please set SUPABASE_URL and SUPABASE_KEY in .env or environment",
              file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
