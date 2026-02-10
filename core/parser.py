"""
Parser for extracting structure from markdown and YAML files.

Handles:
- YAML frontmatter extraction
- Markdown heading hierarchy
- XML-style tag blocks (for phase 4)
- Code block awareness
"""

import re
from typing import List, Tuple, Optional

from models import ParsedDocument, Section, FileFormat, FileType


class Parser:
    """
    Parses markdown/YAML files into structured sections.

    Design philosophy:
    - Validate before every operation
    - Never silently lose data
    - Preserve exact whitespace for round-trip verification
    """

    # Patterns for frontmatter detection
    FRONTMATTER_DELIMITER = re.compile(r"^---\s*$", re.MULTILINE)

    # Patterns for heading detection
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    # Pattern for code blocks (must not split inside)
    CODE_BLOCK_START = re.compile(r"^```\w*\s*$")
    CODE_BLOCK_END = re.compile(r"^```\s*$")

    def __init__(self) -> None:
        """Initialize the parser."""
        pass

    def extract_frontmatter(self, content: str) -> Tuple[str, str]:
        """
        Extract YAML frontmatter from content.

        Args:
            content: Full file content

        Returns:
            Tuple of (frontmatter, remaining_content)
            - frontmatter: YAML content between --- delimiters (without delimiters)
            - remaining_content: Content after closing ---, or original if no frontmatter
        """
        if not content or not content.strip():
            return "", content

        lines = content.splitlines(keepends=True)

        # Need at least 3 lines for valid frontmatter (---, content, ---)
        if len(lines) < 3:
            return "", content

        # Check if first line is opening delimiter
        first_line = lines[0].strip()
        if first_line != "---":
            return "", content

        # Find closing delimiter
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                # Found closing delimiter
                frontmatter = "".join(lines[1:i])
                remaining = "".join(lines[i + 1 :])
                return frontmatter, remaining

        # Malformed: opening but no closing delimiter
        # Treat entire content as body (defensive)
        return "", content

    def parse_headings(self, content: str) -> ParsedDocument:
        """
        Parse markdown content with # headings into structured sections.

        Args:
            content: Markdown content (without frontmatter)

        Returns:
            ParsedDocument with hierarchical sections

        Handles:
        - Heading levels 1-6
        - Code blocks (won't split inside)
        - Consecutive headings (empty sections)
        - Mixed heading levels
        - Orphaned content (content before first heading)
        """
        frontmatter, body = self.extract_frontmatter(content)

        # Track code blocks to avoid splitting inside them
        lines = body.splitlines(keepends=True)
        in_code_block = False
        code_fence_char = None

        # Collect orphaned content (content before first heading)
        orphaned_lines = []
        first_heading_idx = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Check for code block boundaries
            if stripped.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                else:
                    in_code_block = False
            
            # Check for heading (only outside code blocks)
            if not in_code_block:
                if self.HEADING_PATTERN.match(line):
                    # Found first heading
                    first_heading_idx = i
                    break
            
            # Still haven't found a heading, accumulate orphaned content
            orphaned_lines.append(line)
        
        # Get orphaned content if any
        # NOTE: Preserve blank lines for byte-perfect round-trip integrity
        orphaned_content = "".join(orphaned_lines) if orphaned_lines else None

        # Parse headings with line number tracking
        sections = self._parse_heading_lines(lines, first_heading_idx, None, orphaned_content)

        return ParsedDocument(
            frontmatter=frontmatter,
            sections=sections,
            file_type=FileType.REFERENCE,  # Will be set by caller
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="",  # Will be set by caller
        )

    def _parse_heading_lines(
        self,
        lines: List[str],
        start_idx: int,
        parent_level: Optional[int],
        orphaned_content: Optional[str] = None,
        line_offset: int = 0,
    ) -> List[Section]:
        """
        Parse lines into sections, respecting parent level for nesting.

        Args:
            lines: All lines to parse
            start_idx: Starting index in lines
            parent_level: The heading level of parent (None for top-level)
            orphaned_content: Content that appeared before the first heading (top-level only)
            line_offset: Absolute line number offset for recursive calls

        Returns:
            List of Section objects
        """
        sections = []
        i = start_idx
        in_code_block = False
        code_fence_char = None

        # Handle orphaned content (content before first heading) - only at top level
        if orphaned_content and parent_level is None:
            sections.append(Section(
                level=0,  # level=0 indicates orphaned/intro content
                title="",  # No title for orphaned content
                content=orphaned_content,
                line_start=1 + line_offset,  # Always starts at line 1 + offset
                line_end=orphaned_content.count('\n') + 1 + line_offset,
            ))

        while i < len(lines):
            line = lines[i]

            # Check for code block boundaries
            stripped = line.strip()
            if stripped.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_fence_char = stripped
                elif in_code_block:
                    # Closing fence - any ``` closes the block
                    in_code_block = False
                    code_fence_char = None

            # Only parse headings when not in code block
            if not in_code_block:
                heading_match = self.HEADING_PATTERN.match(line)
                if heading_match:
                    hashes, title = heading_match.groups()
                    level = len(hashes)

                    # Check if this heading ends the current section
                    # (same level or higher than current context)
                    if parent_level is not None and level <= parent_level:
                        # Return to parent caller
                        break

                    # Extract content for this section (excluding child sections)
                    section_start = i + 1  # 1-based index in current lines
                    content_lines = []
                    i += 1

                    # Collect content until next heading of same or higher level
                    # Also track child headings separately
                    direct_content_lines = []
                    child_heading_indices = []

                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.strip()

                        # Check code block state
                        if next_stripped.startswith("```"):
                            if not in_code_block:
                                in_code_block = True
                                code_fence_char = next_stripped
                            elif in_code_block:
                                # Closing fence - any ``` closes the block
                                in_code_block = False
                                code_fence_char = None

                        # Check for next heading
                        if not in_code_block:
                            next_heading = self.HEADING_PATTERN.match(next_line)
                            if next_heading:
                                next_level = len(next_heading.group(1))
                                if next_level <= level:
                                    # Found heading that ends our section
                                    break
                                elif next_level > level:
                                    # This is a child heading - mark it but don't include in direct content
                                    child_heading_indices.append(len(direct_content_lines))

                        direct_content_lines.append(next_line)
                        i += 1

                    # Filter out child section content from direct content
                    # Build content by excluding lines that belong to child sections
                    if child_heading_indices:
                        # Content is everything before the first child heading
                        content_lines = direct_content_lines[:child_heading_indices[0]]
                        # Child lines start from first child heading to end
                        child_lines = direct_content_lines[child_heading_indices[0]:]
                    else:
                        # No children - all content is direct content
                        content_lines = direct_content_lines
                        child_lines = []

                    # Create section with direct content only (no child content)
                    section = Section(
                        level=level,
                        title=title,
                        content="".join(content_lines),
                        line_start=section_start + line_offset,
                        line_end=i + line_offset,  # i is now at next heading or end
                    )

                    # Recursively parse children from child lines only
                    if child_lines:
                        # Calculate new offset: current offset + start of children in lines
                        child_offset_in_lines = (section_start - 1) + child_heading_indices[0]
                        new_offset = line_offset + child_offset_in_lines
                        
                        children = self._parse_heading_lines(
                            child_lines, 0, level, None, new_offset
                        )
                        section.children = children
                        for child in children:
                            child.parent = section

                    sections.append(section)
                    continue

            i += 1

        return sections


    def _parse_xml_tag_lines(
        self,
        lines: List[str],
        start_idx: int,
        parent_tag: Optional[str],
        line_offset: int = 0,
    ) -> List[Section]:
        """
        Parse lines into XML tag sections, respecting parent tag for nesting.

        Args:
            lines: All lines to parse
            start_idx: Starting index in lines
            parent_tag: The tag name of parent (None for top-level)
            line_offset: Absolute line number offset

        Returns:
            List of Section objects with level=-1 for XML tags
        """
        sections = []
        i = start_idx

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Look for opening tag
            opening_match = re.match(r"^<([a-z][a-z0-9_]*)>\s*$", line)
            if opening_match:
                tag_name = opening_match.group(1)

                # Check if this closes the parent section
                if parent_tag is not None and stripped == f"</{parent_tag}>":
                    # Found closing tag for parent - return to parent caller
                    break

                # This is a new opening tag
                section_start = i + 1  # 1-based
                content_lines = []
                i += 1

                # Collect content until matching closing tag
                # Also track child tags separately
                direct_content_lines = []
                child_tag_indices = []
                depth = 1  # Track nesting depth (1 = inside current tag)
                closing_tag_prefix = ""  # Store whitespace before closing tag

                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()

                    # Check for our closing tag at our level
                    if next_stripped == f"</{tag_name}>":
                        depth -= 1
                        if depth == 0:
                            # Found our closing tag - capture its prefix (leading whitespace)
                            # Extract leading whitespace from the original line
                            prefix_match = re.match(r"^(\s*)", next_line)
                            if prefix_match:
                                closing_tag_prefix = prefix_match.group(1)
                            break

                    # Check for any opening tag (could be child)
                    nested_opening = re.match(r"^<([a-z][a-z0-9_]*)>\s*$", next_line)
                    if nested_opening and depth == 1:
                        # Inside current tag, this is a child
                        child_tag_indices.append(len(direct_content_lines))
                        depth += 1

                    # Check for closing tags to decrement depth
                    if next_stripped.startswith("</") and depth > 1:
                        # Might be closing a child tag
                        closing_match = re.match(r"^</([a-z][a-z0-9_]*)>\s*$", next_line)
                        if closing_match:
                            depth -= 1

                    direct_content_lines.append(next_line)
                    i += 1

                # Filter out child tag content from direct content
                if child_tag_indices:
                    # Content is everything before the first child tag
                    content_lines = direct_content_lines[:child_tag_indices[0]]
                    # Child lines start from first child tag to before closing tag
                    child_lines = direct_content_lines[child_tag_indices[0]:]
                else:
                    # No children - all content is direct content
                    content_lines = direct_content_lines
                    child_lines = []

                # Create section with level=-1 for XML tags
                section = Section(
                    level=-1,  # -1 indicates XML tag format
                    title=tag_name,
                    content="".join(content_lines),
                    line_start=section_start + line_offset,
                    line_end=i + 1 + line_offset,  # i is at closing tag
                    closing_tag_prefix=closing_tag_prefix,
                )

                # Recursively parse children from child lines only
                if child_lines:
                    child_offset_in_lines = section_start + child_tag_indices[0]
                    new_offset = line_offset + child_offset_in_lines
                    
                    children = self._parse_xml_tag_lines(
                        child_lines, 0, tag_name, new_offset
                    )
                    section.children = children
                    for child in children:
                        child.parent = section

                sections.append(section)

                # Move past closing tag
                i += 1
                continue

            # Check if this is a closing tag for our parent
            if parent_tag is not None and stripped == f"</{parent_tag}>":
                break

            i += 1

        return sections

    def parse_xml_tags(self, content: str) -> ParsedDocument:
        """
        Parse XML-style tag blocks into sections (Phase 4).

        Args:
            content: Content with XML-like tags

        Returns:
            ParsedDocument with tag-based sections

        Handles:
        - <tag>content</tag> blocks on separate lines
        - Nested tags (parent-child relationships)
        - Exact whitespace preservation for round-trip
        """
        frontmatter, body = self.extract_frontmatter(content)
        lines = body.splitlines(keepends=True)

        sections = self._parse_xml_tag_lines(lines, 0, None)

        return ParsedDocument(
            frontmatter=frontmatter,
            sections=sections,
            file_type=FileType.REFERENCE,  # Will be set by caller
            format=FileFormat.XML_TAGS,
            original_path="",  # Will be set by caller
        )

    def parse(self, file_path: str, content: str, file_type: FileType, file_format: FileFormat) -> ParsedDocument:
        """
        Main parse entry point - dispatches to appropriate parser.

        Args:
            file_path: Original file path
            content: Full file content
            file_type: Detected file type
            file_format: Detected format

        Returns:
            Fully parsed ParsedDocument
        """
        if file_format == FileFormat.MARKDOWN_HEADINGS:
            doc = self.parse_headings(content)
        elif file_format == FileFormat.XML_TAGS:
            doc = self.parse_xml_tags(content)
        elif file_format == FileFormat.MIXED:
            # For mixed, try headings first (more common)
            doc = self.parse_headings(content)
        else:
            # Unknown format - try headings as fallback
            doc = self.parse_headings(content)

        # Override metadata
        doc.file_type = file_type
        doc.format = file_format
        doc.original_path = file_path

        return doc
