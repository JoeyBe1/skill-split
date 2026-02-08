# Architecture

**Analysis Date:** 2026-02-08

## Pattern Overview

**Overall:** Layered Architecture with Handler Pattern

**Key Characteristics:**
- Clear separation between parsing, storage, and query layers
- Handler pattern for extensible file type support
- Dual storage backend (SQLite + Supabase) with unified interface
- Progressive disclosure design for token-efficient LLM interactions

## Layers

**CLI Layer (`skill_split.py`):**
- Purpose: Command-line interface exposing all functionality
- Location: `skill_split.py`
- Contains: Command handlers, argument parsing, environment setup
- Depends on: `core/` modules, `handlers/`
- Used by: End users, scripts

**Parser Layer (`core/parser.py`, `core/detector.py`, `handlers/`):**
- Purpose: Extract structure from various file formats
- Location: `core/parser.py`, `core/detector.py`, `handlers/*.py`
- Contains: `Parser`, `FormatDetector`, `BaseHandler` subclasses
- Depends on: `models.py`
- Used by: CLI, storage layer

**Storage Layer (`core/database.py`, `core/supabase_store.py`):**
- Purpose: Persist parsed documents and sections
- Location: `core/database.py` (SQLite), `core/supabase_store.py` (Supabase)
- Contains: `DatabaseStore`, `SupabaseStore`
- Depends on: `models.py`, sqlite3/supabase
- Used by: CLI, query layer, composition

**Query Layer (`core/query.py`, `core/hybrid_search.py`, `core/embedding_service.py`):**
- Purpose: Retrieve and search stored sections
- Location: `core/query.py`, `core/hybrid_search.py`, `core/embedding_service.py`
- Contains: `QueryAPI`, `HybridSearch`, `EmbeddingService`
- Depends on: Storage layer
- Used by: CLI, search commands

**Validation Layer (`core/validator.py`, `core/recomposer.py`, `core/hashing.py`):**
- Purpose: Verify round-trip integrity
- Location: `core/validator.py`, `core/recomposer.py`, `core/hashing.py`
- Contains: `Validator`, `Recomposer`, hash functions
- Depends on: Storage layer, models
- Used by: CLI verify command

**Composition Layer (`core/skill_composer.py`, `core/frontmatter_generator.py`, `core/skill_validator.py`):**
- Purpose: Create new skills from existing sections
- Location: `core/skill_composer.py`, `core/frontmatter_generator.py`, `core/skill_validator.py`
- Contains: `SkillComposer`, frontmatter generators, validators
- Depends on: Query layer, storage layer
- Used by: CLI compose command

**Deployment Layer (`core/checkout_manager.py`):**
- Purpose: File deployment and checkout/checkin
- Location: `core/checkout_manager.py`
- Contains: `CheckoutManager`
- Depends on: `core/supabase_store.py`, `core/recomposer.py`
- Used by: CLI checkout/checkin commands

## Data Flow

**Parsing Flow:**

1. User invokes CLI command (e.g., `parse`, `store`, `verify`)
2. CLI uses `FormatDetector` or `HandlerFactory` to determine file type
3. Appropriate parser is selected:
   - `Parser` for markdown/XML files
   - `PluginHandler`, `HookHandler`, `ConfigHandler` for JSON components
   - Script handlers (`PythonHandler`, `JavaScriptHandler`, etc.) for code files
4. Parser returns `ParsedDocument` with hierarchical `Section` objects
5. Document is stored to database with SHA256 hash

**Query Flow:**

1. User invokes query command (e.g., `get-section`, `search`, `list`)
2. `QueryAPI` queries the database
3. Results returned as `Section` objects with optional file_type metadata
4. For vector search: `EmbeddingService` generates query embedding, `HybridSearch` combines vector + text results

**Composition Flow:**

1. User provides section IDs to `compose` command
2. `SkillComposer` retrieves sections via `QueryAPI`
3. Hierarchy is rebuilt from flat sections using level-based sorting
4. `FrontmatterGenerator` creates enriched YAML frontmatter
5. Content written to filesystem and optionally uploaded to Supabase

**Deployment Flow:**

1. User invokes `checkout` command with file_id
2. `CheckoutManager` retrieves file from `SupabaseStore`
3. `Recomposer` reconstructs file content from sections
4. Related files deployed for multi-file components (plugins, hooks)
5. Files written to target path
6. Checkout recorded in database

**State Management:**
- SQLite: Local cache, fast queries, CASCADE delete for referential integrity
- Supabase: Remote storage, checkout tracking, vector search with pgvector
- Both maintain identical schema for section hierarchy with parent_id relationships

## Key Abstractions

**Section (`models.py`):**
- Purpose: Represents a parsed document fragment
- Examples: Markdown heading with content, XML tag block, function definition
- Pattern: Hierarchical tree with parent/child references, level indicates depth

**ParsedDocument (`models.py`):**
- Purpose: Container for fully parsed file
- Examples: Skill file with frontmatter and sections, plugin with config sections
- Pattern: Aggregates frontmatter + hierarchical sections, tracks file_type and format

**BaseHandler (`handlers/base.py`):**
- Purpose: Abstract interface for type-specific file handlers
- Examples: `PluginHandler`, `PythonHandler`, `ShellHandler`
- Pattern: Template method - subclasses implement parse(), validate(), get_related_files()

**FileType / FileFormat (`models.py`):**
- Purpose: Enumerations for type detection
- Examples: FileType.PLUGIN, FileFormat.MARKDOWN_HEADINGS
- Pattern: Category system enabling handler dispatch via HandlerFactory

## Entry Points

**CLI Main (`skill_split.py`):**
- Location: `skill_split.py`
- Triggers: `./skill_split.py <command> [args]`
- Responsibilities: Argument parsing, environment loading, command dispatch

**Core Commands:**
- `parse` - Parse file and display structure
- `validate` - Validate file structure
- `store` - Store parsed file in database
- `verify` - Round-trip verification
- `get-section` - Retrieve single section by ID
- `search` - Search sections by keyword
- `search-semantic` - Hybrid vector + text search
- `compose` - Create new skill from sections
- `checkout`/`checkin` - Deploy files from library

**Ingestion Scripts:**
- `ingest_to_supabase.py` - Batch file ingestion to Supabase
- `batch_ingest_supabase.py` - Bulk ingestion with progress tracking
- `scripts/generate_embeddings.py` - Generate vector embeddings

## Error Handling

**Strategy:** Defensive validation with clear error messages

**Patterns:**
- FileNotFoundError raised when files don't exist during handler initialization
- ValueError raised for invalid input (missing sections, bad paths)
- sqlite3.Error propagated for database issues
- ImportError with graceful degradation for optional dependencies (Supabase, OpenAI)
- ValidationResult aggregates errors and warnings for batched reporting

## Cross-Cutting Concerns

**Logging:** Minimal - primarily stderr output for warnings and errors
**Validation:** SHA256 hash verification for round-trip integrity at parse/store/verify stages
**Authentication:** Supabase credentials via environment variables (SUPABASE_URL, SUPABASE_KEY)
**Multi-file Support:** Related file tracking via ComponentMetadata and get_related_files() pattern

---

*Architecture analysis: 2026-02-08*
