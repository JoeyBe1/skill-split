# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

`skill-split` is a Python tool for intelligently splitting YAML and Markdown files by sections and subsections. Each section is stored in a SQLite database to enable progressive disclosure of Claude Code components (skills, commands, references).

### Key Design Principle

The program is written in Python to verify what the LLM "claims." It assumes errors to avoid them and keeps things simple.

## Current State

**Phases 1-9 Complete (125/125 tests passing - 100% core functionality)**

**BUG-001 FIXED (2026-02-04):** Parser newline stripping bug removed - byte-perfect round-trip now verified on all 77 real skills.

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
- QueryAPI commands: get-section, next, list, search
- All 16 commands fully functional with error handling

**Phase 7: Supabase Integration**
- **SupabaseStore**: Remote storage with Supabase backend
- `store_file()` - Upload parsed documents to Supabase
- `get_file()` - Retrieve files with section hierarchy
- `search_sections()` - Full-text search across library
- `list_files()` - Browse available files
- Supabase commands: ingest, list-library, search-library

**Phase 8: Checkout/Checkin Workflow**
- **CheckoutManager**: File deployment and tracking
- `checkout()` - Deploy file to local path, track usage
- `checkin()` - Remove deployed file, update status
- `get_active_checkouts()` - View current deployments
- Checkout commands: checkout, checkin, status

**Phase 9: Component Handlers**
- **PluginHandler**: Parse plugin.json with .mcp.json and hooks.json
- **HookHandler**: Parse hooks.json with shell scripts
- **ConfigHandler**: Parse settings.json and mcp_config.json
- **ComponentDetector**: Automatic file type detection
- **HandlerFactory**: Factory pattern for handler instantiation
- **Multi-file support**: Track related files with combined hashing
- **Type validation**: Schema validation for each component type
- 48 new tests for component handlers

### Files Created
```
skill-split/
├── skill_split.py          # CLI entry point (16 commands)
├── models.py               # Data classes (FileType, FileFormat, Section, etc.)
├── core/
│   ├── __init__.py
│   ├── detector.py         # FormatDetector (XML + headings)
│   ├── parser.py           # Parser (headings, XML tags, frontmatter)
│   ├── database.py         # DatabaseStore (SQLite)
│   ├── hashing.py          # SHA256 file hashing
│   ├── recomposer.py       # Recomposer (byte-perfect round-trip)
│   ├── validator.py        # Validator (round-trip verification)
│   ├── query.py            # QueryAPI (progressive disclosure)
│   ├── supabase_store.py   # SupabaseStore (remote storage)
│   └── checkout_manager.py # CheckoutManager (file deployment)
├── handlers/               # NEW: Component handlers (Phase 9)
│   ├── __init__.py
│   ├── base.py             # BaseHandler abstract interface
│   ├── component_detector.py # Component type detection
│   ├── factory.py          # HandlerFactory for handler creation
│   ├── plugin_handler.py   # PluginHandler (plugin.json)
│   ├── hook_handler.py     # HookHandler (hooks.json)
│   └── config_handler.py   # ConfigHandler (settings.json)
├── test/
│   ├── test_parser.py           # 21 tests (Phases 1 + 4)
│   ├── test_hashing.py          # 5 tests (Phase 2)
│   ├── test_database.py         # 7 tests (Phase 2)
│   ├── test_roundtrip.py        # 8 tests (Phase 3)
│   ├── test_query.py            # 18 tests (Phase 5)
│   ├── test_cli.py              # 16 tests (Phase 6)
│   ├── test_supabase_store.py   # 5 tests (Phase 7)
│   ├── test_checkout_manager.py # 5 tests (Phase 8)
│   └── test_handlers/           # NEW: 48 tests (Phase 9)
│       ├── __init__.py
│       ├── test_component_detector.py # 18 tests
│       ├── test_plugin_handler.py     # 10 tests
│       ├── test_hook_handler.py       # 10 tests
│       └── test_config_handler.py     # 10 tests
├── test/fixtures/
│   └── xml_tags.md         # XML tag fixture (Phase 4)
├── demo/
│   ├── progressive_disclosure.sh  # 8-step end-to-end demo
│   └── sample_skill.md     # Realistic 50+ section example
├── EXAMPLES.md             # Usage scenarios with output
├── COMPONENT_HANDLERS.md   # NEW: Component handler guide
├── HANDLER_INTEGRATION.md  # NEW: Integration guide
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
- **Component handlers**: Type-specific parsers for plugins, hooks, configs
- **Multi-file support**: Track related files with combined hashing
- **Automatic type detection**: Path-based component type detection
- **Round-trip verification**: 100% byte-perfect on all 77 production skills (2026-02-04 verified)
- **Test coverage**: 125 tests across all phases (parser, database, hashing, roundtrip, query, CLI, Supabase, checkout, component handlers)
- **Test status**: 125/125 passing (5 Supabase tests require SUPABASE_URL and SUPABASE_KEY env vars to run)

---

*Last Updated: 2026-02-04 (Phases 1-9 Complete + Component Handlers + 100% Round-Trip Verified)*
