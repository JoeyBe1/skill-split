#!/usr/bin/env python3
"""
Batch ingest all Claude Code files from local database to Supabase.
Reads files from SQLite and uploads to Supabase with progress tracking.
"""
import sqlite3
import os
import sys
from pathlib import Path
from core.database import DatabaseStore
from core.supabase_store import SupabaseStore

DB_PATH = os.path.expanduser("~/.claude/databases/skill-split.db")
BATCH_SIZE = 50

def get_claude_files():
    """Get all files from database where path LIKE '%/.claude/%'"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, path, type FROM files WHERE path LIKE '%/.claude/%' ORDER BY id"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def main():
    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase credentials not configured")
        print("\nTo ingest to Supabase, set environment variables:")
        print("  export SUPABASE_URL='your-project-url'")
        print("  export SUPABASE_KEY='your-anon-key'")
        print("\nOr configure in .env file:")
        print("  SUPABASE_URL=https://xxx.supabase.co")
        print("  SUPABASE_KEY=eyJxxx...")
        return
    
    files = get_claude_files()
    total = len(files)
    
    print(f"Starting batch ingestion to Supabase")
    print(f"Files to ingest: {total}")
    print(f"Batch size: {BATCH_SIZE}\n")
    
    # Initialize stores
    local_db = DatabaseStore(DB_PATH)
    supabase = SupabaseStore(supabase_url, supabase_key)
    
    attempted = 0
    successful = 0
    failed = 0
    failed_items = []
    
    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = files[batch_start:batch_end]
        
        for file_id, path, file_type in batch:
            attempted += 1
            try:
                # Get file data from local database
                file_meta, sections = local_db.get_file(str(file_id))
                
                if file_meta is None:
                    failed += 1
                    failed_items.append((file_id, path, "Not found in local db"))
                    continue
                
                # Upload to Supabase
                supabase.store_file(file_meta, sections)
                successful += 1
                
            except Exception as e:
                failed += 1
                failed_items.append((file_id, path, str(e)[:80]))
        
        # Progress report every batch
        pct = (batch_end / total) * 100
        print(f"Progress: {batch_end}/{total} ({pct:.1f}%) - Successful: {successful}, Failed: {failed}")
    
    # Final summary
    print("\n" + "="*60)
    print("BATCH INGESTION COMPLETE")
    print("="*60)
    print(f"Total Attempted: {attempted}")
    print(f"Successful:     {successful}")
    print(f"Failed:         {failed}")
    print(f"Success Rate:   {(successful/attempted*100):.1f}%")
    
    if failed_items and len(failed_items) <= 20:
        print(f"\nFailed Items ({len(failed_items)}):")
        for fid, path, error in failed_items:
            print(f"  ID {fid}: {path[:60]}")
            if error:
                print(f"    Error: {error}")
    elif failed_items:
        print(f"\nFailed Items: {len(failed_items)} (showing first 20)")
        for fid, path, error in failed_items[:20]:
            print(f"  ID {fid}: {path[:60]}")

if __name__ == "__main__":
    main()
