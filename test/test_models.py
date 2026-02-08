"""
Tests for data models: ComposedSkill and CompositionContext.

Tests serialization, defaults, validation, and conversions.
"""

import pytest
from datetime import datetime
from models import ComposedSkill, CompositionContext, Section, FileFormat


class TestComposedSkill:
    """Tests for ComposedSkill model."""

    def test_composed_skill_creation(self):
        """Test basic ComposedSkill instantiation."""
        skill = ComposedSkill(
            section_ids=[1, 2, 3],
            sections={},
            output_path="/tmp/test-skill.md",
            frontmatter="name: test-skill\n",
            title="Test Skill",
            description="A test skill"
        )

        assert skill.section_ids == [1, 2, 3]
        assert skill.output_path == "/tmp/test-skill.md"
        assert skill.title == "Test Skill"
        assert skill.description == "A test skill"
        assert skill.composed_hash == ""  # Default value

    def test_composed_skill_with_sections(self):
        """Test ComposedSkill with Section objects."""
        section1 = Section(
            level=1,
            title="Overview",
            content="This is an overview",
            line_start=1,
            line_end=5
        )
        section2 = Section(
            level=2,
            title="Details",
            content="Some details here",
            line_start=6,
            line_end=10
        )

        skill = ComposedSkill(
            section_ids=[1, 2],
            sections={1: section1, 2: section2},
            output_path="/tmp/composed.md",
            frontmatter="name: composed\n",
            title="Composed",
            description="Composed from sections"
        )

        assert len(skill.sections) == 2
        assert skill.sections[1].title == "Overview"
        assert skill.sections[2].title == "Details"

    def test_composed_skill_to_dict_serialization(self):
        """Test serialization of ComposedSkill to dictionary."""
        skill = ComposedSkill(
            section_ids=[10, 20, 30],
            sections={},
            output_path="/tmp/skill.md",
            frontmatter="name: test\ndesc: test\n",
            title="Test",
            description="Test Description",
            composed_hash="abc123def456"
        )

        result = skill.to_dict()

        assert result["section_ids"] == [10, 20, 30]
        assert result["output_path"] == "/tmp/skill.md"
        assert result["frontmatter"] == "name: test\ndesc: test\n"
        assert result["title"] == "Test"
        assert result["description"] == "Test Description"
        assert result["composed_hash"] == "abc123def456"

    def test_composed_skill_hash_tracking(self):
        """Test that composed_hash can be updated after creation."""
        skill = ComposedSkill(
            section_ids=[1],
            sections={},
            output_path="/tmp/test.md",
            frontmatter="",
            title="Test",
            description="Test"
        )

        assert skill.composed_hash == ""

        skill.composed_hash = "sha256abc123"
        assert skill.composed_hash == "sha256abc123"


class TestCompositionContext:
    """Tests for CompositionContext model."""

    def test_composition_context_creation(self):
        """Test basic CompositionContext instantiation."""
        now = datetime.now().isoformat()
        context = CompositionContext(
            source_files=["/tmp/file1.md", "/tmp/file2.md"],
            source_sections=15,
            target_format=FileFormat.MARKDOWN_HEADINGS,
            created_at=now
        )

        assert context.source_files == ["/tmp/file1.md", "/tmp/file2.md"]
        assert context.source_sections == 15
        assert context.target_format == FileFormat.MARKDOWN_HEADINGS
        assert context.created_at == now
        assert context.validation_status == "pending"  # Default value
        assert context.errors == []  # Default value

    def test_composition_context_with_errors(self):
        """Test CompositionContext with validation errors."""
        now = datetime.now().isoformat()
        errors = ["Missing title", "Invalid hierarchy"]

        context = CompositionContext(
            source_files=["/tmp/source.md"],
            source_sections=5,
            target_format=FileFormat.XML_TAGS,
            created_at=now,
            validation_status="failed",
            errors=errors
        )

        assert context.validation_status == "failed"
        assert context.errors == errors
        assert len(context.errors) == 2

    def test_composition_context_format_types(self):
        """Test CompositionContext with different format types."""
        now = datetime.now().isoformat()

        for fmt in [FileFormat.MARKDOWN_HEADINGS, FileFormat.XML_TAGS,
                    FileFormat.MIXED, FileFormat.JSON]:
            context = CompositionContext(
                source_files=["test.md"],
                source_sections=1,
                target_format=fmt,
                created_at=now
            )
            assert context.target_format == fmt
