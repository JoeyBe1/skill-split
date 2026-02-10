#!/usr/bin/env python3
"""
Automatic migration script for SQLite databases from v0.x to v1.0.0

This script safely migrates skill-split SQLite databases to the v1.0.0 schema
by adding new columns and updating existing data. Uses transactions for safety.

Usage:
    python migrate_sqlite.py                    # Use default database
    python migrate_sqlite.py /path/to/db.db     # Use custom database
"""

import sqlite3
import os
import sys
from pathlib import Path


def migrate_database(db_path: str) -> bool:
    """
    Migrate SQLite database to v1.0.0 schema.

    Adds the following changes:
    - sections.closing_tag_prefix column (XML tag support)
    - files.created_at column (audit trail)
    - files.updated_at column (audit trail)

    Args:
        db_path: Path to SQLite database file

    Returns:
        True if migration successful, False otherwise
    """
    # Expand user path
    db_path = os.path.expanduser(db_path)

    if not os.path.exists(db_path):
        print(f"Error: Database not found: {db_path}")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get current schema version
        cursor.execute("PRAGMA user_version")
        current_version = cursor.fetchone()[0]

        if current_version >= 1:
            print("Database already at v1.0.0 or higher")
            return True

        # Check if migration already applied by checking columns
        cursor.execute("PRAGMA table_info(sections)")
        sections_columns = [row[1] for row in cursor.fetchall()]

        if 'closing_tag_prefix' in sections_columns:
            print("Database already has v1.0.0 schema (columns present)")
            # Update schema version anyway
            cursor.execute("PRAGMA user_version = 1")
            conn.commit()
            return True

        # Begin transaction for atomic migration
        print("Starting migration...")
        conn.execute("BEGIN TRANSACTION")

        # Track migration steps
        steps = []

        # Step 1: Add closing_tag_prefix column to sections
        if 'closing_tag_prefix' not in sections_columns:
            print("  [1/4] Adding closing_tag_prefix column...")
            conn.execute(
                "ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT ''"
            )
            steps.append("closing_tag_prefix")
        else:
            print("  [1/4] closing_tag_prefix column exists, skipping...")

        # Step 2: Check and add timestamp columns to files table
        cursor.execute("PRAGMA table_info(files)")
        files_columns = [row[1] for row in cursor.fetchall()]

        if 'created_at' not in files_columns:
            print("  [2/4] Adding created_at column...")
            conn.execute(
                "ALTER TABLE files ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
            steps.append("created_at")
        else:
            print("  [2/4] created_at column exists, skipping...")

        if 'updated_at' not in files_columns:
            print("  [3/4] Adding updated_at column...")
            conn.execute(
                "ALTER TABLE files ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
            steps.append("updated_at")
        else:
            print("  [3/4] updated_at column exists, skipping...")

        # Step 3: Update existing rows to have default values
        print("  [4/4] Updating existing rows...")
        cursor.rowcount = -1  # Don't require rowcount
        conn.execute(
            "UPDATE sections SET closing_tag_prefix = '' WHERE closing_tag_prefix IS NULL"
        )

        # Set schema version
        cursor.execute("PRAGMA user_version = 1")

        # Commit transaction
        conn.commit()
        print("Migration completed successfully!")
        print(f"Changes applied: {', '.join(steps) if steps else 'none (already up to date)'}")

        # Display statistics
        cursor.execute("SELECT COUNT(*) FROM sections")
        section_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM files")
        file_count = cursor.fetchone()[0]

        print(f"\nDatabase statistics:")
        print(f"  - Files: {file_count}")
        print(f"  - Sections: {section_count}")

        return True

    except sqlite3.Error as e:
        print(f"Migration failed: {e}")
        try:
            conn.rollback()
            print("Transaction rolled back - database unchanged")
        except:
            pass
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        try:
            conn.rollback()
        except:
            pass
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def print_usage():
    """Print usage information."""
    print("Usage: python migrate_sqlite.py [database_path]")
    print()
    print("Arguments:")
    print("  database_path    Optional path to SQLite database")
    print("                   Default: ~/.claude/databases/skill-split.db")
    print()
    print("Examples:")
    print("  python migrate_sqlite.py")
    print("  python migrate_sqlite.py /path/to/database.db")
    print("  python migrate_sqlite.py ./skill_split.db")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate skill-split SQLite database to v1.0.0 schema",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'database',
        nargs='?',
        help='Path to SQLite database (default: ~/.claude/databases/skill-split.db)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Check if migration is needed without making changes'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='migrate_sqlite.py 1.0.0'
    )

    args = parser.parse_args()

    # Determine database path
    if args.database:
        db_path = args.database
    else:
        # Use default location
        db_path = os.path.expanduser("~/.claude/databases/skill-split.db")

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Error: Database not found: {db_path}")
        print()
        print("Please ensure the database exists or specify the correct path.")
        print()
        print_usage()
        sys.exit(1)

    print(f"Database: {db_path}")

    # Dry run mode
    if args.dry_run:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]

            cursor.execute("PRAGMA table_info(sections)")
            sections_columns = [row[1] for row in cursor.fetchall()]

            needs_migration = 'closing_tag_prefix' not in sections_columns

            print(f"Schema version: {version}")
            print(f"Migration needed: {'Yes' if needs_migration else 'No'}")
            print()
            print("Use 'python migrate_sqlite.py' to apply migration.")

            conn.close()
            sys.exit(0 if not needs_migration else 1)
        except Exception as e:
            print(f"Error checking database: {e}")
            sys.exit(1)

    # Perform migration
    success = migrate_database(db_path)

    if success:
        print()
        print("✓ Migration successful!")
        print()
        print("Next steps:")
        print("  1. Verify: python verify_migration.py")
        print("  2. Test: ./skill_split.py list-library")
        sys.exit(0)
    else:
        print()
        print("✗ Migration failed!")
        print()
        print("Troubleshooting:")
        print("  1. Ensure database is not locked by another process")
        print("  2. Ensure you have write permissions")
        print("  3. Check database is valid: sqlite3 <db> 'PRAGMA integrity_check;'")
        sys.exit(1)


if __name__ == "__main__":
    main()
