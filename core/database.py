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
        self._create_schema()

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
        Get a single section by ID.

        Args:
            section_id: ID of the section

        Returns:
            Section object if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT level, title, content, line_start, line_end, closing_tag_prefix
                FROM sections WHERE id = ?
                """,
                (section_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return Section(
                level=row["level"],
                title=row["title"],
                closing_tag_prefix=row["closing_tag_prefix"] if "closing_tag_prefix" in row.keys() else "",
                content=row["content"],
                line_start=row["line_start"],
                line_end=row["line_end"],
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
