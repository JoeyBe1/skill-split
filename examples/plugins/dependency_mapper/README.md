# Dependency Mapper Plugin

Analyzes and maps cross-references and dependencies between documentation sections.

## Features

- **Cross-Reference Detection**: Finds internal links and references
- **Dependency Mapping**: Maps relationships between sections
- **Circular Reference Detection**: Identifies circular dependencies
- **Orphan Detection**: Finds unreferenced sections
- **Graph Generation**: Creates dependency graph visualizations

## Installation

```bash
# Copy to your skill-split plugins directory
cp -r examples/plugins/dependency_mapper ~/.claude/plugins/
```

## Usage

```bash
# Map dependencies for a file
./skill_split.py plugin dependency_mapper map <file>

# Find circular references
./skill_split.py plugin dependency_mapper circular <file>

# Find orphan sections
./skill_split.py plugin dependency_mapper orphans <file>

# Generate dependency graph
./skill_split.py plugin dependency_mapper graph <file> --format dot

# Analyze cross-database dependencies
./skill_split.py plugin dependency_mapper cross-db <db_path>
```

## API

### map_dependencies(file_path: str) -> DependencyMap

Maps all dependencies within a document.

### find_circular_references(map: DependencyMap) -> List[List[str]]

Finds circular dependency chains.

### find_orphan_sections(map: DependencyMap) -> List[str]

Finds sections that are not referenced by any other section.

### generate_graph(map: DependencyMap, format: str) -> str

Generates a dependency graph in specified format (dot, json, mermaid).

## Output Formats

- **DOT**: Graphviz DOT format for visual graphs
- **JSON**: Machine-readable dependency data
- **Mermaid**: Markdown-compatible diagram format
- **Text**: Human-readable tree format

## Requirements

- skill-split >= 1.0
- Python >= 3.9

## License

MIT
