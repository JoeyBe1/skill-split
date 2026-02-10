# Phase 10 Gap Closure Plan

**Based on**: PHASE_10_GAP_ANALYSIS.md
**Goal**: Complete Phase 10 with full CLI integration

---

## Plan Overview

Close the critical gaps to make script handlers actually usable from the CLI.

---

## Tasks (Priority Order)

### Task 1: CLI Integration - Parse/Validate Commands (CRITICAL)

**File**: `skill_split.py`

**Changes needed**:
1. Import HandlerFactory
2. In `cmd_parse()`, detect script files and use HandlerFactory
3. Fall back to existing Parser for non-script files
4. Test: `./skill_split.py parse handlers/python_handler.py`

**Acceptance**:
- Can parse Python files and see class/function structure
- Can parse JS/TS files and see class/interface structure
- Can parse Shell files and see function structure
- Existing markdown parsing still works

---

### Task 2: CLI Integration - Store/Verify Commands (CRITICAL)

**File**: `skill_split.py`

**Changes needed**:
1. In `cmd_store()`, use HandlerFactory for script files
2. In `cmd_verify()`, use HandlerFactory for script files
3. Ensure round-trip works for stored scripts

**Acceptance**:
- Can store script files in database
- Can retrieve script files from database
- Verify command passes for script files

---

### Task 3: Fix Round-Trip Recomposition (HIGH)

**File**: `handlers/script_handler.py`

**Changes needed**:
1. Debug `recompose()` method
2. Ensure sections are joined properly with correct newlines
3. Preserve original formatting exactly

**Acceptance**:
- Demo round-trip test passes
- All existing round-trip tests still pass
- No data loss in recomposition

---

### Task 4: LSP Integration or Honest Removal (MEDIUM)

**Option A**: Implement actual LSP
- Use Serena's `find_symbol` tool
- Requires LSP server configuration

**Option B** (RECOMMENDED): Remove LSP stub
- Delete `_get_symbols_via_lsp()` method
- Update docstrings to say "regex-based parsing"
- Be honest about the implementation

**Acceptance**:
- No confusing LSP stub code
- Clear documentation of parsing approach

---

### Task 5: Update Documentation (LOW)

**Files**: `EXAMPLES.md`, `README.md`

**Changes needed**:
1. Add script file examples to EXAMPLES.md
2. Update README.md with script handler usage
3. Document supported file types

**Acceptance**:
- User can learn how to use script handlers from docs
- Examples are copy-pasteable

---

## Execution Order

1. Task 1 (CLI Parse) → Task 2 (CLI Store) → Task 3 (Round-trip) → Task 4 (LSP) → Task 5 (Docs)

**Sequential dependency**: Each task enables the next.

---

## Testing Checklist

After each task, run:
- `python -m pytest test/` (all 205 tests must pass)
- `./skill_split.py parse <test_file>` (manual verification)
- `./skill_split.py store <test_file>` (database verification)
- `./skill_split.py verify <test_file>` (round-trip verification)

---

## Rollback Plan

If any task breaks existing functionality:
1. Git revert the changes
2. Fix the issue
3. Re-apply the changes

---

**Success Criteria**: User can run `./skill_split.py parse script.py` and see proper class/function structure.
