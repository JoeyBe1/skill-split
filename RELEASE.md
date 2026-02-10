# skill-split v1.0.0 Release

**Released:** 2026-02-10

We are excited to announce the first production release of skill-split, a Python tool for intelligently splitting YAML and Markdown files into sections and storing them in SQLite for progressive disclosure.

## What is skill-split?

skill-split solves a critical problem: **large files consume tokens inefficiently**. Instead of loading entire files into context, skill-split breaks them into discrete sections and stores them in a lightweight SQLite database.

### Key Benefits

- **99% Context Savings:** Load just the section you need (204 bytes) instead of the entire file (21KB)
- **Byte-Perfect Integrity:** SHA256 hashing ensures zero data loss
- **Three Search Modes:** BM25 keywords, Vector semantic, and Hybrid search
- **Component Support:** Plugins, hooks, configs, and scripts
- **Production Ready:** 623 tests passing, real-world verified

## Key Features

### Core Capabilities

- **Intelligent Parsing:** Detects and preserves YAML frontmatter, Markdown headings (h1-h6), and XML-style tags
- **Progressive Disclosure:** Load sections incrementally instead of entire files
- **Full-Text Search:** FTS5 with BM25 relevance ranking for fast local search
- **Semantic Search:** OpenAI embeddings for concept-based discovery
- **Hybrid Search:** Combines keyword and vector search with tunable weights
- **Section Storage:** SQLite database tracks sections with metadata
- **Tree Navigation:** Understand full section hierarchy before diving into details
- **Byte-Perfect Round-Trip:** Recompose files exactly as they were

### Component Handler Support

- **Plugins:** Parse `plugin.json` with MCP config and hooks
- **Hooks:** Parse `hooks.json` with shell scripts
- **Configs:** Parse `settings.json` and `mcp_config.json`
- **Scripts:** Python, JavaScript, TypeScript, and Shell files
- **Multi-File Handling:** Track and hash related files together

### Search Capabilities

**1. BM25 Search (Keywords)**
```bash
./skill_split.py search "python handler"
```
- Fast, works locally without API keys
- Relevance scores based on term frequency
- Boolean operators: AND, OR, NEAR

**2. Vector Search (Semantic)**
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 1.0
```
- OpenAI embeddings for semantic understanding
- Finds conceptually similar content
- Requires `OPENAI_API_KEY` and Supabase

**3. Hybrid Search (Combined)**
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "query" --vector-weight 0.7
```
- Combines BM25 keywords + Vector similarity
- Default vector weight 0.7 (70% semantic, 30% keyword)
- Best overall results

## Real-World Validation

### Production Testing Complete

- **1,365 skill files** ingested (19,207 sections)
- **3 database systems** verified (local demo, production SQLite, Supabase cloud)
- **99% context savings** confirmed (21KB → 204 bytes per section)
- **Byte-perfect round-trip** on complex 92-section files
- **Schema migration** tested and documented

### Deployment Capabilities

- **Single-file checkout:** Production ready (skills, commands, scripts)
- **Multi-file checkout:** Deploys plugins with .mcp.json, hooks with scripts
- **All components runtime-ready:** Skills, commands, scripts, plugins, hooks
- **Composition:** Can create new skills from library sections

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

## Quick Start

### Parse and Store

```bash
# Parse a markdown file
./skill_split.py parse SKILL.md

# Store in database
./skill_split.py store SKILL.md
```

### Search and Retrieve

```bash
# Search for content
./skill_split.py search "python handler"

# Get specific section
./skill_split.py get-section 42
```

### Progressive Disclosure

```bash
# List file structure
./skill_split.py list SKILL.md

# Navigate to next section
./skill_split.py next 42 SKILL.md

# Drill into subsections
./skill_split.py next 42 SKILL.md --child
```

## Documentation

- **[README.md](README.md)** - Complete documentation
- **[EXAMPLES.md](EXAMPLES.md)** - Usage scenarios and workflows
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[INSTALLATION.md](INSTALLATION.md)** - Installation guide
- **[API.md](API.md)** - Programmatic API documentation
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## Project Statistics

- **Total Tests:** 623 passing
- **Test Coverage:** Parser, Database, Search, CLI, Handlers, Composition, Integration
- **Documentation:** 17 phases complete
- **Code Quality:** Byte-perfect round-trip verification

## Development Phases

**Phase 1-4:** Core Parser & Database
- Parser: YAML frontmatter, markdown headings, XML tags
- Database: SQLite storage with CASCADE delete
- Recomposer: Byte-perfect round-trip, SHA256 hashing
- Format Detection: XML tags with level=-1 support

**Phase 5:** Query API
- Progressive disclosure (get_section, get_next_section, get_section_tree, search_sections)

**Phase 6:** Complete CLI
- 16 commands fully functional

**Phase 7:** Supabase Integration
- Remote storage with full-text search

**Phase 8:** Checkout/Checkin
- File deployment and tracking

**Phase 9:** Component Handlers
- Plugins, hooks, configs with multi-file support

**Phase 10:** Script Handlers
- Python, JavaScript, TypeScript, Shell parsing

**Phase 11:** Skill Composition
- Assemble new skills from existing sections

**Phase 12-14:** Documentation Gap Closure
- Comprehensive documentation for all features

## License

MIT

## Support

Report issues, suggest features, or submit PRs on GitHub.

---

**Thank you to all contributors and users who helped test and refine skill-split!**
