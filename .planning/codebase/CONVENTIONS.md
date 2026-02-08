# Coding Conventions

**Analysis Date:** 2026-02-08

## Naming Patterns

**Files:**
- `snake_case` for all Python modules and scripts
- Test files prefixed with `test_`: `test_parser.py`, `test_database.py`
- Module directories use `snake_case`: `core/`, `handlers/`, `test/`
- Fixtures directory: `test/fixtures/`
- `UPPER_CASE.md` for documentation files at project root

**Functions:**
- `snake_case` for all functions and methods
- Private methods prefixed with single underscore: `_parse_heading_lines()`, `_read_content()`
- Private class attributes prefixed with single underscore: `self._conn`, `self._original_bytes`
- Command functions prefixed with `cmd_`: `cmd_parse()`, `cmd_ingest()`, `cmd_checkout()`

**Variables:**
- `snake_case` for local variables
- Constants use `SCREAMING_SNAKE_CASE` for regex patterns: `FRONTMATTER_DELIMITER`, `HEADING_PATTERN`
- Class attributes use `snake_case` with property decorators where appropriate
- Type aliases use `PascalCase` when exported: `FileType`, `FileFormat`

**Types:**
- `PascalCase` for class names: `Parser`, `DatabaseStore`, `BaseHandler`
- `PascalCase` for enums: `FileFormat`, `FileType`
- `PascalCase` for type aliases in annotations: `Optional[str]`, `List[Section]`
- Use `from __future__ import annotations` for forward references in type hints

**Modules:**
- `snake_case` for all module names
- `__init__.py` files define `__all__` lists for explicit exports
- Use `noqa: F401` comments for imported-but-unused exports in `__init__.py`

## Code Style

**Formatting:**
- No explicit formatter configured (no `.black`, `.ruff`, or `.format` config found)
- 4-space indentation standard (Python default)
- Max line length appears to be ~100-120 characters (based on code observation)
- Single quotes preferred for strings: `'test'`, `"string with 'quote'"`
- Double quotes for docstrings and strings containing single quotes

**Linting:**
- No explicit linting config (no `.eslintrc*`, `.flake8`, `.pylintrc`)
- Use `type: ignore` comments where mypy/pyright might complain
- Use `noqa: F401` for intentionally unused imports

**Docstrings:**
- Google-style docstrings used throughout
- Triple double quotes for all docstrings: `"""Description"""`
- Module-level docstrings at top of each file
- Class docstrings describe purpose and design philosophy
- Method docstrings include Args, Returns, Raises sections

## Import Organization

**Order:**
1. Standard library imports (`import os`, `from pathlib import Path`)
2. Third-party imports (`import pytest`, `from dotenv import load_dotenv`)
3. Local imports (`from core.parser import Parser`, `from models import FileFormat`)

**Path Aliases:**
- No explicit path aliases configured
- Use `sys.path.insert(0, ...)` in test files for module imports
- Use `from __future__ import annotations` for forward compatibility
- Use `TYPE_CHECKING` imports for type hints without runtime dependencies

**Conditional imports:**
- Lazy imports pattern for optional dependencies:
  ```python
  SupabaseStore = None
  def _ensure_supabase_imports():
      global SupabaseStore
      if SupabaseStore is None:
          from core.supabase_store import SupabaseStore as SB
  ```

## Error Handling

**Patterns:**
- Explicit error checking over EAFP: `if not content:` before processing
- Return `None` for "not found" cases: `get_file()` returns `None` if file doesn't exist
- Raise exceptions for invalid inputs: `ValueError`, `TypeError`, `FileNotFoundError`
- Use `try/except` for fallback logic:
  ```python
  try:
      symbols = self._get_symbols_via_lsp()
  except Exception:
      symbols = self._get_symbols_via_regex(lines)
  ```

**Validation:**
- Defensive programming: Check for empty/None before operations
- Use `ValidationResult` dataclass for structured validation feedback
- Collect multiple errors before failing: `result.add_error()`
- File existence checks before reading: `if not path.exists():`

**Resource cleanup:**
- Context managers for database connections: `with sqlite3.connect(...) as conn:`
- Explicit cleanup in test teardowns: `shutil.rmtree(temp_dir)`
- Use `tempfile.mkdtemp()` for test isolation

## Logging

**Framework:** `print()` statements used (no structured logging framework)

**Patterns:**
- Print to stdout for normal output
- Print to stderr for errors: `print(f"Error: ...", file=sys.stderr)`
- Return integer exit codes: `return 0` for success, `return 1` for errors
- No log levels or structured logging

## Comments

**When to Comment:**
- Explain design philosophy at module/class level
- Document non-obvious algorithms (especially in parser)
- Note critical behavior for round-trip verification
- Flag temporal issues or known workarounds
- Preserve blank lines for byte-perfect integrity (parser comments)

**JSDoc/TSDoc:**
- Google-style docstrings for all public classes and methods
- Docstring sections: Description, Args, Returns, Raises, Note, Examples
- Use `Args:` section for all parameters
- Use `Returns:` section for non-None return values
- Use `Raises:` section for expected exceptions
- Use `Note:` for important behavioral details
- Use `Examples:` for usage patterns

**Inline comments:**
- Explain "why" not "what"
- Use comments for temporary workarounds
- Flag incomplete implementations with explicit notes
- Comment critical preservation logic: `# NOTE: Preserve blank lines for byte-perfect round-trip`

## Function Design

**Size:** Keep functions focused and under 50 lines when possible
- Complex parsing functions may be longer (parser methods)
- Extract helpers when logical units emerge
- Use private methods for implementation details

**Parameters:**
- Use keyword arguments for options: `def parse(self, validate: bool = True)`
- Avoid positional arguments beyond 2-3 required params
- Use dataclasses for grouping related parameters

**Return Values:**
- Return `None` for "not found" cases
- Return tuples for related values: `return frontmatter, body`
- Use dataclasses for structured returns: `ValidationResult`, `ParsedDocument`
- Return `int` exit codes from CLI commands: `0` for success, `1` for failure

**Type hints:**
- All functions have type hints on parameters and returns
- Use `Optional[T]` for nullable returns
- Use `Union[T1, T2]` for multiple return types
- Use `List[T]`, `Dict[K, V]` for collections
- Use `-> None` explicitly for void functions

## Module Design

**Exports:**
- `__all__` lists in `__init__.py` files for explicit public API
- Use `noqa: F401` for exports imported only for `__all__`
- Re-export commonly used items from package root

**Barrel Files:**
- `handlers/__init__.py` exports all handler classes
- `core/__init__.py` exports core utilities: `Validator`, `ValidationResult`
- `models.py` is the main dataclass module

**Dependency management:**
- Use `TYPE_CHECKING` to avoid circular imports for type hints
- Lazy imports for optional dependencies (Supabase)
- Factory pattern for handler instantiation to avoid import coupling
- Use protocols/ABCs for interface definitions

## Dataclass Usage

**Standard patterns:**
- Use `@dataclass` for data containers
- Use `field(default_factory=list)` for mutable defaults
- Use `field(default=None)` for optional fields
- Use `field(default=False, repr=False)` to exclude from repr
- Implement `to_dict()` methods for JSON serialization

**Models location:**
- All dataclasses in `models.py`
- Enums in `models.py`: `FileType`, `FileFormat`
- Core models: `Section`, `ParsedDocument`, `FileMetadata`, `ValidationResult`, `ComposedSkill`

## Database Patterns

**Connection management:**
- Use `with sqlite3.connect() as conn:` for automatic cleanup
- Enable foreign keys: `conn.execute("PRAGMA foreign_keys = ON")`
- Use `row_factory = sqlite3.Row` for dict-like access
- Lazy initialization pattern for compatibility: `@property def conn(self)`

**Schema:**
- Use `CREATE TABLE IF NOT EXISTS` for idempotency
- Use `CREATE INDEX IF NOT EXISTS` for indexes
- Use `ON DELETE CASCADE` for foreign keys
- Store JSON in TEXT columns (frontmatter, original JSON)

**Transactions:**
- Explicit `conn.commit()` after modifications
- Use context managers for automatic rollback on error
- Separate read connections from write connections

## Testing Patterns (for convention reference)

**Test structure:**
- Use `pytest` framework
- Test classes named `Test<ClassName>`: `TestParser`, `TestDatabase`
- Test methods named `test_<action>_<scenario>`: `test_parse_simple_headings`
- Use `setup_method()` and `teardown_method()` for fixtures
- Use `@pytest.fixture` for reusable test data

**Test organization:**
- Mirror source structure: `test/test_handlers/` mirrors `handlers/`
- Fixture files in `test/fixtures/`
- Use `tempfile.mkdtemp()` for test isolation
- Mock external dependencies: `unittest.mock.MagicMock`

---

*Convention analysis: 2026-02-08*
