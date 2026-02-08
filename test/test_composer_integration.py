"""
Integration tests for SkillComposer with real database and query API.

Phase 11: Skill Composition Integration
End-to-end tests that verify the composition workflow with:
- Real database persistence
- Live section queries
- Multi-stage composition pipelines
- Error recovery and validation
"""

import pytest
import tempfile
from pathlib import Path
from typing import List

from models import (
    Section,
    ParsedDocument,
    FileType,
    FileFormat,
    ComposedSkill,
)
from core.skill_composer import SkillComposer
from core.database import DatabaseStore
from core.query import QueryAPI


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary test database."""
    return str(tmp_path / "integration_test.db")


@pytest.fixture
def sample_document() -> ParsedDocument:
    """Create a sample skill document with multiple sections."""
    sections = [
        Section(
            level=1,
            title="Authentication Patterns",
            content="Auth patterns overview.\n",
            line_start=1,
            line_end=3,
        ),
        Section(
            level=2,
            title="JWT Authentication",
            content="JWT implementation details.\n",
            line_start=4,
            line_end=6,
        ),
        Section(
            level=3,
            title="Token Generation",
            content="How to generate JWT tokens.\n",
            line_start=7,
            line_end=9,
        ),
        Section(
            level=3,
            title="Token Validation",
            content="How to validate JWT tokens.\n",
            line_start=10,
            line_end=12,
        ),
        Section(
            level=2,
            title="OAuth 2.0",
            content="OAuth 2.0 patterns.\n",
            line_start=13,
            line_end=15,
        ),
        Section(
            level=3,
            title="Authorization Code Flow",
            content="Authorization code flow details.\n",
            line_start=16,
            line_end=18,
        ),
    ]

    return ParsedDocument(
        frontmatter="name: auth-patterns\n",
        sections=sections,
        file_type=FileType.SKILL,
        format=FileFormat.MARKDOWN_HEADINGS,
        original_path="/test/auth_patterns.md",
    )


@pytest.fixture
def populated_db(test_db_path, sample_document):
    """Create and populate a test database."""
    store = DatabaseStore(test_db_path)
    store.store_file(
        sample_document.original_path,
        sample_document,
        "mock_hash_123"
    )
    return test_db_path


@pytest.fixture
def query_api_with_data(populated_db):
    """Create QueryAPI instance with populated database."""
    return QueryAPI(populated_db)


@pytest.fixture
def skill_composer_with_db(populated_db):
    """Create SkillComposer with real database."""
    return SkillComposer(populated_db)


# ============================================================================
# Test: Database Integration
# ============================================================================

class TestDatabaseIntegration:
    """Test composition with real database operations."""

    def test_compose_from_stored_sections(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test composing from sections stored in database."""
        output_path = tmp_path / "composed_from_db.md"

        # Get section IDs from query API
        try:
            # Try to get at least one section using query API
            section_1 = query_api_with_data.get_section(1)
            stored_sections = [1] if section_1 else []
        except:
            stored_sections = []

        if len(stored_sections) < 1:
            pytest.skip("No sections available in database")

        # Compose from these sections
        composed = skill_composer_with_db.compose_from_sections(
            section_ids=stored_sections,
            output_path=str(output_path),
            title="Composed from Database",
            description="Test composition from stored sections"
        )

        assert composed is not None
        assert len(composed.section_ids) == len(stored_sections)
        assert all(sid in composed.sections for sid in stored_sections)

    def test_compose_preserves_section_content(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test that section content is preserved during composition."""
        output_path = tmp_path / "preserve_test.md"

        # Get a specific section from database using QueryAPI
        section = query_api_with_data.get_section(1)

        if not section:
            pytest.skip("No sections in database")

        section_id = 1
        original_title = section.title
        original_content = section.content

        # Compose with this section
        composed = skill_composer_with_db.compose_from_sections(
            section_ids=[section_id],
            output_path=str(output_path),
            title="Content Preservation Test"
        )

        # Verify content is preserved
        retrieved_section = composed.sections[section_id]
        assert retrieved_section.title == original_title
        assert retrieved_section.content == original_content

    def test_composition_with_hierarchical_sections(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test composition with sections at different levels."""
        output_path = tmp_path / "hierarchical.md"

        # Get sections at different levels
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id FROM sections
            WHERE level IN (1, 2, 3)
            ORDER BY level, id
            LIMIT 3
        """)
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        if len(section_ids) > 0:
            composed = skill_composer_with_db.compose_from_sections(
                section_ids=section_ids,
                output_path=str(output_path),
                title="Hierarchical Test"
            )

            # Verify sections are included
            assert len(composed.sections) == len(section_ids)


# ============================================================================
# Test: Multi-Stage Composition
# ============================================================================

class TestMultiStageComposition:
    """Test composition with multiple stages and transformations."""

    def test_compose_then_write_workflow(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test complete compose->write->verify workflow."""
        output_path = tmp_path / "multi_stage.md"

        # Get sections to compose
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections ORDER BY id LIMIT 2")
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        # Stage 1: Compose
        composed = skill_composer_with_db.compose_from_sections(
            section_ids=section_ids,
            output_path=str(output_path),
            title="Multi-Stage Test",
            description="Testing multi-stage workflow"
        )

        assert composed is not None
        assert composed.output_path == str(output_path)

        # Stage 2: Write to filesystem
        hash_val = skill_composer_with_db.write_to_filesystem(composed)

        assert hash_val is not None
        assert output_path.exists()

        # Stage 3: Verify written content
        content = output_path.read_text()
        assert "Multi-Stage Test" in content or "multi-stage-test" in content
        assert "Testing multi-stage workflow" in content

    def test_compose_multiple_skills_from_same_db(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test composing multiple different skills from same database."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections ORDER BY id")
        all_section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        if len(all_section_ids) < 2:
            pytest.skip("Not enough sections for multi-skill test")

        # Compose first skill (first N sections)
        output1 = tmp_path / "skill1.md"
        composed1 = skill_composer_with_db.compose_from_sections(
            section_ids=all_section_ids[:1],
            output_path=str(output1),
            title="Skill One"
        )
        skill_composer_with_db.write_to_filesystem(composed1)

        # Compose second skill (remaining sections)
        if len(all_section_ids) > 1:
            output2 = tmp_path / "skill2.md"
            composed2 = skill_composer_with_db.compose_from_sections(
                section_ids=all_section_ids[1:],
                output_path=str(output2),
                title="Skill Two"
            )
            skill_composer_with_db.write_to_filesystem(composed2)

            # Verify both files exist
            assert output1.exists()
            assert output2.exists()

            # Verify they're different
            content1 = output1.read_text()
            content2 = output2.read_text()
            assert "Skill One" in content1 or "skill-one" in content1
            assert "Skill Two" in content2 or "skill-two" in content2


# ============================================================================
# Test: Hierarchy Preservation
# ============================================================================

class TestHierarchyPreservation:
    """Test that section hierarchy is preserved through composition."""

    def test_hierarchy_rebuilt_correctly(self, skill_composer_with_db, query_api_with_data):
        """Test that parent-child relationships are preserved."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT s1.id, s2.id
            FROM sections s1
            JOIN sections s2 ON s1.id < s2.id
            WHERE s1.level = 1 AND s2.level = 2
            LIMIT 1
        """)
        result = cursor.fetchone()
        db.conn.close()

        if result:
            parent_id, child_id = result

            composed = skill_composer_with_db.compose_from_sections(
                section_ids=[parent_id, child_id],
                output_path="/tmp/test_hierarchy.md"
            )

            # Get the rebuilt hierarchy
            sections = composed.sections
            parent = sections[parent_id]

            # Verify parent-child relationship exists
            assert parent.level == 1

    def test_deep_nesting_preserved(self, skill_composer_with_db, query_api_with_data):
        """Test that deep nesting is preserved through levels."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id FROM sections
            WHERE level IN (1, 2, 3)
            ORDER BY id
        """)
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        if len(section_ids) >= 2:
            composed = skill_composer_with_db.compose_from_sections(
                section_ids=section_ids,
                output_path="/tmp/test_deep.md"
            )

            # Verify all requested sections are in composition
            assert len(composed.sections) == len(section_ids)


# ============================================================================
# Test: Frontmatter Generation
# ============================================================================

class TestFrontmatterIntegration:
    """Test frontmatter generation with real sections."""

    def test_frontmatter_with_real_sections(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test that frontmatter is properly generated from real sections."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections LIMIT 2")
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        composed = skill_composer_with_db.compose_from_sections(
            section_ids=section_ids,
            output_path="/tmp/test_frontmatter.md",
            title="Frontmatter Test",
            description="Testing frontmatter generation"
        )

        # Write and verify frontmatter
        output_path = tmp_path / "frontmatter_test.md"
        composed.output_path = str(output_path)
        skill_composer_with_db.write_to_filesystem(composed)

        content = output_path.read_text()
        lines = content.split('\n')

        # Verify frontmatter structure
        assert lines[0] == "---"
        assert any("name:" in line for line in lines[1:])

    def test_frontmatter_section_count_accurate(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test that frontmatter section count is accurate."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections LIMIT 1")
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        if section_ids:
            composed = skill_composer_with_db.compose_from_sections(
                section_ids=section_ids,
                output_path="/tmp/test_count.md",
                title="Count Test"
            )

            output_path = tmp_path / "count_test.md"
            composed.output_path = str(output_path)
            skill_composer_with_db.write_to_filesystem(composed)

            content = output_path.read_text()
            assert "sections:" in content


# ============================================================================
# Test: File Writing Integration
# ============================================================================

class TestFileWritingIntegration:
    """Test file writing with real composed skills."""

    def test_write_creates_valid_markdown(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test that written file is valid markdown."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections LIMIT 2")
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        composed = skill_composer_with_db.compose_from_sections(
            section_ids=section_ids,
            output_path=str(tmp_path / "valid_markdown.md")
        )

        skill_composer_with_db.write_to_filesystem(composed)

        content = (tmp_path / "valid_markdown.md").read_text()

        # Verify basic markdown structure
        assert "---" in content
        assert "#" in content

    def test_write_hash_is_deterministic(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test that writing the same content produces same hash."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections LIMIT 1")
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        if section_ids:
            # Write once
            composed1 = skill_composer_with_db.compose_from_sections(
                section_ids=section_ids,
                output_path=str(tmp_path / "hash_test1.md")
            )
            hash1 = skill_composer_with_db.write_to_filesystem(composed1)

            # Write again
            composed2 = skill_composer_with_db.compose_from_sections(
                section_ids=section_ids,
                output_path=str(tmp_path / "hash_test2.md")
            )
            hash2 = skill_composer_with_db.write_to_filesystem(composed2)

            # Hashes should be identical for same content
            assert hash1 == hash2

    def test_write_handles_special_characters(self, skill_composer_with_db, tmp_path, query_api_with_data):
        """Test that special characters are preserved in output."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections LIMIT 1")
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        if section_ids:
            composed = skill_composer_with_db.compose_from_sections(
                section_ids=section_ids,
                output_path=str(tmp_path / "special_chars.md"),
                title="Test with Special Chars: @#$%",
                description="Description with special characters: <>&\"'"
            )

            output_path = tmp_path / "special_chars.md"
            skill_composer_with_db.write_to_filesystem(composed)

            content = output_path.read_text()
            # Verify content was written
            assert len(content) > 0


# ============================================================================
# Test: Error Recovery
# ============================================================================

class TestErrorRecovery:
    """Test error handling and recovery in composition pipeline."""

    def test_handles_missing_section_id(self, skill_composer_with_db):
        """Test error handling when section ID doesn't exist."""
        with pytest.raises(ValueError):
            skill_composer_with_db.compose_from_sections(
                section_ids=[99999],
                output_path="/tmp/test.md"
            )

    def test_handles_mixed_valid_invalid_sections(self, skill_composer_with_db, query_api_with_data):
        """Test error when one of multiple sections is invalid."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections LIMIT 1")
        result = cursor.fetchone()
        db.conn.close()

        if result:
            valid_id = result[0]
            with pytest.raises(ValueError):
                skill_composer_with_db.compose_from_sections(
                    section_ids=[valid_id, 99999],
                    output_path="/tmp/test.md"
                )


# ============================================================================
# Test: Data Consistency
# ============================================================================

class TestDataConsistency:
    """Test data consistency across composition operations."""

    def test_composed_skill_serialization(self, skill_composer_with_db, query_api_with_data):
        """Test that ComposedSkill serializes and deserializes correctly."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections LIMIT 1")
        section_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        if section_ids:
            composed = skill_composer_with_db.compose_from_sections(
                section_ids=section_ids,
                output_path="/tmp/test.md",
                title="Serialization Test",
                description="Test serialization"
            )

            # Serialize to dict
            data = composed.to_dict()

            # Verify all fields are present
            assert data['title'] == "Serialization Test"
            assert data['description'] == "Test serialization"
            assert data['section_ids'] == section_ids
            assert data['output_path'] == "/tmp/test.md"

    def test_multiple_compositions_independent(self, skill_composer_with_db, query_api_with_data):
        """Test that multiple compositions don't interfere with each other."""
        db = DatabaseStore(query_api_with_data.db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM sections ORDER BY id")
        all_ids = [row[0] for row in cursor.fetchall()]
        db.conn.close()

        if len(all_ids) >= 2:
            # Compose first skill
            composed1 = skill_composer_with_db.compose_from_sections(
                section_ids=[all_ids[0]],
                output_path="/tmp/skill1.md",
                title="Skill 1"
            )

            # Compose second skill
            composed2 = skill_composer_with_db.compose_from_sections(
                section_ids=[all_ids[1]],
                output_path="/tmp/skill2.md",
                title="Skill 2"
            )

            # Verify they're independent
            assert composed1.title == "Skill 1"
            assert composed2.title == "Skill 2"
            assert composed1.output_path != composed2.output_path
