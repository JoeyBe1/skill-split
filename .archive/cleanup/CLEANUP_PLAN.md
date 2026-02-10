# Documentation Cleanup Plan

**Date**: 2026-02-06
**Status**: Ready for Review
**Total Documentation Files**: 62 MD files
**Keep**: 18 files (29%)
**Archive**: 44 files (71%)

---

## Overview

The skill-split project has accumulated 62 markdown files across 6 waves and 14 phases of development. Most are development artifacts (phase plans, completion reports, test reports) valuable for historical context but not needed for user-facing documentation.

This plan categorizes all files and proposes a clean, minimal set of user-facing docs while preserving development history in an `.archive/` directory.

---

## KEEP: Core User Documentation (8 files)

**Purpose**: Essential for users to understand and use skill-split

### Primary Docs
1. **README.md** - Main entry point, feature overview, installation
2. **CLAUDE.md** - Project rules, state, architecture, production readiness status
3. **CODEX.md** - Init checklist and guardrails
4. **AGENT.md** - Agent-wide rules for Claude interaction
5. **EXAMPLES.md** - Usage scenarios with real output examples
6. **DEPLOYMENT_STATUS.md** - Current deployment capabilities and database locations

### Getting Started
7. **DEPLOYMENT_CHECKLIST.md** - Pre-deployment verification steps

---

## KEEP: Feature Documentation (6 files)

**Purpose**: Feature-specific guides and integration docs

1. **COMPONENT_COMPOSITION.md** - Guide to composing components from stored sections
2. **COMPONENT_HANDLERS.md** - Component handler architecture and types
3. **HANDLER_INTEGRATION.md** - Integrating handlers into existing workflows
4. **VECTOR_SEARCH_GUIDE.md** - Vector search setup and usage
5. **SUPABASE_SETUP.md** - Supabase integration instructions
6. **INGESTION_GUIDE.md** - How to ingest files into the database

---

## KEEP: Technical References (4 files)

**Purpose**: Implementation details and testing procedures

1. **migrations/SCHEMA_MIGRATION_GUIDE.md** - Database schema changes (critical for upgrades)
2. **test/MANUAL_ROUNDTRIP_TEST.md** - Manual testing procedures
3. **docs/VECTOR_SEARCH_COSTS.md** - Vector search cost analysis
4. **demo/sample_skill.md** - Example skill file for testing

---

## ARCHIVE: Wave Reports (8 files)

**Category**: Development completion reports from implementation waves

These track progress across waves but are historical artifacts.

```
.archive/wave-reports/
├── WAVE_3_CODE_REFERENCE.md
├── WAVE_3_COMPLETION_REPORT.md
├── WAVE_4_COMPLETION.md
├── WAVE_5_COMPLETION.md
├── WAVE_6_COMPLETION_REPORT.md
├── WAVE_6_IMPLEMENTATION_CHECKLIST.md
├── WAVE_8_COMPLETION_REPORT.md
└── WAVE_8_SUMMARY.md
```

**Reasoning**: Historical record of implementation progress. Useful for understanding design evolution but not needed for users.

---

## ARCHIVE: Phase Planning Documents (9 files)

**Category**: Phase-by-phase planning and delivery docs (Phases 10, 11, 14)

These outline approach for each phase but are superseded by actual implementation.

```
.archive/phase-plans/
├── PHASE_10_CLOSURE_PLAN.md
├── PHASE_10_GAP_ANALYSIS.md
├── PHASE_11_DELIVERY.md
├── PHASE_11_FOUNDATION.md
├── PHASE_11_INDEX.md
├── PHASE_11_OVERVIEW.md
├── PHASE_11_QUICK_START.md
├── PHASE_14_DELIVERY.md
└── PHASE_14_IMPLEMENTATION_READY.md
```

**Reasoning**: Planning documents for previous development phases. Kept for historical reference but implementation is complete.

---

## ARCHIVE: Task Management Documents (5 files)

**Category**: Task lists and execution summaries

```
.archive/task-reports/
├── HAIKU_EXECUTION_TASKLIST.md
├── FINAL_GAP_CLOSURE_TASKS.md
├── TASK-011-COMPLETION.md
├── TASK-011-TEST-REPORT.md
└── TEST_EXECUTION_SUMMARY.md
```

**Reasoning**: Execution tracking documents. Historical value for understanding development process but not user-facing.

---

## ARCHIVE: Roundtrip Testing Documents (6 files)

**Category**: Roundtrip verification and testing guides

```
.archive/testing-docs/
├── ROUNDTRIP_DELIVERY.md
├── ROUNDTRIP_QUICK_REFERENCE.md
├── ROUNDTRIP_TESTING_SUMMARY.md
├── ROUNDTRIP_VERIFICATION_REPORT.md
├── START_HERE_ROUNDTRIP.md
└── TEST_ROUNDTRIP_README.md
```

**Reasoning**: Testing procedures and verification reports. Specific to development verification, not production user workflows.

---

## ARCHIVE: Test Reports (4 files)

**Category**: Development test result summaries

```
.archive/test-reports/
├── COMPREHENSIVE_TEST_REPORT.md
├── REAL_COMPONENT_TEST_REPORT.md
├── REAL_FILE_TEST_REPORT.md
└── SKILL_COMPOSITION_TEST_REPORT.md
```

**Reasoning**: QA and test execution reports. Valuable for QA history but not needed for production usage.

---

## ARCHIVE: Investigation Documents (8 files)

**Category**: Investigation and troubleshooting reports from development

```
.archive/investigations/
├── DB_COUNT_INVESTIGATION.md
├── FOLDER_RECREATION_INVESTIGATION.md
├── SYNC_STATUS.md
├── SYNC_VERIFICATION.md
├── ARCHITECTURE_COMPARISON.md
├── COMPOSITION_INDEX.md
├── COMPOSITION_CAPABILITY_SUMMARY.md
└── HANDLER_FIXES_2026_02_04.md
```

**Reasoning**: Technical investigations and status checks during development. Useful for understanding past issues but implementation is complete.

---

## ARCHIVE: Strategy & Summary Documents (4 files)

**Category**: Implementation status and workflow documentation

```
.archive/strategy-docs/
├── IMPLEMENTATION_COMPLETE.md
├── PRODUCTION_TEST_PLAN.md
├── SESSION_SUMMARY.md
└── HANDOFF.md
```

**Reasoning**: High-level strategy and handoff documents. Captured in CLAUDE.md and README.md for users.

---

## ARCHIVE: Guides & References (5 files)

**Category**: User/developer guides for specific workflows

```
.archive/user-guides/
├── JOEY_GUIDE.md (personal guide)
├── LIBRARIAN_WORKFLOW.md (librarian-specific)
├── RALPH_USAGE.md (tool-specific)
├── IDEAS.md (feature brainstorm)
└── ARCHITECTURE.md (detailed architecture)
```

**Reasoning**: Specific to particular users/tools. Architecture details are in README.md and CLAUDE.md. Feature ideas captured elsewhere.

---

## Directory Structure After Cleanup

```
skill-split/
├── README.md                          # Entry point
├── CLAUDE.md                          # Project state & rules
├── CODEX.md                           # Init checklist
├── AGENT.md                           # Agent rules
├── EXAMPLES.md                        # Usage examples
├── DEPLOYMENT_STATUS.md               # Current deployment status
├── DEPLOYMENT_CHECKLIST.md            # Pre-deployment checklist
│
├── COMPONENT_COMPOSITION.md           # Feature guides
├── COMPONENT_HANDLERS.md
├── HANDLER_INTEGRATION.md
├── VECTOR_SEARCH_GUIDE.md
├── SUPABASE_SETUP.md
├── INGESTION_GUIDE.md
│
├── .archive/                          # Development history
│   ├── wave-reports/                  # 8 files
│   ├── phase-plans/                   # 9 files
│   ├── task-reports/                  # 5 files
│   ├── testing-docs/                  # 6 files
│   ├── test-reports/                  # 4 files
│   ├── investigations/                # 8 files
│   ├── strategy-docs/                 # 4 files
│   └── user-guides/                   # 5 files
│
├── migrations/
│   ├── SCHEMA_MIGRATION_GUIDE.md      # Keep here
│   └── *.sql
│
├── test/
│   ├── MANUAL_ROUNDTRIP_TEST.md       # Keep here
│   └── test_*.py
│
├── docs/
│   ├── VECTOR_SEARCH_COSTS.md         # Keep here
│   └── plans/
│
├── demo/
│   ├── sample_skill.md                # Keep here
│   └── progressive_disclosure.sh
│
└── [source code files]
```

---

## Implementation Steps

### Phase 1: Create Archive Structure

```bash
# Create archive directories
mkdir -p /Users/joey/working/skill-split/.archive/{wave-reports,phase-plans,task-reports,testing-docs,test-reports,investigations,strategy-docs,user-guides}
```

### Phase 2: Move Archive Files

**Wave Reports** (8 files)
```bash
mv WAVE_*.md .archive/wave-reports/
```

**Phase Plans** (9 files)
```bash
mv PHASE_*.md .archive/phase-plans/
```

**Task Reports** (5 files)
```bash
mv HAIKU_EXECUTION_TASKLIST.md .archive/task-reports/
mv FINAL_GAP_CLOSURE_TASKS.md .archive/task-reports/
mv TASK-011-*.md .archive/task-reports/
mv TEST_EXECUTION_SUMMARY.md .archive/task-reports/
```

**Roundtrip Testing** (6 files)
```bash
mv ROUNDTRIP_*.md .archive/testing-docs/
mv START_HERE_ROUNDTRIP.md .archive/testing-docs/
mv TEST_ROUNDTRIP_README.md .archive/testing-docs/
```

**Test Reports** (4 files)
```bash
mv COMPREHENSIVE_TEST_REPORT.md .archive/test-reports/
mv REAL_COMPONENT_TEST_REPORT.md .archive/test-reports/
mv REAL_FILE_TEST_REPORT.md .archive/test-reports/
mv SKILL_COMPOSITION_TEST_REPORT.md .archive/test-reports/
```

**Investigations** (8 files)
```bash
mv DB_COUNT_INVESTIGATION.md .archive/investigations/
mv FOLDER_RECREATION_INVESTIGATION.md .archive/investigations/
mv SYNC_*.md .archive/investigations/
mv ARCHITECTURE_COMPARISON.md .archive/investigations/
mv COMPOSITION_*.md .archive/investigations/
mv HANDLER_FIXES_2026_02_04.md .archive/investigations/
```

**Strategy** (4 files)
```bash
mv IMPLEMENTATION_COMPLETE.md .archive/strategy-docs/
mv PRODUCTION_TEST_PLAN.md .archive/strategy-docs/
mv SESSION_SUMMARY.md .archive/strategy-docs/
mv HANDOFF.md .archive/strategy-docs/
```

**Guides** (5 files)
```bash
mv JOEY_GUIDE.md .archive/user-guides/
mv LIBRARIAN_WORKFLOW.md .archive/user-guides/
mv RALPH_USAGE.md .archive/user-guides/
mv IDEAS.md .archive/user-guides/
mv ARCHITECTURE.md .archive/user-guides/
```

### Phase 3: Create Archive Index

Create `.archive/README.md`:

```markdown
# Development Archive

Historical documentation from skill-split development (Waves 1-8, Phases 10-14).

## Contents

- **wave-reports/** - Completion reports from implementation waves
- **phase-plans/** - Phase planning and delivery documents
- **task-reports/** - Task execution and tracking documents
- **testing-docs/** - Testing procedures and roundtrip verification
- **test-reports/** - Test execution results and summaries
- **investigations/** - Technical investigations and troubleshooting
- **strategy-docs/** - High-level strategy and handoff documentation
- **user-guides/** - User and developer workflow guides

## Note

These files are preserved for historical reference and understanding the development process.
For production usage, refer to the main documentation in the project root.
```

### Phase 4: Create Documentation Index in Root

Create `DOCUMENTATION.md` as quick reference:

```markdown
# Documentation Index

## Quick Start
- [README.md](README.md) - Overview and installation
- [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) - Current system status

## User Guides
- [EXAMPLES.md](EXAMPLES.md) - Usage scenarios and examples
- [COMPONENT_COMPOSITION.md](COMPONENT_COMPOSITION.md) - Creating custom compositions
- [SUPABASE_SETUP.md](SUPABASE_SETUP.md) - Cloud integration
- [VECTOR_SEARCH_GUIDE.md](VECTOR_SEARCH_GUIDE.md) - Vector search setup

## Developer Documentation
- [CLAUDE.md](CLAUDE.md) - Project state and architecture
- [COMPONENT_HANDLERS.md](COMPONENT_HANDLERS.md) - Handler implementation
- [HANDLER_INTEGRATION.md](HANDLER_INTEGRATION.md) - Integration patterns

## Operations
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Pre-deployment verification
- [migrations/SCHEMA_MIGRATION_GUIDE.md](migrations/SCHEMA_MIGRATION_GUIDE.md) - Database migrations
- [INGESTION_GUIDE.md](INGESTION_GUIDE.md) - Batch ingestion procedures

## Testing
- [test/MANUAL_ROUNDTRIP_TEST.md](test/MANUAL_ROUNDTRIP_TEST.md) - Manual testing procedures

## Archive
- [.archive/](/.archive/) - Historical development documentation (Phases 1-14)

## Internal Rules
- [CODEX.md](CODEX.md) - Init checklist and guardrails
- [AGENT.md](AGENT.md) - Agent rules for Claude interaction
```

---

## Gap Analysis: Core Docs Evaluation

### Strengths
- ✅ README.md covers feature overview well
- ✅ EXAMPLES.md has concrete usage scenarios
- ✅ COMPONENT_HANDLERS.md explains architecture
- ✅ DEPLOYMENT_STATUS.md tracks production readiness

### Identified Gaps

1. **Quick Start / Getting Started** ⚠️
   - README.md has basics but could use faster path
   - Recommend: Add `## Quick Start` section to README with top 3 commands

2. **Troubleshooting Guide** ❌
   - Missing: Common issues and solutions
   - Recommend: Create `TROUBLESHOOTING.md` if issues emerge in production

3. **API Reference** ⚠️
   - EXAMPLES.md covers basic usage
   - Missing: Formal API docs for QueryAPI and SupabaseStore
   - Recommend: Extract API reference from code docstrings if needed

4. **Architecture Diagram** ❌
   - CLAUDE.md mentions phases but lacks visual overview
   - Recommend: Add simple ASCII diagram to CLAUDE.md

5. **Migration Path** ⚠️
   - SCHEMA_MIGRATION_GUIDE.md is good
   - Missing: How to migrate existing deployments
   - Recommend: Add section to DEPLOYMENT_CHECKLIST.md

### Recommended New Docs (Optional)

Only create if patterns emerge:
- `TROUBLESHOOTING.md` - Common issues
- `ARCHITECTURE_DIAGRAM.md` - Visual overview
- `MIGRATION_GUIDE.md` - Upgrade path

---

## File Statistics

| Category | Count | Size | Purpose |
|----------|-------|------|---------|
| Keep (user-facing) | 18 | ~150KB | Production docs |
| Archive (development) | 44 | ~200KB | Development history |
| **Total** | **62** | **~350KB** | |

---

## Checklist for Implementation

- [ ] Create `.archive/` directory structure
- [ ] Move 44 archived files to appropriate subdirectories
- [ ] Create `.archive/README.md` index
- [ ] Create `DOCUMENTATION.md` in root
- [ ] Verify all 18 kept docs are accessible from root
- [ ] Update CLAUDE.md "Files Created" section to reflect cleanup
- [ ] Test all links in DOCUMENTATION.md
- [ ] Commit cleanup with message: "refactor(docs): archive development history"

---

## Notes for Joey

1. **Kept docs are intentional**: Each of the 18 kept docs serves a specific purpose for production users or developers
2. **Archive is comprehensive**: All 44 archived files are preserved; can be restored if needed
3. **Easy to reverse**: If any archived doc is needed, can be moved back to root
4. **Future docs**: Any new documentation should go to root; archive should only contain historical artifacts
5. **Size savings**: Moving to archive reduces clutter but not filesystem size

---

**Created**: 2026-02-06
**Status**: Ready for review and approval
