"""
Recomposer for rebuilding original files from database.

This module provides the Recomposer class which reconstructs original
file content from database-stored sections and frontmatter.
"""

from __future__ import annotations

from typing import List, Optional

from core.database import DatabaseStore
from models import Section, FileType
from handlers.factory import HandlerFactory


class Recomposer:
    """
    Reconstructs original file content from database storage.

    Rebuilds exact original files by combining frontmatter (if exists)
    with section content in proper hierarchical order.
    """

    def __init__(self, db: DatabaseStore) -> None:
        """
        Initialize the recomposer with a database store.

        Args:
            db: DatabaseStore instance to retrieve file data from
        """
        self.db = db

    def recompose(self, file_path: str) -> Optional[str]:
        """Rebuild original file from database.

        Reconstructs the exact original file content by combining:
        1. Frontmatter (if exists) wrapped in --- delimiters
        2. A newline separator
        3. All section content in hierarchical order

        For script files (FileType.SCRIPT), uses the handler's recompose()
        method to ensure proper reconstruction.

        Args:
            file_path: Path to the file to reconstruct

        Returns:
            Full file content with frontmatter + body, or None if not found
        """
        result = self.db.get_file(file_path)

        if result is None:
            return None

        metadata, sections = result

        # For script files, use the handler's recompose method
        if metadata.type == FileType.SCRIPT:
            try:
                handler = HandlerFactory.create_handler(file_path)
                return handler.recompose(sections)
            except (ValueError, FileNotFoundError):
                # Fall through to default recomposition
                pass

        # For hook/plugin/config files, return original JSON as-is
        # These are stored byte-for-byte in frontmatter for exact round-trip
        if metadata.type in (FileType.HOOK, FileType.PLUGIN, FileType.CONFIG):
            return metadata.frontmatter if metadata.frontmatter else ""

        # Build frontmatter portion
        frontmatter_part = ""
        if metadata.frontmatter:
            # Check if there's any body content (sections exist)
            has_body = bool(sections)
            frontmatter_part = self._build_frontmatter(metadata.frontmatter, has_body)

        # Build body content from sections in order
        body_part = self._build_sections_content(sections)

        # Check if first section is orphaned content (level=0)
        # If so, frontmatter should end with single \n, not \n\n
        has_orphaned_content = sections and sections[0].level == 0
        if has_orphaned_content and frontmatter_part:
            # Remove the extra \n from frontmatter (orphaned content has its own)
            frontmatter_part = frontmatter_part[:-1]  # Remove one \n

        # Combine frontmatter and body
        if frontmatter_part:
            # Frontmatter exists (ends with \n): frontmatter + body
            if body_part:
                return f"{frontmatter_part}{body_part}"
            return frontmatter_part

        # No frontmatter: just body
        return body_part

    def _build_frontmatter(self, frontmatter: str, has_body_content: bool = True) -> str:
        """Wrap frontmatter in --- delimiters.

        Args:
            frontmatter: Raw frontmatter content
            has_body_content: Whether there's body content after frontmatter

        Returns:
            Frontmatter wrapped in YAML delimiters
        """
        if has_body_content:
            return f"---\n{frontmatter}---\n\n"
        else:
            return f"---\n{frontmatter}---\n"

    def _build_sections_content(self, sections: List[Section]) -> str:
        """
        Build body content from sections in hierarchical order.

        Performs depth-first traversal to maintain the original
        document structure with proper nesting. Each section outputs
        its heading line followed by its direct content only.

        Args:
            sections: List of sections (potentially with children)

        Returns:
            Concatenated content from all sections in order

        Note:
            - level=0: Orphaned content (before first heading)
            - level=-1: XML tag format (<tag>content</tag>)
            - level>=1: Markdown heading format (# Heading)
        """
        content_parts: List[str] = []

        # Detect if this is a top-level XML tag section list
        is_top_level_xml = (
            sections and
            sections[0].level == -1 and
            not any(s.parent is not None for s in sections)
        )

        for i, section in enumerate(sections):
            if section.level == 0:
                # Orphaned content (before first heading) - output content directly
                if section.content:
                    content_parts.append(section.content)
            elif section.level == -1:
                # XML tag format: <tag> at start, </tag> at end
                opening_tag = f"<{section.title}>\n"
                closing_tag = f"{section.closing_tag_prefix}</{section.title}>\n"

                # Add opening tag
                content_parts.append(opening_tag)

                # Add this section's direct content (not children)
                if section.content:
                    content_parts.append(section.content)

                # Recursively add children (they output their own tags)
                if section.children:
                    children_content = self._build_sections_content(section.children)
                    if children_content:
                        content_parts.append(children_content)

                # Add closing tag
                content_parts.append(closing_tag)

                # For top-level XML sections, add blank line after closing tag (except last)
                if is_top_level_xml and i < len(sections) - 1:
                    content_parts.append("\n")
            else:
                # Markdown heading format
                heading_line = "#" * section.level + " " + section.title + "\n"

                # Add heading line
                content_parts.append(heading_line)

                # Build content: remove child content if children exist
                section_content = section.content
                if section.children and section_content:
                    # Find where first child starts and truncate
                    first_child_line = section.children[0].line_start
                    # Split content into lines and keep only lines before first child
                    lines = section_content.splitlines(keepends=True)
                    # The parser's line_start is 1-based, and we need to find where child starts
                    # Child's line_start - section.line_start - 1 = index in our content
                    child_offset = first_child_line - section.line_start
                    if child_offset >= 0 and child_offset < len(lines):
                        section_content = "".join(lines[:child_offset])

                # Add this section's direct content (not children)
                if section_content:
                    content_parts.append(section_content)

                # Recursively add children (they output their own headings)
                if section.children:
                    children_content = self._build_sections_content(section.children)
                    if children_content:
                        content_parts.append(children_content)

        return "".join(content_parts)
