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
        self, current_section_id: int, file_path: str, first_child: bool = False
    ) -> Optional[Section]:
        """
        Get the next sibling section or next top-level section.

        Supports progressive disclosure workflow: after reading section N,
        get section N+1 without reloading the entire file.

        When first_child=True, navigates to first child subsection instead
        of next sibling. Useful for hierarchical exploration.

        Args:
            current_section_id: ID of the current section
            file_path: Path to the file containing the section
            first_child: If True, return first child instead of next sibling

        Returns:
            The next Section object if one exists, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get current section info
            cursor = conn.execute(
                """
                SELECT parent_id, order_index, level
                FROM sections WHERE id = ?
                """,
                (current_section_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            parent_id = row["parent_id"]
            current_order = row["order_index"]
            current_level = row["level"]

            # Get file_id from file path
            cursor = conn.execute(
                "SELECT id FROM files WHERE path = ?",
                (file_path,),
            )
            file_row = cursor.fetchone()

            if not file_row:
                return None

            file_id = file_row["id"]

            # FIRST CHILD: Return first child subsection
            if first_child:
                cursor = conn.execute(
                    """
                    SELECT id, level, title, content, line_start, line_end
                    FROM sections
                    WHERE file_id = ? AND parent_id = ?
                    ORDER BY order_index ASC
                    LIMIT 1
                    """,
                    (file_id, current_section_id),
                )
                child_row = cursor.fetchone()

                if child_row:
                    return Section(
                        level=child_row["level"],
                        title=child_row["title"],
                        content=child_row["content"],
                        line_start=child_row["line_start"],
                        line_end=child_row["line_end"],
                    )

                # No children, fall through to sibling behavior
                # (or could return None to indicate no children)

            # NEXT SIBLING: Query for next section with same parent
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
        Search sections by title or content using FTS5 full-text search.

        Now delegates to search_sections_with_rank() for BM25 relevance ranking.
        Returns (section_id, Section) tuples ordered by relevance.

        Args:
            query: Search string (FTS5 MATCH syntax supported)
            file_path: Optional file path to limit search to one file

        Returns:
            List of (section_id, Section) tuples matching the query, ranked by relevance
        """
        # Get ranked results
        ranked_results = self.search_sections_with_rank(query, file_path)

        # Convert to (section_id, Section) tuples
        results = []
        for section_id, rank in ranked_results:
            section = self.get_section(section_id)
            if section:
                results.append((section_id, section))

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

    def preprocess_query(self, query: str) -> str:
        """
        Preprocess search query for optimal FTS5 syntax.

        Exposes DatabaseStore preprocessing for users who want to
        understand how their query will be interpreted.

        Args:
            query: Raw search query

        Returns:
            Processed FTS5 MATCH syntax
        """
        return self.store.preprocess_fts5_query(query)
