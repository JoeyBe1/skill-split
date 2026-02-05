# Component Handlers Guide

Complete guide for using component handlers with skill-split to manage Claude Code components beyond basic markdown files.

## Overview

Component handlers extend skill-split to support specialized Claude Code file types that don't fit the traditional markdown/YAML model. Each handler is tailored to a specific component type and provides:

- **Type-specific parsing**: Understands the structure and schema of each component type
- **Multi-file support**: Handles components that span multiple related files
- **Validation**: Ensures components follow correct schemas and conventions
- **Progressive disclosure**: Breaks components into logical sections for database storage
- **Round-trip verification**: SHA256 hashing ensures data integrity

## Supported Component Types

### 1. Plugins (PLUGIN)

**Files**: `plugin.json`, `*.mcp.json`, `hooks.json`

Plugins are the primary extension mechanism for Claude Code. A plugin consists of:

- `plugin.json`: Main plugin metadata (name, version, description, permissions)
- `*.mcp.json`: MCP server configuration (optional)
- `hooks.json`: Hook definitions (optional)

**Example plugin structure:**
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "A sample plugin",
  "author": "Your Name",
  "permissions": ["allowNetwork", "allowFileSystemRead"],
  "mcpServers": {
    "server1": {}
  }
}
```

**Sections created:**
- `metadata`: Plugin information formatted as markdown
- `mcp_config`: MCP server configuration (if present)
- `hooks`: Hook definitions (if present)

### 2. Hooks (HOOK)

**Files**: `hooks.json`, `*.sh` scripts

Hooks define lifecycle event handlers for Claude Code operations. Each hook consists of:

- `hooks.json`: Hook definitions and metadata
- `*.sh`: Shell script for each hook (optional but recommended)

**Example hooks structure:**
```json
{
  "pre-commit": {
    "description": "Runs before creating a git commit",
    "enabled": true,
    "permissions": ["allowFileSystemWrite"]
  },
  "post-checkout": {
    "description": "Runs after checking out a branch"
  }
}
```

**Sections created:**
- One section per hook with name, description, and script content
- For plugin-style hooks: overview section + one section per event type

### 3. Configuration Files (CONFIG)

**Files**: `settings.json`, `mcp_config.json`, other JSON configs

Configuration files control Claude Code behavior and MCP server connections.

**Example settings.json:**
```json
{
  "permissions": ["allowNetwork"],
  "plugins": ["my-plugin"],
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    }
  }
}
```

**Sections created:**
- One section per top-level key
- Nested objects formatted as JSON
- Lists formatted as bullet lists (for simple types)

## Usage Examples

### Storing a Plugin

```bash
# Parse and store a plugin component
./skill_split.py store ~/.claude/plugins/my-plugin/plugin.json
```

**Output:**
```
File: /Users/joey/.claude/plugins/my-plugin/plugin.json
File ID: 1
Type: plugin
Format: multi_file
Sections: 3
  - metadata
  - mcp_config
  - hooks
```

### Retrieving Plugin Sections

```bash
# View plugin structure
./skill_split.py tree ~/.claude/plugins/my-plugin/plugin.json

# Get specific section
./skill_split.py get-section 1 --db skill-split.db
# Where 1 is the section ID from tree output
```

### Storing Hooks

```bash
# Store hooks configuration
./skill_split.py store ~/.claude/plugins/my-plugin/hooks.json
```

### Storing Configuration

```bash
# Store settings
./skill_split.py store ~/.claude/settings.json

# Store MCP config
./skill_split.py store ~/.claude/mcp_config.json
```

## Component Detection

skill-split automatically detects component types based on file path patterns:

| Pattern | Type | Handler |
|---------|------|---------|
| `plugin.json` | PLUGIN | PluginHandler |
| `hooks.json` | HOOK | HookHandler |
| `settings.json` | CONFIG | ConfigHandler |
| `mcp_config.json` | CONFIG | ConfigHandler |
| `*.md` | Various | Existing Parser |
| `*.sh` | HOOK | HookHandler |

## Database Integration

Component handlers integrate seamlessly with the existing skill-split database:

### File Type Tracking

The database now tracks multiple file types:

```sql
-- File types stored
SKILL        -- /skills/*/SKILL.md
COMMAND      -- /commands/*/*.md
AGENT        -- /agents/*/*.md
REFERENCE    -- /get-shit-done/references/*.md
PLUGIN       -- plugin.json + related files
HOOK         -- hooks.json + shell scripts
CONFIG       -- settings.json, mcp_config.json
OUTPUT_STYLE -- /output-styles/*.md
DOCUMENTATION-- README.md, CLAUDE.md, etc.
```

### Querying Components

```bash
# Search across all component types
./skill_split.py search "authentication" --db skill-split.db

# Returns matches from:
# - Skills with "authentication" sections
# - Plugins with authentication-related config
# - Hooks with authentication scripts
# - Config files with authentication settings
```

## Validation

Each handler provides type-specific validation:

### Plugin Validation

```bash
./skill_split.py validate plugin.json
```

**Checks:**
- Required fields (name, version, description)
- MCP config file existence
- Hooks file existence
- Valid JSON format

### Hook Validation

```bash
./skill_split.py validate hooks.json
```

**Checks:**
- At least one hook defined
- Script files exist for each hook
- Hook config is valid
- Descriptions present

### Config Validation

```bash
./skill_split.py validate settings.json
```

**Checks:**
- Valid JSON format
- Known settings keys (with warnings for unknown)
- MCP server config structure

## API Documentation

### HandlerFactory

Factory class for creating handler instances:

```python
from handlers.factory import HandlerFactory

# Create handler for file
handler = HandlerFactory.create_handler("plugin.json")

# Detect file type
file_type, file_format = HandlerFactory.detect_file_type("plugin.json")

# Check if supported
is_supported = HandlerFactory.is_supported("plugin.json")

# List supported types
types = HandlerFactory.list_supported_types()
# Returns: ['plugin', 'hook', 'config']
```

### ComponentDetector

Low-level component detection:

```python
from handlers.component_detector import ComponentDetector

# Detect type and format
file_type, file_format = ComponentDetector.detect("plugin.json")

# Get handler instance
handler = ComponentDetector.get_handler("plugin.json")

# Check if should use existing Parser
is_md = ComponentDetector.is_markdown_file("README.md")
```

### BaseHandler Interface

All handlers implement this interface:

```python
from handlers.base import BaseHandler

class CustomHandler(BaseHandler):
    def parse(self) -> ParsedDocument:
        """Parse component into sections"""
        pass

    def validate(self) -> ValidationResult:
        """Validate component structure"""
        pass

    def get_related_files(self) -> List[str]:
        """Get related file paths"""
        pass

    def get_file_type(self) -> FileType:
        """Return component type"""
        pass

    def get_file_format(self) -> FileFormat:
        """Return component format"""
        pass
```

## Progressive Disclosure

Component handlers enable progressive disclosure for complex components:

### Example: Large Plugin

A plugin with extensive MCP configuration and multiple hooks:

1. **Store once:**
   ```bash
   ./skill_split.py store large-plugin/plugin.json
   ```

2. **View structure:**
   ```bash
   ./skill_split.py tree large-plugin/plugin.json
   ```
   ```
   metadata
   mcp_config
   hooks
     pre-commit
     post-checkout
     on-file-change
   ```

3. **Load sections on-demand:**
   ```bash
   # Load only what you need
   ./skill_split.py get-section 1  # metadata
   ./skill_split.py get-section 3  # pre-commit hook
   ```

**Token savings:** 70%+ for typical multi-section components

## Troubleshooting

### Issue: Handler not found

**Error:** `No handler available for file type: XXX`

**Solution:**
- Check that file path matches detection pattern
- Verify file extension is supported
- Use existing Parser for markdown files

### Issue: Multi-file component not fully stored

**Error:** Only primary file stored, related files missing

**Solution:**
- Ensure related files are in same directory as primary file
- Check file naming conventions (e.g., `*.mcp.json`, `*.sh`)
- Verify handler's `get_related_files()` method finds files

### Issue: Validation fails unexpectedly

**Error:** Validation errors for valid component

**Solution:**
- Check JSON syntax with `jq . < component.json`
- Verify required fields are present
- Check that referenced files exist
- Review handler-specific validation rules

### Issue: Round-trip hash mismatch

**Error:** Hashes don't match after parse/recompose

**Solution:**
- For multi-file components: All related files must exist
- Check that no files were modified after initial parse
- Verify handler's `recompose()` method preserves format
- Report bug if issue persists with valid component

## Advanced Topics

### Custom Handlers

Create handlers for new component types:

```python
from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat

class CustomHandler(BaseHandler):
    def parse(self) -> ParsedDocument:
        # Implement parsing logic
        sections = [Section(...)]
        return ParsedDocument(
            frontmatter="...",
            sections=sections,
            file_type=FileType.CUSTOM,
            format=FileFormat.CUSTOM_FORMAT,
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        # Implement validation logic
        result = ValidationResult(is_valid=True)
        return result

    def get_related_files(self) -> List[str]:
        # Return related file paths
        return []
```

### Integration with Existing Parser

Component handlers complement the existing Parser:

- **Markdown files** (`.md`): Use existing Parser
- **Component files** (`.json`, `.sh`): Use component handlers
- **Detection is automatic**: Based on file path and extension

### Multi-File Hashing

For multi-file components, the hash includes all related files:

```python
# Hash computation for plugins
hash = hash(primary_file) + hash(mcp_config) + hash(hooks)

# Any change to any related file changes the overall hash
```

## Best Practices

1. **Store components atomically**: Store the primary file, handler finds related files
2. **Use tree command first**: Understand structure before loading sections
3. **Validate before storing**: Catch errors early with `validate` command
4. **Search broadly**: Use `search` to find components across the database
5. **Progressive disclosure**: Load sections on-demand, not all at once

## Migration Guide

### From Manual Component Management

**Before:**
```bash
# Manually inspect plugin.json
cat plugin.json

# Manually check .mcp.json
cat *.mcp.json

# Manually view hooks
cat hooks.json
```

**After:**
```bash
# Store once
./skill_split.py store plugin.json

# View structure
./skill_split.py tree plugin.json

# Load specific sections
./skill_split.py get-section <id>
```

### Benefits

- **Unified interface**: Single tool for all component types
- **Database-backed**: Fast queries without re-parsing
- **Progressive disclosure**: Load what you need, when you need it
- **Integrity verified**: SHA256 hashing ensures no corruption
- **Cross-component search**: Find related sections across all types

---

**Last Updated:** 2026-02-04
**Phase:** 9 - Component Handlers Complete
