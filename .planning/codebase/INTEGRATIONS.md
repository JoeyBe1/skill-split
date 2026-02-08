# External Integrations

**Analysis Date:** 2026-02-08

## APIs & External Services

**Vector Embeddings:**
- OpenAI API - Text embeddings for semantic search
  - SDK/Client: `openai` Python package (lazy-imported)
  - Model: text-embedding-3-small (1536 dimensions)
  - Auth: `OPENAI_API_KEY` env var
  - Usage: `core/embedding_service.py`
  - Pricing: $0.02 per 1M tokens (as of Feb 2025)
  - Optional: Only used when `OPENAI_API_KEY` is set

## Data Storage

**Databases:**
- SQLite (local)
  - Connection: File-based (`skill_split.db` or path from `SKILL_SPLIT_DB`)
  - Client: `sqlite3` (Python standard library)
  - Implementation: `core/database.py`
  - Schema: Auto-created on init with CASCADE deletes

- Supabase (PostgreSQL with pgvector)
  - Connection: HTTPS REST API
  - Client: `supabase` Python package (>=2.3.0)
  - Auth: `SUPABASE_URL` + `SUPABASE_KEY` env vars
  - Implementation: `core/supabase_store.py`
  - Features: Remote storage, full-text search, vector similarity with pgvector

**File Storage:**
- Local filesystem only - No external object storage

**Caching:**
- In-memory embedding cache in `EmbeddingService` class
- No external cache (Redis, etc.)

## Authentication & Identity

**Auth Provider:**
- Custom - No external identity provider
  - Implementation: Simple username string for checkout tracking
  - Location: `core/checkout_manager.py`
  - Storage: `checkouts` table in database

## Monitoring & Observability

**Error Tracking:**
- None - Standard Python exception handling

**Logs:**
- stderr for errors (`print(..., file=sys.stderr)`)
- stdout for normal output
- No structured logging framework

## CI/CD & Deployment

**Hosting:**
- Not applicable - CLI tool runs locally

**CI Pipeline:**
- None detected - Manual testing with pytest

## Environment Configuration

**Required env vars:**
- `SUPABASE_URL` - Supabase project URL (for Supabase features)
- `SUPABASE_KEY` or `SUPABASE_PUBLISHABLE_KEY` - Supabase API key

**Optional env vars:**
- `OPENAI_API_KEY` - OpenAI API key for embeddings
- `ENABLE_EMBEDDINGS` - Set to 'true' to auto-generate embeddings on store
- `SKILL_SPLIT_DB` - Path to SQLite database (defaults to `./skill_split.db`)

**Secrets location:**
- `.env` file in project root (not committed)
- `.env.example` shows required variables

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None - All operations are synchronous

## Database Migrations

**Supabase Schema Migrations:**
- Location: `migrations/*.sql`
- Key migrations:
  - `enable_pgvector.sql` - Enable vector extension
  - `create_embeddings_table.sql` - Embeddings storage with ivfflat index
  - `add_config_script_types.sql` - Add config and script file types
  - `optimize_vector_search.sql` - Vector search optimization
  - `unify_supabase_schema.sql` - Schema unification

**Migration Guide:**
- `migrations/SCHEMA_MIGRATION_GUIDE.md` - Step-by-step migration instructions

---

*Integration audit: 2026-02-08*
