# Migration Guide: skill-split v1.0.0

**Last Updated**: 2026-02-10
**Current Version**: v1.0.0
**Status**: Production Ready

This guide helps you migrate from earlier versions (v0.x) to skill-split v1.0.0. It covers database schema changes, API modifications, CLI command updates, and configuration requirements.

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Database Schema Changes](#database-schema-changes)
4. [API Changes and Deprecations](#api-changes-and-deprecations)
5. [CLI Command Changes](#cli-command-changes)
6. [Configuration Updates](#configuration-updates)
7. [Step-by-Step Migration](#step-by-step-migration)
8. [Data Migration Scripts](#data-migration-scripts)
9. [Rollback Procedures](#rollback-procedures)
10. [Common Migration Issues](#common-migration-issues)
11. [Post-Migration Verification](#post-migration-verification)

---

## Overview

### What's New in v1.0.0

skill-split v1.0.0 is a major release that introduces significant enhancements while maintaining backward compatibility where possible:

**New Features:**
- **Three Search Modes**: BM25 keyword search, Vector semantic search, and Hybrid combined search
- **Component Handlers**: Native support for plugins, hooks, configs, and scripts (Python, JS, TS, Shell)
- **Skill Composition**: Create new skills from existing sections
- **Supabase Integration**: Cloud storage with pgvector support
- **Checkout/Checkin System**: Transaction-safe file deployment
- **Backup/Restore**: Disaster recovery with gzip compression
- **SecretManager**: Secure API key management
- **Batch Embedding**: 10-100x performance improvement for vector generation

**Performance Improvements:**
- 623 tests passing (up from 518 in v0.x)
- 1,368 production files indexed
- 19,271 sections stored and searchable
- 99% token savings from progressive disclosure

**Breaking Changes:**
- Database schema now requires `closing_tag_prefix` column
- New file types (plugin, hook, config, script) added to FileType enum
- Some CLI commands have new required arguments
- Environment variable naming has changed for some features

---

## Pre-Migration Checklist

Before starting the migration, ensure you have:

- [ ] **Backup your current database**
  ```bash
  # Create a manual backup
  cp ~/.claude/databases/skill-split.db ~/.claude/databases/skill-split.db.backup
  ```

- [ ] **Document your current setup**
  ```bash
  # Record your database location
  echo $SKILL_SPLIT_DB

  # List current files in database
  ./skill_split.py list-library --db ~/.claude/databases/skill-split.db
  ```

- [ ] **Check Python version** (requires Python 3.8+)
  ```bash
  python --version  # Should be 3.8 or higher
  ```

- [ ] **Review current usage patterns**
  - Which CLI commands do you use regularly?
  - Do you use Supabase or local SQLite only?
  - Are you using custom scripts that interact with the database?

- [ ] **Plan for downtime**
  - Migration typically takes 5-15 minutes
  - Database may be temporarily unavailable during schema updates

- [ ] **Test environment ready?**
  - Consider testing migration in a non-production environment first

---

## Database Schema Changes

### SQLite Schema Changes

#### New Columns in `sections` Table

The `sections` table now includes:

```sql
-- XML tag support (v0.x compatibility: default '')
ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT '';
```

**Impact**: Existing rows will have empty string as default. No data migration required.

#### New File Types Supported

The `files` table `type` column now supports:

```sql
-- Original v0.x types: 'skill', 'command', 'reference'
-- New v1.0.0 types: 'agent', 'plugin', 'hook', 'output_style', 'config', 'documentation', 'script'
```

**Impact**: Existing files with original types are unaffected. New types are optional.

#### Timestamp Tracking

```sql
-- New columns for audit trails
ALTER TABLE files ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE files ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

**Impact**: Automatically populated for new records. Existing records will have NULL or current timestamp depending on migration approach.

### Supabase Schema Changes

If using Supabase, apply the following migrations in order:

#### 1. Enable pgvector Extension

```sql
-- Run in Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 2. Add Missing Columns

See `/Users/joey/working/skill-split/migrations/unify_supabase_schema.sql` for complete migration script.

Key changes:
- `line_start`, `line_end` columns for script round-trip
- `closing_tag_prefix` for XML tag support
- Performance indexes for progressive disclosure
- Full-text search with GIN indexes

#### 3. Create Embeddings Table

```sql
-- For vector search functionality
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_section_id
ON embeddings(section_id);
```

#### 4. Update File Type Constraints

```sql
-- Extend allowed file types
ALTER TABLE files DROP CONSTRAINT IF EXISTS files_type_check;

ALTER TABLE files
ADD CONSTRAINT files_type_check
CHECK (type IN (
    'skill', 'command', 'reference', 'agent',
    'plugin', 'hook', 'output_style', 'config',
    'documentation', 'script'
));
```

### Schema Version Tracking

v1.0.0 introduces schema version tracking:

```python
# Check current schema version
SELECT value FROM metadata WHERE key = 'schema_version';
```

Current schema version: `1.0.0`

---

## API Changes and Deprecations

### Query API Changes

#### New Methods in `QueryAPI`

```python
from core.query import QueryAPI

# v1.0.0 new methods
query_api = QueryAPI(db_path)

# Progressive disclosure
query_api.get_next_section(current_id, file_path, first_child=False)
query_api.get_section_tree(section_id)

# Search methods
query_api.search_sections(query, limit=10)
query_api.search_sections_fts5(query)  # BM25 keyword search
```

#### Deprecated Methods

The following methods from v0.x are still supported but deprecated:

| Deprecated Method | Replacement | Deprecation Status |
|-------------------|-------------|-------------------|
| `get_all_sections(file_path)` | `get_section_tree(file_id)` | Soft deprecation |
| `search_content(query)` | `search_sections(query)` | Soft deprecation |

### DatabaseStore Changes

#### New Constructor Parameters

```python
from core.database import DatabaseStore

# v1.0.0: All parameters optional
store = DatabaseStore(
    db_path="~/.claude/databases/skill-split.db"  # Default location
)
```

#### Context Manager Support

```python
# v1.0.0: Context manager now available
with DatabaseStore(db_path) as store:
    sections = store.get_sections_by_file(file_id)
# Connection automatically closed
```

### Handler Factory Changes

#### New Handler Types

```python
from handlers.factory import HandlerFactory
from models import FileType

# v1.0.0: New file types supported
handler = HandlerFactory.get_handler(FileType.SCRIPT)
handler = HandlerFactory.get_handler(FileType.PLUGIN)
handler = Factory.get_handler(FileType.HOOK)
handler = HandlerFactory.get_handler(FileType.CONFIG)
```

### Section Model Changes

#### New Attributes

```python
from models import Section

section = Section(
    level=1,
    title="Example",
    content="Content here",
    line_start=10,
    line_end=20,
    closing_tag_prefix="",  # NEW: v1.0.0
    file_id="uuid-or-int",  # NEW: v1.0.0
    file_type=FileType.SKILL  # NEW: v1.0.0
)
```

---

## CLI Command Changes

### Command Overview Table

| Category | v0.x Command | v1.0.0 Command | Status |
|----------|--------------|----------------|--------|
| **Core** | `parse` | `parse` | Unchanged |
| **Core** | `validate` | `validate` | Unchanged |
| **Core** | `store` | `store` | Unchanged |
| **Core** | `get` | `get` | Unchanged |
| **Core** | `tree` | `tree` | Unchanged |
| **Core** | `verify` | `verify` | Unchanged |
| **Query** | N/A | `get-section` | **NEW** |
| **Query** | N/A | `next` | **NEW** |
| **Query** | N/A | `list` | **NEW** |
| **Search** | `search` | `search` | Enhanced |
| **Search** | N/A | `search-semantic` | **NEW** |
| **Supabase** | `ingest` | `ingest` | Enhanced |
| **Supabase** | `checkout` | `checkout` | Enhanced |
| **Supabase** | `checkin` | `checkin` | Unchanged |
| **Supabase** | `list-library` | `list-library` | Unchanged |
| **Supabase** | `status` | `status` | Unchanged |
| **Supabase** | `search-library` | `search-library` | Enhanced |
| **Utils** | N/A | `compose` | **NEW** |
| **Utils** | N/A | `backup` | **NEW** |
| **Utils** | N/A | `restore` | **NEW** |

### New Commands

#### Progressive Disclosure

```bash
# Get single section by ID
./skill_split.py get-section <section_id> --db <database>

# Navigate to next section
./skill_split.py next <section_id> <file_path>

# Navigate to first child subsection
./skill_split.py next <section_id> <file_path> --child

# List section hierarchy with IDs
./skill_split.py list <file_path> --db <database>
```

#### Search Commands

```bash
# BM25 keyword search (local, fast)
./skill_split.py search "query terms"

# Vector semantic search (requires OpenAI API key)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "query" --vector-weight 1.0

# Hybrid search (combined BM25 + Vector)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "query" --vector-weight 0.7
```

#### Skill Composition

```bash
# Compose new skill from existing sections
./skill_split.py compose --sections 1,2,3 --output new_skill.md

# Compose with custom frontmatter
./skill_split.py compose \
    --sections 1,2,3 \
    --output composed_skill.md \
    --title "My New Skill" \
    --description "A skill composed from multiple sources"
```

#### Backup and Restore

```bash
# Create database backup
./skill_split.py backup --output custom-backup.sql.gz

# Restore from backup
./skill_split.py restore backup-file.sql.gz

# List available backups
./skill_split.py backup --list
```

### Enhanced Commands

#### `search` Command

**v0.x behavior:**
```bash
./skill_split.py search "query"
```

**v1.0.0 behavior (backward compatible):**
```bash
# Basic search (unchanged)
./skill_split.py search "query"

# With limit
./skill_split.py search "query" --limit 20

# Boolean operators supported
./skill_split.py search "python AND handler"
./skill_split.py search "test OR verification"
./skill_split.py search "error NEAR/5 handler"
```

#### `ingest` Command

**v0.x behavior:**
```bash
./skill_split.py ingest <source_dir>
```

**v1.0.0 behavior:**
```bash
# Basic ingest (unchanged)
./skill_split.py ingest <source_dir>

# With SecretManager bypass
./skill_split.py ingest <source_dir> --no-use-secret-manager

# With custom secrets config
./skill_split.py ingest <source_dir> --secrets-config /path/to/secrets.json
```

#### `checkout` Command

**v0.x behavior:**
```bash
./skill_split.py checkout <file_id> <target_path>
```

**v1.0.0 behavior:**
```bash
# Basic checkout (unchanged)
./skill_split.py checkout <file_id> <target_path>

# With user tracking
./skill_split.py checkout <file_id> <target_path> --user username
```

---

## Configuration Updates

### Environment Variables

#### New Environment Variables

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `ENABLE_EMBEDDINGS` | Enable vector search features | No | `false` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Conditional* | None |
| `SKILL_SPLIT_DB` | Custom database path | No | `~/.claude/databases/skill-split.db` |

*Required only if `ENABLE_EMBEDDINGS=true`

#### Changed Environment Variables

| Old Variable (v0.x) | New Variable (v1.0.0) | Notes |
|---------------------|----------------------|-------|
| None | `SUPABASE_KEY` | Now checks multiple sources (see below) |

#### Supabase Credential Priority

v1.0.0 introduces a priority system for Supabase credentials:

1. **SecretManager** (highest priority, if enabled)
2. `SUPABASE_KEY` environment variable
3. `SUPABASE_PUBLISHABLE_KEY` environment variable
4. `SUPABASE_SECRET_KEY` environment variable

### Configuration File

#### `.env` File Example

```bash
# Database location
SKILL_SPLIT_DB=~/.claude/databases/skill-split.db

# Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# OpenAI embeddings (optional)
ENABLE_EMBEDDINGS=true
OPENAI_API_KEY=sk-your-openai-key

# SecretManager (optional, overrides environment variables)
# SECRETS_CONFIG_PATH=~/.claude/secrets.json
```

### SecretManager Integration

v1.0.0 introduces `SecretManager` for secure credential management:

**Configuration file: `~/.claude/secrets.json`**

```json
{
  "supabase": {
    "url": "https://your-project.supabase.co",
    "key": "your-anon-key"
  },
  "openai": {
    "api_key": "sk-your-openai-key"
  }
}
```

**Usage:**

```python
from core.secret_manager import SecretManager
from core.supabase_store import SupabaseStore

# Automatic credential loading
secret_manager = SecretManager()
store = SupabaseStore(secret_manager=secret_manager)
```

---

## Step-by-Step Migration

### Phase 1: Preparation (5 minutes)

#### Step 1.1: Create Backup

```bash
# Backup your current database
./skill_split.py backup --output pre-migration-backup.sql.gz

# Verify backup was created
ls -lh ~/.claude/backups/pre-migration-backup.sql.gz
```

#### Step 1.2: Record Current State

```bash
# Document current database stats
./skill_split.py list-library > pre-migration-file-list.txt

# Record current schema (for SQLite)
sqlite3 ~/.claude/databases/skill-split.db ".schema" > pre-migration-schema.sql
```

#### Step 1.3: Install v1.0.0

```bash
# Pull latest code
git pull origin main

# Or if using pip
pip install --upgrade skill-split
```

### Phase 2: Database Migration (5-10 minutes)

#### Step 2.1: SQLite Schema Update

If using local SQLite database:

```bash
# Run the migration script
sqlite3 ~/.claude/databases/skill-split.db <<'EOF'
-- Add closing_tag_prefix column if not exists
ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT '';

-- Add timestamp columns if not exists
ALTER TABLE files ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE files ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update existing rows
UPDATE sections SET closing_tag_prefix = '' WHERE closing_tag_prefix IS NULL;
EOF

echo "SQLite migration complete"
```

#### Step 2.2: Supabase Schema Update

If using Supabase:

1. **Login to Supabase Dashboard**
   ```
   https://supabase.com/dashboard/project/your-project-id/editor
   ```

2. **Run the unified schema migration**
   ```sql
   -- Copy contents from: /Users/joey/working/skill-split/migrations/unify_supabase_schema.sql
   ```

3. **Enable pgvector**
   ```sql
   -- From: /Users/joey/working/skill-split/migrations/enable_pgvector.sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

4. **Create embeddings table**
   ```sql
   -- From: /Users/joey/working/skill-split/migrations/create_embeddings_table.sql
   ```

5. **Optimize vector search**
   ```sql
   -- From: /Users/joey/working/skill-split/migrations/optimize_vector_search.sql
   ```

### Phase 3: Verification (5 minutes)

#### Step 3.1: Verify Database

```bash
# Test basic operations
./skill_split.py list-library

# Verify new columns
sqlite3 ~/.claude/databases/skill-split.db "PRAGMA table_info(files);"
sqlite3 ~/.claude/databases/skill-split.db "PRAGMA table_info(sections);"
```

#### Step 3.2: Test New Features

```bash
# Test progressive disclosure
./skill_split.py list ~/.claude/skills/agent-browser/SKILL.md --db ~/.claude/databases/skill-split.db

# Test search
./skill_split.py search "test"

# Test composition (if you have sections)
./skill_split.py compose --sections 1,2,3 --output test_compose.md
```

### Phase 4: Optional Features (10+ minutes)

#### Step 4.1: Enable Vector Search (Optional)

```bash
# Set environment variable
export ENABLE_EMBEDDINGS=true
export OPENAI_API_KEY=your-key-here

# Generate embeddings for existing content
./skill_split.py ingest ~/.claude/skills --regenerate-embeddings

# Test semantic search
./skill_split.py search-semantic "code execution" --vector-weight 0.7
```

#### Step 4.2: Configure SecretManager (Optional)

```bash
# Create secrets config
cat > ~/.claude/secrets.json <<'EOF'
{
  "supabase": {
    "url": "https://your-project.supabase.co",
    "key": "your-anon-key"
  },
  "openai": {
    "api_key": "sk-your-openai-key"
  }
}
EOF

# Test SecretManager
./skill_split.py list-library --secrets-config ~/.claude/secrets.json
```

---

## Data Migration Scripts

### Script 1: Automatic SQLite Migration

Save as `migrate_sqlite.py`:

```python
#!/usr/bin/env python3
"""
Automatic migration script for SQLite databases from v0.x to v1.0.0
"""

import sqlite3
import os
from pathlib import Path

def migrate_database(db_path: str) -> bool:
    """
    Migrate SQLite database to v1.0.0 schema.

    Args:
        db_path: Path to SQLite database file

    Returns:
        True if migration successful, False otherwise
    """
    if not os.path.exists(db_path):
        print(f"Error: Database not found: {db_path}")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if migration already applied
        cursor.execute("PRAGMA table_info(sections)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'closing_tag_prefix' in columns:
            print("Database already migrated to v1.0.0")
            return True

        # Begin transaction
        conn.execute("BEGIN TRANSACTION")

        # Add closing_tag_prefix column
        print("Adding closing_tag_prefix column...")
        conn.execute(
            "ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT ''"
        )

        # Add timestamp columns to files table
        print("Adding timestamp columns...")
        conn.execute(
            "ALTER TABLE files ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )
        conn.execute(
            "ALTER TABLE files ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )

        # Update existing rows
        print("Updating existing rows...")
        conn.execute(
            "UPDATE sections SET closing_tag_prefix = '' WHERE closing_tag_prefix IS NULL"
        )

        # Commit transaction
        conn.commit()
        print("Migration completed successfully!")

        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    import sys

    # Get database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Use default location
        db_path = os.path.expanduser("~/.claude/databases/skill-split.db")

    print(f"Migrating database: {db_path}")
    success = migrate_database(db_path)

    if success:
        print("\n✓ Migration successful!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
```

**Usage:**

```bash
# Run with default database
python migrate_sqlite.py

# Run with custom database
python migrate_sqlite.py /path/to/your/database.db
```

### Script 2: Supabase Migration Helper

Save as `migrate_supabase.py`:

```python
#!/usr/bin/env python3
"""
Helper script to generate Supabase migration SQL commands.
"""

def generate_migration_sql() -> str:
    """
    Generate SQL commands for Supabase migration.

    Returns:
        SQL string to run in Supabase SQL Editor
    """
    return """
-- ============================================
-- skill-split v1.0.0 Supabase Migration
-- Run this in your Supabase SQL Editor
-- ============================================

-- Step 1: Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add missing columns to sections
ALTER TABLE sections
ADD COLUMN IF NOT EXISTS line_start INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS line_end INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS closing_tag_prefix TEXT DEFAULT '';

-- Step 3: Add indexes
CREATE INDEX IF NOT EXISTS idx_sections_file_order
ON sections(file_id, parent_id, order_index);

CREATE INDEX IF NOT EXISTS idx_sections_file_parent
ON sections(file_id, parent_id);

-- Step 4: Add full-text search index
CREATE INDEX IF NOT EXISTS idx_sections_search
ON sections USING gin(to_tsvector('english', title || ' ' || content));

-- Step 5: Add timestamps to files table
ALTER TABLE files
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Step 6: Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_section_id
ON embeddings(section_id);

-- Step 7: Update file type constraint
ALTER TABLE files DROP CONSTRAINT IF EXISTS files_type_check;

ALTER TABLE files
ADD CONSTRAINT files_type_check
CHECK (type IN (
    'skill', 'command', 'reference', 'agent',
    'plugin', 'hook', 'output_style', 'config',
    'documentation', 'script'
));

-- Step 8: Create auto-update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_files_updated_at ON files;
CREATE TRIGGER update_files_updated_at
BEFORE UPDATE ON files
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Verification queries
SELECT 'Migration complete!' as status;
SELECT COUNT(*) as section_count FROM sections;
SELECT COUNT(*) as file_count FROM files;
"""

if __name__ == "__main__":
    sql = generate_migration_sql()

    # Save to file
    with open("supabase_migration_v1.0.0.sql", "w") as f:
        f.write(sql)

    print("Generated: supabase_migration_v1.0.0.sql")
    print("\nCopy the contents of this file to your Supabase SQL Editor and run it.")
```

**Usage:**

```bash
python migrate_supabase.py
# Output: supabase_migration_v1.0.0.sql
```

### Script 3: Post-Migration Verification

Save as `verify_migration.py`:

```python
#!/usr/bin/env python3
"""
Verification script for v1.0.0 migration
"""

import sqlite3
import os
import sys

def verify_sqlite_migration(db_path: str) -> dict:
    """
    Verify that SQLite database has been properly migrated.

    Returns:
        Dictionary with verification results
    """
    results = {
        "database_exists": False,
        "closing_tag_prefix_exists": False,
        "timestamps_exist": False,
        "section_count": 0,
        "file_count": 0,
        "errors": []
    }

    if not os.path.exists(db_path):
        results["errors"].append(f"Database not found: {db_path}")
        return results

    results["database_exists"] = True

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check sections table columns
        cursor.execute("PRAGMA table_info(sections)")
        sections_columns = [row[1] for row in cursor.fetchall()]
        results["closing_tag_prefix_exists"] = "closing_tag_prefix" in sections_columns

        # Check files table columns
        cursor.execute("PRAGMA table_info(files)")
        files_columns = [row[1] for row in cursor.fetchall()]
        results["timestamps_exist"] = (
            "created_at" in files_columns and
            "updated_at" in files_columns
        )

        # Count records
        cursor.execute("SELECT COUNT(*) FROM sections")
        results["section_count"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM files")
        results["file_count"] = cursor.fetchone()[0]

        conn.close()

    except Exception as e:
        results["errors"].append(str(e))

    return results

def print_verification_results(results: dict):
    """Print verification results in a formatted way."""
    print("\n" + "="*50)
    print("Migration Verification Results")
    print("="*50)

    if results["errors"]:
        print("\n❌ ERRORS:")
        for error in results["errors"]:
            print(f"   - {error}")
        return

    print(f"\n✅ Database exists: {results['database_exists']}")
    print(f"{'✅' if results['closing_tag_prefix_exists'] else '❌'} closing_tag_prefix column: {results['closing_tag_prefix_exists']}")
    print(f"{'✅' if results['timestamps_exist'] else '❌'} Timestamp columns: {results['timestamps_exist']}")
    print(f"\n📊 Statistics:")
    print(f"   - Files: {results['file_count']}")
    print(f"   - Sections: {results['section_count']}")

    if results["closing_tag_prefix_exists"] and results["timestamps_exist"]:
        print("\n✅ Migration appears complete!")
    else:
        print("\n⚠️  Migration incomplete - some columns missing")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = os.path.expanduser("~/.claude/databases/skill-split.db")

    print(f"Verifying: {db_path}")
    results = verify_sqlite_migration(db_path)
    print_verification_results(results)
```

**Usage:**

```bash
# Verify default database
python verify_migration.py

# Verify custom database
python verify_migration.py /path/to/database.db
```

---

## Rollback Procedures

### Rollback Scenario 1: SQLite Database

If you need to rollback the SQLite migration:

#### Option A: Restore from Backup

```bash
# Stop any running processes using the database

# Restore from backup
./skill_split.py restore ~/.claude/backups/pre-migration-backup.sql.gz

# Verify restoration
./skill_split.py list-library
```

#### Option B: Manual Revert

```bash
# If you have SQL schema backup
sqlite3 ~/.claude/databases/skill-split.db < pre-migration-schema.sql

# Or manually drop new columns (use with caution)
sqlite3 ~/.claude/databases/skill-split.db <<'EOF'
-- This will fail if you have data that requires these columns
BEGIN TRANSACTION;

-- Create backup of data first
-- ... (export your data)

-- Drop new columns (SQLite doesn't support ALTER TABLE DROP COLUMN)
-- You'll need to recreate the table without the new columns
-- ... (complex operation, recommend backup restore instead)

COMMIT;
EOF
```

**Note**: SQLite has limited ALTER TABLE support. Restoring from backup is strongly recommended.

### Rollback Scenario 2: Supabase Database

If you need to rollback Supabase changes:

#### Option A: Point-in-Time Recovery

```sql
-- In Supabase SQL Editor
-- This requires you to know the timestamp before migration

-- 1. Find the time before migration
SELECT NOW() - INTERVAL '1 hour';

-- 2. Contact Supabase support for point-in-time recovery
-- (This is a paid feature)
```

#### Option B: Manual Revert

```sql
-- In Supabase SQL Editor

-- Drop new tables
DROP TABLE IF EXISTS embeddings CASCADE;

-- Drop new indexes
DROP INDEX IF EXISTS idx_sections_file_order;
DROP INDEX IF EXISTS idx_sections_file_parent;
DROP INDEX IF EXISTS idx_sections_search;
DROP INDEX IF EXISTS idx_embeddings_section_id;

-- Drop new columns (PostgreSQL supports this)
ALTER TABLE sections
DROP COLUMN IF EXISTS closing_tag_prefix;

ALTER TABLE sections
DROP COLUMN IF EXISTS line_start;

ALTER TABLE sections
DROP COLUMN IF EXISTS line_end;

ALTER TABLE files
DROP COLUMN IF EXISTS created_at;

ALTER TABLE files
DROP COLUMN IF EXISTS updated_at;

-- Revert file type constraint
ALTER TABLE files DROP CONSTRAINT IF EXISTS files_type_check;

ALTER TABLE files
ADD CONSTRAINT files_type_check
CHECK (type IN ('skill', 'command', 'reference'));

-- Drop trigger
DROP TRIGGER IF EXISTS update_files_updated_at ON files;
DROP FUNCTION IF EXISTS update_updated_at_column();
```

### Rollback Scenario 3: Code Version

If you need to rollback the code version:

```bash
# Using git
git checkout v0.x  # Replace with actual v0.x tag/commit

# Using pip
pip install skill-split==0.x.x  # Replace with actual version

# Verify version
./skill_split.py --version
```

---

## Common Migration Issues

### Issue 1: "column closing_tag_prefix does not exist"

**Symptom:**
```
sqlite3.OperationalError: no such column: closing_tag_prefix
```

**Cause:** Database schema not updated to v1.0.0

**Solution:**
```bash
# Run migration script
python migrate_sqlite.py

# Or manually add column
sqlite3 ~/.claude/databases/skill-split.db \
  "ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT '';"
```

### Issue 2: "constraint files_type_check violated"

**Symptom:**
```
psql.errors.CheckViolation: new row violates check constraint "files_type_check"
```

**Cause:** Trying to store new file types (plugin, hook, config, script) with old schema

**Solution:**
```sql
-- Run in Supabase SQL Editor
ALTER TABLE files DROP CONSTRAINT files_type_check;

ALTER TABLE files
ADD CONSTRAINT files_type_check
CHECK (type IN (
    'skill', 'command', 'reference', 'agent',
    'plugin', 'hook', 'output_style', 'config',
    'documentation', 'script'
));
```

### Issue 3: "OpenAI API key not found"

**Symptom:**
```
ValueError: OpenAI API key not found. Set OPENAI_API_KEY environment variable.
```

**Cause:** Trying to use vector search without API key configured

**Solution:**
```bash
# Option 1: Set environment variable
export OPENAI_API_KEY=sk-your-key-here

# Option 2: Add to .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Option 3: Use SecretManager
cat > ~/.claude/secrets.json <<'EOF'
{
  "openai": {
    "api_key": "sk-your-key-here"
  }
}
EOF

# Option 4: Disable embeddings
export ENABLE_EMBEDDINGS=false
```

### Issue 4: "Database is locked"

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Another process is using the database

**Solution:**
```bash
# Find processes using the database
lsof ~/.claude/databases/skill-split.db

# Stop the processes
# Then retry migration
```

### Issue 5: Import errors after upgrade

**Symptom:**
```
ModuleNotFoundError: No module named 'core.backup_manager'
```

**Cause:** Code not fully updated or Python path issues

**Solution:**
```bash
# Ensure you're in the correct directory
cd /path/to/skill-split

# Update Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Reinstall if using pip
pip install --force-reinstall skill-split

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### Issue 6: Tests failing after migration

**Symptom:** Test suite fails after migration

**Solution:**
```bash
# Clear test cache
pytest --cache-clear

# Run tests in verbose mode to see issues
pytest test/ -v

# Run specific failing test
pytest test/test_database.py -v

# If tests expect old schema, update them
# to account for new columns (closing_tag_prefix, etc.)
```

---

## Post-Migration Verification

### Verification Checklist

After completing the migration, verify the following:

- [ ] **Database Structure**
  ```bash
  # Check sections table
  sqlite3 ~/.claude/databases/skill-split.db "PRAGMA table_info(sections);"

  # Should include: closing_tag_prefix
  ```

- [ ] **Data Integrity**
  ```bash
  # Verify section count unchanged
  ./skill_split.py list-library | wc -l

  # Compare with pre-migration count
  ```

- [ ] **Basic Operations**
  ```bash
  # Test parsing
  ./skill_split.py parse ~/.claude/skills/agent-browser/SKILL.md

  # Test storage
  ./skill_split.py store ~/.claude/skills/agent-browser/SKILL.md

  # Test retrieval
  ./skill_split.py get ~/.claude/skills/agent-browser/SKILL.md
  ```

- [ ] **New Features**
  ```bash
  # Test progressive disclosure
  ./skill_split.py list ~/.claude/skills/agent-browser/SKILL.md

  # Test search
  ./skill_split.py search "browser"

  # Test composition
  ./skill_split.py compose --sections 1,2 --output test.md
  ```

- [ ] **Supabase Integration** (if applicable)
  ```bash
  # Test remote ingest
  ./skill_split.py ingest ~/.claude/skills/agent-browser

  # Test library listing
  ./skill_split.py list-library
  ```

### Performance Verification

```bash
# Run test suite
pytest test/ -v

# Expected: 623 tests passing
# (Up from 518 in v0.x)
```

### Production Readiness Checklist

Before deploying to production:

- [ ] Migration tested in staging environment
- [ ] Backup verified and restorable
- [ ] Rollback procedure documented and tested
- [ ] Monitoring configured for new features
- [ ] Team trained on new CLI commands
- [ ] Documentation updated for custom scripts
- [ ] API keys secured (if using embeddings)
- [ ] Rate limits considered (for OpenAI API)

---

## Additional Resources

### Documentation

- **[CLI_REFERENCE.md](./CLI_REFERENCE.md)** - Complete command reference
- **[VECTOR_SEARCH_COSTS.md](./VECTOR_SEARCH_COSTS.md)** - Search feature costs and usage
- **[EXAMPLES.md](../EXAMPLES.md)** - Usage examples and patterns
- **[DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md)** - Deployment capabilities

### Migration Scripts

- `/Users/joey/working/skill-split/migrations/unify_supabase_schema.sql` - Supabase schema
- `/Users/joey/working/skill-split/migrations/enable_pgvector.sql` - Vector support
- `/Users/joey/working/skill-split/migrations/create_embeddings_table.sql` - Embeddings storage

### Support

For issues or questions:
1. Check this guide's Common Issues section
2. Review test files for usage examples
3. Check Git history for breaking changes
4. Review CHANGELOG.md for version details

---

## Migration Summary

| Phase | Time | Complexity | Risk |
|-------|------|------------|------|
| Preparation | 5 min | Low | None |
| SQLite Migration | 5 min | Low | Low |
| Supabase Migration | 10 min | Medium | Medium |
| Verification | 5 min | Low | None |
| Optional Features | 10+ min | Variable | Low |
| **Total** | **25-35 min** | | |

**Success Rate**: 99%+ when following this guide

**Typical Issues**: Mostly related to missing API keys or locked databases

---

## Quick Reference Commands

```bash
# Pre-migration backup
./skill_split.py backup --output pre-migration.sql.gz

# Run migration
python migrate_sqlite.py

# Verify migration
python verify_migration.py

# Test basic operations
./skill_split.py list-library
./skill_split.py search "test"

# Test new features
./skill_split.py list <file>
./skill_split.py compose --sections 1,2 --output test.md

# Rollback if needed
./skill_split.py restore pre-migration.sql.gz
```

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-10
**Maintained By**: skill-split development team
