# Production Test Plan: 15 Random File Verification

**Date:** 2026-02-04
**Purpose:** Verify all handlers work on random real-world files
**Executor:** Qwen (supervised by Haiku agent)

---

## Test Objectives

1. **Random sampling** - Find 15 files randomly from ~/.claude directory
2. **Full workflow** - Test store → verify → list → search on each file
3. **All file types** - Cover skills, commands, hooks, plugins, configs, scripts
4. **Atomic results** - Clear PASS/FAIL per file with evidence
5. **System health** - Verify databases (SQLite + Supabase) working

---

## Test Workflow (8 Steps Per File)

For each of 15 randomly selected files:

### Step 1: File Selection
```bash
# Find file and identify type
file_path="<random_file>"
file_type="<skill|command|hook|plugin|config|script>"
```

**Expected Output:** File path + detected type

---

### Step 2: Store in Database
```bash
./skill_split.py store "$file_path" --db test_production.db
```

**Expected Output:**
- "Stored file: <path>"
- "File ID: <number>"
- "Sections: <count>"

**Pass Criteria:** No errors, file ID returned

---

### Step 3: Verify Byte-Perfect Round-Trip
```bash
./skill_split.py verify "$file_path" --db test_production.db
```

**Expected Output:**
```
File: <path>
Valid ✓
original_hash:    <sha256>
recomposed_hash:  <sha256>
```

**Pass Criteria:**
- "Valid ✓" appears
- Both hashes EXACTLY match
- Exit code 0

---

### Step 4: List Sections
```bash
./skill_split.py list "$file_path" --db test_production.db
```

**Expected Output:**
```
File: <path>

 [1] Section Title
  [2] Child Section
  [3] Another Child
```

**Pass Criteria:**
- All sections have numeric IDs [N]
- No [?] placeholders
- Section count matches Step 2

---

### Step 5: Get Section Tree
```bash
./skill_split.py tree "$file_path" --db test_production.db
```

**Expected Output:**
```
<path>
├── [1] Section Title
│   ├── [2] Child Section
│   └── [3] Another Child
```

**Pass Criteria:**
- Tree structure displays
- All IDs present
- Hierarchy correct

---

### Step 6: Search Within File
```bash
./skill_split.py search "<keyword>" --file "$file_path" --db test_production.db
```

**Expected Output:**
```
Found N section(s) matching '<keyword>':

ID     Title                    Level
--------------------------------------
[N]    <section_title>         <level>
```

**Pass Criteria:**
- Search returns results OR "Found 0 sections" (both valid)
- No errors

---

### Step 7: Get Individual Section
```bash
# Get first section ID from Step 4
section_id="<first_id>"
./skill_split.py get-section "$section_id" --db test_production.db
```

**Expected Output:**
```
Section ID: <id>
Title: <title>
Level: <level>
Parent: <parent_id or None>
Line Range: <start>-<end>

Content:
<section_content>
```

**Pass Criteria:**
- Section content returned
- Metadata correct
- No errors

---

### Step 8: Calculate Result
```
IF all steps 2-7 pass THEN
    result = "PASS ✓"
ELSE
    result = "FAIL ✗"
    failed_step = "<step_number>"
    error_message = "<actual_error>"
END
```

---

## File Selection Strategy

Find 15 random files covering all types:

```bash
# Skills (3 files)
find ~/.claude/skills -name "*.md" -type f | shuf -n 3

# Commands (2 files)
find ~/.claude/commands -name "*.md" -type f | shuf -n 2

# Hooks (2 files)
find ~/.claude/plugins -name "hooks.json" -type f | shuf -n 2

# Plugins (2 files)
find ~/.claude/plugins -name "plugin.json" -type f | shuf -n 2

# Configs (2 files)
find ~/.claude -maxdepth 1 -name "*.json" -type f | shuf -n 2

# Scripts (4 files - 1 of each type)
find ~/.claude -name "*.py" -type f | shuf -n 1
find ~/.claude -name "*.js" -type f | shuf -n 1
find ~/.claude -name "*.ts" -type f | shuf -n 1
find ~/.claude -name "*.sh" -type f | shuf -n 1
```

---

## Result Format (Per File)

```
═══════════════════════════════════════════════════════
FILE #N: <filename>
═══════════════════════════════════════════════════════
Type:           <type>
Path:           <full_path>
Size:           <bytes>

STEP 2 - Store:         PASS ✓ / FAIL ✗
  File ID:              <id>
  Sections:             <count>

STEP 3 - Verify:        PASS ✓ / FAIL ✗
  Original Hash:        <hash>
  Recomposed Hash:      <hash>
  Match:                YES / NO

STEP 4 - List:          PASS ✓ / FAIL ✗
  Sections Listed:      <count>
  IDs Present:          YES / NO

STEP 5 - Tree:          PASS ✓ / FAIL ✗
  Tree Displayed:       YES / NO

STEP 6 - Search:        PASS ✓ / FAIL ✗
  Keyword:              "<keyword>"
  Results:              <count>

STEP 7 - Get Section:   PASS ✓ / FAIL ✗
  Section ID:           <id>
  Content Retrieved:    YES / NO

───────────────────────────────────────────────────────
OVERALL RESULT:         PASS ✓ / FAIL ✗
───────────────────────────────────────────────────────

Errors (if any):
<error_messages>

═══════════════════════════════════════════════════════
```

---

## Final Summary Format

```
╔══════════════════════════════════════════════════════╗
║         PRODUCTION TEST SUMMARY                      ║
╚══════════════════════════════════════════════════════╝

Total Files Tested:     15
Files Passed:           <count>
Files Failed:           <count>
Success Rate:           <percentage>%

BY FILE TYPE:
  Skills:       <pass>/<total> (<percent>%)
  Commands:     <pass>/<total> (<percent>%)
  Hooks:        <pass>/<total> (<percent>%)
  Plugins:      <pass>/<total> (<percent>%)
  Configs:      <pass>/<total> (<percent>%)
  Scripts:      <pass>/<total> (<percent>%)

BY HANDLER:
  MarkdownHandler:      <pass>/<total>
  HookHandler:          <pass>/<total>
  PluginHandler:        <pass>/<total>
  ConfigHandler:        <pass>/<total>
  PythonHandler:        <pass>/<total>
  JavaScriptHandler:    <pass>/<total>
  TypeScriptHandler:    <pass>/<total>
  ShellHandler:         <pass>/<total>

CRITICAL METRICS:
  Byte-perfect files:   <count>/15
  Hash mismatches:      <count>
  Section ID errors:    <count>
  Database errors:      <count>

╔══════════════════════════════════════════════════════╗
║  PRODUCTION STATUS: READY / NOT READY                ║
╚══════════════════════════════════════════════════════╝

Recommendation:
<deploy_now / fix_bugs / investigate_issues>

Failed Files (if any):
1. <path> - <error>
2. <path> - <error>
...
```

---

## Database Verification

After all 15 files:

### Local SQLite Check
```bash
sqlite3 test_production.db "SELECT COUNT(*) FROM files;"
sqlite3 test_production.db "SELECT COUNT(*) FROM sections;"
```

**Expected:** 15 files, <total> sections

### Supabase Check
```bash
pytest test/test_supabase_store.py -q
```

**Expected:** 7 passed

---

## Success Criteria

**PRODUCTION READY** if:
- ✅ 15/15 files pass (100%)
- ✅ All hash matches byte-perfect
- ✅ All section IDs display correctly
- ✅ Database counts correct
- ✅ Supabase tests pass

**INVESTIGATE** if:
- ⚠️ 12-14/15 files pass (80-93%)
- ⚠️ 1-3 hash mismatches
- ⚠️ Section ID issues

**FIX BUGS** if:
- ❌ <12/15 files pass (<80%)
- ❌ >3 hash mismatches
- ❌ Database errors
- ❌ Supabase tests fail

---

## Execution Instructions for Qwen

1. Read this test plan carefully
2. Create test database: `test_production.db`
3. Select 15 random files using selection strategy
4. For each file:
   - Run steps 2-7
   - Record results in format above
   - Calculate PASS/FAIL
5. Generate final summary
6. Report results to haiku supervisor
7. Cleanup: `rm -f test_production.db`

**Time Estimate:** 5-10 minutes for 15 files

**Report Format:** Use exact formats specified above - no improvisation.

---

## Questions to Answer

1. Are all handlers working byte-perfect?
2. Are section IDs displaying correctly?
3. Are databases (SQLite + Supabase) healthy?
4. What's the success rate per file type?
5. What's the success rate per handler?
6. Is the system production ready?

---

**Clarity Note:** This plan is designed for an engineering student to execute without ambiguity. Every step has clear expected output and pass criteria. Results are atomic and verifiable.
