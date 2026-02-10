#!/usr/bin/env python3
"""
Database Migration Tool

Handles schema migrations for skill-split databases.

Usage:
    python scripts/migrate_database.py --list
    python scripts/migrate_database.py --apply
    python scripts/migrate_database.py --rollback
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict


MIGRATIONS: Dict[str, str] = {
    "001_add_closing_tag_prefix": """
        ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT '';
    """,
    "002_add_metadata_json": """
        ALTER TABLE sections ADD COLUMN metadata_json TEXT;
    """,
    "003_add_index_navigation": """
        CREATE INDEX IF NOT EXISTS idx_navigation
        ON sections(file_path, parent_id, order_in_parent);
    """,
    "004_add_index_level": """
        CREATE INDEX IF NOT EXISTS idx_sections_level
        ON sections(level);
    """,
    "005_add_index_hash": """
        CREATE INDEX IF NOT EXISTS idx_sections_hash
        ON sections(content_hash);
    """,
}


def get_applied_migrations(db_path: str) -> set:
    """Get list of applied migrations."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create migrations table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT name FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def list_migrations(db_path: str):
    """List all migrations and their status."""
    applied = get_applied_migrations(db_path)

    print("📋 Database Migrations")
    print("=" * 40)
    print(f"Database: {db_path}\n")

    for name, sql in MIGRATIONS.items():
        status = "✅ Applied" if name in applied else "⏳ Pending"
        print(f"{status}: {name}")

    print(f"\nTotal: {len(MIGRATIONS)} migrations")
    print(f"Applied: {len(applied)}")
    print(f"Pending: {len(MIGRATIONS) - len(applied)}")


def apply_migrations(db_path: str, dry_run: bool = False):
    """Apply pending migrations."""
    applied = get_applied_migrations(db_path)
    pending = [name for name in MIGRATIONS if name not in applied]

    if not pending:
        print("✅ All migrations applied!")
        return 0

    print(f"🔄 Applying {len(pending)} migrations...")
    print(f"Database: {db_path}\n")

    if dry_run:
        print("🔍 DRY RUN - no changes will be made\n")

    conn = sqlite3.connect(db_path)
    try:
        for name in pending:
            sql = MIGRATIONS[name]
            print(f"Applying: {name}")

            if not dry_run:
                cursor = conn.cursor()
                cursor.execute(sql)
                cursor.execute(
                    "INSERT INTO schema_migrations (name) VALUES (?)",
                    (name,)
                )
                conn.commit()

        if not dry_run:
            print(f"\n✅ Successfully applied {len(pending)} migrations")
        else:
            print(f"\n✅ Would apply {len(pending)} migrations")

        return 0

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        return 1

    finally:
        conn.close()


def rollback_migration(db_path: str, name: str):
    """Rollback a specific migration."""
    applied = get_applied_migrations(db_path)

    if name not in applied:
        print(f"❌ Migration '{name}' not applied")
        return 1

    print(f"⏪ Rolling back: {name}")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schema_migrations WHERE name = ?", (name,))
        conn.commit()

        print(f"✅ Rolled back {name}")
        print("⚠️  Note: Schema changes may need manual reversal")
        return 0

    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback failed: {e}")
        return 1

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Database migration tool for skill-split"
    )

    parser.add_argument("--db", default="skill_split.db",
                       help="Database path (default: skill_split.db)")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List migrations and status")
    parser.add_argument("--apply", "-a", action="store_true",
                       help="Apply pending migrations")
    parser.add_argument("--dry-run", "-n", action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--rollback", "-r", metavar="NAME",
                       help="Rollback specific migration")

    args = parser.parse_args()

    if not any([args.list, args.apply, args.rollback]):
        args.list = True  # Default to listing

    if args.list:
        list_migrations(args.db)
    elif args.apply:
        return apply_migrations(args.db, args.dry_run)
    elif args.rollback:
        return rollback_migration(args.db, args.rollback)

    return 0


if __name__ == "__main__":
    sys.exit(main())
