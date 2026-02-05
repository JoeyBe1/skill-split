"""
Format detection for skill files.

This module provides intelligent detection of file structure types
based on both file path patterns and content analysis.
"""

import os
import re
from typing import Optional

from models import FileFormat, FileType


class FormatDetector:
    """
    Detects the format and type of a skill/command/reference file.

    Detection strategy:
    1. Path-based: Use known patterns for skills, commands, references
    2. Content-based: Analyze for heading patterns vs XML tag patterns
    3. Mixed: Handle files that may use both formats
    """

    # Regex patterns for path matching
    SKILL_PATTERN = re.compile(r"/skills/[^/]+/SKILL\.md$")
    COMMAND_PATTERN = re.compile(r"/commands/[^/]+/[^/]+\.md$")
    REFERENCE_PATTERN = re.compile(r"/get-shit-done/references/[^/]+\.md$|/references/[^/]+\.md$")

    # Regex patterns for content analysis
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+.+$", re.MULTILINE)
    XML_TAG_PATTERN = re.compile(r"^<([a-z][a-z0-9_]*)>.*?</\1>$", re.MULTILINE | re.DOTALL)
    XML_OPENING_TAG_PATTERN = re.compile(r"^<([a-z][a-z0-9_]*)>", re.MULTILINE)

    def __init__(self) -> None:
        """Initialize the detector."""
        pass

    def detect(self, file_path: str, content: str) -> tuple[FileType, FileFormat]:
        """
        Detect both file type and format from path and content.

        Args:
            file_path: Full or relative path to the file
            content: Full file content as string

        Returns:
            Tuple of (FileType, FileFormat)
        """
        file_type = self._detect_file_type(file_path)
        file_format = self._detect_format(content)
        return file_type, file_format

    def _detect_file_type(self, file_path: str) -> FileType:
        """
        Detect file type from path patterns.

        Args:
            file_path: Full or relative path to the file

        Returns:
            Detected FileType (defaults to REFERENCE if no match)
        """
        # Normalize path for matching
        normalized_path = os.path.normpath(file_path)

        # Check patterns in priority order
        if self.SKILL_PATTERN.search(normalized_path):
            return FileType.SKILL
        if self.COMMAND_PATTERN.search(normalized_path):
            return FileType.COMMAND
        if self.REFERENCE_PATTERN.search(normalized_path):
            return FileType.REFERENCE

        # Fallback: check filename patterns
        basename = os.path.basename(file_path)
        if basename == "SKILL.md":
            return FileType.SKILL

        # Default to reference for unknown patterns
        return FileType.REFERENCE

    def _detect_format(self, content: str) -> FileFormat:
        """
        Detect format from content analysis.

        Args:
            content: Full file content

        Returns:
            Detected FileFormat
        """
        if not content or not content.strip():
            return FileFormat.UNKNOWN

        # Count heading matches
        heading_matches = list(self.HEADING_PATTERN.finditer(content))
        heading_count = len(heading_matches)

        # Count XML tag matches (pairs of opening/closing tags on separate lines)
        xml_matches = self._find_xml_tag_blocks(content)
        xml_count = len(xml_matches)

        # Decision logic
        if xml_count > 0 and heading_count > 0:
            return FileFormat.MIXED
        elif xml_count > 0:
            return FileFormat.XML_TAGS
        elif heading_count > 0:
            return FileFormat.MARKDOWN_HEADINGS
        else:
            # Check for potential XML-like patterns even without full matches
            if self.XML_OPENING_TAG_PATTERN.search(content):
                return FileFormat.XML_TAGS
            return FileFormat.UNKNOWN

    def _find_xml_tag_blocks(self, content: str) -> list[tuple[int, int, str]]:
        """
        Find XML-style tag blocks in content.

        Looks for patterns like:
        <tag>
        content
        </tag>

        Args:
            content: File content to search

        Returns:
            List of (start_line, end_line, tag_name) tuples (1-based line numbers)
        """
        blocks = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for opening tag
            opening_match = re.match(r"^<([a-z][a-z0-9_]*)>$", line)
            if opening_match:
                tag_name = opening_match.group(1)
                start_line = i + 1  # Convert to 1-based

                # Look for matching closing tag
                j = i + 1
                while j < len(lines):
                    closing_line = lines[j].strip()
                    if closing_line == f"</{tag_name}>":
                        end_line = j + 1  # Convert to 1-based
                        blocks.append((start_line, end_line, tag_name))
                        i = j  # Continue after closing tag
                        break
                    j += 1

            i += 1

        return blocks

    def get_confidence(self, file_format: FileFormat, content: str) -> float:
        """
        Get confidence score for format detection (0.0 to 1.0).

        Args:
            file_format: The detected format
            content: File content

        Returns:
            Confidence score
        """
        if file_format == FileFormat.UNKNOWN:
            return 0.0

        content_lower = content.lower()

        if file_format == FileFormat.MARKDOWN_HEADINGS:
            # High confidence if we have clear heading structure
            heading_count = len(list(self.HEADING_PATTERN.finditer(content)))
            if heading_count >= 3:
                return 0.95
            return 0.7

        if file_format == FileFormat.XML_TAGS:
            # High confidence for well-formed XML tags
            xml_blocks = self._find_xml_tag_blocks(content)
            if xml_blocks:
                return 0.9
            return 0.6

        if file_format == FileFormat.MIXED:
            return 0.8

        return 0.5
