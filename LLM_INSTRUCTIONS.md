# skill-split: LLM Instructions

**READ THIS BEFORE DOING ANYTHING ELSE.**

This tool is already built. Do not rewrite it. Do not refactor it. Do not "improve" it.
Your job is to USE it, not change it.

---

## What This Tool Does

`skill-split` stores Claude Code skills, commands, and plugins in a SQLite database —
one section per row. You can then search, retrieve, compose, and deploy individual
sections without loading entire files.

**Why this matters:** A 20KB skill file = thousands of tokens. One section = ~200 bytes.
99% token savings by only loading what you need.

---

## The Only Script You Run

```
python skill_split.py <command> [args]
```

That's it. One script. Do not run anything else. Do not edit it.

---

## Database Location

**Default:** `~/.claude/databases/skill-split.db`

Already populated with 1,600+ files. Use it. Don't create a new one unless you have a reason.

To use default DB: **omit `--db`**
To use a custom DB: add `--db /path/to/file.db`

---

## Core Commands (use these)

### Store a file
```bash
python skill_split.py store /path/to/SKILL.md
python skill_split.py store /path/to/command.md
```

### Search across everything
```bash
python skill_split.py search "what you're looking for"
```
Returns section IDs, titles, scores. Use these IDs for everything else.

### Get one section by ID
```bash
python skill_split.py get-section 42
```

### See what's in the library
```bash
python skill_split.py list-library
```

### See section tree for a file
```bash
python skill_split.py tree /path/to/SKILL.md
```

### Checkout (deploy a file to its working location)
```bash
python skill_split.py checkout <file_id> /target/path/SKILL.md
```
This copies the file AND updates `~/.claude/settings.json` if it's a plugin.

### Checkin (remove from working location)
```bash
python skill_split.py checkin /target/path/SKILL.md
```

### Check what's deployed
```bash
python skill_split.py status
```

### Compose a new skill from any sections
```bash
python skill_split.py compose --sections 3,7,12,99 --output /path/new-skill.md
```
Mix sections from ANY files. Order matters — first section sets the context.

---

## Naming Conventions (how names are derived)

| File type | Name comes from |
|-----------|----------------|
| `SKILL.md` inside `my-skill/` | folder name → `my-skill` |
| `insights.md` command | file stem → `insights` |
| `plugin.json` inside `compound-engineering/1.0.0/.claude-plugin/` | walks up past version + hidden dirs → `compound-engineering` |
| anything else | frontmatter `name` field, then frontmatter `title`, then file stem |

---

## Workflow: Finding and Using a Skill

```bash
# 1. Search for it
python skill_split.py search "github repo setup"

# 2. See the section tree to understand structure
python skill_split.py tree /Users/joey/.claude/skills/setting-up-github-repos/SKILL.md

# 3. Get the specific section you need (by ID from search results)
python skill_split.py get-section 24341

# 4. OR compose a new skill from the best sections
python skill_split.py compose --sections 24341,24135,24158 --output /tmp/my-composed-skill.md
```

---

## Workflow: Ingesting New Skills

```bash
# One file
python skill_split.py store ~/.claude/skills/my-new-skill/SKILL.md

# Whole folder (bash)
find ~/.claude/skills -name "SKILL.md" | while read f; do
  python skill_split.py store "$f"
done

# Commands
find ~/.claude/commands -name "*.md" | while read f; do
  python skill_split.py store "$f"
done
```

---

## What NOT To Do

- **Do NOT** run `pip install` or modify `requirements.txt` unless a new dependency is genuinely needed
- **Do NOT** rewrite `skill_split.py` — it works
- **Do NOT** create a new database when `~/.claude/databases/skill-split.db` already has 1,600+ files
- **Do NOT** use `--db` unless you have a specific reason to use a different database
- **Do NOT** edit core files (`core/parser.py`, `core/database.py`, etc.) without the user's explicit instruction
- **Do NOT** run the Supabase commands (`ingest`, `search-library`) without Supabase env vars set

---

## Supabase (Optional Cloud Backend)

Only needed for cloud sync and semantic/vector search.

```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-anon-key
```

Without these vars, use `--db` flag for local mode. Local mode works fine for everything.

---

## If Something Breaks

1. Run the tests first: `python -m pytest test/ -q --tb=short`
2. If tests pass but CLI fails, check that you're running from the project root
3. Check Python version: must be 3.8+
4. Do NOT start rewriting things. Read the error. Fix the specific thing.

---

## File Structure (what matters)

```
skill_split.py          ← THE ONLY SCRIPT YOU RUN
core/                   ← do not touch without instruction
  parser.py             ← parses markdown/yaml into sections
  database.py           ← SQLite storage, naming logic
  checkout_manager.py   ← deploys files, updates settings.json
  skill_composer.py     ← composes new skills from sections
  query.py              ← get_section, search_sections
handlers/               ← type-specific parsers (scripts, plugins, etc.)
test/                   ← 623 tests, all passing
~/.claude/databases/
  skill-split.db        ← production database, 1,600+ files
```

---

## Quick Reference Card

| Goal | Command |
|------|---------|
| Find something | `python skill_split.py search "query"` |
| Get one section | `python skill_split.py get-section <id>` |
| Add a file | `python skill_split.py store /path/to/file.md` |
| List everything | `python skill_split.py list-library` |
| See file structure | `python skill_split.py tree /path/to/file.md` |
| Deploy a file | `python skill_split.py checkout <id> /target/path` |
| Remove deployment | `python skill_split.py checkin /target/path` |
| What's deployed | `python skill_split.py status` |
| Build new skill | `python skill_split.py compose --sections 1,2,3 --output out.md` |
| All help | `python skill_split.py --help` |
