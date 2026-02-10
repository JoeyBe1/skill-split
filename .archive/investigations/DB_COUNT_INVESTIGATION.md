# Database Count Investigation - 2026-02-05

## Question
Why does Supabase have 2,757 files when local DB only has 1,367?

## Findings

### Actual Counts
- **Local SQLite**: 1,367 files
- **Supabase**: 2,757 files
- **Difference**: 1,390 extra files in Supabase

### Duplicate Analysis
```
Total files in Supabase: 2,757
Unique storage_paths: 2,757
Duplicate paths: 0
```

**Conclusion**: NO duplicates. Each file has a unique storage_path.

### What This Means

Supabase contains 1,390 files that are NOT in the current local database. These likely came from:

1. **Previous ingestion runs** before local DB was cleaned
2. **Deleted local files** that remain in Supabase (archive principle)
3. **Different machines/sessions** syncing to same Supabase

### File Path Examples

Supabase contains paths like:
- `/Users/joey/.claude/skills/AIdeas/In-Development/telegram/telegram-ui/node_modules/...`
- Many node_modules files
- Test files that were later removed locally

### Is This a Problem?

**User concern**: "if our db count is wrong that's a major issue"

**Analysis**:
- ❌ Not a counting error - counts are accurate
- ❌ Not a duplicate issue - no duplicates found
- ✅ Expected behavior if: "ARCHIVE WE NEVER DELETE" principle applies
- ⚠️ Issue if: Supabase should mirror local DB exactly

### Implications

**If goal is exact mirror sync:**
- Need to delete 1,390 files from Supabase
- Or re-ingest from scratch (clear Supabase first)

**If goal is archive (never delete):**
- This is correct - Supabase preserves all historical files
- Local DB represents current active files only

### Round-Trip Testing

**Retrieval tested**: ✅ Successfully retrieved file with 1 section
**Recomposition**: ⏸️ Blocked by permissions, needs manual test

**Manual test needed:**
```bash
# Test round-trip
./skill_split.py checkout <file-id> /tmp/test-checkout/
# Verify file is byte-perfect
```

## Recommendation

**Clarify intent with user:**
1. Should Supabase mirror local DB exactly? → Clean Supabase
2. Should Supabase archive all files ever seen? → Current state is correct

## Next Steps

1. User decides: mirror vs archive strategy
2. If mirror: Clear Supabase, re-ingest 1,367 files
3. If archive: Current 2,757 files is correct
4. Test round-trip manually to verify recomposition works
