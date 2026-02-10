# Testing Guide

**Last Updated:** 2026-02-10

Comprehensive guide for testing skill-split.

---

## Test Structure

```
test/
├── test_parser.py              # Parser tests
├── test_database.py            # Database tests
├── test_query.py               # Query API tests
├── test_recomposer.py          # Round-trip tests
├── test_hashing.py             # Hash verification tests
├── test_supabase_store.py      # Supabase tests
├── test_checkout_manager.py    # Checkout/checkin tests
├── test_handlers/              # Handler tests
│   ├── test_plugin_handler.py
│   ├── test_hook_handler.py
│   ├── test_config_handler.py
│   └── test_script_handlers.py
└── integration/                # Integration tests
```

---

## Running Tests

### Run All Tests

```bash
python -m pytest test/ -v
```

### Run Specific Test File

```bash
python -m pytest test/test_parser.py -v
```

### Run Specific Test Class

```bash
python -m pytest test/test_handlers/test_plugin_handler.py::TestPluginHandler -v
```

### Run Specific Test

```bash
python -m pytest test/test_parser.py::TestParser::test_parse_markdown -v
```

### Run with Coverage

```bash
python -m pytest test/ --cov=. --cov-report=term-missing
```

### Generate HTML Coverage Report

```bash
python -m pytest test/ --cov=. --cov-report=html
open htmlcov/index.html
```

---

## Test Categories

### Unit Tests

Test individual components in isolation.

**Example:**
```python
def test_extract_frontmatter():
    """Test frontmatter extraction."""
    content = """---
key: value
---

# Heading"""
    frontmatter, body = extract_frontmatter(content)
    assert frontmatter == {"key": "value"}
```

### Integration Tests

Test multiple components working together.

**Example:**
```python
def test_parse_store_retrieve():
    """Test parse -> store -> retrieve workflow."""
    doc = parser.parse(content, "test.md")
    db.store_document(doc)
    retrieved = db.get_section(doc.sections[0].id)
    assert retrieved.heading == doc.sections[0].heading
```

### Round-Trip Tests

Verify byte-perfect reconstruction.

**Example:**
```python
def test_round_trip_integrity():
    """Test byte-perfect round-trip."""
    original = read_file("test.md")
    doc = parser.parse(original, "test.md")
    reconstructed = recomposer.recompose(doc)
    assert hash_content(original) == hash_content(reconstructed)
```

---

## Writing Tests

### Test Structure

```python
import pytest
from core.parser import Parser

class TestParser:
    """Parser tests."""

    def setup_method(self):
        """Setup before each test."""
        self.parser = Parser()

    def test_parse_markdown(self):
        """Test markdown parsing."""
        content = "# Heading\n\nContent"
        doc = self.parser.parse(content, "test.md")
        assert len(doc.sections) == 1
        assert doc.sections[0].heading == "Heading"

    def test_parse_empty_file(self):
        """Test empty file handling."""
        with pytest.raises(ValueError):
            self.parser.parse("", "empty.md")
```

### Parametrized Tests

```python
@pytest.mark.parametrize("file_type,extension", [
    ("markdown", ".md"),
    ("yaml", ".yaml"),
    ("xml", ".xml"),
])
def test_detect_file_type(file_type, extension):
    """Test file type detection."""
    detected = detect_file_type(f"test{extension}")
    assert detected == file_type
```

### Fixtures

```python
@pytest.fixture
def sample_document():
    """Create a sample document."""
    return ParsedDocument(
        path="test.md",
        format=FileFormat.MARKDOWN,
        sections=[
            Section(id=1, heading="H1", level=1, content="Content"),
            Section(id=2, heading="H2", level=2, content="More content"),
        ]
    )

def test_with_fixture(sample_document):
    """Test using fixture."""
    assert len(sample_document.sections) == 2
```

---

## Benchmark Tests

### Run Benchmarks

```bash
python -m pytest benchmark/bench.py --benchmark-only
```

### Compare Against Baseline

```bash
python -m pytest benchmark/bench.py --benchmark-only --benchmark-compare-fail=mean:10%
```

### Generate Histogram

```bash
python -m pytest benchmark/bench.py --benchmark-only --benchmark-histogram
```

---

## CI/CD Testing

### GitHub Actions

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request

**Test Matrix:**
- OS: Ubuntu, macOS, Windows
- Python: 3.10, 3.11, 3.12, 3.13

### Local Pre-Commit

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Test Data

### Sample Files

```
test/data/
├── markdown/
│   ├── simple.md
│   ├── complex.md
│   └── frontmatter.md
├── yaml/
│   └── config.yaml
└── xml/
    └── component.xml
```

### Creating Test Data

```python
def create_test_file(content: str, path: str):
    """Create a temporary test file."""
    with open(path, 'w') as f:
        f.write(content)
    return path
```

---

## Debugging Tests

### Verbose Output

```bash
python -m pytest test/test_parser.py -vv -s
```

### Drop into PDB on Failure

```bash
python -m pytest test/test_parser.py --pdb
```

### Stop at First Failure

```bash
python -m pytest test/ -x
```

### Show Local Variables

```bash
python -m pytest test/test_parser.py -l
```

---

## Coverage Goals

### Current Coverage

- **Overall**: 95%+
- **Core modules**: 98%+
- **Handlers**: 95%+
- **CLI**: 90%+

### Coverage by Module

| Module | Coverage | Target |
|--------|----------|--------|
| parser.py | 98% | 95% |
| database.py | 97% | 95% |
| query.py | 96% | 95% |
| recomposer.py | 100% | 95% |

---

## Best Practices

### 1. Test Naming

Use descriptive names that explain what is being tested.

```python
def test_search_returns_sections_matching_query()  # Good
def test_search()                                  # Bad
```

### 2. One Assertion Per Test

```python
def test_section_has_id():
    assert section.id is not None

def test_section_has_heading():
    assert section.heading is not None
```

### 3. Use Context Managers

```python
def test_with_temp_file():
    with tempfile.NamedTemporaryFile() as f:
        f.write(content)
        f.flush()
        result = parse_file(f.name)
        assert result is not None
```

### 4. Clean Up Resources

```python
def test_with_database():
    db = DatabaseStore(":memory:")
    try:
        # Test code
        pass
    finally:
        db.close()
```

---

## Continuous Testing

### Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw test/ -- -v
```

### Parallel Testing

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest test/ -n auto
```

---

*For pytest configuration, see `pytest.ini` or `pyproject.toml`*
