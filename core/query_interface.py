"""
Unified query interface for both SQLite and Supabase stores.

This module defines the abstract interface that both DatabaseStore and
SupabaseStore must implement, ensuring consistent behavior regardless
of the storage backend.

Phase 12: Unification Task - SQLite + Supabase Alignment
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from models import FileMetadata, FileMetadata as FileMetadata, Section, FileType


class QueryStoreInterface(ABC):
    """
    Unified interface for section and file queries.

    Both DatabaseStore (SQLite) and SupabaseStore must implement this
    interface to provide consistent query capabilities across backends.
    """

    # Abstract methods - must be implemented by concrete stores

    @abstractmethod
    def get_section(self, section_id: str) -> Optional[Tuple[str, Section]]:
        """
        Get single section WITH file_type metadata.

        Args:
            section_id: ID of the section (int for SQLite, UUID str for Supabase)

        Returns:
            Tuple of (section_id, Section) with file_type populated, or None if not found
        """
        pass

    @abstractmethod
    def get_file(
        self, file_id: str
    ) -> Optional[Tuple[FileMetadata, List[Section]]]:
        """
        Get file with metadata and sections.

        Args:
            file_id: ID of the file (int for SQLite, UUID str for Supabase)

        Returns:
            Tuple of (FileMetadata, List[Section]) or None if not found
        """
        pass

    @abstractmethod
    def get_file_by_path(
        self, file_path: str
    ) -> Optional[Tuple[FileMetadata, List[Section]]]:
        """
        Get file by path with metadata and sections.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (FileMetadata, List[Section]) or None if not found
        """
        pass

    @abstractmethod
    def get_section_tree(self, file_id: str) -> List[Section]:
        """
        Get hierarchical section tree for a file.

        Returns sections in their parent-child hierarchy
        with the children attribute populated.

        Args:
            file_id: ID of the file (int for SQLite, UUID str for Supabase)

        Returns:
            List of top-level Section objects with populated children
        """
        pass

    @abstractmethod
    def get_next_section(
        self, section_id: str, file_id: str
    ) -> Optional[Tuple[str, Section]]:
        """
        Get next section for progressive disclosure.

        Finds the section that follows the given section_id in the file,
        respecting the hierarchical order.

        Args:
            section_id: Current section ID
            file_id: File ID to search within

        Returns:
            Tuple of (next_section_id, Section) or None if no next section
        """
        pass

    @abstractmethod
    def search_sections(
        self, query: str, file_id: Optional[str] = None
    ) -> List[Tuple[str, Section]]:
        """
        Search sections by title/content.

        Performs case-insensitive search across section titles and content.
        If file_id is provided, restricts search to that file.

        Args:
            query: Search query string
            file_id: Optional file ID to restrict search to

        Returns:
            List of (section_id, Section) tuples matching the query
        """
        pass

    @abstractmethod
    def list_files_by_prefix(self, prefix: str) -> List[Dict[str, Any]]:
        """
        List all files with path starting with prefix.

        Useful for component discovery by directory.

        Args:
            prefix: Directory-like prefix (e.g., "/skills/")

        Returns:
            List of file metadata dictionaries
        """
        pass


class StoreCapabilities:
    """
    Flags indicating which capabilities a store implementation supports.

    Different stores (SQLite vs Supabase) may have different capabilities.
    This allows querying the store for its features at runtime.
    """

    def __init__(
        self,
        supports_progressive_disclosure: bool = True,
        supports_full_text_search: bool = False,
        supports_vector_search: bool = False,
        supports_realtime: bool = False,
        supports_embeddings: bool = False,
    ) -> None:
        """Initialize capability flags."""
        self.supports_progressive_disclosure = supports_progressive_disclosure
        self.supports_full_text_search = supports_full_text_search
        self.supports_vector_search = supports_vector_search
        self.supports_realtime = supports_realtime
        self.supports_embeddings = supports_embeddings

    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary for serialization."""
        return {
            "progressive_disclosure": self.supports_progressive_disclosure,
            "full_text_search": self.supports_full_text_search,
            "vector_search": self.supports_vector_search,
            "realtime": self.supports_realtime,
            "embeddings": self.supports_embeddings,
        }
