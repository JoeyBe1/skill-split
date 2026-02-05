#!/usr/bin/env python3
"""
skill-split - Intelligent Markdown/YAML Section Splitter

A Python tool that decomposes skill/command/reference files into discrete
sections stored in a database, enabling progressive disclosure.
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.parser import Parser
from core.detector import FormatDetector
from core.database import DatabaseStore
from core.hashing import compute_file_hash
from core.validator import Validator
from core.recomposer import Recomposer
from core.query import QueryAPI
from models import FileFormat, FileType

# Lazy imports for Supabase-dependent modules
# (to allow running core commands without Supabase installed)
SupabaseStore = None
CheckoutManager = None


def get_default_db_path():
    """Get database path from env var or use default location."""
    env_path = os.getenv("SKILL_SPLIT_DB")
    if env_path:
        return os.path.expanduser(env_path)
    # Check for Claude databases directory
    claude_db_dir = Path.home() / ".claude" / "databases"
    if claude_db_dir.exists():
        return str(claude_db_dir / "skill-split.db")
    # Fall back to current directory
    return "./skill_split.db"


def _ensure_supabase_imports():
    """Lazy load Supabase dependencies when needed."""
    global SupabaseStore, CheckoutManager
    if SupabaseStore is None:
        try:
            from core.supabase_store import SupabaseStore as SB
            from core.checkout_manager import CheckoutManager as CM
            SupabaseStore = SB
            CheckoutManager = CM
        except ImportError as e:
            print(f"Error: Supabase modules not available. {e}", file=sys.stderr)
            sys.exit(1)



def _get_supabase_store():
    """Get SupabaseStore instance from environment credentials.
    
    Returns:
        SupabaseStore instance if credentials are valid, None otherwise.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required", file=sys.stderr)
        return None
    
    return SupabaseStore(supabase_url, supabase_key)


def cmd_parse(args) -> int:
    """Parse a file and display its structure."""
    file_path = args.file

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    with open(file_path) as f:
        content = f.read()

    # Detect format and type
    detector = FormatDetector()
    file_type, file_format = detector.detect(file_path, content)

    # Parse
    parser = Parser()
    doc = parser.parse(file_path, content, file_type, file_format)

    # Display results
    print(f"File: {file_path}")
    print(f"Type: {file_type.value}")
    print(f"Format: {file_format.value}")
    print()

    if doc.frontmatter:
        print("Frontmatter:")
        print("---")
        print(doc.frontmatter)
        print("---")
        print()

    print("Sections:")
    _print_sections(doc.sections, indent=0)

    return 0


def _print_sections(sections, indent: int) -> None:
    """Print sections with indentation."""
    for section in sections:
        prefix = "  " * indent
        level_indicator = "#" * section.level
        print(f"{prefix}{level_indicator} {section.title}")
        print(f"{prefix}  Lines: {section.line_start}-{section.line_end}")

        if section.children:
            _print_sections(section.children, indent + 1)


def cmd_validate(args) -> int:
    """Validate a file's structure."""
    file_path = args.file

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    with open(file_path) as f:
        content = f.read()

    # Detect format and type
    detector = FormatDetector()
    file_type, file_format = detector.detect(file_path, content)

    # Parse
    parser = Parser()
    doc = parser.parse(file_path, content, file_type, file_format)

    # Basic validation
    errors = []
    warnings = []

    if not doc.sections:
        errors.append("No sections found in file")

    # Check for empty sections
    def check_empty(sections, path=""):
        for section in sections:
            full_path = f"{path}/{section.title}" if path else section.title
            if not section.content.strip() and not section.children:
                warnings.append(f"Empty section: {full_path}")
            check_empty(section.children, full_path)

    check_empty(doc.sections)

    # Report
    print(f"Validating: {file_path}")
    print(f"Type: {file_type.value}, Format: {file_format.value}")
    print()

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  ✗ {error}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    if not errors and not warnings:
        print("✓ No issues found")

    return 1 if errors else 0


def cmd_store(args) -> int:
    """Store a parsed file in the database."""
    file_path = args.file
    db_path = args.db or get_default_db_path()

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    with open(file_path) as f:
        content = f.read()

    # Compute hash
    content_hash = compute_file_hash(file_path)
    if not content_hash:
        print(f"Error: Unable to compute hash for {file_path}", file=sys.stderr)
        return 1

    # Detect format and type
    detector = FormatDetector()
    file_type, file_format = detector.detect(file_path, content)

    # Parse
    parser = Parser()
    doc = parser.parse(file_path, content, file_type, file_format)

    # Store in database
    store = DatabaseStore(db_path)
    try:
        file_id = store.store_file(file_path, doc, content_hash)
    except Exception as e:
        print(f"Error storing file: {e}", file=sys.stderr)
        return 1

    # Display results
    print(f"File: {file_path}")
    print(f"File ID: {file_id}")
    print(f"Hash: {content_hash}")
    print(f"Type: {file_type.value}")
    print(f"Format: {file_format.value}")
    print(f"Sections: {_count_sections(doc.sections)}")

    return 0


def cmd_get(args) -> int:
    """Retrieve a file from the database and display metadata."""
    file_path = args.file
    db_path = args.db or get_default_db_path()

    store = DatabaseStore(db_path)
    result = store.get_file(file_path)

    if result is None:
        print(f"Error: File not found in database: {file_path}", file=sys.stderr)
        return 1

    metadata, sections = result

    # Display results
    print(f"File: {metadata.path}")
    print(f"Type: {metadata.type.value}")
    print(f"Hash: {metadata.hash}")

    if metadata.frontmatter:
        print("Frontmatter:")
        print("---")
        print(metadata.frontmatter)
        print("---")

    print(f"Sections: {_count_sections(sections)}")

    return 0


def cmd_tree(args) -> int:
    """Show section hierarchy for a file in the database."""
    file_path = args.file
    db_path = args.db or get_default_db_path()

    store = DatabaseStore(db_path)
    sections = store.get_section_tree(file_path)

    if not sections:
        # File might not exist or have no sections
        result = store.get_file(file_path)
        if result is None:
            print(f"Error: File not found in database: {file_path}", file=sys.stderr)
            return 1
        print(f"File: {file_path}")
        print("(No sections)")
        return 0

    print(f"File: {file_path}")
    print()
    print("Sections:")
    _print_sections(sections, indent=0)

    return 0


def cmd_verify(args) -> int:
    """Verify a file by storing it and validating round-trip integrity."""
    file_path = args.file
    db_path = args.db or get_default_db_path()

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    with open(file_path) as f:
        content = f.read()

    # Compute hash
    content_hash = compute_file_hash(file_path)
    if not content_hash:
        print(f"Error: Unable to compute hash for {file_path}", file=sys.stderr)
        return 1

    # Detect format and type
    detector = FormatDetector()
    file_type, file_format = detector.detect(file_path, content)

    # Parse
    parser = Parser()
    doc = parser.parse(file_path, content, file_type, file_format)

    # Store in database (or update if exists)
    store = DatabaseStore(db_path)
    try:
        file_id = store.store_file(file_path, doc, content_hash)
    except Exception as e:
        print(f"Error storing file: {e}", file=sys.stderr)
        return 1

    # Run round-trip validation
    recomposer = Recomposer(store)
    validator = Validator(store, recomposer)
    result = validator.validate_round_trip(file_path)

    # Display results
    print(f"File: {file_path}")
    print(f"File ID: {file_id}")
    print(f"Type: {file_type.value}")
    print(f"Format: {file_format.value}")
    print()

    # Show validity status
    if result.is_valid:
        print("Valid")
    else:
        print("Invalid")

    print()

    # Show hashes
    print(f"original_hash:    {result.original_hash}")
    print(f"recomposed_hash:  {result.recomposed_hash}")
    print()

    # Show errors
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  {error}")
        print()

    # Show warnings
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  {warning}")

    # Return 0 if valid, 1 if invalid
    return 0 if result.is_valid else 1


def _count_sections(sections) -> int:
    """Count all sections recursively."""
    count = len(sections)
    for section in sections:
        count += _count_sections(section.children)
    return count


def cmd_ingest(args) -> int:
    """Parse files from directory and store in Supabase."""
    _ensure_supabase_imports()
    source_dir = args.source_dir

    if not Path(source_dir).exists():
        print(f"Error: Directory not found: {source_dir}", file=sys.stderr)
        return 1

    # Initialize store
    store = _get_supabase_store()
    if store is None:
        return 1

    # Find all markdown files in source directory
    source_path = Path(source_dir)
    md_files = list(source_path.glob("*.md")) + list(source_path.glob("**/*.md"))

    if not md_files:
        print(f"No markdown files found in {source_dir}")
        return 0

    # Parse and store each file
    detector = FormatDetector()
    parser = Parser()
    ingested_count = 0

    for file_path in md_files:
        try:
            with open(file_path) as f:
                content = f.read()

            # Detect format and type
            file_type, file_format = detector.detect(str(file_path), content)

            # Parse
            doc = parser.parse(str(file_path), content, file_type, file_format)

            # Compute hash
            content_hash = compute_file_hash(str(file_path))
            if not content_hash:
                print(f"Warning: Could not compute hash for {file_path}", file=sys.stderr)
                continue

            # Store in Supabase
            file_id = store.store_file(
                storage_path=str(file_path),
                name=file_path.stem,
                doc=doc,
                content_hash=content_hash
            )

            print(f"Stored: {file_path.name} (ID: {file_id})")
            ingested_count += 1

        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            continue

    print(f"\nIngested {ingested_count} files successfully")
    return 0


def cmd_checkout(args) -> int:
    """Checkout file to target path."""
    _ensure_supabase_imports()
    file_id = args.file_id
    target_path = args.target_path
    user = args.user

    # Get Supabase credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required", file=sys.stderr)
        return 1

    # Initialize store and manager
    store = SupabaseStore(supabase_url, supabase_key)
    manager = CheckoutManager(store)

    try:
        deployed_path = manager.checkout_file(
            file_id=file_id,
            user=user,
            target_path=target_path
        )
        print(f"File checked out to: {deployed_path}")
        return 0
    except Exception as e:
        print(f"Error checking out file: {e}", file=sys.stderr)
        return 1


def cmd_checkin(args) -> int:
    """Checkin file from target path."""
    _ensure_supabase_imports()
    target_path = args.target_path

    # Get Supabase credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required", file=sys.stderr)
        return 1

    # Initialize store and manager
    store = SupabaseStore(supabase_url, supabase_key)
    manager = CheckoutManager(store)

    try:
        manager.checkin(target_path)
        print(f"File checked in from: {target_path}")
        return 0
    except Exception as e:
        print(f"Error checking in file: {e}", file=sys.stderr)
        return 1


def cmd_list_library(args) -> int:
    """List files in library."""
    _ensure_supabase_imports()
    # Initialize store
    store = _get_supabase_store()
    if store is None:
        return 1

    try:
        files = store.get_all_files()

        if not files:
            print("No files in library")
            return 0

        # Print header
        print(f"{'Name':<30} {'Type':<15} {'Storage Path':<50} {'Checkout Status':<20}")
        print("-" * 115)

        # Print each file
        for file_data in files:
            name = file_data.get("name", "")
            file_type = file_data.get("type", "unknown")
            storage_path = file_data.get("storage_path", "")

            # Check if file has active checkout
            active_checkouts = store.get_active_checkouts()
            checkout_status = "checked out" if any(
                c.get("file_id") == file_data.get("id") for c in active_checkouts
            ) else "available"

            print(f"{name:<30} {file_type:<15} {storage_path:<50} {checkout_status:<20}")

        return 0
    except Exception as e:
        print(f"Error listing files: {e}", file=sys.stderr)
        return 1


def cmd_status(args) -> int:
    """Show active checkouts."""
    _ensure_supabase_imports()
    user = getattr(args, 'user', None)

    # Initialize store
    store = _get_supabase_store()
    if store is None:
        return 1

    try:
        checkouts = store.get_active_checkouts(user=user)

        if not checkouts:
            if user:
                print(f"No active checkouts for user: {user}")
            else:
                print("No active checkouts")
            return 0

        # Print header
        print(f"{'User':<20} {'File ID':<40} {'Target Path':<50} {'Status':<15}")
        print("-" * 125)

        # Print each checkout
        for checkout in checkouts:
            user_name = checkout.get("user_name", "")
            file_id = checkout.get("file_id", "")
            target_path = checkout.get("target_path", "")
            status = checkout.get("status", "active")

            print(f"{user_name:<20} {file_id:<40} {target_path:<50} {status:<15}")

        return 0
    except Exception as e:
        print(f"Error getting checkout status: {e}", file=sys.stderr)
        return 1


def cmd_search_library(args) -> int:
    """Search files by query."""
    _ensure_supabase_imports()
    query = args.query

    # Initialize store
    store = _get_supabase_store()
    if store is None:
        return 1

    try:
        results = store.search_files(query)

        if not results:
            print(f"No files found matching: {query}")
            return 0

        # Print header
        print(f"Found {len(results)} file(s) matching '{query}':")
        print()
        print(f"{'Name':<30} {'Type':<15} {'Storage Path':<50}")
        print("-" * 95)

        # Print each result
        for file_data in results:
            name = file_data.get("name", "")
            file_type = file_data.get("type", "unknown")
            storage_path = file_data.get("storage_path", "")

            print(f"{name:<30} {file_type:<15} {storage_path:<50}")

        return 0
    except Exception as e:
        print(f"Error searching files: {e}", file=sys.stderr)
        return 1


def cmd_get_section(args) -> int:
    """Retrieve and display a single section by ID."""
    file_path = args.file
    section_id = args.section_id
    db_path = args.db or get_default_db_path()

    try:
        query_api = QueryAPI(db_path)
        section = query_api.get_section(section_id)

        if section is None:
            print(f"Error: Section {section_id} not found", file=sys.stderr)
            sys.exit(1)

        # Display section
        print(f"Section {section_id}: {section.title}")
        print(f"Level: {section.level}")
        print(f"Lines: {section.line_start}-{section.line_end}")
        print()
        print(section.content)

        return 0
    except Exception as e:
        print(f"Error retrieving section: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_next(args) -> int:
    """Retrieve and display the next section after given ID."""
    file_path = args.file
    section_id = args.section_id
    db_path = args.db or get_default_db_path()

    try:
        query_api = QueryAPI(db_path)
        section = query_api.get_next_section(section_id, file_path)

        if section is None:
            print(f"No next section found after ID {section_id}", file=sys.stderr)
            sys.exit(1)

        # Display section
        print(f"Next Section: {section.title}")
        print(f"Level: {section.level}")
        print(f"Lines: {section.line_start}-{section.line_end}")
        print()
        print(section.content)

        return 0
    except Exception as e:
        print(f"Error retrieving next section: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list_sections(args) -> int:
    """List all sections in a file with IDs and titles."""
    file_path = args.file
    db_path = args.db or get_default_db_path()

    try:
        query_api = QueryAPI(db_path)
        sections = query_api.get_section_tree(file_path)

        if not sections:
            print(f"No sections found for file: {file_path}")
            return 0

        # Display sections in tree format
        print(f"File: {file_path}")
        print()
        _print_sections_with_ids(sections, indent=0, db_path=db_path)

        return 0
    except Exception as e:
        print(f"Error listing sections: {e}", file=sys.stderr)
        sys.exit(1)


def _print_sections_with_ids(sections, indent: int, db_path: str) -> None:
    """Print sections with IDs in tree format."""
    # Get section IDs from database
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT id, title FROM sections WHERE parent_id IS NULL")
        id_map = {row["title"]: row["id"] for row in cursor.fetchall()}

    for section in sections:
        prefix = "  " * indent
        level_indicator = "#" * section.level
        section_id = id_map.get(section.title, "?")
        print(f"{prefix}{level_indicator} [{section_id}] {section.title}")

        if section.children:
            _print_sections_with_ids(section.children, indent + 1, db_path)


def cmd_search_sections_query(args) -> int:
    """Search sections by query across all files or a specific file."""
    query = args.query
    file_path = args.file if hasattr(args, 'file') and args.file else None
    db_path = args.db or get_default_db_path()

    try:
        query_api = QueryAPI(db_path)
        results = query_api.search_sections(query, file_path)

        if not results:
            if file_path:
                print(f"No sections found matching '{query}' in {file_path}")
            else:
                print(f"No sections found matching '{query}'")
            return 0

        # Display results
        print(f"Found {len(results)} section(s) matching '{query}':")
        print()
        print(f"{'ID':<6} {'Title':<40} {'Level':<6}")
        print("-" * 52)

        for section_id, section in results:
            title = section.title[:37] + "..." if len(section.title) > 40 else section.title
            print(f"{section_id:<6} {title:<40} {section.level:<6}")

        return 0
    except Exception as e:
        print(f"Error searching sections: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="skill-split - Intelligent Markdown/YAML Section Splitter",
        prog="skill-split",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Parse command
    parse_parser = subparsers.add_parser(
        "parse", help="Parse a file and display its structure"
    )
    parse_parser.add_argument("file", help="Path to the file to parse")
    parse_parser.set_defaults(func=cmd_parse)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate a file's structure"
    )
    validate_parser.add_argument("file", help="Path to the file to validate")
    validate_parser.set_defaults(func=cmd_validate)

    # Store command
    store_parser = subparsers.add_parser(
        "store", help="Parse file and store in database"
    )
    store_parser.add_argument("file", help="Path to the file to store")
    store_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    store_parser.set_defaults(func=cmd_store)

    # Get command
    get_parser = subparsers.add_parser(
        "get", help="Retrieve file from database"
    )
    get_parser.add_argument("file", help="Path to the file to retrieve")
    get_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    get_parser.set_defaults(func=cmd_get)

    # Tree command
    tree_parser = subparsers.add_parser(
        "tree", help="Show section hierarchy for file in database"
    )
    tree_parser.add_argument("file", help="Path to the file")
    tree_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    tree_parser.set_defaults(func=cmd_tree)

    # Verify command
    verify_parser = subparsers.add_parser(
        "verify", help="Store file and verify round-trip integrity"
    )
    verify_parser.add_argument("file", help="Path to the file to verify")
    verify_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    verify_parser.set_defaults(func=cmd_verify)

    # Ingest command
    ingest_parser = subparsers.add_parser(
        "ingest", help="Parse and store files from directory"
    )
    ingest_parser.add_argument("source_dir", help="Path to directory containing files to ingest")
    ingest_parser.set_defaults(func=cmd_ingest)

    # Checkout command
    checkout_parser = subparsers.add_parser(
        "checkout", help="Checkout file to target path"
    )
    checkout_parser.add_argument("file_id", help="UUID of file to checkout")
    checkout_parser.add_argument("target_path", help="Target path to deploy file to")
    checkout_parser.add_argument("--user", default="unknown", help="Username checking out the file")
    checkout_parser.set_defaults(func=cmd_checkout)

    # Checkin command
    checkin_parser = subparsers.add_parser(
        "checkin", help="Checkin file from target path"
    )
    checkin_parser.add_argument("target_path", help="Path where file is currently deployed")
    checkin_parser.set_defaults(func=cmd_checkin)

    # List-library command
    list_library_parser = subparsers.add_parser(
        "list-library", help="List files in library"
    )
    list_library_parser.set_defaults(func=cmd_list_library)

    # Status command
    status_parser = subparsers.add_parser(
        "status", help="Show active checkouts"
    )
    status_parser.add_argument("--user", help="Filter by username (optional)")
    status_parser.set_defaults(func=cmd_status)

    # Search-library command
    search_library_parser = subparsers.add_parser(
        "search-library", help="Search files by query"
    )
    search_library_parser.add_argument("query", help="Search query")
    search_library_parser.set_defaults(func=cmd_search_library)

    # Get-section command (query)
    get_section_parser = subparsers.add_parser(
        "get-section", help="Display single section content by ID"
    )
    get_section_parser.add_argument("file", help="Path to the file")
    get_section_parser.add_argument("section_id", type=int, help="Section ID to retrieve")
    get_section_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    get_section_parser.set_defaults(func=cmd_get_section)

    # Next command (query)
    next_parser = subparsers.add_parser(
        "next", help="Display next section after given ID"
    )
    next_parser.add_argument("file", help="Path to the file")
    next_parser.add_argument("section_id", type=int, help="Current section ID")
    next_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    next_parser.set_defaults(func=cmd_next)

    # List command (query - sections in file)
    list_sections_parser = subparsers.add_parser(
        "list", help="List all sections with IDs and titles"
    )
    list_sections_parser.add_argument("file", help="Path to the file")
    list_sections_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    list_sections_parser.set_defaults(func=cmd_list_sections)

    # Search command (query - sections)
    search_sections_parser = subparsers.add_parser(
        "search", help="Search section content across files"
    )
    search_sections_parser.add_argument("query", help="Search query")
    search_sections_parser.add_argument(
        "--file", default=None, help="Limit search to specific file (optional)"
    )
    search_sections_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    search_sections_parser.set_defaults(func=cmd_search_sections_query)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
