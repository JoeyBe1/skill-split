# Handler Integration Guide

Guide for integrating component handlers with existing skill-split installation and workflows.

## Overview

Component handlers (Phase 9) extend skill-split to support specialized Claude Code file types while maintaining full compatibility with existing functionality. This guide covers integration, migration, and usage patterns.

## What's New in Phase 9

### New Capabilities

1. **Plugin Support**: Parse and store `plugin.json` with related MCP config and hooks
2. **Hook Support**: Parse and store `hooks.json` with associated shell scripts
3. **Config Support**: Parse and store `settings.json` and `mcp_config.json`
4. **Type Detection**: Automatic component type detection based on file patterns
5. **Multi-File Hashing**: Combined SHA256 hashing for multi-file components

### New Files

```
skill-split/
├── handlers/
│   ├── __init__.py           # Handler package initialization
│   ├── base.py               # Abstract base handler interface
│   ├── component_detector.py # File type detection
│   ├── factory.py            # Handler factory
│   ├── plugin_handler.py     # Plugin component handler
│   ├── hook_handler.py       # Hook component handler
│   └── config_handler.py     # Config file handler
├── test/test_handlers/
│   ├── __init__.py
│   ├── test_component_detector.py  # 18 tests
│   ├── test_plugin_handler.py      # 10 tests
│   ├── test_hook_handler.py        # 10 tests
│   └── test_config_handler.py      # 10 tests
```

### New Models

**FileFormat enum additions:**
- `JSON` - JSON files
- `JSON_SCHEMA` - JSON with known schema
- `SHELL_SCRIPT` - Shell scripts
- `MULTI_FILE` - Multi-file components

**FileType enum additions:**
- `AGENT` - Agent definitions
- `PLUGIN` - Plugin components
- `HOOK` - Hook components
- `OUTPUT_STYLE` - Output style definitions
- `CONFIG` - Configuration files
- `DOCUMENTATION` - Documentation files

## Integration with Existing Code

### No Breaking Changes

Phase 9 is **fully backward compatible** with existing skill-split:

- All existing commands work unchanged
- Existing databases can be used without modification
- Markdown parsing uses existing Parser
- New handlers only activate for specific file types

### Automatic Handler Selection

```python
# In skill_split.py or any code using handlers
from handlers.factory import HandlerFactory

# Returns appropriate handler or None for markdown files
handler = HandlerFactory.create_handler(file_path)

if handler:
    # Use component handler
    doc = handler.parse()
else:
    # Use existing Parser for markdown
    from core.parser import Parser
    parser = Parser()
    doc = parser.parse(file_path)
```

### Database Schema

**No schema changes required**. Existing database structure supports all component types:

```sql
-- files table already supports all types
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    original_hash TEXT,
    type TEXT,  -- Now includes: plugin, hook, config
    format TEXT,  -- Now includes: json, multi_file, shell
    frontmatter TEXT,
    modified_at TIMESTAMP
);

-- sections table unchanged
CREATE TABLE sections (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    title TEXT,
    level INTEGER,
    content TEXT,
    start_byte INTEGER,
    end_byte INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id)
);
```

## Migration Guide

### For Existing Users

If you're already using skill-split:

1. **No action required** for existing markdown files
2. **New capability** for plugins, hooks, and configs
3. **Optional migration** to store components in database

### Step-by-Step Migration

#### 1. Update Installation

```bash
cd /path/to/skill-split
git pull origin main  # Or latest branch

# Verify new files present
ls -la handlers/
ls -la test/test_handlers/
```

#### 2. Test Handler Installation

```bash
# Run handler tests
pytest test/test_handlers/ -v

# Expected: 48 tests passing (18 + 10 + 10 + 10)
```

#### 3. Store Components

```bash
# Store plugins
./skill_split.py store ~/.claude/plugins/my-plugin/plugin.json

# Store hooks
./skill_split.py store ~/.claude/plugins/my-plugin/hooks.json

# Store config
./skill_split.py store ~/.claude/settings.json
```

#### 4. Verify Integration

```bash
# Check database contains new types
sqlite3 skill-split.db "SELECT DISTINCT type FROM files;"

# Expected output:
# skill
# command
# reference
# plugin
# hook
# config
```

### Migration Patterns

#### Pattern 1: Plugin Management

**Before:**
```bash
# Manually inspect plugins
find ~/.claude/plugins -name plugin.json -exec cat {} \;
```

**After:**
```bash
# Store all plugins
find ~/.claude/plugins -name plugin.json -exec ./skill_split.py store {} \;

# Search across all plugins
./skill_split.py search "authentication" --db skill-split.db
```

#### Pattern 2: Hook Inspection

**Before:**
```bash
# Manually view hooks
cat ~/.claude/plugins/my-plugin/hooks.json
cat ~/.claude/plugins/my-plugin/pre-commit.sh
```

**After:**
```bash
# Store hooks once
./skill_split.py store ~/.claude/plugins/my-plugin/hooks.json

# View structure
./skill_split.py tree ~/.claude/plugins/my-plugin/hooks.json

# Get specific hook
./skill_split.py get-section <section-id>
```

#### Pattern 3: Configuration Tracking

**Before:**
```bash
# Manual config inspection
cat ~/.claude/settings.json
cat ~/.claude/mcp_config.json
```

**After:**
```bash
# Store configs
./skill_split.py store ~/.claude/settings.json
./skill_split.py store ~/.claude/mcp_config.json

# Track changes over time
./skill_split.py verify ~/.claude/settings.json
```

## Code Integration Examples

### Using Handlers in Python

```python
from handlers.factory import HandlerFactory
from core.database import DatabaseStore

# Store a component
handler = HandlerFactory.create_handler("plugin.json")
if handler:
    doc = handler.parse()

    # Store in database
    db = DatabaseStore("skill-split.db")
    file_id = db.store_file(doc)

    print(f"Stored plugin with ID: {file_id}")
```

### Custom Handler Integration

```python
from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat

class MyCustomHandler(BaseHandler):
    """Custom handler for my component type."""

    def parse(self) -> ParsedDocument:
        # Parse logic here
        sections = [
            Section(
                level=1,
                title="section1",
                content="...",
                line_start=1,
                line_end=10,
            )
        ]

        return ParsedDocument(
            frontmatter="{}",
            sections=sections,
            file_type=FileType.CUSTOM,
            format=FileFormat.CUSTOM_FORMAT,
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        # Validation logic here
        return ValidationResult(is_valid=True)

    def get_related_files(self) -> List[str]:
        # Return related files
        return []

# Register custom handler
from handlers.component_detector import ComponentDetector
ComponentDetector.PATTERNS[FileType.CUSTOM] = re.compile(r"custom\.json$")
ComponentDetector._handler_classes[FileType.CUSTOM] = MyCustomHandler
```

## CLI Integration

### Existing Commands

All existing commands work with component handlers:

```bash
# Parse component
./skill_split.py parse plugin.json

# Validate component
./skill_split.py validate hooks.json

# Store component
./skill_split.py store settings.json

# Get component
./skill_split.py get plugin.json

# Tree view
./skill_split.py tree plugin.json

# Verify component
./skill_split.py verify plugin.json
```

### New Query Capabilities

```bash
# Search across all component types
./skill_split.py search "mcp" --db skill-split.db

# List components by type
sqlite3 skill-split.db "SELECT path, type FROM files WHERE type='plugin';"

# Get section by ID (works for all types)
./skill_split.py get-section 1 --db skill-split.db
```

## Testing Integration

### Test Suite Structure

```
test/
├── test_parser.py           # Existing: 21 tests
├── test_hashing.py          # Existing: 5 tests
├── test_database.py         # Existing: 7 tests
├── test_roundtrip.py        # Existing: 8 tests
├── test_query.py            # Existing: 18 tests
├── test_cli.py              # Existing: 16 tests
├── test_supabase_store.py   # Existing: 5 tests
├── test_checkout_manager.py # Existing: 5 tests
└── test_handlers/           # New: 48 tests
    ├── test_component_detector.py  # 18 tests
    ├── test_plugin_handler.py      # 10 tests
    ├── test_hook_handler.py        # 10 tests
    └── test_config_handler.py      # 10 tests
```

### Running Tests

```bash
# Run all tests
pytest -v

# Run handler tests only
pytest test/test_handlers/ -v

# Run specific handler test
pytest test/test_handlers/test_plugin_handler.py::test_plugin_parse_basic -v
```

### Test Coverage

**Total tests**: 123 (75 existing + 48 new)
- Parser: 21 tests
- Database: 7 tests
- Hashing: 5 tests
- Round-trip: 8 tests
- Query: 18 tests
- CLI: 16 tests
- Supabase: 5 tests
- Checkout: 5 tests
- Component Detector: 18 tests
- Plugin Handler: 10 tests
- Hook Handler: 10 tests
- Config Handler: 10 tests

## Troubleshooting Integration

### Issue: Import errors for handlers

**Error:** `ModuleNotFoundError: No module named 'handlers'`

**Solution:**
```bash
# Verify handlers directory exists
ls -la handlers/

# Check PYTHONPATH includes current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Reinstall if needed
pip install -e .
```

### Issue: Handler not activated

**Error:** Component uses existing Parser instead of handler

**Solution:**
```bash
# Check file path matches pattern
# plugin.json must be named exactly "plugin.json"
# hooks.json must be named exactly "hooks.json"

# Verify detection
python3 -c "
from handlers.component_detector import ComponentDetector
print(ComponentDetector.detect('plugin.json'))
"
```

### Issue: Database conflicts

**Error:** Database schema mismatch

**Solution:**
```bash
# Existing databases should work without modification
# If issues occur, backup and recreate:

mv skill-split.db skill-split.db.backup

# Re-store files
./skill_split.py store plugin.json
```

## Performance Considerations

### Handler Overhead

Component handlers add minimal overhead:

- **Detection**: O(1) regex pattern matching
- **Parsing**: O(n) where n = file size
- **Multi-file**: O(n*m) where m = number of related files

### Database Performance

Component handlers use existing database schema:

- **Query speed**: Same as existing files
- **Storage**: Slightly more for multi-file components
- **Indexing**: No new indexes required

### Optimization Tips

1. **Batch store components**: Store multiple components at once
2. **Use tree before get**: View structure before loading sections
3. **Search with filters**: Use file_path parameter in search_sections()
4. **Cache frequently used**: Keep database in memory for frequent access

## Best Practices

### 1. File Naming

Use standard naming conventions:

- Plugins: `plugin.json` (exact name required)
- Hooks: `hooks.json` (exact name required)
- MCP config: `*.mcp.json` (any name with .mcp.json suffix)
- Settings: `settings.json` (exact name)
- Scripts: `{hook-name}.sh` (matches hook name)

### 2. Directory Structure

Keep related files together:

```
my-plugin/
├── plugin.json          # Primary file
├── my-plugin.mcp.json   # MCP config
└── hooks.json          # Hooks (optional)
```

### 3. Validation First

Always validate before storing:

```bash
./skill_split.py validate plugin.json
./skill_split.py store plugin.json
```

### 4. Progressive Disclosure

Load sections on-demand:

```bash
# View structure first
./skill_split.py tree plugin.json

# Load specific sections
./skill_split.py get-section 1  # metadata
./skill_split.py get-section 2  # mcp_config
```

## Future Enhancements

### Planned Features

1. **More component types**: Agent definitions, output styles
2. **Schema validation**: JSON schema validation for configs
3. **Cross-references**: Link between related components
4. **Version tracking**: Track component versions in database
5. **Dependency graph**: Visualize component dependencies

### Extensibility Points

1. **Custom handlers**: Add handlers for new component types
2. **Custom detectors**: Extend detection patterns
3. **Custom validators**: Add validation rules
4. **Custom formatters**: Format sections for specific use cases

## Support

### Documentation

- [COMPONENT_HANDLERS.md](./COMPONENT_HANDLERS.md) - Complete component handler guide
- [README.md](./README.md) - Main documentation
- [EXAMPLES.md](./EXAMPLES.md) - Usage examples
- [CLAUDE.md](./CLAUDE.md) - Project context

### Issues

Report bugs or request features via GitHub issues.

### Testing

Run test suite to verify installation:

```bash
pytest test/test_handlers/ -v
```

---

**Last Updated:** 2026-02-04
**Phase:** 9 - Component Handlers Integration Complete
