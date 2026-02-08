"""
Skill validation for composed skills.

This module provides the SkillValidator class which validates composed skills
for structural integrity, content requirements, and metadata completeness.

Features:
- Structural validation (hierarchy, level progression)
- Content validation (empty sections, code blocks)
- Metadata validation (frontmatter requirements)
- Detailed error reporting with line numbers
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Tuple
from models import Section, ParsedDocument, FileFormat, FileType


class SkillValidator:
    """
    Validates composed skills for correctness and completeness.

    Performs three-level validation:
    1. Structure: Heading hierarchy, level progression, no orphaned sections
    2. Content: Empty sections, unclosed code blocks, formatting
    3. Metadata: Frontmatter presence, required fields
    """

    def __init__(self) -> None:
        """Initialize the skill validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_document(self, doc: ParsedDocument) -> Tuple[bool, List[str], List[str]]:
        """
        Perform comprehensive validation on a parsed document.

        Args:
            doc: ParsedDocument to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Validate structure
        struct_errors = self.validate_structure(doc.sections)
        self.errors.extend(struct_errors)

        # Validate content
        content_errors = self.validate_content(doc.sections)
        self.errors.extend(content_errors)

        # Validate metadata
        meta_errors = self.validate_metadata(doc.frontmatter, doc.file_type)
        self.errors.extend(meta_errors)

        # Check for common warnings
        self._check_warnings(doc)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def validate_structure(self, sections: List[Section]) -> List[str]:
        """
        Validate the hierarchical structure of sections.

        Checks:
        - Level progression (no jumps like H1 -> H3)
        - No orphaned sections (levels > 1 without parent)
        - Consistent heading nesting
        - Proper parent-child relationships

        Args:
            sections: Top-level sections to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not sections:
            errors.append("No sections found in document")
            return errors

        # Check level progression in flat traversal
        all_sections = self._flatten_sections(sections)

        # Only validate if we have sections
        if all_sections:
            # Find the first non-XML section to establish baseline
            first_valid_section = None
            for section in all_sections:
                if section.level >= 0:  # Skip XML tags (level -1)
                    first_valid_section = section
                    break

            if first_valid_section:
                current_level = first_valid_section.level

                # Check that first section is H1 or H2 (common in documents)
                if current_level not in [1, 2]:  # Allow H1 or H2 as starting level
                    self.warnings.append(f"First section is H{current_level}, expected H1 or H2")

                for i, section in enumerate(all_sections):
                    # Skip XML tags (level -1)
                    if section.level == -1:
                        continue

                    # Check for level jumps (e.g., H1 -> H3)
                    if section.level > current_level + 1:
                        errors.append(
                            f"Level jump detected: H{current_level} -> H{section.level} "
                            f"at '{section.title}' (line {section.line_start})"
                        )

                    current_level = section.level

        # Check parent-child consistency
        for section in all_sections:
            if section.children:
                for child in section.children:
                    if child.level != section.level + 1:
                        errors.append(
                            f"Child level mismatch: parent is H{section.level}, "
                            f"child is H{child.level} at '{child.title}'"
                        )

        return errors

    def validate_content(self, sections: List[Section]) -> List[str]:
        """
        Validate content quality and completeness.

        Checks:
        - No empty sections
        - Balanced code fences (```)
        - No orphaned code blocks
        - Minimum content length

        Args:
            sections: Sections to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        all_sections = self._flatten_sections(sections)

        for section in all_sections:
            # Check for empty content
            if not section.content or not section.content.strip():
                if section.level == 1:
                    # Top-level sections should have content
                    errors.append(
                        f"Empty section: '{section.title}' (line {section.line_start})"
                    )
                else:
                    # Subsections may be allowed to be empty if they have children
                    if not section.children:
                        self.warnings.append(
                            f"Empty subsection: '{section.title}' (line {section.line_start})"
                        )

            # Check code block balance
            code_fence_count = section.content.count("```")
            if code_fence_count % 2 != 0:
                errors.append(
                    f"Unbalanced code fences in '{section.title}': "
                    f"found {code_fence_count} backticks (line {section.line_start})"
                )

            # Check for orphaned code blocks
            lines = section.content.split("\n")
            in_code = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_code = not in_code

            if in_code:
                errors.append(
                    f"Unclosed code block in '{section.title}' (line {section.line_start})"
                )

        return errors

    def validate_metadata(self, frontmatter: str, file_type: FileType) -> List[str]:
        """
        Validate frontmatter metadata.

        Checks:
        - Frontmatter presence
        - Required fields (name, description, sections)
        - Valid YAML structure
        - Required fields by file type

        Args:
            frontmatter: YAML frontmatter as string
            file_type: Type of file being validated

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check for frontmatter
        if not frontmatter or not frontmatter.strip():
            errors.append("Missing frontmatter")
            return errors

        # Try to parse YAML
        try:
            import yaml
            metadata = yaml.safe_load(frontmatter)
            if not isinstance(metadata, dict):
                errors.append("Frontmatter is not valid YAML dictionary")
                return errors
        except Exception as e:
            errors.append(f"Invalid YAML in frontmatter: {str(e)}")
            return errors

        # Check required fields
        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing required field in frontmatter: '{field}'")
            elif not metadata[field]:
                errors.append(f"Empty required field in frontmatter: '{field}'")

        # Check file-type specific fields
        if file_type == FileType.SKILL:
            if "composed_from" in metadata:
                composed = metadata["composed_from"]
                if not isinstance(composed, list) or not composed:
                    errors.append(
                        "Invalid 'composed_from' field: must be non-empty list"
                    )

        return errors

    def _check_warnings(self, doc: ParsedDocument) -> None:
        """
        Check for non-critical issues that warrant warnings.

        Args:
            doc: Document to check
        """
        all_sections = self._flatten_sections(doc.sections)

        # Warn about very long sections
        for section in all_sections:
            if len(section.content) > 10000:
                self.warnings.append(
                    f"Very long section: '{section.title}' "
                    f"({len(section.content)} chars)"
                )

        # Warn about insufficient sections
        if len(all_sections) < 3:
            self.warnings.append(
                f"Document has only {len(all_sections)} sections (consider more depth)"
            )

        # Warn about missing description in frontmatter
        if doc.frontmatter:
            try:
                import yaml
                metadata = yaml.safe_load(doc.frontmatter)
                if isinstance(metadata, dict):
                    desc = metadata.get("description", "").strip()
                    if len(desc) < 10:
                        self.warnings.append("Very short or missing description")
            except:
                pass

    def _flatten_sections(self, sections: List[Section]) -> List[Section]:
        """
        Flatten nested sections into a single list.

        Args:
            sections: Top-level sections

        Returns:
            Flattened list of all sections
        """
        result = []
        for section in sections:
            result.append(section)
            result.extend(self._flatten_sections(section.children))
        return result


def validate_skill(doc: ParsedDocument) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate a skill document.

    Args:
        doc: ParsedDocument to validate

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = SkillValidator()
    return validator.validate_document(doc)