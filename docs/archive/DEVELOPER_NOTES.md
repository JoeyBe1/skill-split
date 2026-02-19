# Developer Notes

**Internal notes for skill-split development**

## Quick Commands

```bash
# Run all tests
make test

# Run specific test file
pytest test/test_parser.py -v

# Run with coverage
make coverage

# Lint and format
make lint-all

# Run benchmarks
make benchmark

# Run demos
make demo
```

## Database Locations

| Environment | Path |
|-------------|------|
| Demo | `./skill_split.db` |
| Production | `~/.claude/databases/skill-split.db` |
| Test | `:memory:` (default) |
| Custom | `--db /path/to/db.db` |

## Common Issues

### Import Errors

```python
# Wrong
from skill_split import Parser

# Right
from core.parser import Parser
```

### Database Locked

```bash
# Enable WAL mode
sqlite3 skill_split.db "PRAGMA journal_mode=WAL;"
```

### Test Failures

```bash
# Clear cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reinstall
pip install -e .
```

## Debugging

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Trace SQL queries
import sqlite3
sqlite3.connect(':memory:', trace_callback=lambda sql: print(sql))
```

## Performance Tips

1. **Batch operations** - Store 100+ sections at once
2. **Use indexes** - FTS5 for search, foreign keys for joins
3. **Connection pooling** - Reuse database connections
4. **Async for I/O** - Use async for network operations

## Testing Patterns

```python
# Test structure
def test_feature():
    # Arrange
    input_data = "..."
    expected = "..."

    # Act
    result = function(input_data)

    # Assert
    assert result == expected
```

## Adding New Handlers

1. Create handler class inheriting from `BaseHandler`
2. Implement `parse()` and `validate()` methods
3. Register in `handlers/factory.py`
4. Add tests in `test/test_handlers/`
5. Update documentation

## Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml` and `VERSION`
- [ ] git tag created
- [ ] PyPI published (if applicable)

---

*Internal use - see [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines*
