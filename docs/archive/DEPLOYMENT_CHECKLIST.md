# Skill-Split Production Deployment Checklist

**Last Updated**: 2026-02-05
**Version**: 1.0
**Status**: Ready for Production

---

## Phase 0: Pre-Deployment Validation

- [ ] All 205+ tests passing (`pytest test/`)
- [ ] SQLite database verified with sample data
- [ ] Supabase credentials configured in `.env`
- [ ] Python 3.9+ installed and available
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] No sensitive data in version control

**Approver Signature**: ___________________  **Date**: _________

---

## Phase 1: Core Database Setup (SQLite)

### Local Development

- [ ] Create database directory: `mkdir -p ~/.claude/databases`
- [ ] Verify database path: `~/.claude/databases/skill-split.db`
- [ ] Run schema creation: `./skill_split.py init-db`
- [ ] Test basic operations:
  ```bash
  ./skill_split.py parse test/fixtures/sample.md
  ./skill_split.py validate test/fixtures/sample.md
  ```
- [ ] Confirm database file created and readable
- [ ] Run smoke tests: `pytest test/test_database.py -v`

**Verified By**: ___________________  **Date**: _________

---

## Phase 2: Core Features Deployment

### Parser & Format Detection

- [ ] Test markdown parsing: `./skill_split.py parse ~/.claude/skills/agent-browser/SKILL.md`
- [ ] Test YAML frontmatter detection
- [ ] Test XML tag parsing (if applicable)
- [ ] Verify heading level detection (h1-h6)
- [ ] Run parser tests: `pytest test/test_parser.py -v`

### Hashing & Verification

- [ ] Test SHA256 computation: `./skill_split.py verify ~/.claude/skills/agent-browser/SKILL.md`
- [ ] Verify byte-perfect round-trip
- [ ] Confirm hash consistency across multiple runs
- [ ] Run hashing tests: `pytest test/test_hashing.py -v`

### Database Storage

- [ ] Store sample file: `./skill_split.py store ~/.claude/skills/agent-browser/SKILL.md`
- [ ] Query stored file: `./skill_split.py get-section 1 --db ~/.claude/databases/skill-split.db`
- [ ] Verify section hierarchy: `./skill_split.py tree ~/.claude/skills/agent-browser/SKILL.md`
- [ ] Run database tests: `pytest test/test_database.py -v`

**Verified By**: ___________________  **Date**: _________

---

## Phase 3: Component Handlers Deployment

### Plugin Handler

- [ ] Test plugin.json parsing
- [ ] Verify .mcp.json detection
- [ ] Test hooks.json parsing
- [ ] Validate multi-file tracking
- [ ] Run plugin handler tests: `pytest test/test_handlers/test_plugin_handler.py -v`

### Hook Handler

- [ ] Test hooks.json parsing
- [ ] Verify shell script detection
- [ ] Test nested handler support
- [ ] Run hook handler tests: `pytest test/test_handlers/test_hook_handler.py -v`

### Config Handler

- [ ] Test settings.json parsing
- [ ] Test mcp_config.json parsing
- [ ] Verify schema validation
- [ ] Run config handler tests: `pytest test/test_handlers/test_config_handler.py -v`

### Script Handlers

- [ ] Test Python handler: `pytest test/test_handlers/test_script_handlers.py::TestPythonHandler -v`
- [ ] Test JavaScript handler: `pytest test/test_handlers/test_script_handlers.py::TestJavaScriptHandler -v`
- [ ] Test TypeScript handler: `pytest test/test_handlers/test_script_handlers.py::TestTypeScriptHandler -v`
- [ ] Test Shell handler: `pytest test/test_handlers/test_script_handlers.py::TestShellHandler -v`

**Verified By**: ___________________  **Date**: _________

---

## Phase 4: Supabase Integration Setup

### Environment Configuration

- [ ] Set `SUPABASE_URL` in `.env`
- [ ] Set `SUPABASE_KEY` in `.env`
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test connection: `python3 -c "from core.supabase_store import SupabaseStore; import os; store = SupabaseStore(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')); print('✓ Connected')"`
- [ ] Confirm no errors in output

### Schema Migration (if needed)

- [ ] Check if `config` and `script` types exist in `files_type` enum:
  ```sql
  SELECT enum_range(NULL::files_type);
  ```
- [ ] If missing, apply migration: `migrations/add_config_script_types.sql`
- [ ] Verify migration successful

### Test Data Upload

- [ ] Upload test file: `./skill_split.py ingest ~/.claude/skills/agent-browser/SKILL.md`
- [ ] Verify in Supabase dashboard: Check `files` and `sections` tables
- [ ] Confirm section count matches local parse
- [ ] Test retrieval: `./skill_split.py list-library --limit 5`
- [ ] Run Supabase tests: `pytest test/test_supabase_store.py -v` (requires env vars)

**Verified By**: ___________________  **Date**: _________

---

## Phase 5: Checkout & Deployment Workflow

### Basic Checkout

- [ ] Store a file to Supabase (see Phase 4)
- [ ] Get file ID: `./skill_split.py list-library | head -5`
- [ ] Checkout file: `./skill_split.py checkout <FILE_ID> /tmp/test-checkout/`
- [ ] Verify file exists at target path
- [ ] Compare with original: `diff /tmp/test-checkout/<filename> <original-path>`
- [ ] Expected: No output (identical files)

### Checkin Workflow

- [ ] Checkin deployed file: `./skill_split.py checkin <FILE_ID>`
- [ ] Verify status updated to `checkedin`
- [ ] Confirm local copy removed

### Status Tracking

- [ ] List active checkouts: `./skill_split.py status`
- [ ] Verify format shows: file_id, path, deployed_at
- [ ] Run checkout tests: `pytest test/test_checkout_manager.py -v`

**Verified By**: ___________________  **Date**: _________

---

## Phase 6: Query API Deployment

### Progressive Section Loading

- [ ] Get single section: `./skill_split.py get-section 1 --db ~/.claude/databases/skill-split.db`
- [ ] Get next section: `./skill_split.py next-section 1 --db ~/.claude/databases/skill-split.db`
- [ ] Verify parent-child relationships
- [ ] Test tree navigation: `./skill_split.py tree <file> --db ~/.claude/databases/skill-split.db`

### Search Functionality

- [ ] Single-file search: `./skill_split.py search "authentication" --file ~/.claude/skills/agent-browser/SKILL.md --db ~/.claude/databases/skill-split.db`
- [ ] Cross-file search: `./skill_split.py search "authentication" --db ~/.claude/databases/skill-split.db`
- [ ] Verify results include section IDs
- [ ] Run query tests: `pytest test/test_query.py -v`

**Verified By**: ___________________  **Date**: _________

---

## Phase 7: Vector Search Setup (Optional)

### pgvector Extension

- [ ] Create migration file and review: `migrations/enable_pgvector.sql`
- [ ] Execute in Supabase SQL Editor:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
- [ ] Verify: `SELECT extname FROM pg_extension WHERE extname = 'vector';`

### Embeddings Table

- [ ] Review migration: `migrations/create_embeddings_table.sql`
- [ ] Execute in Supabase SQL Editor
- [ ] Verify table created:
  ```sql
  SELECT table_name FROM information_schema.tables WHERE table_name = 'section_embeddings';
  ```

### Embedding Metadata

- [ ] Review migration: `migrations/add_embedding_metadata.sql`
- [ ] Execute in Supabase SQL Editor
- [ ] Verify table created

### OpenAI Configuration

- [ ] Set `OPENAI_API_KEY` in `.env`
- [ ] Set `ENABLE_EMBEDDINGS=true` (optional, for auto-embedding)
- [ ] Test connection:
  ```bash
  python3 -c "from core.embedding_service import EmbeddingService; service = EmbeddingService('$OPENAI_API_KEY'); print('✓ Ready')"
  ```

### Batch Embedding Generation

- [ ] Review script: `scripts/generate_embeddings.py`
- [ ] Run with caution (costs $0.08 for 19K sections):
  ```bash
  python3 scripts/generate_embeddings.py --dry-run  # Preview first
  python3 scripts/generate_embeddings.py              # Execute
  ```
- [ ] Monitor progress and costs
- [ ] Verify embeddings table populated

### Vector Search Testing

- [ ] Test semantic search: `./skill_split.py search-semantic "authentication patterns" --limit 5`
- [ ] Adjust vector weight: `./skill_split.py search-semantic "authentication" --vector-weight 0.8`
- [ ] Compare results with text search
- [ ] Run vector search tests: `pytest test/test_vector_search.py -v` (requires OPENAI_API_KEY)

**Verified By**: ___________________  **Date**: _________

---

## Phase 8: Monitoring & Observability

### Embedding Cost Monitoring

- [ ] Review monitoring script: `scripts/monitor_embeddings.py`
- [ ] Run monitoring: `python3 scripts/monitor_embeddings.py`
- [ ] Verify output includes:
  - [ ] Total sections with embeddings
  - [ ] Total tokens used
  - [ ] Estimated cost
  - [ ] Failed embeddings count
- [ ] Set up daily monitoring (cron job or scheduled task)

### Performance Metrics

- [ ] Measure search latency:
  ```bash
  time ./skill_split.py search "authentication"
  time ./skill_split.py search-semantic "authentication"
  ```
- [ ] Compare text vs. vector performance
- [ ] Document baseline metrics

### Error Tracking

- [ ] Set up error logging
- [ ] Monitor failed embeddings
- [ ] Configure alerts for cost overages
- [ ] Create incident response plan

**Verified By**: ___________________  **Date**: _________

---

## Phase 9: Full Integration Testing

### End-to-End Workflow

- [ ] Parse a complex 50+ section file
- [ ] Validate structure (no errors)
- [ ] Store to SQLite
- [ ] Retrieve and verify (byte-perfect)
- [ ] Upload to Supabase
- [ ] Checkout from Supabase
- [ ] Search semantically (if vector search enabled)
- [ ] Compose custom skill from sections
- [ ] Verify composed skill works

### Test Suite Execution

- [ ] Run full test suite: `pytest test/ -v --tb=short`
- [ ] Verify all tests passing
- [ ] Note any warnings
- [ ] Document any platform-specific issues

### Regression Testing

- [ ] Re-run all Phase 1-8 checks
- [ ] Verify no degradation in performance
- [ ] Confirm no new errors introduced

**Verified By**: ___________________  **Date**: _________

---

## Phase 10: Documentation Review

### User Guides

- [ ] Review `README.md` - comprehensive and current
- [ ] Review `EXAMPLES.md` - practical usage scenarios
- [ ] Review `COMPONENT_HANDLERS.md` - handler guide
- [ ] Review `COMPONENT_COMPOSITION.md` - composition guide (Phase 11)
- [ ] Review `VECTOR_SEARCH_GUIDE.md` - vector search guide (Phase 14)
- [ ] Review `docs/VECTOR_SEARCH_COSTS.md` - cost analysis

### Developer Guides

- [ ] Review `CLAUDE.md` - architecture and principles
- [ ] Review `CODEX.md` - initialization checklist
- [ ] Review `AGENT.md` - agent-wide rules
- [ ] Review migration guides in `migrations/` directory

### API Documentation

- [ ] Verify all CLI commands documented: `./skill_split.py --help`
- [ ] Verify all methods have docstrings
- [ ] Generate API docs (if applicable)

**Verified By**: ___________________  **Date**: _________

---

## Phase 11: Security & Performance

### Security Checklist

- [ ] `.env` file created and contains no secrets in git
- [ ] Database credentials rotated (if applicable)
- [ ] OpenAI API key is restricted (optional IP/domain)
- [ ] Supabase RLS policies reviewed
- [ ] No sensitive data in logs
- [ ] No debugging endpoints in production

### Performance Optimization

- [ ] Database indexes verified:
  ```sql
  SELECT * FROM pg_indexes WHERE tablename IN ('files', 'sections');
  ```
- [ ] Query performance benchmarked
- [ ] Caching strategy validated
- [ ] No N+1 queries identified

### Scalability Assessment

- [ ] Load test with 100+ concurrent queries (if applicable)
- [ ] Verify database handles 100K+ sections
- [ ] Test vector search with large result sets
- [ ] Document scaling limits

**Verified By**: ___________________  **Date**: _________

---

## Phase 12: Production Readiness

### Pre-Launch Verification

- [ ] All phases 1-11 complete and signed off
- [ ] No outstanding bugs or issues
- [ ] Documentation updated and reviewed
- [ ] Team trained on deployment and operation
- [ ] Runbook prepared (see below)
- [ ] Rollback plan documented

### Runbook

#### Starting the Service

```bash
# Verify database connection
./skill_split.py status

# Test a query
./skill_split.py search "test" --db ~/.claude/databases/skill-split.db

# Monitor costs (if vector search enabled)
python3 scripts/monitor_embeddings.py
```

#### Monitoring

- Check embedding metadata: `SELECT * FROM embedding_metadata LIMIT 1;`
- Monitor query latency: Review logs for slow queries
- Track cost trends: Run monitor script weekly

#### Troubleshooting

| Issue | Resolution |
|-------|-----------|
| Database locked | Check for hanging processes, restart if needed |
| Embeddings failed | Review error logs, retry with --retry flag |
| High latency | Check vector index status, reindex if necessary |
| Cost overages | Review recent searches, check for loops |

### Launch Sign-Off

- [ ] Project Manager Approval: ___________________
- [ ] Technical Lead Review: ___________________
- [ ] Security Review: ___________________
- [ ] Launch Date: ___________________

---

## Phase 13: Post-Launch (First 24 Hours)

### Immediate Monitoring

- [ ] Monitor for errors: Check logs every 30 minutes
- [ ] Verify searches working: Sample 5+ queries
- [ ] Check cost metrics: Should be < $0.01/hour
- [ ] Confirm no database corruption
- [ ] Review user feedback

### 24-Hour Validation

- [ ] All systems operational for 24 hours
- [ ] No unexpected errors or warnings
- [ ] Performance metrics within baseline
- [ ] Costs tracking as expected
- [ ] Users able to search and checkout files

### Sign-Off

- [ ] Production Deployment Successful: ✓
- [ ] Date: 2026-02-05
- **Next Phase**: Ongoing monitoring and optimization

---

## Appendix A: Database Schema

### Files Table
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    format TEXT NOT NULL,
    storage_path TEXT,
    content_hash TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Sections Table
```sql
CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    title TEXT,
    level INTEGER,
    start_line INTEGER,
    end_line INTEGER,
    content TEXT,
    content_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Appendix B: Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=https://dnqbnwalycyoynbcpbpz.supabase.co
SUPABASE_KEY=eyJhbGc...

# Vector Search (Optional)
ENABLE_EMBEDDINGS=false          # Set to true to auto-embed on store
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small

# Database
DATABASE_PATH=~/.claude/databases/skill-split.db

# Monitoring
COST_ALERT_THRESHOLD=0.50        # Alert if monthly cost exceeds
```

---

## Appendix C: Rollback Procedure

If deployment fails, follow these steps:

1. **Stop current operations**: `pkill -f skill_split`
2. **Restore database**: `cp ~/.claude/databases/skill-split.db.backup ~/.claude/databases/skill-split.db`
3. **Revert code**: `git checkout main` (if using git)
4. **Clear environment**: `unset ENABLE_EMBEDDINGS`
5. **Verify rollback**: Run Phase 1 checks
6. **Document incident**: Record what failed and why

---

**Document Version**: 1.0
**Last Reviewed**: 2026-02-05
**Next Review**: 2026-02-15

