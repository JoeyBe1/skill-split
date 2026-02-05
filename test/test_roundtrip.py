"""
Round-trip verification tests for skill-split.

These tests verify that files can be:
1. Parsed into sections
2. Stored in the database
3. Recomposed back to original form
4. Verified against original content (hashes match)

This ensures no data loss occurs during the parse and storage process.

The recomposer is designed to achieve perfect round-trip integrity:
- Heading lines ARE preserved in section content
- Recomposed output WILL match original hash
- No duplication of child section content
- Progressive disclosure is maintained while preserving round-trip capability
"""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest

from core.database import DatabaseStore
from core.detector import FormatDetector
from core.hashing import compute_file_hash
from core.parser import Parser
from core.recomposer import Recomposer


class TestRoundTrip:
    """Test round-trip integrity: original -> parse -> DB -> recompose -> verify."""

    def setup_method(self):
        """Setup test fixtures with temporary database file."""
        # Use a temporary file database instead of :memory: to allow
        # multiple connections to see the same schema
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def test_round_trip_simple_skill(self):
        """Test round-trip with simple skill file with frontmatter.

        Verifies perfect round-trip: original_hash == recomposed_hash
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write("""---
name: test-skill
description: A simple test skill
version: 1.0.0
---

# Test Skill

This is a test skill file.

## Overview

This skill demonstrates basic structure.

### Details

Some detailed information here.

## Usage

Use this skill for testing purposes.
""")
            tmp_path = tmp.name

        try:
            # Setup: parser, detector, database (temp file)
            parser = Parser()
            detector = FormatDetector()
            db = DatabaseStore(self.temp_db.name)
            recomposer = Recomposer(db)

            # Step 1: Load original file and compute hash
            original_hash = compute_file_hash(tmp_path)
            assert original_hash, "Original file should have a hash"

            # Step 2: Read content and detect format
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            file_type, file_format = detector.detect(tmp_path, content)

            # Step 3: Parse the file
            parsed_doc = parser.parse(tmp_path, content, file_type, file_format)

            # Step 4: Store in database
            file_id = db.store_file(tmp_path, parsed_doc, original_hash)
            assert file_id > 0, "File should be stored with valid ID"

            # Step 5: Recompose from database
            recomposed_content = recomposer.recompose(tmp_path)
            assert recomposed_content is not None, "Recomposed content should not be None"

            # Step 6: Compute hash of recomposed content
            recomposed_hash = hashlib.sha256(recomposed_content.encode('utf-8')).hexdigest()

            # Verify perfect round-trip: hashes must match
            assert recomposed_hash == original_hash, (
                f"Round-trip failed: hashes do not match.\n"
                f"Original: {original_hash}\n"
                f"Recomposed: {recomposed_hash}\n"
                f"Original length: {len(content)}\n"
                f"Recomposed length: {len(recomposed_content)}\n"
                f"Original content:\n{content}\n"
                f"Recomposed content:\n{recomposed_content}"
            )

        finally:
            Path(tmp_path).unlink()

    def test_round_trip_no_frontmatter(self):
        """Test round-trip with file that has no YAML frontmatter.

        Verifies perfect round-trip: original_hash == recomposed_hash
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write("""# No Frontmatter

This file has no YAML frontmatter.

## Content

Just regular markdown content.
""")
            tmp_path = tmp.name

        try:
            # Setup
            parser = Parser()
            detector = FormatDetector()
            db = DatabaseStore(self.temp_db.name)
            recomposer = Recomposer(db)

            # Step 1: Load and hash original
            original_hash = compute_file_hash(tmp_path)

            # Step 2: Read content and detect format
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            file_type, file_format = detector.detect(tmp_path, content)

            # Step 3: Parse
            parsed_doc = parser.parse(tmp_path, content, file_type, file_format)

            # Step 4: Store
            db.store_file(tmp_path, parsed_doc, original_hash)

            # Step 5: Recompose
            recomposed_content = recomposer.recompose(tmp_path)
            assert recomposed_content is not None, "Should produce recomposed content"

            # Step 6: Verify perfect round-trip
            recomposed_hash = hashlib.sha256(recomposed_content.encode('utf-8')).hexdigest()
            assert recomposed_hash == original_hash, (
                f"Round-trip failed: hashes do not match.\n"
                f"Original: {original_hash}\n"
                f"Recomposed: {recomposed_hash}\n"
                f"Original length: {len(content)}\n"
                f"Recomposed length: {len(recomposed_content)}"
            )

        finally:
            Path(tmp_path).unlink()

    def test_round_trip_edge_cases(self):
        """Test round-trip with edge cases: code blocks, empty sections, nested sections.

        Verifies perfect round-trip: original_hash == recomposed_hash
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write("""---
name: edge-cases
version: 1.0.0
---

# Edge Cases

## Code Block With Heading

Should NOT split inside this code block:

```python
# This looks like a heading but isn't
def foo():
    pass
```

## Empty Section

### Subsection

Content here.

## Jump Levels

# Back to level 1

## Level 2 after level 1

### Level 3

## Level 2 again
""")
            tmp_path = tmp.name

        try:
            # Setup
            parser = Parser()
            detector = FormatDetector()
            db = DatabaseStore(self.temp_db.name)
            recomposer = Recomposer(db)

            # Round-trip process
            original_hash = compute_file_hash(tmp_path)

            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            file_type, file_format = detector.detect(tmp_path, content)
            parsed_doc = parser.parse(tmp_path, content, file_type, file_format)
            db.store_file(tmp_path, parsed_doc, original_hash)

            recomposed_content = recomposer.recompose(tmp_path)
            assert recomposed_content is not None

            recomposed_hash = hashlib.sha256(recomposed_content.encode('utf-8')).hexdigest()

            # Code blocks should NOT be split (parser should respect them)
            assert "```python" in recomposed_content, "Code blocks should be preserved"

            # Verify perfect round-trip
            assert recomposed_hash == original_hash, (
                f"Round-trip failed: hashes do not match.\n"
                f"Original: {original_hash}\n"
                f"Recomposed: {recomposed_hash}\n"
                f"Original length: {len(content)}\n"
                f"Recomposed length: {len(recomposed_content)}"
            )

        finally:
            Path(tmp_path).unlink()

    def test_round_trip_all_fixtures(self):
        """Test round-trip for all fixture files in test/fixtures directory.

        Verifies perfect round-trip for all fixtures: original_hash == recomposed_hash
        """
        # Setup
        parser = Parser()
        detector = FormatDetector()
        db = DatabaseStore(self.temp_db.name)
        recomposer = Recomposer(db)

        # Find all fixture files
        fixtures_dir = Path(__file__).parent / 'fixtures'
        fixture_files = list(fixtures_dir.glob('*.md'))

        assert fixture_files, "No fixture files found"

        results = {}

        for fixture_path in fixture_files:
            fixture_path_str = str(fixture_path)

            # Round-trip process
            original_hash = compute_file_hash(fixture_path_str)

            with open(fixture_path_str, 'r', encoding='utf-8') as f:
                content = f.read()

            file_type, file_format = detector.detect(fixture_path_str, content)
            parsed_doc = parser.parse(fixture_path_str, content, file_type, file_format)
            db.store_file(fixture_path_str, parsed_doc, original_hash)

            recomposed_content = recomposer.recompose(fixture_path_str)
            assert recomposed_content is not None, (
                f"Failed to recompose fixture: {fixture_path.name}"
            )

            recomposed_hash = hashlib.sha256(recomposed_content.encode('utf-8')).hexdigest()

            # Verify perfect round-trip
            hashes_match = recomposed_hash == original_hash
            results[fixture_path.name] = {
                'hashes_match': hashes_match,
                'original': original_hash,
                'recomposed': recomposed_hash,
            }

        # All fixtures should have matching hashes (perfect round-trip)
        failed_fixtures = [name for name, r in results.items() if not r['hashes_match']]
        assert not failed_fixtures, (
            f"The following fixtures failed round-trip verification: {failed_fixtures}\n"
            f"Results: {results}"
        )


class TestRoundTripPasses:
    """Tests verifying perfect round-trip behavior after recomposer fix.

    These tests verify that:
    - Headings ARE preserved in section content
    - NO duplication of child content occurs
    - Perfect round-trip is achieved: original_hash == recomposed_hash
    """

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def test_headings_preserved_in_content(self):
        """Verify that headings are preserved in recomposed content.

        The recomposer properly reconstructs heading lines from metadata,
        ensuring round-trip integrity is maintained.
        """
        content = """# Main Heading

Some content.

## Sub Heading

More content.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            parser = Parser()
            detector = FormatDetector()
            db = DatabaseStore(self.temp_db.name)
            recomposer = Recomposer(db)

            file_type, file_format = detector.detect(tmp_path, content)
            parsed_doc = parser.parse(tmp_path, content, file_type, file_format)

            # Verify headings are in metadata
            assert parsed_doc.sections[0].title == "Main Heading"
            assert parsed_doc.sections[0].children[0].title == "Sub Heading"

            # Store and recompose
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            db.store_file(tmp_path, parsed_doc, content_hash)
            recomposed = recomposer.recompose(tmp_path)

            # Verify headings are preserved in recomposed content
            assert "# Main Heading" in recomposed, "Main heading should be preserved"
            assert "## Sub Heading" in recomposed, "Sub heading should be preserved"

            # Verify perfect round-trip
            recomposed_hash = hashlib.sha256(recomposed.encode('utf-8')).hexdigest()
            assert recomposed_hash == content_hash, (
                f"Round-trip failed: hashes do not match.\n"
                f"Original: {content_hash}\n"
                f"Recomposed: {recomposed_hash}"
            )

        finally:
            Path(tmp_path).unlink()

    def test_child_content_not_duplicated_in_recompose(self):
        """Verify that child content is NOT duplicated in recomposed output.

        The recomposer properly handles parent-child relationships,
        ensuring each section's content appears exactly once.
        """
        content = """# Parent

Parent content.

## Child

Child content.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            parser = Parser()
            detector = FormatDetector()
            db = DatabaseStore(self.temp_db.name)
            recomposer = Recomposer(db)

            file_type, file_format = detector.detect(tmp_path, content)
            parsed_doc = parser.parse(tmp_path, content, file_type, file_format)

            # Store and recompose
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            db.store_file(tmp_path, parsed_doc, content_hash)
            recomposed = recomposer.recompose(tmp_path)

            # Child content should appear exactly once
            child_count = recomposed.count("Child content")
            assert child_count == 1, (
                f"Child content should appear exactly once, but appears {child_count} times"
            )

            # Verify perfect round-trip
            recomposed_hash = hashlib.sha256(recomposed.encode('utf-8')).hexdigest()
            assert recomposed_hash == content_hash, (
                f"Round-trip failed: hashes do not match.\n"
                f"Original: {content_hash}\n"
                f"Recomposed: {recomposed_hash}"
            )

        finally:
            Path(tmp_path).unlink()

    def test_perfect_round_trip_with_nested_sections(self):
        """Verify perfect round-trip with deeply nested sections.

        Tests that the recomposer handles multiple levels of nesting
        while maintaining exact content integrity.
        """
        content = """# Level 1

Content at level 1.

## Level 2

Content at level 2.

### Level 3

Content at level 3.

#### Level 4

Content at level 4.

## Back to Level 2

More level 2 content.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            parser = Parser()
            detector = FormatDetector()
            db = DatabaseStore(self.temp_db.name)
            recomposer = Recomposer(db)

            file_type, file_format = detector.detect(tmp_path, content)
            parsed_doc = parser.parse(tmp_path, content, file_type, file_format)

            # Store and recompose
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            db.store_file(tmp_path, parsed_doc, content_hash)
            recomposed = recomposer.recompose(tmp_path)

            # Verify all heading levels are preserved
            assert "# Level 1" in recomposed
            assert "## Level 2" in recomposed
            assert "### Level 3" in recomposed
            assert "#### Level 4" in recomposed

            # Verify each content section appears exactly once
            assert recomposed.count("Content at level 1") == 1
            assert recomposed.count("Content at level 2") == 1  # Both level 2 sections have different content
            assert recomposed.count("Content at level 3") == 1
            assert recomposed.count("Content at level 4") == 1
            assert recomposed.count("More level 2 content") == 1

            # Verify perfect round-trip
            recomposed_hash = hashlib.sha256(recomposed.encode('utf-8')).hexdigest()
            assert recomposed_hash == content_hash, (
                f"Round-trip failed: hashes do not match.\n"
                f"Original: {content_hash}\n"
                f"Recomposed: {recomposed_hash}"
            )

        finally:
            Path(tmp_path).unlink()

    def test_perfect_round_trip_with_frontmatter(self):
        """Verify perfect round-trip with YAML frontmatter.

        Tests that frontmatter is preserved exactly as in the original.
        """
        content = """---
name: test-skill
description: Test description
version: 1.0.0
tags:
  - test
  - example
---

# Heading

Content here.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            parser = Parser()
            detector = FormatDetector()
            db = DatabaseStore(self.temp_db.name)
            recomposer = Recomposer(db)

            file_type, file_format = detector.detect(tmp_path, content)
            parsed_doc = parser.parse(tmp_path, content, file_type, file_format)

            # Store and recompose
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            db.store_file(tmp_path, parsed_doc, content_hash)
            recomposed = recomposer.recompose(tmp_path)

            # Verify frontmatter is preserved
            assert recomposed.startswith("---")
            assert "name: test-skill" in recomposed
            assert "description: Test description" in recomposed
            assert "version: 1.0.0" in recomposed

            # Verify perfect round-trip
            recomposed_hash = hashlib.sha256(recomposed.encode('utf-8')).hexdigest()
            assert recomposed_hash == content_hash, (
                f"Round-trip failed: hashes do not match.\n"
                f"Original: {content_hash}\n"
                f"Recomposed: {recomposed_hash}"
            )

        finally:
            Path(tmp_path).unlink()


class TestRoundTripHelper:
    """Helper methods and utilities for round-trip testing.

    The helper methods assume perfect round-trip behavior is expected
    and will return failure if hashes do not match.
    """

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA256 hash of string content.

        Args:
            content: String content to hash

        Returns:
            SHA256 hexdigest string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def run_full_round_trip(file_path: str) -> tuple[bool, str, str]:
        """Run complete round-trip and return result.

        Args:
            file_path: Path to the file to test

        Returns:
            Tuple of (success: bool, original_hash: str, recomposed_hash: str)

        Note:
            Success means perfect round-trip: original_hash == recomposed_hash
        """
        parser = Parser()
        detector = FormatDetector()
        db = DatabaseStore(':memory:')
        recomposer = Recomposer(db)

        original_hash = compute_file_hash(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        file_type, file_format = detector.detect(file_path, content)
        parsed_doc = parser.parse(file_path, content, file_type, file_format)
        db.store_file(file_path, parsed_doc, original_hash)

        recomposed_content = recomposer.recompose(file_path)
        if recomposed_content is None:
            return False, original_hash, ""

        recomposed_hash = TestRoundTripHelper.compute_content_hash(recomposed_content)

        # Perfect round-trip means hashes must match
        return recomposed_hash == original_hash, original_hash, recomposed_hash
