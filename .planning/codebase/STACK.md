# Technology Stack

**Analysis Date:** 2026-02-08

## Languages

**Primary:**
- Python 3.11-3.13 - Core application logic, CLI, parsers, database operations
- Shell (Bash) - CLI commands, shell scripts for handlers
- JavaScript/TypeScript - Component handlers for script languages
- JSON - Configuration files, metadata

**Secondary:**
- SQL - SQLite database queries
- YAML - Frontmatter parsing, skill definitions
- Markdown - Skill documentation format

## Runtime

**Environment:**
- Python 3.11-3.13 (tested with multiple versions)
- Node.js v22.15.0 (for JavaScript/TypeScript handlers)

**Package Manager:**
- pip (Python) - Primary package management
- npm (Node.js) - For JavaScript/TypeScript dependencies

## Frameworks

**Core:**
- Custom Python framework - Modular design with handlers, parsers, and database operations
- Command-line interface built with argparse

**Testing:**
- pytest - Test framework with coverage support
- pytest-mock - Mocking utilities

**Build/Dev:**
- No external build tools - Pure Python with direct execution

## Key Dependencies

**Critical:**
- SQLite3 - Local database storage
- PyYAML - YAML frontmatter parsing
- markdown - Markdown processing
- supabase-py - Supabase cloud integration

**Infrastructure:**
- hashlib - SHA256 hashing for integrity verification
- requests - HTTP requests for external APIs
- openai - OpenAI embeddings for semantic search

## Configuration

**Environment:**
- Environment variables for API keys (SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)
- Configuration files in JSON format
- User home directory for production database (~/.claude/databases/)

**Build:**
- No build configuration required
- Direct script execution with Python

## Platform Requirements

**Development:**
- Python 3.11+ with pip
- pytest for testing
- SQLite3 (included with Python)

**Production:**
- Python 3.11+ runtime
- SQLite database file storage
- Optional: Supabase cloud instance
- Optional: OpenAI API for embeddings

---

*Stack analysis: 2026-02-08*