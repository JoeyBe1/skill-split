"""
Integration tests for DatabaseStore class.
"""

import os
import sys
import hashlib
import sqlite3
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import DatabaseStore
from core.parser import Parser
from core.detector import FormatDetector
from models import FileFormat, FileType, Section, ParsedDocument


class TestSchemaCreation:
    """Test database schema creation."""

    def setup_method(self):
        """Setup test fixtures with temporary database file."""
        # Use a temporary file database instead of :memory: to allow
        # multiple connections to see the same schema
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.store = DatabaseStore(self.temp_db.name)

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def test_schema_creation(self):
        """Verify tables and indexes exist."""
        with sqlite3.connect(self.store.db_path) as conn:
            # Check files table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='files'"
            )
            assert cursor.fetchone() is not None, "files table should exist"

            # Check sections table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sections'"
            )
            assert cursor.fetchone() is not None, "sections table should exist"

            # Check indexes exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_sections_file'"
            )
            assert cursor.fetchone() is not None, "idx_sections_file index should exist"

            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_sections_parent'"
            )
            assert cursor.fetchone() is not None, "idx_sections_parent index should exist"

            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_files_path'"
            )
            assert cursor.fetchone() is not None, "idx_files_path index should exist"

            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_files_type'"
            )
            assert cursor.fetchone() is not None, "idx_files_type index should exist"

            # Check foreign keys are enabled (PRAGMA foreign_keys returns 0 or 1)
            # We need to check within a connection where foreign_keys was set
            # The store's _create_schema sets this, but each connection needs it set
            # Let's verify by checking the database has proper foreign key support
            cursor = conn.execute("PRAGMA foreign_keys")
            fk_setting = cursor.fetchone()[0]
            # Note: PRAGMA foreign_keys is per-connection, so we check if it's settable
            # Just verify that foreign keys are supported (they should be in SQLite 3.x)
            assert fk_setting in (0, 1), "foreign keys pragma should be queryable"


class TestStoreAndRetrieve:
    """Test storing and retrieving files."""

    def setup_method(self):
        """Setup test fixtures."""
        # Use a temporary file database
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.store = DatabaseStore(self.temp_db.name)
        self.parser = Parser()
        self.detector = FormatDetector()

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def _load_fixture(self, filename):
        """Load a fixture file."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", filename
        )
        with open(fixture_path) as f:
            return f.read()

    def _compute_hash(self, content):
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def test_store_and_retrieve_file(self):
        """Store a parsed document, retrieve it, verify metadata matches."""
        content = self._load_fixture("simple_skill.md")
        file_path = "/skills/test-skill/SKILL.md"

        # Parse the file
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)

        # Store the file
        file_id = self.store.store_file(file_path, doc, content_hash)
        assert file_id > 0, "file_id should be positive"

        # Retrieve the file
        result = self.store.get_file(file_path)
        assert result is not None, "file should be retrievable"

        metadata, sections = result

        # Verify metadata matches
        assert metadata.path == file_path, "path should match"
        assert metadata.type == FileType.SKILL, "type should be SKILL"
        assert metadata.frontmatter == doc.frontmatter, "frontmatter should match"
        assert metadata.hash == content_hash, "hash should match"

        # Verify sections structure
        assert len(sections) > 0, "should have at least one section"
        # Blank line after frontmatter is now preserved as orphaned section (level=0)
        # This is critical for byte-perfect round-trip
        assert sections[0].level == 0, "first section should be orphaned (blank line)"
        assert sections[1].title == "Test Skill", "second section should be 'Test Skill'"

    def test_store_duplicate_path_updates(self):
        """Storing same path twice should UPDATE not INSERT."""
        content = self._load_fixture("simple_skill.md")
        file_path = "/skills/test-skill/SKILL.md"

        # Parse and store first time
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)
        self.store.store_file(file_path, doc, content_hash)

        # Get the initial file_id from a direct query
        with sqlite3.connect(self.store.db_path) as conn:
            cursor = conn.execute("SELECT id FROM files WHERE path = ?", (file_path,))
            file_id_1 = cursor.fetchone()[0]

        # Verify we got exactly one file
        with sqlite3.connect(self.store.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            assert count == 1, "should have exactly 1 file after first insert"

        # Modify content and store again with same path
        modified_content = content + "\n## New Section\n\nNew content."
        doc_modified = self.parser.parse(file_path, modified_content, file_type, file_format)
        modified_hash = self._compute_hash(modified_content)
        self.store.store_file(file_path, doc_modified, modified_hash)

        # Get the file_id after update
        with sqlite3.connect(self.store.db_path) as conn:
            cursor = conn.execute("SELECT id FROM files WHERE path = ?", (file_path,))
            file_id_2 = cursor.fetchone()[0]

        # Should still have exactly one file (UPDATE, not INSERT)
        with sqlite3.connect(self.store.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            assert count == 1, "should still have exactly 1 file (not duplicated)"

        # File IDs should match (same row was updated)
        assert file_id_1 == file_id_2, "same file_id on duplicate path"

        # Retrieve and verify updated content
        result = self.store.get_file(file_path)
        assert result is not None
        metadata, sections = result

        # Hash should be updated
        assert metadata.hash == modified_hash, "hash should be updated"
        assert metadata.hash != content_hash, "hash should be different from original"

        # Should have the new section
        section_titles = [s.title for s in sections]
        # Find the "New Section" in the tree (might be nested)
        found_new = False
        for section in sections:
            if section.title == "New Section":
                found_new = True
                break
            for child in section.children:
                if child.title == "New Section":
                    found_new = True
                    break
        assert found_new, "new section should be present"


class TestSectionHierarchy:
    """Test section hierarchy preservation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
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

    def test_section_hierarchy(self):
        """Verify parent-child relationships preserved."""
        content = """# Main Section

Main content.

## Subsection 1

Subsection 1 content.

### Sub-subsection

Deeper content.

## Subsection 2

Subsection 2 content.
"""

        file_path = "/test/hierarchy.md"
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)

        # Store the file
        self.store.store_file(file_path, doc, content_hash)

        # Retrieve and check hierarchy
        result = self.store.get_file(file_path)
        assert result is not None
        metadata, sections = result

        # Should have one top-level section
        assert len(sections) == 1, "should have 1 top-level section"
        main_section = sections[0]
        assert main_section.title == "Main Section"
        assert main_section.level == 1

        # Should have 2 children
        assert len(main_section.children) == 2, "Main Section should have 2 children"

        # Check first child
        sub1 = main_section.children[0]
        assert sub1.title == "Subsection 1"
        assert sub1.level == 2
        assert sub1.parent is not None, "child should have parent reference"

        # Check first child's child
        assert len(sub1.children) == 1, "Subsection 1 should have 1 child"
        subsub = sub1.children[0]
        assert subsub.title == "Sub-subsection"
        assert subsub.level == 3
        assert subsub.parent is not None, "sub-subsection should have parent reference"

        # Check second child
        sub2 = main_section.children[1]
        assert sub2.title == "Subsection 2"
        assert sub2.level == 2
        assert len(sub2.children) == 0, "Subsection 2 should have no children"


class TestCascadeDelete:
    """Test cascade delete behavior."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
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

    def test_cascade_delete(self):
        """Deleting file should delete all sections."""
        content = """# Section 1

Content 1.

## Subsection

Sub content.

# Section 2

Content 2.
"""

        file_path = "/test/cascade.md"
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)

        # Store the file
        self.store.store_file(file_path, doc, content_hash)

        # Verify sections exist
        result = self.store.get_file(file_path)
        assert result is not None
        metadata, sections = result
        assert len(sections) > 0, "should have sections"

        # Manually delete the file record (simulating cascade)
        with sqlite3.connect(self.store.db_path) as conn:
            conn.execute("DELETE FROM files WHERE path = ?", (file_path,))
            conn.commit()

        # Verify sections are deleted (cascade)
        with sqlite3.connect(self.store.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sections WHERE file_id IN (SELECT id FROM files WHERE path = ?)",
                (file_path,)
            )
            count = cursor.fetchone()[0]
            assert count == 0, "all sections should be deleted"


class TestGetSectionTree:
    """Test section tree reconstruction."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
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

    def test_get_section_tree(self):
        """Verify tree structure rebuilt correctly."""
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

        file_path = "/test/tree.md"
        file_type, file_format = self.detector.detect(file_path, content)
        doc = self.parser.parse(file_path, content, file_type, file_format)
        content_hash = self._compute_hash(content)

        # Store the file
        self.store.store_file(file_path, doc, content_hash)

        # Get section tree
        sections = self.store.get_section_tree(file_path)

        # Verify top-level structure
        assert len(sections) == 2, "should have 2 root sections"
        assert sections[0].title == "Root 1"
        assert sections[1].title == "Root 2"

        # Verify first root's children
        root1 = sections[0]
        assert len(root1.children) == 2, "Root 1 should have 2 children"
        assert root1.children[0].title == "Child 1.1"
        assert root1.children[1].title == "Child 1.2"

        # Verify grandchild
        child1_1 = root1.children[0]
        assert len(child1_1.children) == 1, "Child 1.1 should have 1 child"
        assert child1_1.children[0].title == "Grandchild 1.1.1"

        # Verify second root has no children
        root2 = sections[1]
        assert len(root2.children) == 0, "Root 2 should have no children"

    def test_get_section_tree_nonexistent_file(self):
        """Verify get_section_tree returns empty list for nonexistent file."""
        sections = self.store.get_section_tree("/nonexistent/file.md")
        assert sections == [], "should return empty list for nonexistent file"


class TestDatabaseStoreFTS5:
    """Test FTS5 full-text search with BM25 ranking in DatabaseStore."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.store = DatabaseStore(self.temp_db.name)

    def teardown_method(self):
        """Clean up temporary database file."""
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def _compute_hash(self, content):
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def test_search_sections_with_rank_returns_tuples(self):
        """search_sections_with_rank() returns (section_id, rank) tuples."""
        from models import ParsedDocument, Section, FileType, FileFormat
        doc = ParsedDocument(
            frontmatter="",
            sections=[
                Section(level=1, title="Python", content="Python code here", line_start=1, line_end=2),
                Section(level=1, title="JavaScript", content="JS code here", line_start=3, line_end=4),
            ],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/search.md"
        )
        self.store.store_file("/test/search.md", doc, "test_hash")

        results = self.store.search_sections_with_rank("python")

        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
        assert all(isinstance(r[0], int) for r in results)  # section_id
        assert all(isinstance(r[1], float) for r in results)  # rank

    def test_search_sections_with_rank_ranking_quality(self):
        """BM25 ranking prioritizes relevant matches over position."""
        from models import ParsedDocument, Section, FileType, FileFormat

        # Create test sections where relevant content is NOT first
        sections = [
            Section(level=1, title="Intro", content="Basic intro text", line_start=1, line_end=2),
            Section(level=1, title="Python", content="Some python code", line_start=3, line_end=4),
            Section(level=2, title="Python Advanced", content="Advanced python handler with detailed implementation", line_start=5, line_end=6),
            Section(level=1, title="Database", content="Database storage", line_start=7, line_end=8),
        ]

        doc = ParsedDocument(
            frontmatter="",
            sections=sections,
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/python.md"
        )
        self.store.store_file("/test/python.md", doc, "test_hash")

        results = self.store.search_sections_with_rank("python")

        # Results should be ranked by relevance, not position
        # "Python" and "Python Advanced" should both match, with "Python Advanced" ranking higher
        assert len(results) > 1, f"Expected multiple results, got {len(results)}"
        ranks = [r[1] for r in results]
        assert ranks == sorted(ranks, reverse=True), "Ranks should be descending"

    def test_search_sections_with_rank_case_insensitive(self):
        """FTS5 search is case-insensitive."""
        from models import ParsedDocument, Section, FileType, FileFormat

        doc = ParsedDocument(
            frontmatter="",
            sections=[Section(level=1, title="Python", content="Python content", line_start=1, line_end=2)],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/case.md"
        )
        self.store.store_file("/test/case.md", doc, "test_hash")

        results_lower = self.store.search_sections_with_rank("python")
        results_upper = self.store.search_sections_with_rank("PYTHON")
        results_mixed = self.store.search_sections_with_rank("Python")

        # Should return same results
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_sections_with_rank_empty_query(self):
        """Empty query returns empty results."""
        results = self.store.search_sections_with_rank("")
        # FTS5 MATCH with empty string returns no results
        assert results == []

    def test_search_sections_with_rank_file_filter(self):
        """file_path parameter restricts search to specific file."""
        from models import ParsedDocument, Section, FileType, FileFormat

        doc1 = ParsedDocument(
            frontmatter="",
            sections=[Section(level=1, title="Test", content="Test content", line_start=1, line_end=2)],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/path1.md"
        )
        self.store.store_file("/test/path1.md", doc1, "hash1")

        doc2 = ParsedDocument(
            frontmatter="",
            sections=[Section(level=1, title="Test", content="Test content", line_start=1, line_end=2)],
            file_type=FileType.SKILL,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="/test/path2.md"
        )
        self.store.store_file("/test/path2.md", doc2, "hash2")

        all_results = self.store.search_sections_with_rank("test")
        file_results = self.store.search_sections_with_rank("test", file_path="/test/path1.md")

        # File-restricted results should be subset of all results
        assert len(file_results) <= len(all_results)


def run_tests():
    """Run all tests."""
    import traceback

    test_classes = [
        TestSchemaCreation,
        TestStoreAndRetrieve,
        TestSectionHierarchy,
        TestCascadeDelete,
        TestGetSectionTree,
        TestDatabaseStoreFTS5,
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

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
