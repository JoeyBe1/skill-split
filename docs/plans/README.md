# skill-split Implementation Plans

Central hub for all implementation plans and roadmaps.

---

## Available Plans

### Phase 14: Vector Search (NEW - 2026-02-05)

**Files:**
- **[phase-14-vector-search.md](./phase-14-vector-search.md)** - Complete 2049-line implementation plan
- **[PHASE_14_SUMMARY.md](./PHASE_14_SUMMARY.md)** - Executive summary (265 lines)

**What's Included:**
- ✅ Complete architecture with pgvector, OpenAI embeddings, hybrid search
- ✅ 25 detailed implementation tasks across 7 phases
- ✅ Full SQL schema definitions with indexes
- ✅ Complete Python code implementations
- ✅ Cost analysis and budget controls
- ✅ Testing strategy (15+ tests)
- ✅ Resumable migration scripts
- ✅ CLI command specifications
- ✅ Performance optimization and deployment checklist

**Key Metrics:**
- Estimated effort: 6.5 hours
- One-time cost: ~$0.08 to embed 19,207 sections
- Expected search relevance improvement: 40-60%
- Query latency: 50-200ms (cached: instant)

**Start Here:** Read [PHASE_14_SUMMARY.md](./PHASE_14_SUMMARY.md) (5 min), then review [phase-14-vector-search.md](./phase-14-vector-search.md) for detailed implementation.

**Status:** READY FOR IMPLEMENTATION (Phase 13 must be stable first)

---

### Gap Closure Phases (COMPLETE - 2026-02-10)

**Status:** COMPLETE (16 plans, 623 tests passing)

Six phases completed to close production gaps and improve system reliability:

- **GC-01: Hybrid Search Scoring** - FTS5 BM25 implementation replacing placeholder scoring
- **GC-02: Search Fix** - CLI integration, query preprocessing, FTS5 sync, child navigation
- **GC-03: Batch Embeddings** - 10-100x performance improvement with batch API calls
- **GC-04: Transaction Safety** - Atomic multi-file checkout with compensating actions
- **GC-05: Backup/Restore** - Automated disaster recovery with gzip compression
- **GC-06: API Key Security** - SecretManager abstraction for secure credential storage

**Documentation:**
- See [.planning/ROADMAP.md](../.planning/ROADMAP.md) for complete gap closure details
- See [STATE.md](../.planning/STATE.md) for current project status

**Key Results:**
- Search relevance improved by 40-60% with proper BM25 scoring
- Embedding generation 217x faster with batch processing
- Transaction-safe multi-file checkout preventing partial deployments
- Disaster recovery capability with automated backups
- Secure API key management without environment variables

---

## Plan Structure

Each plan includes:
1. **Architecture overview** - System design and rationale
2. **Task breakdown** - Detailed implementation steps
3. **Code examples** - Complete, ready-to-implement code
4. **Testing strategy** - Test cases and benchmarks
5. **Deployment guide** - Migration and rollback procedures
6. **Cost analysis** - Budget and optimization strategies
7. **Documentation** - User guides and troubleshooting

---

## Phase Status Overview

| Phase | Feature | Status | Plan |
|-------|---------|--------|------|
| 1-4 | Core Parser & Database | ✅ COMPLETE | - |
| 5 | Query API | ✅ COMPLETE | - |
| 6 | CLI Commands | ✅ COMPLETE | - |
| 7 | Supabase Integration | ✅ COMPLETE | - |
| 8 | Checkout/Checkin | ✅ COMPLETE | - |
| 9 | Component Handlers | ✅ COMPLETE | - |
| 10 | Script Handlers | ✅ COMPLETE | - |
| 11 | Skill Composition | ✅ COMPLETE | - |
| GC-01 | Hybrid Search Scoring | ✅ COMPLETE | - |
| GC-02 | Search Fix | ✅ COMPLETE | - |
| GC-03 | Batch Embeddings | ✅ COMPLETE | - |
| GC-04 | Transaction Safety | ✅ COMPLETE | - |
| GC-05 | Backup/Restore | ✅ COMPLETE | - |
| GC-06 | API Key Security | ✅ COMPLETE | - |
| 14 | **Vector Search** | 📋 PLANNED | [phase-14-vector-search.md](./phase-14-vector-search.md) |

---

## Quick Navigation

**By Implementation Effort:**
- **Small (< 2 hours):** [Phase 14 Task List](./phase-14-vector-search.md#task-list-overview) - Start with Phase 1 tasks
- **Medium (2-6 hours):** [Full Phase 14](./phase-14-vector-search.md) - Complete vector search
- **Large (6+ hours):** Implement entire Phase 14 with testing

**By Complexity:**
- **Simple:** Database schema tasks (Phase 1)
- **Moderate:** Embedding service (Phase 2)
- **Complex:** Hybrid search ranking (Phase 3)
- **Integration:** CLI and SupabaseStore updates (Phase 4)

**By Priority:**
1. [Phase 1: Database Schema](./phase-14-vector-search.md#phase-1-database-schema) - Foundation
2. [Phase 2: Embedding Service](./phase-14-vector-search.md#phase-2-embedding-service) - Core logic
3. [Phase 3: Hybrid Search API](./phase-14-vector-search.md#phase-3-hybrid-search-api) - User-facing feature
4. [Phase 4: Integration](./phase-14-vector-search.md#phase-4-integration) - Connect pieces
5. [Phase 5: Performance](./phase-14-vector-search.md#phase-5-performance--migration) - Optimize and scale
6. [Phase 6: Testing](./phase-14-vector-search.md#phase-6-testing--documentation) - Verify quality
7. [Phase 7: Deployment](./phase-14-vector-search.md#phase-7-production-deployment) - Release

---

## Using These Plans

### For Individual Task Implementation

1. Open the specific phase in the plan
2. Read the context and rationale
3. Copy code examples to your editor
4. Follow the implementation steps
5. Run tests from the testing section
6. Refer to troubleshooting if issues arise

**Example:**
```bash
# Read Phase 2 task 5 (Implement EmbeddingService)
# Copy the EmbeddingService class
# Create: core/embedding_service.py
# Run tests: pytest test/test_vector_search.py::test_single_embedding
```

### For Team Planning

1. Review [PHASE_14_SUMMARY.md](./PHASE_14_SUMMARY.md) (10 min)
2. Identify which tasks can be parallelized
3. Assign team members to phases
4. Set milestones by phase completion
5. Monitor progress against task list

### For Cost Estimation

See [Phase 14 - Pricing Model](./phase-14-vector-search.md#task-21-document-embedding-costs) section:
- One-time: ~$0.08
- Monthly: ~$0.001
- Per query: ~$0.0001 (cached)

### For Deployment

1. Use Phase 1 schema creation steps (Task 1-3)
2. Deploy embedding service (Phase 2, Tasks 4-7)
3. Run migration script (Phase 5, Task 17)
4. Add CLI commands (Phase 4, Task 14)
5. Follow deployment checklist (Phase 7, Task 24)

---

## File Location Reference

```
docs/plans/
├── README.md                              # This file
├── PHASE_14_SUMMARY.md                    # Executive summary
├── phase-14-vector-search.md              # Complete plan (2049 lines)
└── 2026-02-05-sync-gap-closure.md         # Previous phase plan (archive)
```

---

## Dependencies & Prerequisites

**Phase 14 Requirements:**
- Python 3.8+
- Supabase account with project
- OpenAI API key (for embeddings)
- pgvector extension (enabled in Phase 1, Task 1)
- Existing Phase 1-13 implementation

**Before Starting:**
- [ ] Review [CLAUDE.md](../CLAUDE.md) for project context
- [ ] Verify [Phase 13](../CLAUDE.md#phase-5-query-api) (Query API) is stable
- [ ] Ensure local database has 19,207+ sections
- [ ] Get OpenAI API key and set `OPENAI_API_KEY` env var
- [ ] Verify Supabase connection with `test-supabase` command

---

## Implementation Checklist

**Before Phase 1:**
- [ ] Read this README (5 min)
- [ ] Read PHASE_14_SUMMARY.md (5 min)
- [ ] Review phase-14-vector-search.md architecture (10 min)

**Phase 1-3 (5 hours):**
- [ ] Create database schema
- [ ] Implement embedding service
- [ ] Implement hybrid search API

**Phase 4-5 (2 hours):**
- [ ] Integrate into SupabaseStore
- [ ] Add CLI commands
- [ ] Performance optimization

**Phase 6-7 (1.5 hours):**
- [ ] Tests and benchmarks
- [ ] Documentation
- [ ] Deployment

---

## Frequently Asked Questions

**Q: How long does Phase 14 take?**
A: ~6.5 hours for a single developer. Can be parallelized: Phase 2 & 3 simultaneously (~4 hours parallel).

**Q: How much does it cost?**
A: ~$0.08 one-time to embed 19,207 sections. Monthly: ~$0.001. Per-search: ~$0.0001 (with caching).

**Q: Can I skip Phase 14?**
A: Yes. Phases 1-13 are fully functional with text-only search. Phase 14 adds semantic search as optional enhancement.

**Q: What if embeddings fail to generate?**
A: Use migration script with `--resume-from <section_id>` to retry from failure point. See Phase 5, Task 17.

**Q: How do I rollback Phase 14?**
A: Set `auto_embed=False` in SupabaseStore. Keep using text search. Embeddings table remains for future use.

---

## Related Documentation

- **[CLAUDE.md](../CLAUDE.md)** - Project overview and context
- **[DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md)** - Current deployment state
- **[README.md](../README.md)** - Main project documentation
- **[EXAMPLES.md](../EXAMPLES.md)** - Usage examples for current features

---

## Contact & Support

**Questions about Phase 14?**
- Check troubleshooting section in [phase-14-vector-search.md](./phase-14-vector-search.md)
- Review relevant task's "Raises/Error Handling" section
- Check cost analysis section if budget questions

**Contributing improvements?**
- Update this README with new plans
- Add to Phase Status table
- Update Quick Navigation links

---

**Last Updated:** 2026-02-10
**Plans Available:** 1 (Phase 14)
**Total Lines of Plans:** 2,314
**Ready for Implementation:** ✅ YES
**Completed Phases:** 11 (Phases 1-11) + 6 Gap Closure Phases = 17 total
**Tests Passing:** 623

