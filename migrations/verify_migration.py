#!/usr/bin/env python3
"""
Verification script for skill-split v1.0.0 migration

This script verifies that a SQLite database has been properly migrated
to v1.0.0 schema by checking for required columns and data integrity.

Usage:
    python verify_migration.py                    # Verify default database
    python verify_migration.py /path/to/db.db     # Verify custom database
    python verify_migration.py --verbose          # Detailed output
"""

import sqlite3
import os
import sys
from typing import Dict, List


def verify_sqlite_migration(db_path: str, verbose: bool = False) -> Dict:
    """
    Verify that SQLite database has been properly migrated to v1.0.0.

    Checks:
    - Database exists and is readable
    - Required columns present (closing_tag_prefix, timestamps)
    - Data integrity (record counts, no NULL values in new columns)

    Args:
        db_path: Path to SQLite database file
        verbose: Enable detailed output

    Returns:
        Dictionary with verification results
    """
    # Expand user path
    db_path = os.path.expanduser(db_path)

    results = {
        "database_path": db_path,
        "database_exists": False,
        "database_readable": False,
        "schema_version": 0,
        "required_columns": {
            "sections_closing_tag_prefix": False,
            "files_created_at": False,
            "files_updated_at": False
        },
        "optional_columns": {
            "sections_line_start": False,
            "sections_line_end": False
        },
        "statistics": {
            "file_count": 0,
            "section_count": 0,
            "sections_with_null_prefix": 0
        },
        "indexes": {
            "sections_file_order": False,
            "sections_file_parent": False
        },
        "errors": [],
        "warnings": []
    }

    # Check database exists
    if not os.path.exists(db_path):
        results["errors"].append(f"Database not found: {db_path}")
        return results

    results["database_exists"] = True

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        results["database_readable"] = True

        # Get schema version
        cursor.execute("PRAGMA user_version")
        results["schema_version"] = cursor.fetchone()[0]

        if verbose:
            print(f"Schema version: {results['schema_version']}")

        # Check sections table columns
        cursor.execute("PRAGMA table_info(sections)")
        sections_columns = [row[1] for row in cursor.fetchall()]

        # Required columns for v1.0.0
        results["required_columns"]["sections_closing_tag_prefix"] = \
            "closing_tag_prefix" in sections_columns

        # Optional columns (may not exist in all v1.0.0 databases)
        results["optional_columns"]["sections_line_start"] = \
            "line_start" in sections_columns
        results["optional_columns"]["sections_line_end"] = \
            "line_end" in sections_columns

        if verbose:
            print(f"Sections table columns: {len(sections_columns)}")
            print(f"  - closing_tag_prefix: {'✓' if results['required_columns']['sections_closing_tag_prefix'] else '✗'}")

        # Check files table columns
        cursor.execute("PRAGMA table_info(files)")
        files_columns = [row[1] for row in cursor.fetchall()]

        results["required_columns"]["files_created_at"] = \
            "created_at" in files_columns
        results["required_columns"]["files_updated_at"] = \
            "updated_at" in files_columns

        if verbose:
            print(f"Files table columns: {len(files_columns)}")
            print(f"  - created_at: {'✓' if results['required_columns']['files_created_at'] else '✗'}")
            print(f"  - updated_at: {'✓' if results['required_columns']['files_updated_at'] else '✗'}")

        # Check for indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]

        results["indexes"]["sections_file_order"] = \
            "idx_sections_file_order" in indexes or \
            "sections_file_id_parent_id_order_index_idx" in indexes
        results["indexes"]["sections_file_parent"] = \
            "idx_sections_file_parent" in indexes or \
            "sections_file_id_parent_id_idx" in indexes

        if verbose:
            print(f"Indexes found: {len(indexes)}")
            print(f"  - file_order index: {'✓' if results['indexes']['sections_file_order'] else '✗'}")
            print(f"  - file_parent index: {'✓' if results['indexes']['sections_file_parent'] else '✗'}")

        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM files")
        results["statistics"]["file_count"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sections")
        results["statistics"]["section_count"] = cursor.fetchone()[0]

        if verbose:
            print(f"\nStatistics:")
            print(f"  - Files: {results['statistics']['file_count']}")
            print(f"  - Sections: {results['statistics']['section_count']}")

        # Check for NULL values in new columns
        if results["required_columns"]["sections_closing_tag_prefix"]:
            cursor.execute(
                "SELECT COUNT(*) FROM sections WHERE closing_tag_prefix IS NULL"
            )
            null_count = cursor.fetchone()[0]
            results["statistics"]["sections_with_null_prefix"] = null_count

            if null_count > 0:
                results["warnings"].append(
                    f"{null_count} sections have NULL closing_tag_prefix"
                )

        # Verify foreign key constraints are enabled
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        if not fk_enabled:
            results["warnings"].append("Foreign keys not enabled")

        # Test database integrity
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        if integrity_result != "ok":
            results["errors"].append(f"Database integrity check failed: {integrity_result}")

        conn.close()

    except sqlite3.Error as e:
        results["errors"].append(f"SQLite error: {e}")
        return results
    except Exception as e:
        results["errors"].append(f"Unexpected error: {e}")
        return results

    return results


def print_verification_results(results: Dict, verbose: bool = False):
    """Print verification results in a formatted way."""
    print("\n" + "="*60)
    print("Migration Verification Results")
    print("="*60)

    if results["errors"]:
        print("\n❌ ERRORS:")
        for error in results["errors"]:
            print(f"   - {error}")
        return

    print(f"\n✅ Database: {results['database_path']}")
    print(f"✅ Database exists: {results['database_exists']}")
    print(f"✅ Database readable: {results['database_readable']}")

    # Schema version
    version_color = "✅" if results["schema_version"] >= 1 else "⚠️"
    print(f"{version_color} Schema version: {results['schema_version']}")

    # Required columns
    print("\n📋 Required Columns:")
    for col_name, present in results["required_columns"].items():
        status = "✅" if present else "❌"
        print(f"   {status} {col_name}")

    # Optional columns
    if any(results["optional_columns"].values()):
        print("\n📋 Optional Columns:")
        for col_name, present in results["optional_columns"].items():
            status = "✅" if present else "➖"
            print(f"   {status} {col_name}")

    # Indexes
    print("\n🔍 Indexes:")
    for idx_name, present in results["indexes"].items():
        status = "✅" if present else "⚠️"
        print(f"   {status} {idx_name}")

    # Statistics
    print("\n📊 Statistics:")
    print(f"   - Files: {results['statistics']['file_count']}")
    print(f"   - Sections: {results['statistics']['section_count']}")

    # Warnings
    if results["warnings"]:
        print("\n⚠️  WARNINGS:")
        for warning in results["warnings"]:
            print(f"   - {warning}")

    # Overall status
    all_required_present = all(results["required_columns"].values())
    no_errors = len(results["errors"]) == 0

    if all_required_present and no_errors:
        print("\n✅ Migration appears complete and successful!")
    elif all_required_present:
        print("\n⚠️  Migration complete but with warnings")
    else:
        print("\n❌ Migration incomplete - some required columns missing")


def print_usage():
    """Print usage information."""
    print("Usage: python verify_migration.py [options] [database_path]")
    print()
    print("Arguments:")
    print("  database_path    Optional path to SQLite database")
    print("                   Default: ~/.claude/databases/skill-split.db")
    print()
    print("Options:")
    print("  -v, --verbose    Enable detailed output")
    print("  -h, --help       Show this help message")
    print()
    print("Examples:")
    print("  python verify_migration.py")
    print("  python verify_migration.py /path/to/database.db")
    print("  python verify_migration.py --verbose")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify skill-split v1.0.0 migration",
        add_help=False
    )
    parser.add_argument(
        'database',
        nargs='?',
        help='Path to SQLite database (default: ~/.claude/databases/skill-split.db)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable detailed output'
    )
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show help message'
    )

    args = parser.parse_args()

    if args.help:
        print_usage()
        sys.exit(0)

    # Determine database path
    if args.database:
        db_path = args.database
    else:
        # Use default location
        db_path = os.path.expanduser("~/.claude/databases/skill-split.db")

    # Run verification
    results = verify_sqlite_migration(db_path, verbose=args.verbose)

    # Print results
    print_verification_results(results, verbose=args.verbose)

    # Exit code based on results
    all_required_present = all(results["required_columns"].values())
    no_errors = len(results["errors"]) == 0

    if all_required_present and no_errors:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
