#!/usr/bin/env python3
"""
Batch ingest Claude Code component files to Supabase.
Reads from local SQLite database and uploads to Supabase.
"""
import sqlite3
import os
from pathlib import Path
from core.supabase_store import SupabaseStore
from core.database import DatabaseStore

DB_PATH = os.path.expanduser("~/.claude/databases/skill-split.db")
BATCH_SIZE = 50

def get_files_from_db():
    """Get all file IDs and paths from database"""
    db = DatabaseStore(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM files WHERE path LIKE '%/.claude/%' ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_file_data(file_id):
    """Get file data from local database"""
    db = DatabaseStore(DB_PATH)
    result = db.get_file(str(file_id))
    return result

def upload_to_supabase(supabase_url, supabase_key, file_id):
    """Upload single file to Supabase"""
    try:
        # Get file data from local database
        db = DatabaseStore(DB_PATH)
        file_meta, sections = db.get_file(str(file_id))
        
        if file_meta is None:
            return False, "File not found in local database"
        
        # Initialize Supabase store
        supabase = SupabaseStore(supabase_url, supabase_key)
        
        # Store in Supabase
        supabase.store_file(file_meta, sections)
        return True, None
    except Exception as e:
        return False, str(e)[:100]

def main():
    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        print("Set these variables and try again:")
        print("  export SUPABASE_URL='your-url'")
        print("  export SUPABASE_KEY='your-key'")
        return
    
    files = get_files_from_db()
    total = len(files)
    print(f"Found {total} Claude Code files to ingest")
    print(f"Target: Supabase ({supabase_url[:40]}...)\n")
    
    attempted = 0
    successful = 0
    failed = 0
    failed_ids = []
    
    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = files[batch_start:batch_end]
        
        for file_id, path in batch:
            attempted += 1
            success, error = upload_to_supabase(supabase_url, supabase_key, file_id)
            
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
            if error:
                print(f"    Error: {error}")

if __name__ == "__main__":
    main()
