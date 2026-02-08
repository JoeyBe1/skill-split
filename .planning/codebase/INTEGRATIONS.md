# External Integrations

**Analysis Date:** 2026-02-08

## APIs & External Services

**Cloud Storage:**
- Supabase - Remote database storage
  - SDK/Client: supabase-py
  - Auth: SUPABASE_URL, SUPABASE_KEY environment variables
  - Used for: Remote skill library, production deployment

**AI/ML Services:**
- OpenAI Embeddings - Semantic search capabilities
  - SDK/Client: openai
  - API Key: OPENAI_API_KEY environment variable
  - Used for: Vector embeddings in hybrid search
  - Models: text-embedding-ada-002 (default)

## Data Storage

**Databases:**
- SQLite - Primary local storage
  - Connection: Direct SQLite3 connection
  - Client: Native Python sqlite3 module
  - Schema: FileMetadata, Section tables with CASCADE delete

**File Storage:**
- Local filesystem - Primary skill file storage
- Supabase Cloud - Remote synchronization option

**Caching:**
- No explicit caching - Direct database queries

## Authentication & Identity

**Auth Provider:**
- Custom token-based - For Supabase integration
  - Implementation: Bearer tokens via Supabase client
  - No user authentication - API key-based access

## Monitoring & Observability

**Error Tracking:**
- No external error tracking - Python exception handling
- Error logging to console with detailed stack traces

**Logs:**
- Console output only - No external logging service
- Verbose logging for debug operations

## CI/CD & Deployment

**Hosting:**
- Local development - Direct Python execution
- Production - SQLite database on filesystem
- Cloud option - Supabase remote storage

**CI Pipeline:**
- No CI/CD detected - Manual testing and deployment
- Git-based version control

## Environment Configuration

**Required env vars:**
- SUPABASE_URL - Supabase instance URL
- SUPABASE_KEY - Supabase service role key
- OPENAI_API_KEY - OpenAI API for embeddings
- DATABASE_PATH - SQLite database location (optional, defaults to ~/.claude/databases/)

**Secrets location:**
- Environment variables - Primary method
- No secrets committed to repository
- .env file for local development

## Webhooks & Callbacks

**Incoming:**
- None detected - No webhook endpoints

**Outgoing:**
- HTTP requests to Supabase - For data synchronization
- HTTP requests to OpenAI - For embedding generation

---

*Integration audit: 2026-02-08*