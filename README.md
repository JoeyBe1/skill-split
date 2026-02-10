# skill-split

Intelligently split YAML and Markdown files into sections and store them in SQLite for progressive disclosure. Now with component handler support for plugins, hooks, and configuration files.

## What It Does

`skill-split` solves a critical problem: **large files consume tokens inefficiently**. Instead of loading entire files into context, skill-split breaks them into discrete sections and stores them in a lightweight SQLite database.

### Key Features

**Core Capabilities:**
- **Intelligent Parsing**: Detects and preserves YAML frontmatter, Markdown headings (h1-h6), and XML-style tags
- **Byte-Perfect Round-Trip**: Recompose files exactly as they were—no corruption, no whitespace changes
- **Progressive Disclosure**: Load sections incrementally instead of entire files
- **Section Storage**: SQLite database tracks sections with metadata (id, title, level, content, byte position)
- **Tree Navigation**: Understand full section hierarchy before diving into details
- **Search-Ready**: Query sections by title, level, or content
- **Code-Block Aware**: Doesn't split inside markdown code fences

**Phase 9: Component Handlers**
- **Plugin Support**: Parse `plugin.json` with MCP config and hooks
- **Hook Support**: Parse `hooks.json` with shell scripts
- **Config Support**: Parse `settings.json` and `mcp_config.json`
- **Multi-File Handling**: Track and hash related files together
- **Type Detection**: Automatic component type detection

### Why This Matters

Imagine a 50KB skill definition file with 20 sections. Instead of sending all 50KB to Claude every time you need one section:

1. Parse the file once: `./skill_split.py store skill.md`
2. Get just the section you need: `./skill_split.py get-section skill.md "Installation"`
3. Save thousands of tokens per query

## Installation

### Prerequisites

- Python 3.8+
- Click (for CLI)
- pytest (for testing)

### From Source

```bash
git clone https://github.com/yourusername/skill-split.git
cd skill-split
pip install -e .
```

Or install dependencies manually:

```bash
pip install click pytest
```

### Verify Installation

```bash
python skill_split.py --help
```

You should see 16 commands:
- **Core**: `parse`, `validate`, `store`, `get`, `tree`, `verify`
- **Query**: `get-section`, `next`, `list`, `search`
- **Supabase**: `ingest`, `checkout`, `checkin`, `list-library`, `status`, `search-library`

## Quick Start

### Parse and Structure

```bash
# Parse a markdown file
./skill_split.py parse SKILL.md

# Validate structure
./skill_split.py validate SKILL.md

# Store in database
./skill_split.py store SKILL.md
```

### Search and Retrieve

```bash
# Search for content (BM25 keyword search)
./skill_split.py search "python handler"

# List file sections
./skill_split.py list SKILL.md

# Get specific section by ID
./skill_split.py get-section 42
```

### Progressive Disclosure

```bash
# Navigate to next section (sibling)
./skill_split.py next 42 SKILL.md

# Drill into first child subsection
./skill_split.py next 42 SKILL.md --child
```

Returns exit code 0 if valid, non-zero if problems found.

### 6. Search Sections

Search across all stored files using FTS5 full-text search:

```bash
./skill_split.py search "python handler"
```

Output:
```
Found 3 section(s) matching 'python handler':

ID      Score   File                                   Title
-------- -------- -------------------------------------- --------
42      3.52    /skills/programming/SKILL.md           Python Handler
15      2.18    /docs/advanced/TECHNIQUES.md           Advanced Python
8       1.05    /setup/INSTALL.md                      Setup Python
```

Multi-word queries use OR search for broader discovery (finds sections with ANY word).

### 7. Verify Round-Trip Integrity

Confirm that parsing and recomposition produce an exact byte match:

```bash
./skill_split.py verify docs/my-skill.md
```

Output:
```
✓ Round-trip successful
  Original hash:  abc123def456...
  Recomposed hash: abc123def456...
  Match: YES
```

## CLI Reference

### Parse Command

```bash
./skill_split.py parse <file>
```

**Description**: Parse file and display section structure without storing.

**Arguments**:
- `file`: Path to YAML or Markdown file

**Output**: Hierarchical section listing with byte positions

**Example**:
```bash
./skill_split.py parse README.md
```

---

### Store Command

```bash
./skill_split.py store <file>
```

**Description**: Parse file and store all sections in SQLite database.

**Arguments**:
- `file`: Path to YAML or Markdown file

**Output**: Confirmation message with section count

**Example**:
```bash
./skill_split.py store ~/.claude/skills/my-skill.md
```

**Note**: Re-running store on the same file updates the database automatically.

---

### Get Command

```bash
./skill_split.py get <file> [section_name]
```

**Description**: Retrieve a specific section from the database by title.

**Arguments**:
- `file`: Path to stored file
- `section_name`: (Optional) Section title to retrieve. If omitted, shows all sections with IDs.

**Output**: Section content with metadata header

**Example**:
```bash
./skill_split.py get README.md "Installation"
./skill_split.py get README.md "Quick Start"
./skill_split.py get README.md  # Lists all sections
```

---

### Tree Command

```bash
./skill_split.py tree <file>
```

**Description**: Display section hierarchy as a tree without content.

**Arguments**:
- `file`: Path to stored file

**Output**: ASCII tree with section titles and levels

**Example**:
```bash
./skill_split.py tree ~/.claude/skills/my-skill.md
```

---

### Validate Command

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
./skill_split.py validate README.md
```

---

### Verify Command

```bash
./skill_split.py verify <file>
```

**Description**: Verify round-trip integrity (parse → store → recompose). Hashes must match exactly.

**Arguments**:
- `file`: Path to YAML or Markdown file

**Output**: Hash comparison and match status

**Exit Codes**:
- `0`: Hashes match (round-trip successful)
- `1`: Hashes don't match (data loss detected)

**Example**:
```bash
./skill_split.py verify README.md
```

---

### Search Command

```bash
./skill_split.py search <query> [--file <path>] [--db <path>]
```

**Description**: Search section content using FTS5 full-text search with BM25 relevance ranking. Multi-word queries use OR search for better discovery.

**Arguments**:
- `query`: Search string (natural language or FTS5 MATCH syntax)
- `--file`: (Optional) Limit search to specific file
- `--db`: (Optional) Path to database (default: skill_split.db)

**Output**: Ranked results with relevance scores (higher = more relevant)

**Examples**:
```bash
# Multi-word search uses OR (finds sections with either word)
./skill_split.py search "git setup"

# Exact phrase search (use quotes)
./skill_split.py search '"git repository"'

# AND search (both words required)
./skill_split.py search "git AND repository"

# Search within specific file
./skill_split.py search "python" --file /skills/programming/SKILL.md

# Use custom database
./skill_split.py search "authentication" --db ~/.claude/databases/skill-split.db
```

**Query Processing**: Natural language queries are automatically converted to optimal FTS5 syntax. See [Search Syntax](#search-syntax) for details.

---

### Backup Command

```bash
./skill_split.py backup [--output <path>] [--db <path>]
```

**Description**: Creates a timestamped, gzip-compressed SQLite dump of the database for disaster recovery.

**Arguments**:
- `--output`: (Optional) Custom filename for the backup (default: auto-generated timestamp)
- `--db`: (Optional) Path to database (default: skill_split.db)

**Output**: Full path to the created backup file

**Examples**:
```bash
# Create backup with auto-generated filename
./skill_split.py backup

# Create backup with custom filename
./skill_split.py backup --output my-backup

# Backup specific database
./skill_split.py backup --db ~/.claude/databases/skill-split.db

# Create backup in specific location
./skill_split.py backup --output production-backup --db ~/.claude/databases/skill-split.db
```

**Notes**:
- Backups are stored in `~/.claude/backups/` by default
- Backup files are gzip-compressed SQL dumps with `.sql.gz` extension
- FTS5 virtual tables are handled properly during backup
- Timestamp format: `skill-split-YYYYMMDD-HHMMSS.sql.gz`

---

## Search & Navigation

skill-split provides THREE search modes for different use cases, plus progressive disclosure navigation for token-efficient content access.

### Three Search Modes

#### 1. BM25 Search (Keywords) - `search` command

**Best for:** Exact keyword matching, fast text search

```bash
./skill_split.py search "python handler"
```

**Features:**
- FTS5 full-text search with BM25 ranking
- Fast, works locally without API keys
- Multi-word queries use OR for discovery
- Relevance scores based on term frequency
- Boolean operators: AND, OR, NEAR

#### 2. Vector Search (Semantic) - `search-semantic` command

**Best for:** Semantic similarity, concept matching

```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 1.0
```

**Features:**
- OpenAI embeddings for semantic understanding
- Finds conceptually similar content
- Requires `OPENAI_API_KEY` and Supabase
- Pure vector search (set `--vector-weight 1.0`)

#### 3. Hybrid Search (Combined) - `search-semantic` command

**Best for:** Best of both worlds

```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "python error handling" --vector-weight 0.7
```

**Features:**
- Combines BM25 keywords + Vector similarity
- Default vector weight 0.7 (70% semantic, 30% keyword)
- Tunable balance between precision and discovery
- Requires `OPENAI_API_KEY` and Supabase

### Which Search to Use?

| Use Case | Command | Notes |
|----------|---------|-------|
| Exact keyword match | `search "python"` | Fast, local, no API needed |
| Boolean operators | `search "python AND handler"` | AND/OR/NEAR supported |
| Semantic similarity | `search-semantic "code execution" --vector-weight 1.0` | Requires API keys |
| Best results | `search-semantic "query" --vector-weight 0.7` | Hybrid search |

**Use BM25 (`search`) when:**
- You know the exact keywords
- You want fast local search
- You don't have API keys configured
- You need boolean operators (AND/OR/NEAR)

**Use Vector (`search-semantic --vector-weight 1.0`) when:**
- You want semantic similarity
- Exact keywords don't matter
- You're exploring concepts
- You have API keys configured

**Use Hybrid (`search-semantic --vector-weight 0.7`) when:**
- You want the best results
- You need both keyword and semantic matching
- You're doing comprehensive research
- You have API keys configured

## Search Syntax

skill-split uses SQLite FTS5 full-text search with intelligent query processing.

### Basic Search

**Single word:** Finds exact matches
```bash
./skill_split.py search "python"
```

**Multi-word:** Finds sections with ANY word (OR search for discovery)
```bash
./skill_split.py search "git setup"
# Finds sections about git OR setup (broader discovery)
```

### Advanced Syntax

**Exact phrase:** Use quotes for phrase matching
```bash
./skill_split.py search '"git repository"'
# Finds exact phrase "git repository"
```

**AND search:** Both words required
```bash
./skill_split.py search "git AND repository"
# Finds sections with BOTH git AND repository
```

**OR search:** Either word required (explicit)
```bash
./skill_split.py search "git OR repository"
# Finds sections with git OR repository
```

**NEAR search:** Words within proximity
```bash
./skill_split.py search "git NEAR repository"
# Finds "git" near "repository" in text
```

**Complex queries:** Combine operators
```bash
./skill_split.py search '"python handler" OR config'
# Finds exact phrase "python handler" OR sections about config
```

### How Queries Are Processed

1. **Empty/whitespace:** Returns no results
2. **User operators (AND/OR/NEAR):** Used as-is (you know FTS5 syntax)
3. **Quoted phrases:** Exact phrase match
4. **Single word:** Direct match
5. **Multi-word unquoted:** Converts to OR for discovery

**Example conversions:**
- `"python"` → `"python"` (quoted phrase)
- `python` → `python` (single word)
- `python handler` → `"python" OR "handler"` (multi-word → OR)
- `python AND handler` → `python AND handler` (user operator)
- `"python handler" OR config` → `"python handler" OR config` (complex)

### Relevance Scores

Search results include BM25 relevance scores (higher = more relevant):

```bash
$ ./skill_split.py search "python"
Found 3 section(s) matching 'python':

ID      Score   Title                                 Level
-------- -------- ---------------------------------------- ------
42      3.52    Python Handler                        1
15      2.18    Advanced Python Techniques            2
8       1.05    Setup Python Environment              1
```

### File-Specific Search

Search within a specific file:

```bash
./skill_split.py search "python" --file /skills/programming/SKILL.md
```

### Tips

- Use quotes for exact phrases: `"exact words here"`
- Use OR for broader discovery: `term1 OR term2`
- Use AND for narrower results: `term1 AND term2`
- Multi-word without quotes defaults to OR (better discovery)
- Relevance scores help identify most relevant results

### Progressive Disclosure

Load large files section-by-section to minimize token usage.

#### List File Structure

Show all sections with their IDs:
```bash
./skill_split.py list /skills/programming/SKILL.md
```

Output:
```
ID  Title                             Level
--- -------------------------------- ------
1  Overview                         1
2  Installation                     1
3  Usage                            1
4  Advanced Topics                  1
5    Configuration Options          2
6    Performance Tuning             2
7  Troubleshooting                  1
```

#### Get Single Section

Load just one section by ID:
```bash
./skill_split.py get-section 42 --db ~/.claude/databases/skill-split.db
```

#### Navigate Sequentially

Get next section (sibling):
```bash
./skill_split.py next 42 /skills/programming/SKILL.md
```

Navigate to first child subsection:
```bash
./skill_split.py next 42 /skills/programming/SKILL.md --child
```

#### Typical Workflow

1. List file structure to get section IDs
2. Load specific section of interest
3. Use `next` to navigate through content
4. Use `--child` to drill into subsections
5. Use `search` to find relevant content across files

**Token Savings:** Instead of loading entire 50-section skill (21KB), load just one section (204 bytes) - **99% context savings**.

For detailed search and navigation examples, see [EXAMPLES.md](EXAMPLES.md).

---

## Supabase Integration

skill-split includes optional Supabase integration for remote storage and sharing of parsed files.

### Setup

Set environment variables:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_PUBLISHABLE_KEY="your-anon-key"
```

### Ingest Command

Upload local files to Supabase library:

```bash
./skill_split.py ingest ~/.claude/skills/
```

Parses all markdown files in directory and uploads to Supabase.

### List Library

View all files in Supabase:

```bash
./skill_split.py list-library
```

### Search Library

Search across all files in Supabase:

```bash
./skill_split.py search-library "authentication"
```

### Checkout

Deploy a file from Supabase to local path:

```bash
./skill_split.py checkout <file-id> ~/.claude/skills/temp-skill.md
```

Tracks deployment in Supabase for management.

### Checkin

Remove deployed file and update status:

```bash
./skill_split.py checkin ~/.claude/skills/temp-skill.md
```

### Status

View active checkouts:

```bash
./skill_split.py status
```

---

## Use Cases

### Use Case 1: Claude Code Skills

You have a 100KB skill definition with 15 sections. Instead of sending the entire file every interaction:

```bash
# Setup once
./skill_split.py store ~/.claude/skills/my-framework.md

# During a session, retrieve just what you need
./skill_split.py get ~/.claude/skills/my-framework.md "API Reference"
./skill_split.py get ~/.claude/skills/my-framework.md "Examples"
```

**Token Savings**: ~60% reduction for typical multi-section queries.

---

### Use Case 2: Progressive Disclosure Documentation

You're building documentation with nested detail levels. Users should understand the hierarchy before diving deep:

```bash
# Show user the structure first
./skill_split.py tree project-docs.md

# User navigates to sections they care about
./skill_split.py get project-docs.md "Architecture"
./skill_split.py get project-docs.md "Architecture > Database Design"
```

---

### Use Case 3: Cross-File Search Integration

You have 5 related skill files. With progressive disclosure, you can search for relevant sections without loading entire files:

```bash
# Future feature: search across all stored files
./skill_split.py search "authentication" --all

# Returns matching sections from all stored files
# User clicks on relevant result, loads just that section
```

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Entry Point                      │
│                  (skill_split.py)                       │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │     Format Detection                │
        │   (detector.py)                     │
        │                                     │
        │ • YAML frontmatter detection        │
        │ • Markdown heading detection        │
        │ • XML tag detection                 │
        └─────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │     Parser                          │
        │   (parser.py)                       │
        │                                     │
        │ • Extract sections by format        │
        │ • Build section tree                │
        │ • Track byte positions              │
        └─────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │     Database                        │
        │   (database.py)                     │
        │                                     │
        │ • SQLite storage                    │
        │ • Files table (path, hash, mtime)   │
        │ • Sections table (title, level, pos)│
        └─────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │     Recomposer                      │
        │   (recomposer.py)                   │
        │                                     │
        │ • Reconstruct from sections         │
        │ • Preserve exact formatting         │
        │ • Byte-perfect round-trip           │
        └─────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │     Integrity Verification          │
        │   (hashing.py)                      │
        │                                     │
        │ • SHA256 file hashing               │
        │ • Round-trip validation             │
        └─────────────────────────────────────┘
```

### Key Design Principles

1. **Assume Errors to Avoid Them**: Every parse includes validation. Hashes verify exact round-trip.
2. **Keep It Simple**: Pure Python, minimal dependencies, 600 LOC total.
3. **Progressive Disclosure**: Load incrementally instead of all-at-once.
4. **Byte-Perfect**: Round-trip hashing ensures zero data loss.

### Database Schema

**Files Table**:
```
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    original_hash TEXT,
    modified_at TIMESTAMP
);
```

**Sections Table**:
```
CREATE TABLE sections (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    title TEXT,
    level INTEGER,
    content TEXT,
    start_byte INTEGER,
    end_byte INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id)
        ON DELETE CASCADE
);
```

## Component Handler Support (Phase 9)

skill-split now supports specialized Claude Code component types beyond markdown files:

### Supported Components

| Component Type | Files | Handler |
|----------------|-------|---------|
| Plugins | `plugin.json`, `*.mcp.json`, `hooks.json` | PluginHandler |
| Hooks | `hooks.json`, `*.sh` | HookHandler |
| Config | `settings.json`, `mcp_config.json` | ConfigHandler |

### Usage Examples

```bash
# Store a plugin component
./skill_split.py store ~/.claude/plugins/my-plugin/plugin.json

# View plugin structure
./skill_split.py tree ~/.claude/plugins/my-plugin/plugin.json

# Store hooks configuration
./skill_split.py store ~/.claude/plugins/my-plugin/hooks.json

# Store configuration files
./skill_split.py store ~/.claude/settings.json
./skill_split.py store ~/.claude/mcp_config.json
```

### Component Features

- **Multi-file support**: Tracks related files (e.g., plugin.json + .mcp.json)
- **Type validation**: Ensures components follow correct schemas
- **Progressive disclosure**: Load sections on-demand
- **Cross-component search**: Search across all component types

For complete documentation, see [COMPONENT_HANDLERS.md](./COMPONENT_HANDLERS.md) and [HANDLER_INTEGRATION.md](./HANDLER_INTEGRATION.md).

## Testing

### Run All Tests

```bash
pytest -v
```

### Test Coverage

- **Parser Tests** (21 tests): YAML, Markdown headings, XML tags, nested sections
- **Database Tests** (85 tests): Storage, retrieval, cascade delete, FTS5 search, query preprocessing
- **Hashing Tests** (5 tests): Round-trip verification
- **Round-Trip Tests** (8 tests): Full parse → store → recompose cycle
- **Query Tests** (18 tests): Progressive disclosure API
- **CLI Tests** (16 tests): Command-line interface
- **Supabase Tests** (5 tests): Remote storage integration
- **Checkout Tests** (5 tests): File deployment workflow
- **Component Handler Tests** (48 tests): Plugin, Hook, Config handlers
- **Hybrid Search Tests** (80 tests): FTS5, vector search, hybrid ranking
- **Embedding Service Tests** (15 tests): Vector generation and similarity
- **Composer Tests** (25 tests): Skill composition and validation
- **Frontmatter Tests** (12 tests): Auto-generation of skill frontmatter
- **Other Tests** (215 tests): Integration, cross-component, utilities

### Current Test Count

**518 tests passing** (Phases 1-11 complete, including query preprocessing and FTS5 search)

### Example Test Run

```bash
$ pytest -v

test/test_parser.py::test_yaml_frontmatter PASSED
test/test_parser.py::test_markdown_headings PASSED
test/test_parser.py::test_xml_tags PASSED
...
test/test_database.py::test_store_and_retrieve PASSED
test/test_hashing.py::test_round_trip PASSED
...

======================== 28 passed in 2.34s ========================
```

### Testing Philosophy

- **Test-First**: Write verification tests before implementation
- **Edge Cases**: Handle code blocks, nested sections, edge spacing
- **Round-Trip Verification**: Every phase confirms byte-perfect hashing
- **Fixtures**: Real-world examples (YAML skills, nested MD docs, XML structures)

## Advanced Topics

### Supported File Formats

#### Markdown with Headings
```markdown
# Section 1
Content here

## Subsection 1.1
More content

## Subsection 1.2
Even more
```

#### YAML with Frontmatter
```yaml
---
name: my-skill
version: 1.0
---

# Installation
Content...
```

#### XML-Style Tags
```markdown
<skill>
  This entire block is level=-1 (custom)
</skill>

# Normal heading
Regular level 1
```

### Handling Special Cases

**Code Blocks**: Parser respects markdown code fences. Headings inside code blocks are ignored.

```markdown
# Real Heading

# Don't treat this as a heading
```

**Whitespace Preservation**: Round-trip verification ensures exact byte match. Leading spaces, trailing newlines, indentation all preserved.

**YAML Frontmatter**: Extracted and stored separately. Frontmatter content remains available in sections table.

## Future Enhancements (Phases 5-6)

### Phase 5: Query API
- `get_section(id)` - Direct section retrieval
- `get_next_section(id)` - Progressive disclosure navigation
- `get_section_tree(path)` - Full hierarchy in one call
- `search_sections(query)` - Search across all sections

### Phase 6: CLI Completion
- `get-section` command for programmatic access
- `next` command for progressive disclosure workflow
- `list` command for section enumeration
- `search` command for cross-file queries

## Contributing

Report issues, suggest features, or submit PRs. Philosophy: Keep it simple, verify via hashing.

## License

MIT

---

**Last Updated**: 2026-02-08
**Status**: Phases 1-11 Complete (518 tests passing)
**Supabase**: 2,757 files in archival mode
**Next**: Phase 02 - Search Fix (Query preprocessing and documentation)
