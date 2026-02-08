# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Start Here

Also read `AGENTS.md` (agent-wide rules and workflow guardrails) and `CODEX.md` (init checklist).

## Project Purpose

`skill-split` is a Python tool for intelligently splitting YAML and Markdown files by sections and subsections. Each section is stored in a SQLite database to enable progressive disclosure of Claude Code components (skills, commands, references).

### Key Design Principle

The program is written in Python to verify what the LLM "claims." It assumes errors to avoid them and keeps things simple.

## Current State

**ACTIVE PHASE: 02-search_fix (Planning Complete, Ready to Execute)**

**Phases 1-11 Complete (518/518 tests passing)**

**Phase 02: Search Fix (5 plans ready)**
- BM25 (Keywords): FTS5 full-text search
- Vector (Semantic): OpenAI embeddings
- Hybrid (Combined): BM25 + Vector

**Real-World Testing Complete:**
- 1,365 skill files ingested (19,207 sections)
- 3 database systems verified (local demo, production SQLite, Supabase cloud)
- 99% context savings confirmed (21KB → 204 bytes per section)
- Byte-perfect round-trip on complex 92-section files
- Schema migration tested and documented
- Skill Composition verified with absolute line number tracking

### What's Complete

**Phase 1-4: Core Parser & Database**
- Parser: YAML frontmatter, markdown headings, XML tags
- Database: SQLite storage with CASCADE delete
- Recomposer: Byte-perfect round-trip, SHA256 hashing
- Format Detection: XML tags with level=-1 support

**Phase 5: Query API** - Progressive disclosure (get_section, get_next_section, get_section_tree, search_sections)

**Phase 6: Complete CLI** - 16 commands fully functional

**Phase 7: Supabase Integration** - Remote storage with full-text search

**Phase 8: Checkout/Checkin** - File deployment and tracking

**Phase 9: Component Handlers** - Plugins, hooks, configs with multi-file support

**Phase 10: Script Handlers** - Python, JavaScript, TypeScript, Shell parsing

**Phase 11: Skill Composition** - Assemble new skills from existing sections

## Development Commands

### Testing
```bash
# Run all tests
python -m pytest test/ -v

# Run specific test file
python -m pytest test/test_parser.py -v

# Run tests with coverage
python -m pytest test/test_parser.py --cov=core/parser

# Run specific test class
python -m pytest test/test_handlers/test_plugin_handler.py::TestPluginHandler
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-mock
```

## Core Architecture

**Main Modules (`core/`)**:
- `parser.py` - Extracts structure from markdown/YAML files
- `detector.py` - Detects file format (markdown, XML, mixed)
- `database.py` - SQLite operations with CASCADE delete
- `hashing.py` - SHA256 integrity verification
- `recomposer.py` - Reconstructs files for byte-perfect round-trip
- `validator.py` - Validates structure and round-trip integrity
- `query.py` - Query API for progressive disclosure
- `supabase_store.py` - Remote storage with Supabase
- `checkout_manager.py` - File deployment and checkout/checkin
- `skill_composer.py` - Composes new skills from sections
- `skill_validator.py` - Validates composed skills
- `frontmatter_generator.py` - Auto-generates frontmatter
- `embedding_service.py` - Vector embeddings for semantic search
- `hybrid_search.py` - Combines keyword and vector search

**Handlers (`handlers/`)**:
- `base.py` - Abstract base class
- `factory.py` - Factory pattern for handler creation
- `component_detector.py` - Component type detection
- `plugin_handler.py` - Parses plugin.json
- `hook_handler.py` - Parses hooks.json
- `config_handler.py` - Parses settings.json and mcp_config.json
- `script_handler.py` - Base for script file parsing
- `python_handler.py` - Python files (class/function/method)
- `javascript_handler.py` - JavaScript/JSX files
- `typescript_handler.py` - TypeScript/TSX files with interfaces
- `shell_handler.py` - Shell script function blocks

**Models (`models.py`)**:
- Data classes: Section, FileMetadata, ParsedDocument, FileType, FileFormat

## CLI Commands

**Core:** `parse`, `validate`, `store`, `get`, `tree`, `verify`
**Query:** `get-section`, `next`, `list`, `search`
**Search:** `search` (BM25 keywords), `search-semantic` (Vector/Hybrid)
**Supabase:** `ingest`, `checkout`, `checkin`, `list-library`, `status`, `search-library`
**Composition:** `compose --sections <ids> --output <file>`

## Quick Start

### Parse and Structure

```bash
# Parse a markdown file
./skill_split.py parse <file>

# Validate file structure
./skill_split.py validate <file>

# Store in database
./skill_split.py store <file>
```

### Search and Retrieve

```bash
# BM25 keyword search (fast, local)
./skill_split.py search "python handler"

# Semantic/Hybrid search (requires API keys)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 0.7

# Show section hierarchy with IDs
./skill_split.py list <file> --db <database>

# Get single section by ID
./skill_split.py get-section <id> --db <database>
```

### Progressive Disclosure

```bash
# Navigate sequentially (next sibling)
./skill_split.py next <id> <file>

# Drill into subsections (first child)
./skill_split.py next <id> <file> --child

# Compose new skill from sections
./skill_split.py compose --sections 1,2,3 --output new_skill.md
```

## Production Deployment

**IMPORTANT:** See [DEPLOYMENT_STATUS.md](./DEPLOYMENT_STATUS.md) for current deployment capabilities.

**Database Locations:**
- **Demo**: `./skill_split.db` (1 file, 4 sections)
- **Production**: `~/.claude/databases/skill-split.db` (1,365 files, 19,207 sections)
- **Supabase**: Cloud remote storage (fully functional)

**Deployment Capabilities (2026-02-06):**
- Single-file checkout: Production ready (skills, commands, scripts)
- Multi-file checkout: FIXED - Deploys plugins with .mcp.json, hooks with scripts
- All components runtime-ready: Skills, commands, scripts, plugins, hooks
- Composition: Can create new skills from library sections

**Schema Migration (if needed):**
```bash
sqlite3 ~/.claude/databases/skill-split.db "ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT '';"
```

## Search and Navigation

### Three Search Modes

**1. BM25 Search (Keywords)** - `search` command
- FTS5 full-text search with BM25 ranking
- Fast, works locally without API keys
- Multi-word queries use OR for discovery
- Boolean operators: AND, OR, NEAR

**2. Vector Search (Semantic)** - `search-semantic` command
- OpenAI embeddings for semantic understanding
- Finds conceptually similar content
- Requires `OPENAI_API_KEY` and Supabase
- Use `--vector-weight 1.0` for pure vector search

**3. Hybrid Search (Combined)** - `search-semantic` command
- Combines BM25 keywords + Vector similarity
- Default vector weight 0.7 (70% semantic, 30% keyword)
- Tunable balance between precision and discovery
- Best overall results

### Progressive Disclosure

**Navigation Commands:**
- `list <file>` - Show section hierarchy with IDs
- `get-section <id>` - Load single section by ID
- `next <id> <file>` - Navigate to next sibling
- `next <id> <file> --child` - Drill into first child subsection

**Token Efficiency:**
- 99% context savings: 21KB file → 204 bytes per section
- Search before loading to find relevant content
- Navigate incrementally through large files
- Load specific sections instead of entire files

## References

- **[EXAMPLES.md](./EXAMPLES.md)** - Usage scenarios (progressive disclosure, cross-file search, tree navigation)
- **[demo/progressive_disclosure.sh](./demo/progressive_disclosure.sh)** - 8-step end-to-end demo
- **[COMPONENT_HANDLERS.md](./COMPONENT_HANDLERS.md)** - Component handler guide
- **[HANDLER_INTEGRATION.md](./HANDLER_INTEGRATION.md)** - Integration guide
- **[README.md](./README.md)** - Complete documentation

---

*Last Updated: 2026-02-08 (Phase 02 Ready: 5 plans for BM25+Vector+Hybrid search, 518 tests passing)*

---

## Session Restart Workflow

On session restart, run `/remap-codebase` to:
1. Rename session with timestamp
2. Map codebase structure
3. Index repository
4. Update Claude context
5. Provide concise summary

**Last Updated**: 2026-02-08

---

## Quick Reference: Auto-Full-Auto Workflow

**Current Status:** Phase 02 plans complete, ready to execute

**Next Session Command:**
```bash
/clear
/gsd:execute-phase 02-search_fix
```

**Expected:** 518 → 548 tests passing, all 3 search modes working

**Workflow:** See `.planning/GSD_WORKFLOW.md` for full auto-full-auto loop

**Three Search Modes After Execution:**
1. BM25 (Keywords): `./skill_split.py search "query"`
2. Vector (Semantic): `./skill_split.py search-semantic "query" --vector-weight 1.0`
3. Hybrid (Combined): `./skill_split.py search-semantic "query" --vector-weight 0.7`
