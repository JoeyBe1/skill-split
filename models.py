"""
Data models for skill-split.

This module defines all data classes used throughout the skill-split system.
Each model represents a distinct component of the file parsing and storage pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class FileFormat(Enum):
    """Detected file structure type."""

    MARKDOWN_HEADINGS = "markdown_headings"
    XML_TAGS = "xml_tags"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class FileType(Enum):
    """Type of file based on its location/purpose."""

    SKILL = "skill"  # /skills/*/SKILL.md
    COMMAND = "command"  # /commands/*/*.md
    REFERENCE = "reference"  # /get-shit-done/references/*.md


@dataclass
class Section:
    """
    A parsed section of a document.

    Attributes:
        level: Heading level (1-6 for # through ######) or -1 for XML tags
        title: The heading title or tag name
        content: The full content under this section (excluding children)
        line_start: Starting line number (1-based) in original file
        line_end: Ending line number (1-based) in original file
        children: Nested subsections
        parent: Reference to parent section (for tree navigation)
    """

    level: int
    title: str
    content: str
    line_start: int
    line_end: int
    children: List[Section] = field(default_factory=list)
    parent: Optional[Section] = field(default=None, repr=False)

    def add_child(self, child: Section) -> None:
        """Add a child section, setting parent reference."""
        child.parent = self
        self.children.append(child)

    def get_all_content(self) -> str:
        """
        Get all content including children recursively.

        Returns:
            The section content plus all descendant content.
        """
        result = self.content
        for child in self.children:
            result += child.get_all_content()
        return result

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": self.level,
            "title": self.title,
            "content": self.content,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class ParsedDocument:
    """
    A fully parsed document with structure preserved.

    Attributes:
        frontmatter: YAML frontmatter as string (empty string if none)
        sections: List of top-level sections
        file_type: The type of file (skill, command, reference)
        format: The detected format type
        original_path: Original file path for reference
    """

    frontmatter: str
    sections: List[Section]
    file_type: FileType
    format: FileFormat
    original_path: str

    def get_section_by_title(self, title: str) -> Optional[Section]:
        """
        Find a section by title (top-level only).

        Args:
            title: The section title to search for

        Returns:
            The matching section or None
        """
        for section in self.sections:
            if section.title == title:
                return section
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "frontmatter": self.frontmatter,
            "sections": [s.to_dict() for s in self.sections],
            "file_type": self.file_type.value,
            "format": self.format.value,
            "original_path": self.original_path,
        }


@dataclass
class FileMetadata:
    """
    Metadata about a parsed file.

    Attributes:
        path: Full file path
        type: File type (skill, command, reference)
        frontmatter: YAML frontmatter as string (or None)
        hash: SHA256 hash of original file content
    """

    path: str
    type: FileType
    frontmatter: Optional[str]
    hash: str


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    A perfect round-trip is expected: original file content should
    exactly match recomposed content byte-for-byte.

    When hashes match:
    - is_valid=True
    - errors list is empty (cleared on match)
    - files_match=True

    When hashes do not match:
    - is_valid=False
    - errors contains failure details
    - warnings contains diagnostic information

    Attributes:
        is_valid: Whether validation passed (True when hashes match)
        original_hash: SHA256 hash of the original file
        recomposed_hash: SHA256 hash of the recomposed content
        files_match: Whether original and recomposed hashes match
        errors: List of error messages (empty when hashes match)
        warnings: List of warning messages (diagnostic info on failure)
    """

    is_valid: bool
    original_hash: str = ""
    recomposed_hash: str = ""
    files_match: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message and mark invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
