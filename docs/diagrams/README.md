# Skill-Split Architecture Diagrams

This directory contains architecture diagrams and PlantUML source files for the skill-split project.

## Diagrams

### System Architecture
- **File**: `system_architecture.puml`
- **Description**: High-level system architecture showing all major components and their relationships
- **Topics**: Input layer, parsing layer, storage layer, query layer, output layer

### Data Flow
- **File**: `data_flow.puml`
- **Description**: Sequence diagram showing the parse and store workflow
- **Topics**: CLI flow, parsing, storage, validation

### Database Schema
- **File**: `database_schema.puml`
- **Description**: Entity-relationship diagram for SQLite database
- **Topics**: Files, sections, FTS5 index, checkouts tables

### Search Architecture
- **File**: `search_architecture.puml`
- **Description**: Three-tier search system architecture
- **Topics**: BM25 keywords, vector search, hybrid fusion

### Component Handlers
- **File**: `component_handlers.puml`
- **Description**: Class diagram for handler hierarchy
- **Topics**: BaseHandler, PluginHandler, HookHandler, ConfigHandler, ScriptHandler

### Progressive Disclosure
- **File**: `progressive_disclosure.puml`
- **Description**: State machine for progressive disclosure workflow
- **Topics**: Search, navigation, section loading

## Architecture Decision Records (ADRs)

### ADR-001: SQLite FTS5 for Local Search
- **File**: `ADR-001-sqlite-fts5.md`
- **Decision**: Use SQLite FTS5 with BM25 ranking for local keyword search
- **Rationale**: Fast, reliable, no external dependencies

### ADR-002: Supabase + pgvector for Cloud Storage
- **File**: `ADR-002-supabase-pgvector.md`
- **Decision**: Use Supabase PostgreSQL with pgvector for cloud storage and vector search
- **Rationale**: Semantic search, automatic backups, real-time sync

### ADR-003: Hybrid Search with Configurable Weights
- **File**: `ADR-003-hybrid-search.md`
- **Decision**: Implement hybrid search combining BM25 and vector scores
- **Rationale**: Flexibility for different search use cases

### ADR-004: SHA256 Hashing for Integrity Verification
- **File**: `ADR-004-sha256-hashing.md`
- **Decision**: Use SHA256 hashing for file integrity verification
- **Rationale**: Cryptographic certainty, byte-perfect round-trip

### ADR-005: Factory Pattern for Component Handlers
- **File**: `ADR-005-factory-pattern.md`
- **Decision**: Implement Factory Pattern for handler creation
- **Rationale**: Extensibility, consistency, separation of concerns

## Rendering Diagrams

### Using PlantUML

Install PlantUML:
```bash
# Using Homebrew (macOS)
brew install plantuml

# Using apt (Ubuntu/Debian)
sudo apt-get install plantuml

# Using Docker
docker run -d -p 8080:8080 plantuml/plantuml-server
```

Render diagram:
```bash
plantuml system_architecture.puml
```

### Using Online Editor

Visit [PlantUML Online Editor](https://plantuml.com/online) and paste the contents of any `.puml` file.

### Using VS Code Extension

1. Install the "PlantUML" extension
2. Open any `.puml` file
3. Press `Alt+D` to preview

## SVG Export

To export diagrams as SVG files (for use in documentation):

```bash
# Render all diagrams to SVG
for file in *.puml; do
    plantuml -tsvg "$file"
done
```

## Mermaid Diagrams

The main architecture documentation (`../ARCHITECTURE.md`) uses Mermaid diagrams that render natively in GitHub and many Markdown viewers.

Mermaid diagrams are embedded directly in the Markdown and don't require separate rendering.

## Contributing

When adding new diagrams:

1. Create PlantUML source files (`.puml`)
2. Keep diagrams focused on a single aspect
3. Use consistent styling (`!theme plain`)
4. Add descriptive notes for complex elements
5. Update this README with the new diagram

When making architecture decisions:

1. Create a new ADR following the template
2. Number sequentially (ADR-006, ADR-007, etc.)
3. Include context, decision, rationale, and consequences
4. Link to related ADRs
5. Update this README with the new ADR

## References

- [Main Architecture Documentation](../ARCHITECTURE.md)
- [PlantUML Documentation](https://plantuml.com/)
- [Mermaid Documentation](https://mermaid-js.github.io/)
