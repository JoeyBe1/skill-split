#!/usr/bin/env python3
"""
Bulk ingest all files from skill-split database to Supabase.

Reads all file paths from the files table in the local database and
runs the ingest command for each one, tracking success/errors.
"""

import subprocess
import sqlite3
import sys
from pathlib import Path
from tqdm import tqdm
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Setup logging
log_file = "errors.log"
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


def get_db_path():
    """Get database path from environment or default."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    env_path = os.getenv("SKILL_SPLIT_DB")
    if env_path:
        return os.path.expanduser(env_path)

    claude_db_dir = Path.home() / ".claude" / "databases"
    if claude_db_dir.exists():
        return str(claude_db_dir / "skill-split.db")

    return "./skill_split.db"


def get_all_file_paths(db_path):
    """Read all file paths from the files table."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT path FROM files ORDER BY id")
        paths = [row[0] for row in cursor.fetchall()]
        conn.close()
        return paths
    except Exception as e:
        logger.error(f"Failed to read database {db_path}: {e}")
        print(f"Error: Cannot read database: {e}", file=sys.stderr)
        return []


def ingest_file(file_path):
    """
    Run skill_split.py ingest {file_path} for a single file.

    Returns tuple: (success: bool, error_msg: str or None)
    """
    try:
        # Get the directory containing the file
        source_dir = str(Path(file_path).parent)

        # Run ingest command
        result = subprocess.run(
            ["python3", "./skill_split.py", "ingest", source_dir],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for large files + Supabase latency
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            return False, error_msg

        return True, None

    except subprocess.TimeoutExpired:
        error_msg = f"Timeout (300s) ingesting {file_path}"
        return False, error_msg
    except Exception as e:
        error_msg = f"Exception ingesting {file_path}: {e}"
        return False, error_msg


def main():
    """Main bulk ingest workflow."""
    db_path = get_db_path()

    # Verify database exists
    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}", file=sys.stderr)
        return 1

    print(f"Reading file paths from: {db_path}")

    # Get all file paths from database
    file_paths = get_all_file_paths(db_path)

    if not file_paths:
        print("No files found in database.", file=sys.stderr)
        return 1

    print(f"Found {len(file_paths)} files to ingest")
    print(f"Logging errors to: {log_file}\n")

    # Track progress
    success_count = 0
    error_count = 0
    errors = []

    # Process each file with progress bar
    for file_path in tqdm(file_paths, desc="Ingesting files", unit="file"):
        # Skip if file doesn't exist
        if not Path(file_path).exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            errors.append((file_path, error_msg))
            error_count += 1
            continue

        # Ingest file
        success, error_msg = ingest_file(file_path)

        if success:
            success_count += 1
        else:
            error_count += 1
            logger.error(f"{file_path}: {error_msg}")
            errors.append((file_path, error_msg))

    # Print summary
    print(f"\n{'='*60}")
    print(f"Bulk Ingest Complete")
    print(f"{'='*60}")
    print(f"Total files:      {len(file_paths)}")
    print(f"Successful:       {success_count}")
    print(f"Failed:           {error_count}")
    print(f"Success rate:     {100*success_count/len(file_paths):.1f}%")
    print(f"Log file:         {log_file}")

    if error_count > 0:
        print(f"\nFirst 10 errors:")
        for file_path, error_msg in errors[:10]:
            print(f"  - {Path(file_path).name}: {error_msg[:80]}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more (see {log_file})")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
