# Codebase Concerns

**Analysis Date:** 2026-02-08

## Tech Debt

### Placeholder Implementation
**Hybrid Search Scoring**:
- Issue: `_merge_rankings()` in `core/hybrid_search.py:282` uses simplified position-based scoring for text search results (score = 1.0 - position/limit)
- Files: `core/hybrid_search.py:179-196`
- Impact: Text search relevance is poor compared to proper full-text search. Current implementation only considers position, not term frequency or actual relevance.
- Fix approach: Implement proper full-text search scoring using SQLite FTS5 or Supabase's text search capabilities with rank normalization

### Skill Composer Metadata Generation
**Auto-Frontmatter Generation**:
- Issue: `_generate_frontmatter()` in `core/skill_composer.py:262` has placeholder implementation comments
- Files: `core/skill_composer.py:343`
- Impact: Composed skills may have suboptimal auto-generated metadata; manual editing often required
- Fix approach: Use `frontmatter_generator.py` modules consistently, or enhance with AI-powered metadata inference

## Known Bugs

### XML Closing Tag Indentation (Historical)
**XML round-trip indentation not fully preserved**:
- Symptoms: Historical bug documented in test reports; may be partially addressed
- Files: `core/parser.py:285-410`, `core/recomposer.py:147-166`
- Trigger: XML tag sections with specific indentation patterns
- Workaround: Considered mostly resolved with `closing_tag_prefix` field (added in migration)
- Status: Schema migration added `closing_tag_prefix` field; implementation in parser extracts whitespace correctly

### Shell Handler Test Failures (Historical)
**Missing content between functions in shell handler**:
- Symptoms: Historical test failures documented in `SHELL_HANDLER_TEST_RESULTS.txt`
- Files: `handlers/shell_handler.py`
- Trigger: Shell scripts with consecutive functions or specific formatting
- Workaround: Status unclear; tests may need updating to reflect current implementation
- Status: Historical report; current test status unknown (499 tests passing according to CLAUDE.md)

## Security Considerations

### API Key Handling
**OpenAI API Key in Environment Variables**:
- Risk: API keys stored in environment variables can be leaked through process info, logs, or debugger
- Files: `core/embedding_service.py:52`, `core/supabase_store.py:485`
- Current mitigation: Keys read from `OPENAI_API_KEY` env var; no hardcoded values found
- Recommendations:
  - Use secret management service (e.g., HashiCorp Vault, AWS Secrets Manager)
  - Implement key rotation mechanism
  - Add logging to track key usage
  - Consider using short-lived tokens instead of long-lived keys

### Supabase Credentials
**Database URL and Key in Environment**:
- Risk: Supabase URL and anon/service_role keys exposed if environment compromised
- Files: `skill_split.py:54` (global import), `core/supabase_store.py:15-21`
- Current mitigation: Credentials read from `SUPABASE_URL` and `SUPABASE_KEY` env vars
- Recommendations:
  - Use Row Level Security (RLS) policies consistently
  - Implement service account key rotation
  - Audit all Supabase client usage for appropriate permission levels

### Bare Exception Handling
**Silent exception swallowing in validation**:
- Risk: `except:` clause without exception type in `core/skill_validator.py:277` could mask errors
- Files: `core/skill_validator.py:277`
- Current mitigation: Limited to description validation non-critical path
- Recommendations:
  - Change to `except Exception:` with logging
  - Consider if this validation should fail loudly instead

### Global Statement Import Pattern
**Runtime imports using global**:
- Risk: Dynamic module imports using `global` statement in `skill_split.py:54`
- Files: `skill_split.py:54`
- Current mitigation: Limited to conditional Supabase imports
- Recommendations:
  - Refactor to explicit import/try-except pattern
  - Document why lazy loading is necessary

## Performance Bottlenecks

### Embedding Generation
**No Batching for Multiple Embeddings**:
- Problem: `generate_embedding()` in `core/embedding_service.py:59` processes one section at a time
- Files: `core/embedding_service.py:59-98`
- Cause: OpenAI API supports batch embeddings, but current implementation calls API individually
- Improvement path: Implement batch embedding generation to reduce API calls by 10-100x for large files

### Vector Search RPC Dependency
**Supabase RPC Function Required**:
- Problem: Vector search requires custom `match_sections` RPC function in Supabase
- Files: `core/hybrid_search.py:136-146`, `core/supabase_store.py:138-146`
- Cause: No fallback to client-side vector search when RPC unavailable
- Improvement path: Implement client-side vector similarity using numpy/scipy as fallback

### Large File Processing
**No Streaming for Large Files**:
- Problem: Entire file content loaded into memory during parsing
- Files: `core/parser.py:96-140`, `core/recomposer.py:34-97`
- Cause: Line-by-line processing exists but entire document kept in memory
- Improvement path: Implement streaming parser for files >10MB

### Database Connection Pooling
**No Connection Pooling for Supabase**:
- Problem: Each operation creates new Supabase client connection
- Files: `core/supabase_store.py:15-21`
- Cause: Single client instantiated in `__init__` but no pooling configuration
- Improvement path: Configure connection pooling for concurrent operations

## Fragile Areas

### Multi-File Component Deployment
**Checkout Manager File Writing**:
- Files: `core/checkout_manager.py:24-63`, `core/checkout_manager.py:112-175`
- Why fragile: Multi-file components (plugins, hooks) require coordinated file writes; failure mid-deployment leaves inconsistent state
- Safe modification: Always write to temp location first, then atomic rename
- Test coverage: Tests exist but may not cover all failure scenarios (disk full, permission errors)

### Parser Code Block Detection
**Code Fence Detection Logic**:
- Files: `core/parser.py:98-114`, `core/parser.py:180-189`
- Why fragile: Code block detection relies on simple string matching; can be confused by fenced code blocks in examples or edge cases
- Safe modification: Add comprehensive test cases for nested/malformed code fences
- Test coverage: Basic coverage exists; edge cases around ```` ``` ``` with language specifiers need validation

### Handler Factory Type Detection
**File Type Detection Heuristics**:
- Files: `handlers/component_detector.py:28-75`, `handlers/factory.py:38-68`
- Why fragile: Detection based on filename patterns and content inspection; new file types require changes
- Safe modification: Add new detection rules to ComponentDetector; maintain backward compatibility
- Test coverage: Handler tests exist but may not cover all filename variations

### Recursive Section Building
**Section Tree Construction**:
- Files: `core/database.py:355-395`, `core/supabase_store.py:180-222`
- Why fragile: Relies on parent_id references; orphaned sections or circular references could cause infinite loops
- Safe modification: Add depth limits and cycle detection
- Test coverage: Standard cases tested; malformed data cases not tested

## Scaling Limits

### SQLite Database Size
**Current capacity**: Unknown limit, but SQLite has theoretical 281TB limit
**Limit**: Practical limit around 100GB before performance degrades significantly
**Scaling path**: Migrate to PostgreSQL/Supabase for production use (already implemented)

### Concurrent Embedding Generation
**Current capacity**: Single-threaded embedding generation
**Limit**: OpenAI rate limits (RPM/TPM) will throttle large batch operations
**Scaling path**: Implement async/await or multiprocessing for parallel embedding generation

### Supabase Vector Search Performance
**Current capacity**: Dependent on Supabase instance size and pgvector index quality
**Limit**: 10K-100K embeddings before performance degrades without proper indexing
**Scaling path**: Ensure HNSW indexes are created and optimized (see `migrations/optimize_vector_search.sql`)

### File Ingestion Rate
**Current capacity**: Unknown, likely limited by parsing overhead
**Limit**: Network and database write throughput for Supabase ingestions
**Scaling path**: Batch ingestion scripts exist (`batch_ingest_supabase.py`, `bulk_ingest_supabase.py`) but could use parallelization

## Dependencies at Risk

### Supabase Python Client
**Package**: `supabase>=2.3.0`
**Risk**: Version pinning uses `>=` which allows breaking changes
**Impact**: API changes could break database operations
**Migration plan**: Pin to specific version (e.g., `==2.3.0`) and test upgrades explicitly

### python-dotenv
**Package**: `python-dotenv>=1.0.0`
**Risk**: Minor risk; mature library with stable API
**Impact**: Low; only used for environment variable loading
**Migration plan**: No action needed currently

### OpenAI API Dependency
**Service**: OpenAI Embeddings API
**Risk**: Service disruption, rate limits, pricing changes
**Impact**: Vector search and hybrid search will fail or degrade
**Migration plan**: Support alternative embedding providers (Cohere, HuggingFace, local models)

### Optional Dependencies Not Specified
**Issue**: Embedding service and other features have optional dependencies not in `requirements.txt`
**Files**: `core/embedding_service.py:5-8` (try/except import for openai)
**Impact**: Features fail silently without clear error messages
**Migration plan**: Create `requirements-dev.txt` or document optional dependencies

## Missing Critical Features

### Transaction Safety
**Feature gap**: No transaction support for multi-file operations
**Problem**: Checkout/checkin operations not wrapped in database transactions
**Blocks**: Reliable deployment of multi-file components
**Files**: `core/checkout_manager.py:24-63`
**Impact**: Failed deployments can leave system in inconsistent state

### Backup/Restore
**Feature gap**: No automated backup or restore functionality
**Problem**: No way to recover from accidental data loss or corruption
**Blocks**: Production deployment confidence
**Impact**: Data loss risk; manual recovery only

### Access Control
**Feature gap**: No user authentication or authorization
**Problem**: Any user with Supabase credentials can read/write all data
**Blocks**: Multi-user deployment scenarios
**Impact**: Cannot safely share Supabase instance between users

### Audit Logging
**Feature gap**: No audit trail for file operations
**Problem**: Cannot track who checked out what file when
**Blocks**: Compliance and debugging requirements
**Impact**: Limited visibility into system usage

## Test Coverage Gaps

### Error Path Coverage
**What's not tested**: Malformed data, network failures, disk errors
**Files**: `core/checkout_manager.py`, `core/supabase_store.py`
**Risk**: Production failures may not be caught by tests
**Priority**: High

### Edge Cases in Parsing
**What's not tested**: Empty files, files with only frontmatter, circular XML tags
**Files**: `core/parser.py`, `handlers/script_handler.py`
**Risk**: Parser crashes or produces incorrect output for unusual inputs
**Priority**: Medium

### Handler Integration
**What's not tested**: All handler types working together in complex workflows
**Files**: `handlers/*.py`, `core/checkout_manager.py`
**Risk**: Inter-handler compatibility issues not discovered until production
**Priority**: Medium

### Vector Search Accuracy
**What's not tested**: Actual relevance of vector search results, embedding quality
**Files**: `core/hybrid_search.py`, `core/embedding_service.py`, `test/test_hybrid_search.py`
**Risk**: Poor search performance not detected by unit tests
**Priority**: Low (requires manual evaluation or golden dataset)

### Concurrent Operations
**What's not tested**: Multiple users checking out files simultaneously
**Files**: `core/checkout_manager.py`, `core/supabase_store.py`
**Risk**: Race conditions in multi-user scenarios
**Priority**: Medium

---

*Concerns audit: 2026-02-08*
