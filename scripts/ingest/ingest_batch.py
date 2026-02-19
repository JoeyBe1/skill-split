#!/usr/bin/env python3
"""
Batch ingest Claude Code component files to Supabase.
"""
import sqlite3
import subprocess
import os
from pathlib import Path

DB_PATH = os.path.expanduser("~/.claude/databases/skill-split.db")
BATCH_SIZE = 50

def get_file_ids():
    """Get file IDs from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM files WHERE path LIKE '%/.claude/%' ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows

def ingest_file(file_id):
    """Ingest a single file"""
    try:
        result = subprocess.run(
            ["python3", "skill_split.py", "ingest", str(file_id), "--db", DB_PATH],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stderr[:100] if result.returncode != 0 else None
    except Exception as e:
        return False, str(e)[:100]

def main():
    files = get_file_ids()
    total = len(files)
    print(f"Found {total} files to ingest\n")
    
    attempted = 0
    successful = 0
    failed = 0
    failed_ids = []
    
    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = files[batch_start:batch_end]
        
        for file_id, path in batch:
            attempted += 1
            success, error = ingest_file(file_id)
            
            if success:
                successful += 1
            else:
                failed += 1
                failed_ids.append((file_id, path, error))
        
        pct = (batch_end / total) * 100
        print(f"Progress: {batch_end}/{total} ({pct:.1f}%) - Successful: {successful}, Failed: {failed}")
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Total Attempted: {attempted}")
    print(f"Successful:     {successful}")
    print(f"Failed:         {failed}")
    print(f"Success Rate:   {(successful/attempted*100):.1f}%")
    
    if failed_ids and len(failed_ids) < 20:
        print(f"\nFailed Files ({len(failed_ids)}):")
        for fid, path, error in failed_ids[:20]:
            print(f"  ID {fid}: {path[:50]}")

if __name__ == "__main__":
    main()
