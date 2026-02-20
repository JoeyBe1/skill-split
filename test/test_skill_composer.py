"""
Comprehensive tests for SkillComposer.

Phase 11: Skill Composition API
Tests cover the complete composition workflow including:
- Section retrieval from database
- Hierarchy reconstruction from flat collections
- Frontmatter generation with metadata
- File writing with proper formatting
- Supabase upload integration
- Error handling and validation
"""

import pytest
from pathlib import Path
from typing import List, Dict
from unittest.mock import Mock, MagicMock, patch

from models import (
    Section,
    ParsedDocument,
    FileType,
    FileFormat,
    ComposedSkill,
    CompositionContext,
)
from core.skill_composer import SkillComposer
from core.database import DatabaseStore
from core.query import QueryAPI


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def tmp_db_path(tmp_path):
    """Create a temporary test database."""
    return str(tmp_path / "test_composer.db")


@pytest.fixture
def sample_sections() -> List[Section]:
    """Create sample sections for testing."""
    return [
        Section(
            level=1,
            title="Introduction",
            content="This is the introduction.\n",
            line_start=1,
            line_end=2,
        ),
        Section(
            level=2,
            title="Getting Started",
            content="How to get started.\n",
            line_start=3,
            line_end=4,
        ),
        Section(
            level=2,
            title="Advanced Usage",
            content="Advanced techniques.\n",
            line_start=5,
            line_end=6,
        ),
        Section(
            level=3,
            title="Pro Tips",
            content="Professional tips for advanced users.\n",
            line_start=7,
            line_end=8,
        ),
    ]


@pytest.fixture
def mock_query_api(sample_sections):
    """Create a mock QueryAPI that returns sample sections."""
    mock = Mock(spec=QueryAPI)

    # Map section IDs to sections for testing
    section_mapping = {
        1: sample_sections[0],
        2: sample_sections[1],
        3: sample_sections[2],
        4: sample_sections[3],
    }

    def get_section(section_id):
        return section_mapping.get(section_id)

    mock.get_section = Mock(side_effect=get_section)
    return mock


@pytest.fixture
def skill_composer(tmp_db_path, mock_query_api):
    """Create a SkillComposer with mocked dependencies."""
    composer = SkillComposer(tmp_db_path)
    # Replace query_api with mock
    composer.query_api = mock_query_api
    return composer


# ============================================================================
# Test: Initialization and Validation
# ============================================================================

class TestSkillComposerInitialization:
    """Test SkillComposer initialization and parameter validation."""

    def test_init_with_database_store(self, tmp_db_path):
        """Test initialization with DatabaseStore instance."""
        db = DatabaseStore(tmp_db_path)
        composer = SkillComposer(db)

        assert composer.db_store == db
        assert composer.query_api is not None

    def test_init_with_string_path(self, tmp_db_path):
        """Test initialization with string database path."""
        composer = SkillComposer(tmp_db_path)

        assert isinstance(composer.db_store, DatabaseStore)
        assert composer.query_api is not None

    def test_init_fails_with_none(self):
        """Test that initialization fails with None db_store."""
        with pytest.raises(ValueError, match="db_store cannot be None"):
            SkillComposer(None)

    def test_init_fails_with_invalid_type(self):
        """Test that initialization fails with invalid type."""
        with pytest.raises(TypeError, match="db_store must be DatabaseStore or string path"):
            SkillComposer(123)


# ============================================================================
# Test: Section Retrieval
# ============================================================================

class TestSectionRetrieval:
    """Test section retrieval from database."""

    def test_retrieve_single_section(self, skill_composer, sample_sections):
        """Test retrieving a single section."""
        sections = skill_composer._retrieve_sections([1])

        assert len(sections) == 1
        assert 1 in sections
        assert sections[1].title == "Introduction"

    def test_retrieve_multiple_sections(self, skill_composer, sample_sections):
        """Test retrieving multiple sections."""
        sections = skill_composer._retrieve_sections([1, 2, 3])

        assert len(sections) == 3
        assert 1 in sections
        assert 2 in sections
        assert 3 in sections

    def test_retrieve_all_sections(self, skill_composer, sample_sections):
        """Test retrieving all sample sections."""
        sections = skill_composer._retrieve_sections([1, 2, 3, 4])

        assert len(sections) == 4
        for i in range(1, 5):
            assert i in sections

    def test_retrieve_missing_section(self, skill_composer):
        """Test error when section not found."""
        with pytest.raises(ValueError, match="Section 999 not found"):
            skill_composer._retrieve_sections([999])

    def test_retrieve_partial_missing(self, skill_composer):
        """Test error when one of multiple sections is missing."""
        with pytest.raises(ValueError, match="Section 999 not found"):
            skill_composer._retrieve_sections([1, 999, 2])

    def test_retrieve_empty_list(self, skill_composer):
        """Test that empty section list is handled correctly."""
        sections = skill_composer._retrieve_sections([])
        assert len(sections) == 0


# ============================================================================
# Test: Hierarchy Reconstruction
# ============================================================================

class TestHierarchyRebuilding:
    """Test rebuilding section hierarchy from flat collections."""

    def test_rebuild_single_section(self, skill_composer):
        """Test rebuilding hierarchy with single root section."""
        section = Section(
            level=1,
            title="Root",
            content="Root content\n",
            line_start=1,
            line_end=2,
        )
        sections_list = [section]

        hierarchy = skill_composer._rebuild_hierarchy(sections_list)

        assert len(hierarchy) == 1
        assert hierarchy[0].title == "Root"
        assert len(hierarchy[0].children) == 0

    def test_rebuild_parent_child_relationship(self, skill_composer, sample_sections):
        """Test that children are properly attached to parents."""
        sections_list = [
            sample_sections[0],  # Level 1
            sample_sections[1],  # Level 2
            sample_sections[2],  # Level 2
        ]

        hierarchy = skill_composer._rebuild_hierarchy(sections_list)

        assert len(hierarchy) == 1
        assert hierarchy[0].title == "Introduction"
        assert len(hierarchy[0].children) == 2
        assert hierarchy[0].children[0].title == "Getting Started"
        assert hierarchy[0].children[1].title == "Advanced Usage"

    def test_rebuild_deep_hierarchy(self, skill_composer, sample_sections):
        """Test deep nesting with multiple levels."""
        sections_list = [
            sample_sections[0],  # Level 1
            sample_sections[1],  # Level 2
            sample_sections[3],  # Level 3
        ]

        hierarchy = skill_composer._rebuild_hierarchy(sections_list)

        assert len(hierarchy) == 1
        root = hierarchy[0]
        assert len(root.children) == 1
        assert len(root.children[0].children) == 1
        assert root.children[0].children[0].title == "Pro Tips"

    def test_rebuild_multiple_roots(self, skill_composer):
        """Test multiple root-level sections."""
        sections_list = [
            Section(1, "Root1", "Content1\n", 1, 2),
            Section(1, "Root2", "Content2\n", 3, 4),
            Section(1, "Root3", "Content3\n", 5, 6),
        ]

        hierarchy = skill_composer._rebuild_hierarchy(sections_list)

        assert len(hierarchy) == 3
        assert hierarchy[0].title == "Root1"
        assert hierarchy[1].title == "Root2"
        assert hierarchy[2].title == "Root3"

    def test_rebuild_empty_dict(self, skill_composer):
        """Test error when sections list is empty."""
        with pytest.raises(ValueError, match="sections list cannot be empty"):
            skill_composer._rebuild_hierarchy([])

    def test_rebuild_preserves_order(self, skill_composer):
        """Test that sections are ordered by input list order."""
        sections_list = [
            Section(1, "Third", "Content3\n", 15, 16),
            Section(1, "First", "Content1\n", 1, 2),
            Section(1, "Second", "Content2\n", 5, 6),
        ]

        # Order should be preserved exactly as input
        hierarchy = skill_composer._rebuild_hierarchy(sections_list)

        assert len(hierarchy) == 3
        assert hierarchy[0].title == "Third"
        assert hierarchy[1].title == "First"
        assert hierarchy[2].title == "Second"


# ============================================================================
# Test: Frontmatter Generation
# ============================================================================

class TestFrontmatterGeneration:
    """Test YAML frontmatter generation."""

    def test_generate_basic_frontmatter(self, skill_composer):
        """Test basic frontmatter generation."""
        sections = [
            Section(1, "Title", "Content\n", 1, 2),
        ]

        frontmatter = skill_composer._generate_frontmatter(
            title="Test Skill",
            description="Test Description",
            sections=sections
        )

        assert "name: test-skill" in frontmatter
        assert "description: Test Description" in frontmatter
        assert "sections:" in frontmatter

    def test_generate_with_empty_title(self, skill_composer):
        """Test frontmatter with empty title uses default."""
        sections = [Section(1, "Title", "Content\n", 1, 2)]

        frontmatter = skill_composer._generate_frontmatter(
            title="",
            description="Test",
            sections=sections
        )

        assert "name: composed-skill" in frontmatter

    def test_generate_with_empty_description(self, skill_composer):
        """Test frontmatter with empty description uses default."""
        sections = [Section(1, "Title", "Content\n", 1, 2)]

        frontmatter = skill_composer._generate_frontmatter(
            title="Test",
            description="",
            sections=sections
        )

        assert "Skill composed from existing sections" in frontmatter

    def test_generate_counts_all_sections(self, skill_composer):
        """Test that section count includes nested children."""
        root = Section(1, "Root", "Content\n", 1, 2)
        child1 = Section(2, "Child1", "Content\n", 3, 4)
        child2 = Section(2, "Child2", "Content\n", 5, 6)
        root.add_child(child1)
        root.add_child(child2)

        frontmatter = skill_composer._generate_frontmatter(
            title="Test",
            description="Test",
            sections=[root]
        )

        assert "sections: 3" in frontmatter

    def test_generate_basic_frontmatter_counts_recursively(self, skill_composer):
        """Test that basic frontmatter counts nested sections recursively."""
        root = Section(1, "Root", "Root content\n", 1, 2)
        child = Section(2, "Child", "Child content\n", 3, 4)
        grandchild = Section(3, "Grandchild", "Grandchild content\n", 5, 6)
        child.add_child(grandchild)
        root.add_child(child)

        frontmatter = skill_composer._generate_basic_frontmatter(
            title="Test",
            description="Test",
            sections=[root],
            section_ids=[1, 2, 3],
        )

        assert "sections: 3" in frontmatter

    def test_slugify_spaces_to_hyphens(self, skill_composer):
        """Test that spaces are converted to hyphens."""
        slug = skill_composer._slugify("My Test Skill")
        assert slug == "my-test-skill"

    def test_slugify_removes_special_chars(self, skill_composer):
        """Test that special characters are removed."""
        slug = skill_composer._slugify("Test@Skill#123!")
        assert slug == "testskill123"

    def test_slugify_removes_consecutive_hyphens(self, skill_composer):
        """Test that consecutive hyphens are collapsed."""
        slug = skill_composer._slugify("Test___Skill")
        assert slug == "test-skill"

    def test_slugify_strips_edges(self, skill_composer):
        """Test that leading/trailing hyphens are stripped."""
        slug = skill_composer._slugify("--test--skill--")
        assert slug == "test-skill"


# ============================================================================
# Test: Composition Workflow
# ============================================================================

class TestComposeFromSections:
    """Test the main compose_from_sections workflow."""

    def test_compose_basic(self, skill_composer, sample_sections):
        """Test basic skill composition."""
        composed = skill_composer.compose_from_sections(
            section_ids=[1, 2],
            output_path="/tmp/test.md",
            title="Test Skill",
            description="Test Description"
        )

        assert isinstance(composed, ComposedSkill)
        assert composed.title == "Test Skill"
        assert composed.description == "Test Description"
        assert len(composed.section_ids) == 2
        assert composed.output_path == "/tmp/test.md"

    def test_compose_validates_section_ids(self, skill_composer):
        """Test error with missing section IDs."""
        with pytest.raises(ValueError, match="Section 999 not found"):
            skill_composer.compose_from_sections(
                section_ids=[1, 999],
                output_path="/tmp/test.md"
            )

    def test_compose_rejects_duplicate_section_ids(self, skill_composer):
        """Test error with duplicate section IDs."""
        with pytest.raises(ValueError, match="Duplicate section IDs in compose request"):
            skill_composer.compose_from_sections(
                section_ids=[1, 1, 2],
                output_path="/tmp/test.md"
            )

    def test_compose_requires_non_empty_sections(self, skill_composer):
        """Test error with empty section list."""
        with pytest.raises(ValueError, match="section_ids list cannot be empty"):
            skill_composer.compose_from_sections(
                section_ids=[],
                output_path="/tmp/test.md"
            )

    def test_compose_requires_output_path(self, skill_composer):
        """Test error with empty output path."""
        with pytest.raises(ValueError, match="output_path cannot be empty"):
            skill_composer.compose_from_sections(
                section_ids=[1],
                output_path=""
            )

    def test_compose_validates_section_ids_is_list(self, skill_composer):
        """Test error when section_ids is not a list."""
        with pytest.raises(TypeError, match="section_ids must be a list"):
            skill_composer.compose_from_sections(
                section_ids="1,2,3",
                output_path="/tmp/test.md"
            )

    def test_compose_auto_generates_title(self, skill_composer):
        """Test that title is auto-generated if empty."""
        composed = skill_composer.compose_from_sections(
            section_ids=[1],
            output_path="/tmp/test.md",
            title=""
        )

        assert composed.title == "Composed Skill"

    def test_compose_auto_generates_description(self, skill_composer):
        """Test that description is auto-generated if empty."""
        composed = skill_composer.compose_from_sections(
            section_ids=[1],
            output_path="/tmp/test.md",
            description=""
        )

        assert composed.description == "Skill composed from sections"

    def test_compose_includes_frontmatter(self, skill_composer):
        """Test that frontmatter is included in composed skill."""
        composed = skill_composer.compose_from_sections(
            section_ids=[1],
            output_path="/tmp/test.md",
            title="Test"
        )

        assert composed.frontmatter
        assert "name:" in composed.frontmatter


# ============================================================================
# Test: File Writing
# ============================================================================

class TestWriteToFilesystem:
    """Test writing composed skills to filesystem."""

    def test_write_creates_file(self, skill_composer, tmp_path):
        """Test that write_to_filesystem creates a file."""
        output_path = tmp_path / "test_skill.md"

        composed = ComposedSkill(
            section_ids=[1],
            sections={1: Section(1, "Test", "Content\n", 1, 2)},
            output_path=str(output_path),
            frontmatter="name: test\n",
            title="Test",
            description="Test"
        )

        hash_val = skill_composer.write_to_filesystem(composed)

        assert output_path.exists()
        assert hash_val  # Hash should be returned
        assert composed.composed_hash == hash_val

    def test_write_includes_frontmatter(self, skill_composer, tmp_path):
        """Test that frontmatter is written to file."""
        output_path = tmp_path / "test_skill.md"

        composed = ComposedSkill(
            section_ids=[1],
            sections={1: Section(1, "Test", "Content\n", 1, 2)},
            output_path=str(output_path),
            frontmatter="name: test-skill\n",
            title="Test",
            description="Test"
        )

        skill_composer.write_to_filesystem(composed)

        content = output_path.read_text()
        assert "---" in content
        assert "name: test-skill" in content

    def test_write_includes_sections(self, skill_composer, tmp_path):
        """Test that section content is written to file."""
        output_path = tmp_path / "test_skill.md"
        section = Section(1, "Introduction", "This is intro content.\n", 1, 2)

        composed = ComposedSkill(
            section_ids=[1],
            sections={1: section},
            output_path=str(output_path),
            frontmatter="name: test\n",
            title="Test",
            description="Test"
        )

        skill_composer.write_to_filesystem(composed)

        content = output_path.read_text()
        assert "# Introduction" in content
        assert "This is intro content." in content

    def test_write_creates_parent_directory(self, skill_composer, tmp_path):
        """Test that parent directories are created."""
        output_path = tmp_path / "subdir" / "nested" / "test.md"

        composed = ComposedSkill(
            section_ids=[1],
            sections={1: Section(1, "Test", "Content\n", 1, 2)},
            output_path=str(output_path),
            frontmatter="name: test\n",
            title="Test",
            description="Test"
        )

        skill_composer.write_to_filesystem(composed)

        assert output_path.exists()

    def test_write_fails_with_invalid_path(self, skill_composer):
        """Test that invalid paths are rejected."""
        composed = ComposedSkill(
            section_ids=[1],
            sections={1: Section(1, "Test", "Content\n", 1, 2)},
            output_path="",
            frontmatter="name: test\n",
            title="Test",
            description="Test"
        )

        with pytest.raises(ValueError, match="output_path must be a valid file path"):
            skill_composer.write_to_filesystem(composed)

    def test_write_computes_hash(self, skill_composer, tmp_path):
        """Test that hash is computed and stored."""
        output_path = tmp_path / "test_skill.md"

        composed = ComposedSkill(
            section_ids=[1],
            sections={1: Section(1, "Test", "Content\n", 1, 2)},
            output_path=str(output_path),
            frontmatter="name: test\n",
            title="Test",
            description="Test"
        )

        assert not composed.composed_hash

        hash_val = skill_composer.write_to_filesystem(composed)

        assert hash_val
        assert composed.composed_hash == hash_val
        assert len(hash_val) == 64  # SHA256 hex digest length


# ============================================================================
# Test: Build Sections Content
# ============================================================================

class TestBuildSectionsContent:
    """Test section content reconstruction."""

    def test_build_single_section(self, skill_composer):
        """Test building content from single section."""
        section = Section(1, "Introduction", "Intro content.\n", 1, 2)

        content = skill_composer._build_sections_content([section])

        assert "# Introduction" in content
        assert "Intro content." in content

    def test_build_with_children(self, skill_composer):
        """Test building content with nested sections."""
        parent = Section(1, "Parent", "Parent content.\n", 1, 2)
        child = Section(2, "Child", "Child content.\n", 3, 4)
        parent.add_child(child)

        content = skill_composer._build_sections_content([parent])

        assert "# Parent" in content
        assert "## Child" in content
        assert "Parent content." in content
        assert "Child content." in content

    def test_build_preserves_hierarchy(self, skill_composer):
        """Test that heading levels are preserved."""
        root = Section(1, "Root", "Root.\n", 1, 2)
        level2 = Section(2, "Level 2", "L2.\n", 3, 4)
        level3 = Section(3, "Level 3", "L3.\n", 5, 6)
        root.add_child(level2)
        level2.add_child(level3)

        content = skill_composer._build_sections_content([root])

        # Check heading levels in content
        lines = content.split('\n')
        assert any(line.startswith("# Root") for line in lines)
        assert any(line.startswith("## Level 2") for line in lines)
        assert any(line.startswith("### Level 3") for line in lines)

    def test_build_empty_sections(self, skill_composer):
        """Test building with empty section list."""
        content = skill_composer._build_sections_content([])
        assert content == ""

    def test_build_preserves_content_formatting(self, skill_composer):
        """Test that content formatting is preserved."""
        section = Section(1, "Test", "Line 1\nLine 2\nLine 3\n", 1, 4)

        content = skill_composer._build_sections_content([section])

        assert "Line 1\nLine 2\nLine 3" in content


# ============================================================================
# Test: Supabase Upload
# ============================================================================

class TestSupabaseUpload:
    """Test uploading composed skills to Supabase."""

    def test_upload_reads_file(self, skill_composer, tmp_path):
        """Test that upload reads the file from disk."""
        output_path = tmp_path / "test.md"
        output_path.write_text("---\nname: test\n---\n\n# Test\nContent")

        composed = ComposedSkill(
            section_ids=[1],
            sections={1: Section(1, "Test", "Content\n", 1, 2)},
            output_path=str(output_path),
            frontmatter="name: test\n",
            title="Test",
            description="Test",
            composed_hash="abc123"
        )

        mock_store = Mock()
        mock_store.store_file.return_value = "file-uuid-123"

        with patch('core.detector.FormatDetector') as mock_detector_class, \
             patch('core.parser.Parser') as mock_parser_class:

            mock_detector = Mock()
            mock_detector.detect.return_value = (FileType.SKILL, FileFormat.MARKDOWN_HEADINGS)
            mock_detector_class.return_value = mock_detector

            mock_parser = Mock()
            mock_doc = Mock(spec=ParsedDocument)
            mock_parser.parse.return_value = mock_doc
            mock_parser_class.return_value = mock_parser

            result = skill_composer.upload_to_supabase(composed, mock_store)

            assert result == "file-uuid-123"
            mock_detector.detect.assert_called_once()
            mock_parser.parse.assert_called_once()

    def test_upload_fails_if_file_missing(self, skill_composer):
        """Test error when composed file not found."""
        composed = ComposedSkill(
            section_ids=[1],
            sections={1: Section(1, "Test", "Content\n", 1, 2)},
            output_path="/nonexistent/path/file.md",
            frontmatter="name: test\n",
            title="Test",
            description="Test"
        )

        mock_store = Mock()

        with pytest.raises(IOError, match="Composed file not found"):
            skill_composer.upload_to_supabase(composed, mock_store)

    def test_upload_calls_store_file(self, skill_composer, tmp_path):
        """Test that store_file is called with correct parameters."""
        output_path = tmp_path / "test.md"
        output_path.write_text("---\nname: test\n---\n\n# Test\nContent")

        composed = ComposedSkill(
            section_ids=[1],
            sections={1: Section(1, "Test", "Content\n", 1, 2)},
            output_path=str(output_path),
            frontmatter="name: test\n",
            title="Test",
            description="Test",
            composed_hash="abc123def456"
        )

        mock_store = Mock()
        mock_store.store_file.return_value = "file-uuid"

        with patch('core.detector.FormatDetector') as mock_detector_class, \
             patch('core.parser.Parser') as mock_parser_class:

            mock_detector = Mock()
            mock_detector.detect.return_value = (FileType.SKILL, FileFormat.MARKDOWN_HEADINGS)
            mock_detector_class.return_value = mock_detector

            mock_parser = Mock()
            mock_doc = Mock(spec=ParsedDocument)
            mock_parser.parse.return_value = mock_doc
            mock_parser_class.return_value = mock_parser

            skill_composer.upload_to_supabase(composed, mock_store)

            mock_store.store_file.assert_called_once()
            call_args = mock_store.store_file.call_args
            assert call_args[1]['content_hash'] == "abc123def456"
            assert call_args[1]['name'] == "test.md"


# ============================================================================
# Test: Integration
# ============================================================================

class TestIntegration:
    """Integration tests for complete composition workflow."""

    def test_full_composition_workflow(self, skill_composer, tmp_path, sample_sections):
        """Test complete workflow from sections to file."""
        output_path = tmp_path / "composed.md"

        # Compose
        composed = skill_composer.compose_from_sections(
            section_ids=[1, 2, 3],
            output_path=str(output_path),
            title="Complete Test",
            description="Full workflow test"
        )

        # Verify composed object
        assert composed.title == "Complete Test"
        assert len(composed.section_ids) == 3

        # Write to filesystem
        hash_val = skill_composer.write_to_filesystem(composed)

        # Verify file was written
        assert output_path.exists()
        content = output_path.read_text()
        assert "Complete Test" in content or "complete-test" in content
        assert "Full workflow test" in content

    def test_composed_skill_to_dict(self, skill_composer):
        """Test serialization of composed skill."""
        composed = skill_composer.compose_from_sections(
            section_ids=[1, 2],
            output_path="/tmp/test.md",
            title="Test",
            description="Test Description"
        )

        data = composed.to_dict()

        assert data['title'] == "Test"
        assert data['description'] == "Test Description"
        assert data['section_ids'] == [1, 2]
        assert data['output_path'] == "/tmp/test.md"
