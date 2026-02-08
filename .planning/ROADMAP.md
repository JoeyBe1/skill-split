# Roadmap: skill-split Gap Closure

## Overview

This roadmap closes 5 identified production gaps in the skill-split system. Each gap maps to one phase, delivering improvements to search quality, performance, data safety, and security. Phases execute sequentially with minimal dependencies, enabling parallel planning of subsequent phases.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Hybrid Search Scoring** — Replace placeholder text scoring with proper full-text search ✓ (2026-02-08)
- [ ] **Phase 2: Batch Embeddings** - Implement batch embedding generation for 10-100x speedup
- [ ] **Phase 3: Transaction Safety** - Add atomic multi-file checkout operations
- [ ] **Phase 4: Backup/Restore** - Implement automated backup and disaster recovery
- [ ] **Phase 5: API Key Security** - Remove API keys from environment variables

## Phase Details

### Phase 1: Hybrid Search Scoring

**Goal**: Hybrid search returns relevant results based on actual text content, not position-based placeholder scoring

**Depends on**: Nothing (first phase)

**Requirements**: GS-01

**Success Criteria** (what must be TRUE):
1. User searches for "vector search" and finds sections about vector search regardless of position in file
2. User searches for "python handler" and sees relevant Python sections ranked higher than unrelated sections
3. Hybrid search results include normalized relevance scores combining text and vector similarity
4. All existing tests pass with new scoring implementation

**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Implement FTS5-based text scoring with rank normalization ✓
- [x] 01-02-PLAN.md — Add text search quality tests for relevance verification ✓

### Phase 2: Batch Embeddings

**Goal**: Large file embedding generation is 10-100x faster through batch API calls

**Depends on**: Nothing (can run in parallel with Phase 1)

**Requirements**: GS-02

**Success Criteria** (what must be TRUE):
1. User ingests 1000 sections and embeddings complete in ~1 minute instead of ~15 minutes
2. Embedding service automatically batches requests up to OpenAI's limit (2048 embeddings per batch)
3. Batch embedding fails gracefully with partial results if API rate limit exceeded
4. All existing embedding tests pass with batch implementation

**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Add batch_generate_embeddings() with 2048-item batch support and graceful failure
- [ ] 02-02-PLAN.md — Add comprehensive batch integration tests and performance benchmarks

### Phase 3: Transaction Safety

**Goal**: Multi-file checkout operations are atomic (all-or-nothing) with automatic rollback on failure

**Depends on**: Nothing (can run in parallel with Phases 1-2)

**Requirements**: GS-03

**Success Criteria** (what must be TRUE):
1. User checks out multi-file component and partial failure leaves no files deployed
2. Failed checkin operation rolls back all database changes atomically
3. Transaction errors are logged with clear messages about which operation failed
4. All existing tests pass with transaction wrapping

**Plans**: TBD

Plans:
- [ ] 03-01: Wrap checkout_manager.py operations in database transactions
- [ ] 03-02: Add transaction rollback tests for multi-file failure scenarios

### Phase 4: Backup/Restore

**Goal**: User can create automated database backups and restore from them for disaster recovery

**Depends on**: Nothing (can run in parallel with Phases 1-3)

**Requirements**: GS-04

**Success Criteria** (what must be TRUE):
1. User runs backup command and creates timestamped database dump file
2. User runs restore command and recovers database from backup file
3. Backup includes all sections, metadata, and embeddings
4. Restore operation validates data integrity after restoration

**Plans**: TBD

Plans:
- [ ] 04-01: Create backup module with SQLite dump functionality
- [ ] 04-02: Add restore command with integrity validation

### Phase 5: API Key Security

**Goal**: API keys retrieved from secure storage, not environment variables

**Depends on**: Nothing (can run in parallel with Phases 1-4)

**Requirements**: GS-05

**Success Criteria** (what must be TRUE):
1. User runs skill-split commands without OPENAI_API_KEY in environment
2. EmbeddingService retrieves API key from configured secret manager
3. SupabaseStore retrieves service key from configured secret manager
4. Secret manager integration includes fallback to environment variables for local development

**Plans**: TBD

Plans:
- [ ] 05-01: Add secret manager integration (HashiCorp Vault or AWS Secrets Manager)
- [ ] 05-02: Add fallback to environment variables for local development
- [ ] 05-03: Update tests to support secret manager mocking

## Requirements Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GS-01 | Phase 1 | Complete |
| GS-02 | Phase 2 | Ready to execute |
| GS-03 | Phase 3 | Planned |
| GS-04 | Phase 4 | Planned |
| GS-05 | Phase 5 | Planned |

---
*Roadmap created: 2026-02-08*
*Last updated: 2026-02-08*
