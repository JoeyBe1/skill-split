# skill-split CLI Reference

Complete reference for all skill-split commands and options.

## Commands

### parse

Parse a markdown or YAML file and display its structure.

```bash
./skill_split.py parse <file>
```

**Description**: Parse file and display section structure without storing.

**Arguments**:
- `file`: Path to YAML or Markdown file

**Output**: Hierarchical section listing with byte positions

**Example**:
```bash
./skill_split.py parse SKILL.md
```

**Output**:
```
File: SKILL.md
Type: skill
Format: markdown

Frontmatter:
---
name: test-skill
description: A simple test skill
version: 1.0.0
---

Sections:
# Test Skill
  Lines: 7-9
  ## Overview
    Lines: 11-13
```

---

### validate

Validate a file's structure and check for round-trip integrity.

```bash
./skill_split.py validate <file>
```

**Description**: Check if file structure is valid and parseable.

**Arguments**:
- `file`: Path to YAML or Markdown file

**Output**: Valid/Invalid status and detailed error messages

**Exit Codes**:
- `0`: File is valid
- `1`: Parse errors detected

**Example**:
```bash
./skill_split.py validate SKILL.md
```

**Output**:
```
Validating: SKILL.md
Type: skill, Format: markdown

✓ No issues found
```

---

### store

Parse and store a file in the database.

```bash
./skill_split.py store <file> [--db <path>]
```

**Description**: Parse file and store all sections in SQLite database.

**Arguments**:
- `file`: Path to YAML or Markdown file

**Options**:
- `--db <path>`: Database path (default: `~/.claude/databases/skill-split.db`)

**Output**: File ID and section count stored

**Example**:
```bash
./skill_split.py store SKILL.md
./skill_split.py store SKILL.md --db /custom/path/database.db
```

**Output**:
```
File: SKILL.md
File ID: 1
Hash: 3f8c2a91d7e4b5c6a9f1e2d3c4b5a6f7
Type: skill
Format: markdown
Sections: 4
```

**Note**: Re-running store on the same file updates the database automatically.

---

### list

List all sections in a file with their IDs and hierarchy.

```bash
./skill_split.py list <file> [--db <path>]
```

**Description**: Display section hierarchy as a tree without content.

**Arguments**:
- `file`: Path to stored file

**Options**:
- `--db <path>`: Database path

**Output**: ASCII tree with section titles, levels, and IDs

**Example**:
```bash
./skill_split.py list /skills/programming/SKILL.md
```

**Output**:
```
ID  Title                             Level
--- -------------------------------- ------
1  Overview                         1
2  Installation                     1
3  Usage                            1
4    Configuration                  2
5    Troubleshooting                2
6  Advanced Topics                  1
```

---

### get-section

Retrieve a single section by ID.

```bash
./skill_split.py get-section <id> [--db <path>]
```

**Description**: Retrieve a specific section from the database by ID.

**Arguments**:
- `id`: Section ID (from `list` command)

**Options**:
- `--db <path>`: Database path

**Output**: Section content with title and level

**Example**:
```bash
./skill_split.py get-section 42
```

**Output**:
```
=== Python Handler (Level 1, Section ID: 42) ===

# Python Handler

Handles Python script files with class and function detection.
```

---

### next

Get the next section after a given section.

```bash
./skill_split.py next <section_id> <file> [--child] [--db <path>]
```

**Description**: Get the next sibling section or first child subsection.

**Arguments**:
- `section_id`: Current section ID
- `file`: Path to the file containing the section

**Options**:
- `--child`: Navigate to first child subsection instead of next sibling
- `--db <path>`: Database path

**Examples**:
```bash
# Get next sibling (default)
./skill_split.py next 42 /skills/programming/SKILL.md

# Get first child subsection
./skill_split.py next 42 /skills/programming/SKILL.md --child
```

**Output**: Next section content with title and level

---

### search

Search sections by query across all files or a specific file using FTS5 BM25 ranking.

```bash
./skill_split.py search <query> [--file <path>] [--db <path>]
```

**Description**: Search section content using FTS5 full-text search with BM25 relevance ranking.

**Arguments**:
- `query`: Search string (natural language or FTS5 MATCH syntax)

**Options**:
- `--file <path>`: Limit search to specific file
- `--db <path>`: Database path

**Search Syntax**:
- Single word: `python`
- Multi-word (OR): `git setup`
- Exact phrase: `"git repository"`
- AND search: `python AND handler`
- OR search: `python OR handler`
- NEAR search: `git NEAR repository`

**Examples**:
```bash
# Search all files
./skill_split.py search "python handler"

# Search specific file
./skill_split.py search "configuration" --file /skills/api/SKILL.md

# Exact phrase search
./skill_split.py search '"python handler"'

# AND search
./skill_split.py search "python AND testing"
```

**Output**: Results with section IDs, titles, relevance scores, and files

```
Found 5 section(s) matching 'python handler':

ID      Score   Title                                     Level
-------- -------- ---------------------------------------- ------
42      3.52    Python Handler Implementation              1
15      2.18    Advanced Python Techniques                2
```

**Query Processing**: Natural language queries are automatically converted to optimal FTS5 syntax. Multi-word queries use OR for broader discovery.

---

### search-semantic

Search sections using semantic similarity (vector search) or hybrid search.

```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic <query> [--limit <n>] [--vector-weight <w>] [--db <path>]
```

**Description**: Search sections using semantic vector similarity or hybrid BM25+vector search.

**Arguments**:
- `query`: Search query string

**Options**:
- `--limit <n>`: Maximum results to return (default: 10)
- `--vector-weight <w>`: Vector score weight 0.0-1.0 (default: 0.7)
- `--db <path>`: Database path

**Environment Variables**:
- `ENABLE_EMBEDDINGS=true`: Required for vector search
- `OPENAI_API_KEY`: Required for embeddings
- `SUPABASE_URL`: Required for vector storage
- `SUPABASE_PUBLISHABLE_KEY`: Required for vector storage

**Vector Weight Guide**:
- `1.0` = Pure vector search (semantic only)
- `0.7` = Hybrid search (70% semantic, 30% keyword) - **Recommended**
- `0.5` = Equal balance
- `0.0` = Pure keyword search

**Examples**:
```bash
# Hybrid search (recommended)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 0.7

# Pure vector search
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "error handling" --vector-weight 1.0

# More keyword-focused
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "python testing" --vector-weight 0.3
```

**Output**: Results with similarity scores

```
Found 5 section(s) matching 'code execution' (semantic search, weight=0.7):

Score    ID      Title
-------- ------ ------------------------------------------
0.89     42      Process Execution
0.75     15      Command Runner
0.68     87      Script Handler
```

**Note**: Falls back to keyword search if embeddings not enabled or API keys missing.

---

### verify

Verify round-trip integrity for a stored file.

```bash
./skill_split.py verify <file> [--db <path>]
```

**Description**: Verify round-trip integrity (parse → store → recompose).

**Arguments**:
- `file`: Path to YAML or Markdown file

**Options**:
- `--db <path>`: Database path

**Output**: Hash comparison and match status

**Exit Codes**:
- `0`: Hashes match (round-trip successful)
- `1`: Hashes don't match (data loss detected)

**Example**:
```bash
./skill_split.py verify SKILL.md
```

**Output**:
```
File: SKILL.md
File ID: 1
Type: skill
Format: markdown

✓ Round-trip successful
  Original hash:  3f8c2a91d7e4b5c6a9f1e2d3c4b5a6f7
  Recomposed hash: 3f8c2a91d7e4b5c6a9f1e2d3c4b5a6f7
  Match: YES
```

---

### tree

Display section hierarchy as a tree without content.

```bash
./skill_split.py tree <file> [--db <path>]
```

**Description**: Display section hierarchy as a tree without content.

**Arguments**:
- `file`: Path to stored file

**Options**:
- `--db <path>`: Database path

**Output**: ASCII tree with section titles and levels

**Example**:
```bash
./skill_split.py tree ~/.claude/skills/my-skill.md
```

**Output**:
```
~/.claude/skills/my-skill.md
├── What it does (Level 1)
│   ├── Key Features (Level 2)
│   └── Why This Matters (Level 2)
├── Installation (Level 1)
│   ├── Prerequisites (Level 2)
│   └── From Source (Level 2)
└── Testing (Level 1)
    └── Running Tests (Level 2)
```

---

### get

Retrieve a specific section from the database by title.

```bash
./skill_split.py get <file> [section_name]
```

**Description**: Retrieve a specific section from the database by title.

**Arguments**:
- `file`: Path to stored file
- `section_name`: (Optional) Section title to retrieve

**Output**: Section content with metadata header

**Example**:
```bash
./skill_split.py get README.md "Installation"
./skill_split.py get README.md "Quick Start"
./skill_split.py get README.md  # Lists all sections
```

---

## Supabase Commands

### ingest

Upload local files to Supabase library.

```bash
./skill_split.py ingest <directory>
```

**Description**: Parse all markdown files in directory and upload to Supabase.

**Arguments**:
- `directory`: Path to directory containing skill files

**Example**:
```bash
./skill_split.py ingest ~/.claude/skills/
```

---

### checkout

Deploy a file from Supabase to local path.

```bash
./skill_split.py checkout <file_id> <target_path>
```

**Description**: Deploy a file from Supabase to local path and track deployment.

**Arguments**:
- `file_id`: ID of file in Supabase
- `target_path`: Local file path to deploy to

**Example**:
```bash
./skill_split.py checkout 42 ~/.claude/skills/temp-skill.md
```

---

### checkin

Remove deployed file and update status.

```bash
./skill_split.py checkin <file_path>
```

**Description**: Remove deployed file and update Supabase status.

**Arguments**:
- `file_path`: Path to deployed file

**Example**:
```bash
./skill_split.py checkin ~/.claude/skills/temp-skill.md
```

---

### list-library

View all files in Supabase.

```bash
./skill_split.py list-library
```

**Description**: List all files stored in Supabase library.

**Example**:
```bash
./skill_split.py list-library
```

---

### search-library

Search across all files in Supabase.

```bash
./skill_split.py search-library <query>
```

**Description**: Search files by query across Supabase library.

**Arguments**:
- `query`: Search query string

**Example**:
```bash
./skill_split.py search-library "authentication"
```

---

### status

View active checkouts.

```bash
./skill_split.py status
```

**Description**: Display all active checkout deployments.

**Example**:
```bash
./skill_split.py status
```

---

## Global Options

### `--db`

Specify database path for commands that access the database.

**Default:** `~/.claude/databases/skill-split.db` (or `SKILL_SPLIT_DB` environment variable)

**Example**:
```bash
./skill_split.py search "python" --db /custom/path/db.sqlite
```

---

## Environment Variables

### `SKILL_SPLIT_DB`

Default database path for all commands.

**Example**:
```bash
export SKILL_SPLIT_DB=/custom/path/db.sqlite
./skill_split.py search "python"  # Uses /custom/path/db.sqlite
```

### `ENABLE_EMBEDDINGS`

Enable vector search functionality.

**Example**:
```bash
export ENABLE_EMBEDDINGS=true
./skill_split.py search-semantic "code execution"
```

### `OPENAI_API_KEY`

OpenAI API key for embedding generation (required for vector search).

### `SUPABASE_URL`

Supabase project URL (required for Supabase integration).

### `SUPABASE_PUBLISHABLE_KEY`

Supabase publishable key (required for Supabase integration).

---

## Exit Codes

- `0`: Success
- `1`: Error occurred

---

## See Also

- [README.md](../README.md) - Complete documentation
- [EXAMPLES.md](../EXAMPLES.md) - Real-world usage examples
- [CLAUDE.md](../CLAUDE.md) - Project reference for Claude Code
