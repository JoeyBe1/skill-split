# Architecture

**Analysis Date:** 2026-02-08

## Pattern Overview

**Overall:** Layered Pipeline Architecture with Handler Extension Pattern

**Key Characteristics:**
- Multi-stage file processing pipeline
- Plugin-based handler system for component types
- Progressive disclosure via database storage
- Hybrid search (BM25 + Vector)
- Byte-perfect round-trip capability

## Layers

**[CLI Layer]:**
- Purpose: Command-line interface and argument parsing
- Location: `skill_split.py`
- Contains: Command dispatchers, argument parsing
- Depends on: Core modules, Handlers
- Used by: End users, scripts

**[Core Layer]:**
- Purpose: Fundamental parsing, storage, and reconstruction operations
- Location: `core/` directory
- Contains: Parser, DatabaseStore, Recomposer, Validator, QueryAPI
- Depends on: Models layer
- Used by: CLI layer, Handlers

**[Handler Layer]:**
- Purpose: Specialized parsing for different file types
- Location: `handlers/` directory
- Contains: Factory, ComponentDetector, specific handlers (plugin, hook, config, scripts)
- Depends on: Core layer, Models
- Used by: CLI layer, Core layer (for recomposition)

**[Models Layer]:**
- Purpose: Data structures and type definitions
- Location: `models.py`
- Contains: Section, FileMetadata, ParsedDocument, FileType, FileFormat enums
- Depends on: Python standard library
- Used by: All other layers

## Data Flow

**File Ingestion Pipeline:**

1. **CLI Command** → `cmd_parse/store/verify`
2. **File Detection** → `HandlerFactory.is_supported()` or `FormatDetector`
3. **Handler Selection** → `HandlerFactory.create_handler()` or `Parser`
4. **Parsing** → Handler-specific parsing or markdown parsing
5. **Hashing** → `compute_file_hash()` or `compute_combined_hash()`
6. **Storage** → `DatabaseStore.store_file()`
7. **Validation** → `Validator.validate_round_trip()`

**Progressive Disclosure:**

1. **Query Request** → `QueryAPI.get_section()`
2. **Database Lookup** → `DatabaseStore.get_section()`
3. **Section Return** → Single section for minimal token usage
4. **Navigation** → `get_next_section()` for progressive traversal

**Search Pipeline:**

1. **Search Query** → `QueryAPI.search_sections()` or `HybridSearch`
2. **Keyword Search** → FTS5 BM25 ranking
3. **Vector Search** → OpenAI embeddings + similarity
4. **Hybrid Results** → Combined scores with configurable weights
5. **Result Return** → Ranked sections with scores

**Round-Tip Verification:**

1. **Original File** → Parse and store in database
2. **Database Storage** → Sections with metadata and hash
3. **Recomposition** → `Recomposer.recompose()`
4. **Hash Verification** → Compare original vs recomposed hash
5. **Validation Report** → Success/failure with error details

## Key Abstractions

**[Section]:**
- Purpose: Represents a document section with hierarchy
- Examples: `core/parser.py`, `models.py`
- Pattern: Tree structure with parent-child relationships

**[FileMetadata]:**
- Purpose: Tracks file-level information
- Examples: `core/database.py` (files table)
- Pattern: Entity with type, path, hash, timestamps

**[Handler]:**
- Purpose: Abstract file type processing
- Examples: `handlers/base.py`, `handlers/plugin_handler.py`
- Pattern: Strategy pattern with common interface

**[DatabaseStore]:**
- Purpose: Data persistence with foreign key constraints
- Examples: `core/database.py`
- Pattern: Repository pattern with SQLite

**[QueryAPI]:**
- Purpose: Progressive disclosure interface
- Examples: `core/query.py`
- Pattern: Gateway pattern for section-by-section access

## Entry Points

**[Main CLI]:**
- Location: `skill_split.py`
- Triggers: Command-line arguments
- Responsibilities: Command dispatch, argument validation

**[Parser]:**
- Location: `core/parser.py`
- Triggers: File parsing requests
- Responsibilities: Markdown/YAML structure extraction

**[HandlerFactory]:**
- Location: `handlers/factory.py`
- Triggers: File type detection
- Responsibilities: Handler selection and creation

**[DatabaseStore]:**
- Location: `core/database.py`
- Triggers: Data persistence requests
- Responsibilities: CRUD operations for files and sections

**[QueryAPI]:**
- Location: `core/query.py`
- Triggers: Section retrieval requests
- Responsibilities: Progressive disclosure of content

## Error Handling

**Strategy:** Layered validation with descriptive errors

**Patterns:**
- Parser validates file structure before processing
- Database uses foreign key constraints and CASCADE delete
- Validator checks byte-perfect round-trip integrity
- CLI provides clear error messages with file paths

## Cross-Cutting Concerns

**Logging:**
- Minimal logging (print statements in CLI)
- Structured error messages with context
- Hash verification results

**Validation:**
- Schema validation at database level
- Round-trip integrity checking
- Handler-specific validation rules

**Authentication:**
- Supabase credential validation
- Environment-based configuration

---

*Architecture analysis: 2026-02-08*