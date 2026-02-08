"""
Test for write_to_filesystem() method in SkillComposer (Task 6.1).

This test verifies that the write_to_filesystem() method correctly:
1. Creates output directory if needed
2. Writes composed skill to disk
3. Computes SHA256 hash for verification
4. Handles path validation
"""

import tempfile
from pathlib import Path
import pytest

from models import ComposedSkill, Section
from core.skill_composer import SkillComposer


class TestWriteToFilesystem:
    """Test the write_to_filesystem() method."""

    def test_write_to_filesystem_creates_file(self):
        """write_to_filesystem() creates file with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_skill.md"

            # Create sections
            section1 = Section(
                level=1,
                title="Introduction",
                content="This is the introduction\n",
                line_start=1,
                line_end=3
            )

            section2 = Section(
                level=2,
                title="Details",
                content="Here are the details\n",
                line_start=5,
                line_end=7
            )
            section1.add_child(section2)

            # Create ComposedSkill
            composed = ComposedSkill(
                section_ids=[1, 2],
                sections={1: section1, 2: section2},
                output_path=str(output_path),
                frontmatter="name: test-skill\ndescription: Test skill\n",
                title="Test Skill",
                description="A test skill"
            )

            # Create composer and write
            db_path = tempfile.mktemp(suffix=".db")
            composer = SkillComposer(db_path)
            hash_val = composer.write_to_filesystem(composed)

            # Verify file exists
            assert output_path.exists()

            # Verify hash is set
            assert hash_val is not None
            assert len(hash_val) == 64  # SHA256 hex length
            assert composed.composed_hash == hash_val

            # Verify file content starts with frontmatter
            content = output_path.read_text()
            assert content.startswith("---\n")
            assert "name: test-skill" in content
            assert "description: Test skill" in content

    def test_write_to_filesystem_creates_parent_directory(self):
        """write_to_filesystem() creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a nested path that doesn't exist yet
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "skill.md"

            section = Section(
                level=1,
                title="Main",
                content="Content\n",
                line_start=1,
                line_end=3
            )

            composed = ComposedSkill(
                section_ids=[1],
                sections={1: section},
                output_path=str(output_path),
                frontmatter="name: nested-skill\ndescription: Nested skill\n",
                title="Nested",
                description="Nested skill"
            )

            db_path = tempfile.mktemp(suffix=".db")
            composer = SkillComposer(db_path)
            hash_val = composer.write_to_filesystem(composed)

            # Parent directories should be created
            assert output_path.parent.exists()
            assert output_path.exists()
            assert hash_val is not None

    def test_write_to_filesystem_invalid_path_raises_error(self):
        """write_to_filesystem() raises error for invalid output_path."""
        db_path = tempfile.mktemp(suffix=".db")
        composer = SkillComposer(db_path)

        section = Section(
            level=1,
            title="Main",
            content="Content\n",
            line_start=1,
            line_end=3
        )

        # Invalid: empty path
        composed = ComposedSkill(
            section_ids=[1],
            sections={1: section},
            output_path="",  # Empty path
            frontmatter="name: test\ndescription: Test\n",
            title="Test",
            description="Test"
        )

        with pytest.raises(ValueError):
            composer.write_to_filesystem(composed)

    def test_write_to_filesystem_hash_consistency(self):
        """Hashes computed by write_to_filesystem() are consistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "skill.md"

            section = Section(
                level=1,
                title="Main",
                content="Consistent content\n",
                line_start=1,
                line_end=3
            )

            composed = ComposedSkill(
                section_ids=[1],
                sections={1: section},
                output_path=str(output_path),
                frontmatter="name: consistent\ndescription: Consistent\n",
                title="Consistent",
                description="Consistent"
            )

            db_path = tempfile.mktemp(suffix=".db")
            composer = SkillComposer(db_path)
            hash1 = composer.write_to_filesystem(composed)

            # Read file and compute hash independently
            from core.hashing import compute_file_hash
            hash2 = compute_file_hash(str(output_path))

            # Hashes should match
            assert hash1 == hash2
