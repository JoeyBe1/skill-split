"""
Shared round-trip testing library.

Used by all section tests (commands/, agents/, skills/, etc.)
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Parent directory imports
import sys
TEST_DIR = Path(__file__).parent
ROOT_DIR = TEST_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from core.parser import Parser
from core.detector import FormatDetector
from core.database import DatabaseStore
from core.recomposer import Recomposer
from core.hashing import compute_file_hash


def test_round_trip(file_path: str, test_db: str = "/tmp/roundtrip-test.db") -> Dict:
    """
    Test round-trip for a single file.
    
    Returns:
        dict with success, original_hash, recomposed_hash, details
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "file": file_path
        }
    
    print(f"\n{'='*80}")
    print(f"ROUND-TRIP TEST: {path.name}")
    print(f"{'='*80}")
    print(f"Path: {file_path}")
    print(f"Size: {path.stat().st_size} bytes")
    
    # Clean test database
    if Path(test_db).exists():
        os.unlink(test_db)
    
    # Step 1: Compute original hash
    print("\n[1/5] Computing original hash...")
    original_hash = compute_file_hash(file_path)
    print(f"      Original SHA256: {original_hash[:32]}...")
    
    # Step 2: Read and parse file
    print("\n[2/5] Parsing file...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    detector = FormatDetector()
    file_type, file_format = detector.detect(file_path, content)
    print(f"      Type: {file_type.value}")
    print(f"      Format: {file_format.value}")
    
    parser = Parser()
    doc = parser.parse(file_path, content, file_type, file_format)
    print(f"      Sections: {len(doc.sections)}")
    
    # Step 3: Store in database
    print("\n[3/5] Storing in database...")
    db = DatabaseStore(test_db)
    file_id = db.store_file(file_path, doc, original_hash)
    print(f"      File ID: {file_id}")
    
    # Step 4: Recompose from database
    print("\n[4/5] Recomposing from database...")
    recomposer = Recomposer(db)
    recomposed_content = recomposer.recompose(file_path)
    
    if recomposed_content is None:
        return {
            "success": False,
            "error": "Failed to recompose file",
            "file": file_path,
            "original_hash": original_hash
        }
    
    # Step 5: Verify hash
    print("\n[5/5] Verifying hash...")
    recomposed_hash = hashlib.sha256(recomposed_content.encode('utf-8')).hexdigest()
    print(f"      Recomposed SHA256: {recomposed_hash[:32]}...")
    
    if original_hash == recomposed_hash:
        print(f"\n      ✅ SUCCESS: Hashes match!")
        return {
            "success": True,
            "file": file_path,
            "original_hash": original_hash,
            "recomposed_hash": recomposed_hash,
            "sections": len(doc.sections),
            "file_type": file_type.value,
            "file_format": file_format.value
        }
    else:
        print(f"\n      ❌ FAILURE: Hashes do not match!")
        print(f"      Original:  {original_hash}")
        print(f"      Recomposed: {recomposed_hash}")
        
        # Show first difference
        orig_lines = content.splitlines(keepends=True)
        rec_lines = recomposed_content.splitlines(keepends=True)
        
        for i, (o, r) in enumerate(zip(orig_lines, rec_lines)):
            if o != r:
                print(f"\n      First difference at line {i+1}:")
                print(f"      Original:  {repr(o[:80])}")
                print(f"      Recomposed: {repr(r[:80])}")
                break
        
        return {
            "success": False,
            "error": "Hash mismatch",
            "file": file_path,
            "original_hash": original_hash,
            "recomposed_hash": recomposed_hash,
            "first_diff_line": i+1 if 'i' in locals() else None
        }


def test_directory_files(directory: Path, pattern: str = "*.md", test_db: str = "/tmp/roundtrip-test.db") -> Tuple[List[Dict], str]:
    """
    Test round-trip for all files in a directory matching pattern.
    
    Returns:
        (results list, summary message)
    """
    files = list(directory.rglob(pattern))
    
    print(f"\n{'='*80}")
    print(f"ROUND-TRIP VERIFICATION: {directory.name}")
    print(f"{'='*80}")
    print(f"Found {len(files)} files matching '{pattern}'")
    
    results = []
    for i, file_path in enumerate(files, 1):
        print(f"\n--- Test {i}/{len(files)} ---")
        result = test_round_trip(str(file_path), test_db=test_db)
        results.append(result)
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    
    summary = f"{directory.name}: {passed}/{len(results)} passed ({failed} failed)"
    return results, summary
