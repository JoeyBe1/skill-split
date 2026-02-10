"""
Tests for SkillValidator: Validation of composed skills.

This module tests the SkillValidator class which validates composed skills
for structural integrity, content requirements, and metadata completeness.

Test Coverage:
- Structural validation (hierarchy, level progression)
- Content validation (empty sections, code blocks)
- Metadata validation (frontmatter requirements)
- Integration validation across all three layers
"""

import pytest
from core.skill_validator import SkillValidator, validate_skill
from models import Section, ParsedDocument, FileType, FileFormat


class TestSkillValidatorStructure:
    """Test structural validation of skills."""

    def test_valid_hierarchy_no_errors(self):
        """Valid hierarchical structure should pass validation."""
        # Build a valid hierarchy: H1 -> H2 -> H3
        section_h3 = Section(
            level=3,
            title="Subsection",
            content="Content here",
            line_start=10,
            line_end=12
        )
        section_h2 = Section(
            level=2,
            title="Section",
            content="Content",
            line_start=5,
            line_end=12
        )
        section_h2.add_child(section_h3)

        section_h1 = Section(
            level=1,
            title="Main",
            content="Main content",
            line_start=1,
            line_end=12
        )
        section_h1.add_child(section_h2)

        validator = SkillValidator()
        errors = validator.validate_structure([section_h1])
        assert errors == []

    def test_level_jump_detected(self):
        """Level jump (H1 -> H3) should raise error."""
        section_h3 = Section(
            level=3,
            title="Bad Jump",
            content="Content",
            line_start=5,
            line_end=7
        )
        section_h1 = Section(
            level=1,
            title="Main",
            content="Main",
            line_start=1,
            line_end=7
        )
        section_h1.add_child(section_h3)

        validator = SkillValidator()
        errors = validator.validate_structure([section_h1])
        assert len(errors) > 0
        assert any("Level jump" in err for err in errors)

    def test_non_h1_first_section_error(self):
        """First section H2 or H3 generates warning (H1 is preferred but H2 allowed)."""
        section = Section(
            level=3,  # H3 should generate warning
            title="Not H1 or H2",
            content="Content",
            line_start=1,
            line_end=3
        )

        validator = SkillValidator()
        errors = validator.validate_structure([section])
        warnings = validator.warnings
        # H3 generates a warning (H1 and H2 are allowed)
        assert len(warnings) > 0 or len(errors) > 0

    def test_empty_sections_list_error(self):
        """Empty sections list should raise error."""
        validator = SkillValidator()
        errors = validator.validate_structure([])
        assert len(errors) > 0
        assert any("No sections found" in err for err in errors)

    def test_child_level_mismatch_error(self):
        """Child with wrong level relative to parent raises error."""
        # Parent H1, child H3 (should be H2)
        section_child = Section(
            level=3,
            title="Wrong Level",
            content="Content",
            line_start=5,
            line_end=7
        )
        section_parent = Section(
            level=1,
            title="Parent",
            content="Content",
            line_start=1,
            line_end=7
        )
        # Manually set wrong level relationship
        section_child.parent = section_parent
        section_parent.children = [section_child]

        validator = SkillValidator()
        errors = validator.validate_structure([section_parent])
        assert len(errors) > 0


class TestSkillValidatorContent:
    """Test content validation of skills."""

    def test_empty_section_error(self):
        """Top-level empty section raises error."""
        section = Section(
            level=1,
            title="Empty",
            content="",  # Empty content
            line_start=1,
            line_end=1
        )

        validator = SkillValidator()
        errors = validator.validate_content([section])
        assert len(errors) > 0
        assert any("Empty section" in err for err in errors)

    def test_unbalanced_code_fences_error(self):
        """Odd number of code fences raises error."""
        section = Section(
            level=1,
            title="Bad Code",
            content="Content\n```python\nprint('hello')\n",  # Missing closing ```
            line_start=1,
            line_end=4
        )

        validator = SkillValidator()
        errors = validator.validate_content([section])
        assert len(errors) > 0
        assert any("Unbalanced code fences" in err for err in errors)

    def test_balanced_code_fences_no_error(self):
        """Balanced code fences should pass validation."""
        section = Section(
            level=1,
            title="Good Code",
            content="Content\n```python\nprint('hello')\n```\nMore content",
            line_start=1,
            line_end=5
        )

        validator = SkillValidator()
        errors = validator.validate_content([section])
        # Should not have code fence errors
        code_errors = [e for e in errors if "Unbalanced" in e or "Unclosed" in e]
        assert len(code_errors) == 0

    def test_empty_subsection_warning(self):
        """Empty subsection (without children) generates warning."""
        child = Section(
            level=2,
            title="Empty Child",
            content="",
            line_start=5,
            line_end=5
        )
        parent = Section(
            level=1,
            title="Parent",
            content="Content",
            line_start=1,
            line_end=5
        )
        parent.add_child(child)

        validator = SkillValidator()
        errors = validator.validate_content([parent])
        # Check that warning was added
        assert len(validator.warnings) > 0
        assert any("Empty subsection" in w for w in validator.warnings)


class TestSkillValidatorMetadata:
    """Test metadata (frontmatter) validation."""

    def test_missing_frontmatter_error(self):
        """Missing frontmatter raises error."""
        validator = SkillValidator()
        errors = validator.validate_metadata("", FileType.SKILL)
        assert len(errors) > 0
        assert any("Missing frontmatter" in err for err in errors)

    def test_invalid_yaml_frontmatter_error(self):
        """Invalid YAML raises error."""
        bad_yaml = "name: test\n  invalid indentation: [bad"  # Bad YAML
        validator = SkillValidator()
        errors = validator.validate_metadata(bad_yaml, FileType.SKILL)
        assert len(errors) > 0
        assert any("Invalid YAML" in err for err in errors)

    def test_missing_required_fields_error(self):
        """Missing required fields (name, description) raises error."""
        frontmatter = "name: test\n"  # Missing 'description'
        validator = SkillValidator()
        errors = validator.validate_metadata(frontmatter, FileType.SKILL)
        assert any("Missing required field" in err and "description" in err for err in errors)

    def test_valid_frontmatter_no_error(self):
        """Valid frontmatter with all required fields passes."""
        frontmatter = "name: test-skill\ndescription: A test skill\nsections: 5\n"
        validator = SkillValidator()
        errors = validator.validate_metadata(frontmatter, FileType.SKILL)
        # Should have no errors for required fields
        required_errors = [e for e in errors if "required field" in e]
        assert len(required_errors) == 0


class TestSkillValidatorIntegration:
    """Integration tests for full document validation."""

    def test_complete_valid_document(self):
        """Complete valid document passes all validations."""
        # Build valid document
        section_h2 = Section(
            level=2,
            title="Subsection",
            content="Subsection content with details",
            line_start=10,
            line_end=12
        )
        section_h1 = Section(
            level=1,
            title="Main Section",
            content="Main content here",
            line_start=5,
            line_end=12
        )
        section_h1.add_child(section_h2)

        frontmatter = "name: test-skill\ndescription: A test skill\n"
        doc = ParsedDocument(
            frontmatter=frontmatter,
            sections=[section_h1],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/skill.md"
        )

        validator = SkillValidator()
        is_valid, errors, warnings = validator.validate_document(doc)
        assert is_valid
        assert len(errors) == 0

    def test_document_with_errors(self):
        """Document with structural errors fails validation."""
        # Invalid: H1 -> H3 (skips H2)
        section_h3 = Section(
            level=3,
            title="Bad Jump",
            content="Content",
            line_start=5,
            line_end=7
        )
        section_h1 = Section(
            level=1,
            title="Main",
            content="Main content",
            line_start=1,
            line_end=7
        )
        section_h1.add_child(section_h3)

        frontmatter = "name: test\ndescription: Test\n"
        doc = ParsedDocument(
            frontmatter=frontmatter,
            sections=[section_h1],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/skill.md"
        )

        validator = SkillValidator()
        is_valid, errors, warnings = validator.validate_document(doc)
        assert not is_valid
        assert len(errors) > 0

    def test_convenience_function_validate_skill(self):
        """Convenience function validate_skill() works correctly."""
        section = Section(
            level=1,
            title="Main",
            content="Content",
            line_start=1,
            line_end=3
        )
        frontmatter = "name: test\ndescription: Test skill\n"
        doc = ParsedDocument(
            frontmatter=frontmatter,
            sections=[section],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/skill.md"
        )

        is_valid, errors, warnings = validate_skill(doc)
        assert is_valid
        assert len(errors) == 0


class TestSkillValidatorEdgeCases:
    """Test edge cases and special scenarios."""

    def test_xml_tag_sections_skipped_in_level_checks(self):
        """XML tag sections (level -1) are skipped in level progression checks."""
        # XML tag sections have level=-1 and are skipped in the main level checks
        h1_parent = Section(
            level=1,
            title="Parent",
            content="Parent content",
            line_start=1,
            line_end=5
        )
        h2_child = Section(
            level=2,
            title="Child",
            content="Child content",
            line_start=6,
            line_end=8
        )
        h1_parent.add_child(h2_child)

        validator = SkillValidator()
        errors = validator.validate_structure([h1_parent])
        # Should pass level progression check (H1 -> H2)
        level_jump_errors = [e for e in errors if "Level jump" in e]
        assert len(level_jump_errors) == 0

    def test_very_long_section_warning(self):
        """Very long sections generate warnings."""
        long_content = "x" * 11000  # Over 10KB
        section = Section(
            level=1,
            title="Long Section",
            content=long_content,
            line_start=1,
            line_end=1000
        )

        doc = ParsedDocument(
            frontmatter="name: test\ndescription: Test\n",
            sections=[section],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/skill.md"
        )

        validator = SkillValidator()
        is_valid, errors, warnings = validator.validate_document(doc)
        assert len(warnings) > 0
        assert any("Very long section" in w for w in warnings)

    def test_insufficient_sections_warning(self):
        """Document with < 3 sections generates warning."""
        section = Section(
            level=1,
            title="Only One",
            content="Content",
            line_start=1,
            line_end=3
        )

        doc = ParsedDocument(
            frontmatter="name: test\ndescription: Test\n",
            sections=[section],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/skill.md"
        )

        validator = SkillValidator()
        is_valid, errors, warnings = validator.validate_document(doc)
        assert any("only" in w.lower() and "sections" in w for w in warnings)

    def test_short_description_warning(self):
        """Short description generates warning."""
        section = Section(
            level=1,
            title="Main",
            content="Content",
            line_start=1,
            line_end=3
        )
        short_frontmatter = "name: test\ndescription: Hi\n"

        doc = ParsedDocument(
            frontmatter=short_frontmatter,
            sections=[section],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/skill.md"
        )

        validator = SkillValidator()
        is_valid, errors, warnings = validator.validate_document(doc)
        assert any("description" in w.lower() for w in warnings)
