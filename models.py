"""
Data models for skill-split.

This module defines all data classes used throughout the skill-split system.
Each model represents a distinct component of the file parsing and storage pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FileFormat(Enum):
    """Detected file structure type."""

    MARKDOWN_HEADINGS = "markdown_headings"
    XML_TAGS = "xml_tags"
    MIXED = "mixed"
    UNKNOWN = "unknown"
    # NEW formats for component handlers
    JSON = "json"             # JSON files (config, plugins, hooks)
    JSON_SCHEMA = "json_schema"  # JSON with known schema
    SHELL_SCRIPT = "shell"    # Shell scripts
    MULTI_FILE = "multi_file"  # Component spanning multiple files
    # Script file formats (Phase 10+)
    PYTHON_SCRIPT = "python"  # Python (.py) files
    JAVASCRIPT_TYPESCRIPT = "javascript_typescript"  # JavaScript/TypeScript files


class FileType(Enum):
    """Type of file based on its location/purpose."""

    SKILL = "skill"  # /skills/*/SKILL.md
    COMMAND = "command"  # /commands/*/*.md
    REFERENCE = "reference"  # /get-shit-done/references/*.md
    # NEW types for component handlers
    AGENT = "agent"           # /agents/*/*.md
    PLUGIN = "plugin"         # plugin.json + .mcp.json + hooks.json
    HOOK = "hook"             # hooks.json + shell scripts
    OUTPUT_STYLE = "output_style"  # /output-styles/*.md
    CONFIG = "config"         # settings.json, mcp_config.json
    DOCUMENTATION = "documentation"  # README.md, CLAUDE.md, reference/*.md
    # Script files (Phase 10+)
    SCRIPT = "script"         # Python, Shell, JavaScript, TypeScript files


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
        file_id: Origin file ID (UUID for Supabase, int for SQLite) - optional
        file_type: Origin file type - optional, used for composition
    """

    level: int
    title: str
    content: str
    line_start: int
    line_end: int
    closing_tag_prefix: str = ""  # Whitespace before closing tag (e.g., "  " for "  </tag>")
    children: List[Section] = field(default_factory=list)
    parent: Optional[Section] = field(default=None, repr=False)
    file_id: Optional[str] = None  # UUID for Supabase, int for SQLite (stored as str for consistency)
    file_type: Optional[FileType] = None  # Origin file type, preserves context through composition

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


@dataclass
class ComponentMetadata:
    """
    Metadata for non-markdown components.

    For multi-file components (plugins, hooks), tracks
    related files and their relationships.

    Attributes:
        component_type: Type of component (FileType)
        primary_file: Main file path
        related_files: Associated file paths
        schema_version: For validation
        dependencies: Other components this depends on
    """

    component_type: FileType
    primary_file: str
    related_files: List[str] = field(default_factory=list)
    schema_version: str = "1.0"
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "component_type": self.component_type.value,
            "primary_file": self.primary_file,
            "related_files": self.related_files,
            "schema_version": self.schema_version,
            "dependencies": self.dependencies,
        }


@dataclass
class ComposedSkill:
    """Represents a skill composed from multiple sections."""

    section_ids: List[int]
    sections: Dict[int, "Section"]
    output_path: str
    frontmatter: str
    title: str
    description: str
    composed_hash: str = ""

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "section_ids": self.section_ids,
            "output_path": self.output_path,
            "frontmatter": self.frontmatter,
            "title": self.title,
            "description": self.description,
            "composed_hash": self.composed_hash,
        }


@dataclass
class CompositionContext:
    """Metadata for skill composition process."""

    source_files: List[str]
    source_sections: int
    target_format: FileFormat
    created_at: str
    validation_status: str = "pending"
    errors: List[str] = field(default_factory=list)
