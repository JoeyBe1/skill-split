# Manual Round-Trip Test Guide

## Purpose

Verify that files retrieved from Supabase are **byte-perfect copies** of the original files. This ensures:
- No data corruption during upload
- No formatting loss during parsing/recomposition
- Exact SHA256 hash match before and after

## Prerequisites

- `skill_split.py` CLI tool available
- Supabase connection working (test with `./skill_split.py list-library`)
- At least one skill file stored in Supabase
- Environment variables set:
  ```bash
  export SUPABASE_URL="https://dnqbnwalycyoynbcpbpz.supabase.co"
  export SUPABASE_KEY="your-anon-key"
  ```

## Test Steps

### Step 1: Identify Test File

Pick a skill file from Supabase:

```bash
python3 << 'EOF'
from dotenv import load_dotenv
import os
load_dotenv()
from core.supabase_store import SupabaseStore

store = SupabaseStore(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
result = store.client.table('files').select('id,name,storage_path,type').eq('type', 'skill').limit(1).execute()

if result.data:
    file_info = result.data[0]
    print(f"File ID:   {file_info['id']}")
    print(f"Name:      {file_info['name']}")
    print(f"Path:      {file_info['storage_path']}")
    print(f"Type:      {file_info['type']}")
else:
    print("No skill files found in Supabase")
EOF
```

**Expected Output**:
```
File ID:   550e8400-e29b-41d4-a716-446655440000
Name:      agent-browser.md
Path:      /Users/joey/.claude/skills/agent-browser/SKILL.md
Type:      skill
```

**Note**: Save the File ID and Name for the next step.

### Step 2: Checkout File from Supabase

Deploy the file to a temporary location:

```bash
# Use File ID from Step 1
./skill_split.py checkout <file-id> /tmp/skill-test/

# Example:
./skill_split.py checkout 550e8400-e29b-41d4-a716-446655440000 /tmp/skill-test/
```

**Expected Output**:
```
Deployed: /tmp/skill-test/agent-browser.md (92 sections)
Hash: c1d5f8a2b3e4c5d6e7f8a9b0c1d2e3f4...
```

### Step 3: Verify Byte-Perfect Match

Compare the checked-out file with the original:

```bash
# Use the filename from Step 1
diff /tmp/skill-test/<filename> <original-path>

# Example:
diff /tmp/skill-test/agent-browser.md /Users/joey/.claude/skills/agent-browser/SKILL.md
```

**Expected Output**:
```
(no output = success)
```

**Success Criteria**: `diff` produces **NO output** (completely silent)

If there's any output, the files differ - this is a failure condition.

### Step 4: Verify Hash Integrity

Check the hash of the original file:

```bash
# Get hash of original file
./skill_split.py verify <original-path>

# Example:
./skill_split.py verify /Users/joey/.claude/skills/agent-browser/SKILL.md
```

**Expected Output**:
```
File: /Users/joey/.claude/skills/agent-browser/SKILL.md
Status: Valid ✓
Hash: c1d5f8a2b3e4c5d6e7f8a9b0c1d2e3f4...
Sections: 92
```

### Step 5: Verify Checkout Hash Matches

Compare checkout hash with original:

```bash
# Get hash of checked-out file
./skill_split.py verify /tmp/skill-test/<filename>

# Example:
./skill_split.py verify /tmp/skill-test/agent-browser.md
```

**Expected Output**:
```
File: /tmp/skill-test/agent-browser.md
Status: Valid ✓
Hash: c1d5f8a2b3e4c5d6e7f8a9b0c1d2e3f4...
Sections: 92
```

**Success Criteria**: Hash values **must match exactly** between original and checked-out file.

### Step 6: Automated Comparison (Optional)

For automated testing, use Python:

```bash
python3 << 'EOF'
import hashlib
from pathlib import Path

original = Path("/Users/joey/.claude/skills/agent-browser/SKILL.md")
checked_out = Path("/tmp/skill-test/agent-browser.md")

def compute_hash(path):
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

original_hash = compute_hash(original)
checkout_hash = compute_hash(checked_out)

print(f"Original:   {original_hash}")
print(f"Checked-out: {checkout_hash}")
print(f"Match: {'✓ YES' if original_hash == checkout_hash else '✗ NO'}")

# Also compare file sizes
print(f"\nFile sizes:")
print(f"Original:    {original.stat().st_size} bytes")
print(f"Checked-out: {checked_out.stat().st_size} bytes")
print(f"Match: {'✓ YES' if original.stat().st_size == checked_out.stat().st_size else '✗ NO'}")
EOF
```

## Success Criteria

All of these must be true:

- [ ] **Step 3**: `diff` output is empty (completely silent)
- [ ] **Step 4-5**: SHA256 hashes match exactly
- [ ] **Step 5**: `verify` shows `Valid ✓` for both files
- [ ] **Step 6** (if run): File sizes match
- [ ] **Step 6** (if run): Hash comparison shows `Match: ✓ YES`

## Failure Diagnosis

### Case 1: Diff Shows Differences

**Problem**: Files don't match byte-for-byte

**Debug**:
```bash
# Show first difference
diff /tmp/skill-test/<filename> <original-path> | head -20

# Compare file sizes
ls -lh /tmp/skill-test/<filename> <original-path>

# Check line counts
wc -l /tmp/skill-test/<filename> <original-path>
```

**Possible Causes**:
- Line ending differences (CRLF vs LF) - check with `file` command
- Encoding differences (UTF-8 vs ASCII) - check with `file` command
- Parser lost data during recomposition

### Case 2: Hash Mismatch

**Problem**: Hashes don't match

**Debug**:
```bash
# Recompute hashes with verbose output
./skill_split.py verify <original-path> -v
./skill_split.py verify /tmp/skill-test/<filename> -v

# Compare byte counts
stat <original-path> /tmp/skill-test/<filename>
```

**Possible Causes**:
- File was modified after storage
- Recomposition algorithm error
- Encoding issue during storage

### Case 3: Verify Shows Invalid

**Problem**: One or both files show `Status: Invalid ✗`

**Debug**:
```bash
# Try re-parsing the original
./skill_split.py parse <original-path>

# Check database
./skill_split.py list <original-path> --db ~/.claude/databases/skill-split.db
```

**Possible Causes**:
- Original file has parsing errors
- Database is corrupted
- Schema mismatch

## Test Automation Script

For repeated testing, use this script:

```bash
#!/bin/bash
# test_roundtrip.sh - Automated round-trip verification

FILE_ID=$1
ORIGINAL_PATH=$2
TEST_DIR="/tmp/skill-test-$(date +%s)"

if [ -z "$FILE_ID" ] || [ -z "$ORIGINAL_PATH" ]; then
  echo "Usage: ./test_roundtrip.sh <file-id> <original-path>"
  exit 1
fi

echo "=== Round-Trip Test ==="
echo "File ID: $FILE_ID"
echo "Original: $ORIGINAL_PATH"
echo "Test dir: $TEST_DIR"
echo ""

# Create test directory
mkdir -p "$TEST_DIR"

# Step 2: Checkout
echo "Step 1: Checking out file..."
./skill_split.py checkout "$FILE_ID" "$TEST_DIR/" || exit 1
FILENAME=$(basename "$ORIGINAL_PATH")
CHECKOUT_PATH="$TEST_DIR/$FILENAME"

# Step 3: Diff
echo "Step 2: Comparing files..."
if diff "$CHECKOUT_PATH" "$ORIGINAL_PATH" > /dev/null; then
  echo "✓ Files match (diff OK)"
else
  echo "✗ Files differ (diff failed)"
  exit 1
fi

# Step 4-5: Hash verification
echo "Step 3: Verifying hashes..."
ORIGINAL_HASH=$(./skill_split.py verify "$ORIGINAL_PATH" 2>&1 | grep "Hash:" | awk '{print $NF}')
CHECKOUT_HASH=$(./skill_split.py verify "$CHECKOUT_PATH" 2>&1 | grep "Hash:" | awk '{print $NF}')

if [ "$ORIGINAL_HASH" == "$CHECKOUT_HASH" ]; then
  echo "✓ Hashes match: $ORIGINAL_HASH"
else
  echo "✗ Hashes differ"
  echo "  Original:  $ORIGINAL_HASH"
  echo "  Checked-out: $CHECKOUT_HASH"
  exit 1
fi

echo ""
echo "=== TEST PASSED ==="
echo "Round-trip verification successful!"
rm -rf "$TEST_DIR"
```

Usage:
```bash
chmod +x test_roundtrip.sh
./test_roundtrip.sh 550e8400-e29b-41d4-a716-446655440000 /Users/joey/.claude/skills/agent-browser/SKILL.md
```

## Interpreting Results

| Result | Meaning | Action |
|--------|---------|--------|
| All steps pass | Files are byte-perfect copies | ✓ Supabase storage is working correctly |
| Diff shows differences | Files don't match | ✗ Investigate parser/recomposer |
| Hashes don't match | Content is different | ✗ Recompute and compare |
| Verify shows Invalid | File has parse errors | ✗ Check original file structure |

## Multiple File Testing

To test multiple files:

```bash
python3 << 'EOF'
from dotenv import load_dotenv
import os
import subprocess
from core.supabase_store import SupabaseStore

load_dotenv()
store = SupabaseStore(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Get first 5 skill files
result = store.client.table('files').select('id,name,storage_path').eq('type', 'skill').limit(5).execute()

passed = 0
failed = 0

for file in result.data:
    file_id = file['id']
    path = file['storage_path']
    name = file['name']

    print(f"\nTesting: {name}")

    # Run test
    ret = subprocess.run(
        ['bash', 'test_roundtrip.sh', file_id, path],
        capture_output=True
    )

    if ret.returncode == 0:
        print("✓ PASS")
        passed += 1
    else:
        print("✗ FAIL")
        failed += 1

print(f"\n=== Summary ===")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
EOF
```

## Summary

| Stage | Action | Expected Result |
|-------|--------|-----------------|
| **Identify** | Pick a test file | File ID, name, and path |
| **Checkout** | Deploy from Supabase | File stored locally |
| **Compare** | Run diff | No output |
| **Verify Original** | Check hash | Valid ✓ |
| **Verify Checkout** | Check hash | Valid ✓ + matching hash |
| **Success** | All checks pass | Round-trip verified ✓ |

---

**Last Updated**: 2026-02-05
**Status**: Ready for User Execution
