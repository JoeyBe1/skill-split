---
name: using-skill-split
version: 1.0.0
category: documentation
description: How to use skill-split for progressive disclosure and SkillBank librarian system
triggers:
  - /using-skill-split
  - using-skill-split
---

# Using skill-split

Two systems working together: **Local SQLite** (progressive disclosure) + **Supabase SkillBank** (librarian checkout).

## Quick Reference

### Progressive Disclosure (Local SQLite)

**Purpose**: Load sections incrementally to save tokens

```bash
# Parse and store file
skill-split store ~/.claude/skills/my-skill.md

# View structure (shows section IDs)
skill-split tree ~/.claude/skills/my-skill.md

# Load single section
skill-split get-section ~/.claude/skills/my-skill.md 3

# Search all indexed files
skill-split search "authentication"
```

**Database**: `~/.claude/databases/skill-split.db`

---

### SkillBank Librarian (Supabase)

**Purpose**: Shared library with checkout tracking

```bash
# List library
skill-split list-library

# Checkout to local file
skill-split checkout <uuid> ~/.claude/skills/temp.md --user joey

# See who has what
skill-split status

# Checkin (deletes local file, updates DB)
skill-split checkin ~/.claude/skills/temp.md
```

**Database**: SkillBank on Supabase

---

## Workflows

### Token Savings Workflow

```bash
# 1. Store skill once
skill-split store ~/.claude/skills/creating-output-styles/SKILL.md

# 2. View tree (10 lines instead of 114)
skill-split tree ~/.claude/skills/creating-output-styles/SKILL.md

# 3. Load only section 3
skill-split get-section ~/.claude/skills/creating-output-styles/SKILL.md 3

# Result: 91% token savings
```

### Hot-Swap Workflow

```bash
# 1. Get UUID from library
skill-split list-library | grep "my-skill"

# 2. Checkout to workspace
skill-split checkout <uuid> ~/.claude/skills/active-skill.md --user joey

# 3. Agent uses skill...

# 4. Checkin when done
skill-split checkin ~/.claude/skills/active-skill.md
# File deleted, DB updated
```

## Database Contents

**SkillBank currently has**:
- 12 skills
- 43 references
- Total: 55 files

## Getting UUIDs

```bash
# Search for file
skill-split search-library "output-styles"

# Or query Supabase directly
python3 << EOF
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_PUBLISHABLE_KEY'))
result = client.table('files').select('id, name').ilike('name', '%output%').execute()
for f in result.data:
    print(f"{f['id']}: {f['name']}")
EOF
```

## Environment Setup

**Required in .env**:
```bash
SUPABASE_URL=https://dnqbnwalycyoynbcpbpz.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SKILL_SPLIT_DB=~/.claude/databases/skill-split.db
```

## Troubleshooting

**"No active project" error (Supabase)**:
- Check .env has correct keys
- Verify wrapper loads .env: `~/.claude/commands/skill-split`

**"Invalid UUID" error**:
- UUIDs are from Supabase, not SQLite IDs
- Use `list-library` to see files
- Use Python query to get UUIDs

**"File not found" error**:
- Check file path is absolute
- For Supabase: file must be ingested first

## Key Differences

| Feature | SQLite Local | Supabase SkillBank |
|---------|--------------|-------------------|
| **Purpose** | Token savings | Shared library |
| **Storage** | Sections in DB | Files + tracking |
| **Commands** | tree, get-section | checkout, checkin |
| **Database** | ~/.claude/databases/ | Supabase cloud |
| **Use case** | Progressive load | Hot-swap workflow |

## Examples

### Example 1: Research Mode
```bash
# Search across all indexed skills
skill-split search "error handling"

# Load relevant sections only
skill-split get-section <file> <id>
```

### Example 2: Agent Workflow
```bash
# Agent needs skill temporarily
skill-split checkout <uuid> ~/.claude/skills/temp-skill.md --user agent-1

# Agent completes task

# Cleanup
skill-split checkin ~/.claude/skills/temp-skill.md
```

### Example 3: Cross-File Search
```bash
# Find all references to "template"
skill-split search "template"

# Shows matches across:
# - creating-output-styles
# - prompt-engineering
# - other indexed skills
```

## Commands Reference

**Local (SQLite)**:
- `parse` - Preview file structure
- `validate` - Check file validity
- `store` - Index file for queries
- `get-section` - Load single section
- `tree` - Show hierarchy
- `search` - Find content

**Supabase (SkillBank)**:
- `list-library` - Show all files
- `checkout` - Get file from library
- `checkin` - Return file to library
- `status` - Show active checkouts
- `search-library` - Find files by name

## Token Savings

**Example**: 400-line skill file
- Full load: ~1000 tokens
- Tree view: ~50 tokens
- Single section: ~150 tokens
- **Savings: 85%**

## Integration

Both systems work together:
1. **Ingest to SkillBank** (once)
2. **Checkout when needed** (temporary local file)
3. **Store in SQLite** (if token savings needed)
4. **Query sections** (progressive disclosure)
5. **Checkin** (cleanup)

**Last Updated**: 2026-02-04
