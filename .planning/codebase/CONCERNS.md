# Codebase Concerns

**Analysis Date:** 2026-02-08

## Tech Debt

### 1. Exception Handling
- **Broad Exception Catching**: Multiple modules use bare `except Exception:` statements
  - `core/database.py:294`: FTS5 optimization fails silently
  - `core/hybrid_search.py:158,207,291`: Vector search failures caught generically
  - **Impact**: May hide important errors and make debugging difficult
  - **Fix approach**: Replace specific exceptions and implement proper error logging

### 2. Error Message Quality
- **Generic Warnings**: Handler warnings lack context about severity
  - `handlers/hook_handler.py:124`: "Script not found for hook"
  - `handlers/config_handler.py:136`: "Unknown settings key"
  - **Impact**: Hard to distinguish between critical issues and minor warnings
  - **Fix approach**: Add severity levels and suggest fixes in warnings

### 3. Large Files
- **`skill_split.py`** (1,264 lines): Main CLI handles multiple responsibilities
  - Contains database, Supabase, search, and validation logic
  - **Impact**: Hard to maintain and test
  - **Fix approach**: Extract into focused modules (search_ops, validation_ops)

- **`test/test_handlers/test_script_handlers.py`** (1,108 lines): Overly complex test suite
  - Tests multiple handlers in single file
  - **Impact**: Difficult to debug specific handler failures
  - **Fix approach**: Split into handler-specific test files

## Known Bugs

### 1. XML Tag Preservation
- **Issue**: XML closing tag indentation not preserved during round-trip
- **Files**: `core/recomposer.py`
- **Symptoms**: Files differ by 2 spaces in closing tags
- **Workaround**: Use `--verbose` flag to debug specific mismatches
- **Trigger**: Files with XML tags that have nested indentation

### 2. Parser API Evolution
- **Issue**: `Parser.parse()` method signature changed but not all callers updated
- **Files**: Multiple ingestion scripts
- **Symptoms**: `Parser.parse() missing 2 required positional arguments`
- **Trigger**: Running ingestion on older database schema
- **Fix**: Update all parser calls to include `file_type` and `file_format` params

### 3. Search Command Edge Cases
- **Issue**: `search-semantic` command fails on certain unpacking
- **Files**: `skill_split.py` line 951
- **Symptoms**: Command crashes with unpacking error
- **Priority**: HIGH (blocks new search features)
- **Fix**: Add proper null checks in search result handling

## Security Considerations

### 1. Credential Management
- **Risk**: Supabase credentials stored in environment variables
- **Files**: `skill_split.py:74-84`, `upload_to_supabase.py:76-92`
- **Current mitigation**: Using `os.getenv()` for credential retrieval
- **Recommendations**:
  - Add credential validation to prevent empty keys
  - Consider secure storage for production deployments
  - Add audit logging for credential usage

### 2. SQL Injection Protection
- **Status**: GOOD - Uses parameterized queries throughout
- **Files**: All database modules use `?` placeholders with tuple params
- **Example**: `core/database.py:266-268`
- **No concerns found**: All database operations are properly parameterized

### 3. Command Injection
- **Status**: GOOD - No direct system command execution
- **Files**: No `os.system()`, `subprocess()`, or `eval()` usage found
- **Exception**: SQLite operations use safe parameterized queries

## Performance Bottlenecks

### 1. Database Operations
- **Issue**: Multiple individual queries instead of batch operations
- **Files**: `core/database.py`, `core/hybrid_search.py`
- **Problem**: Section-by-section FTS5 sync during ingestion
- **Improvement path**: Implement bulk insert for FTS5 updates
- **Current**: ~19k sections processed individually
- **Target**: Batch processing for 10x+ speedup

### 2. Embedding Generation
- **Issue**: Synchronous OpenAI API calls block ingestion
- **Files**: `core/embedding_service.py:201-219`
- **Problem**: Failed embeddings fail entire file ingestion
- **Improvement path**: Async embeddings with retry mechanism
- **Current**: One failure = entire file rejected
- **Target**: Graceful fallback for individual section failures

### 3. Large Result Sets
- **Issue**: Hybrid search loads all results before ranking
- **Files**: `core/hybrid_search.py`
- **Problem**: Memory usage grows with result set size
- **Improvement path**: Stream results and use generators
- **Current**: All results loaded into memory
- **Target**: Lazy evaluation for large datasets

## Fragile Areas

### 1. Format Detection
- **Files**: `core/detector.py`
- **Why fragile**: Relies on file extensions and content patterns
- **Safe modification**: Always test with mixed-format files
- **Test coverage**: Gaps in edge cases (empty files, unusual extensions)
- **Risk**: False positives can misclassify entire files

### 2. Component Handler Factory
- **Files**: `handlers/factory.py`
- **Why fragile**: Handler registration relies on string matching
- **Safe modification**: Add new handlers to registry mapping
- **Risk**: Missing handler causes FileNotFoundError
- **Test coverage**: Good, but misses error propagation paths

### 3. Schema Migrations
- **Files**: `migrations/` directory
- **Why fragile**: Manual SQL execution with no rollback
- **Safe modification**: Always backup before applying migrations
- **Risk**: Irreversible changes to production data
- **Current**: Only one migration documented

## Scaling Limits

### 1. Database Size
- **Current**: 1,365 files, 19,207 sections
- **Limit**: SQLite file size max 281TB (theoretical)
- **Practical limit**: Query performance degrades after ~100k sections
- **Scaling path**:
  - Implement connection pooling
  - Add query result caching
  - Consider PostgreSQL for production scale

### 2. Memory Usage
- **Current**: All sections loaded into memory during search
- **Limit**: Python process memory (~2GB typical)
- **Practical limit**: ~50k sections before significant slowdown
- **Scaling path**:
  - Implement pagination for large result sets
  - Use streaming for file recomposition
  - Add memory usage monitoring

### 3. API Rate Limits
- **Current**: OpenAI embeddings called synchronously
- **Limit**: API rate limits (varies by tier)
- **Practical limit**: ~100 requests/minute
- **Scaling path**:
  - Implement request queuing
  - Add exponential backoff for retries
  - Consider local embedding cache

## Dependencies at Risk

### 1. SQLite Version Dependencies
- **Package**: Built-in SQLite
- **Risk**: FTS5 features require SQLite 3.9.0+
- **Impact**: Search functionality may break on older systems
- **Migration plan**: Add version check at startup
- **Alternative**: Consider PostgreSQL for production deployments

### 2. OpenAI Python Client
- **Package**: `openai`
- **Risk**: API changes could break embedding generation
- **Impact**: Vector search functionality fails
- **Migration plan**: Abstract embedding service interface
- **Alternative**: Support multiple embedding providers

## Missing Critical Features

### 1. Transaction Support
- **Problem**: No transaction rollback for failed operations
- **Files**: `core/database.py`
- **Issue**: Partial updates may leave database inconsistent
- **Blocks**: Critical batch operations
- **Priority**: HIGH (data integrity)

### 2. Backup and Recovery
- **Problem**: No automated backup mechanism
- **Files**: No backup module
- **Issue**: Data loss risk in production
- **Blocks**: Production deployments
- **Priority**: HIGH (data safety)

## Test Coverage Gaps

### 1. Error Scenarios
- **Untested area**: Database connection failures during ingestion
- **Files**: `core/database.py`
- **Risk**: Silent failures during bulk operations
- **Priority**: HIGH
- **Missing tests**:
  - Connection timeout handling
  - Disk full scenarios
  - Network interruptions

### 2. Large File Handling
- **Untested area**: Files with >10k sections
- **Files**: `core/parser.py`
- **Risk**: Memory exhaustion or timeouts
- **Priority**: MEDIUM
- **Missing tests**: Performance and memory usage profiling

### 3. Concurrency
- **Untested area**: Multiple processes accessing database
- **Files**: No concurrency tests
- **Risk**: Database lock contention
- **Priority**: MEDIUM
- **Missing tests**: Parallel ingestion and queries

---

*Concerns audit: 2026-02-08*