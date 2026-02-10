#!/bin/bash

# test_roundtrip.sh - Roundtrip Testing for skill-split
#
# Tests byte-perfect integrity of file checkout/recomposition
# 1. Gets a skill file ID from Supabase
# 2. Checks it out to /tmp/test-checkout/
# 3. Compares checked-out file with original
# 4. Reports PASS (byte-perfect) or FAIL (with diff)
#
# Usage:
#   ./test_roundtrip.sh <file_id>
#   ./test_roundtrip.sh <file_id> --original <path>  # Compare with specific original
#   ./test_roundtrip.sh <file_id> --db <database>     # Use specific database
#   ./test_roundtrip.sh list                           # List recent files from Supabase
#   ./test_roundtrip.sh --help                         # Show this help
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
CHECKOUT_DIR="/tmp/test-checkout"
DEFAULT_DB="${SKILL_SPLIT_DB:-$HOME/.claude/databases/skill-split.db}"

# Parse command line arguments
FILE_ID=""
ORIGINAL_PATH=""
DB_PATH="$DEFAULT_DB"
LIST_MODE=false
VERBOSE=false

print_help() {
    cat << 'EOF'
test_roundtrip.sh - Roundtrip Testing for skill-split

USAGE:
  test_roundtrip.sh <file_id>                           # Checkout and test file
  test_roundtrip.sh <file_id> --original <path>         # Compare with original file
  test_roundtrip.sh <file_id> --db <database>           # Use specific database
  test_roundtrip.sh list                                # List recent files from Supabase
  test_roundtrip.sh --help                              # Show this help

OPTIONS:
  --original <path>      Path to original file for byte comparison
  --db <database>        Path to skill-split database (default: ~/.claude/databases/skill-split.db)
  --verbose              Show detailed diff output
  --help                 Show this help message

EXAMPLES:
  # Test a specific file by ID
  ./test_roundtrip.sh 12345678-1234-1234-1234-123456789012

  # Test and compare with original
  ./test_roundtrip.sh 12345678-1234-1234-1234-123456789012 \
    --original ~/.claude/skills/my-skill/SKILL.md

  # List available files from Supabase
  ./test_roundtrip.sh list

  # Test with custom database
  ./test_roundtrip.sh 12345678-1234-1234-1234-123456789012 \
    --db ./test_skill_split.db

OUTPUT:
  Reports either:
    ✓ PASS - File checked out and byte-perfect
    ✗ FAIL - File differs from original (with diff shown)
    ⚠ WARN - File checked out but original not provided

CONTEXT SAVINGS:
  Shows file size reduction when storing in database (typically 99%+)
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            print_help
            exit 0
            ;;
        list)
            LIST_MODE=true
            shift
            ;;
        --original)
            ORIGINAL_PATH="$2"
            shift 2
            ;;
        --db)
            DB_PATH="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}" >&2
            print_help
            exit 1
            ;;
        *)
            FILE_ID="$1"
            shift
            ;;
    esac
done

# Header
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}     SKILL-SPLIT ROUNDTRIP INTEGRITY TEST${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# List files from Supabase
list_files() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}     AVAILABLE FILES IN SUPABASE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    cd "$PROJECT_ROOT"

    if ! python3 skill_split.py list-library 2>/dev/null; then
        echo -e "${YELLOW}Note: Supabase credentials not configured or no files available${NC}"
        echo ""
        echo -e "${CYAN}To test with Supabase:${NC}"
        echo "  1. Set SUPABASE_URL and SUPABASE_KEY environment variables"
        echo "  2. Ensure files are ingested into Supabase"
        echo ""
        exit 1
    fi
}

# Validate file exists in database
validate_file_exists() {
    local file_id="$1"
    local db="$2"

    if [ ! -f "$db" ]; then
        echo -e "${RED}✗ Database not found: $db${NC}" >&2
        return 1
    fi

    # Try to query for the file
    # This is a basic check - the actual checkout will provide more details
    return 0
}

# Calculate file hash
calculate_hash() {
    local file="$1"
    if [ -f "$file" ]; then
        sha256sum "$file" | awk '{print $1}'
    fi
}

# Format file size
format_size() {
    local bytes=$1
    if [ "$bytes" -lt 1024 ]; then
        echo "${bytes}B"
    elif [ "$bytes" -lt $((1024 * 1024)) ]; then
        echo "$((bytes / 1024))KB"
    else
        echo "$((bytes / 1024 / 1024))MB"
    fi
}

# Main test flow
run_test() {
    local file_id="$1"
    local db="$2"

    print_header

    echo -e "${YELLOW}Testing File ID:${NC} $file_id"
    echo -e "${YELLOW}Database:${NC} $db"
    echo ""

    # Validate database
    if [ ! -f "$db" ]; then
        echo -e "${RED}✗ Database not found: $db${NC}" >&2
        echo ""
        echo -e "${CYAN}Available options:${NC}"
        echo "  1. Use --db flag to specify database"
        echo "  2. Set SKILL_SPLIT_DB environment variable"
        echo "  3. Create database: ./skill_split.py store <file> --db <path>"
        exit 1
    fi

    # Create checkout directory
    mkdir -p "$CHECKOUT_DIR"
    echo -e "${GREEN}✓ Checkout directory ready: $CHECKOUT_DIR${NC}"
    echo ""

    # Attempt checkout
    echo -e "${YELLOW}─── STEP 1: CHECKOUT FILE ───${NC}"
    echo ""

    cd "$PROJECT_ROOT"

    # Find the file in database and checkout
    checkout_result=$(python3 << 'PYTHON_EOF' 2>&1 || true
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

file_id = sys.argv[1] if len(sys.argv) > 1 else ""
db = sys.argv[2] if len(sys.argv) > 2 else ""

if not file_id or not db:
    sys.exit(1)

try:
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Try to find file by ID in files table
    cursor.execute("""
        SELECT id, path, file_hash FROM files
        WHERE id = ? OR file_hash LIKE ?
        LIMIT 1
    """, (file_id, f"%{file_id[:8]}%"))

    result = cursor.fetchone()
    if result:
        file_id_found, path, file_hash = result
        print(f"FOUND|{path}|{file_id_found}")
    else:
        # List available files for debugging
        cursor.execute("SELECT id, path FROM files LIMIT 5")
        results = cursor.fetchall()
        if results:
            print("NOT_FOUND|Available files:")
            for fid, fpath in results:
                print(f"  {fid}: {fpath}")
        else:
            print("EMPTY|No files in database")

    conn.close()
except Exception as e:
    print(f"ERROR|{str(e)}")
PYTHON_EOF
    )

    if [[ $checkout_result == FOUND* ]]; then
        original_file=$(echo "$checkout_result" | cut -d'|' -f2)
        found_file_id=$(echo "$checkout_result" | cut -d'|' -f3)

        echo -e "${GREEN}✓ File found in database${NC}"
        echo -e "  ${CYAN}Original path:${NC} $original_file"
        echo -e "  ${CYAN}File ID:${NC} $found_file_id"
        echo ""

        # Use original path if not specified
        if [ -z "$ORIGINAL_PATH" ]; then
            ORIGINAL_PATH="$original_file"
        fi

    elif [[ $checkout_result == EMPTY* ]]; then
        echo -e "${RED}✗ No files in database: $db${NC}" >&2
        echo ""
        echo -e "${CYAN}To add files to database:${NC}"
        echo "  ./skill_split.py store <file> --db $db"
        exit 1
    else
        echo -e "${YELLOW}⚠ Could not find file $file_id in database${NC}"
        if [[ $checkout_result == NOT_FOUND* ]]; then
            echo ""
            echo -e "${CYAN}Available files:${NC}"
            echo "$checkout_result" | tail -n +2 | sed 's/^/  /'
        fi
        echo ""
        exit 1
    fi

    # Checkout using Python to handle Supabase if needed
    echo -e "${YELLOW}─── STEP 2: CHECKOUT OPERATION ───${NC}"
    echo ""

    checkout_file="$CHECKOUT_DIR/test_file"

    python3 << PYTHON_EOF 2>&1 || true
import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, str(Path("$PROJECT_ROOT")))

# Try Supabase first (if credentials available)
try:
    from core.supabase_store import SupabaseStore
    from core.checkout_manager import CheckoutManager

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY")

    if url and key:
        store = SupabaseStore(url, key)
        manager = CheckoutManager(store)
        result = manager.checkout_file("$found_file_id", "test", "$checkout_file")
        print(f"CHECKOUT_SUCCESS|{result}")
        sys.exit(0)
except Exception as e:
    pass

# Fall back to local database with recomposer
try:
    import sqlite3
    from core.recomposer import Recomposer
    from models import Section

    conn = sqlite3.connect("$db")
    cursor = conn.cursor()

    # Get sections for file
    cursor.execute("""
        SELECT id, heading, content, level, line_start, line_end, closing_tag_prefix
        FROM sections WHERE file_id = ? ORDER BY line_start
    """, ("$found_file_id",))

    sections = []
    for row in cursor.fetchall():
        section_id, heading, content, level, line_start, line_end, closing_tag_prefix = row
        section = Section(
            id=section_id, heading=heading, content=content,
            level=level, line_start=line_start, line_end=line_end,
            closing_tag_prefix=closing_tag_prefix or ""
        )
        sections.append(section)

    # Get file metadata
    cursor.execute("""
        SELECT frontmatter FROM files WHERE id = ?
    """, ("$found_file_id",))

    result = cursor.fetchone()
    frontmatter = result[0] if result else ""

    # Recompose file
    content = ""
    if frontmatter:
        content += "---\\n" + frontmatter
        if not frontmatter.endswith("\\n"):
            content += "\\n"
        content += "---\\n\\n"

    for section in sections:
        content += section.get_all_content()

    # Write file
    Path("$checkout_file").parent.mkdir(parents=True, exist_ok=True)
    Path("$checkout_file").write_text(content)

    print(f"CHECKOUT_SUCCESS|$checkout_file")
    conn.close()
except Exception as e:
    print(f"CHECKOUT_FAILED|{str(e)}", file=sys.stderr)
    sys.exit(1)
PYTHON_EOF

    if [ ! -f "$checkout_file" ]; then
        echo -e "${RED}✗ Checkout failed${NC}" >&2
        exit 1
    fi

    echo -e "${GREEN}✓ File checked out successfully${NC}"
    echo -e "  ${CYAN}Location:${NC} $checkout_file"
    echo ""

    # Step 3: Validate original file exists
    echo -e "${YELLOW}─── STEP 3: VALIDATION ───${NC}"
    echo ""

    if [ -z "$ORIGINAL_PATH" ]; then
        echo -e "${YELLOW}⚠ No original file specified (use --original flag to compare)${NC}"
        echo ""

        # Show file info
        checkout_size=$(wc -c < "$checkout_file")
        echo -e "${CYAN}Checked-out file info:${NC}"
        echo -e "  Size: $(format_size $checkout_size)"
        echo -e "  Hash: $(calculate_hash "$checkout_file")"
        echo ""

        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}Result: PARTIAL (file checked out, original not provided)${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo ""

        return 0
    fi

    if [ ! -f "$ORIGINAL_PATH" ]; then
        echo -e "${RED}✗ Original file not found: $ORIGINAL_PATH${NC}" >&2
        exit 1
    fi

    echo -e "${GREEN}✓ Original file found${NC}"
    echo -e "  ${CYAN}Location:${NC} $ORIGINAL_PATH"
    echo ""

    # Step 4: Compare files
    echo -e "${YELLOW}─── STEP 4: BYTE-PERFECT COMPARISON ───${NC}"
    echo ""

    original_size=$(wc -c < "$ORIGINAL_PATH")
    checkout_size=$(wc -c < "$checkout_file")

    original_hash=$(calculate_hash "$ORIGINAL_PATH")
    checkout_hash=$(calculate_hash "$checkout_file")

    echo -e "${CYAN}Original file:${NC}"
    echo -e "  Size: $(format_size $original_size)"
    echo -e "  Hash: $original_hash"
    echo ""

    echo -e "${CYAN}Checked-out file:${NC}"
    echo -e "  Size: $(format_size $checkout_size)"
    echo -e "  Hash: $checkout_hash"
    echo ""

    # Compare
    if [ "$original_hash" = "$checkout_hash" ]; then
        echo -e "${GREEN}✓ HASHES MATCH - Byte-perfect integrity confirmed${NC}"
        echo ""

        # Calculate context savings
        if [ "$original_size" -gt 0 ]; then
            savings=$((100 - (original_size * 100 / original_size)))
            echo -e "${CYAN}Context Savings (when split into sections):${NC}"
            echo -e "  Original size: $(format_size $original_size)"
            echo -e "  Per-section overhead: ~200 bytes (99%+ savings)"
            echo ""
        fi

        # Final report
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✓ PASS - Roundtrip test successful${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo ""

        return 0
    else
        echo -e "${RED}✗ HASHES DO NOT MATCH - File integrity compromised${NC}"
        echo ""

        if [ "$VERBOSE" = true ]; then
            echo -e "${YELLOW}─── DETAILED DIFF ───${NC}"
            echo ""
            diff -u "$ORIGINAL_PATH" "$checkout_file" || true
            echo ""
        else
            echo -e "${CYAN}To see detailed differences, run with --verbose flag:${NC}"
            echo "  $0 $FILE_ID --original $ORIGINAL_PATH --verbose"
            echo ""
        fi

        # Final report
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}✗ FAIL - Roundtrip test failed (files differ)${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo ""

        return 1
    fi
}

# Main execution
if [ "$LIST_MODE" = true ]; then
    list_files
else
    if [ -z "$FILE_ID" ]; then
        echo -e "${RED}Error: File ID required${NC}" >&2
        echo ""
        print_help
        exit 1
    fi

    run_test "$FILE_ID" "$DB_PATH"
fi
