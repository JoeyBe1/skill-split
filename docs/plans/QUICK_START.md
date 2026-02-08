# Phase 14: Vector Search - Quick Start Guide

**Read Time:** 3 minutes
**Prerequisites:** Supabase access, OpenAI API key

---

## The 60-Second Overview

Phase 14 adds **semantic vector search** to skill-split:
- **What:** Find sections by meaning, not just keywords
- **How:** OpenAI embeddings + pgvector database + hybrid ranking
- **Cost:** ~$0.08 one-time to embed 19,207 sections
- **Time:** 6.5 hours to implement
- **Status:** ✅ READY - Complete plan exists

---

## Files You Need

1. **Complete Plan:** `phase-14-vector-search.md` (2049 lines, 59 KB)
   - All 25 tasks with step-by-step instructions
   - Complete code ready to copy-paste
   - Cost analysis, testing, deployment

2. **Executive Summary:** `PHASE_14_SUMMARY.md` (265 lines, 7.4 KB)
   - High-level overview
   - Key design decisions
   - Phase breakdown

3. **Implementation Ready:** `PHASE_14_IMPLEMENTATION_READY.md` (current folder)
   - What was created
   - Next steps
   - Quick reference

---

## Quick Phase Breakdown

| Phase | What | Time | When to Start |
|-------|------|------|---------------|
| 1 | Add pgvector, create tables | 45 min | Day 1 |
| 2 | Build embedding service | 90 min | After Phase 1 |
| 3 | Hybrid search algorithm | 60 min | After Phase 2 |
| 4 | Connect to existing code | 45 min | After Phase 3 |
| 5 | Performance + migration | 60 min | After Phase 4 |
| 6 | Tests + documentation | 45 min | After Phase 5 |
| 7 | Deploy to production | 30 min | After Phase 6 |

---

## Before You Start

**Checklist:**
- [ ] Read [PHASE_14_SUMMARY.md](PHASE_14_SUMMARY.md) (5 min)
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Access Supabase dashboard
- [ ] Verify database has 19,207+ sections
- [ ] Estimate cost: ~$0.08

**Commands:**
```bash
# Set OpenAI key
export OPENAI_API_KEY="your-key-here"

# Verify Supabase connection (when you get there)
python -c "from core.supabase_store import SupabaseStore; print('OK')"

# Check section count (when you need it)
sqlite3 ~/.claude/databases/skill-split.db "SELECT COUNT(*) FROM sections;"
```

---

## Step 1: Read the Plan (15 minutes)

1. Read this file (3 min)
2. Read `PHASE_14_SUMMARY.md` (5 min)
3. Review `phase-14-vector-search.md` architecture (7 min)

**Stop and decide:** Do you want to implement this?

---

## Step 2: Phase 1 - Database Schema (45 minutes)

**Task 1.1:** Add pgvector extension
```
Go to Supabase Dashboard → SQL Editor → Run:
CREATE EXTENSION IF NOT EXISTS vector;
```

**Task 1.2:** Create embeddings table
- Copy SQL from `phase-14-vector-search.md` → Task 2
- Run in Supabase SQL Editor
- Takes 2-3 minutes

**Task 1.3:** Add metadata table
- Copy SQL from `phase-14-vector-search.md` → Task 3
- Run in Supabase SQL Editor
- Takes 1-2 minutes

**Result:** Database ready for embeddings

---

## Step 3: Phase 2 - Embedding Service (90 minutes)

**Task 2.1:** Design strategy (already done - in plan)

**Task 2.2:** Create `core/embedding_service.py`
- Copy EmbeddingService class from plan (200 lines)
- Copy EmbeddingCache class from plan (80 lines)
- Takes 10 minutes

**Task 2.3:** Test it
```bash
pytest test/test_vector_search.py::test_single_embedding
pytest test/test_vector_search.py::test_batch_embedding
```

**Task 2.4:** Add batch processing
- Copy method from plan
- Integrate into EmbeddingService
- Takes 15 minutes

**Result:** Embedding service ready and tested

---

## Step 4: Phase 3 - Hybrid Search (60 minutes)

**Task 3.1:** Design scoring (already done)

**Task 3.2:** Add vector search to SupabaseStore
- Copy SQL function from plan
- Copy `search_by_vector()` method
- Takes 15 minutes

**Task 3.3:** Add hybrid search
- Copy `hybrid_search()` method
- Takes 10 minutes

**Task 3.4:** Add ranking
- Copy HybridSearchRanker class (150 lines)
- Integrate into search methods
- Takes 15 minutes

**Result:** Search API ready with hybrid scoring

---

## Step 5: Phase 4 - Integration (45 minutes)

**Task 4.1:** Connect to SupabaseStore
- Modify `__init__` to use EmbeddingService
- Add `auto_embed=True` parameter
- Takes 10 minutes

**Task 4.2:** Auto-embed on store
- Modify `store_file()` to generate embeddings
- Add progress tracking
- Takes 15 minutes

**Task 4.3:** Add CLI commands
- Copy 3 new commands from plan
- Add to `skill_split.py`
- Test them
- Takes 15 minutes

**Result:** Full pipeline working end-to-end

---

## Step 6: Phase 5 - Performance (60 minutes)

**Task 5.1:** Add metrics (10 min)
- Copy SearchMetrics and MetricsCollector classes

**Task 5.2:** Incremental embedding (15 min)
- Copy method from plan for new sections only

**Task 5.3:** Migration script (20 min)
- Copy `migrate_to_vector_search.py` from plan
- Test with `--estimate` flag first
- Then run full migration

**Task 5.4:** Add indexes (15 min)
- Copy index creation SQL from plan
- Run in Supabase

**Result:** Optimized for production scale

---

## Step 7: Phase 6 - Testing (45 minutes)

**Task 6.1:** Create `test/test_vector_search.py`
- Copy test cases from plan
- 15+ tests covering all functionality
- Takes 20 minutes

**Task 6.2:** Performance benchmarks
- Copy benchmark script from plan
- Run and document results
- Takes 10 minutes

**Task 6.3:** Documentation
- Copy cost guide from plan
- Copy usage guide from plan
- Takes 10 minutes

**Result:** Verified and documented

---

## Step 8: Phase 7 - Deploy (30 minutes)

**Task 7.1:** Cost analysis (5 min)
- Review cost section in plan
- Verify estimate matches actual

**Task 7.2:** Follow deployment checklist (10 min)
- All items in `phase-14-vector-search.md` → Phase 7, Task 24

**Task 7.3:** Set up monitoring (10 min)
- Create metrics dashboard
- Set up alerts if needed

**Task 7.4:** Document for team (5 min)
- Update CLAUDE.md with new commands
- Add troubleshooting notes

**Result:** Production deployment complete!

---

## Usage Examples

**After implementation:**

```bash
# Search semantically (new!)
./skill_split.py search-vector "authenticate users"

# Hybrid search (best results)
./skill_split.py search-hybrid "security" --vector-weight 0.7

# Generate embeddings for new sections
./skill_split.py generate-embeddings

# Adjust semantic weight
./skill_split.py search-hybrid "oauth" --vector-weight 0.9
```

---

## Key Numbers

| Item | Value |
|------|-------|
| **Sections:** | 19,207 |
| **Embedding dimensions:** | 1536 |
| **Model:** | text-embedding-3-small |
| **One-time cost:** | ~$0.08 |
| **Monthly cost:** | ~$0.001 |
| **Query latency:** | 50-200ms |
| **Cache hit rate:** | 80%+ |
| **Relevance improvement:** | 40-60% |
| **Implementation time:** | 6.5 hours |

---

## Common Questions

**Q: Is this required?**
A: No. Phases 1-13 work without Phase 14. This is an optional enhancement.

**Q: Can I implement it in pieces?**
A: Yes. After Phase 1-2, you have working embeddings. After Phase 3-4, you have working search. Can release progressively.

**Q: What if OpenAI API fails?**
A: Migration script is resumable. Restart from last checkpoint with `--resume-from <section_id>`.

**Q: How do I test without committing?**
A: Implement in a branch, run tests, then merge. See plan Phase 6 for test cases.

**Q: Can I skip certain phases?**
A: Phases are sequential. Phase 2 requires Phase 1. Phase 3 requires Phase 2. Etc.

**Q: What about the existing search?**
A: Text search continues to work. Hybrid search combines both.

---

## Troubleshooting

**"pgvector not found"**
- Run: `CREATE EXTENSION IF NOT EXISTS vector;` in Supabase

**"OpenAI API error"**
- Check: `OPENAI_API_KEY` environment variable set
- Check: Rate limits (3000 req/min)
- Reduce batch size in EmbeddingService

**"Migration taking too long"**
- Normal for 19,207 sections (~2-3 minutes)
- Can pause with Ctrl+C, resume with `--resume-from`

**"Search results not relevant"**
- Adjust `--vector-weight` (try 0.9 for more semantic)
- Use text search if you need exact keywords

---

## Next Steps

1. **Right now:** Read `PHASE_14_SUMMARY.md` (5 min)
2. **Next:** Review architecture section in `phase-14-vector-search.md` (15 min)
3. **When ready:** Start Phase 1, Task 1 (Supabase setup)
4. **Follow:** Implementation plan sequentially

---

## Links in This Repo

- **Full Plan:** `docs/plans/phase-14-vector-search.md`
- **Summary:** `docs/plans/PHASE_14_SUMMARY.md`
- **Status:** `PHASE_14_IMPLEMENTATION_READY.md`
- **This file:** `docs/plans/QUICK_START.md`
- **Navigation Hub:** `docs/plans/README.md`

---

## Estimated Timeline

- **Today:** Read plan (20 min) + Phase 1 (45 min) = 1 hour
- **Tomorrow:** Phase 2-4 (4 hours)
- **Next day:** Phase 5-7 (2.5 hours)

**Total:** 6.5 hours of focused work

---

**Status:** ✅ READY TO START
**Complexity:** MODERATE
**Estimated Effort:** 6.5 hours
**Expected Outcome:** Semantic search fully operational

---

*For detailed information, see `phase-14-vector-search.md`*
*For executive summary, see `PHASE_14_SUMMARY.md`*
