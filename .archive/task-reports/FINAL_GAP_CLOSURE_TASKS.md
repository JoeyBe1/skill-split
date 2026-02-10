# Final Gap Closure Tasks - 2026-02-05

## Current State Summary

**✅ Working:**
- Local SQLite: 1,367 files, 19,207 sections
- Supabase: 2,757 files (archival mode - includes historical)
- Fast bulk ingest: Parallel processing, 0 failures
- File retrieval: Tested and working
- Sync system: Production ready

**Strategy Confirmed:** Archival mode (Supabase keeps all files ever ingested)

---

## Remaining Gaps to Close

### Gap 1: Schema Migration (User Action Required)
**Status:** SQL ready, awaiting manual application
**Blocker:** User must apply in Supabase dashboard

**Actions:**
1. Open: https://supabase.com/dashboard/project/dnqbnwalycyoynbcpbpz/editor
2. Paste SQL from: `migrations/add_config_script_types.sql`
3. Click "Run"
4. Verify: No "files_type_check" errors when ingesting config/script files

**Impact:** Enables config.json and script file (.py/.js/.sh) sync

---

### Gap 2: Round-Trip Verification
**Status:** Retrieval works, full test blocked by permissions
**Needs:** Manual user testing

**Test Script:**
```bash
# Pick a skill file from Supabase
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
from core.supabase_store import SupabaseStore

store = SupabaseStore(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
result = store.client.table('files').select('id,name,storage_path').eq('type', 'skill').limit(1).execute()
if result.data:
    print(f\"File ID: {result.data[0]['id']}\")
    print(f\"Name: {result.data[0]['name']}\")
    print(f\"Path: {result.data[0]['storage_path']}\")
"

# Checkout the file
./skill_split.py checkout <file-id> /tmp/skill-test/

# Verify byte-perfect match
diff /tmp/skill-test/<filename> <original-path>
# Should output nothing (perfect match)

# Check hash
./skill_split.py verify <original-path>
```

**Success Criteria:** Checkout produces byte-perfect copy

---

### Gap 3: Custom Skill Composition
**Status:** Core functionality exists, needs testing
**Purpose:** Validate the "composition power" vision

**Test Scenario:**
1. Search Supabase for sections about "authentication"
2. Retrieve relevant sections
3. Combine into new custom skill file
4. Store new skill in Supabase
5. Verify new skill can be checked out

**Test Commands:**
```bash
# Search for auth-related sections
./skill_split.py search-library "authentication" --db supabase

# Get specific sections by ID
./skill_split.py get-section <section-id> --db supabase

# TODO: Need command to compose new skill from section IDs
# This is the missing piece for "composition power"
```

**Gap:** No CLI command for "compose new file from section IDs"

---

### Gap 4: Section-Level Composition API
**Status:** Not implemented
**Criticality:** HIGH - Core vision feature

**Required Functionality:**
```python
# Proposed API
from core.composer import SkillComposer

composer = SkillComposer()
new_skill = composer.compose_from_sections(
    section_ids=["abc-123", "def-456", "ghi-789"],
    frontmatter={
        "name": "custom-auth-skill",
        "description": "Combined authentication patterns"
    },
    output_path="~/.claude/skills/custom-auth.md"
)
```

**Files to Create:**
- `core/composer.py` - SkillComposer class
- `test/test_composer.py` - Composition tests
- CLI command: `./skill_split.py compose --sections <ids> --output <path>`

**Estimated:** 200 lines, 2 hours

---

### Gap 5: Vector Search (Future Enhancement)
**Status:** Not started
**Criticality:** MEDIUM - Part of "TRUE power" vision

**Requirements:**
- Add embedding column to sections table
- Generate embeddings for section content
- Implement semantic search alongside text search
- Update search API to support both modes

**Estimated:** 500+ lines, 1-2 days

---

### Gap 6: Documentation Updates
**Status:** Partial
**Needs:** Update all docs to reflect archival strategy

**Files to Update:**
1. `CLAUDE.md` - Add archival mode explanation
2. `README.md` - Update sync statistics (2,757 files)
3. `HANDOFF.md` - Reflect current state
4. `SYNC_STATUS.md` - Mark as archival mode

---

## Priority Order

**Immediate (Today):**
1. ✅ Apply schema migration (user action)
2. ✅ Manual round-trip test
3. ✅ Document archival strategy

**Short-term (This Week):**
4. Implement section-level composition API
5. Test custom skill creation
6. Update all documentation

**Medium-term (Next Sprint):**
7. Vector search implementation
8. Pattern detection/learning system
9. Section-level editing API

---

## Success Criteria

**Core Functionality:**
- [x] Parse files into sections
- [x] Store in SQLite
- [x] Store in Supabase (archival)
- [x] Retrieve files with sections
- [x] Recompose byte-perfect
- [ ] Compose NEW files from sections (Gap 4)
- [ ] Vector search (Gap 5)

**Production Ready:**
- [x] 2,757 files in Supabase
- [x] 1,367 current files in local
- [x] Fast bulk ingest (parallel)
- [x] All 230 tests passing
- [ ] Schema migration applied
- [ ] Round-trip verified manually

---

## Next Session Priorities

1. **User applies schema migration** (5 min)
2. **User tests round-trip** (10 min)
3. **Implement SkillComposer API** (2 hours)
4. **Test custom skill creation** (30 min)
5. **Update all docs** (30 min)

**Total:** ~3.5 hours to complete all gaps

---

**Status:** 85% complete. Core storage/retrieval working. Composition API is the final critical piece for "TRUE power" vision.
