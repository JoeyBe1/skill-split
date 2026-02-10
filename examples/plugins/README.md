# Skill-Split Example Plugins

This directory contains working example plugins for the skill-split documentation system. Each plugin demonstrates a different aspect of plugin development and integration.

## Available Plugins

### 1. Documentation Validator (`documentation_validator/`)

Validates markdown documentation structure and integrity.

**Key Features:**
- Structure validation (heading hierarchy, depth)
- Frontmatter completeness checks
- Link verification (internal and external)
- Code block validation
- Detailed reporting with suggestions

**Commands:**
```bash
./skill_split.py plugin documentation_validator validate <file>
./skill_split.py plugin documentation_validator validate-all
./skill_split.py plugin documentation_validator report <file> --suggest
```

**Exit Codes:**
- `0`: Validation passed
- `1`: Validation failed with errors
- `2`: Validation passed with warnings

### 2. Auto-Tagger (`auto_tagger/`)

Automatically analyzes content and suggests relevant tags.

**Key Features:**
- NLP-based content analysis
- TF-IDF keyword extraction
- Tag categorization (technology, framework, tool, concept)
- Automatic frontmatter updates
- Tag consistency management

**Commands:**
```bash
./skill_split.py plugin auto_tagger suggest <file> --count 10
./skill_split.py plugin auto_tagger update <file> --tags "python,tutorial"
./skill_split.py plugin auto_tagger extract <file> --count 5
./skill_split.py plugin auto_tagger similar <file> --limit 5
```

**Tag Categories:**
- **Technology**: Programming languages, runtime versions
- **Framework**: Libraries and frameworks
- **Tool**: Development tools and utilities
- **Concept**: Algorithms, patterns, methodologies
- **Pattern**: Design patterns and architectural patterns

### 3. Dependency Mapper (`dependency_mapper/`)

Analyzes cross-references and maps dependencies between sections.

**Key Features:**
- Cross-reference detection (internal links, includes, references)
- Dependency graph generation
- Circular reference detection
- Orphan section identification
- Multiple graph formats (DOT, Mermaid, JSON)

**Commands:**
```bash
./skill_split.py plugin dependency_mapper map <file>
./skill_split.py plugin dependency_mapper circular <file>
./skill_split.py plugin dependency_mapper orphans <file>
./skill_split.py plugin dependency_mapper graph <file> --format dot
./skill_split.py plugin dependency_mapper analyze <file> --report
```

**Graph Formats:**
- **DOT**: Graphviz format for visual graphs
- **Mermaid**: Markdown-compatible diagrams
- **JSON**: Machine-readable structured data

## Installation

All plugins can be installed by copying their directories to your skill-split plugins folder:

```bash
# Install all plugins
cp -r examples/plugins/* ~/.claude/plugins/

# Install specific plugin
cp -r examples/plugins/documentation_validator ~/.claude/plugins/
```

## Plugin Structure

Each plugin follows this structure:

```
plugin-name/
├── README.md              # User documentation
├── plugin.json           # Plugin manifest and configuration
├── main.py               # Main plugin code
└── tests/
    └── test_*.py         # Plugin tests
```

## Plugin Manifest (`plugin.json`)

The `plugin.json` file defines:

- **Metadata**: Name, version, description, author
- **Commands**: Available commands with arguments and options
- **Hooks**: Lifecycle hooks (post-parse, pre-store, etc.)
- **Configuration**: Default configuration values
- **Dependencies**: Required skill-split and Python versions

Example:
```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "My plugin description",
  "main": "main.py",
  "type": "validator",
  "commands": {
    "run": {
      "description": "Run the plugin",
      "arguments": ["file_path"],
      "options": {
        "verbose": {"type": "boolean", "default": false}
      }
    }
  },
  "hooks": {
    "post-parse": "run_after_parse"
  },
  "config": {
    "setting_name": "default_value"
  }
}
```

## Plugin Types

Plugins are categorized by type:

- **validator**: Validates document structure/content
- **transformer**: Transforms or modifies documents
- **analyzer**: Analyzes documents and reports
- **generator**: Generates new content

## Testing

Each plugin includes comprehensive tests:

```bash
# Run tests for a specific plugin
pytest examples/plugins/documentation_validator/tests/

# Run all plugin tests
pytest examples/plugins/*/tests/

# Run with coverage
pytest examples/plugins/*/tests/ --cov=examples/plugins/
```

## Development Guidelines

When creating new plugins:

1. **Follow the structure**: Use the standard directory layout
2. **Include tests**: Write comprehensive test coverage
3. **Document well**: Clear README with usage examples
4. **Handle errors**: Graceful error handling with helpful messages
5. **Support hooks**: Integrate with skill-split lifecycle
6. **Type hints**: Use Python type annotations
7. **Configurable**: Support configuration via `plugin.json`

## Command Integration

Plugins integrate with skill-split CLI:

```bash
# Run plugin command
./skill_split.py plugin <plugin_name> <command> [args] [options]

# Example
./skill_split.py plugin documentation_validator validate README.md --strict
```

## Hooks Integration

Plugins can hook into skill-split lifecycle events:

```json
{
  "hooks": {
    "post-parse": "function_name",
    "pre-store": "function_name",
    "post-store": "function_name"
  }
}
```

Available hooks:
- **post-parse**: After document parsing
- **pre-store**: Before database storage
- **post-store**: After database storage
- **pre-checkout**: Before file checkout
- **post-checkout**: After file checkout

## Examples

### Creating a New Plugin

1. Create directory structure:
```bash
mkdir -p examples/plugins/my_plugin/tests
cd examples/plugins/my_plugin
```

2. Create `plugin.json`:
```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "My awesome plugin",
  "main": "main.py",
  "type": "analyzer",
  "commands": {
    "analyze": {
      "description": "Analyze document",
      "arguments": ["file_path"]
    }
  }
}
```

3. Create `main.py`:
```python
#!/usr/bin/env python3
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="My Plugin")
    parser.add_argument("command", choices=["analyze"])
    parser.add_argument("file_path")
    args = parser.parse_args()

    if args.command == "analyze":
        print(f"Analyzing {args.file_path}...")

if __name__ == "__main__":
    sys.exit(main())
```

4. Create `README.md` with documentation

5. Add tests in `tests/`

## Contributing

To contribute new example plugins:

1. Follow the existing structure and patterns
2. Include comprehensive tests
3. Document thoroughly
4. Test with skill-split integration
5. Submit as pull request

## Resources

- **skill-split Documentation**: See project root
- **Plugin Development Guide**: (Coming soon)
- **API Reference**: (Coming soon)

## License

All example plugins are released under the MIT License, consistent with the skill-split project.
