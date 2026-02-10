# NEXT SESSION: Execute Search Fix

**Date:** 2026-02-08
**Status:** PLANS COMPLETE, READY TO EXECUTE

## Command to Execute

```bash
/clear
/gsd:execute-phase 02-search_fix
```

## What This Does

Executes 5 comprehensive plans with verifier agents:

1. **Plan 02-01**: CLI FTS5 Integration → Verifier → Commit
2. **Plan 02-02**: Smart Query Processing → Verifier → Commit
3. **Plan 02-03**: FTS5 Sync Fix → Verifier → Commit
4. **Plan 02-04**: Progressive Disclosure → Verifier → Commit
5. **Plan 02-05**: Documentation → Verifier → Commit

## Expected Results

**Before:**
- 485 tests passing
- `search` uses LIKE (broken multi-word)
- No query preprocessing
- FTS5 sync edge cases
- No child navigation
- Incomplete docs

**After:**
- 515 tests passing (+30 new)
- `search` uses FTS5 BM25 (fixed)
- Smart query preprocessing (OR for discovery)
- FTS5 sync robust
- `next --child` for subsections
- Complete BM25+Vector+Hybrid docs

## Three Search Modes

### 1. BM25 (Keywords) - `search` command
```bash
./skill_split.py search "python handler"
```
**Features:** Fast local search, FTS5 BM25 ranking, multi-word OR

### 2. Vector (Semantic) - `search-semantic` command
```bash
./skill_split.py search-semantic "code execution" --vector-weight 1.0
```
**Features:** Semantic similarity, OpenAI embeddings, requires API keys

### 3. Hybrid (Combined) - `search-semantic` command
```bash
./skill_split.py search-semantic "python error" --vector-weight 0.7
```
**Features:** Best of both, 70% semantic + 30% keyword by default

## Verification After Execution

```bash
# Test BM25 search
./skill_split.py search "python handler" --db skill_split.db

# Test vector search (requires API keys)
./skill_split.py search-semantic "code execution" --db skill_split.db

# Test all tests
python -m pytest test/ -v
```

## Context Management

**Before execution:**
```bash
/clear
```

**After execution:**
```bash
/clear
```

## Files Created

Plans:
- `.planning/phases/02-search_fix/02-01-PLAN.md`
- `.planning/phases/02-search_fix/02-02-PLAN.md`
- `.planning/phases/02-search_fix/02-03-PLAN.md`
- `.planning/phases/02-search_fix/02-04-PLAN.md`
- `.planning/phases/02-search_fix/02-05-PLAN.md`

Verification:
- `.planning/phases/02-search_fix/VERIFICATION.md`
- `.planning/phases/02-search_fix/EXECUTE.md`

Research:
- `.planning/research/search-investigation.md`

Workflow:
- `.planning/GSD_WORKFLOW.md`

## Duration

**Expected:** ~45 minutes

## Rollback

If issues occur:
```bash
git log --oneline -5  # See commits
git revert <commit>  # Rollback specific plan
```

---

**Ready?** Run: `/clear` then `/gsd:execute-phase 02-search_fix`
