# Requirements: skill-split Gap Closure

**Defined:** 2026-02-08
**Core Value:** Token-efficient progressive disclosure without data loss

## v1 Requirements

Requirements for closing identified production gaps.

### Gap Closure

**Performance & Quality:**

- [ ] **GS-01**: Fix hybrid search text scoring
  - Replace placeholder position-based scoring with proper full-text search
  - Use SQLite FTS5 or Supabase text search with rank normalization
  - Files: `core/hybrid_search.py:179-196`, `core/hybrid_search.py:282`
  - Acceptance: Text search relevance improves, tests pass

- [ ] **GS-02**: Implement batch embedding generation
  - Add batch embedding support to reduce API calls by 10-100x
  - Update `EmbeddingService.generate_embedding()` for batch processing
  - Files: `core/embedding_service.py:59-98`
  - Acceptance: Large file embedding is 10x faster, tests pass

**Safety & Reliability:**

- [ ] **GS-03**: Add transaction safety for multi-file operations
  - Wrap checkout/checkin operations in database transactions
  - Ensure atomic multi-file deployments (all-or-nothing)
  - Files: `core/checkout_manager.py:24-63`, `core/checkout_manager.py:112-175`
  - Acceptance: Failed deployments roll back cleanly, tests pass

- [ ] **GS-04**: Implement backup/restore functionality
  - Add automated backup mechanism for database
  - Implement restore functionality for disaster recovery
  - Files: New module `core/backup.py` or integrate into existing stores
  - Acceptance: Backup creates dump, restore recovers data, tests pass

**Security:**

- [ ] **GS-05**: Improve API key security
  - Add support for secret management service (HashiCorp Vault, AWS Secrets Manager)
  - Or implement short-lived token generation
  - Files: `core/embedding_service.py:52`, `core/supabase_store.py:485`
  - Acceptance: API keys not in environment variables, tests pass

## Out of Scope

| Feature | Reason |
|---------|--------|
| New file type handlers | Current 8 handlers cover all use cases |
| Alternative embedding providers | OpenAI is sufficient for current scale |
| Multi-user access control | Single-user deployment model |
| Real-time streaming | Batch processing is adequate |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GS-01 | Phase 1 | Pending |
| GS-02 | Phase 2 | Pending |
| GS-03 | Phase 3 | Pending |
| GS-04 | Phase 4 | Pending |
| GS-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0 ✓

**Phase Mappings:**
- Phase 1 (Hybrid Search Scoring): GS-01
- Phase 2 (Batch Embeddings): GS-02
- Phase 3 (Transaction Safety): GS-03
- Phase 4 (Backup/Restore): GS-04
- Phase 5 (API Key Security): GS-05

---
*Requirements defined: 2026-02-08*
*Last updated: 2026-02-08 after roadmap creation*
