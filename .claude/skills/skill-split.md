---
name: skill-split
version: 1.0.0
category: file-tools
description: Progressive disclosure of large YAML and Markdown files via SQLite-backed section storage
author: Joey
created: 2026-02-03
keywords: [progressive-disclosure, file-parsing, sections, tokens, sqlite]
triggers:
  - /skill-split
  - skill-split
allowed-tools: [Bash, Read, Write, Grep]
---

# skill-split

Progressive disclosure tool for intelligent file splitting by sections and subsections. Stores parsed content in SQLite for token-efficient exploration.

## Purpose

`skill-split` solves the token-bloat problem when working with large documentation files. Instead of loading entire files, you:

1. Parse files into section hierarchy (YAML frontmatter + Markdown headings + XML tags)
2. Store sections in SQLite with metadata
3. Query progressively - load only what you need
4. Save tokens while maintaining document structure

**Key Innovation**: SQLite-backed section storage enables on-demand, granular file exploration without token waste.

## Usage

### Basic Workflow

```bash
# 1. Parse file and display structure
./skill_split.py parse <file.md>

# 2. Store in database
./skill_split.py store <file.md>

# 3. Retrieve specific section
./skill_split.py get-section <file_id> <section_id>

# 4. Search across sections
./skill_split.py search <query>

# 5. View section hierarchy
./skill_split.py tree <file.md>
```

### Installation

#### For Claude Code Users

The `/skill-split` command is pre-configured. Just use it:
```
/skill-split parse <file>
/skill-split store <file>
/skill-split search <query>
```

**Database location**: `~/.claude/databases/skill-split.db` (auto-created)

#### For Standalone Users

```bash
cd /Users/joey/working/skill-split
pip install -r requirements.txt
./skill_split.py --help
```

## Quick Start Example

1. **Ingest a skill**:
   ```
   /skill-split store ~/.claude/skills/creating-output-styles/SKILL.md
   ```

2. **View structure** (shows section IDs):
   ```
   /skill-split tree ~/.claude/skills/creating-output-styles/SKILL.md
   ```

3. **Search across skills**:
   ```
   /skill-split search "format templates"
   ```

4. **Load specific section** (by ID from tree):
   ```
   /skill-split get-section ~/.claude/skills/creating-output-styles/SKILL.md 3
   ```

## Value Proposition

**Token Savings**: 70-90% reduction through progressive disclosure

**Example**: A 400-line skill file
- Old way: Load entire file = ~1000 tokens per session
- New way: Load tree (50 tokens) → fetch 1 section (150 tokens) = 80% savings

## Commands

### parse
Parse file and display detected sections without storing.

```bash
./skill_split.py parse <file>
```

**Output**: Displays YAML frontmatter, markdown headings, XML tags, and their nesting levels.

**Use case**: Understand file structure before storage.

---

### store
Parse file and store all sections in SQLite database.

```bash
./skill_split.py store <file>
```

**Database**: `skill-split.db` (created in project root)

**Tables**:
- `files`: File metadata (id, path, hash, created_at)
- `sections`: Section content (id, file_id, title, content, level, start_line, end_line)

**Use case**: Index large documentation files for progressive retrieval.

---

### get-section
Retrieve single section from database by ID.

```bash
./skill_split.py get-section <file_id> <section_id>
```

**Output**: Section title, content, metadata (level, line numbers, parent).

**Use case**: Load only the section you need in your Claude session.

---

### search
Search section content by keyword across all files.

```bash
./skill_split.py search <query>
```

**Output**: Matching sections with preview snippets.

**Use case**: Find relevant sections without loading entire files.

---

### tree
Display section hierarchy as indented tree.

```bash
./skill_split.py tree <file>
```

**Output**: Nested section structure with line ranges.

```
Level 1: Introduction (lines 1-50)
  Level 2: Background (lines 5-20)
  Level 2: Goals (lines 21-50)
Level 1: Architecture (lines 51-150)
  Level 2: Parser (lines 55-80)
  Level 2: Database (lines 81-120)
```

**Use case**: Understand document structure before querying.

---

### validate
Verify file structure and detect parsing issues.

```bash
./skill_split.py validate <file>
```

**Checks**:
- Valid YAML frontmatter
- Well-formed markdown headings
- Matched XML tags
- No code block intrusions

**Use case**: Prepare files for storage.

---

### verify
Round-trip verification: parse → store → recompose → hash compare.

```bash
./skill_split.py verify <file>
```

**Verification**: SHA256 hash of original file MUST match recomposed file bit-for-bit.

**Use case**: Ensure storage integrity (CRITICAL).

---

## Integration

### Progressive Disclosure Workflow

1. **Store Phase**: User runs `./skill_split.py store large-skill.md` once
2. **Query Phase**: Claude session uses QueryAPI to load sections progressively
3. **Token Savings**: Only request sections you need, avoid full-file bloat

### QueryAPI (Python)

```python
from core.query import QueryAPI

api = QueryAPI("skill-split.db")

# Get single section
section = api.get_section(file_id=1, section_id=5)

# Progressive disclosure - get next section
next_section = api.get_next_section(current_id=5)

# Get section hierarchy
tree = api.get_section_tree("large-skill.md")

# Search across files
results = api.search_sections("authentication")
```

### Claude Code Skill Integration

When `skill-split` is installed as a Claude Code skill:

```bash
/skill-split parse <file>        # Show structure
/skill-split store <file>        # Index for progressive disclosure
/skill-split get-section <id>    # Load specific section
/skill-split search <query>      # Find relevant sections
/skill-split tree <file>         # Display hierarchy
```

## Error Handling

### Common Issues

**"File not found"**
```
Error: Cannot read <file>
Fix: Verify file path and permissions
```

**"Invalid YAML frontmatter"**
```
Error: Frontmatter must start with --- on line 1
Fix: Add valid YAML header at file start (or remove if not needed)
```

**"Code block detected inside section"**
```
Error: Section spans across ``` fence (line 45-87)
Fix: Move fence boundaries to align with section breaks
```

**"Round-trip hash mismatch"**
```
Error: Original hash: abc123 | Recomposed hash: def456
Fix: Check for lost whitespace or newlines in recomposer
```

**"Database locked"**
```
Error: skill-split.db is locked by another process
Fix: Wait for other query to complete, or delete .db and re-store
```

## Token Savings & Benefits

### Why Progressive Disclosure Matters

**Scenario: 500-line skill file**

- **Old way**: Load entire file in every Claude session → 500 lines × cost per token = $0.XX
- **New way**: Load section on demand → 50 lines × cost per token = $0.00X (90% savings)

**Scenario: Cross-file search**

- **Old way**: Load all 10 documentation files to find one answer
- **New way**: `search()` finds matching sections in all files, load only relevant ones

### Benefits Summary

| Feature | Benefit |
|---------|---------|
| **Section-based storage** | Load only what you need (token efficiency) |
| **Hierarchical queries** | Navigate large files without cognitive overload |
| **Search API** | Find answers across entire skill library in one query |
| **Byte-perfect round-trip** | Integrity verified via SHA256 hashing |
| **SQLite backend** | Portable, queryable, no external dependencies |

## Technical Details

### Supported Formats

- **YAML frontmatter**: `---` delimited metadata at file start
- **Markdown headings**: `# Level 1`, `## Level 2`, etc.
- **XML tags**: `<tag>content</tag>` for custom sections (level=-1)
- **Code blocks**: Respects ``` fences (no splitting inside)

### Database Schema

```sql
-- Files
CREATE TABLE files (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Sections
CREATE TABLE sections (
  id INTEGER PRIMARY KEY,
  file_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  level INTEGER,
  start_line INTEGER,
  end_line INTEGER,
  FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
)
```

### Architecture

```
Input File
    ↓
[Parser] → Detects YAML/headings/XML → [Database] → SQLite sections table
    ↓
[Recomposer] → Reconstructs file from sections → SHA256 verify
    ↓
Original ↔ Recomposed (must match exactly)
```

## Examples

### Example 1: Index a Large Skill

```bash
# Store skill-split.md in database
./skill_split.py store ~/.claude/skills/my-skill.md

# View structure
./skill_split.py tree ~/.claude/skills/my-skill.md

# Retrieve "Installation" section
./skill_split.py get-section 1 3
```

### Example 2: Progressive Disclosure

```python
from core.query import QueryAPI

api = QueryAPI("skill-split.db")

# Start with main sections
sections = api.get_section_tree("large-file.md")
print(f"Found {len(sections)} top-level sections")

# User asks about "Authentication"
results = api.search_sections("authentication")
print(f"Found {len(results)} matching sections")

# Load only relevant section
section = api.get_section(file_id=1, section_id=results[0].id)
print(section.content)  # Only this section → token savings!
```

### Example 3: Cross-File Search

```bash
# Search all indexed files
./skill_split.py search "error handling"

# Output: Finds matching sections in:
# - skill-split.md (section 12)
# - error-patterns.md (section 3)
# - debugging-guide.md (section 8)
```

## Testing

Run test suite to verify functionality:

```bash
# All tests (should see 28+ passing)
pytest -v

# Specific module
pytest test/test_parser.py -v

# With coverage
pytest --cov=core --cov-report=term-missing
```

**Test Categories**:
- Parser tests: 21 (YAML, headings, XML tags, edge cases)
- Database tests: 7 (storage, retrieval, cascading deletes)
- Hashing tests: 5 (SHA256 file integrity)
- Round-trip tests: 8 (recomposer byte-perfect matching)

---

**Last Updated**: 2026-02-03 | **Status**: Phase 4 Complete (Phase 5-6 in progress)
