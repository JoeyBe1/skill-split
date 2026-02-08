#!/usr/bin/env python3
"""
Upload all local Claude Code files to Supabase.
Reads from local SQLite, parses files, and uploads to Supabase.
"""
import sqlite3
import os
import sys
from pathlib import Path
from core.parser import Parser
from core.detector import FormatDetector
from core.hashing import compute_file_hash
from core.supabase_store import SupabaseStore
from handlers.factory import HandlerFactory

DB_PATH = os.path.expanduser("~/.claude/databases/skill-split.db")
BATCH_SIZE = 50

def get_claude_files():
    """Get all files from database where path LIKE '%/.claude/%'"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, path, hash FROM files WHERE path LIKE '%/.claude/%' ORDER BY id"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def upload_to_supabase(store, file_path, stored_hash):
    """Upload single file to Supabase"""
    try:
        # Read file content
        content = Path(file_path).read_text()
        
        # Try HandlerFactory first (for scripts and components)
        handler = None
        doc = None
        if HandlerFactory.is_supported(file_path):
            handler = HandlerFactory.create_handler(file_path)
            doc = handler.parse()
        else:
            # Fall back to parser for markdown/yaml files
            detector = FormatDetector()
            file_type, file_format = detector.detect(file_path, content)
            parser = Parser()
            doc = parser.parse(file_path, content, file_type, file_format)
        
        if doc is None:
            return False, "Parser returned None"
        
        # Determine storage path
        home = Path.home()
        try:
            rel_path = Path(file_path).relative_to(home)
        except ValueError:
            rel_path = Path(file_path)
        
        storage_path = f"~/{rel_path}"
        file_name = Path(file_path).name
        
        # Upload to Supabase
        file_id = store.store_file(
            storage_path=storage_path,
            name=file_name,
            doc=doc,
            content_hash=stored_hash
        )
        return True, file_id
    except Exception as e:
        return False, str(e)[:100]

def main():
    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase credentials not configured")
        print("\nSet environment variables:")
        print("  export SUPABASE_URL='your-url'")
        print("  export SUPABASE_KEY='your-key'")
        return 1
    
    files = get_claude_files()
    total = len(files)
    
    print(f"Uploading {total} files to Supabase")
    print(f"URL: {supabase_url}\n")
    
    # Initialize Supabase store
    store = SupabaseStore(supabase_url, supabase_key)
    
    attempted = 0
    successful = 0
    failed = 0
    failed_items = []
    
    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = files[batch_start:batch_end]
        
        for file_id, file_path, stored_hash in batch:
            attempted += 1
            
            # Check if file exists
            if not Path(file_path).exists():
                failed += 1
                failed_items.append((file_id, file_path, "File not found"))
                continue
            
            success, result = upload_to_supabase(store, file_path, stored_hash)
            
            if success:
                successful += 1
            else:
                failed += 1
                failed_items.append((file_id, file_path, result))
        
        # Progress report
        pct = (batch_end / total) * 100
        print(f"Progress: {batch_end}/{total} ({pct:.1f}%) - Successful: {successful}, Failed: {failed}")
    
    # Final summary
    print("\n" + "="*60)
    print("UPLOAD COMPLETE")
    print("="*60)
    print(f"Total Attempted: {attempted}")
    print(f"Successful:     {successful}")
    print(f"Failed:         {failed}")
    print(f"Success Rate:   {(successful/attempted*100):.1f}%")
    
    if failed_items:
        print(f"\nFailed Items: {len(failed_items)}")
        for fid, path, error in failed_items[:10]:
            print(f"  ID {fid}: {Path(path).name}")
            if error and error != "File not found":
                print(f"    {error[:60]}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
