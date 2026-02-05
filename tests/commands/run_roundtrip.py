#!/usr/bin/env python3
"""
Round-trip verification for COMMANDS directory.

Tests that command files can be:
1. Parsed into sections
2. Stored in database  
3. Recomposed to EXACT original (SHA256 match)
"""

import sys
from pathlib import Path

TEST_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TEST_DIR.parent))

from tests.roundtrip_lib import test_directory_files


def main():
    commands_dir = Path.home() / ".claude" / "commands"
    
    # Test all .md files in commands/
    results, summary = test_directory_files(commands_dir, "*.md", test_db="/tmp/commands-test.db")
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY: {summary}")
    print(f"{'='*80}")
    
    # Show failed files
    failed = [r for r in results if not r["success"]]
    if failed:
        print(f"\n❌ FAILED FILES ({len(failed)}):")
        for r in failed:
            print(f"   - {Path(r['file']).name}")
            if 'first_diff_line' in r:
                print(f"     First diff at line {r['first_diff_line']}")
    
    return len(failed) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
