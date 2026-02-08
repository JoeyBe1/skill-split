# skill-split

## What This Is

A production-ready Python tool for intelligent file splitting and progressive disclosure. Parses YAML/Markdown files into sections stored in SQLite/Supabase for token-efficient LLM interactions. Currently deployed with 1,365 files (19,207 sections) achieving 99% context savings.

## Core Value

**Token-efficient progressive disclosure without data loss.** Every section can be retrieved, recomposed, and deployed byte-perfectly.

## Requirements

### Validated

- ✓ **Parsing** - Markdown headings, YAML frontmatter, XML tags with byte-perfect round-trip
- ✓ **Storage** - Dual backend (SQLite local + Supabase cloud) with CASCADE delete
- ✓ **Handlers** - Plugin, hook, config, and script file parsing (Python, JS, TS, Shell)
- ✓ **Query API** - Progressive disclosure (get_section, get_next_section, search_sections)
- ✓ **Composition** - Assemble new skills from existing sections with metadata
- ✓ **Deployment** - Checkout/checkin with multi-file support for components
- ✓ **Vector Search** - Hybrid semantic + keyword search with OpenAI embeddings
- ✓ **Testing** - 470 tests passing with comprehensive coverage

### Active

- [ ] **GS-01**: Fix hybrid search text scoring (replace placeholder position-based scoring)
- [ ] **GS-02**: Implement batch embedding generation (10-100x speedup for large files)
- [ ] **GS-03**: Add transaction safety for multi-file checkout operations
- [ ] **GS-04**: Implement backup/restore functionality
- [ ] **GS-05**: Improve API key security (secret management or short-lived tokens)

### Out of Scope

- New file type handlers (current 8 handlers cover all use cases)
- Alternative embedding providers (OpenAI is sufficient for current needs)
- Multi-user access control (single-user deployment model)
- Real-time streaming (current batch processing is adequate)

## Context

**Technical Environment:**
- Python 3.8+, Click CLI, pytest 9.0.2
- SQLite for local storage, Supabase for cloud
- OpenAI text-embedding-3-small for vector search
- pgvector extension for similarity search

**Production Status:**
- Local: `~/.claude/databases/skill-split.db` (1,365 files, 19,207 sections)
- Remote: Supabase cloud with vector search enabled
- Deployment: Single-file and multi-file checkout fully functional

**Known Issues from Codebase Analysis:**
- Hybrid search uses simplified scoring (position-based, not term frequency)
- Embeddings generated individually (no batching despite OpenAI support)
- Multi-file operations lack transaction wrapping
- No automated backup/restore mechanisms
- API keys stored in environment variables (recommended: secret manager)

## Constraints

- **Compatibility**: Must maintain byte-perfect round-trip for all existing deployments
- **Performance**: Vector search queries must complete in <100ms for 20K sections
- **Cost**: OpenAI embeddings cost ~$0.04 initial + ~$0.01/month for current scale
- **Backward Compatibility**: All existing 470 tests must continue passing

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Dual storage backend (SQLite + Supabase) | Local for speed, cloud for sharing | ✓ Good |
| Handler pattern for extensibility | Easy to add new file types | ✓ Good |
| SHA256 hash verification | Ensures data integrity | ✓ Good |
| pgvector for vector search | Efficient similarity search | ✓ Good |
| OpenAI embeddings | Best quality, simple API | — Pending (alternative providers) |

---
*Last updated: 2026-02-08 after codebase mapping*
