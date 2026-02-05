# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

`skill-split` is a Python tool for intelligently splitting YAML and Markdown files by sections and subsections. Each section is stored in a SQLite database to enable progressive disclosure of Claude Code components (skills, commands, references).

### Key Design Principle

The program is written in Python to verify what the LLM "claims." It assumes errors to avoid them and keeps things simple.

## Current State

**Phases 1-6 Complete (75/75 tests passing)**

### What's Complete

**Phase 1-4: Core Parser & Database**
- **Parser**: YAML frontmatter, markdown headings, XML tags (Phase 1)
- **Database**: SQLite storage with files + sections tables (Phase 2)
- **Recomposer**: Byte-perfect round-trip, SHA256 hashing (Phase 3)
- **Format Detection**: XML tags with level=-1 support (Phase 4)

**Phase 5: Query API**
- `get_section(id)` - Single section retrieval
- `get_next_section(id)` - Progressive section navigation
- `get_section_tree(path)` - Full hierarchy view
- `search_sections(query, file_path)` - Cross-file and single-file search
- Returns (section_id, Section) tuples for progressive disclosure

**Phase 6: Complete CLI**
- Core commands: parse, validate, store, get, tree, verify
- Supabase commands: ingest, checkout, checkin, list-library, search-library, status
- QueryAPI commands: get-section, next, list, search
- All 16 commands fully functional with error handling

### Files Created
```
skill-split/
├── skill_split.py          # CLI entry point (16 commands)
├── models.py               # Data classes
├── core/
│   ├── __init__.py
│   ├── detector.py         # FormatDetector (XML + headings)
│   ├── parser.py           # Parser (headings, XML tags, frontmatter)
│   ├── database.py         # DatabaseStore (SQLite)
│   ├── hashing.py          # SHA256 file hashing
│   ├── recomposer.py       # Recomposer (byte-perfect round-trip)
│   ├── validator.py        # Validator (round-trip verification)
│   └── query.py            # QueryAPI (progressive disclosure)
├── test/
│   ├── test_parser.py      # 21 tests (Phases 1 + 4)
│   ├── test_hashing.py     # 5 tests (Phase 2)
│   ├── test_database.py    # 7 tests (Phase 2)
│   ├── test_roundtrip.py   # 8 tests (Phase 3)
│   ├── test_query.py       # 18 tests (Phase 5)
│   └── test_cli.py         # 16 tests (Phase 6)
├── test/fixtures/
│   └── xml_tags.md         # XML tag fixture (Phase 4)
├── demo/
│   ├── progressive_disclosure.sh  # 8-step end-to-end demo
│   └── sample_skill.md     # Realistic 50+ section example
├── EXAMPLES.md             # 3 usage scenarios with output
├── README.md               # Complete documentation
└── .claude/skills/skill-split.md  # Claude Code skill wrapper
```

## Quick Start

```bash
# Parse and display structure
./skill_split.py parse <file>

# Validate file structure
./skill_split.py validate <file>

# Store in database
./skill_split.py store <file>

# Get single section by ID
./skill_split.py get-section <id> --db <database>

# Show section hierarchy with IDs
./skill_split.py list <file> --db <database>

# Search sections across files
./skill_split.py search <query> --db <database>

# Full documentation: See EXAMPLES.md
```

## Demo

End-to-end walkthrough: `./demo/progressive_disclosure.sh`

This 8-step demo shows parse, validate, store, verify, list, tree, search, and get commands working together.

## Usage Examples

See [EXAMPLES.md](./EXAMPLES.md) for detailed scenarios:
1. Progressive disclosure workflow
2. Cross-file search
3. Tree navigation

## Key Technical Properties

- **Round-trip verification**: EXACT byte match required (SHA256 hashing)
- **Database**: SQLite with CASCADE delete on file removal
- **Line numbering**: 1-based for human debugging
- **Code block aware**: Doesn't split inside ``` fences
- **Progressive disclosure**: Load sections incrementally, save tokens
- **XML tag support**: Parse `<tag>content</tag>` style with level=-1
- **Test coverage**: 75 tests across all phases (parser, database, hashing, roundtrip, query, CLI)

---

*Last Updated: 2026-02-03 (Phases 1-6 Complete)*
