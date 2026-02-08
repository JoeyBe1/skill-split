"""
Tests for the SkillComposer class.

Phase 11: Composition Foundation
Tests cover the composer API design and basic functionality scaffolding.
"""

import pytest
from pathlib import Path
from typing import List

from models import (
    Section,
    ParsedDocument,
    FileType,
    FileFormat,
    ComposedSkill,
)
from core.composer import SkillComposer, CompositionContext
from core.database import DatabaseStore


# Test fixtures and helper data
@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary test database."""
    return str(tmp_path / "test_composer.db")


@pytest.fixture
def sample_sections():
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
    ]


@pytest.fixture
def sample_document(sample_sections):
    """Create a sample parsed document."""
    return ParsedDocument(
        frontmatter="",
        sections=sample_sections,
        file_type=FileType.SKILL,
        format=FileFormat.MARKDOWN_HEADINGS,
        original_path="/test/skill.md",
    )


@pytest.fixture
def populated_db(test_db_path, sample_document):
    """Create and populate a test database."""
    store = DatabaseStore(test_db_path)
    # store_file requires: file_path, doc, content_hash
    file_hash = "abc123def456"  # Mock hash for testing
    store.store_file(sample_document.original_path, sample_document, file_hash)
    return test_db_path


# Test CompositionContext
class TestCompositionContext:
    def test_context_creation(self):
        """Test creating a composition context."""
        context = CompositionContext(
            source_file_path="/test/skill.md",
            target_skill_name="my-composed-skill",
        )

        assert context.source_file_path == "/test/skill.md"
        assert context.target_skill_name == "my-composed-skill"
        assert context.inclusion_type == "full"
        assert context.metadata == {}

    def test_context_with_metadata(self):
        """Test context with additional metadata."""
        metadata = {"author": "test-user", "version": "1.0"}
        context = CompositionContext(
            source_file_path="/test/skill.md",
            target_skill_name="my-skill",
            metadata=metadata,
        )

        assert context.metadata == metadata

    def test_context_with_inclusion_type(self):
        """Test context with custom inclusion type."""
        context = CompositionContext(
            source_file_path="/test/skill.md",
            target_skill_name="my-skill",
            inclusion_type="partial",
        )

        assert context.inclusion_type == "partial"


# Test SkillComposer initialization
class TestSkillComposerInit:
    def test_composer_initialization(self, test_db_path):
        """Test creating a SkillComposer instance."""
        composer = SkillComposer(test_db_path)

        assert composer.db_path == test_db_path
        assert composer.store is not None
        assert composer.query_api is not None

    def test_composer_with_existing_db(self, populated_db):
        """Test composer with an existing database."""
        composer = SkillComposer(populated_db)

        # Should not raise any errors
        assert composer.db_path == populated_db


# Test compose_skill method signature
class TestComposeSkill:
    def test_compose_skill_signature(self, populated_db, sample_document):
        """Test that compose_skill method exists and is callable."""
        composer = SkillComposer(populated_db)
        context = CompositionContext(
            source_file_path=sample_document.original_path,
            target_skill_name="test-skill",
        )

        # Should be callable (Phase 11: stub returns None)
        result = composer.compose_skill(context)
        assert result is None

    def test_compose_skill_with_section_ids(self, populated_db, sample_document):
        """Test compose_skill with specific section IDs."""
        composer = SkillComposer(populated_db)
        context = CompositionContext(
            source_file_path=sample_document.original_path,
            target_skill_name="test-skill",
        )

        # Phase 11: stub, should handle section_ids parameter
        result = composer.compose_skill(context, section_ids=[1, 2])
        assert result is None


# Test compose_from_sections method
class TestComposeFromSections:
    def test_compose_from_sections_signature(self, sample_sections):
        """Test that compose_from_sections method exists."""
        composer = SkillComposer(":memory:")

        # Phase 11: stub returns None
        result = composer.compose_from_sections(
            sample_sections, "test-skill", FileType.SKILL
        )
        assert result is None

    def test_compose_from_sections_with_defaults(self, sample_sections):
        """Test compose_from_sections with default parameters."""
        composer = SkillComposer(":memory:")

        result = composer.compose_from_sections(sample_sections, "test-skill")
        assert result is None


# Test get_section_tree method
class TestGetSectionTree:
    def test_get_section_tree_signature(self, populated_db):
        """Test that get_section_tree method exists."""
        composer = SkillComposer(populated_db)

        # Phase 11: stub returns None
        result = composer.get_section_tree(1)
        assert result is None

    def test_get_section_tree_with_children(self, populated_db):
        """Test get_section_tree parameter handling."""
        composer = SkillComposer(populated_db)

        result = composer.get_section_tree(1, include_children=True)
        assert result is None

        result = composer.get_section_tree(1, include_children=False)
        assert result is None


# Test filter_sections_by_level method
class TestFilterSectionsByLevel:
    def test_filter_sections_by_level_signature(self, sample_sections):
        """Test that filter_sections_by_level exists."""
        composer = SkillComposer(":memory:")

        # Phase 11: stub returns None
        result = composer.filter_sections_by_level(sample_sections)
        assert result is None

    def test_filter_sections_by_level_custom_range(self, sample_sections):
        """Test filter with custom level range."""
        composer = SkillComposer(":memory:")

        result = composer.filter_sections_by_level(
            sample_sections, min_level=2, max_level=3
        )
        assert result is None


# Test merge_sections method
class TestMergeSections:
    def test_merge_sections_signature(self, sample_sections):
        """Test that merge_sections method exists."""
        composer = SkillComposer(":memory:")

        # Phase 11: stub returns None
        result = composer.merge_sections(sample_sections, sample_sections)
        assert result is None

    def test_merge_sections_with_strategy(self, sample_sections):
        """Test merge with different strategies."""
        composer = SkillComposer(":memory:")

        for strategy in ["append", "prepend", "deduplicate"]:
            result = composer.merge_sections(
                sample_sections,
                sample_sections,
                merge_strategy=strategy,
            )
            assert result is None


# Test enrich_metadata method
class TestEnrichMetadata:
    def test_enrich_metadata_signature(self, sample_document):
        """Test that enrich_metadata method exists."""
        composer = SkillComposer(":memory:")

        # Phase 11: stub returns None
        result = composer.enrich_metadata(
            sample_document,
            "/test/source.md",
        )
        assert result is None

    def test_enrich_metadata_with_type(self, sample_document):
        """Test enrich_metadata with composition type."""
        composer = SkillComposer(":memory:")

        result = composer.enrich_metadata(
            sample_document,
            "/test/source.md",
            composition_type="automatic",
        )
        assert result is None


# Test validate_composition method
class TestValidateComposition:
    def test_validate_composition_signature(self, sample_document):
        """Test that validate_composition method exists."""
        composer = SkillComposer(":memory:")

        # Phase 11: stub returns None
        result = composer.validate_composition(sample_document)
        assert result is None

    def test_validate_composition_return_type(self, sample_document):
        """Test validate_composition return type when implemented."""
        composer = SkillComposer(":memory:")

        result = composer.validate_composition(sample_document)
        # Phase 11: expect None, but later should be dict
        assert result is None


# Test ComposedSkill model
class TestComposedSkill:
    def test_composed_skill_creation(self, sample_document):
        """Test creating a ComposedSkill instance."""
        section_dict = {1: sample_document.sections[0]}
        skill = ComposedSkill(
            section_ids=[1],
            sections=section_dict,
            output_path="/tmp/test-skill.md",
            frontmatter="name: test\ndescription: Test\n",
            title="Test Skill",
            description="A test skill",
        )

        assert skill.title == "Test Skill"
        assert skill.description == "A test skill"
        assert skill.section_ids == [1]
        assert skill.output_path == "/tmp/test-skill.md"
        assert skill.composed_hash == ""

    def test_composed_skill_with_metadata(self):
        """Test ComposedSkill with sections."""
        section = Section(
            level=1,
            title="Test",
            content="Content",
            line_start=1,
            line_end=5
        )
        section_dict = {1: section, 2: section}

        skill = ComposedSkill(
            section_ids=[1, 2],
            sections=section_dict,
            output_path="/tmp/test.md",
            frontmatter="name: test\n",
            title="Multi Section",
            description="Multiple sections",
            composed_hash="abc123"
        )

        assert skill.section_ids == [1, 2]
        assert len(skill.sections) == 2
        assert skill.composed_hash == "abc123"

    def test_composed_skill_to_dict(self):
        """Test ComposedSkill serialization."""
        section = Section(
            level=1,
            title="Test",
            content="Content",
            line_start=1,
            line_end=5
        )
        skill = ComposedSkill(
            section_ids=[1],
            sections={1: section},
            output_path="/tmp/test.md",
            frontmatter="name: test\n",
            title="Test",
            description="Desc",
        )

        result = skill.to_dict()

        assert isinstance(result, dict)
        assert result["title"] == "Test"
        assert result["output_path"] == "/tmp/test.md"
        assert "section_ids" in result
        assert "frontmatter" in result
        assert "description" in result

    def test_composed_skill_get_composed_content(self):
        """Test composed skill structure."""
        section = Section(
            level=1,
            title="Test Section",
            content="Test content here",
            line_start=1,
            line_end=5
        )
        skill = ComposedSkill(
            section_ids=[1],
            sections={1: section},
            output_path="/tmp/test.md",
            frontmatter="name: test\n",
            title="Test",
            description="Desc",
        )

        # Should include section in dict
        assert skill.sections[1].title == "Test Section"
        assert skill.sections[1].content == "Test content here"

    def test_composed_skill_get_composed_content_with_frontmatter(self):
        """Test composed skill with frontmatter."""
        section = Section(
            level=1,
            title="Test",
            content="Test content",
            line_start=1,
            line_end=2,
        )
        skill = ComposedSkill(
            section_ids=[1],
            sections={1: section},
            output_path="/tmp/test.md",
            frontmatter="key: value\n",
            title="Test Skill",
            description="With frontmatter"
        )

        # Verify frontmatter and sections are present
        assert skill.frontmatter == "key: value\n"
        assert skill.sections[1].title == "Test"
        assert "Test content" in skill.sections[1].content
