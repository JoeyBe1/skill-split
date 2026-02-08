"""
Unit tests for FrontmatterGenerator class.

Tests cover:
- Basic frontmatter generation
- Slug generation
- Tag extraction
- Dependency detection
- File type detection
- Statistics calculation
- Integration with CompositionContext
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.frontmatter_generator import FrontmatterGenerator, generate_frontmatter
from models import Section, CompositionContext, FileFormat
import yaml


class TestSlugify:
    """Test the _slugify method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = FrontmatterGenerator()

    def test_slugify_basic(self):
        """Test basic slugification of simple text."""
        result = self.generator._slugify("My Awesome Skill")
        assert result == "my-awesome-skill"

    def test_slugify_with_slashes(self):
        """Test slugification with slashes."""
        result = self.generator._slugify("Python/JavaScript")
        assert result == "python-javascript"

    def test_slugify_with_parentheses(self):
        """Test slugification with parentheses."""
        result = self.generator._slugify("API (v2)")
        assert result == "api-v2"

    def test_slugify_with_special_chars(self):
        """Test slugification removes special characters."""
        result = self.generator._slugify("Advanced & Powerful!")
        assert result == "advanced-powerful"

    def test_slugify_multiple_spaces(self):
        """Test slugification collapses multiple spaces."""
        result = self.generator._slugify("Multiple    Spaces   Here")
        assert result == "multiple-spaces-here"

    def test_slugify_leading_trailing_hyphens(self):
        """Test slugification removes leading/trailing hyphens."""
        result = self.generator._slugify("-leading-and-trailing-")
        assert result == "leading-and-trailing"

    def test_slugify_with_numbers(self):
        """Test slugification preserves numbers."""
        result = self.generator._slugify("Python 3.11 Guide")
        assert result == "python-311-guide"


class TestTagExtraction:
    """Test the _extract_tags method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = FrontmatterGenerator()

    def test_extract_tags_from_title(self):
        """Test extraction of @tags from section title."""
        section = Section(
            level=1,
            title="Authentication @auth @security",
            content="Content here",
            line_start=1,
            line_end=5,
        )
        tags = self.generator._extract_tags([section])
        assert "auth" in tags
        assert "security" in tags

    def test_extract_hashtags(self):
        """Test extraction of #hashtags."""
        section = Section(
            level=1,
            title="Tutorial #python #web",
            content="Content",
            line_start=1,
            line_end=5,
        )
        tags = self.generator._extract_tags([section])
        assert "python" in tags
        assert "web" in tags

    def test_extract_tags_from_content(self):
        """Test extraction of tags from section content."""
        section = Section(
            level=1,
            title="Testing",
            content="This demonstrates @pattern @best-practice approaches",
            line_start=1,
            line_end=5,
        )
        tags = self.generator._extract_tags([section])
        assert "pattern" in tags
        assert "best-practice" in tags

    def test_extract_no_tags(self):
        """Test extraction when no tags are present."""
        section = Section(
            level=1,
            title="No Tags Here",
            content="Just plain content",
            line_start=1,
            line_end=5,
        )
        tags = self.generator._extract_tags([section])
        assert len(tags) == 0

    def test_extract_tags_deduplicate(self):
        """Test that duplicate tags are deduplicated."""
        sections = [
            Section(
                level=1,
                title="First @auth",
                content="More @auth content",
                line_start=1,
                line_end=5,
            ),
            Section(
                level=2,
                title="Second @auth",
                content="Yet more @auth",
                line_start=6,
                line_end=10,
            ),
        ]
        tags = self.generator._extract_tags(sections)
        assert tags == {"auth"}  # Single occurrence, not multiple


class TestDependencyExtraction:
    """Test the _extract_dependencies method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = FrontmatterGenerator()

    def test_extract_requires(self):
        """Test extraction of 'requires' keyword."""
        section = Section(
            level=1,
            title="Setup Guide",
            content="This requires Python 3.8",
            line_start=1,
            line_end=5,
        )
        deps = self.generator._extract_dependencies([section])
        assert "python" in deps

    def test_extract_uses(self):
        """Test extraction of 'uses' keyword."""
        section = Section(
            level=1,
            title="Implementation",
            content="Uses FastAPI for routing",
            line_start=1,
            line_end=5,
        )
        deps = self.generator._extract_dependencies([section])
        assert "fastapi" in deps

    def test_extract_depends_on(self):
        """Test extraction of 'depends on' keyword."""
        section = Section(
            level=1,
            title="Configuration",
            content="Depends on PostgreSQL database",
            line_start=1,
            line_end=5,
        )
        deps = self.generator._extract_dependencies([section])
        assert "postgresql" in deps

    def test_extract_tool_keyword(self):
        """Test extraction with 'tool' keyword."""
        section = Section(
            level=1,
            title="Build Process",
            content="Tool: Docker",
            line_start=1,
            line_end=5,
        )
        deps = self.generator._extract_dependencies([section])
        assert "docker" in deps

    def test_extract_language_keyword(self):
        """Test extraction with 'language' keyword."""
        section = Section(
            level=1,
            title="Implementation",
            content="Language: Rust",
            line_start=1,
            line_end=5,
        )
        deps = self.generator._extract_dependencies([section])
        assert "rust" in deps


class TestFileTypeDetection:
    """Test the _detect_file_types method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = FrontmatterGenerator()

    def test_detect_python(self):
        """Test detection of Python."""
        section = Section(
            level=1,
            title="Python Guide",
            content="Write Python code like this",
            line_start=1,
            line_end=5,
        )
        types = self.generator._detect_file_types([section])
        assert "python" in types

    def test_detect_javascript(self):
        """Test detection of JavaScript."""
        section = Section(
            level=1,
            title="JS Tutorial",
            content="JavaScript enables client-side scripting",
            line_start=1,
            line_end=5,
        )
        types = self.generator._detect_file_types([section])
        assert "javascript" in types

    def test_detect_typescript(self):
        """Test detection of TypeScript."""
        section = Section(
            level=1,
            title="Type Safety",
            content="Use TypeScript for better type safety",
            line_start=1,
            line_end=5,
        )
        types = self.generator._detect_file_types([section])
        assert "typescript" in types

    def test_detect_bash(self):
        """Test detection of Bash."""
        section = Section(
            level=1,
            title="Shell Scripts",
            content="Write bash scripts for automation",
            line_start=1,
            line_end=5,
        )
        types = self.generator._detect_file_types([section])
        assert "bash" in types

    def test_detect_multiple_types(self):
        """Test detection of multiple file types."""
        sections = [
            Section(
                level=1,
                title="Languages",
                content="Python and JavaScript",
                line_start=1,
                line_end=5,
            ),
        ]
        types = self.generator._detect_file_types(sections)
        assert "python" in types
        assert "javascript" in types

    def test_detect_no_types(self):
        """Test detection when no file types are mentioned."""
        section = Section(
            level=1,
            title="General Info",
            content="Just some generic content",
            line_start=1,
            line_end=5,
        )
        types = self.generator._detect_file_types([section])
        assert len(types) == 0


class TestStatisticsCalculation:
    """Test the _calculate_statistics method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = FrontmatterGenerator()

    def test_calculate_total_characters(self):
        """Test calculation of total characters."""
        sections = [
            Section(
                level=1,
                title="First",
                content="Content",
                line_start=1,
                line_end=5,
            ),
        ]
        stats = self.generator._calculate_statistics(sections)
        assert "total_characters" in stats
        assert stats["total_characters"] > 0

    def test_calculate_level_counts(self):
        """Test calculation of heading level counts."""
        sections = [
            Section(
                level=1,
                title="H1",
                content="",
                line_start=1,
                line_end=1,
            ),
            Section(
                level=2,
                title="H2",
                content="",
                line_start=2,
                line_end=2,
            ),
            Section(
                level=3,
                title="H3",
                content="",
                line_start=3,
                line_end=3,
            ),
        ]
        stats = self.generator._calculate_statistics(sections)
        assert "levels" in stats
        assert stats["levels"]["h1"] == 1
        assert stats["levels"]["h2"] == 1
        assert stats["levels"]["h3"] == 1

    def test_calculate_max_depth_single_level(self):
        """Test max depth calculation for single level."""
        sections = [
            Section(
                level=1,
                title="H1",
                content="",
                line_start=1,
                line_end=1,
            ),
        ]
        stats = self.generator._calculate_statistics(sections)
        assert stats.get("max_depth") == 1

    def test_calculate_max_depth_nested(self):
        """Test max depth calculation for nested sections."""
        parent = Section(
            level=1,
            title="Parent",
            content="",
            line_start=1,
            line_end=3,
        )
        child = Section(
            level=2,
            title="Child",
            content="",
            line_start=2,
            line_end=2,
        )
        grandchild = Section(
            level=3,
            title="Grandchild",
            content="",
            line_start=3,
            line_end=3,
        )
        child.parent = parent
        parent.add_child(child)
        grandchild.parent = child
        child.add_child(grandchild)

        stats = self.generator._calculate_statistics([parent])
        assert stats.get("max_depth") == 3


class TestFrontmatterGeneration:
    """Test the main generate method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = FrontmatterGenerator()
        self.now = datetime.now().isoformat()

    def test_generate_basic_frontmatter(self):
        """Test basic frontmatter generation."""
        sections = [
            Section(
                level=1,
                title="Introduction",
                content="Test content",
                line_start=1,
                line_end=3,
            ),
        ]
        context = CompositionContext(
            source_files=["test.md"],
            source_sections=1,
            target_format=FileFormat.MARKDOWN_HEADINGS,
            created_at=self.now,
        )

        frontmatter = self.generator.generate(
            title="Test Skill",
            description="A test skill",
            sections=sections,
            context=context,
        )

        # Parse the YAML to verify it's valid
        data = yaml.safe_load(frontmatter)

        assert data["name"] == "test-skill"
        assert data["description"] == "A test skill"
        assert data["version"] == "1.0.0"
        assert data["category"] == "composed"
        assert data["triggers"] == ["/test-skill", "test-skill"]
        assert data["description"] == "A test skill"
        assert data["sections"] == 1
        assert data["composed_from"] == ["test.md"]
        assert data["created_at"] == self.now

    def test_generate_with_tags(self):
        """Test frontmatter generation with extracted tags."""
        sections = [
            Section(
                level=1,
                title="Authentication @security @auth",
                content="Content",
                line_start=1,
                line_end=5,
            ),
        ]
        context = CompositionContext(
            source_files=["auth.md"],
            source_sections=1,
            target_format=FileFormat.MARKDOWN_HEADINGS,
            created_at=self.now,
        )

        frontmatter = self.generator.generate(
            title="Auth Guide",
            description="Authentication patterns",
            sections=sections,
            context=context,
        )

        data = yaml.safe_load(frontmatter)
        assert "keywords" in data
        assert "auth" in data["keywords"]
        assert "security" in data["keywords"]
        assert "auth" in data["tags"]
        assert "security" in data["tags"]

    def test_generate_with_dependencies(self):
        """Test frontmatter generation with extracted dependencies."""
        sections = [
            Section(
                level=1,
                title="Setup",
                content="Requires Python 3.8",
                line_start=1,
                line_end=5,
            ),
        ]
        context = CompositionContext(
            source_files=["setup.md"],
            source_sections=1,
            target_format=FileFormat.MARKDOWN_HEADINGS,
            created_at=self.now,
        )

        frontmatter = self.generator.generate(
            title="Python Setup",
            description="Setup guide",
            sections=sections,
            context=context,
        )

        data = yaml.safe_load(frontmatter)
        assert "dependencies" in data
        assert "python" in data["dependencies"]

    def test_generate_with_file_types(self):
        """Test frontmatter generation with detected file types."""
        sections = [
            Section(
                level=1,
                title="Code Examples",
                content="Python and JavaScript examples follow",
                line_start=1,
                line_end=10,
            ),
        ]
        context = CompositionContext(
            source_files=["examples.md"],
            source_sections=1,
            target_format=FileFormat.MARKDOWN_HEADINGS,
            created_at=self.now,
        )

        frontmatter = self.generator.generate(
            title="Code Examples",
            description="Multi-language examples",
            sections=sections,
            context=context,
        )

        data = yaml.safe_load(frontmatter)
        assert "file_types" in data
        assert "python" in data["file_types"]
        assert "javascript" in data["file_types"]

    def test_generate_complex_composition(self):
        """Test frontmatter generation for complex multi-section composition."""
        sections = [
            Section(
                level=1,
                title="Introduction @api",
                content="REST API basics",
                line_start=1,
                line_end=5,
            ),
            Section(
                level=2,
                title="Authentication",
                content="Requires JWT tokens",
                line_start=6,
                line_end=10,
            ),
            Section(
                level=2,
                title="Examples @code",
                content="Python and JavaScript implementations",
                line_start=11,
                line_end=20,
            ),
        ]
        context = CompositionContext(
            source_files=["api-guide.md", "examples.md"],
            source_sections=3,
            target_format=FileFormat.MARKDOWN_HEADINGS,
            created_at=self.now,
        )

        frontmatter = self.generator.generate(
            title="REST API Guide",
            description="Complete REST API reference",
            sections=sections,
            context=context,
        )

        data = yaml.safe_load(frontmatter)

        # Verify all components
        assert data["name"] == "rest-api-guide"
        assert data["sections_count"] == 3
        assert "api" in data["keywords"]
        assert "code" in data["keywords"]
        assert len(data["composed_from"]) == 2
        assert "api" in data.get("tags", [])
        assert "code" in data.get("tags", [])
        assert "python" in data.get("file_types", [])
        assert "javascript" in data.get("file_types", [])
        assert "levels" in data
        assert data["levels"]["h1"] == 1
        assert data["levels"]["h2"] == 2

    def test_generate_empty_sections(self):
        """Test frontmatter generation with empty sections list."""
        context = CompositionContext(
            source_files=[],
            source_sections=0,
            target_format=FileFormat.MARKDOWN_HEADINGS,
            created_at=self.now,
        )

        frontmatter = self.generator.generate(
            title="Empty Skill",
            description="No sections",
            sections=[],
            context=context,
        )

        data = yaml.safe_load(frontmatter)
        assert data["sections_count"] == 0
        assert data["composed_from"] == []


class TestConvenienceFunction:
    """Test the module-level convenience function."""

    def test_generate_frontmatter_function(self):
        """Test the generate_frontmatter convenience function."""
        now = datetime.now().isoformat()
        sections = [
            Section(
                level=1,
                title="Test",
                content="Content",
                line_start=1,
                line_end=3,
            ),
        ]
        context = CompositionContext(
            source_files=["test.md"],
            source_sections=1,
            target_format=FileFormat.MARKDOWN_HEADINGS,
            created_at=now,
        )

        frontmatter = generate_frontmatter(
            title="Test",
            description="Test",
            sections=sections,
            context=context,
        )

        data = yaml.safe_load(frontmatter)
        assert data["name"] == "test"
        assert data["description"] == "Test"
        assert data["version"] == "1.0.0"
