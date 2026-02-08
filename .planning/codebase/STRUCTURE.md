# Codebase Structure

**Analysis Date:** 2026-02-08

## Directory Layout

```
skill-split/
├── core/               # Core parsing, storage, and query modules
├── handlers/           # File type-specific handlers (plugins, scripts)
├── test/               # Test suite with 499 tests
├── test/test_handlers/ # Handler-specific tests
├── test/fixtures/      # Test fixtures and sample files
├── migrations/         # Database schema migrations
├── scripts/            # Utility scripts (embedding generation, monitoring)
├── demo/               # Demo scripts and examples
├── tests/              # Legacy test directory (plugins, agents)
├── .archive/           # Archived development artifacts
├── .planning/          # Planning and codebase documentation
├── .serena/            # Serena memory system cache
├── .claude/            # Claude Code configuration and skills
├── skill_split.py      # Main CLI entry point
├── models.py           # Data models and enums
├── conftest.py         # Pytest configuration
└── requirements.txt    # Python dependencies
```

## Directory Purposes

**core/:**
- Purpose: Core parsing, storage, and query functionality
- Contains: Parser, database stores, query API, composition logic, vector search
- Key files: `parser.py`, `database.py`, `supabase_store.py`, `query.py`, `skill_composer.py`

**handlers/:**
- Purpose: File type-specific parsing via handler pattern
- Contains: Base handler, factory, component and script handlers
- Key files: `base.py`, `factory.py`, `plugin_handler.py`, `python_handler.py`, `shell_handler.py`

**test/ and test/test_handlers/:**
- Purpose: Comprehensive test coverage for all modules
- Contains: Unit tests, integration tests, fixtures
- Key files: `test_parser.py`, `test_database.py`, `test_handlers/test_plugin_handler.py`

**migrations/:
- Purpose: Database schema evolution and Supabase setup
- Contains: SQL migration scripts, migration guide
- Key files: `enable_pgvector.sql`, `create_embeddings_table.sql`, `SCHEMA_MIGRATION_GUIDE.md`

**scripts/:**
- Purpose: Operational utilities for embedding generation and monitoring
- Contains: Batch embedding generation, metadata monitoring
- Key files: `generate_embeddings.py`, `monitor_embeddings.py`

**demo/:**
- Purpose: Example usage and demonstration scripts
- Contains: Progressive disclosure demo, handler demos
- Key files: `progressive_disclosure.sh`, `script_handlers_demo.py`

## Key File Locations

**Entry Points:**
- `skill_split.py`: Main CLI with 16 commands for parsing, querying, composing
- `models.py`: All data classes (Section, ParsedDocument, FileFormat, FileType enums)

**Configuration:**
- `.env`: Environment variables (SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, SKILL_SPLIT_DB)
- `conftest.py`: Pytest fixtures and test configuration

**Core Logic:**
- `core/parser.py`: Markdown/XML parsing with heading and tag support
- `core/database.py`: SQLite storage with CASCADE delete and hierarchical queries
- `core/supabase_store.py`: Supabase client with vector search and checkout tracking
- `core/query.py`: Progressive disclosure API (get_section, get_next_section, search_sections)
- `core/skill_composer.py`: Skill composition from multiple sections
- `core/checkout_manager.py`: File deployment with multi-file support
- `core/hybrid_search.py`: Vector + text search with adjustable weighting
- `core/embedding_service.py`: OpenAI embeddings with caching and batch generation

**Handlers:**
- `handlers/base.py`: Abstract BaseHandler class defining handler interface
- `handlers/factory.py`: HandlerFactory for creating appropriate handlers
- `handlers/component_detector.py`: File type detection from path patterns
- `handlers/plugin_handler.py`: Plugin component parsing (plugin.json + .mcp.json + hooks.json)
- `handlers/hook_handler.py`: Hook component parsing (hooks.json + shell scripts)
- `handlers/config_handler.py`: Settings and MCP config parsing
- `handlers/python_handler.py`: Python file parsing (classes, functions, methods)
- `handlers/javascript_handler.py`: JavaScript/JSX parsing
- `handlers/typescript_handler.py`: TypeScript/TSX parsing with interface support
- `handlers/shell_handler.py`: Shell script function block parsing

**Testing:**
- `test/test_parser.py`: Parser tests for markdown, XML, mixed formats
- `test/test_database.py`: DatabaseStore CRUD and cascade tests
- `test/test_supabase_store.py`: SupabaseStore integration tests
- `test/test_handlers/`: Individual handler tests with fixtures
- `test/test_skill_composer.py`: Composition logic tests
- `test/test_vector_search*.py`: Hybrid search integration tests

## Naming Conventions

**Files:**
- `core/<module>.py`: Core functionality modules
- `handlers/<type>_handler.py`: Handler implementations
- `test/test_<module>.py`: Test files matching source modules
- `<script>.py`: Standalone scripts in root directory

**Directories:**
- `core/`: Core business logic
- `handlers/`: Pluggable file type handlers
- `test/`: All test code (pytest)
- `test/fixtures/`: Test data and sample files
- `migrations/`: Database schema changes
- `scripts/`: Operational utilities
- `demo/`: Usage examples

**Classes:**
- `<Name>Handler`: Handler classes (e.g., PluginHandler, PythonHandler)
- `<Name>Store`: Storage backends (e.g., DatabaseStore, SupabaseStore)
- `<Name>API`: Query interfaces (e.g., QueryAPI)
- <Name>Manager`: Complex orchestration (e.g., CheckoutManager, SkillComposer)

**Functions:**
- `cmd_<name>()`: CLI command handlers in skill_split.py
- `_<name>()`: Private methods within classes
- `is_<name>()`: Boolean predicate functions
- `get_<name>()`: Getter/retrieval functions

## Where to Add New Code

**New Handler (file type support):**
- Primary code: `handlers/<type>_handler.py`
- Base class: Extend `handlers/base.py::BaseHandler`
- Tests: `test/test_handlers/test_<type>_handler.py`
- Factory: Register in `handlers/factory.py::HandlerFactory.get_handler_for_type()`
- Detector: Add pattern to `handlers/component_detector.py`

**New Core Module:**
- Implementation: `core/<module>.py`
- Tests: `test/test_<module>.py`
- Import pattern: Use `from core.<module> import <Name>` in CLI

**New CLI Command:**
- Implementation: `skill_split.py::cmd_<name>()`
- Registration: Add subparser in `skill_split.py::main()`

**New Database Migration:**
- Schema: `migrations/<description>.sql`
- Documentation: Update `migrations/SCHEMA_MIGRATION_GUIDE.md`

**New Search/Query Feature:**
- Implementation: `core/<feature>.py`
- Integration: Add to `core/query.py::QueryAPI` or create new service
- Tests: `test/test_<feature>.py`

**Utilities:**
- Shared helpers: `core/<utility>.py` or root-level `<utility>.py`
- Standalone scripts: `scripts/<script>.py`

## Special Directories

**.planning/:**
- Purpose: Planning documents and codebase analysis (this file)
- Generated: Yes - by GSD mapping commands
- Committed: Yes - part of repository

**.claude/:**
- Purpose: Claude Code configuration and local skills
- Generated: Partially - insights/ subdirectory is generated
- Committed: Configuration committed, insights may be ephemeral

**.archive/:**
- Purpose: Historical development artifacts, old reports
- Generated: Yes - from previous development cycles
- Committed: Yes - for historical reference

**.serena/:**
- Purpose: Serena memory system cache
- Generated: Yes - by Serena agent
- Committed: No - cached data, may be gitignored

**.pytest_cache/:**
- Purpose: Pytest cache for optimized test runs
- Generated: Yes - automatically by pytest
- Committed: No - gitignored

**__pycache__/:**
- Purpose: Python bytecode cache
- Generated: Yes - automatically by Python interpreter
- Committed: No - gitignored

**node_modules/:**
- Purpose: Node.js dependencies (if any present)
- Generated: Yes - by npm install
- Committed: No - gitignored

**migrations/:**
- Purpose: Database schema migrations for Supabase
- Generated: No - manually authored SQL scripts
- Committed: Yes - version controlled schema changes

---

*Structure analysis: 2026-02-08*
