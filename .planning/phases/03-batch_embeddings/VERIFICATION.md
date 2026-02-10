---
phase: 03-batch_embeddings
status: ready
created: 2026-02-08
plans: 2
---

# Phase 3: Batch Embeddings - Verification Plan

**Phase Goal**: Large file embedding generation is 10-100x faster through optimized batch API calls and parallel processing

**Plans**: 2 comprehensive plans
- 03-01: Implement True Batch Embedding Generation
- 03-02: Comprehensive Tests and Performance Benchmarks

## Unified Success Criteria

### Observable Truths (Must Be TRUE After Execution)

| # | Truth | Plan | Evidence |
|---|-------|------|----------|
| 1 | Batch size supports up to 2,048 texts per API call | 03-01 | `max_batch_size` parameter accepts 2048 |
| 2 | Embeddings process in parallel using ThreadPoolExecutor | 03-01 | `batch_generate_parallel()` with max_workers parameter |
| 3 | Token-aware batching keeps each batch under 8,191 token limit | 03-01 | `_create_token_aware_batches()` estimates and limits tokens |
| 4 | Integration points use batch operations (supabase_store.py, database.py) | 03-01 | `batch_generate_embeddings()` methods added to both stores |
| 5 | Graceful failure with partial results saved | 03-01 | Failed batches don't crash entire process |
| 6 | Rate limit retry with exponential backoff | 03-01 | `batch_generate_with_retry()` implements backoff logic |
| 7 | 10-100x speedup verified by benchmarks | 03-02 | Performance tests show improvement |
| 8 | All existing 518 tests pass | 03-02 | No regressions from implementation |
| 9 | Token-aware batching tests pass | 03-02 | 5 tests verify batch limits |
| 10 | Parallel processing tests pass | 03-02 | 5 tests verify concurrent execution |

## Execution Order

### Wave 1: Foundation (Plan 03-01)
```
03-01-PLAN.md ──> Implementation ──> Verifier ──> Commit
```

**Dependencies**: None
**Parallelizable**: No (must complete before testing)

### Wave 2: Verification (Plan 03-02)
```
03-02-PLAN.md ──> Tests ──> Verifier ──> Commit
```

**Dependencies**: Plan 03-01 must be complete
**Parallelizable**: No (requires implementation)

## Required Artifacts

### From Plan 03-01
| Artifact | File | Description |
|----------|------|-------------|
| Updated batch_generate() | core/embedding_service.py | max_batch_size=2048, token-aware batching |
| batch_generate_parallel() | core/embedding_service.py | Parallel processing with ThreadPoolExecutor |
| _create_token_aware_batches() | core/embedding_service.py | Token-aware batch creation |
| batch_generate_with_retry() | core/embedding_service.py | Rate limit retry logic |
| batch_generate_embeddings() | core/supabase_store.py | Batch integration for Supabase |
| batch_generate_embeddings() | core/database.py | Batch integration for SQLite |

### From Plan 03-02
| Artifact | File | Description |
|----------|------|-------------|
| TestTokenAwareBatching | test/test_embedding_service.py | 5 tests for token-aware batching |
| TestParallelBatchProcessing | test/test_embedding_service.py | 5 tests for parallel processing |
| TestBatchEmbeddingIntegration | test/test_batch_integration.py | 2 integration tests |
| TestEmbeddingPerformance | test/test_embedding_benchmarks.py | 4 performance benchmarks |
| TestRateLimitHandling | test/test_embedding_service.py | 2 tests for rate limits |
| Performance documentation | README.md | Performance section added |

## Verification Steps

### After Plan 03-01

1. **Code Review**
   - Check max_batch_size increased to 2048
   - Verify token-aware batching implementation
   - Verify parallel processing with ThreadPoolExecutor
   - Verify rate limit retry logic

2. **Manual Testing**
   ```python
   # Test large batch
   service = EmbeddingService(api_key)
   texts = [f"section {i}" for i in range(5000)]
   embeddings = service.batch_generate_parallel(texts, max_workers=5)
   # Should complete in ~30 seconds (not 30+ minutes)
   ```

3. **Verifier Agent**: `compound-engineering:review:kieran-python-reviewer`

### After Plan 03-02

1. **Run New Tests**
   ```bash
   python -m pytest test/test_embedding_service.py::TestTokenAwareBatching -v
   python -m pytest test/test_embedding_service.py::TestParallelBatchProcessing -v
   python -m pytest test/test_batch_integration.py -v
   python -m pytest test/test_embedding_benchmarks.py -v
   python -m pytest test/test_embedding_service.py::TestRateLimitHandling -v
   ```

2. **Run All Tests**
   ```bash
   python -m pytest test/ -v
   # Expected: 518 + 19 = 537 tests passing
   ```

3. **Verifier Agent**: `compound-engineering:review:performance-oracle`

## Expected Results

### Before Execution
- 518 tests passing
- 19,207 sections = 19,207 API calls = 30+ minutes
- max_batch_size = 100
- No parallel processing

### After Execution
- 537 tests passing (+19 new tests)
- 19,207 sections = ~10 API calls = ~30 seconds
- max_batch_size = 2048
- Parallel processing with 5 workers
- Token-aware batching
- Rate limit handling

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI API rate limits | Medium | Exponential backoff, graceful failure |
| Memory usage for large batches | Low | Token-aware batching limits memory |
| Test flakiness from network | Low | Mock OpenAI client in tests |
| Regression in existing code | Low | All 518 tests must pass |

## Rollback Plan

If issues occur:
```bash
# Check recent commits
git log --oneline -3

# Revert specific plan
git revert <commit-hash>

# Or reset to before phase
git reset --hard HEAD~2
```

## Context Management

**Before execution:**
```bash
/clear
```

**After Plan 03-01:**
```bash
/clear
```

**After Plan 03-02:**
```bash
/clear
```

## Status

- [x] Plan 03-01 created
- [x] Plan 03-02 created
- [x] Verification plan created
- [ ] Plan 03-01 executed
- [ ] Plan 03-02 executed
- [ ] Phase 3 complete

---

**Ready to execute?** Run: `/clear` then `/gsd:execute-phase 03-batch_embeddings`
