#!/usr/bin/env python3
"""
Round-trip verification for SKILLS directory.

CRITICAL: Skills MUST have byte-perfect round-trip for modular recomposition.
This enables stitching sections from different sources to create "custom" functionality.
"""

import sys
from pathlib import Path

TEST_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TEST_DIR.parent))

from tests.roundtrip_lib import test_directory_files, test_round_trip


def main():
    skills_dir = Path.home() / ".claude" / "skills"
    
    # First: Test a sample of skills to verify approach
    print(f"\n{'='*80}")
    print(f"PHASE 1: Sample test - First 10 skills")
    print(f"{'='*80}")
    
    sample_files = list(skills_dir.rglob("*.md"))[:10]
    sample_results = []
    for file_path in sample_files:
        print(f"\nTesting: {file_path.relative_to(skills_dir)}")
        result = test_round_trip(str(file_path), test_db="/tmp/skills-sample-test.db")
        sample_results.append(result)
    
    sample_passed = sum(1 for r in sample_results if r["success"])
    print(f"\n{'='*80}")
    print(f"PHASE 1 RESULTS: {sample_passed}/{len(sample_results)} passed")
    print(f"{'='*80}")
    
    if sample_passed < len(sample_results):
        print("\n⚠️  Sample test had failures - review before full test")
        return False
    
    # Second: If sample passes, test all skills
    print(f"\n{'='*80}")
    print(f"PHASE 2: Full test - All {len(list(skills_dir.rglob('*.md')))} skills")
    print(f"{'='*80}")
    
    results, summary = test_directory_files(skills_dir, "*.md", test_db="/tmp/skills-test.db")
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY: {summary}")
    print(f"{'='*80}")
    
    # Show failed files
    failed = [r for r in results if not r["success"]]
    if failed:
        print(f"\n❌ FAILED SKILLS ({len(failed)}):")
        for r in failed[:10]:  # Show first 10
            print(f"   - {Path(r['file']).relative_to(skills_dir)}")
        if len(failed) > 10:
            print(f"   ... and {len(failed) - 10} more")
    
    return len(failed) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
