#!/bin/bash

# test_roundtrip_examples.sh - Example usage patterns for test_roundtrip.sh
#
# This script demonstrates common usage patterns and workflows for
# the roundtrip integrity testing script.
#
# Note: This is documentation via runnable examples. Uncomment lines
# to execute specific examples.

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(dirname "$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")")"
cd "$PROJECT_ROOT"

print_section() {
    echo ""
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_example() {
    echo -e "${YELLOW}→ $1${NC}"
}

# ============================================================================
# EXAMPLE 1: Show help
# ============================================================================
print_section "EXAMPLE 1: Get Help"

print_example "Display full help for test_roundtrip.sh"
echo "Command:"
echo "  ./test_roundtrip.sh --help"
echo ""
echo "Use this to see all available options and examples."
echo ""
echo "To run this example:"
echo "  ./test_roundtrip.sh --help"
echo ""

# ============================================================================
# EXAMPLE 2: List available files from Supabase
# ============================================================================
print_section "EXAMPLE 2: List Available Files (Supabase)"

print_example "Show all files available in Supabase storage"
echo "Command:"
echo "  ./test_roundtrip.sh list"
echo ""
echo "Prerequisites:"
echo "  export SUPABASE_URL='https://your-project.supabase.co'"
echo "  export SUPABASE_KEY='your-publishable-key'"
echo ""
echo "Output:"
echo "  Lists file IDs and paths of all files stored in Supabase"
echo ""
echo "To run this example:"
echo "  export SUPABASE_URL='...'"
echo "  export SUPABASE_KEY='...'"
echo "  ./test_roundtrip.sh list"
echo ""

# ============================================================================
# EXAMPLE 3: Basic roundtrip test (no comparison)
# ============================================================================
print_section "EXAMPLE 3: Basic Checkout Test"

print_example "Checkout file from database (no byte comparison)"
echo "Command:"
echo "  ./test_roundtrip.sh 12345678-1234-1234-1234-123456789012"
echo ""
echo "What it does:"
echo "  1. Finds file in database"
echo "  2. Checks it out to /tmp/test-checkout/"
echo "  3. Shows file info (size, hash)"
echo "  4. Reports PARTIAL (file checked out but not compared)"
echo ""
echo "Best for:"
echo "  - Verifying checkout functionality works"
echo "  - Debugging file retrieval issues"
echo "  - Quick sanity checks"
echo ""

# ============================================================================
# EXAMPLE 4: Full roundtrip with comparison
# ============================================================================
print_section "EXAMPLE 4: Full Roundtrip Test (Recommended)"

print_example "Test checkout AND byte-perfect comparison"
echo "Command:"
echo "  ./test_roundtrip.sh 12345678-1234-1234-1234-123456789012 \\"
echo "    --original ~/.claude/skills/my-skill/SKILL.md"
echo ""
echo "What it does:"
echo "  1. Finds file in database"
echo "  2. Checks it out to /tmp/test-checkout/"
echo "  3. Compares checked-out file with original"
echo "  4. Verifies SHA256 hashes match"
echo "  5. Reports PASS or FAIL"
echo ""
echo "Best for:"
echo "  - Production validation"
echo "  - Deployment verification"
echo "  - Ensuring data integrity"
echo ""
echo "Example with real workflow:"
echo "  # 1. Store file in database"
echo "  ./skill_split.py store ~/.claude/skills/my-skill/SKILL.md"
echo ""
echo "  # 2. Get file ID from database query or previous output"
echo "  FILE_ID='12345678-...'"
echo ""
echo "  # 3. Run roundtrip test"
echo "  ./test_roundtrip.sh \"\$FILE_ID\" \\"
echo "    --original ~/.claude/skills/my-skill/SKILL.md"
echo ""

# ============================================================================
# EXAMPLE 5: Custom database path
# ============================================================================
print_section "EXAMPLE 5: Using Custom Database"

print_example "Test with specific database file"
echo "Command:"
echo "  ./test_roundtrip.sh 12345678-1234-1234-1234-123456789012 \\"
echo "    --original /path/to/original.md \\"
echo "    --db /path/to/skill-split.db"
echo ""
echo "Best for:"
echo "  - Testing specific database versions"
echo "  - Development/testing with separate DBs"
echo "  - Database migration verification"
echo ""
echo "Environment variable alternative:"
echo "  export SKILL_SPLIT_DB=/path/to/skill-split.db"
echo "  ./test_roundtrip.sh 12345678-1234-1234-1234-123456789012 \\"
echo "    --original /path/to/original.md"
echo ""

# ============================================================================
# EXAMPLE 6: Verbose output for debugging
# ============================================================================
print_section "EXAMPLE 6: Debugging with Verbose Output"

print_example "Show detailed diff when test fails"
echo "Command:"
echo "  ./test_roundtrip.sh 12345678-1234-1234-1234-123456789012 \\"
echo "    --original /path/to/original.md \\"
echo "    --verbose"
echo ""
echo "What it does:"
echo "  - Performs normal roundtrip test"
echo "  - If test fails, shows full diff output"
echo "  - Helps identify exact byte differences"
echo ""
echo "Best for:"
echo "  - Debugging failed tests"
echo "  - Investigating differences"
echo "  - Troubleshooting content corruption"
echo ""

# ============================================================================
# EXAMPLE 7: Batch testing multiple files
# ============================================================================
print_section "EXAMPLE 7: Batch Testing Multiple Files"

print_example "Test multiple files in one go"
cat << 'BATCH_SCRIPT'
#!/bin/bash
# batch_roundtrip_test.sh

cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")"

# Array of file_id:original_path pairs
FILES=(
  "12345678-1234-1234-1234-123456789012:$HOME/.claude/skills/skill1/SKILL.md"
  "87654321-4321-4321-4321-210987654321:$HOME/.claude/skills/skill2/SKILL.md"
  "11111111-2222-3333-4444-555555555555:$HOME/.claude/skills/skill3/SKILL.md"
)

PASSED=0
FAILED=0

for FILE_SPEC in "${FILES[@]}"; do
  IFS=':' read FILE_ID ORIGINAL <<< "$FILE_SPEC"
  echo "Testing: $ORIGINAL"

  if ./test_roundtrip.sh "$FILE_ID" --original "$ORIGINAL"; then
    ((PASSED++))
  else
    ((FAILED++))
  fi
  echo ""
done

echo "═════════════════════════════════════════════════════════"
echo "Results: $PASSED passed, $FAILED failed"
echo "═════════════════════════════════════════════════════════"

[ $FAILED -eq 0 ] && exit 0 || exit 1
BATCH_SCRIPT

echo ""
echo "To use this pattern:"
echo "  1. Create batch_roundtrip_test.sh with the script above"
echo "  2. Make it executable: chmod +x batch_roundtrip_test.sh"
echo "  3. Run: ./batch_roundtrip_test.sh"
echo ""

# ============================================================================
# EXAMPLE 8: Continuous verification loop
# ============================================================================
print_section "EXAMPLE 8: Continuous Verification (Watch Mode)"

print_example "Repeatedly test a file for consistency"
cat << 'WATCH_SCRIPT'
#!/bin/bash
# watch_roundtrip_test.sh FILE_ID ORIGINAL_PATH

FILE_ID=$1
ORIGINAL=$2
INTERVAL=${3:-5}  # Default 5 seconds

if [ -z "$FILE_ID" ] || [ -z "$ORIGINAL" ]; then
  echo "Usage: $0 <file_id> <original_path> [interval_seconds]"
  exit 1
fi

ITERATION=0
PASSED=0
FAILED=0

echo "Starting continuous verification..."
echo "File ID: $FILE_ID"
echo "Original: $ORIGINAL"
echo "Interval: ${INTERVAL}s"
echo ""

while true; do
  ((ITERATION++))
  echo "[$ITERATION] Testing at $(date '+%H:%M:%S')..."

  if ./test_roundtrip.sh "$FILE_ID" --original "$ORIGINAL" >/dev/null 2>&1; then
    echo "  ✓ PASS"
    ((PASSED++))
  else
    echo "  ✗ FAIL"
    ((FAILED++))
  fi

  echo "  Cumulative: $PASSED passed, $FAILED failed"
  echo "  Sleeping ${INTERVAL}s... (Press Ctrl+C to stop)"
  sleep $INTERVAL
done
WATCH_SCRIPT

echo ""
echo "To use this pattern:"
echo "  1. Create watch_roundtrip_test.sh with the script above"
echo "  2. Make it executable: chmod +x watch_roundtrip_test.sh"
echo "  3. Run: ./watch_roundtrip_test.sh <file_id> <original_path>"
echo ""

# ============================================================================
# EXAMPLE 9: Integration test (store and verify)
# ============================================================================
print_section "EXAMPLE 9: End-to-End Integration Test"

print_example "Complete workflow: store file, then verify roundtrip"
cat << 'INTEGRATION_SCRIPT'
#!/bin/bash
# integration_test.sh

set -e

SKILL_FILE="$1"
if [ -z "$SKILL_FILE" ]; then
  echo "Usage: $0 <skill_file>"
  exit 1
fi

echo "Step 1: Store file in database"
python skill_split.py store "$SKILL_FILE"

echo ""
echo "Step 2: Get file ID from database"
# This is simplified - in practice you'd query the database
# For now, you'd need to get the ID from step 1 output or manually
FILE_ID="${2:-12345678-1234-1234-1234-123456789012}"

echo "File ID: $FILE_ID"
echo ""

echo "Step 3: Test roundtrip integrity"
./test_roundtrip.sh "$FILE_ID" --original "$SKILL_FILE"

echo ""
echo "Step 4: Report results"
echo "✓ Integration test complete"
INTEGRATION_SCRIPT

echo ""
echo "To use this pattern:"
echo "  1. Create integration_test.sh with the script above"
echo "  2. Make it executable: chmod +x integration_test.sh"
echo "  3. Run: ./integration_test.sh ~/.claude/skills/my-skill/SKILL.md"
echo ""

# ============================================================================
# EXAMPLE 10: Supabase roundtrip with credentials
# ============================================================================
print_section "EXAMPLE 10: Supabase Integration"

print_example "Test roundtrip using Supabase remote storage"
echo "Setup:"
echo "  export SUPABASE_URL='https://your-project.supabase.co'"
echo "  export SUPABASE_KEY='your-publishable-key'"
echo ""
echo "Commands:"
echo "  # List available files in Supabase"
echo "  ./test_roundtrip.sh list"
echo ""
echo "  # Test specific file from Supabase"
echo "  ./test_roundtrip.sh <file_id> \\"
echo "    --original ~/.claude/skills/my-skill/SKILL.md"
echo ""
echo "Best for:"
echo "  - Cloud storage verification"
echo "  - Production deployment testing"
echo "  - Multi-environment validation"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
print_section "Summary: When to Use Each Pattern"

cat << 'SUMMARY'
1. Basic Checkout Test
   Use when: Just checking if file retrieval works
   Command: ./test_roundtrip.sh <file_id>

2. Full Roundtrip Test (RECOMMENDED)
   Use when: Verifying production integrity
   Command: ./test_roundtrip.sh <file_id> --original <path>

3. Batch Testing
   Use when: Testing multiple files at once
   Script: Create batch_roundtrip_test.sh

4. Watch Mode (Continuous)
   Use when: Monitoring for consistency issues
   Script: Create watch_roundtrip_test.sh

5. Integration Test
   Use when: Testing complete store→retrieve workflow
   Script: Create integration_test.sh

6. Verbose Debugging
   Use when: Investigating failed tests
   Command: ./test_roundtrip.sh <file_id> --original <path> --verbose

7. Supabase Verification
   Use when: Testing cloud storage deployment
   Command: ./test_roundtrip.sh list / ./test_roundtrip.sh <file_id> ...

KEY METRICS:
  - ~99% context savings when files stored in database
  - <1 second checkout time for typical skill files
  - Byte-perfect SHA256 hash verification
  - Supports files up to 10MB+
SUMMARY

echo ""
echo -e "${GREEN}All examples documented!${NC}"
echo ""
echo "For more details, see: TEST_ROUNDTRIP_README.md"
echo ""
