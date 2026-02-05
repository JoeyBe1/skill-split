"""
Unit tests for QueryAPI class.

Tests cover all QueryAPI methods with focus on edge cases:
- get_section: found, not found, invalid file
- get_next_section: middle section, last section, no next
- get_section_tree: empty file, nested sections, flat sections
- search_sections: match found, no match, multi-file search
"""

import os
import sys
import hashlib
import sqlite3
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.query import QueryAPI
from core.database import DatabaseStore
from core.parser import Parser
from core.detector import FormatDetector
from models import FileFormat, FileType, Section


class TestGetSection:
    """Test QueryAPI.get_section method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.query = QueryAPI(self.temp_db.name)
        self.store = DatabaseStore(self.temp_db.name)
        self.parser = Parser()
        self.detector = FormatDetector()

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def _compute_hash(self, content):
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _store_file(self, file_path, content):
        """Parse and store a file, return file_id."""
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)
        return self.store.store_file(file_path, doc, content_hash)

    def test_get_section_found(self):
        """Test retrieving an existing section by ID."""
        content = """# Main Section

Main content.

## Subsection

Sub content.
"""
        file_path = "/test/get_section.md"
        self._store_file(file_path, content)

        # Get sections from DB to find IDs
        result = self.store.get_file(file_path)
        assert result is not None
        metadata, sections = result

        # Get the first section by ID
        section = self.query.get_section(sections[0].id if hasattr(sections[0], 'id') else 1)
        # Note: Sections from get_file don't have IDs stored; we need to query directly
        # Let's use a different approach - get sections via database directly
        with sqlite3.connect(self.query.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id FROM sections WHERE title = ? LIMIT 1",
                ("Main Section",)
            )
            row = cursor.fetchone()
            assert row is not None, "Main Section should exist in DB"
            section_id = row["id"]

        section = self.query.get_section(section_id)
        assert section is not None, "section should be found"
        assert section.title == "Main Section", "title should match"
        assert "Main content" in section.content, "content should match"

    def test_get_section_not_found(self):
        """Test retrieving a non-existent section returns None."""
        section = self.query.get_section(99999)
        assert section is None, "non-existent section should return None"

    def test_get_section_invalid_file(self):
        """Test get_section when file hasn't been loaded."""
        # Just try to get a section without storing anything
        section = self.query.get_section(1)
        assert section is None, "should return None when no data in DB"


class TestGetNextSection:
    """Test QueryAPI.get_next_section method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.query = QueryAPI(self.temp_db.name)
        self.store = DatabaseStore(self.temp_db.name)
        self.parser = Parser()
        self.detector = FormatDetector()

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def _compute_hash(self, content):
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _store_file(self, file_path, content):
        """Parse and store a file."""
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)
        self.store.store_file(file_path, doc, content_hash)

    def _get_section_ids(self, file_path):
        """Get list of all section IDs for a file in order."""
        with sqlite3.connect(self.query.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id FROM sections
                WHERE file_id = (SELECT id FROM files WHERE path = ?)
                ORDER BY order_index ASC
                """,
                (file_path,)
            )
            return [row["id"] for row in cursor.fetchall()]

    def test_get_next_section_middle(self):
        """Test getting next section from middle of document."""
        content = """# Section 1

Content 1.

# Section 2

Content 2.

# Section 3

Content 3.
"""
        file_path = "/test/next_middle.md"
        self._store_file(file_path, content)

        section_ids = self._get_section_ids(file_path)
        assert len(section_ids) >= 3, "should have 3 top-level sections"

        # Get next from first section
        next_section = self.query.get_next_section(section_ids[0], file_path)
        assert next_section is not None, "should have next section"
        assert next_section.title == "Section 2", "should get Section 2"

    def test_get_next_section_last(self):
        """Test get_next_section from last section returns None."""
        content = """# Section 1

Content 1.

# Section 2

Content 2.
"""
        file_path = "/test/next_last.md"
        self._store_file(file_path, content)

        section_ids = self._get_section_ids(file_path)
        assert len(section_ids) >= 2, "should have 2 sections"

        # Try to get next from last section
        next_section = self.query.get_next_section(section_ids[-1], file_path)
        assert next_section is None, "should return None for last section"

    def test_get_next_section_no_next(self):
        """Test get_next_section when no next sibling exists."""
        content = """# Parent

Content.

## Child

Child content.
"""
        file_path = "/test/next_no_next.md"
        self._store_file(file_path, content)

        with sqlite3.connect(self.query.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Get the child section
            cursor = conn.execute(
                "SELECT id FROM sections WHERE title = ? LIMIT 1",
                ("Child",)
            )
            child_id = cursor.fetchone()["id"]

        # Child has no next sibling
        next_section = self.query.get_next_section(child_id, file_path)
        assert next_section is None, "child should have no next sibling"

    def test_get_next_section_nonexistent_current(self):
        """Test get_next_section with non-existent current section."""
        content = """# Section 1

Content.
"""
        file_path = "/test/next_nonexistent.md"
        self._store_file(file_path, content)

        next_section = self.query.get_next_section(99999, file_path)
        assert next_section is None, "should return None for non-existent section"


class TestGetSectionTree:
    """Test QueryAPI.get_section_tree method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.query = QueryAPI(self.temp_db.name)
        self.store = DatabaseStore(self.temp_db.name)
        self.parser = Parser()
        self.detector = FormatDetector()

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def _compute_hash(self, content):
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _store_file(self, file_path, content):
        """Parse and store a file."""
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)
        self.store.store_file(file_path, doc, content_hash)

    def test_get_section_tree_empty_file(self):
        """Test get_section_tree on non-existent file returns empty list."""
        tree = self.query.get_section_tree("/nonexistent/file.md")
        assert tree == [], "should return empty list for non-existent file"

    def test_get_section_tree_nested_sections(self):
        """Test get_section_tree with nested hierarchy."""
        content = """# Root 1

Root 1 content.

## Child 1.1

Child 1.1 content.

### Grandchild 1.1.1

Grandchild content.

## Child 1.2

Child 1.2 content.

# Root 2

Root 2 content.
"""
        file_path = "/test/tree_nested.md"
        self._store_file(file_path, content)

        tree = self.query.get_section_tree(file_path)

        assert len(tree) == 2, "should have 2 root sections"
        assert tree[0].title == "Root 1", "first root should be Root 1"
        assert tree[1].title == "Root 2", "second root should be Root 2"

        # Check nested structure
        root1 = tree[0]
        assert len(root1.children) == 2, "Root 1 should have 2 children"
        assert root1.children[0].title == "Child 1.1"
        assert root1.children[1].title == "Child 1.2"

        # Check grandchild
        child1_1 = root1.children[0]
        assert len(child1_1.children) == 1, "Child 1.1 should have 1 grandchild"
        assert child1_1.children[0].title == "Grandchild 1.1.1"

        # Root 2 should have no children
        root2 = tree[1]
        assert len(root2.children) == 0, "Root 2 should have no children"

    def test_get_section_tree_flat_sections(self):
        """Test get_section_tree with flat (no nesting) structure."""
        content = """# Section 1

Content 1.

# Section 2

Content 2.

# Section 3

Content 3.
"""
        file_path = "/test/tree_flat.md"
        self._store_file(file_path, content)

        tree = self.query.get_section_tree(file_path)

        assert len(tree) == 3, "should have 3 root sections"
        for section in tree:
            assert len(section.children) == 0, "no section should have children"

        assert tree[0].title == "Section 1"
        assert tree[1].title == "Section 2"
        assert tree[2].title == "Section 3"


class TestSearchSections:
    """Test QueryAPI.search_sections method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.query = QueryAPI(self.temp_db.name)
        self.store = DatabaseStore(self.temp_db.name)
        self.parser = Parser()
        self.detector = FormatDetector()

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def _compute_hash(self, content):
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _store_file(self, file_path, content):
        """Parse and store a file."""
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)
        self.store.store_file(file_path, doc, content_hash)

    def test_search_sections_match_found_in_title(self):
        """Test search finding match in section title."""
        content = """# Python Guide

Python content.

# JavaScript Guide

JavaScript content.
"""
        file_path = "/test/search_title.md"
        self._store_file(file_path, content)

        results = self.query.search_sections("Python")
        assert len(results) > 0, "should find Python"
        assert any(section.title == "Python Guide" for _, section in results), \
            "should find Python Guide section"

    def test_search_sections_match_found_in_content(self):
        """Test search finding match in section content."""
        content = """# Guide

This is a guide about testing.

# Other

Different content.
"""
        file_path = "/test/search_content.md"
        self._store_file(file_path, content)

        results = self.query.search_sections("testing")
        assert len(results) > 0, "should find 'testing' in content"
        # The section containing "testing" should be in results
        found = False
        for section_id, section in results:
            if "testing" in section.content:
                found = True
                break
        assert found, "should find section with 'testing' in content"

    def test_search_sections_no_match(self):
        """Test search with no matching results."""
        content = """# Section 1

Content 1.

# Section 2

Content 2.
"""
        file_path = "/test/search_no_match.md"
        self._store_file(file_path, content)

        results = self.query.search_sections("NonExistentTerm")
        assert len(results) == 0, "should return empty list for no match"

    def test_search_sections_case_insensitive(self):
        """Test that search is case-insensitive."""
        content = """# Python Programming

Learn Python.

# JavaScript Basics

Learn JavaScript.
"""
        file_path = "/test/search_case.md"
        self._store_file(file_path, content)

        # Search for lowercase
        results_lower = self.query.search_sections("python")
        # Search for uppercase
        results_upper = self.query.search_sections("PYTHON")

        assert len(results_lower) > 0, "lowercase search should find matches"
        assert len(results_upper) > 0, "uppercase search should find matches"
        assert len(results_lower) == len(results_upper), "case-insensitive search should return same count"

    def test_search_sections_single_file(self):
        """Test search limited to single file."""
        content1 = """# Python

Python content.
"""
        content2 = """# JavaScript

JavaScript content.
"""
        file_path1 = "/test/search_file1.md"
        file_path2 = "/test/search_file2.md"

        self._store_file(file_path1, content1)
        self._store_file(file_path2, content2)

        # Search for "Python" in file1 only
        results = self.query.search_sections("Python", file_path=file_path1)
        assert len(results) > 0, "should find Python in file1"

        # Search for "Python" in file2 (should be empty)
        results = self.query.search_sections("Python", file_path=file_path2)
        assert len(results) == 0, "should not find Python in file2"

    def test_search_sections_multi_file_search(self):
        """Test cross-file search."""
        content1 = """# API Documentation

REST API details.
"""
        content2 = """# API Errors

Error handling guide.
"""
        file_path1 = "/test/search_api_1.md"
        file_path2 = "/test/search_api_2.md"

        self._store_file(file_path1, content1)
        self._store_file(file_path2, content2)

        # Search for "API" across all files
        results = self.query.search_sections("API")
        assert len(results) >= 2, "should find API in both files"

    def test_search_sections_returns_tuples(self):
        """Test that search returns (section_id, Section) tuples."""
        content = """# Test Section

Test content.
"""
        file_path = "/test/search_tuples.md"
        self._store_file(file_path, content)

        results = self.query.search_sections("Test")
        assert len(results) > 0, "should find results"

        # Each result should be a tuple
        for result in results:
            assert isinstance(result, tuple), "result should be a tuple"
            assert len(result) == 2, "tuple should have 2 elements"
            section_id, section = result
            assert isinstance(section_id, int), "section_id should be int"
            assert isinstance(section, Section), "second element should be Section"


class TestQueryAPIIntegration:
    """Integration tests combining multiple QueryAPI methods."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.query = QueryAPI(self.temp_db.name)
        self.store = DatabaseStore(self.temp_db.name)
        self.parser = Parser()
        self.detector = FormatDetector()

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def _compute_hash(self, content):
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _store_file(self, file_path, content):
        """Parse and store a file."""
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)
        self.store.store_file(file_path, doc, content_hash)

    def test_progressive_disclosure_workflow(self):
        """Test complete progressive disclosure workflow."""
        content = """# Getting Started

Start here.

# Installation

Install steps.

## Prerequisites

Prerequisites.

## Setup

Setup steps.

# Usage

Usage guide.
"""
        file_path = "/test/progressive.md"
        self._store_file(file_path, content)

        # 1. Get the tree to show structure
        tree = self.query.get_section_tree(file_path)
        assert len(tree) == 3, "should have 3 root sections"

        # 2. Get first section
        get_started = self.query.get_section(tree[0].id if hasattr(tree[0], 'id') else None)
        # Note: tree sections from get_section_tree don't have DB IDs
        # Use search to get section with ID
        search_results = self.query.search_sections("Getting Started", file_path)
        assert len(search_results) > 0, "should find Getting Started"
        section_id_1, section_1 = search_results[0]
        assert section_1.title == "Getting Started"

        # 3. Get next section
        next_section = self.query.get_next_section(section_id_1, file_path)
        assert next_section is not None, "should have next section"
        assert next_section.title == "Installation"

        # 4. Search within specific context
        install_results = self.query.search_sections("Prerequisites", file_path)
        assert len(install_results) > 0, "should find Prerequisites"


def run_tests():
    """Run all tests."""
    import traceback

    test_classes = [
        TestGetSection,
        TestGetNextSection,
        TestGetSectionTree,
        TestSearchSections,
        TestQueryAPIIntegration,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                method = getattr(instance, method_name)
                try:
                    instance.setup_method()
                    method()
                    passed += 1
                    print(f"OK {test_class.__name__}.{method_name}")
                except AssertionError as e:
                    failed += 1
                    print(f"FAIL {test_class.__name__}.{method_name}")
                    print(f"  {e}")
                except Exception as e:
                    failed += 1
                    print(f"ERROR {test_class.__name__}.{method_name}")
                    print(f"  {e}")
                    traceback.print_exc()
                finally:
                    try:
                        instance.teardown_method()
                    except Exception:
                        pass

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
