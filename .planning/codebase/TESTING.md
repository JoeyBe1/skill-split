# Testing Patterns

**Analysis Date:** 2026-02-08

## Test Framework

**Runner:**
- pytest 9.0.2
- Config: Uses default pytest configuration (no explicit `pytest.ini` or `pyproject.toml` found)

**Assertion Library:**
- Standard pytest `assert` statements
- No additional assertion libraries

**Plugins installed:**
- pytest-asyncio (async test support)
- pytest-benchmark (performance testing)
- pytest-mock (mocking utilities)
- pytest-cov (coverage reporting)
- pyfakefs (filesystem mocking)
- respx (HTTP mocking)

**Run Commands:**
```bash
# Run all tests
python -m pytest test/ -v

# Run specific test file
python -m pytest test/test_parser.py -v

# Run with coverage
python -m pytest test/ --cov

# Run specific test class
python -m pytest test/test_handlers/test_plugin_handler.py::TestPluginHandler

# Run tests with no traceback (summary only)
python -m pytest test/ -v --tb=no
```

**Current test count:**
- 470 tests passing (as of 2026-02-08)

## Test File Organization

**Location:**
- Tests co-located in `test/` directory at project root
- Test file structure mirrors source structure:
  - `test/test_parser.py` mirrors `core/parser.py`
  - `test/test_handlers/test_plugin_handler.py` mirrors `handlers/plugin_handler.py`
  - `test/test_handlers/test_config_handler.py` mirrors `handlers/config_handler.py`

**Naming:**
- Test files prefixed with `test_`: `test_parser.py`, `test_database.py`
- Test classes named `Test<ClassName>`: `TestParser`, `TestDatabaseStore`, `TestPluginHandler`
- Test methods named `test_<action>_<scenario>`:
  - `test_parse_simple_headings`
  - `test_detect_xml_tag_format`
  - `test_checkout_file_copies_to_target`

**Structure:**
```
test/
├── conftest.py                    # Shared fixtures
├── fixtures/                      # Test data files
│   ├── simple_skill.md
│   ├── no_frontmatter.md
│   ├── xml_tags.md
│   └── handlers/                 # Handler-specific fixtures
├── test_parser.py                # Parser tests
├── test_database.py              # Database tests
├── test_handlers/                # Handler tests
│   ├── test_plugin_handler.py
│   ├── test_config_handler.py
│   ├── test_hook_handler.py
│   └── test_script_handlers.py
└── test_integration/             # Integration tests
```

## Test Structure

**Suite Organization:**
```python
class TestParserHeadings:
    """Test heading-based parsing."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = Parser()

    def test_parse_simple_headings(self):
        """Test parsing simple heading structure."""
        content = """# Title

Content under title.

## Section 1

Content under section 1."""
        doc = self.parser.parse_headings(content)

        assert len(doc.sections) == 1
        assert doc.sections[0].title == "Title"
        assert doc.sections[0].level == 1
```

**Patterns:**
- `setup_method()` for test initialization (pytest standard)
- `teardown_method()` for cleanup (temp files, databases)
- Use descriptive docstrings for each test method
- Arrange-Act-Assert pattern in test bodies
- Minimal test interdependence (each test should stand alone)

**Fixture patterns:**
```python
@pytest.fixture
def plugin_dir():
    """Create a temporary directory with test plugin files."""
    temp_dir = tempfile.mkdtemp()
    plugin_path = Path(temp_dir) / "plugin.json"

    # Create test data
    plugin_data = {"name": "test-plugin", "version": "1.0.0"}
    with open(plugin_path, 'w') as f:
        json.dump(plugin_data, f, indent=2)

    yield str(plugin_path)

    # Cleanup
    shutil.rmtree(temp_dir)
```

**Teardown pattern:**
```python
def teardown_method(self):
    """Clean up temporary database file."""
    try:
        os.unlink(self.temp_db.name)
    except FileNotFoundError:
        pass
```

## Mocking

**Framework:** unittest.mock.MagicMock (via pytest-mock)

**Patterns:**
```python
@pytest.fixture
def mock_supabase_store():
    """Mock SupabaseStore for testing."""
    return MagicMock(spec=SupabaseStore)

def test_ingest_command_stores_files(self, mock_supabase_store, monkeypatch):
    """Test that ingest command parses and stores files."""
    # Mock the SupabaseStore import
    monkeypatch.setattr('skill_split.SupabaseStore',
                       lambda *args, **kwargs: mock_supabase_store)
    mock_supabase_store.store_file.return_value = str(uuid4())

    # Test code...

    assert mock_supabase_store.store_file.called
```

**What to Mock:**
- External services: SupabaseStore, CheckoutManager
- File I/O for integration tests (when not using temp files)
- Environment variables via `monkeypatch`
- Expensive operations (hash computation in some cases)

**What NOT to Mock:**
- Core parsing logic (Parser class)
- Database operations (use temp SQLite databases)
- Dataclass models
- Validation logic

**Monkeypatch usage:**
```python
def test_with_env_override(self, monkeypatch):
    """Test with environment variable override."""
    monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
    monkeypatch.setenv('SUPABASE_KEY', 'test-key')
    # Test code...
```

## Fixtures and Factories

**Test Data:**
```python
def _load_fixture(self, filename):
    """Load a fixture file."""
    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", filename
    )
    with open(fixture_path) as f:
        return f.read()
```

**Location:**
- `test/fixtures/` directory
- Fixture files mirror real file structure
- Common fixtures: `simple_skill.md`, `no_frontmatter.md`, `xml_tags.md`, `edge_cases.md`
- Handler fixtures in `test/fixtures/handlers/`

**Temp directory pattern:**
```python
def setup_method(self):
    """Setup test fixtures with temporary database file."""
    self.temp_db = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.db'
    )
    self.temp_db.close()
    self.store = DatabaseStore(self.temp_db.name)
```

**Shared fixtures (conftest.py):**
```python
@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database file for testing.

    This fixture provides a unique database path for each test,
    ensuring tests don't interfere with each other.
    """
    return str(tmp_path / "test.db")
```

## Coverage

**Requirements:** No explicit coverage target enforced

**View Coverage:**
```bash
python -m pytest test/ --cov
python -m pytest test/ --cov=core/parser
```

**Current coverage:**
- 470 tests passing
- Tests cover all major modules: parser, database, handlers, CLI
- Integration tests for checkout/checkin workflows
- Round-trip verification tests

## Test Types

**Unit Tests:**
- Test individual classes and methods in isolation
- Mock external dependencies
- Use temp databases for data layer
- Focus on single responsibility

**Integration Tests:**
- Test multiple components working together
- Test database operations end-to-end
- Test handler-to-database workflows
- Test CLI command flows

**E2E Tests:**
- Round-trip tests: parse -> store -> retrieve -> recompose
- Real file tests using fixture files
- Multi-file component tests (plugins, hooks)
- Shell scripts in `demo/` directory

**Handler Tests:**
- Test each handler type separately
- Test parsing, validation, related files
- Use temp directories with test files
- Test error conditions (missing files, invalid JSON)

## Common Patterns

**Async Testing:**
```python
# No async tests currently (all tests are synchronous)
# Framework installed (pytest-asyncio) but not actively used
```

**Error Testing:**
```python
def test_validate_missing_required_fields(self):
    """Test validation with missing required fields."""
    handler = PluginHandler(incomplete_file)
    result = handler.validate()

    assert not result.is_valid
    assert len(result.errors) > 0
    assert any("version" in e for e in result.errors)
```

**Database testing pattern:**
```python
def test_store_and_retrieve_file(self):
    """Store a parsed document, retrieve it, verify metadata matches."""
    content = self._load_fixture("simple_skill.md")
    file_path = "/skills/test-skill/SKILL.md"

    # Parse
    doc = self.parser.parse(file_path, content, file_type, file_format)
    content_hash = self._compute_hash(content)

    # Store
    file_id = self.store.store_file(file_path, doc, content_hash)
    assert file_id > 0

    # Retrieve
    result = self.store.get_file(file_path)
    assert result is not None

    metadata, sections = result
    assert metadata.path == file_path
    assert metadata.hash == content_hash
```

**Round-trip testing pattern:**
```python
def test_xml_round_trip_fixture(self):
    """Test round-trip of XML tag fixture file."""
    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "xml_tags.md"
    )
    with open(fixture_path) as f:
        original = f.read()

    # Parse
    file_type, file_format = self.detector.detect(fixture_path, original)
    doc = self.parser.parse(fixture_path, original, file_type, file_format)

    # Verify structure
    assert len(doc.sections) == 4
    assert doc.sections[0].title == "example"
```

**Command testing pattern:**
```python
def test_ingest_command_stores_files(self, tmp_path, mock_store, monkeypatch):
    """Test that ingest command parses and stores files."""
    # Setup test files
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    skill_file = skill_dir / "test_skill.md"
    skill_file.write_text("# Test")

    # Mock dependencies
    monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
    monkeypatch.setattr('skill_split.SupabaseStore',
                       lambda *args, **kwargs: mock_store)
    mock_store.store_file.return_value = str(uuid4())

    # Execute command
    from skill_split import cmd_ingest
    args = argparse.Namespace(source_dir=str(skill_dir))
    result = cmd_ingest(args)

    # Verify
    assert result == 0
    assert mock_store.store_file.called
```

## Test Data Management

**Fixture file organization:**
- `test/fixtures/simple_skill.md` - Basic skill with frontmatter
- `test/fixtures/no_frontmatter.md` - File without frontmatter
- `test/fixtures/xml_tags.md` - XML tag format examples
- `test/fixtures/edge_cases.md` - Edge case coverage
- `test/fixtures/handlers/` - Handler-specific test files

**Temp file cleanup:**
- Use `tempfile.mkdtemp()` with explicit `shutil.rmtree()` cleanup
- Use `tmp_path` fixture (pytest built-in) for auto-cleanup
- Try/except pattern for cleanup resilience

## CI/CD Testing

**Test execution:**
```bash
# Full test suite
python -m pytest test/ -v

# Quick smoke test
python -m pytest test/test_parser.py test/test_database.py -v

# Handler tests only
python -m pytest test/test_handlers/ -v
```

**Test categorization:**
- Unit tests: Fast, isolated, mock external deps
- Integration tests: Slower, real dependencies
- Round-trip tests: Verify data integrity
- Command tests: CLI interface testing

---

*Testing analysis: 2026-02-08*
