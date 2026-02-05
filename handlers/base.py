"""
Base handler interface for component handlers.

This module defines the abstract base class that all type-specific
handlers must implement.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult
from core.hashing import compute_file_hash


class BaseHandler(ABC):
    """
    Abstract base class for component handlers.

    All type-specific handlers must implement this interface to ensure
    compatibility with the existing DatabaseStore and QueryAPI systems.

    Design principles:
    - All handlers return ParsedDocument for database compatibility
    - Support round-trip verification (SHA256)
    - Support progressive disclosure (section-based)
    - Handle multi-file components when applicable
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize handler with file path.

        Args:
            file_path: Path to the primary file for this component

        Raises:
            FileNotFoundError: If the file does not exist
        """
        self.file_path = file_path
        self.content = self._read_content()

    def _read_content(self) -> str:
        """
        Read file content from disk.

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file cannot be read
        """
        path = Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()

    @abstractmethod
    def parse(self) -> ParsedDocument:
        """
        Parse the component into structured sections.

        Returns:
            ParsedDocument with component-specific structure

        Must create sections that make sense for progressive disclosure:
        - For JSON: Top-level keys become sections
        - For plugins: Each config section becomes a section
        - For hooks: Each hook definition becomes a section

        Note:
            All handlers must return a ParsedDocument compatible with
            the existing DatabaseStore.store_file() method.
        """
        pass

    @abstractmethod
    def validate(self) -> ValidationResult:
        """
        Validate component structure and schema.

        Returns:
            ValidationResult with errors/warnings

        Should check:
        - Required fields present
        - Correct data types
        - Valid schema version
        - Referenced files exist
        """
        pass

    @abstractmethod
    def get_related_files(self) -> List[str]:
        """
        Get list of related files for multi-file components.

        Returns:
            List of file paths (absolute paths)

        For single-file components: Return empty list
        For multi-file components: Return paths to all related files

        Note:
            All returned paths should be absolute for consistency.
        """
        pass

    def recompute_hash(self) -> str:
        """
        Compute hash for component verification.

        For multi-file components, hash includes all related files.

        Returns:
            SHA256 hash string

        Note:
            Multi-file hashes are computed by combining the hash of
            the primary file with hashes of all related files.
        """
        related_files = self.get_related_files()

        if not related_files:
            # Single file: use existing hash function
            return compute_file_hash(self.file_path)

        # Multi-file: combine hashes
        combined = hashlib.sha256()
        primary_hash = compute_file_hash(self.file_path)
        combined.update(primary_hash.encode())

        for related in related_files:
            related_hash = compute_file_hash(related)
            combined.update(related_hash.encode())

        return combined.hexdigest()

    def recompose(self, sections: List[Section]) -> str:
        """
        Reconstruct component from sections.

        Args:
            sections: List of sections from database

        Returns:
            Complete component content as string

        Default implementation joins section content with newlines.
        Override for custom recomposition logic (e.g., JSON formatting).

        Note:
            This is a simple default implementation. Complex handlers
            may override this to handle format-specific requirements.
        """
        return "\n\n".join(s.content for s in sections if s.content)

    def get_file_type(self) -> FileType:
        """
        Get the FileType for this handler.

        Returns:
            The FileType enum value for this handler

        Note:
            This should be overridden by subclasses to return
            the appropriate FileType value.
        """
        return FileType.REFERENCE  # Default fallback

    def get_file_format(self) -> FileFormat:
        """
        Get the FileFormat for this handler.

        Returns:
            The FileFormat enum value for this handler

        Note:
            This should be overridden by subclasses to return
            the appropriate FileFormat value.
        """
        return FileFormat.UNKNOWN  # Default fallback
