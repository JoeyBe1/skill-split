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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.parser import Parser
from core.detector import FormatDetector
from core.database import DatabaseStore
from core.hashing import compute_file_hash, compute_combined_hash
from core.validator import Validator
from core.recomposer import Recomposer
from core.query import QueryAPI
from models import FileFormat, FileType, Section

# Import HandlerFactory for script and component file handling
from handlers.factory import HandlerFactory

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
    supabase_key = _get_supabase_key()
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY (or SUPABASE_PUBLISHABLE_KEY) environment variables are required", file=sys.stderr)
        return None
    
    return SupabaseStore(supabase_url, supabase_key)


def _get_supabase_key():
    """Return Supabase key from supported environment variables."""
    return (
        os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("SUPABASE_SECRET_KEY")
    )


def cmd_parse(args) -> int:
    """Parse a file and display its structure."""
    file_path = args.file

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    with open(file_path) as f:
        content = f.read()

    # Try to use HandlerFactory for script and component files
    handler = None
    try:
        if HandlerFactory.is_supported(file_path):
            handler = HandlerFactory.create_handler(file_path)
    except (ValueError, FileNotFoundError):
        # File not supported or doesn't exist, fall back to parser
        pass

    if handler:
        # Use handler for script/component files
        doc = handler.parse()
        file_type = handler.get_file_type()
        file_format = handler.get_file_format()
    else:
        # Fall back to existing Parser for markdown files
        detector = FormatDetector()
        file_type, file_format = detector.detect(file_path, content)
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

    # Try to use HandlerFactory for script and component files
    handler = None
    try:
        if HandlerFactory.is_supported(file_path):
            handler = HandlerFactory.create_handler(file_path)
    except (ValueError, FileNotFoundError):
        # File not supported or doesn't exist, fall back to parser
        pass

    if handler:
        # Use handler for script/component files
        doc = handler.parse()
        file_type = handler.get_file_type()
        file_format = handler.get_file_format()
        result = handler.validate()
        errors = result.errors
        warnings = result.warnings
    else:
        # Fall back to existing Parser for markdown files
        detector = FormatDetector()
        file_type, file_format = detector.detect(file_path, content)
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

    # Try to use HandlerFactory for script and component files
    handler = None
    try:
        if HandlerFactory.is_supported(file_path):
            handler = HandlerFactory.create_handler(file_path)
    except (ValueError, FileNotFoundError):
        # File not supported or doesn't exist, fall back to parser
        pass

    if handler:
        # Use handler for script/component files
        doc = handler.parse()
        file_type = handler.get_file_type()
        file_format = handler.get_file_format()
    else:
        # Fall back to existing Parser for markdown files
        detector = FormatDetector()
        file_type, file_format = detector.detect(file_path, content)
        parser = Parser()
        doc = parser.parse(file_path, content, file_type, file_format)

    # Compute hash (combined for multi-file components)
    related_paths = []
    if handler and hasattr(handler, "get_related_files"):
        related_paths = handler.get_related_files()
    if related_paths:
        content_hash = compute_combined_hash(file_path, related_paths)
    else:
        content_hash = compute_file_hash(file_path)
    if not content_hash:
        print(f"Error: Unable to compute hash for {file_path}", file=sys.stderr)
        return 1

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

    id_map = _build_section_id_map(db_path, file_path)

    print(f"File: {file_path}")
    print()
    print("Sections:")
    _print_sections_with_ids(sections, indent=0, id_map=id_map)

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

    # Try to use HandlerFactory for script and component files
    handler = None
    try:
        if HandlerFactory.is_supported(file_path):
            handler = HandlerFactory.create_handler(file_path)
    except (ValueError, FileNotFoundError):
        # File not supported or doesn't exist, fall back to parser
        pass

    if handler:
        # Use handler for script/component files
        doc = handler.parse()
        file_type = handler.get_file_type()
        file_format = handler.get_file_format()
    else:
        # Fall back to existing Parser for markdown files
        detector = FormatDetector()
        file_type, file_format = detector.detect(file_path, content)
        parser = Parser()
        doc = parser.parse(file_path, content, file_type, file_format)

    # Compute hash (combined for multi-file components)
    related_paths = []
    if handler and hasattr(handler, "get_related_files"):
        related_paths = handler.get_related_files()
    if related_paths:
        content_hash = compute_combined_hash(file_path, related_paths)
    else:
        content_hash = compute_file_hash(file_path)
    if not content_hash:
        print(f"Error: Unable to compute hash for {file_path}", file=sys.stderr)
        return 1

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

    # Find all supported files in source directory
    source_path = Path(source_dir)
    files = []
    files.extend(source_path.glob("*.md"))
    files.extend(source_path.glob("**/*.md"))

    # Include handler-supported extensions (json + scripts)
    for ext in HandlerFactory.list_supported_extensions():
        files.extend(source_path.glob(f"*{ext}"))
        files.extend(source_path.glob(f"**/*{ext}"))

    # De-duplicate
    files = list({str(p): p for p in files}.values())

    if not files:
        print(f"No supported files found in {source_dir}")
        return 0

    # Parse and store each file
    detector = FormatDetector()
    parser = Parser()
    ingested_count = 0

    for file_path in files:
        try:
            with open(file_path) as f:
                content = f.read()

            # Try handler first for supported component/script files
            handler = None
            try:
                if HandlerFactory.is_supported(str(file_path)):
                    handler = HandlerFactory.create_handler(str(file_path))
            except (ValueError, FileNotFoundError):
                handler = None

            if handler:
                doc = handler.parse()
            else:
                # Detect format and type
                file_type, file_format = detector.detect(str(file_path), content)
                # Parse
                doc = parser.parse(str(file_path), content, file_type, file_format)

            # Compute hash
            related_paths = []
            if handler and hasattr(handler, "get_related_files"):
                related_paths = handler.get_related_files()
            if related_paths:
                content_hash = compute_combined_hash(str(file_path), related_paths)
            else:
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
    supabase_key = _get_supabase_key()

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY (or SUPABASE_PUBLISHABLE_KEY) environment variables are required", file=sys.stderr)
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
    file_path = None
    section_id = None
    if args.section_id is None:
        try:
            section_id = int(args.section_id_or_file)
        except ValueError:
            print("Error: Section ID must be an integer", file=sys.stderr)
            sys.exit(1)
    else:
        file_path = args.section_id_or_file
        section_id = args.section_id
    db_path = args.db or get_default_db_path()

    try:
        query_api = QueryAPI(db_path)
        section = query_api.get_section(section_id)

        if section is None:
            print(f"Error: Section {section_id} not found", file=sys.stderr)
            sys.exit(1)

        # Validate section belongs to file if file_path provided
        if file_path:
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT f.path
                    FROM sections s
                    JOIN files f ON s.file_id = f.id
                    WHERE s.id = ?
                    """,
                    (section_id,),
                )
                row = cursor.fetchone()
                if not row or row["path"] != file_path:
                    print(f"Error: Section {section_id} does not belong to {file_path}", file=sys.stderr)
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
    first_child = getattr(args, 'child', False)
    db_path = args.db or get_default_db_path()

    try:
        query_api = QueryAPI(db_path)
        section = query_api.get_next_section(section_id, file_path, first_child=first_child)

        if section is None:
            if first_child:
                print(f"No child subsection found after section {section_id}")
            else:
                print(f"No next section found after section {section_id}")
            return 0

        # Display section
        print(f"--- Section {section.title} (Level {section.level}) ---")
        print()
        print(section.content)
        print()

        return 0
    except Exception as e:
        print(f"Error getting next section: {e}", file=sys.stderr)
        return 1


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

        id_map = _build_section_id_map(db_path, file_path)

        # Display sections in tree format
        print(f"File: {file_path}")
        print()
        _print_sections_with_ids(sections, indent=0, id_map=id_map)

        return 0
    except Exception as e:
        print(f"Error listing sections: {e}", file=sys.stderr)
        sys.exit(1)


def _build_section_id_map(db_path: str, file_path: str) -> dict:
    """Build a mapping from section identity to ID for a specific file."""
    import sqlite3
    id_map = {}
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT s.id, s.title, s.level, s.line_start, s.line_end
            FROM sections s
            JOIN files f ON s.file_id = f.id
            WHERE f.path = ?
            """,
            (file_path,),
        )
        for row in cursor.fetchall():
            key = (row["title"], row["level"], row["line_start"], row["line_end"])
            id_map[key] = row["id"]
    return id_map


def _print_sections_with_ids(sections, indent: int, id_map: dict) -> None:
    """Print sections with IDs in tree format."""
    for section in sections:
        prefix = "  " * indent
        level_indicator = "#" * section.level
        key = (section.title, section.level, section.line_start, section.line_end)
        section_id = id_map.get(key, "?")
        print(f"{prefix}{level_indicator} [{section_id}] {section.title}")

        if section.children:
            _print_sections_with_ids(section.children, indent + 1, id_map)


def cmd_compose(args) -> int:
    """Compose new skill from section IDs."""
    _ensure_supabase_imports()

    section_ids_str = args.sections
    output_path = args.output
    title = args.title or ""
    description = args.description or ""
    upload = args.upload
    validate_flag = getattr(args, 'validate', True)  # Default to True
    enrich_flag = getattr(args, 'enrich', True)      # Default to True
    db_path = args.db or get_default_db_path()

    # Parse section IDs
    try:
        section_ids = [int(sid.strip()) for sid in section_ids_str.split(',')]
    except ValueError:
        print("Error: Section IDs must be comma-separated integers", file=sys.stderr)
        return 1

    if not section_ids:
        print("Error: At least one section ID is required", file=sys.stderr)
        return 1

    try:
        from core.skill_composer import SkillComposer

        # Create composer
        composer = SkillComposer(db_path)

        # Compose skill with validation and enrichment flags
        composed = composer.compose_from_sections(
            section_ids=section_ids,
            output_path=output_path,
            title=title,
            description=description,
            validate=validate_flag,
            enrich=enrich_flag
        )

        # Write to filesystem
        hash_val = composer.write_to_filesystem(composed)
        print(f"Composed skill written: {output_path}")
        print(f"Hash: {hash_val}")
        print(f"Sections: {len(composed.sections)}")

        # Upload to Supabase if requested
        if upload:
            supabase_store = _get_supabase_store()
            if not supabase_store:
                print("Warning: Supabase credentials not available, skipping upload", file=sys.stderr)
                return 0

            file_id = composer.upload_to_supabase(composed, supabase_store)
            print(f"Uploaded to Supabase: {file_id}")

        return 0

    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error composing skill: {str(e)}", file=sys.stderr)
        return 1


def cmd_search_semantic(args) -> int:
    """Search sections using semantic similarity (vector search)."""
    _ensure_supabase_imports()

    query = args.query
    limit = args.limit
    vector_weight = args.vector_weight
    db_path = args.db or get_default_db_path()

    # Validate vector weight
    if not (0.0 <= vector_weight <= 1.0):
        print("Error: vector_weight must be between 0.0 and 1.0", file=sys.stderr)
        return 1

    try:
        # Check if embeddings are enabled
        import os
        if os.getenv('ENABLE_EMBEDDINGS', 'false') != 'true':
            print("Info: Embeddings not enabled. Set ENABLE_EMBEDDINGS=true to use vector search", file=sys.stderr)
            print("Falling back to keyword search...", file=sys.stderr)
            # Fall back to keyword search
            from core.query import QueryAPI
            query_api = QueryAPI(db_path)
            results = query_api.search_sections(query)
            if not results:
                print(f"No sections found matching '{query}'")
                return 0

            print(f"Found {len(results)} section(s) matching '{query}' (keyword search):")
            print()
            print(f"{'ID':<6} {'Title':<40} {'Level':<6} {'File':<50}")
            print("-" * 110)
            for section_id, section, path in results:
                title = section.title[:37] + "..." if len(section.title) > 40 else section.title
                file_display = path[:47] + "..." if len(path) > 50 else path
                print(f"{section_id:<6} {title:<40} {section.level:<6} {file_display:<50}")
            return 0

        # Vector search enabled
        from core.hybrid_search import HybridSearch
        from core.query import QueryAPI

        supabase_store = _get_supabase_store()
        if not supabase_store:
            print("Error: Supabase credentials required for semantic search", file=sys.stderr)
            return 1

        # Get embedding service
        from core.embedding_service import EmbeddingService
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("Error: OPENAI_API_KEY required for semantic search", file=sys.stderr)
            return 1

        embedding_service = EmbeddingService(openai_key)
        query_api = QueryAPI(db_path)
        hybrid = HybridSearch(embedding_service, supabase_store, query_api)

        # Perform hybrid search
        results = hybrid.hybrid_search(query, limit, vector_weight)

        if not results:
            print(f"No sections found matching '{query}'")
            return 0

        # Display results
        print(f"Found {len(results)} section(s) matching '{query}' (semantic search, weight={vector_weight}):")
        print()
        print(f"{'Score':<8} {'ID':<6} {'Title':<40} {'Level':<6}")
        print("-" * 62)
        for section_id, score in results:
            section = query_api.get_section(section_id)
            if section:
                title = section.title[:37] + "..." if len(section.title) > 40 else section.title
                print(f"{score:<8.2f} {section_id:<6} {title:<40} {section.level:<6}")

        return 0

    except ImportError as e:
        print(f"Error: Vector search components not available: {str(e)}", file=sys.stderr)
        print("Ensure hybrid_search.py and embedding_service.py are implemented", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error performing semantic search: {str(e)}", file=sys.stderr)
        return 1


def cmd_search_sections_query(args) -> int:
    """Search sections by query across all files or a specific file using FTS5 BM25 ranking."""
    query = args.query
    file_path = args.file if hasattr(args, 'file') and args.file else None
    db_path = args.db or get_default_db_path()

    try:
        query_api = QueryAPI(db_path)

        # Get ranked results from FTS5
        ranked_results = query_api.search_sections_with_rank(query, file_path)

        if not ranked_results:
            if file_path:
                print(f"No sections found matching '{query}' in {file_path}")
            else:
                print(f"No sections found matching '{query}'")
            return 0

        # Display results with relevance scores
        print(f"Found {len(ranked_results)} section(s) matching '{query}':")
        print()

        if file_path:
            print(f"{'ID':<6} {'Score':<8} {'Title':<40} {'Level':<6}")
            print("-" * 62)
            for section_id, score in ranked_results:
                section = query_api.get_section(section_id)
                if section:
                    title = section.title[:37] + "..." if len(section.title) > 40 else section.title
                    print(f"{section_id:<6} {score:<8.2f} {title:<40} {section.level:<6}")
        else:
            import sqlite3
            print(f"{'ID':<6} {'Score':<8} {'Title':<40} {'Level':<6} {'File':<50}")
            print("-" * 113)
            for section_id, score in ranked_results:
                section = query_api.get_section(section_id)
                if section:
                    title = section.title[:37] + "..." if len(section.title) > 40 else section.title
                    # Get file path
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.execute(
                            "SELECT f.path FROM sections s JOIN files f ON s.file_id = f.id WHERE s.id = ?",
                            (section_id,)
                        )
                        row = cursor.fetchone()
                        path = row[0] if row else "unknown"
                    file_display = path[:47] + "..." if len(path) > 50 else path
                    print(f"{section_id:<6} {score:<8.2f} {title:<40} {section.level:<6} {file_display:<50}")

        return 0
    except Exception as e:
        print(f"Error searching sections: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_backup(args) -> int:
    """Create a database backup."""
    from core.backup_manager import BackupManager, BackupError

    db_path = args.db
    filename = args.filename

    try:
        manager = BackupManager()
        backup_path = manager.create_backup(db_path, filename)

        # Get file size info
        backup_stat = os.stat(backup_path)
        compressed_size = backup_stat.st_size

        print(f"Backup created: {backup_path}")
        print(f"Size: {compressed_size:,} bytes (compressed)")

        return 0
    except BackupError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_restore(args) -> int:
    """Restore database from backup."""
    from core.backup_manager import BackupManager, BackupError, IntegrityError

    backup_file = args.backup_file
    target_db_path = args.db
    overwrite = args.overwrite

    try:
        manager = BackupManager()

        # Warn if overwriting
        if Path(target_db_path).exists() and overwrite:
            print(f"Warning: Overwriting existing database: {target_db_path}")

        result = manager.restore_backup(backup_file, target_db_path, overwrite)

        print(f"Database restored: {target_db_path}")
        print(f"Files: {result['files_count']}")
        print(f"Sections: {result['sections_count']}")
        print(f"FTS5 index: {'OK' if result.get('fts5_exists', False) else 'MISSING'}")
        print(f"Integrity check: {'PASSED' if result['integrity_check_passed'] else 'FAILED'}")

        return 0
    except BackupError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IntegrityError as e:
        print(f"Integrity error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


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
    get_section_parser.add_argument("section_id_or_file", help="Section ID or file path")
    get_section_parser.add_argument("section_id", nargs="?", type=int, help="Section ID if file path provided")
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
        "--child",
        action="store_true",
        help="Navigate to first child subsection instead of next sibling"
    )
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

    # Compose command (skill composition)
    compose_parser = subparsers.add_parser(
        "compose", help="Compose new skill from section IDs"
    )
    compose_parser.add_argument("--sections", required=True, help="Comma-separated section IDs")
    compose_parser.add_argument("--output", required=True, help="Output file path")
    compose_parser.add_argument("--title", default="", help="Skill title (optional)")
    compose_parser.add_argument("--description", default="", help="Skill description (optional)")
    compose_parser.add_argument("--upload", action="store_true", help="Upload to Supabase after composition")
    compose_parser.add_argument("--validate", action=argparse.BooleanOptionalAction, default=True, help="Run strict validation (default: True)")
    compose_parser.add_argument("--enrich", action=argparse.BooleanOptionalAction, default=True, help="Force deep metadata extraction (default: True)")
    compose_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    compose_parser.set_defaults(func=cmd_compose)

    # Search-semantic command (vector search)
    search_semantic_parser = subparsers.add_parser(
        "search-semantic", help="Search sections using semantic similarity"
    )
    search_semantic_parser.add_argument("query", help="Search query")
    search_semantic_parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    search_semantic_parser.add_argument("--vector-weight", type=float, default=0.7, help="Vector score weight (0.0-1.0, default: 0.7)")
    search_semantic_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    search_semantic_parser.set_defaults(func=cmd_search_semantic)

    # Backup command
    backup_parser = subparsers.add_parser(
        "backup", help="Create a database backup"
    )
    backup_parser.add_argument(
        "--filename", "-f", help="Optional backup filename (default: auto-generated timestamp)"
    )
    backup_parser.add_argument(
        "--db", default=get_default_db_path(), help="Path to database to backup (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    backup_parser.set_defaults(func=cmd_backup)

    # Restore command
    restore_parser = subparsers.add_parser(
        "restore", help="Restore database from backup"
    )
    restore_parser.add_argument("backup_file", help="Path to backup file (.sql.gz)")
    restore_parser.add_argument(
        "--db", default=get_default_db_path(), help="Target database path (default: env SKILL_SPLIT_DB or ~/.claude/databases/skill-split.db)"
    )
    restore_parser.add_argument(
        "--overwrite", "-o", action="store_true", help="Overwrite existing database"
    )
    restore_parser.set_defaults(func=cmd_restore)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
