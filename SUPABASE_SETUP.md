# Supabase Setup Guide

## Quick Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Save your project URL and anon key

### 2. Run Schema

Copy and run `/Users/joey/working/skill-split/schema.sql` in Supabase SQL Editor:

**4 Tables:**
- `files` - File metadata (name, type, hash, frontmatter)
- `sections` - Hierarchical content structure
- `checkouts` - Track active deployments
- `deployment_paths` - Canonical paths for each file type

**Pre-populated deployment paths:**
- `skill` → `~/.claude/skills/`
- `command` → `~/.claude/commands/`
- `plugin` → `~/.claude/plugins/`
- `reference` → `~/.claude/references/`

### 3. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SKILL_LIBRARY_PATH=~/.skill-library
SKILL_SPLIT_DB=~/.claude/databases/skill-split.db
```

## Table Schemas

### files
```sql
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    storage_path TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('skill', 'command', 'plugin', 'reference')),
    frontmatter TEXT,
    hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### sections
```sql
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL
);
```

### checkouts
```sql
CREATE TABLE checkouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    section_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    user_name TEXT NOT NULL,
    target_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'returned')),
    checked_out_at TIMESTAMPTZ DEFAULT NOW(),
    checked_in_at TIMESTAMPTZ,
    notes TEXT,
    CONSTRAINT file_or_section CHECK (
        (file_id IS NOT NULL AND section_id IS NULL) OR
        (file_id IS NULL AND section_id IS NOT NULL)
    )
);
```

### deployment_paths
```sql
CREATE TABLE deployment_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_type TEXT NOT NULL CHECK (file_type IN ('skill', 'command', 'plugin', 'reference')),
    base_path TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Quick Test Commands

```bash
# 1. Verify connection
python3 -c "from core.supabase_store import SupabaseStore; import os; from dotenv import load_dotenv; load_dotenv(); print('Connected!' if SupabaseStore(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')) else 'Failed')"

# 2. Ingest file to library
./skill_split.py ingest demo/sample_skill.md --name sample_skill

# 3. List library files
./skill_split.py list-library

# 4. Search library
./skill_split.py search-library "usage"

# 5. Checkout file
./skill_split.py checkout <file-id> ~/.claude/skills/test/

# 6. Check status
./skill_split.py status

# 7. Check in file
./skill_split.py checkin ~/.claude/skills/test/
```

## Testing

Run Supabase tests:

```bash
# All Supabase tests
pytest test/test_supabase_store.py -v

# Specific test
pytest test/test_supabase_store.py::TestSupabaseConnection::test_can_connect_to_supabase -v
```

## Troubleshooting

**Connection Error**: Verify URL and key in `.env`
**Table Error**: Re-run `schema.sql` in Supabase SQL Editor
**CASCADE Error**: Tables created in correct order (files → sections → checkouts)

## Commands Reference

| Command | Description |
|---------|-------------|
| `ingest <file>` | Parse and store file in Supabase library |
| `checkout <file-id>` | Deploy file from library to local path |
| `checkin <path>` | Return deployed file to library |
| `list-library` | Show all files in library |
| `search-library <query>` | Search files by name |
| `status` | Show active checkouts |

---

*See [README.md](./README.md) for full CLI documentation*
