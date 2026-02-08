# Coding Conventions

**Analysis Date:** 2026-02-08

## Naming Patterns

**Files:**
- Modules: snake_case (e.g., `database.py`, `parser.py`, `hybrid_search.py`)
- Test files: `test_<module>.py` (e.g., `test_parser.py`, `test_database.py`)
- Classes: PascalCase (e.g., `DatabaseStore`, `Parser`, `FormatDetector`)
- Functions/methods: snake_case (e.g., `extract_frontmatter`, `parse_file`, `detect_format`)
- Variables: snake_case (e.g., `file_path`, `section_content`, `db_path`)
- Constants: UPPER_SNAKE_CASE (e.g., `FRONTMATTER_DELIMITER`, `HEADING_PATTERN`)

**Types:**
- Enums: PascalCase (e.g., `FileFormat`, `FileType`)
- Data classes: PascalCase (e.g., `Section`, `FileMetadata`, `ParsedDocument`)
- Type hints: CamelCase for types (e.g., `List[str]`, `Optional[Tuple]`)

## Code Style

**Formatting:**
- Line length: 88 characters (PEP 8 default)
- Indentation: 4 spaces
- Trailing whitespace: No trailing whitespace
- Newline at end of file: Required
- Docstrings: Triple quotes on separate lines

**Import Organization:**
```python
# Standard library imports
from __future__ import annotations  # Always at top
import os
import sys

# Third-party imports
from typing import List, Optional, Tuple
import sqlite3

# Local imports
from core.database import DatabaseStore
from models import FileFormat, FileType
```

**Order:**
1. `from __future__ import annotations`
2. Standard library imports (alphabetical)
3. Third-party imports (alphabetical)
4. Local imports (relative imports first, then absolute)

## Documentation

**Module Docstrings:**
```python
"""
Module description.

This module provides functionality for...
"""

# Additional docstring content if needed
```

**Function/Method Docstrings:**
```python
def extract_frontmatter(self, content: str) -> Tuple[str, str]:
    """
    Extract YAML frontmatter from content.

    Args:
        content: Full file content

    Returns:
        Tuple of (frontmatter, remaining_content)
        - frontmatter: YAML content between --- delimiters
        - remaining_content: Content after frontmatter

    Raises:
        ValueError: If frontmatter is malformed
    """
```

**Class Docstrings:**
```python
class Parser:
    """
    Parses markdown/YAML files into structured sections.

    Design philosophy:
    - Validate before every operation
    - Never silently lose data
    - Preserve exact whitespace for round-trip verification
    """
```

## Function Design

**Size:**
- Keep functions focused and under 50 lines
- Complex operations should be broken into smaller helper methods
- Use class methods for related functionality

**Parameters:**
- Use type hints for all parameters
- Keep parameter count under 5 when possible
- Use default values for optional parameters
- Prefer keyword arguments for clarity

**Return Values:**
- Always use type hints
- Prefer tuples for multiple related values
- Return empty collections (not None) when applicable
- Use Optional for nullable returns

## Error Handling

**Patterns:**
```python
# Use specific exceptions
raise FileNotFoundError(f"File not found: {self.file_path}")
raise ValueError(f"Invalid frontmatter format: {error_msg}")

# Validate input
if not content:
    raise ValueError("Content cannot be empty")

# Propagate exceptions with context
try:
    # operation
except sqlite3.Error as e:
    raise DatabaseError(f"Database operation failed: {e}")
```

**Logging:**
- Use f-strings for message formatting
- Include error context in messages
- Re-raise exceptions with additional context

## Import Style

**Relative vs Absolute:**
```python
# Relative imports within package
from .database import DatabaseStore
from ..models import FileFormat

# Absolute imports for top-level modules
from core.database import DatabaseStore
from models import FileFormat
```

**Type Hints:**
```python
from typing import List, Optional, Dict, Tuple, Any
from __future__ import annotations  # Enable forward references
```

## Class Design

**Properties:**
```python
@property
def conn(self) -> sqlite3.Connection:
    """Lazily-initialized database connection."""
    if self._conn is None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
    return self._conn
```

**Context Managers:**
```python
def __enter__(self) -> "DatabaseStore":
    _ = self.conn
    return self

def __exit__(self, exc_type, exc, tb) -> None:
    if self._conn is not None:
        self._conn.close()
        self._conn = None
```

**Abstract Classes:**
```python
from abc import ABC, abstractmethod

class BaseHandler(ABC):
    @abstractmethod
    def parse(self) -> ParsedDocument:
        """Parse the component into structured sections."""
        pass

    @abstractmethod
    def validate(self) -> ValidationResult:
        """Validate component structure and schema."""
        pass
```

## Design Principles

**Core Philosophy:**
- Validate before every operation
- Never silently lose data
- Preserve exact whitespace for round-trip verification
- Assume errors to avoid them

**Database Operations:**
- Use context managers for connections
- Enable foreign key constraints
- Use parameterized queries to prevent SQL injection
- Lazy-initialize connections for test compatibility

**File Operations:**
- Always use explicit encoding (utf-8)
- Use Path objects for file paths
- Check file existence before operations
- Clean up temporary resources

---

*Convention analysis: 2026-02-08*
```