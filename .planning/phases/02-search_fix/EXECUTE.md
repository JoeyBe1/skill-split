# EXECUTE PHASE 02: Search Fix

**Date:** 2026-02-08
**Status:** READY FOR EXECUTION

## Command to Execute

```bash
/gsd:execute-phase 02-search_fix
```

## What This Does

Executes 5 comprehensive plans with verifier agents after each:

1. **Plan 02-01**: CLI FTS5 Integration → Verifier → Commit
2. **Plan 02-02**: Smart Query Processing → Verifier → Commit
3. **Plan 02-03**: FTS5 Sync Fix → Verifier → Commit
4. **Plan 02-04**: Progressive Disclosure → Verifier → Commit
5. **Plan 02-05**: Documentation → Verifier → Commit

## Three Search Modes Covered

### Before Execution
| Search Type | Status |
|-------------|--------|
| BM25 (Keywords) | ❌ Uses LIKE, not FTS5 |
| Vector (Semantic) | ✅ Working via `search-semantic` |
| Hybrid (Combined) | ✅ Working via `search-semantic` |

### After Execution
| Search Type | Status |
|-------------|--------|
| BM25 (Keywords) | ✅ `search` uses FTS5 BM25 |
| Vector (Semantic) | ✅ `search-semantic` working |
| Hybrid (Combined) | ✅ `search-semantic` working |
| Documentation | ✅ All 3 modes documented |

## Execution Waves

**Wave 1 (Parallel):**
- Plan 02-01: CLI FTS5 Integration
- Plan 02-02: Smart Query Processing
- Plan 02-03: FTS5 Sync Fix

**Wave 2 (After 01):**
- Plan 02-04: Progressive Disclosure

**Wave 3 (After all):**
- Plan 02-05: Documentation

## Expected Results

**Tests:** 485 → 515 (+30 new tests)

**Features:**
- Multi-word search works: "git setup" finds relevant sections
- Exact phrase search: `"exact phrase"` with quotes
- Relevance scores displayed for BM25
- FTS5 index synchronized automatically
- Navigate to subsections with `--child` flag
- Complete documentation for all 3 search modes

**No Regressions:**
- All 485 existing tests pass
- Byte-perfect round-trip preserved
- SHA256 verification maintained
- Backward compatible

## Context Management

**Before execution:**
```bash
/clear
```

**After execution:**
```bash
/clear
```

**Status check:**
```bash
/gsd:status
```

## Rollback

If issues occur, each plan commits separately:
```bash
git log --oneline -5  # See recent commits
git revert <commit>  # Rollback specific plan
```

## Verification

After execution, verify:
```bash
# Test BM25 search
./skill_split.py search "python handler" --db skill_split.db

# Test vector search (requires API keys)
./skill_split.py search-semantic "code execution" --db skill_split.db

# Test navigation
./skill_split.py list /test/file.md --db skill_split.db
./skill_split.py next <id> /test/file.md --child

# Run all tests
python -m pytest test/ -v
```

---

**Ready to execute?** Run: `/gsd:execute-phase 02-search_fix`
