"""
Query API for progressive disclosure of skill-split sections.

This module provides the QueryAPI class with methods for retrieving sections
from the database in a progressive manner, supporting gradual disclosure
of large documents for token-efficient Claude interactions.
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from models import Section
from core.database import DatabaseStore


class QueryAPI:
    """
    Query interface for progressive section disclosure.

    Provides methods to retrieve sections individually, progressively,
    hierarchically, and via search to support token-efficient interactions
    with large skill and documentation files.
    """

    def __init__(self, db_path: str) -> None:
        """
        Initialize the QueryAPI with database access.

        Args:
            db_path: Path to SQLite database file
        """
        self.store = DatabaseStore(db_path)
        self.db_path = db_path

    def get_section(self, section_id: int) -> Optional[Section]:
        """
        Retrieve a single section by ID.

        This is the fundamental building block for progressive disclosure.
        Enables loading one section at a time to minimize token usage.

        Args:
            section_id: ID of the section to retrieve

        Returns:
            Section object if found, None otherwise
        """
        return self.store.get_section(section_id)

    def get_next_section(
        self, current_section_id: int, file_path: str
    ) -> Optional[Section]:
        """
        Get the next sibling section or next top-level section.

        Supports progressive disclosure workflow: after reading section N,
        get section N+1 without reloading the entire file.

        Args:
            current_section_id: ID of the current section
            file_path: Path to the file containing the section

        Returns:
            The next Section object if one exists, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get current section's parent_id and order_index
            cursor = conn.execute(
                """
                SELECT parent_id, order_index
                FROM sections WHERE id = ?
                """,
                (current_section_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            parent_id = row["parent_id"]
            current_order = row["order_index"]

            # Get file_id from file path
            cursor = conn.execute(
                "SELECT id FROM files WHERE path = ?",
                (file_path,),
            )
            file_row = cursor.fetchone()

            if not file_row:
                return None

            file_id = file_row["id"]

            # Query for next section with same parent
            cursor = conn.execute(
                """
                SELECT id, level, title, content, line_start, line_end
                FROM sections
                WHERE file_id = ? AND parent_id IS ? AND order_index > ?
                ORDER BY order_index ASC
                LIMIT 1
                """,
                (file_id, parent_id, current_order),
            )
            next_row = cursor.fetchone()

            if next_row:
                return Section(
                    level=next_row["level"],
                    title=next_row["title"],
                    content=next_row["content"],
                    line_start=next_row["line_start"],
                    line_end=next_row["line_end"],
                )

        return None

    def get_section_tree(self, file_path: str) -> List[Section]:
        """
        Get the full hierarchical tree of sections for a file.

        Returns all sections organized in their parent-child hierarchy,
        useful for navigation and understanding document structure.

        Args:
            file_path: Path to the file

        Returns:
            List of top-level Section objects with populated children
        """
        return self.store.get_section_tree(file_path)

    def search_sections(
        self, query: str, file_path: Optional[str] = None
    ) -> List[tuple[int, Section]]:
        """
        Search sections by title or content.

        Supports cross-file and single-file searches. Returns matches
        along with their database IDs for progressive disclosure.

        Args:
            query: Search string (searches in section titles and content)
            file_path: Optional file path to limit search to one file.
                      If None, searches all files.

        Returns:
            List of (section_id, Section) tuples matching the query
        """
        results: List[tuple[int, Section]] = []
        query_lower = query.lower()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if file_path:
                # Single file search
                cursor = conn.execute(
                    """
                    SELECT s.id, s.level, s.title, s.content,
                           s.line_start, s.line_end
                    FROM sections s
                    JOIN files f ON s.file_id = f.id
                    WHERE f.path = ?
                      AND (LOWER(s.title) LIKE ? OR LOWER(s.content) LIKE ?)
                    ORDER BY s.order_index
                    """,
                    (file_path, f"%{query_lower}%", f"%{query_lower}%"),
                )
            else:
                # Cross-file search
                cursor = conn.execute(
                    """
                    SELECT s.id, s.level, s.title, s.content,
                           s.line_start, s.line_end
                    FROM sections s
                    WHERE LOWER(s.title) LIKE ? OR LOWER(s.content) LIKE ?
                    ORDER BY s.id
                    """,
                    (f"%{query_lower}%", f"%{query_lower}%"),
                )

            for row in cursor.fetchall():
                section = Section(
                    level=row["level"],
                    title=row["title"],
                    content=row["content"],
                    line_start=row["line_start"],
                    line_end=row["line_end"],
                )
                results.append((row["id"], section))

        return results

    def search_sections_with_rank(
        self, query: str, file_path: Optional[str] = None
    ) -> List[tuple[int, float]]:
        """
        Search sections using FTS5 full-text search with relevance ranking.

        Delegates to DatabaseStore which performs BM25 ranking based on
        term frequency and inverse document frequency.

        Args:
            query: Search string
            file_path: Optional file path to limit search to one file

        Returns:
            List of (section_id, rank) tuples where higher rank = more relevant
        """
        return self.store.search_sections_with_rank(query, file_path)
