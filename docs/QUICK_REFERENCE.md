# skill-split Quick Reference

**Last Updated:** 2026-02-10

Cheat sheet for common skill-split operations.

---

## Installation

```bash
pip install -e .
# or
pip install skill-split
```

---

## Core Commands

### Parsing & Validation

```bash
# Parse file
./skill_split.py parse file.md

# Validate structure
./skill_split.py validate file.md

# Verify round-trip
./skill_split.py verify file.md
```

### Storage

```bash
# Store in database
./skill_split.py store file.md

# Custom database
./skill_split.py store file.md --db /path/to/db.db

# Multiple files
./skill_split.py store docs/**/*.md
```

### Search

```bash
# BM25 keyword search (fast)
./skill_split.py search "query"

# Semantic search (requires API key)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "query"

# Hybrid search (balanced)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "query" --vector-weight 0.7

# Boolean operators
./skill_split.py search "term1 AND term2"
./skill_split.py search "term1 NOT term2"
./skill_split.py search "term1 NEAR/5 term2"

# Limit results
./skill_split.py search "query" --limit 10
```

### Navigation

```bash
# List sections with IDs
./skill_split.py list file.md

# Get specific section
./skill_split.py get-section 42

# Next sibling
./skill_split.py next 42 file.md

# First child
./skill_split.py next 42 file.md --child
```

### Composition

```bash
# Compose from sections
./skill_split.py compose --sections 1,5,10 --output new.md

# From specific file
./skill_split.py compose --sections 1,5,10 --file source.md --output new.md

# With frontmatter
./skill_split.py compose --sections 1,5,10 --name "My Skill" --output new.md
```

---

## Supabase Integration

```bash
# Set credentials
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-key"

# Ingest files
./skill_split.py ingest file.md

# Search library
./skill_split.py search-library "query"

# Checkout file
./skill_split.py checkout file.md

# Checkin file
./skill_split.py checkin file.md

# List library
./skill_split.py list-library

# Status
./skill_split.py status
```

---

## Python API

```python
from core.parser import Parser
from core.database import DatabaseStore
from core.query import QueryAPI

# Parse
parser = Parser()
document = parser.parse(content, "file.md")

# Store
db = DatabaseStore("database.db")
db.store_document(document)

# Query
api = QueryAPI(db)
results = api.search("query")
section = api.get_section(42)
```

---

## Search Modes Comparison

| Mode | Command | Speed | Best For |
|------|---------|-------|----------|
| BM25 | `search` | ⚡⚡⚡ | Exact matches |
| Vector | `search-semantic --vector-weight 1.0` | ⚡ | Concepts |
| Hybrid | `search-semantic --vector-weight 0.7` | ⚡⚡ | Balanced |

---

## Common Options

```bash
# Database
--db /path/to/database.db

# Output
--output /path/to/output.md
-o /path/to/output.md

# Limits
--limit 10
-n 10

# Format
--format markdown
--format xml

# Verbose
--verbose
-v

# Help
--help
-h
```

---

## Environment Variables

```bash
# Database location
export SKILL_SPLIT_DB="/path/to/default.db"

# OpenAI API (for semantic search)
export OPENAI_API_KEY="sk-..."

# Enable embeddings
export ENABLE_EMBEDDINGS="true"

# Supabase
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-key"

# Debug mode
export DEBUG="1"
```

---

## File Formats

### Markdown (default)

```markdown
---
frontmatter: optional
---

# Heading 1
Content

## Heading 2
More content
```

### XML

```xml
<component name="Example">
  <section>
    Content here
  </section>
</component>
```

### Mixed

```xml
---
frontmatter
---
<xml>content</xml>

# Markdown heading

More markdown
```

---

## Database Schema

```sql
-- Files table
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    hash TEXT,
    metadata TEXT
);

-- Sections table
CREATE TABLE sections (
    id INTEGER PRIMARY KEY,
    file_id INTEGER,
    parent_id INTEGER,
    level INTEGER,
    heading TEXT,
    content TEXT,
    order_in_parent INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES sections(id) ON DELETE CASCADE
);

-- Full-text search
CREATE VIRTUAL TABLE sections_fts USING fts5(
    content, file_path, section_id,
    content_rowid='sections'
);
```

---

## Performance Tips

```bash
# Use limits for faster queries
./skill_split.py search "query" --limit 10

# Use file path filters
./skill_split.py search "query" --file-path "specific/file.md"

# Rebuild FTS5 index
sqlite3 db.db "INSERT INTO sections_fts(sections_fts) VALUES('rebuild');"

# Optimize database
sqlite3 db.db "VACUUM; ANALYZE;"
```

---

## Troubleshooting

```bash
# Database locked?
rm -f *.db-wal *.db-shm

# No sections found?
./skill_split.py validate file.md

# Search slow?
./skill_split.py search "query" --limit 10

# Check integrity
sqlite3 db.db "PRAGMA integrity_check;"
```

---

## Token Savings

| File Size | Full Load | One Section | Savings |
|-----------|-----------|-------------|---------|
| 10KB | 2,500 tokens | 50 tokens | 98% |
| 50KB | 12,500 tokens | 50 tokens | 99.6% |
| 100KB | 25,000 tokens | 50 tokens | 99.8% |

---

## Aliases (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# skill-split aliases
alias ss='python /path/to/skill-split/skill_split.py'
alias ss-search='ss search'
alias ss-get='ss get-section'
alias ss-next='ss next'
alias ss-list='ss list'
```

Usage:

```bash
ss search "query"
ss get 42
ss next 42 file.md
ss list file.md
```

---

## Keyboard Shortcuts (VS Code)

If using VS Code extension:

| Shortcut | Action |
|----------|--------|
| `Cmd+Shift+S` | Search sections |
| `Cmd+Shift+N` | Next section |
| `Cmd+Shift+P` | Previous section |
| `Cmd+Shift+L` | List sections |

---

## File Location Defaults

| Platform | Default Database |
|----------|------------------|
| Linux | `~/.claude/databases/skill-split.db` |
| macOS | `~/.claude/databases/skill-split.db` |
| Windows | `%USERPROFILE%\.claude\databases\skill-split.db` |

---

## Common Workflows

### Progressive Disclosure

```bash
# 1. Search for topic
./skill_split.py search "authentication"

# 2. Load specific section
./skill_split.py get-section 42

# 3. Navigate to next
./skill_split.py next 42 file.md

# 4. Drill deeper
./skill_split.py next 42 file.md --child
```

### Skill Composition

```bash
# 1. Find relevant sections
./skill_split.py search "python handler"

# 2. Note section IDs: 42, 57, 103

# 3. Compose new skill
./skill_split.py compose --sections 42,57,103 --output python_guide.md

# 4. Validate result
./skill_split.py validate python_guide.md
```

### CI/CD Validation

```yaml
- name: Validate documentation
  run: |
    pip install -e .
    for file in docs/**/*.md; do
      skill_split.py validate "$file"
    done
```

---

## Quick Links

- [Full Documentation](../README.md)
- [Installation Guide](../INSTALLATION.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
- [API Reference](../API.md)
- [Integration Guides](../integrations/)

---

*Need more? See [FAQ.md](./FAQ.md) or open an issue!*
