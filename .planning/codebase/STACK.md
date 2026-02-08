# Technology Stack

**Analysis Date:** 2026-02-08

## Languages

**Primary:**
- Python 3.13.5 - All core logic, CLI, database operations, handlers

**Secondary:**
- SQL - SQLite and PostgreSQL (Supabase) database schemas
- Shell (bash) - Deployment scripts and demo workflows

## Runtime

**Environment:**
- Python 3.13.5

**Package Manager:**
- pip (standard Python package manager)
- Lockfile: `requirements.txt` (minimal - only 2 dependencies)

## Frameworks

**Core:**
- None - Pure Python with dataclasses and standard library

**Testing:**
- pytest 9.0.2 - Test runner and assertion library
- pytest-mock - Mocking support (implied by test patterns)

**Build/Dev:**
- python-dotenv - Environment variable management from `.env`

## Key Dependencies

**Critical:**
- supabase>=2.3.0 - Supabase client for remote database storage
- python-dotenv>=1.0.0 - Load environment variables from `.env` file

**Infrastructure:**
- sqlite3 (standard library) - Local database storage
- dataclasses (standard library) - Data models
- argparse (standard library) - CLI argument parsing
- pathlib (standard library) - Cross-platform path handling

**Optional (lazy-loaded):**
- openai - Vector embeddings for semantic search (only when `OPENAI_API_KEY` is set)

## Configuration

**Environment:**
- `.env` file loaded via `python-dotenv`
- Key configs: `SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY`, `ENABLE_EMBEDDINGS`, `SKILL_SPLIT_DB`

**Build:**
- No build step required - pure Python interpreter
- Entry point: `./skill_split.py` (executable with shebang)

## Platform Requirements

**Development:**
- Python 3.13+ (developed on 3.13.5)
- pytest for running tests
- SQLite support (included with Python)

**Production:**
- Any platform supporting Python 3.13+
- Optional: Supabase account for remote storage
- Optional: OpenAI API key for vector embeddings

---

*Stack analysis: 2026-02-08*
