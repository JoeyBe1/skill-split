# Codebase Structure

**Analysis Date:** 2026-02-08

## Directory Layout

```
skill-split/
├── skill_split.py              # Main CLI entry point
├── models.py                  # Data models and enums
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── core/                      # Core functionality
│   ├── parser.py              # Markdown/YAML parser
│   ├── database.py            # SQLite storage operations
│   ├── recomposer.py          # File reconstruction
│   ├── validator.py            # Round-trip validation
│   ├── detector.py            # File format detection
│   ├── hashing.py             # SHA256 integrity
│   ├── query.py               # Progressive disclosure API
│   ├── query_interface.py     # Query interface implementation
│   ├── frontmatter_generator.py # Auto-generates frontmatter
│   ├── skill_composer.py      # Composes new skills
│   ├── skill_validator.py      # Validates composed skills
│   ├── supabase_store.py      # Remote storage integration
│   ├── checkout_manager.py    # File deployment tracking
│   ├── embedding_service.py   # Vector embeddings
│   └── hybrid_search.py       # BM25 + Vector search
├── handlers/                   # Component and script handlers
│   ├── base.py                # Abstract handler base
│   ├── factory.py             # Handler creation
│   ├── component_detector.py  # File type detection
│   ├── plugin_handler.py      # Plugin.json parsing
│   ├── hook_handler.py        # Hook parsing
│   ├── config_handler.py     # Config parsing
│   ├── script_handler.py     # Base for script parsing
│   ├── python_handler.py      # Python files
│   ├── javascript_handler.py # JavaScript files
│   ├── typescript_handler.py  # TypeScript files
│   └── shell_handler.py       # Shell scripts
├── test/                      # Test suite
│   ├── test_*.py              # Core module tests
│   ├── test_handlers/         # Handler-specific tests
│   └── fixtures/              # Test data files
├── demo/                      # Demonstration scripts
├── migrations/                # Database schema migrations
├── .archive/                  # Historical artifacts
└── .planning/                 # Project planning documents
```

## Directory Purposes

**[core/]:**
- Purpose: Fundamental processing pipeline
- Contains: Parser, database, recomposer, validation
- Key files:
  - `parser.py` - Markdown/YAML structure extraction
  - `database.py` - SQLite with CASCADE delete
  - `recomposer.py` - Byte-perfect reconstruction
  - `query.py` - Progressive disclosure API

**[handlers/]:**
- Purpose: Specialized file type processing
- Contains: Factory, detector, and specific handlers
- Key files:
  - `factory.py` - Handler creation and selection
  - `component_detector.py` - File type detection
  - `plugin_handler.py` - Plugin JSON parsing
  - `script_handler.py` - Base for script handlers

**[test/]:**
- Purpose: Comprehensive test coverage
- Contains: Unit tests, integration tests, fixtures
- Key files:
  - `test_parser.py` - Parser functionality
  - `test_database.py` - Database operations
  - `test_handlers/` - Handler-specific tests

**[demo/]:**
- Purpose: Usage demonstrations
- Contains: Shell scripts showing end-to-end usage

**[migrations/]:**
- Purpose: Database schema evolution
- Contains: SQL migration scripts

## Key File Locations

**Entry Points:**
- `skill_split.py` - Main CLI with 16 commands
- `core/parser.py` - File parsing entry point
- `core/query.py` - Query API entry point

**Configuration:**
- `models.py` - Type definitions and enums
- `requirements.txt` - Python dependencies
- `.env` - Environment variables

**Core Logic:**
- `core/database.py` - SQLite operations with foreign keys
- `core/recomposer.py` - File reconstruction
- `core/validator.py` - Round-trip validation
- `core/hashing.py` - Integrity verification

**Testing:**
- `test/` - All test files
- `test/fixtures/` - Test data files

## Naming Conventions

**Files:**
- `snake_case.py` for Python modules
- `PascalCase` for class names
- `camelCase` for method names
- `SCREAMING_SNAKE_CASE` for constants

**Functions:**
- `verb_noun()` - Action-oriented names
- `get_thing()` - Getter pattern
- `is_thing()` - Predicate pattern
- `_internal_method()` - Private methods with underscore

**Variables:**
- `snake_case` for local variables
- `camelCase` for loop variables
- `_private_var` for internal use

## Where to Add New Code

**New File Type Handler:**
- Implementation: `handlers/new_handler.py`
- Registration: Update `handlers/component_detector.py`
- Tests: Add to `test/test_handlers/`

**New Search Mode:**
- Implementation: Extend `core/hybrid_search.py`
- CLI command: Add to `skill_split.py`
- Tests: Add to `test/test_query.py`

**New Validation Rule:**
- Implementation: Extend `core/validator.py`
- Integration: Update round-trip validation
- Tests: Add validation tests

**New Database Feature:**
- Implementation: Extend `core/database.py`
- Schema: Update `migrations/` if needed
- Tests: Add database operation tests

**New Component Type:**
- Implementation: New handler in `handlers/`
- Detection: Update `handlers/component_detector.py`
- Factory: Update `handlers/factory.py`

## Special Directories

**[.planning/]:**
- Purpose: Project planning and documentation
- Contains: Phase plans, architecture docs, test reports
- Generated: By GSD workflow
- Committed: Yes

**[.archive/]:**
- Purpose: Historical artifacts and deprecated code
- Contains: Old versions, investigations, reports
- Generated: By cleanup processes
- Committed: Yes (for history)

**[test/fixtures/]:**
- Purpose: Test data files
- Contains: Sample markdown, JSON, script files
- Generated: Manual creation
- Committed: Yes

---

*Structure analysis: 2026-02-08*