# Project Index: skill-split

**Generated**: 2026-02-08
**Purpose**: Token-efficient codebase navigation (94% reduction vs full file read)

---

## 📁 Project Structure

```
skill-split/
├── core/                    # Core parsing, storage, query modules
│   ├── parser.py            # Markdown/XML parsing with frontmatter
│   ├── database.py          # SQLite storage with CASCADE delete
│   ├── supabase_store.py    # Supabase client with vector search
│   ├── query.py             # Progressive disclosure API
│   ├── hybrid_search.py     # Vector + text search
│   ├── embedding_service.py # OpenAI embeddings with caching
│   ├── skill_composer.py    # Assemble skills from sections
│   ├── checkout_manager.py  # File deployment & checkout/checkin
│   └── [other modules...]
├── handlers/                # File-type specific handlers
│   ├── base.py              # Abstract BaseHandler
│   ├── factory.py           # HandlerFactory for type dispatch
│   ├── plugin_handler.py    # Plugin component parsing
│   ├── hook_handler.py      # Hook component parsing
│   ├── config_handler.py    # Settings/MCP config parsing
│   ├── python_handler.py    # Python file parsing
│   ├── javascript_handler.py # JS/JSX parsing
│   ├── typescript_handler.py # TS/TSX parsing
│   └── shell_handler.py     # Shell script parsing
├── test/                    # 499 tests, comprehensive coverage
│   ├── test_parser.py
│   ├── test_database.py
│   ├── test_handlers/
│   └── fixtures/
├── migrations/              # Database schema migrations
│   ├── enable_pgvector.sql
│   ├── create_embeddings_table.sql
│   └── optimize_vector_search.sql
├── scripts/                 # Utilities (embedding generation, monitoring)
├── demo/                    # Example usage scripts
└── skill_split.py           # Main CLI entry point (16 commands)
```

---

## 🚀 Entry Points

**CLI**: `skill_split.py` - Main CLI with 16 commands
- Commands: parse, validate, store, verify, get-section, search, search-semantic, compose, checkout, checkin, list-library, status, ingest, batch-ingest
- Usage: `./skill_split.py <command> [args]`

**API**: `core/query.py` - QueryAPI for progressive disclosure
- Methods: `get_section()`, `get_next_section()`, `search_sections()`, `get_section_tree()`
- Usage: Import for programmatic access

**Tests**: `pytest test/` - 499 tests passing
- Framework: pytest 9.0.2
- Coverage: All core modules, handlers, integration tests

---

## 📦 Core Modules

### Module: Parser (`core/parser.py`)
- **Purpose**: Parse markdown/XML with frontmatter, headings, tags
- **Key Classes**: `Parser`, `FormatDetector`
- **Exports**: `parse_headings()`, `parse_xml_tags()`, `detect_format()`

### Module: Database (`core/database.py`)
- **Purpose**: SQLite storage with CASCADE delete, hierarchical queries
- **Key Classes**: `DatabaseStore`
- **Exports**: `store_file()`, `get_file()`, `get_section()`, `search_sections()`

### Module: Supabase Store (`core/supabase_store.py`)
- **Purpose**: Supabase client with vector search, checkout tracking
- **Key Classes**: `SupabaseStore`
- **Exports**: Remote storage, vector similarity search, checkout status

### Module: Query API (`core/query.py`)
- **Purpose**: Progressive disclosure interface
- **Key Classes**: `QueryAPI`
- **Exports**: Section-by-section retrieval, navigation, search

### Module: Hybrid Search (`core/hybrid_search.py`)
- **Purpose**: Vector + text search with adjustable weighting
- **Key Classes**: `HybridSearch`
- **Exports**: `hybrid_search()`, `vector_search()`, `text_search()`

### Module: Embedding Service (`core/embedding_service.py`)
- **Purpose**: OpenAI embeddings with caching and batch generation
- **Key Classes**: `EmbeddingService`
- **Exports**: `generate_embedding()`, batch embeddings

### Module: Skill Composer (`core/skill_composer.py`)
- **Purpose**: Assemble new skills from existing sections
- **Key Classes**: `SkillComposer`
- **Exports**: `compose_from_sections()`, rebuild hierarchy

### Module: Checkout Manager (`core/checkout_manager.py`)
- **Purpose**: File deployment with multi-file support
- **Key Classes**: `CheckoutManager`
- **Exports**: `checkout_file()`, `checkin_file()`, multi-file deployment

---

## 🔧 Configuration

**Environment**: `.env` or environment variables
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon/service_role key
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `SKILL_SPLIT_DB`: Path to SQLite database (default: `skill_split.db`)

**Dependencies**: `requirements.txt`
- `supabase>=2.3.0`: Supabase Python client
- `python-dotenv>=1.0.0`: Environment variable loading

**Testing**: `pytest` + plugins
- `pytest-asyncio`: Async test support
- `pytest-benchmark`: Performance testing
- `pytest-mock`: Mocking utilities
- `pytest-cov`: Coverage reporting
- `pyfakefs`: Filesystem mocking
- `respx`: HTTP mocking

---

## 📚 Documentation

**Quick Start**:
- `README.md` - Project overview and installation
- `CLAUDE.md` - Project context for Claude Code agents
- `EXAMPLES.md` - Usage scenarios (progressive disclosure, search)
- `VECTOR_SEARCH_GUIDE.md` - Vector search implementation guide

**Architecture**:
- `COMPONENT_HANDLERS.md` - Handler system documentation
- `HANDLER_INTEGRATION.md` - Integration guide
- `COMPONENT_COMPOSITION.md` - Skill composition reference

**Planning**:
- `.planning/codebase/` - Codebase analysis (7 documents, 1,433 lines)
- `docs/plans/` - Phase plans and summaries

---

## 🧪 Test Coverage

**Test Count**: 499 tests passing (as of 2026-02-08)

**Unit Tests**:
- `test/test_parser.py` - Parser tests for markdown, XML, mixed formats
- `test/test_database.py` - DatabaseStore CRUD and cascade tests
- `test/test_handlers/` - Handler-specific tests with fixtures
- `test/test_skill_composer.py` - Composition logic tests
- `test/test_hybrid_search.py` - Vector search tests
- `test/test_embedding_service.py` - Embedding generation tests

**Integration Tests**:
- `test/test_supabase_store.py` - Supabase integration
- `test/test_composer_integration.py` - End-to-end composition
- `test/test_vector_search_integration.py` - Vector search integration

**Round-trip Tests**:
- `test/test_roundtrip.py` - Byte-perfect round-trip verification
- `demo/test_roundtrip_examples.sh` - Real-world round-trip testing

---

## 🔗 Key Dependencies

**Runtime**:
- `supabase>=2.3.0` - Supabase client (PostgreSQL, storage, auth)
- `python-dotenv>=1.0.0` - Environment configuration

**Development**:
- `pytest>=9.0.2` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-benchmark` - Performance testing
- `pytest-mock` - Mocking
- `pytest-cov` - Coverage
- `pyfakefs` - Filesystem mocking
- `respx` - HTTP mocking

**Optional** (for vector search):
- `openai>=1.0.0` - OpenAI API for embeddings

---

## 📝 Quick Start

**1. Parse and store a file:**
```bash
./skill_split.py parse skill.md
./skill_split.py store skill.md
```

**2. Retrieve specific section:**
```bash
./skill_split.py get-section <section_id> --db skill_split.db
```

**3. Search sections:**
```bash
./skill_split.py search "authentication" --db skill_split.db
```

**4. Compose new skill:**
```bash
./skill_split.py compose --sections 1,2,3 --output new_skill.md
```

**5. Deploy from library:**
```bash
./skill_split.py checkout <file_id> --target ~/.claude/skills/new/SKILL.md
```

**6. Run tests:**
```bash
python -m pytest test/ -v
```

---

## 🎯 Production Status

**Phase 1-11 Complete** (2026-02-06)
- ✅ 499/499 tests passing
- ✅ Single-file checkout (skills, commands, scripts)
- ✅ Multi-file checkout (plugins, hooks with related files)
- ✅ Vector search (semantic + hybrid ranking)
- ✅ Skill composition (absolute line number tracking)

**Deployment Ready**:
- Local: `~/.claude/databases/skill-split.db` (1,365 files, 19,207 sections)
- Remote: Supabase cloud storage fully functional

---

## 🔍 Token Efficiency

**Index Size**: ~3KB (this file)
**Full Codebase Read**: ~58,000 tokens
**Savings**: 94% token reduction per session

**Break-even**: 1 session
**10 sessions savings**: 550,000 tokens
**100 sessions savings**: 5,500,000 tokens

---

*Generated by /sc:index-repo skill-split 2026-02-08*
