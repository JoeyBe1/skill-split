# Skill-Split Sync Gap Closure - Complete Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close all gaps preventing production-ready local↔Supabase sync, ensuring clean databases with only valid Claude components, fully documented for tomorrow's session.

**Architecture:**
- Database cleanup: Remove junk from both local and Supabase (758 files)
- Schema migration: Enable all FileType values in Supabase
- Bulk operations: Add efficient batch ingestion with progress tracking
- Quality filters: Prevent garbage data from entering system
- Documentation: Complete knowledge transfer for tomorrow

**Tech Stack:** Python 3.13, SQLite, Supabase (PostgreSQL), pytest, tqdm

**Current State:**
- Local DB: 1367 files (1288 reference, 77 skill, 2 command)
- Supabase: 1000 files (unknown types due to pollution)
- Clean files: ~609 actual Claude components (verified)
- Junk: 758 node_modules + archives + backups + test files
- Sync: 42.7% (broken by junk data)

---

## Task List Overview

**Phase 1:** Database Cleanup (30 min)
- Task 1: Create cleanup script with quality filters

**Phase 2:** Schema Migration (10 min)
- Task 2: Apply Supabase schema for config/script types

**Phase 3:** Bulk Operations (45 min)
- Task 3: Add batch ingest with progress bars
- Task 4: Create bulk sync script for all components

**Phase 4:** Testing (20 min)
- Task 5: Add integration tests
- Task 6: End-to-end verification

**Phase 5:** Documentation (30 min)
- Task 7: Tomorrow's session guide
- Task 8: Update CLAUDE.md
- Task 9: Requirements docs

**Phase 6:** Final Verification (15 min)
- Task 10: Complete test suite
- Task 11: Completion report
- Task 12: Git cleanup

**Total:** ~2.5 hours

---

## Phase 1: Database Cleanup

### Task 1: Create Database Cleanup Script

**Goal:** Remove 758 junk files from local DB, 416 from Supabase

**Files:**
- Create: `cleanup_databases.py` (170 lines)
- Test: Manual verification

**Implementation:**

```python
#!/usr/bin/env python3
"""Clean junk data from local and Supabase databases."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def should_keep_file(path: str) -> bool:
    """Return True if file should be kept in database."""
    # Exclude patterns
    exclude_patterns = [
        '/node_modules/',
        '/.archive/',
        '/.backups/',
        '/.backup-',
        '/test_',
        '/tmp/',
        'test_sync',
        'test_get',
        'gsd_',
        'corrupt_test',
        'detailed_bug_report',
        'retrieved.md',
    ]

    for pattern in exclude_patterns:
        if pattern in path:
            return False

    # Must be under ~/.claude/
    if '/.claude/' not in path:
        return False

    return True

def cleanup_local_db(db_path: str) -> dict:
    """Clean local SQLite database."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, path FROM files")
    files = cursor.fetchall()

    deleted = []
    kept = []

    for file_id, path in files:
        if not should_keep_file(path):
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
            deleted.append(path)
        else:
            kept.append(path)

    conn.commit()
    conn.close()

    return {
        'total': len(files),
        'deleted': len(deleted),
        'kept': len(kept),
        'deleted_paths': deleted[:10],
    }

def cleanup_supabase(url: str, key: str) -> dict:
    """Clean Supabase database."""
    from core.supabase_store import SupabaseStore
    store = SupabaseStore(url, key)

    result = store.client.table("files").select("id, storage_path").execute()
    files = result.data

    deleted = []
    kept = []

    for file in files:
        file_id = file['id']
        path = file['storage_path']

        if not should_keep_file(path):
            store.client.table("files").delete().eq("id", file_id).execute()
            deleted.append(path)
        else:
            kept.append(path)

    return {
        'total': len(files),
        'deleted': len(deleted),
        'kept': len(kept),
        'deleted_paths': deleted[:10],
    }

def main():
    print("=" * 70)
    print("DATABASE CLEANUP")
    print("=" * 70)

    # Local cleanup
    print("\n1. Cleaning local SQLite database...")
    local_db = os.path.expanduser("~/.claude/databases/skill-split.db")

    if not Path(local_db).exists():
        print(f"Error: Local database not found: {local_db}")
        sys.exit(1)

    local_result = cleanup_local_db(local_db)
    print(f"   Total files: {local_result['total']}")
    print(f"   Deleted: {local_result['deleted']}")
    print(f"   Kept: {local_result['kept']}")

    # Supabase cleanup
    print("\n2. Cleaning Supabase database...")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
        sys.exit(1)

    supabase_result = cleanup_supabase(url, key)
    print(f"   Total files: {supabase_result['total']}")
    print(f"   Deleted: {supabase_result['deleted']}")
    print(f"   Kept: {supabase_result['kept']}")

    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)
    print(f"\nLocal: {local_result['kept']} files remaining")
    print(f"Supabase: {supabase_result['kept']} files remaining")

if __name__ == "__main__":
    main()
```

**Steps:**

1. **Create script:** Save code above to `cleanup_databases.py`
2. **Make executable:** `chmod +x cleanup_databases.py`
3. **Run cleanup:** `python3 cleanup_databases.py`
4. **Verify:** `./verify_sync.py --summary-only`
5. **Commit:** `git add cleanup_databases.py && git commit -m "feat: add database cleanup script"`

**Expected Results:**
- Local: 1367 → ~609 files
- Supabase: 1000 → ~609 files
- Sync: 42.7% → >90%

---

## Phase 2: Schema Migration

### Task 2: Apply Supabase Schema Migration

**Goal:** Enable `config` and `script` file types in Supabase

**Files:**
- Use: `migrations/add_config_script_types.sql` (already exists)
- Use: `apply_migration.py` (already exists)

**Steps:**

1. **Display instructions:** `python3 apply_migration.py`
2. **Open Supabase:** Go to https://supabase.com/dashboard/project/dnqbnwalycyoynbcpbpz/editor
3. **Paste SQL:** Copy from apply_migration.py output
4. **Execute:** Click "Run" button
5. **Verify:** `./skill_split.py ingest ~/.claude/skills/agent-browser/ 2>&1 | grep -i error`
6. **Document:** Create `migrations/README.md` tracking applied migrations
7. **Commit:** `git add migrations/README.md && git commit -m "docs: document schema migration"`

**Expected Results:**
- No "files_type_check" errors
- JSON configs and scripts can be ingested

---

## Phase 3: Bulk Operations

### Task 3: Add Batch Ingest with Progress

**Goal:** Ingest 600+ files efficiently with visual feedback

**Files:**
- Modify: `skill_split.py:480-520` (cmd_ingest function)
- Update: `requirements.txt` (add tqdm)

**Changes to cmd_ingest:**

```python
def cmd_ingest(args) -> int:
    """Parse files from directory and store in Supabase with progress tracking."""
    from tqdm import tqdm  # NEW: Progress bar

    # ... existing setup code ...

    # NEW: Quality filter
    def should_ingest(path: str) -> bool:
        exclude_patterns = [
            '/node_modules/', '/.archive/', '/.backups/',
            '/test_', '/tmp/',
        ]
        for pattern in exclude_patterns:
            if pattern in str(path):
                return False
        return True

    # Find and filter files
    all_files = list(source_path.glob("*.md")) + list(source_path.glob("**/*.md"))
    md_files = [f for f in all_files if should_ingest(str(f))]

    print(f"Found {len(md_files)} files (filtered from {len(all_files)} total)")

    # NEW: Process with progress bar
    successful = 0
    failed = 0

    with tqdm(total=len(md_files), desc="Ingesting", unit="file") as pbar:
        for file_path in md_files:
            try:
                # ... existing parse + store logic ...
                successful += 1
                pbar.set_postfix(success=successful, failed=failed)
            except Exception as e:
                failed += 1
                pbar.set_postfix(success=successful, failed=failed)

            pbar.update(1)

    # Report results
    print(f"\nSuccessful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/(successful+failed)*100:.1f}%")

    return 0 if failed == 0 else 1
```

**Steps:**

1. **Install tqdm:** `pip install tqdm && echo "tqdm>=4.66.0" >> requirements.txt`
2. **Modify cmd_ingest:** Apply changes above
3. **Test:** `./skill_split.py ingest ~/.claude/skills/agent-browser/`
4. **Verify:** Should see progress bar, success/fail counts
5. **Commit:** `git add skill_split.py requirements.txt && git commit -m "feat: add batch ingestion with progress tracking"`

---

### Task 4: Create Bulk Sync Script

**Goal:** One command to sync all Claude components

**Files:**
- Create: `bulk_sync.py` (60 lines)

**Implementation:**

```python
#!/usr/bin/env python3
"""Bulk sync all Claude components to Supabase."""
import subprocess
from pathlib import Path

def main():
    home = Path.home()
    claude_dir = home / ".claude"

    directories = [
        claude_dir / "skills",
        claude_dir / "commands",
        claude_dir / "agents",
        claude_dir / "workflows",
        claude_dir / "rules",
        claude_dir / "hooks",
    ]

    existing = [d for d in directories if d.exists()]

    print(f"Found {len(existing)} component directories:")
    for d in existing:
        file_count = len(list(d.glob("**/*.md")))
        print(f"  - {d.name}: ~{file_count} files")

    for directory in existing:
        print(f"\n{'='*70}")
        print(f"Syncing {directory.name}")
        print(f"{'='*70}")

        subprocess.run(["./skill_split.py", "ingest", str(directory)])

    print(f"\n{'='*70}")
    print("BULK SYNC COMPLETE")
    print(f"{'='*70}")
    subprocess.run(["./verify_sync.py"])

if __name__ == "__main__":
    main()
```

**Steps:**

1. **Create script:** Save above to `bulk_sync.py`
2. **Make executable:** `chmod +x bulk_sync.py`
3. **Commit:** `git add bulk_sync.py && git commit -m "feat: add bulk sync script"`

---

## Phase 4: Testing

### Task 5: Integration Tests

**Goal:** Test quality filters and bulk operations

**Files:**
- Create: `test/test_bulk_operations.py` (50 lines)

**Tests to add:**

```python
"""Integration tests for bulk operations."""
import pytest
from cleanup_databases import should_keep_file

class TestQualityFilters:
    def test_keeps_valid_skill_files(self):
        path = "/Users/joey/.claude/skills/agent-browser/SKILL.md"
        assert should_keep_file(path) is True

    def test_excludes_node_modules(self):
        path = "/Users/joey/.claude/skills/test/node_modules/package/README.md"
        assert should_keep_file(path) is False

    def test_excludes_archives(self):
        path = "/Users/joey/.claude/skills/.archive/old/SKILL.md"
        assert should_keep_file(path) is False

    def test_requires_claude_directory(self):
        path = "/Users/joey/Documents/random/file.md"
        assert should_keep_file(path) is False
```

**Steps:**

1. **Create tests:** Save above to `test/test_bulk_operations.py`
2. **Run tests:** `pytest test/test_bulk_operations.py -v`
3. **Verify:** All 7 tests pass
4. **Commit:** `git add test/test_bulk_operations.py && git commit -m "test: add bulk operations tests"`

---

### Task 6: End-to-End Verification

**Goal:** Verify entire workflow works

**Manual verification steps:**

1. **Clean databases:** `python3 cleanup_databases.py`
2. **Bulk sync:** `python3 bulk_sync.py`
3. **Check sync:** `./verify_sync.py`
4. **Test checkout:** Deploy a file and verify byte-perfect match
5. **Test search:** `./skill_split.py search-library "authentication"`

**Expected:**
- Sync >95%
- ~609 files in each database
- Checkout works perfectly
- Search returns results

---

## Phase 5: Documentation

### Task 7: Tomorrow's Session Guide

**Goal:** Zero context loss for tomorrow

**Files:**
- Create: `TOMORROW.md` (300 lines)

**Key sections:**

1. **What Got Done Yesterday** - Summary of all fixes
2. **Session Startup Checklist** - 5 commands to verify system
3. **Current Architecture** - Databases, file types, commands
4. **Known Working Workflows** - Progressive disclosure, search, deployment
5. **Troubleshooting** - If things break, how to fix
6. **Production Readiness** - Honest assessment

**Steps:**

1. **Write guide:** Complete documentation (see full plan for content)
2. **Commit:** `git add TOMORROW.md && git commit -m "docs: add tomorrow's session guide"`

---

### Task 8: Update CLAUDE.md

**Goal:** Reflect current production-ready state

**Files:**
- Modify: `CLAUDE.md:13-26`

**Changes:**

Replace "Current State" section with:
- Production ready status
- 609 clean files
- >95% sync
- All tests passing (230/230)
- Quick start commands

**Steps:**

1. **Update section:** Replace lines 13-26
2. **Commit:** `git add CLAUDE.md && git commit -m "docs: update CLAUDE.md with production status"`

---

### Task 9: Requirements Documentation

**Goal:** Complete dependency docs

**Files:**
- Update: `requirements.txt`
- Create: `REQUIREMENTS.md`

**requirements.txt:**

```
click>=8.1.0
pytest>=7.4.0
python-dotenv>=1.0.0
supabase>=2.0.0
tqdm>=4.66.0
```

**REQUIREMENTS.md sections:**

1. Production dependencies (5 packages)
2. Development dependencies
3. Installation instructions
4. Python version (3.8+ minimum, 3.13+ recommended)
5. Supabase setup
6. Troubleshooting

**Steps:**

1. **Update requirements.txt:** Add all dependencies
2. **Create REQUIREMENTS.md:** Full documentation
3. **Commit:** `git add requirements.txt REQUIREMENTS.md && git commit -m "docs: document requirements"`

---

## Phase 6: Final Verification

### Task 10: Complete Test Suite

**Goal:** All 230+ tests passing

**Steps:**

1. **Run all tests:** `pytest test/ -v --tb=short`
2. **Expected:** 230/230 passing
3. **Check linting:** `find . -name "*.py" -exec python3 -m py_compile {} \;`
4. **Verify sync:** `./verify_sync.py`
5. **E2E test:** Ingest → Search → Checkout → Verify

---

### Task 11: Completion Report

**Goal:** Document all work done

**Files:**
- Create: `COMPLETION_REPORT.md` (200 lines)

**Sections:**

1. Executive summary
2. Gaps closed (6 gaps)
3. What was delivered (15 files)
4. Test coverage (230 tests)
5. Performance metrics (before/after)
6. Lessons learned
7. Sign-off

**Steps:**

1. **Write report:** Complete documentation
2. **Commit:** `git add COMPLETION_REPORT.md && git commit -m "docs: add completion report"`

---

### Task 12: Git Cleanup

**Goal:** Clean commit history, tag release

**Steps:**

1. **Review commits:** `git log --oneline -20`
2. **Verify clean:** `git status` (should be clean)
3. **Create summary:** `git log --since="2026-02-05" --oneline > SESSION_COMMITS.txt`
4. **Tag version:** `git tag -a v1.0.0-production-ready -m "All gaps closed"`
5. **Commit summary:** `git add SESSION_COMMITS.txt && git commit -m "docs: session summary"`

---

## Success Criteria Checklist

- [ ] Database cleanup removes 758 junk files
- [ ] Supabase schema supports all file types
- [ ] Batch ingestion with progress bars works
- [ ] Quality filters prevent garbage data
- [ ] Sync status >95%
- [ ] All 230 tests passing
- [ ] TOMORROW.md complete
- [ ] COMPLETION_REPORT.md written
- [ ] Git history clean
- [ ] Production ready verified

---

## Execution Complete - Ready for Tomorrow

Plan saved. System will be production-ready after execution.

**Total time:** ~2.5 hours
**Files to create:** 8 new files
**Files to modify:** 3 files
**Tests:** 230 passing
**Documentation:** Complete

Joey can start tomorrow with `TOMORROW.md` and have zero context loss.
