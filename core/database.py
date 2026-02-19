"""
Database storage for skill-split.

This module provides the DatabaseStore class which handles all SQLite
database operations for storing parsed files and their sections.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any, Callable

from models import FileMetadata, Section, ParsedDocument, FileType


class DatabaseStore:
    """
    SQLite database store for parsed documents and sections.

    Implements a hierarchical storage model where files contain sections,
    and sections can have parent-child relationships.
    """

    def __init__(self, db_path: str) -> None:
        """
        Initialize the database store.

        Args:
            db_path: Path to SQLite database file (will be created if needed)
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._create_schema()

    @property
    def conn(self) -> sqlite3.Connection:
        """
        Lazily-initialized connection for compatibility with integration tests.
        """
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def __enter__(self) -> "DatabaseStore":
        """
        Context manager support for DatabaseStore.
        """
        _ = self.conn
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """
        Close any opened connection when leaving context.
        """
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _create_schema(self) -> None:
        """
        Create database tables if they don't exist.

        Creates the files and sections tables with proper indexes
        and foreign key constraints.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    frontmatter TEXT,
                    hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    parent_id INTEGER,
                    level INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    order_index INTEGER NOT NULL,
                    line_start INTEGER NOT NULL,
                    line_end INTEGER NOT NULL,
                    closing_tag_prefix TEXT DEFAULT '',
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_id) REFERENCES sections(id) ON DELETE CASCADE
                )
                """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sections_file ON sections(file_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sections_parent ON sections(parent_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_type ON files(type)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    user TEXT NOT NULL DEFAULT 'unknown',
                    target_path TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    notes TEXT DEFAULT '',
                    checked_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    returned_at TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_checkouts_file ON checkouts(file_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_checkouts_target ON checkouts(target_path)"
            )

            # Create FTS5 virtual table for full-text search
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
                    title,
                    content,
                    content=sections,
                    content_rowid=id
                )
                """
            )

            # Populate FTS table with existing data (only on new creation)
            conn.execute(
                """
                INSERT INTO sections_fts(rowid, title, content)
                SELECT id, title, content FROM sections
                WHERE NOT EXISTS (SELECT 1 FROM sections_fts WHERE sections_fts.rowid = sections.id)
                """
            )

            conn.commit()

    def store_file(
        self, file_path: str, doc: ParsedDocument, content_hash: str
    ) -> int:
        """
        Store a file and its sections in the database with FTS5 synchronization.

        Handles duplicate paths by updating existing records.

        Args:
            file_path: Path to the file
            doc: ParsedDocument containing sections and metadata
            content_hash: SHA256 hash of original file content

        Returns:
            The file_id of the stored/updated file

        Raises:
            sqlite3.Error: On database error
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Insert or update file record
            conn.execute(
                """
                INSERT INTO files (path, type, frontmatter, hash, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(path) DO UPDATE SET
                    type = excluded.type,
                    frontmatter = excluded.frontmatter,
                    hash = excluded.hash,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (file_path, doc.file_type.value, doc.frontmatter, content_hash),
            )

            # Get the file_id (works for both INSERT and UPDATE cases)
            cursor = conn.execute(
                "SELECT id FROM files WHERE path = ?",
                (file_path,)
            )
            row = cursor.fetchone()
            file_id = row[0]

            # Delete existing sections for this file (cascade delete handles children)
            conn.execute("DELETE FROM sections WHERE file_id = ?", (file_id,))

            # Store sections recursively (already includes FTS sync)
            self._store_sections(conn, file_id, doc.sections, parent_id=None)

            # FINAL FTS SYNC to ensure complete index
            self._ensure_fts_sync(conn)

            conn.commit()
            return file_id

    def _store_sections(
        self,
        conn: sqlite3.Connection,
        file_id: int,
        sections: List[Section],
        parent_id: Optional[int],
        order_start: int = 0,
    ) -> None:
        """
        Recursively store sections in the database with FTS5 synchronization.

        Args:
            conn: Database connection (within transaction)
            file_id: ID of the parent file
            sections: List of sections to store
            parent_id: ID of parent section (None for top-level)
            order_start: Starting order index for this batch
        """
        for order_index, section in enumerate(sections, start=order_start):
            cursor = conn.execute(
                """
                INSERT INTO sections (
                    file_id, parent_id, level, title, content,
                    order_index, line_start, line_end, closing_tag_prefix
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    parent_id,
                    section.level,
                    section.title,
                    section.content,
                    order_index,
                    section.line_start,
                    section.line_end,
                    section.closing_tag_prefix,
                ),
            )
            section_id = cursor.lastrowid

            # Recursively store children
            if section.children:
                self._store_sections(conn, file_id, section.children, section_id)

            # Sync FTS table for this section
            self._sync_section_fts(conn, file_id, section)

        # ENSURE FTS SYNC after bulk insert
        # This guarantees FTS index is up-to-date for new sections
        self._ensure_fts_sync(conn)

    def _sync_section_fts(
        self,
        conn: sqlite3.Connection,
        file_id: int,
        section: Section,
        parent_id: Optional[int] = None
    ) -> None:
        """
        Sync a single section to FTS table.

        Args:
            conn: Database connection (within transaction)
            file_id: ID of the parent file
            section: Section to sync
            parent_id: ID of parent section (None for top-level)
        """
        # Get section_id from last insert or query
        cursor = conn.execute(
            "SELECT id FROM sections WHERE file_id = ? AND title = ? AND line_start = ?",
            (file_id, section.title, section.line_start)
        )
        row = cursor.fetchone()
        if row:
            section_id = row[0]
            conn.execute(
                "INSERT OR REPLACE INTO sections_fts(rowid, title, content) VALUES (?, ?, ?)",
                (section_id, section.title, section.content)
            )
        # Recursively sync children
        if section.children:
            for child in section.children:
                self._sync_section_fts(conn, file_id, child, section_id)

    def _ensure_fts_sync(self, conn: sqlite3.Connection) -> None:
        """
        Ensure FTS5 index is synchronized with main sections table.

        FTS5 external content tables can become out of sync during bulk
        operations or CASCADE deletes. This forces an explicit sync.

        Args:
            conn: Active database connection
        """
        try:
            # FTS5 'optimize' command rebuilds index ensuring sync
            conn.execute("INSERT INTO sections_fts(sections_fts) VALUES('optimize')")
        except Exception:
            # Optimize may fail if index is empty, ignore
            pass

    def _sync_single_section_fts(self, conn: sqlite3.Connection, section_id: int) -> None:
        """
        Synchronize a single section's FTS5 entry.

        Ensures FTS index contains current section data after updates.

        Args:
            conn: Active database connection
            section_id: Section ID to synchronize
        """
        # FTS5 external content auto-syncs on INSERT/UPDATE
        # This ensures explicit sync after potential issues
        conn.execute(
            """
            INSERT INTO sections_fts(rowid, title, content)
            SELECT id, title, content
            FROM sections
            WHERE id = ?
            ON CONFLICT(rowid) DO UPDATE SET
                title = excluded.title,
                content = excluded.content
            """,
            (section_id,)
        )

    def get_file(
        self, file_path: str
    ) -> Optional[Tuple[FileMetadata, List[Section]]]:
        """
        Retrieve a file with its sections from the database.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (FileMetadata, List[Section]) if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get file metadata
            cursor = conn.execute(
                """
                SELECT id, path, type, frontmatter, hash
                FROM files WHERE path = ?
                """,
                (file_path,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            file_id = row["id"]
            metadata = FileMetadata(
                path=row["path"],
                type=FileType(row["type"]),
                frontmatter=row["frontmatter"],
                hash=row["hash"],
            )

            # Get all sections for this file
            cursor = conn.execute(
                """
                SELECT id, parent_id, level, title, content,
                       order_index, line_start, line_end, closing_tag_prefix
                FROM sections
                WHERE file_id = ?
                ORDER BY order_index
                """,
                (file_id,),
            )
            rows = cursor.fetchall()

            # Build section tree
            sections = self._build_section_tree(rows)

            return metadata, sections

    def get_section(self, section_id: int) -> Optional[Section]:
        """
        Get a single section by ID with file_type metadata.

        Args:
            section_id: ID of the section

        Returns:
            Section object with file_id and file_type populated if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT s.level, s.title, s.content, s.line_start, s.line_end,
                       s.closing_tag_prefix, s.file_id, f.type as file_type
                FROM sections s
                JOIN files f ON s.file_id = f.id
                WHERE s.id = ?
                """,
                (section_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return Section(
                level=row["level"],
                title=row["title"],
                content=row["content"],
                line_start=row["line_start"],
                line_end=row["line_end"],
                closing_tag_prefix=row["closing_tag_prefix"] if "closing_tag_prefix" in row.keys() else "",
                file_id=str(row["file_id"]),
                file_type=FileType(row["file_type"]),
            )

    def get_section_tree(self, file_path: str) -> List[Section]:
        """
        Get hierarchical section tree for a file.

        Returns sections in their parent-child hierarchy
        with the children attribute populated.

        Args:
            file_path: Path to the file

        Returns:
            List of top-level Section objects with populated children
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT f.id AS file_id
                FROM files f
                WHERE f.path = ?
                """,
                (file_path,),
            )
            row = cursor.fetchone()

            if not row:
                return []

            file_id = row["file_id"]

            cursor = conn.execute(
                """
                SELECT id, parent_id, level, title, content,
                       order_index, line_start, line_end
                FROM sections
                WHERE file_id = ?
                ORDER BY order_index
                """,
                (file_id,),
            )
            rows = cursor.fetchall()

            return self._build_section_tree(rows)

    def _build_section_tree(self, rows: List[sqlite3.Row]) -> List[Section]:
        """
        Build hierarchical section tree from flat database rows.

        Args:
            rows: List of database rows from sections table

        Returns:
            List of top-level Section objects with populated children
        """
        sections_by_id: dict[int, Section] = {}
        root_sections: List[Section] = []

        # First pass: create all Section objects
        for row in rows:
            # Handle closing_tag_prefix - may not exist in old databases
            prefix = row["closing_tag_prefix"] if "closing_tag_prefix" in row.keys() else ""
            
            section = Section(
                level=row["level"],
                title=row["title"],
                content=row["content"],
                line_start=row["line_start"],
                line_end=row["line_end"],
                closing_tag_prefix=prefix,
            )
            sections_by_id[row["id"]] = section

        # Second pass: build parent-child relationships
        for row in rows:
            section = sections_by_id[row["id"]]
            parent_id = row["parent_id"]

            if parent_id is None:
                root_sections.append(section)
            else:
                parent = sections_by_id.get(parent_id)
                if parent:
                    parent.add_child(section)

        return root_sections

    def get_next_section(
        self, section_id: int, file_id: int
    ) -> Optional[Section]:
        """
        Get next section for progressive disclosure.

        Finds the section that follows the given section_id in the file,
        respecting the hierarchical order (by order_index within same parent).

        Args:
            section_id: Current section ID
            file_id: File ID to search within

        Returns:
            Section object with file_type populated if next section exists, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get current section's order_index and parent_id
            cursor = conn.execute(
                """
                SELECT parent_id, order_index
                FROM sections
                WHERE id = ? AND file_id = ?
                """,
                (section_id, file_id),
            )
            current = cursor.fetchone()

            if not current:
                return None

            # Find next section by order_index within same file and parent
            cursor = conn.execute(
                """
                SELECT s.id, s.level, s.title, s.content, s.line_start, s.line_end,
                       s.closing_tag_prefix, s.file_id, f.type as file_type
                FROM sections s
                JOIN files f ON s.file_id = f.id
                WHERE s.file_id = ?
                  AND (s.parent_id IS NULL AND ? IS NULL OR s.parent_id = ?)
                  AND s.order_index > ?
                ORDER BY s.order_index ASC
                LIMIT 1
                """,
                (file_id, current["parent_id"], current["parent_id"], current["order_index"]),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return Section(
                level=row["level"],
                title=row["title"],
                content=row["content"],
                line_start=row["line_start"],
                line_end=row["line_end"],
                closing_tag_prefix=row["closing_tag_prefix"] if "closing_tag_prefix" in row.keys() else "",
                file_id=str(row["file_id"]),
                file_type=FileType(row["file_type"]),
            )

    def search_sections(
        self, query: str, file_path: Optional[str] = None
    ) -> List[Tuple[int, Section]]:
        """
        Search sections by title/content.

        Performs case-insensitive search across section titles and content.
        If file_path is provided, restricts search to that file.

        Args:
            query: Search query string
            file_path: Optional file path to restrict search to

        Returns:
            List of (section_id, Section) tuples matching the query
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Build query with search conditions
            if file_path:
                # First get file_id from path
                cursor = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    (file_path,)
                )
                file_row = cursor.fetchone()
                if not file_row:
                    return []
                file_id = file_row["id"]

                cursor = conn.execute(
                    """
                    SELECT s.id, s.level, s.title, s.content, s.line_start, s.line_end,
                           s.closing_tag_prefix, s.file_id, f.type as file_type
                    FROM sections s
                    JOIN files f ON s.file_id = f.id
                    WHERE s.file_id = ?
                      AND (s.title LIKE ? OR s.content LIKE ?)
                    ORDER BY s.file_id, s.order_index
                    """,
                    (file_id, f"%{query}%", f"%{query}%"),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT s.id, s.level, s.title, s.content, s.line_start, s.line_end,
                           s.closing_tag_prefix, s.file_id, f.type as file_type
                    FROM sections s
                    JOIN files f ON s.file_id = f.id
                    WHERE s.title LIKE ? OR s.content LIKE ?
                    ORDER BY s.file_id, s.order_index
                    """,
                    (f"%{query}%", f"%{query}%"),
                )

            results = []
            for row in cursor.fetchall():
                section = Section(
                    level=row["level"],
                    title=row["title"],
                    content=row["content"],
                    line_start=row["line_start"],
                    line_end=row["line_end"],
                    closing_tag_prefix=row["closing_tag_prefix"] if "closing_tag_prefix" in row.keys() else "",
                    file_id=str(row["file_id"]),
                    file_type=FileType(row["file_type"]),
                )
                results.append((row["id"], section))

            return results

    @staticmethod
    def preprocess_fts5_query(query: str) -> str:
        """
        Convert natural language query to optimal FTS5 MATCH syntax.

        Rules:
        1. Empty/whitespace: return empty string
        2. User provided AND/OR/NEAR: use as-is (user knows FTS5 syntax)
        3. Quoted phrase "exact words": use as-is (phrase search)
        4. Single word: direct match
        5. Multi-word unquoted: convert to OR for broader discovery

        Args:
            query: Raw user search query

        Returns:
            FTS5 MATCH syntax string

        Examples:
            "python" → "python"
            "python handler" → "python" OR "handler"
            '"python handler"' → '"python handler"' (phrase search)
            "python AND handler" → "python AND handler" (user operator)
            "python OR handler" → "python OR handler" (user operator)

        Why OR for multi-word: FTS5 default is implicit AND (both words required).
            OR provides better discovery - users expect "setup git" to find
            sections about setup OR git, not only sections mentioning both.
        """
        if not query:
            return ""

        # Normalize whitespace
        query = ' '.join(query.split())

        if not query:
            return ""

        query_lower = query.lower()

        # Check for user-provided FTS5 operators (case-insensitive)
        # If user knows FTS5 syntax, respect their intent and normalize to uppercase
        fts5_operators = [' and ', ' or ', ' near ']
        has_operator = any(op in query_lower for op in fts5_operators)

        if has_operator:
            # Normalize operators to uppercase for consistency
            result = query_lower.replace(' and ', ' AND ').replace(' or ', ' OR ').replace(' near ', ' NEAR ')
            return result

        # Check for quoted phrase search
        if query.startswith('"') and query.endswith('"'):
            # Quoted phrase - use as-is for exact phrase matching
            return query

        # Check for single word
        if ' ' not in query:
            # Single word - check for special characters that need quoting
            # FTS5 treats certain characters as operators (-, *, ", etc.)
            special_chars = set('-*"\'<>')
            if any(char in query for char in special_chars):
                return f'"{query}"'
            return query

        # Multi-word unquoted: convert to OR for discovery
        # "setup git" → "setup" OR "git"
        # This finds sections with EITHER word, not just both
        words = query.split()

        # Quote each word for exact matching (handles special chars)
        or_terms = ' OR '.join(f'"{w}"' for w in words)

        return or_terms

    def search_sections_with_rank(
        self, query: str, file_path: Optional[str] = None
    ) -> List[Tuple[int, float]]:
        """
        Search sections using FTS5 full-text search with relevance ranking.

        Uses BM25 algorithm for ranking based on term frequency and
        inverse document frequency. Returns results with relevance scores
        where higher = more relevant.

        Query preprocessing converts natural language to FTS5 syntax:
        - Multi-word queries use OR for discovery
        - Quoted phrases use exact phrase matching
        - User-provided AND/OR/NEAR operators are respected

        Args:
            query: Search string (natural language or FTS5 MATCH syntax)
            file_path: Optional file path to limit search to one file

        Returns:
            List of (section_id, rank) tuples where rank is negative BM25 score
            (higher values = more relevant, so we negate for compatibility)
        """
        # Preprocess query for optimal FTS5 syntax
        processed_query = self.preprocess_fts5_query(query)

        # Handle empty query after preprocessing
        if not processed_query:
            return []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if file_path:
                # Single file search with FTS
                cursor = conn.execute(
                    """
                    SELECT s.id, bm25(sections_fts) as rank
                    FROM sections_fts
                    JOIN sections s ON sections_fts.rowid = s.id
                    JOIN files f ON s.file_id = f.id
                    WHERE sections_fts MATCH ? AND f.path = ?
                    ORDER BY rank
                    """,
                    (processed_query, file_path)
                )
            else:
                # Cross-file search with FTS
                cursor = conn.execute(
                    """
                    SELECT s.id, bm25(sections_fts) as rank
                    FROM sections_fts
                    JOIN sections s ON sections_fts.rowid = s.id
                    WHERE sections_fts MATCH ?
                    ORDER BY rank
                    """,
                    (processed_query,)
                )

            # Return (section_id, normalized_rank) tuples
            # BM25 returns negative scores, negate for "higher = better"
            results = [(row["id"], -row["rank"]) for row in cursor.fetchall()]
            return results

    def delete_file(self, file_id: int) -> bool:
        """
        Delete a file and all its sections with FTS cleanup.

        CASCADE delete removes sections, and FTS5 external content table
        should automatically clean up. We verify and clean any orphans.

        Args:
            file_id: File ID to delete

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Check file exists
            cursor = conn.execute("SELECT id FROM files WHERE id = ?", (file_id,))
            if not cursor.fetchone():
                return False

            # Delete file (CASCADE deletes sections)
            # FTS5 external content table should auto-cleanup when sections are deleted
            conn.execute("DELETE FROM files WHERE id = ?", (file_id,))

            # Verify no orphaned FTS entries remain and clean if needed
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM sections_fts
                WHERE rowid NOT IN (SELECT id FROM sections)
                """
            )

            orphaned = cursor.fetchone()[0]

            # Clean up any remaining orphans (safety for FTS5 external content)
            if orphaned > 0:
                # Use a simple delete without subquery for orphans
                conn.execute(
                    """
                    DELETE FROM sections_fts
                    WHERE rowid NOT IN (SELECT id FROM sections)
                    """
                )

            conn.commit()
            return True

    def get_all_files(self) -> List[Dict]:
        """List all files in the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, path, type, frontmatter, hash, created_at, updated_at FROM files ORDER BY path"
            )
            result = []
            for row in cursor.fetchall():
                d = dict(row)
                d["name"] = Path(d["path"]).stem
                d["storage_path"] = d["path"]
                result.append(d)
            return result

    def get_file_by_path(self, path: str):
        """Get a file by its path, returning (metadata, sections) tuple or None."""
        return self.get_file(path)

    def get_file_by_id(self, file_id: int):
        """Get a file by its integer ID, returning (metadata, sections) tuple or None."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, path, type, frontmatter, hash FROM files WHERE id = ?",
                (file_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            # Delegate to get_file using the path
            return self.get_file(row["path"])

    def checkout_file(self, file_id, user: str, target_path: str, notes: str = "") -> int:
        """Record a file checkout. Returns checkout id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO checkouts (file_id, user, target_path, status, notes)
                VALUES (?, ?, ?, 'active', ?)
                """,
                (file_id, user, target_path, notes)
            )
            conn.commit()
            return cursor.lastrowid

    def checkin_file(self, checkout_id: int) -> None:
        """Mark a checkout as returned."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE checkouts SET status='returned', returned_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (checkout_id,)
            )
            conn.commit()

    def get_checkout_info(self, target_path: str) -> Optional[Dict]:
        """Get active checkout info for a target path."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, file_id, user, target_path, status, notes, checked_out_at
                FROM checkouts WHERE target_path=? AND status='active'
                ORDER BY checked_out_at DESC LIMIT 1
                """,
                (target_path,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_active_checkouts(self, user: Optional[str] = None) -> List[Dict]:
        """Get all active checkouts, optionally filtered by user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if user:
                cursor = conn.execute(
                    """
                    SELECT c.id, c.file_id, c.user, c.target_path, c.status, c.checked_out_at,
                           f.path as file_path, f.type as file_type
                    FROM checkouts c JOIN files f ON c.file_id=f.id
                    WHERE c.status='active' AND c.user=?
                    ORDER BY c.checked_out_at DESC
                    """,
                    (user,)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT c.id, c.file_id, c.user, c.target_path, c.status, c.checked_out_at,
                           f.path as file_path, f.type as file_type
                    FROM checkouts c JOIN files f ON c.file_id=f.id
                    WHERE c.status='active'
                    ORDER BY c.checked_out_at DESC
                    """
                )
            return [dict(row) for row in cursor.fetchall()]

    def list_files_by_prefix(self, prefix: str) -> List[Dict]:
        """
        List files whose path starts with the given prefix.

        Args:
            prefix: Directory-like prefix (e.g., "/skills/")

        Returns:
            List of file dictionaries with id, path, type, frontmatter, hash
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT id, path, type, frontmatter, hash, created_at, updated_at
                FROM files
                WHERE path LIKE ?
                ORDER BY path
                """,
                (f"{prefix}%",),
            )

            return [dict(row) for row in cursor.fetchall()]

    def batch_generate_embeddings(
        self,
        sections: List[Dict[str, Any]],
        embedding_service: Any,
        force_regenerate: bool = False
    ) -> Dict[int, List[float]]:
        """
        Generate embeddings for multiple sections in batch.

        Args:
            sections: List of section dicts with id, content, content_hash
            embedding_service: EmbeddingService instance
            force_regenerate: If True, regenerate all embeddings

        Returns:
            Dict mapping section_id to embedding vector
        """
        # Note: Local SQLite doesn't have section_embeddings table
        # This is a placeholder for consistency with SupabaseStore
        # Embeddings are typically generated during Supabase sync

        if not sections:
            return {}

        # Progress callback
        def progress_callback(current: int, total: int):
            pct = (current / total) * 100
            print(f"Generating embeddings: {current}/{total} ({pct:.1f}%)", end='\r')

        # Collect texts and indices
        texts = [s['content'] for s in sections]

        # Generate embeddings in parallel
        embeddings = embedding_service.batch_generate_parallel(
            texts,
            progress_callback=progress_callback
        )

        # Store results (in-memory only for local SQLite)
        section_embeddings: Dict[int, List[float]] = {}
        for section, embedding in zip(sections, embeddings):
            if embedding is not None:  # Skip failed embeddings
                section_embeddings[section['id']] = embedding

        # Print final progress
        print(f"Generating embeddings: {len(texts)}/{len(texts)} (100.0%)")

        return section_embeddings

    def _has_embedding(self, section_id: int) -> bool:
        """
        Check if a section already has an embedding.

        Note: Local SQLite doesn't track embeddings in a separate table.
        This always returns False to trigger regeneration.

        Args:
            section_id: Section ID to check

        Returns:
            True if embedding exists, False otherwise
        """
        # Local SQLite doesn't have section_embeddings table
        return False

    def _store_embedding(self, section_id: int, embedding: List[float]) -> None:
        """
        Store an embedding for a section.

        Note: Local SQLite doesn't have section_embeddings table.
        This is a no-op for consistency with SupabaseStore.

        Args:
            section_id: Section ID
            embedding: Embedding vector
        """
        # Local SQLite doesn't store embeddings separately
        # Embeddings are typically generated during Supabase sync
        pass
