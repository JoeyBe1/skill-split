"""
Database storage for skill-split.

This module provides the DatabaseStore class which handles all SQLite
database operations for storing parsed files and their sections.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Tuple

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
        Store a file and its sections in the database.

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

            # Store sections recursively
            self._store_sections(conn, file_id, doc.sections, parent_id=None)

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
        Recursively store sections in the database.

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

    def search_sections_with_rank(
        self, query: str, file_path: Optional[str] = None
    ) -> List[Tuple[int, float]]:
        """
        Search sections using FTS5 full-text search with relevance ranking.

        Uses BM25 algorithm for ranking based on term frequency and
        inverse document frequency. Returns results with relevance scores
        where higher = more relevant.

        Args:
            query: Search string (FTS5 MATCH syntax)
            file_path: Optional file path to limit search to one file

        Returns:
            List of (section_id, rank) tuples where rank is negative BM25 score
            (higher values = more relevant, so we negate for compatibility)
        """
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
                    (query, file_path)
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
                    (query,)
                )

            # Return (section_id, normalized_rank) tuples
            # BM25 returns negative scores, negate for "higher = better"
            results = [(row["id"], -row["rank"]) for row in cursor.fetchall()]
            return results

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
