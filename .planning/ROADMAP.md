# Roadmap: skill-split Gap Closure

## Overview

This roadmap closes 5 identified production gaps in the skill-split system. Each gap maps to one phase, delivering improvements to search quality, performance, data safety, and security. Phases execute sequentially with minimal dependencies, enabling parallel planning of subsequent phases.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Hybrid Search Scoring** - Replace placeholder text scoring with proper full-text search ✓ (2026-02-08)
- [x] **Phase 2: Search Fix** - Fix CLI search, add query preprocessing, FTS5 sync, child navigation, and documentation ✓ (2026-02-08)
- [x] **Phase 3: Batch Embeddings** - Implement batch embedding generation for 10-100x speedup ✓ (2026-02-08)
- [x] **Phase 4: Transaction Safety** - Add atomic multi-file checkout operations ✓ (2026-02-09)
- [x] **Phase 5: Backup/Restore** - Implement automated backup and disaster recovery ✓ (2026-02-10)
- [x] **Phase 6: API Key Security** - Remove API keys from environment variables ✓ (2026-02-10)
- [x] **Phase 7: Documentation Gaps** - Close documentation gaps for backup/restore and phase status ✓ (2026-02-10)

## Future Phases (Planned)

- [ ] **Phase 8: Community Skill Discovery** - Ingest community skill repos (awesome-claude-code, awesome-claude-skills, GitHub topics) into the skill-split DB. Any LLM can search and checkout community skills the same way it searches local skills. This transforms skill-split from a personal library into a community skill discovery layer. **Joey's idea, 2026-02-18.**

- [ ] **Phase 9: GitHub Actions Ingest** - Auto-ingest new skills from watched repos on push. Keep the community DB fresh without manual effort.

- [ ] **Phase 10: skill-split as MCP Server** - Expose search/checkout/compose as MCP tools so any Claude session can query the skill library natively without CLI.

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
- [x] 01-01-PLAN.md - Implement FTS5-based text scoring with rank normalization ✓
- [x] 01-02-PLAN.md - Add text search quality tests for relevance verification ✓

### Phase 2: Search Fix

**Goal**: CLI search uses FTS5 BM25 ranking with intelligent query preprocessing and comprehensive documentation

**Depends on**: Phase 1 (FTS5 implementation)

**Success Criteria** (what must be TRUE):
1. CLI search uses FTS5 BM25 ranking instead of LIKE queries
2. Multi-word queries use OR for discovery ("setup git" finds sections with either word)
3. Exact phrases preserved with quotes
4. Progressive disclosure supports child navigation via --child flag
5. FTS5 index stays synchronized after all CRUD operations
6. Comprehensive documentation explains all search modes and navigation

**Plans**: 5 plans

Plans:
- [x] 02-01-PLAN.md - CLI search command FTS5 integration ✓
- [x] 02-02-PLAN.md - Smart query preprocessing for natural language ✓
- [x] 02-03-PLAN.md - FTS5 index synchronization fixes ✓
- [x] 02-04-PLAN.md - Child navigation for progressive disclosure ✓
- [x] 02-05-PLAN.md - Comprehensive search and navigation documentation ✓

### Phase 3: Batch Embeddings

**Goal**: Large file embedding generation is 10-100x faster through batch API calls

**Depends on**: Nothing (can run in parallel with Phases 1-2)

**Requirements**: GS-02

**Success Criteria** (what must be TRUE):
1. User ingests 1000 sections and embeddings complete in ~1 minute instead of ~15 minutes
2. Embedding service automatically batches requests up to OpenAI's limit (2048 embeddings per batch)
3. Batch embedding fails gracefully with partial results if API rate limit exceeded
4. All existing embedding tests pass with batch implementation

**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md - Add batch_generate_embeddings() with 2048-item batch support and graceful failure ✓
- [x] 03-02-PLAN.md - Add comprehensive batch integration tests and performance benchmarks ✓

### Phase 4: Transaction Safety

**Goal**: Multi-file checkout operations are atomic (all-or-nothing) with automatic rollback on failure

**Depends on**: Nothing (can run in parallel with Phases 1-3)

**Requirements**: GS-03

**Success Criteria** (what must be TRUE):
1. User checks out multi-file component and partial failure leaves no files deployed
2. Failed checkin operation rolls back all database changes atomically
3. Transaction errors are logged with clear messages about which operation failed
4. All existing tests pass with transaction wrapping

**Plans**: 2 plans

Plans:
- [x] 04-01-PLAN.md - Wrap checkout_manager.py operations in compensating actions ✓
- [x] 04-02-PLAN.md - Add transaction rollback tests for multi-file failure scenarios ✓

### Phase 5: Backup/Restore

**Goal**: User can create automated database backups and restore from them for disaster recovery

**Depends on**: Nothing (can run in parallel with Phases 1-4)

**Requirements**: GS-04

**Success Criteria** (what must be TRUE):
1. User runs backup command and creates timestamped database dump file
2. User runs restore command and recovers database from backup file
3. Backup includes all sections, metadata, and embeddings
4. Restore operation validates data integrity after restoration

**Plans**: 2 plans

Plans:
- [x] 05-01-PLAN.md - Create backup module with SQLite dump functionality ✓
- [x] 05-02-PLAN.md - Add restore command with integrity validation ✓

### Phase 6: API Key Security

**Goal**: API keys retrieved from secure storage, not environment variables

**Depends on**: Nothing (can run in parallel with Phases 1-5)

**Requirements**: GS-05

**Success Criteria** (what must be TRUE):
1. User runs skill-split commands without OPENAI_API_KEY in environment
2. EmbeddingService retrieves API key from configured secret manager
3. SupabaseStore retrieves service key from configured secret manager
4. Secret manager integration includes fallback to environment variables for local development

**Plans**: 3 plans

Plans:
- [x] 06-01-PLAN.md - Create SecretManager abstraction with file, keyring, and environment sources ✓
- [x] 06-02-PLAN.md - Update EmbeddingService to use SecretManager with backward compatibility ✓
- [x] 06-03-PLAN.md - Update SupabaseStore and CLI to use SecretManager ✓

### Phase 7: Documentation Gaps

**Goal**: Close all remaining documentation gaps identified by verification team

**Depends on**: Phases 1-6 (all features complete)

**Success Criteria** (what must be TRUE):
1. README.md documents backup and restore commands with usage examples
2. EXAMPLES.md includes backup/restore workflow examples and disaster recovery scenarios
3. docs/plans/README.md includes all completed phases in status table
4. All documentation reflects current project state (623 tests passing)

**Plans**: 3 plans

Plans:
- [x] 07-01-PLAN.md - Update README.md with backup/restore command documentation ✓
- [x] 07-02-PLAN.md - Add backup/restore examples to EXAMPLES.md ✓
- [x] 07-03-PLAN.md - Update docs/plans/README.md with complete phase status ✓

## Requirements Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GS-01 | Phase 1 | Complete |
| GS-02 | Phase 3 | Complete |
| GS-03 | Phase 4 | Complete |
| GS-04 | Phase 5 | Complete |
| GS-05 | Phase 6 | Complete |

---
*Roadmap created: 2026-02-08*
*Last updated: 2026-02-10 (Phase 7 complete - All 7 phases executed, 19 plans complete, 623 tests passing)*
