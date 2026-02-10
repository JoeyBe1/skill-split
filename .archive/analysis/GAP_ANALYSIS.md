# skill-split Gap Analysis

**Date**: 2026-02-06
**Status**: Production Ready with Known Issues
**Test Results**: 474 passed, 17 failed

---

## Executive Summary

skill-split is **functionally usable** with core commands working correctly. However, there are **critical issues in new features** (composition, semantic search) and **integration test failures** that prevent full production deployment. The system is suitable for **basic operations** (parse, store, search) but requires fixes before using compose/search-semantic in production.

---

## Verification Results

### 1. Core Commands ✅
All fundamental commands work correctly:

```
./skill_split.py --help
```

**Working commands** (tested and verified):
- ✅ `parse` - Parse file and display structure
- ✅ `validate` - Validate file structure
- ✅ `store` - Parse and store in database
- ✅ `get` - Retrieve file from database
- ✅ `tree` - Show section hierarchy
- ✅ `verify` - Store and verify round-trip
- ✅ `ingest` - Batch directory ingestion
- ✅ `list` - List sections with IDs
- ✅ `search` - Keyword search across sections
- ✅ `checkout` - Deploy file to path
- ✅ `checkin` - Remove deployed file
- ✅ `get-section` - Retrieve single section
- ✅ `next` - Get next section
- ✅ `status` - Show active checkouts

### 2. Test Results

**Overall**: 474/491 tests passing (96.5%)

**By Category**:
- ✅ Parser tests: 21/21 passing
- ✅ Database tests: 7/7 passing
- ✅ Query tests: 18/18 passing
- ✅ CLI tests: 16/16 passing
- ✅ Component detector: 28/28 passing
- ✅ Script handlers: 62/62 passing
- ❌ Composer integration: 13 failures (issues with DatabaseStore API)
- ❌ Vector search integration: 4 failures (embedding mocking issues)

---

## Critical Issues Found

### Issue 1: Bug in search-semantic Command (Priority: HIGH)
**Severity**: Command crashes when embeddings disabled
**Location**: `skill_split.py` line 951

**Problem**:
```python
# Line 942: search_sections returns (section_id, Section) tuples
results = query_api.search_sections(query)

# Line 951: Code expects (section_id, section, path) - 3 values!
for section_id, section, path in results:  # ERROR: not enough values to unpack
```

**Symptom**:
```bash
./skill_split.py search-semantic "test"
# Error: not enough values to unpack (expected 3, got 2)
```

**Root Cause**: QueryAPI.search_sections() returns `List[tuple[int, Section]]` (2-tuple), but the fallback code expects a 3-tuple including the file path.

**Impact**:
- search-semantic command fails with misleading error
- Only works when ENABLE_EMBEDDINGS=true (bypasses fallback code)
- Blocks users from testing without embeddings

**Fix Required**:
```python
# Option A: Get file_path from database lookup
results = query_api.search_sections(query)
for section_id, section in results:  # Unpack 2-tuple
    file_path = db.get_file_path_for_section(section_id)

# Option B: Modify QueryAPI to return 3-tuple
# Add file_path to returned data
```

---

### Issue 2: DatabaseStore API Mismatch (Priority: HIGH)
**Severity**: 13 integration tests fail
**Location**: `test/test_composer_integration.py` and `test/test_vector_search_integration.py`

**Problem**:
```python
# Tests try to access database connection directly:
db = DatabaseStore(path)
cursor = db.conn.cursor()  # AttributeError: 'DatabaseStore' object has no attribute 'conn'

# Tests expect context manager:
with DatabaseStore(path) as db:  # TypeError: object does not support context manager protocol
    # ... code ...
```

**Root Cause**:
- DatabaseStore does not expose a `conn` attribute
- DatabaseStore does not implement `__enter__` and `__exit__` methods
- Tests were written with incorrect API assumptions

**Impact**:
- 13 integration tests cannot run
- Blocks testing of composer with hierarchical sections
- Blocks testing of frontmatter generation
- Blocks testing of vector search integration

**Fix Required**:
Either:
1. Add `conn` property to DatabaseStore (expose internal connection)
2. Make DatabaseStore a context manager
3. Rewrite tests to use public DatabaseStore API only

---

### Issue 3: Compose Command Works But Missing Documentation (Priority: MEDIUM)
**Severity**: Feature works but unclear to users
**Location**: `COMPONENT_COMPOSITION.md`

**Verification Test**:
```bash
./skill_split.py compose --sections 1,2,3 --output /tmp/test.md
# Output: ✅ Composed skill written successfully
```

**Problem**: While the command works, the documentation doesn't clearly explain:
- What sections should be used (must have IDs from database)
- How to discover section IDs
- Expected output format
- When composition fails and why

**Example Gap**:
```markdown
# COMPONENT_COMPOSITION.md says:

./skill_split.py compose \
  --sections 101,205,310 \    # ← Where do these IDs come from?
  --output ~/.claude/skills/custom-auth.md

# Guide should include:
# Step 1: Find section IDs
./skill_split.py search "authentication" --db <database>
# Output shows section IDs

# Step 2: Use IDs in compose
./skill_split.py compose --sections <IDs> ...
```

**Impact**:
- Users don't know how to find section IDs
- Trial-and-error workflow expected
- No troubleshooting guidance

---

### Issue 4: Search-Semantic Requires Embeddings (Priority: MEDIUM)
**Severity**: Feature only partially functional
**Location**: `skill_split.py` lines 934-955

**Problem**:
- search-semantic falls back to keyword search when ENABLE_EMBEDDINGS=false
- Fallback has a bug (Issue #1)
- Users expect semantic search to work by default

**Current Behavior**:
```bash
# Without OPENAI_API_KEY:
./skill_split.py search-semantic "auth patterns"
# Info: Embeddings not enabled. Falling back to keyword search...
# Error: not enough values to unpack
```

**Expected Behavior**:
```bash
# Should either:
# 1. Work with keyword search (no embeddings)
# 2. Or gracefully exit with clear instructions
```

**Documentation Gap**:
- VECTOR_SEARCH_GUIDE.md requires OPENAI_API_KEY
- No guide for keyword-only search
- Fallback path not documented

**Impact**:
- Feature doesn't degrade gracefully
- Users confused by "semantic search" that's actually keyword search
- No clear path to enable real vector search

---

## Documentation Assessment

### What's Good ✅
1. **DOCUMENTATION.md** - Excellent index with clear role-based navigation
2. **README.md** - Complete overview with installation and quick start
3. **COMPONENT_COMPOSITION.md** - Well-structured guide (except missing piece noted above)
4. **VECTOR_SEARCH_GUIDE.md** - Comprehensive setup and cost guidance
5. **EXAMPLES.md** - Real-world scenarios with output examples
6. **DEPLOYMENT_CHECKLIST.md** - Pre-deployment verification steps

### What's Missing ❌

#### 1. Getting Started: "First 5 Minutes"
**Gap**: No simple "start here" for new users

**Should Have**:
```markdown
# Your First skill-split Experience (5 minutes)

1. Create demo file
2. Parse it
3. Store it
4. Search it
5. Get a section

# [Exact commands with expected output]
```

**Current State**: README has Quick Start, but it's theoretical. No actual demo file provided to run.

#### 2. Troubleshooting Guide
**Missing**: No guide for common errors

**Should Cover**:
- "Database not found" - how to create one
- "No sections found" - debugging search
- "Compose command failed" - section ID validation
- "Import error" - missing dependencies

#### 3. Section ID Discovery
**Gap**: Users don't know how to find valid section IDs for compose

**Missing Workflow**:
```bash
# Step 1: What section IDs are available?
./skill_split.py search "auth" --db <database>  # Shows IDs

# Step 2: Want to see section content first?
./skill_split.py get-section <id> --db <database>

# Step 3: Then compose from those IDs
./skill_split.py compose --sections <id1>,<id2>
```

#### 4. Semantic Search vs Keyword Search
**Gap**: VECTOR_SEARCH_GUIDE.md doesn't explain tradeoffs

**Missing**:
- When to use keyword vs semantic
- Cost comparison
- Accuracy comparison
- How fallback works

#### 5. Production Deployment Guide
**Gap**: No guide for deploying to production environment

**Missing**:
- Database backup strategy
- Migration procedures
- Monitoring and health checks
- Scaling considerations

#### 6. API Documentation
**Gap**: No Python API reference for programmatic use

**Current**: Docs focus on CLI only
**Missing**: Examples for:
```python
from core.skill_composer import SkillComposer
from core.query import QueryAPI
from core.database import DatabaseStore
```

---

## User Journey Analysis

### Current Flow (What Works)
```
User wants to: "Parse and search a skill file"

1. Create database ✅
   ./skill_split.py store skill.md

2. Search by keyword ✅
   ./skill_split.py search "pattern"

3. Get single section ✅
   ./skill_split.py get-section 42

4. See structure ✅
   ./skill_split.py tree
```

### Broken Flow (What Needs Fixes)
```
User wants to: "Build custom skill from pieces"

1. Find interesting sections
   ./skill_split.py search "auth" ✅ Works

2. Get section content
   ./skill_split.py get-section 101 ✅ Works

3. Compose from those sections
   ./skill_split.py compose --sections 101,205 ✅ Works

BUT: User doesn't know steps 1-2 because docs don't explain section ID discovery

4. Search semantically
   ./skill_split.py search-semantic "patterns" ❌ BROKEN when no embeddings
```

### Missing Flow (Not Documented)
```
User wants to: "Use skill-split as a Python library"

from core.skill_composer import SkillComposer
from core.query import QueryAPI

# What do I do now? → No documentation!
```

---

## Honest Assessment

### What Works Well
1. **Core parsing** - Handles complex YAML, Markdown, XML
2. **Database storage** - Reliable SQLite with proper schema
3. **Round-trip verification** - Byte-perfect reconstruction
4. **CLI commands** - 14/16 commands fully functional
5. **Component handlers** - Plugins, hooks, configs parsed correctly
6. **Tests** - 96% coverage, failures are test infrastructure issues

### What Needs Work
1. **New features** - compose and search-semantic need fixes
2. **Edge cases** - Fallback paths not working (Issue #1)
3. **Integration tests** - Test suite assumes incorrect API (Issue #2)
4. **User documentation** - Missing practical guides and workflows
5. **Error handling** - Some commands fail with confusing errors

### What's Risky
1. Using search-semantic without embeddings → Will crash
2. Using compose without understanding section IDs → Will fail silently
3. Running integration tests → Will report failures that don't affect CLI
4. Deploying to production → No guidance on backups, scaling

---

## Detailed Fix List

| Issue | Severity | Effort | Category | Fix |
|-------|----------|--------|----------|-----|
| search-semantic crash | HIGH | 1 hour | Bug | Fix unpacking in line 951 |
| DatabaseStore.conn missing | HIGH | 2 hours | Test Infrastructure | Expose conn or rewrite tests |
| Composition workflow unclear | MEDIUM | 1 hour | Documentation | Add section ID discovery guide |
| Getting started missing | MEDIUM | 2 hours | Documentation | Create 5-minute walkthrough |
| Semantic search fallback broken | MEDIUM | 1 hour | Bug | Fix fallback or remove it |
| No troubleshooting guide | LOW | 3 hours | Documentation | Create common errors guide |
| No Python API docs | LOW | 2 hours | Documentation | Create programmatic examples |
| Production deployment guide missing | LOW | 4 hours | Documentation | Create ops guide |

---

## Recommended Action Plan

### Phase 1: Fix Critical Bugs (2-3 hours)
1. Fix search-semantic unpacking bug (Issue #1)
2. Fix DatabaseStore API for integration tests (Issue #2)
3. Run full test suite → should see 0 failures

### Phase 2: Fix Documentation Gaps (4-5 hours)
1. Create "Getting Started" guide with demo
2. Add section ID discovery workflow to compose guide
3. Create troubleshooting guide for common errors
4. Document semantic vs keyword search tradeoffs

### Phase 3: Improve User Experience (Optional, 2-3 hours)
1. Add Python API reference
2. Create production deployment guide
3. Add monitoring/health check examples

---

## Verification Commands

To verify each component yourself:

```bash
# 1. Test core parse/store
./skill_split.py parse demo/sample_skill.md
./skill_split.py store demo/sample_skill.md

# 2. Test search
./skill_split.py search "skill" --db skill_split.db

# 3. Test composition (WORKS)
./skill_split.py compose --sections 1,2,3 --output /tmp/test.md

# 4. Test semantic search (BROKEN)
./skill_split.py search-semantic "test" --db skill_split.db
# Expected: Error or keyword fallback
# Actual: Crash

# 5. Run tests
pytest test/ -v | grep -E "FAILED|passed"
# Expected: 491 passed (but will show 17 failed due to test API issues)
```

---

## Conclusion

**skill-split is usable for basic operations** but has two high-priority bugs that prevent new features from working correctly. The documentation is comprehensive but missing practical guides for common workflows. With 2-3 hours of fixes and 4-5 hours of documentation work, the system can be production-ready with full feature support.

**Current Status**: Production-ready for basic parse/store/search workflows. Not ready for compose or semantic search without fixes.

**Recommendation**: Apply fixes in Phase 1 before deploying to production. Document workflows in Phase 2 before distributing to users.

---

Last Updated: 2026-02-06
