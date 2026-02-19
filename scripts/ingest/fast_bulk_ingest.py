#!/usr/bin/env python3
"""
Fast bulk ingest script with parallel processing.

Uses multiprocessing.Pool to process files in parallel with direct SupabaseStore
integration, progress tracking, and error logging.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from multiprocessing import Pool
from typing import List, Tuple
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from core.supabase_store import SupabaseStore
from core.parser import Parser
from core.detector import FormatDetector
from core.hashing import compute_file_hash
from models import ParsedDocument


# Configure logging
logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_local_db(db_path: str) -> List[str]:
    """
    Get all file paths from local SQLite database.

    Args:
        db_path: Path to local SQLite database

    Returns:
        List of file paths stored in database
    """
    file_paths = []

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT path FROM files ORDER BY id")
            file_paths = [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        logger.error(f"Database error reading {db_path}: {e}")
        return []

    return file_paths


def ingest_file(file_path: str) -> Tuple[str, bool, str]:
    """
    Parse and store a single file to Supabase.

    Creates SupabaseStore inside worker process to avoid pickling issues
    with thread locks in httpx client.

    Args:
        file_path: Path to file to ingest

    Returns:
        Tuple of (file_path, success, error_message)
    """
    try:
        # Verify file exists
        if not Path(file_path).exists():
            msg = f"File not found: {file_path}"
            logger.error(msg)
            return (file_path, False, msg)

        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse document
        parser = Parser()
        detector = FormatDetector()

        # Determine file format and type
        file_type, file_format = detector.detect(file_path, content)

        # Parse document (returns ParsedDocument)
        doc = parser.parse(file_path, content, file_type, file_format)

        # Compute hash
        content_hash = compute_file_hash(file_path)

        # Create SupabaseStore inside worker process using env vars
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            msg = "Missing SUPABASE_URL or SUPABASE_KEY environment variables"
            logger.error(msg)
            return (file_path, False, msg)

        store = SupabaseStore(supabase_url, supabase_key)

        # Store to Supabase
        file_id = store.store_file(
            storage_path=file_path,
            name=Path(file_path).name,
            doc=doc,
            content_hash=content_hash
        )

        return (file_path, True, file_id)

    except Exception as e:
        error_msg = f"Failed to ingest {file_path}: {str(e)}"
        logger.error(error_msg)
        return (file_path, False, str(e))


def main() -> None:
    """
    Main ingestion workflow.

    1. Read all file paths from local database
    2. Create parallel worker pool
    3. Process files with progress bar
    4. Report results
    """
    # Configuration
    local_db = os.getenv('LOCAL_DB', '~/.claude/databases/skill-split.db')
    local_db = os.path.expanduser(local_db)

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not Path(local_db).exists():
        print(f"Error: Local database not found at {local_db}")
        sys.exit(1)

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables required")
        sys.exit(1)

    print(f"Reading file paths from: {local_db}")
    file_paths = read_local_db(local_db)

    if not file_paths:
        print("No files to ingest")
        sys.exit(0)

    print(f"Found {len(file_paths)} files to ingest")

    # Process files with multiprocessing pool
    successful = 0
    failed = 0

    try:
        with Pool(processes=8) as pool:
            results = list(tqdm(
                pool.imap_unordered(ingest_file, file_paths),
                total=len(file_paths),
                desc="Ingesting files"
            ))

        # Summarize results
        for file_path, success, result in results:
            if success:
                successful += 1
            else:
                failed += 1

        # Report summary
        print(f"\n{'='*60}")
        print(f"Ingestion Complete")
        print(f"{'='*60}")
        print(f"Successful: {successful}")
        print(f"Failed:     {failed}")
        print(f"Total:      {len(file_paths)}")
        print(f"{'='*60}")

        if failed > 0:
            print(f"\nErrors logged to: errors.log")

        sys.exit(0 if failed == 0 else 1)

    except KeyboardInterrupt:
        print("\nIngestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
