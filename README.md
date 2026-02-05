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

### 1. Parse a File

Get an overview of all sections in a file without storing it:

```bash
./skill_split.py parse docs/my-skill.md
```

Output shows section hierarchy:
```
File: docs/my-skill.md
Total sections: 12

Level 1: What it does (bytes 0-450)
  Level 2: Key Features (bytes 451-1200)
  Level 2: Why This Matters (bytes 1201-2000)
Level 1: Installation (bytes 2001-3500)
  Level 2: Prerequisites (bytes 3501-3800)
  Level 2: From Source (bytes 3801-5000)
...
```

### 2. Store a File in the Database

```bash
./skill_split.py store docs/my-skill.md
```

This creates or updates the SQLite database with all sections. The database tracks:
- File path and modification time
- Section title, level, and content
- Byte positions for exact recomposition

### 3. Retrieve a Single Section

```bash
./skill_split.py get docs/my-skill.md "Installation"
```

Output:
```
=== Installation (Level 1, Section ID: 2) ===

### Prerequisites

- Python 3.8+
- Click
...
```

### 4. View Section Tree

See the full hierarchy without loading content:

```bash
./skill_split.py tree docs/my-skill.md
```

Output:
```
docs/my-skill.md
├── What it does (Level 1)
│   ├── Key Features (Level 2)
│   └── Why This Matters (Level 2)
├── Installation (Level 1)
│   ├── Prerequisites (Level 2)
│   └── From Source (Level 2)
└── Testing (Level 1)
    └── Running Tests (Level 2)
```

### 5. Validate File Structure

Check if a file can be parsed correctly:

```bash
./skill_split.py validate docs/my-skill.md
```

Returns exit code 0 if valid, non-zero if problems found.

### 6. Verify Round-Trip Integrity

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
- **Database Tests** (7 tests): Storage, retrieval, cascade delete
- **Hashing Tests** (5 tests): Round-trip verification
- **Round-Trip Tests** (8 tests): Full parse → store → recompose cycle
- **Query Tests** (18 tests): Progressive disclosure API
- **CLI Tests** (16 tests): Command-line interface
- **Supabase Tests** (5 tests): Remote storage integration
- **Checkout Tests** (5 tests): File deployment workflow
- **Component Handler Tests** (48 tests): Plugin, Hook, Config handlers

### Current Test Count

**125 tests passing** (Phases 1-9 complete, 5 Supabase tests skipped without env vars)

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

**Last Updated**: 2026-02-04
**Status**: Phases 1-9 Complete (123 tests passing)
**Next**: Phase 10 - Advanced Component Types (Agents, Output Styles)
