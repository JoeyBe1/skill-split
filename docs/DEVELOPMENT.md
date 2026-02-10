# Development Guide

**Last Updated:** 2026-02-10

This guide is for developers who want to contribute to or extend skill-split.

---

## Quick Start

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/joeymafella/skill-split.git
cd skill-split

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify setup
python -m pytest test/ -v
```

### Project Structure

```
skill-split/
├── core/                    # Core modules
│   ├── parser.py           # Markdown/YAML parsing
│   ├── database.py         # SQLite operations
│   ├── query.py            # Query API
│   ├── recomposer.py       # File reconstruction
│   ├── validator.py        # Validation logic
│   └── embedding_service.py # Vector embeddings
├── handlers/               # File type handlers
│   ├── base.py            # Base handler class
│   ├── factory.py         # Handler factory
│   └── *_handler.py       # Specific handlers
├── models.py               # Data models
├── skill_split.py          # CLI entry point
├── test/                   # Test suite
├── benchmark/              # Performance benchmarks
├── docs/                   # Documentation
└── examples/               # Usage examples
```

---

## Architecture

### Core Components

#### Parser (core/parser.py)

Extracts structure from markdown files:

```python
from core.parser import Parser

parser = Parser()
document = parser.parse(content, "file.md")

# Document contains:
# - sections: List of Section objects
# - metadata: FileMetadata
# - format: FileType enum
```

**Key Design:**
- Heading detection (`#`, `##`, etc.)
- Frontmatter extraction (YAML between `---`)
- XML tag support (`<tag>content</tag>`)
- Hierarchy tracking (parent-child relationships)

#### Database (core/database.py)

SQLite storage with CASCADE delete:

```python
from core.database import DatabaseStore

db = DatabaseStore("database.db")
db.store_document(document)

# Key operations:
section = db.get_section(section_id)
sections = db.get_sections_by_file(file_path)
results = db.search_sections(query)
```

**Schema:**
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    hash TEXT,
    metadata TEXT
);

CREATE TABLE sections (
    id INTEGER PRIMARY KEY,
    file_id INTEGER,
    parent_id INTEGER,
    level INTEGER,
    heading TEXT,
    content TEXT,
    order_in_parent INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES sections(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE sections_fts USING fts5(
    content, file_path, section_id,
    content_rowid='sections'
);
```

#### Query API (core/query.py)

Progressive disclosure interface:

```python
from core.query import QueryAPI

api = QueryAPI(db)

# Navigation
section = api.get_section(section_id)
next_section = api.get_next_section(section_id)
children = api.get_child_sections(section_id)

# Search
results = api.search("query")
```

#### Recomposer (core/recomposer.py)

Byte-perfect file reconstruction:

```python
from core.recomposer import Recomposer

recomposer = Recomposer()
original_content = recomposer.recompose(document)

# Includes:
# - Frontmatter
# - All sections with markers
# - Original spacing/formatting
```

---

## Adding Features

### Creating a New Handler

```python
# handlers/my_format_handler.py

from handlers.base import BaseHandler

class MyFormatHandler(BaseHandler):
    """Handle custom file format."""

    def can_parse(self, file_path: str, content: str) -> bool:
        """Check if this handler can parse the file."""
        return file_path.endswith('.myformat')

    def parse(self, content: str, file_path: str) -> ParsedDocument:
        """Parse content into sections."""
        sections = []
        # Custom parsing logic here
        return ParsedDocument(
            sections=sections,
            metadata=FileMetadata(
                path=file_path,
                format=FileType.CUSTOM,
                section_count=len(sections)
            )
        )
```

Register in `handlers/factory.py`:

```python
from handlers.my_format_handler import MyFormatHandler

HANDLERS = [
    # ... existing handlers
    MyFormatHandler(),
]
```

### Adding a CLI Command

```python
# In skill_split.py

@click.command()
@click.argument('input_file')
@click.option('--output', '-o', help='Output file')
def my_command(input_file, output):
    """My custom command."""
    parser = Parser()
    document = parser.parse_file(input_file)

    # Do something with document

    if output:
        with open(output, 'w') as f:
            f.write(result)

# Add to CLI group
cli.add_command(my_command)
```

### Adding Search Mode

```python
# In core/query.py or core/hybrid_search.py

class CustomSearch:
    def __init__(self, db):
        self.db = db

    def search(self, query: str, limit: int = 10):
        """Custom search implementation."""
        results = []
        # Custom search logic
        return results
```

---

## Testing

### Writing Tests

```python
# test/test_my_feature.py

import pytest
from core.parser import Parser
from core.database import DatabaseStore

class TestMyFeature:
    @pytest.fixture
    def parser(self):
        return Parser()

    @pytest.fixture
    def temp_db(self, tmp_path):
        db_path = tmp_path / "test.db"
        return DatabaseStore(str(db_path))

    def test_basic_functionality(self, parser, temp_db):
        """Test basic functionality."""
        content = """
# Test Heading

Test content.
"""
        document = parser.parse(content, "test.md")
        temp_db.store_document(document)

        # Assertions
        assert len(document.sections) == 1
        assert document.sections[0].heading == "Test Heading"

    def test_edge_case(self, parser):
        """Test edge cases."""
        with pytest.raises(ValueError):
            parser.parse("", "empty.md")
```

### Running Tests

```bash
# All tests
python -m pytest test/ -v

# Specific test file
python -m pytest test/test_parser.py -v

# Specific test class
python -m pytest test/test_parser.py::TestParser -v

# With coverage
python -m pytest test/ --cov=core --cov-report=html

# Run fast tests only
python -m pytest test/ -m "not slow"
```

### Test Organization

```
test/
├── test_parser.py          # Parser tests
├── test_database.py        # Database tests
├── test_query.py           # Query API tests
├── test_handlers/          # Handler tests
│   ├── test_plugin_handler.py
│   └── test_python_handler.py
├── test_integration/       # Integration tests
└── conftest.py             # Shared fixtures
```

---

## Debugging

### Enable Debug Logging

```bash
# Set environment variable
export DEBUG=1

# Run with debug output
./skill_split.py parse file.md
```

### Python Debugger

```python
import pdb

def my_function():
    pdb.set_trace()  # Breakpoint
    # Code to debug
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug skill-split",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/skill_split.py",
            "args": ["parse", "test.md"],
            "console": "integratedTerminal",
            "env": {
                "DEBUG": "1"
            }
        }
    ]
}
```

---

## Performance Profiling

### Profile Parser

```bash
python -m cProfile -o profile.stats skill_split.py parse large_file.md

# Analyze
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
"
```

### Memory Profiling

```bash
pip install memory_profiler

python -m memory_profiler skill_split.py parse large_file.md
```

### Benchmark

```bash
cd benchmark
python bench.py
```

---

## Code Style

### Formatting

```bash
# Install dev dependencies
pip install black ruff

# Format code
black .

# Lint
ruff check .

# Auto-fix lint issues
ruff check . --fix
```

### Type Hints

```python
from typing import List, Optional
from models import Section, ParsedDocument

def parse_sections(content: str) -> List[Section]:
    """Parse content into sections."""
    sections: List[Section] = []
    # Parsing logic
    return sections
```

### Docstrings

```python
def search_sections(query: str, limit: int = 10) -> List[Section]:
    """
    Search for sections matching query.

    Args:
        query: Search query string
        limit: Maximum results to return

    Returns:
        List of matching sections

    Raises:
        DatabaseError: If query fails

    Example:
        >>> results = search_sections("python")
        >>> len(results) <= 10
        True
    """
```

---

## Contributing

### Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes with tests
4. Ensure all tests pass: `python -m pytest test/ -v`
5. Format code: `black . && ruff check . --fix`
6. Commit with clear message
7. Push to fork: `git push origin feature/my-feature`
8. Create pull request

### Commit Messages

```
feat(parser): add XML comment support

- Parse XML comments as separate section type
- Add tests for comment extraction
- Update documentation

Closes #123
```

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] Code formatted with black
- [ ] No lint warnings
- [ ] Commit messages follow convention

---

## Release Process

### Version Bump

```bash
# Update version in models.py
__version__ = "1.1.0"

# Update CHANGELOG.md
# Add release notes

# Commit
git commit -m "chore: bump version to 1.1.0"

# Tag
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

### Publish to PyPI

```bash
# Build
python -m build

# Upload (requires API token)
twine upload dist/*
```

---

## Architecture Decisions

### Why SQLite?

- **Zero configuration**: Works out of the box
- **FTS5**: Built-in full-text search
- **ACID**: Reliable transactions
- **Portable**: Single file for easy backup
- **Fast**: Optimized for reads

### Why Click for CLI?

- **Composable**: Nested commands naturally
- **Type hints**: Automatic validation
- **Testing**: Easy CLI testing
- **Documentation**: Auto-generated help

### Why Separate Handlers?

- **Extensible**: Add formats without core changes
- **Testable**: Isolated handler tests
- **Maintainable**: Clear separation of concerns
- **Discoverable**: Auto-detect file types

---

## Common Patterns

### Database Transactions

```python
def store_multiple_documents(documents):
    """Store multiple documents in one transaction."""
    with self.db.transaction():
        for doc in documents:
            self._store_document(doc)
```

### Error Handling

```python
from core.exceptions import ParserError, DatabaseError

try:
    document = parser.parse(content, file_path)
    db.store_document(document)
except ParserError as e:
    logger.error(f"Parse error: {e}")
    raise
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Debug info")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
```

---

## Resources

### Internal Documentation

- [CLAUDE.md](../CLAUDE.md) - Project rules
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
- [API.md](../API.md) - API reference

### External Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [FTS5 Full-Text Search](https://www.sqlite.org/fts5.html)
- [Click Documentation](https://click.palletsprojects.com/)
- [pytest Documentation](https://docs.pytest.org/)

---

## Getting Help

- Open a GitHub issue for bugs
- Start a discussion for questions
- Check existing issues first
- Include minimal reproduction case

---

*Happy hacking! 🚀*
