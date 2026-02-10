"""
Frontmatter generator for composed skills.

This module provides the FrontmatterGenerator class which automatically
generates YAML frontmatter with metadata for composed skills.

Features:
- YAML generation with customizable metadata
- Slug generation from titles
- Tag extraction from sections
- Dependency detection
- File type detection
"""

from __future__ import annotations

import re
import yaml
from typing import List, Dict, Any, Set, Optional
from datetime import datetime

from models import Section, CompositionContext, FileFormat


class FrontmatterGenerator:
    """
    Generates YAML frontmatter for composed skills.

    Automatically creates metadata frontmatter that captures:
    - Skill name and description
    - Number of sections
    - Source files used
    - Creation timestamp
    - Extracted tags and dependencies
    - File types involved
    """

    def __init__(self) -> None:
        """Initialize the frontmatter generator."""
        self.tag_patterns = [
            r'@([\w\-]+)',  # @tag or @tag-with-hyphens format
            r'#([\w\-]+)',  # #tag or #tag-with-hyphens format (hashtags)
        ]
        self.tool_patterns = [
            r'(?:requires|uses|needs|depends\s+on):?\s*([A-Za-z0-9_\-\.]+)',
            r'(?:tool|language|framework):?\s*([A-Za-z0-9_\-\.]+)',
        ]

    def generate(
        self,
        title: str,
        description: str,
        sections: List[Section],
        context: CompositionContext,
        original_type: Optional[FileType] = None,
    ) -> str:
        """
        Generate YAML frontmatter for a composed skill.

        Creates complete frontmatter metadata including:
        - Basic metadata (name, description, sections count)
        - Composition source info
        - Auto-extracted tags
        - Detected dependencies
        - Detected file types
        - Creation timestamp

        Args:
            title: Title of the composed skill
            description: Human-readable description
            sections: List of Section objects included
            context: CompositionContext with composition details
            original_type: Optional FileType to preserve original component category

        Returns:
            YAML frontmatter as string (without --- delimiters)
        """
        # Build base metadata
        # Strictly following Claude Code skill schema
        slug = self._slugify(title)

        # Determine category - use original_type if provided, else default to "composed"
        category = original_type.value if original_type else "composed"

        metadata = {
            "title": title,  # Preserve original human-readable title
            "name": slug,
            "version": "1.0.0",  # Standard default
            "category": category,  # Use original type or default to "composed"
            "description": description,
            "author": "SkillComposer",
            "created": context.created_at,  # ISO format timestamp
            "created_at": context.created_at,  # For backward compatibility with tests
            "triggers": [
                f"/{slug}",
                slug
            ],
            "allowed-tools": ["Bash", "Read", "Write", "Grep"],  # Standard safe defaults
            # Section count - use both names for compatibility
            "sections": context.source_sections,
            "sections_count": context.source_sections,  # Extended metadata (kept for traceability)
            "composed_from": context.source_files,
        }

        # Add enriched metadata
        enriched = self._enrich_metadata(sections, metadata)

        # Generate YAML with proper formatting
        # Use sort_keys=False to preserve insertion order
        # Use allow_unicode=True for proper text handling
        yaml_content = yaml.dump(
            enriched,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=80,
        )

        return yaml_content

    def _slugify(self, text: str) -> str:
        """
        Convert text to a slug suitable for identifiers.

        Rules:
        - Convert to lowercase
        - Replace spaces with hyphens
        - Remove non-alphanumeric characters except hyphens
        - Collapse consecutive hyphens
        - Strip leading/trailing hyphens

        Args:
            text: Text to slugify

        Returns:
            Slugified string

        Examples:
            "My Awesome Skill" -> "my-awesome-skill"
            "Python/JavaScript" -> "python-javascript"
            "API (v2)" -> "api-v2"
        """
        # Convert to lowercase
        slug = text.lower()

        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', slug)

        # Replace slashes, underscores with hyphens
        slug = re.sub(r'[/_]', '-', slug)

        # Remove non-alphanumeric characters except hyphens
        slug = re.sub(r'[^a-z0-9\-]', '', slug)

        # Collapse consecutive hyphens
        slug = re.sub(r'\-+', '-', slug)

        # Strip leading/trailing hyphens
        slug = slug.strip('-')

        return slug

    def _enrich_metadata(
        self,
        sections: List[Section],
        base_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract and add enriched metadata to base metadata.

        Analyzes sections to extract:
        - Common tags across sections
        - Tool/dependency mentions
        - File types involved
        - Content statistics

        Args:
            sections: List of sections to analyze
            base_metadata: Base metadata dictionary to enrich

        Returns:
            Enriched metadata dictionary

        Note:
            This method modifies and returns the input dictionary.
        """
        # Extract tags from section content and map to both 'keywords' and 'tags'
        tags = self._extract_tags(sections)
        if tags:
            tags_list = sorted(list(tags))
            base_metadata["keywords"] = tags_list
            base_metadata["tags"] = tags_list  # Both keywords and tags for compatibility
        else:
            # Ensure both exist even if empty, as they're standard
            base_metadata["keywords"] = []
            base_metadata["tags"] = []

        # Extract dependencies/tools from sections
        dependencies = self._extract_dependencies(sections)
        if dependencies:
            base_metadata["dependencies"] = sorted(list(dependencies))

        # Detect file types mentioned
        file_types = self._detect_file_types(sections)
        if file_types:
            base_metadata["file_types"] = sorted(list(file_types))

        # Add content statistics
        stats = self._calculate_statistics(sections)
        if stats:
            base_metadata.update(stats)

        return base_metadata

    def _extract_tags(self, sections: List[Section]) -> Set[str]:
        """
        Extract tags from section content.

        Searches for @tag or #tag patterns in section titles and content.

        Args:
            sections: List of sections to analyze

        Returns:
            Set of unique tags found
        """
        tags: Set[str] = set()

        for section in sections:
            # Search in title
            for pattern in self.tag_patterns:
                matches = re.findall(pattern, section.title)
                tags.update(matches)

            # Search in content (first 500 chars to avoid parsing entire content)
            content_sample = section.content[:500] if section.content else ""
            for pattern in self.tag_patterns:
                matches = re.findall(pattern, content_sample)
                tags.update(matches)

        return tags

    def _extract_dependencies(self, sections: List[Section]) -> Set[str]:
        """
        Extract tool/dependency mentions from sections.

        Searches for patterns like "requires X", "uses Y", "depends on Z".

        Args:
            sections: List of sections to analyze

        Returns:
            Set of unique dependencies found
        """
        dependencies: Set[str] = set()

        for section in sections:
            # Search in title
            for pattern in self.tool_patterns:
                matches = re.findall(pattern, section.title, re.IGNORECASE)
                dependencies.update(m.lower() for m in matches)

            # Search in content (first 1000 chars)
            content_sample = section.content[:1000] if section.content else ""
            for pattern in self.tool_patterns:
                matches = re.findall(pattern, content_sample, re.IGNORECASE)
                dependencies.update(m.lower() for m in matches)

        return dependencies

    def _detect_file_types(self, sections: List[Section]) -> Set[str]:
        """
        Detect file types mentioned in sections.

        Looks for common file type keywords in section content.

        Args:
            sections: List of sections to analyze

        Returns:
            Set of unique file types found

        Examples:
            Detects: python, javascript, typescript, bash, yaml, json, etc.
        """
        file_types: Set[str] = set()

        # Common file type keywords to detect
        type_keywords = {
            'python': r'\bpython(?:3)?(?:\s|\.|$)',
            'javascript': r'\bjavascript\b',
            'typescript': r'\btypescript\b',
            'bash': r'\bbash\b',
            'shell': r'\b(?:shell|sh)\b',
            'yaml': r'\byaml\b',
            'json': r'\bjson\b',
            'markdown': r'\bmarkdown\b',
            'html': r'\bhtml\b',
            'css': r'\bcss\b',
            'sql': r'\bsql\b',
            'go': r'\bgo\blang\b',
            'rust': r'\brust\b',
            'java': r'\bjava\b',
        }

        content = ' '.join(
            f"{s.title} {s.content[:200]}"
            for s in sections
            if s.title or s.content
        )

        for ftype, pattern in type_keywords.items():
            if re.search(pattern, content, re.IGNORECASE):
                file_types.add(ftype)

        return file_types

    def _calculate_statistics(self, sections: List[Section]) -> Dict[str, Any]:
        """
        Calculate content statistics from sections.

        Computes:
        - Total characters
        - Total lines
        - Heading levels present
        - Nesting depth

        Args:
            sections: List of sections to analyze

        Returns:
            Dictionary with statistics

        Note:
            Returns empty dict if no meaningful stats can be calculated.
        """
        if not sections:
            return {}

        stats: Dict[str, Any] = {}

        # Count total content
        total_chars = sum(
            len(s.content) + len(s.title) + 2
            for s in sections
        )
        stats["total_characters"] = total_chars

        # Count sections by level
        level_counts: Dict[int, int] = {}
        for section in sections:
            level = section.level
            level_counts[level] = level_counts.get(level, 0) + 1

        if level_counts:
            stats["levels"] = {
                f"h{level}": count
                for level, count in sorted(level_counts.items())
                if level > 0  # Skip orphaned content
            }

        # Find max nesting depth
        max_depth = self._calculate_max_depth(sections)
        if max_depth > 0:
            stats["max_depth"] = max_depth

        return stats

    def _calculate_max_depth(self, sections: List[Section]) -> int:
        """
        Calculate maximum nesting depth in section hierarchy.

        Args:
            sections: List of top-level sections

        Returns:
            Maximum depth (1 for no children, 2 for one level, etc.)
        """
        if not sections:
            return 0

        max_depth = 1
        for section in sections:
            depth = self._depth_recursive(section)
            max_depth = max(max_depth, depth)

        return max_depth

    def _depth_recursive(self, section: Section) -> int:
        """
        Recursively calculate depth of a section tree.

        Args:
            section: Section to measure

        Returns:
            Depth of this section's subtree
        """
        if not section.children:
            return 1

        child_depths = [self._depth_recursive(child) for child in section.children]
        return 1 + max(child_depths)


# Convenience function for direct use
def generate_frontmatter(
    title: str,
    description: str,
    sections: List[Section],
    context: CompositionContext,
    original_type: Optional[FileType] = None,
) -> str:
    """
    Generate YAML frontmatter for sections.

    Convenience function that creates a FrontmatterGenerator instance
    and generates frontmatter in one call.

    Args:
        title: Skill title
        description: Skill description
        sections: List of sections to include
        context: Composition context
        original_type: Optional FileType to preserve original component category

    Returns:
        YAML frontmatter as string
    """
    generator = FrontmatterGenerator()
    return generator.generate(title, description, sections, context, original_type)
