# Testing Patterns

**Analysis Date:** 2026-02-08

## Test Framework

**Runner:**
- pytest 9.0.2
- Config: Standard pytest configuration
- Coverage: Enforced with pytest-cov

**Assertion Library:**
- Standard Python assert statements
- No external assertion libraries used

**Run Commands:**
```bash
# Run all tests
python -m pytest test/ -v

# Run specific test file
python -m pytest test/test_parser.py -v

# Run tests with coverage
python -m pytest test/ --cov=core --cov=handlers

# Run specific test class
python -m pytest test/test_handlers/test_plugin_handler.py::TestPluginHandler

# Run with verbose output
python -m pytest test/test_parser.py -vvs
```

## Test File Organization

**Location:**
- Tests in `test/` directory (co-located with source)
- Mirror directory structure of source code
- Integration tests in same files as unit tests

**Naming:**
- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<scenario>`

**Structure:**
```
test/
├── __init__.py
├── conftest.py                      # Shared fixtures
├── test_parser.py                   # Parser tests
├── test_database.py                  # Database tests
├── test_handlers/
│   ├── __init__.py
│   ├── test_plugin_handler.py
│   ├── test_script_handlers.py
│   └── ...
├── test_cli.py                      # CLI tests
└── test_composer_integration.py      # Integration tests
```

## Test Structure

**Suite Organization:**
```python
class TestParser:
    """Test suite for Parser class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = Parser()

    def test_extract_valid_frontmatter(self):
        """Test extraction of valid YAML frontmatter."""
        # Arrange
        content = "---\ntitle: Test\n---\nContent"

        # Act
        frontmatter, remaining = self.parser.extract_frontmatter(content)

        # Assert
        assert frontmatter == "title: Test"
        assert remaining == "Content"

    def test_extract_no_frontmatter(self):
        """Test handling of content without frontmatter."""
        content = "No frontmatter here"
        frontmatter, remaining = self.parser.extract_frontmatter(content)
        assert frontmatter == ""
        assert remaining == content
```

**Test Methods:**
- Setup via `setup_method()` (called before each test)
- No teardown needed in most cases
- Use descriptive test names that explain the scenario
- Arrange-Act-Assert pattern
- Clear separation of test phases

## Mocking

**Framework:** Built-in unittest.mock (no additional mocking library)

**Patterns:**
```python
import unittest.mock as mock

def test_database_connection(self):
    """Test lazy initialization of database connection."""
    # Create store with temporary file
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        store = DatabaseStore(tmp.name)

        # Mock the sqlite3.connect call
        with mock.patch('sqlite3.connect') as mock_connect:
            mock_conn = mock.MagicMock()
            mock_connect.return_value = mock_conn

            # Access property to trigger lazy init
            _ = store.conn

            # Verify connection was created
            mock_connect.assert_called_once()
```

**What to Mock:**
- External dependencies (sqlite3.connect, file I/O)
- Time-dependent operations
- Network calls
- Complex objects for isolation

**What NOT to Mock:**
- Core business logic
- Internal class interactions
- Simple data transformations
- Database operations (tested against real database)

## Fixtures and Factories

**Shared Fixtures (conftest.py):**
```python
import pytest

@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database file for testing.

    This fixture provides a unique database path for each test,
    ensuring tests don't interfere with each other.
    """
    return str(tmp_path / "test.db")

@pytest.fixture
def sample_skill_content():
    """Sample skill content for testing."""
    return """---
title: Test Skill
tags: [test, example]
---

# Overview
This is a test skill.

## Usage
```python
test_skill.run()
```
"""
```

**Custom Test Data:**
```python
def test_parse_with_code_blocks(self):
    """Test that code blocks are not split by headings."""
    content = """# Test Skill

## Section 1
Content here.

```python
def test_function():
    # This is inside a code block
    pass
```

## Section 2
More content."""

    # Test parsing...
```

## Test Categories

**Unit Tests:**
- Test individual methods in isolation
- Mock external dependencies
- Fast execution
- Focus on business logic

```python
def test_extract_frontmatter(self):
    """Test YAML frontmatter extraction."""
    parser = Parser()
    result = parser.extract_frontmatter("---\nkey: value\n---\ncontent")
    assert result == ("key: value", "content")
```

**Integration Tests:**
- Test multiple components together
- Use real databases where appropriate
- Test round-trip functionality
- Verify data flow between components

```python
def test_round_trip_skill(self):
    """Test that a skill can be parsed, stored, and recombined."""
    # Parse original skill
    parser = Parser()
    detector = FormatDetector()
    parsed = parser.parse_file(content, detector)

    # Store in database
    with DatabaseStore(":memory:") as store:
        store.store_file(parsed, "/test/skill.md")

        # Retrieve sections
        sections = store.get_sections_for_file("/test/skill.md")

        # Reconstruct
        recomposer = Recomposer(store)
        reconstructed = recomposer.reconstruct_file(parsed, sections)

        # Verify round-trip
        assert reconstructed == content
```

**System Tests:**
- End-to-end functionality
- Test real file operations
- CLI command testing

```python
def test_cli_parse_command(self):
    """Test the parse command through CLI."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md') as tmp:
        tmp.write(sample_skill_content)
        tmp.flush()

        result = subprocess.run([
            './skill_split.py', 'parse', tmp.name
        ], capture_output=True, text=True)

        assert result.returncode == 0
        assert "Section 1" in result.stdout
```

## Common Patterns

**Async Testing:**
```python
def test_database_operations(self):
    """Test database operations with context manager."""
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        with DatabaseStore(tmp.name) as store:
            # Test operations
            parser = Parser()
            detector = FormatDetector()
            parsed = parser.parse_file("test content", detector)
            store.store_file(parsed, "/test/file.md")

            # Verify
            sections = store.get_sections_for_file("/test/file.md")
            assert len(sections) == 1
```

**Error Testing:**
```python
def test_parse_malformed_frontmatter(self):
    """Test handling of malformed frontmatter."""
    content = "---\ninvalid: yaml\n---\n---\nmore content"

    with pytest.raises(ValueError) as exc_info:
        frontmatter, remaining = self.parser.extract_frontmatter(content)

    assert "malformed" in str(exc_info.value)
```

**Temporary Files:**
```python
def test_file_operations(self):
    """Test file operations with temporary files."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md') as tmp:
        tmp.write(test_content)
        tmp.flush()

        # Test reading and parsing
        detector = FormatDetector()
        file_type, file_format = detector.detect(tmp.name, test_content)

        assert file_type == FileType.SKILL
        assert file_format == FileFormat.MARKDOWN_HEADINGS
```

**Testing Database Operations:**
```python
def test_cascade_delete(self):
    """Test that deleting a file deletes its sections."""
    # Setup
    with DatabaseStore(":memory:") as store:
        # Store file with sections
        store.store_file(parsed_file, "/test/file.md")

        # Verify sections exist
        sections = store.get_sections_for_file("/test/file.md")
        assert len(sections) == 2

        # Delete file
        store.delete_file("/test/file.md")

        # Verify sections are gone
        sections = store.get_sections_for_file("/test/file.md")
        assert len(sections) == 0
```

## Coverage

**Requirements:**
- Target: 85% coverage
- Enforced through CI
- Reports generated as HTML

**View Coverage:**
```bash
# Generate coverage report
python -m pytest --cov=core --cov=handlers --cov-report=html

# View coverage in terminal
python -m pytest --cov=core --cov-report=term-missing

# Cover specific file
python -m pytest test/test_parser.py --cov=core/parser
```

**Critical Areas Covered:**
- All core methods in database.py
- Parser edge cases and error conditions
- Handler validation logic
- CLI command error handling
- Round-trip verification

---

*Testing analysis: 2026-02-08*
```