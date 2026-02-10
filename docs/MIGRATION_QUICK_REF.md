# Migration Quick Reference Card

**skill-split v0.x → v1.0.0**

---

## Pre-Migration (5 min)

```bash
# 1. Create backup
./skill_split.py backup --output pre-migration.sql.gz

# 2. Record current state
./skill_split.py list-library > pre-migration-files.txt
```

---

## SQLite Migration (5 min)

```bash
# Option 1: Automated (recommended)
python migrations/migrate_sqlite.py

# Option 2: Manual
sqlite3 ~/.claude/databases/skill-split.db <<'EOF'
ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT '';
ALTER TABLE files ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE files ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
UPDATE sections SET closing_tag_prefix = '' WHERE closing_tag_prefix IS NULL;
EOF
```

---

## Supabase Migration (10 min)

```bash
# 1. Generate migration SQL
python migrations/migrate_supabase.py -o migration.sql

# 2. Open Supabase SQL Editor
# https://supabase.com/dashboard/project/YOUR_PROJECT/editor

# 3. Paste and run migration.sql
```

---

## Verification (2 min)

```bash
# Run verification script
python migrations/verify_migration.py

# Expected output:
# ✅ Database: ~/.claude/databases/skill-split.db
# ✅ closing_tag_prefix column: Yes
# ✅ Timestamp columns: Yes
# ✅ Migration appears complete and successful!
```

---

## Test New Features (5 min)

```bash
# Progressive disclosure
./skill_split.py list ~/.claude/skills/agent-browser/SKILL.md

# Search (BM25)
./skill_split.py search "browser"

# Compose skills
./skill_split.py compose --sections 1,2,3 --output test.md
```

---

## Rollback (if needed)

```bash
# SQLite: Restore from backup
./skill_split.py restore pre-migration.sql.gz

# Supabase: Generate and run rollback
python migrations/migrate_supabase.py --rollback -o rollback.sql
# Then run rollback.sql in Supabase SQL Editor
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| `column closing_tag_prefix does not exist` | Run `python migrations/migrate_sqlite.py` |
| `constraint files_type_check violated` | Update Supabase schema |
| `OpenAI API key not found` | Set `OPENAI_API_KEY` or disable embeddings |
| `database is locked` | Close other processes using the database |

---

## Environment Variables

```bash
# Required for vector search (optional)
export ENABLE_EMBEDDINGS=true
export OPENAI_API_KEY=sk-your-key

# Custom database location (optional)
export SKILL_SPLIT_DB=/path/to/database.db

# Supabase (for cloud features)
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-anon-key
```

---

## What's New in v1.0.0

| Feature | Command |
|---------|---------|
| Progressive Disclosure | `list`, `get-section`, `next` |
| BM25 Search | `search "query"` |
| Vector Search | `search-semantic "query"` |
| Skill Composition | `compose --sections 1,2,3` |
| Backup/Restore | `backup`, `restore` |
| Script Handlers | Automatic for `.py`, `.js`, `.ts`, `.sh` |
| Component Handlers | Automatic for `plugin.json`, `hooks.json` |

---

## Migration Timeline

| Phase | Time | Status |
|-------|------|--------|
| Backup | 2 min | ✓ |
| SQLite Migration | 5 min | ✓ |
| Supabase Migration | 10 min | ✓ |
| Verification | 2 min | ✓ |
| Testing | 5 min | ✓ |
| **Total** | **~25 min** | |

---

## Success Indicators

- ✅ 623 tests passing (up from 518)
- ✅ `closing_tag_prefix` column present
- ✅ Timestamp columns present
- ✅ All existing files accessible
- ✅ New commands working

---

## Help Resources

- Full guide: `docs/MIGRATION.md`
- CLI reference: `docs/CLI_REFERENCE.md`
- Migration scripts: `migrations/`
- Test suite: `pytest test/ -v`

---

**Need Help?** Check `docs/MIGRATION.md` Common Issues section
