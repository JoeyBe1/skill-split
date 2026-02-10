# Skill-Split Architecture Documentation

**Version**: 1.0.0
**Last Updated**: 2025-02-10
**Status**: Production Ready (518 tests passing)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [System Architecture](#system-architecture)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [Search Architecture](#search-architecture)
7. [Component Handlers](#component-handlers)
8. [API Layer](#api-layer)
9. [Extension Points](#extension-points)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

Skill-split is a Python-based intelligent document parsing and storage system that enables progressive disclosure of large documentation files. The system decomposes markdown, YAML, and various code files into discrete sections stored in a database, supporting both local SQLite and remote Supabase backends.

### Key Features

- **Multi-format Parsing**: Markdown headings, XML tags, JSON configs, shell scripts, Python/JavaScript/TypeScript
- **Dual Storage**: Local SQLite with FTS5 full-text search + Supabase cloud with vector embeddings
- **Progressive Disclosure**: Load sections individually to minimize token usage (99% context savings)
- **Hybrid Search**: BM25 keyword ranking + vector similarity search with configurable weights
- **Skill Composition**: Assemble new skills from existing sections with validation
- **Component Handlers**: Specialized parsers for plugins, hooks, configs, and scripts

### Technology Stack

```
Python 3.13+ | SQLite 3.38+ (FTS5) | Supabase (PostgreSQL + pgvector)
OpenAI Embeddings (text-embedding-3-small) | SHA256 Hashing
```

---

## Architecture Principles

### 1. Big-O Philosophy
- **3 AM Rule**: Code that makes sense at 3 AM when debugging
- **Single Responsibility**: Each module has one clear purpose
- **Junior Developer Principle**: Clear enough for anyone to understand

### 2. Design Patterns
- **Factory Pattern**: HandlerFactory for component-specific parsers
- **Strategy Pattern**: Different storage backends (SQLite vs Supabase)
- **Repository Pattern**: DatabaseStore abstracts data access
- **Builder Pattern**: SkillComposer constructs complex objects

### 3. Core Guarantees
- **Byte-Perfect Round-trip**: SHA256 verification ensures data integrity
- **Never Lose Data**: Defensive programming with validation at every step
- **Assume Errors**: Check before operations, fail gracefully

---

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Input Layer"
        CLI[CLI Interface]
        Files[Source Files]
    end

    subgraph "Parsing Layer"
        Detector[FormatDetector]
        Factory[HandlerFactory]
        Parser[Core Parser]
        Handlers[Component Handlers]
    end

    subgraph "Storage Layer"
        LocalDB[(SQLite + FTS5)]
        CloudDB[(Supabase + pgvector)]
    end

    subgraph "Query Layer"
        QueryAPI[Query API]
        HybridSearch[Hybrid Search]
        EmbeddingSvc[Embedding Service]
    end

    subgraph "Output Layer"
        Recomposer[Recomposer]
        Composer[Skill Composer]
        Checkout[Checkout Manager]
    end

    CLI --> Files
    Files --> Detector
    Detector --> Factory
    Factory --> Parser
    Factory --> Handlers
    Parser --> LocalDB
    Handlers --> LocalDB
    LocalDB <--> CloudDB
    QueryAPI --> LocalDB
    HybridSearch --> QueryAPI
    HybridSearch --> EmbeddingSvc
    HybridSearch --> CloudDB
    Recomposer --> LocalDB
    Composer --> LocalDB
    Checkout --> CloudDB

    style CLI fill:#e1f5ff
    style LocalDB fill:#c8e6c9
    style CloudDB fill:#ffccbc
    style QueryAPI fill:#fff9c4
```

### Component Overview

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **Input** | CLI (`skill_split.py`) | Command-line interface with 16 commands |
| **Parsing** | `Parser` | Markdown headings, XML tag extraction |
| **Parsing** | `FormatDetector` | File type and format detection |
| **Parsing** | `HandlerFactory` | Route to appropriate component handler |
| **Parsing** | Component Handlers | Specialized parsers (plugins, hooks, scripts) |
| **Storage** | `DatabaseStore` | SQLite operations with FTS5 |
| **Storage** | `SupabaseStore` | Remote storage with vector search |
| **Query** | `QueryAPI` | Progressive disclosure operations |
| **Query** | `HybridSearch` | BM25 + vector combination |
| **Output** | `Recomposer` | Byte-perfect file reconstruction |
| **Output** | `SkillComposer` | Assemble skills from sections |
| **Output** | `CheckoutManager` | File deployment and tracking |

---

## Data Flow

### Parse and Store Flow

```mermaid
sequenceDiagram
    participant C as CLI
    participant D as FormatDetector
    participant H as HandlerFactory
    participant P as Parser/Handler
    participant DB as DatabaseStore
    participant V as Validator

    C->>D: detect(file_path, content)
    D-->>C: (file_type, file_format)

    C->>H: create_handler(file_path)
    alt Supported File
        H-->>C: Handler instance
        C->>P: handler.parse()
    else Markdown File
        C->>P: parser.parse()
    end

    P-->>C: ParsedDocument
    C->>DB: store_file(file, doc, hash)
    DB->>DB: _store_sections()
    DB->>DB: _sync_section_fts()
    DB-->>C: file_id

    C->>V: validate_round_trip()
    V->>DB: get_file()
    V->>P: recompose()
    V-->>C: ValidationResult
```

### Search and Retrieve Flow

```mermaid
sequenceDiagram
    participant U as User
    participant Q as QueryAPI
    participant H as HybridSearch
    participant E as EmbeddingService
    participant L as LocalDB (FTS5)
    participant S as Supabase

    U->>Q: search_sections(query)
    Q->>L: FTS5 BM25 search
    L-->>Q: ranked_results

    U->>H: hybrid_search(query)
    H->>E: generate_embedding(query)
    E-->>H: query_vector

    par Parallel Search
        H->>L: text_search(query)
        H->>S: vector_search(vector)
    end

    H-->>H: merge_rankings()
    H-->>U: (section_id, hybrid_score)

    U->>Q: get_section(section_id)
    Q-->>U: Section object
```

### Progressive Disclosure Flow

```mermaid
stateDiagram-v2
    [*] --> Search: User enters query
    Search --> Results: Ranked sections
    Results --> LoadSection: User selects section
    LoadSection --> DisplayContent: Show section content
    DisplayContent --> Next: User wants next section
    Next --> HasChild: Drill into subsections?
    HasChild --> LoadChild: Load first child
    HasChild --> NextSibling: Move to next sibling
    LoadChild --> DisplayContent
    NextSibling --> LoadSection
    DisplayContent --> [*]: User satisfied
```

---

## Database Schema

### SQLite Schema (Local)

```mermaid
erDiagram
    FILES ||--o{ SECTIONS : contains
    FILES ||--o{ CHECKOUTS : tracks
    SECTIONS ||--o{ SECTIONS : parent_child
    SECTIONS ||--o|| SECTIONS_FTS : fulltext_index

    FILES {
        INTEGER id PK
        TEXT path UK
        TEXT type
        TEXT frontmatter
        TEXT hash
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    SECTIONS {
        INTEGER id PK
        INTEGER file_id FK
        INTEGER parent_id FK
        INTEGER level
        TEXT title
        TEXT content
        INTEGER order_index
        INTEGER line_start
        INTEGER line_end
        TEXT closing_tag_prefix
    }

    SECTIONS_FTS {
        INTEGER rowid PK
        TEXT title
        TEXT content
    }

    CHECKOUTS {
        INTEGER id PK
        TEXT file_id FK
        TEXT user_name
        TEXT target_path
        TEXT status
        TIMESTAMP checked_out_at
        TIMESTAMP checked_in_at
    }
```

### Supabase Schema (Cloud)

```mermaid
erDiagram
    FILES ||--o{ SECTIONS : contains
    FILES ||--o{ CHECKOUTS : tracks
    SECTIONS ||--o{ SECTION_EMBEDDINGS : vectors
    FILES ||--o{ MULTIFILE_METADATA : related

    FILES {
        UUID id PK
        TEXT storage_path UK
        TEXT name
        TEXT type
        TEXT frontmatter
        TEXT hash
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    SECTIONS {
        UUID id PK
        UUID file_id FK
        UUID parent_id FK
        INTEGER level
        TEXT title
        TEXT content
        INTEGER order_index
        INTEGER line_start
        INTEGER line_end
        TEXT closing_tag_prefix
        VECTOR(1536) embedding
    }

    SECTION_EMBEDDINGS {
        UUID section_id FK
        TEXT content_hash
        VECTOR(1536) embedding
        TIMESTAMP created_at
    }

    CHECKOUTS {
        UUID id PK
        UUID file_id FK
        TEXT user_name
        TEXT target_path
        TEXT status
        TEXT notes
        TIMESTAMP checked_out_at
        TIMESTAMP checked_in_at
    }

    MULTIFILE_METADATA {
        UUID id PK
        UUID primary_file_id FK
        TEXT component_type
        JSONB related_files
        TEXT schema_version
        JSONB dependencies
    }
```

### Key Relationships

- **CASCADE Delete**: Deleting a file automatically removes all sections
- **Foreign Keys**: `sections.file_id` → `files.id`, `sections.parent_id` → `sections.id`
- **FTS5 External Content**: `sections_fts` mirrors `sections` for full-text search
- **Vector Index**: Supabase uses ivfflat HNSW indexing for fast similarity search

---

## Search Architecture

### Three-Tier Search System

```mermaid
graph LR
    subgraph "Tier 1: BM25 Keywords"
        Query[User Query]
        Preproc[Query Preprocessor]
        FTS5[FTS5 Full-Text]
        BM25[BM25 Ranking]
    end

    subgraph "Tier 2: Vector Search"
        Embed[Embedding Service]
        Supa[Supabase pgvector]
        Cosine[Cosine Similarity]
    end

    subgraph "Tier 3: Hybrid Fusion"
        Normalize[Score Normalizer]
        Weight[Weighted Average]
        Rank[Final Ranking]
    end

    Query --> Preproc
    Preproc --> FTS5
    FTS5 --> BM25
    Query --> Embed
    Embed --> Supa
    Supa --> Cosine
    BM25 --> Normalize
    Cosine --> Normalize
    Normalize --> Weight
    Weight --> Rank

    style BM25 fill:#c8e6c9
    style Cosine fill:#fff9c4
    style Rank fill:#ffccbc
```

### Search Modes Comparison

| Mode | Use Case | Speed | Accuracy | API Key Required |
|------|----------|-------|----------|------------------|
| **BM25** (Keywords) | Exact term matching, technical queries | Fastest | High for precise terms | No |
| **Vector** (Semantic) | Conceptual similarity, synonyms | Fast | High for meaning | Yes (OpenAI) |
| **Hybrid** (Combined) | Best overall results | Medium | Highest | Yes (OpenAI) |

### Query Preprocessing

```
Natural Language Input
         |
         v
[Contains Operators?] ──Yes──> Normalize AND/OR/NEAR to uppercase
         |
         No
         |
[Quoted Phrase?] ──Yes──> Use as-is (phrase search)
         |
         No
         |
[Single Word?] ──Yes──> Quote if special chars
         |
         No
         |
[Multi-word] ──Yes──> Convert to OR for discovery
         |
         v
    FTS5 MATCH Syntax
```

**Example Transformations**:
- `"python handler"` → `"python handler"` (phrase search)
- `python AND handler` → `python AND handler` (user operator)
- `python handler` → `"python" OR "handler"` (discovery mode)

### Hybrid Scoring Formula

```
hybrid_score = (vector_weight × vector_similarity) + ((1 - vector_weight) × text_score)

Where:
- vector_weight: 0.0 (text-only) to 1.0 (vector-only), default 0.7
- vector_similarity: Cosine similarity from pgvector (0-1)
- text_score: Normalized BM25 rank (0-1)
```

### Performance Metrics

```mermaid
graph TB
    subgraph "Search Metrics"
        Total[Total Searches: 0]
        Latency[Avg Latency: 0ms]
        Vector[Vector Searches: 0]
        Text[Text Searches: 0]
        Cache[Embedding Cache Hit Rate: 0%]
        Failed[Failed Searches: 0]
    end

    style Total fill:#e1f5ff
    style Latency fill:#fff9c4
    style Cache fill:#c8e6c9
```

---

## Component Handlers

### Handler Architecture

```mermaid
classDiagram
    class BaseHandler {
        <<abstract>>
        +parse() ParsedDocument
        +validate() ValidationResult
        +get_file_type() FileType
        +get_file_format() FileFormat
        +get_related_files() List~str~
    }

    class PluginHandler {
        -plugin_path: str
        +parse() ParsedDocument
        +_parse_plugin_json() dict
        +_extract_hooks() List~Hook~
        +_find_related_files() List~str~
    }

    class HookHandler {
        -hooks_path: str
        +parse() ParsedDocument
        +_parse_hooks_json() dict
        +_extract_shell_scripts() List~Section~
        +_validate_script_syntax() bool
    }

    class ConfigHandler {
        -config_path: str
        +parse() ParsedDocument
        +_parse_settings_json() dict
        +_parse_mcp_config() dict
        +_validate_schema() bool
    }

    class ScriptHandler {
        <<abstract>>
        +parse() ParsedDocument
        +_extract_functions() List~Section~
        +_extract_classes() List~Section~
    }

    class PythonHandler {
        +parse() ParsedDocument
        +_extract_classes() List~Section~
        +_extract_functions() List~Section~
        +_extract_methods() List~Section~
    }

    class JavaScriptHandler {
        +parse() ParsedDocument
        +_extract_functions() List~Section~
        +_extract_classes() List~Section~
        +_extract_exports() List~Section~
    }

    class TypeScriptHandler {
        +parse() ParsedDocument
        +_extract_interfaces() List~Section~
        +_extract_types() List~Section~
        +_extract_classes() List~Section~
    }

    class ShellHandler {
        +parse() ParsedDocument
        +_extract_functions() List~Section~
        +_extract_heredocs() List~Section~
    }

    BaseHandler <|-- PluginHandler
    BaseHandler <|-- HookHandler
    BaseHandler <|-- ConfigHandler
    BaseHandler <|-- ScriptHandler
    ScriptHandler <|-- PythonHandler
    ScriptHandler <|-- JavaScriptHandler
    ScriptHandler <|-- TypeScriptHandler
    ScriptHandler <|-- ShellHandler
```

### Supported File Types

| Handler | Extensions | Parsed Elements | Multi-File |
|---------|------------|-----------------|------------|
| **PluginHandler** | `.json` (plugin.json) | Commands, hooks, metadata | Yes (.mcp.json, hooks.json) |
| **HookHandler** | `.json` (hooks.json) | Hook definitions | Yes (shell scripts) |
| **ConfigHandler** | `.json` (settings.json, mcp_config.json) | Settings, MCP servers | No |
| **PythonHandler** | `.py` | Classes, functions, methods | No |
| **JavaScriptHandler** | `.js`, `.jsx` | Functions, classes, exports | No |
| **TypeScriptHandler** | `.ts`, `.tsx` | Interfaces, types, classes | No |
| **ShellHandler** | `.sh` | Functions, heredocs | No |

### Handler Factory Flow

```mermaid
graph TB
    Start[File Path] --> Detect{ComponentDetector}
    Detect -->|Plugin.json| Plugin[PluginHandler]
    Detect -->|Hooks.json| Hook[HookHandler]
    Detect -->|Settings/MCP Config| Config[ConfigHandler]
    Detect -->|.py/.js/.ts/.sh| Script{ScriptHandler}
    Script -->|Python| Python[PythonHandler]
    Script -->|JavaScript| JS[JavaScriptHandler]
    Script -->|TypeScript| TS[TypeScriptHandler]
    Script -->|Shell| Shell[ShellHandler]
    Detect -->|Unknown| Default[Use Core Parser]

    style Plugin fill:#c8e6c9
    style Hook fill:#fff9c4
    style Config fill:#ffccbc
    style Python fill:#e1f5ff
```

---

## API Layer

### CLI Commands (16 Total)

#### Core Commands

```mermaid
graph LR
    subgraph "Parsing"
        P1[parse]
        P2[validate]
        P3[store]
    end

    subgraph "Query"
        Q1[get]
        Q2[tree]
        Q3[get-section]
        Q4[next]
        Q5[list]
        Q6[search]
        Q7[search-semantic]
    end

    subgraph "Supabase"
        S1[ingest]
        S2[checkout]
        S3[checkin]
        S4[list-library]
        S5[status]
        S6[search-library]
    end

    subgraph "Composition"
        C1[compose]
    end

    subgraph "Utilities"
        U1[verify]
        U2[backup]
        U3[restore]
    end
```

#### Command Reference

| Command | Purpose | Database |
|---------|---------|----------|
| `parse <file>` | Display structure without storing | N/A |
| `validate <file>` | Validate file structure | N/A |
| `store <file> --db <path>` | Parse and store | Local |
| `get <file> --db <path>` | Retrieve file metadata | Local |
| `tree <file> --db <path>` | Show section hierarchy | Local |
| `get-section <id> --db <path>` | Load single section | Local |
| `next <id> <file> --db <path>` | Get next section | Local |
| `list <file> --db <path>` | List sections with IDs | Local |
| `search <query> --db <path>` | BM25 keyword search | Local |
| `search-semantic <query> --db <path>` | Hybrid vector search | Local + Supabase |
| `verify <file> --db <path>` | Round-trip validation | Local |
| `ingest <dir>` | Batch upload | Supabase |
| `checkout <id> <path>` | Deploy file | Supabase |
| `checkin <path>` | Return file | Supabase |
| `list-library` | List all files | Supabase |
| `status [--user]` | Show checkouts | Supabase |
| `search-library <query>` | Search files | Supabase |
| `compose --sections <ids> --output <file>` | Create new skill | Local |
| `backup [--db <path>]` | Create backup | Local |
| `restore <backup> [--db <path>]` | Restore from backup | Local |

### Query API

```python
from core.query import QueryAPI

query_api = QueryAPI(db_path)

# Progressive disclosure operations
section = query_api.get_section(section_id)
next_section = query_api.get_next_section(current_id, file_path, first_child=True)
tree = query_api.get_section_tree(file_path)

# Search operations
results = query_api.search_sections(query)  # FTS5 BM25
ranked = query_api.search_sections_with_rank(query)  # With scores
```

### Hybrid Search API

```python
from core.hybrid_search import HybridSearch
from core.embedding_service import EmbeddingService

embedding_service = EmbeddingService(openai_api_key)
hybrid = HybridSearch(embedding_service, supabase_store, query_api)

# Adjustable vector weight (0.0 = text-only, 1.0 = vector-only)
results = hybrid.hybrid_search(
    query="how to setup git",
    limit=10,
    vector_weight=0.7
)

# Get performance metrics
metrics = hybrid.get_metrics()
```

---

## Extension Points

### Adding a New Handler

1. **Create Handler Class**:

```python
from handlers.base import BaseHandler
from models import FileType, FileFormat, ParsedDocument

class MyHandler(BaseHandler):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> ParsedDocument:
        # Implementation
        pass

    def validate(self) -> ValidationResult:
        # Implementation
        pass

    def get_file_type(self) -> FileType:
        return FileType.MY_TYPE

    def get_file_format(self) -> FileFormat:
        return FileFormat.CUSTOM
```

2. **Register in ComponentDetector**:

```python
# In handlers/component_detector.py
def detect(self, file_path: str) -> tuple[FileType, FileFormat]:
    # Add detection logic
    if file_path.endswith('.myext'):
        return FileType.MY_TYPE, FileFormat.CUSTOM
```

3. **Register in HandlerFactory**:

```python
# In handlers/factory.py
@classmethod
def list_supported_extensions(cls) -> list[str]:
    return [..., '.myext']
```

### Adding a New Search Backend

```python
from core.database import DatabaseStore

class CustomSearchStore(DatabaseStore):
    def search_sections_with_rank(
        self, query: str, file_path: Optional[str] = None
    ) -> List[Tuple[int, float]]:
        # Implement custom search logic
        results = self._custom_search_algorithm(query)
        return results
```

### Adding a New Validation Rule

```python
from core.skill_validator import validate_skill, ValidationResult

def custom_validation_rule(doc: ParsedDocument) -> tuple[bool, List[str], List[str]]:
    errors = []
    warnings = []

    # Custom validation logic
    if some_condition:
        errors.append("Custom validation failed")

    return len(errors) == 0, errors, warnings
```

---

## Deployment Architecture

### Database Locations

```mermaid
graph TB
    subgraph "Local Development"
        Demo[./skill_split.db<br/>Demo: 1 file, 4 sections]
    end

    subgraph "Production Local"
        Prod[~/.claude/databases/skill-split.db<br/>Production: 1,365 files, 19,207 sections]
    end

    subgraph "Cloud Backup"
        Supabase[(Supabase PostgreSQL<br/>Full library with vector embeddings)]
    end

    Demo <--> Prod
    Prod <--> Supabase

    style Demo fill:#e1f5ff
    style Prod fill:#c8e6c9
    style Supabase fill:#ffccbc
```

### Schema Migration

If upgrading from an old schema, run:

```sql
ALTER TABLE sections ADD COLUMN closing_tag_prefix TEXT DEFAULT '';
```

### Backup and Restore

```bash
# Create backup
./skill_split.py backup --filename my-backup.sql.gz

# Restore from backup
./skill_split.py restore my-backup.sql.gz --db ~/.claude/databases/skill-split.db --overwrite
```

### Environment Variables

```bash
# Database
SKILL_SPLIT_DB=~/.claude/databases/skill-split.db

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...
ENABLE_EMBEDDINGS=true
```

---

## Performance Characteristics

### Token Efficiency

```
Original File: 21,000 tokens
Section Average: 204 tokens
Context Savings: 99.03%

Progressive Loading:
- First section: 204 tokens
- Next sections: 204 tokens each
- Total loaded: Only what's needed
```

### Search Performance

| Operation | Local (SQLite) | Cloud (Supabase) |
|-----------|----------------|------------------|
| BM25 Search | ~10ms | ~50ms |
| Vector Search | N/A | ~100ms |
| Hybrid Search | ~110ms | ~150ms |
| Section Retrieval | ~1ms | ~20ms |

### Scalability

- **Files per Database**: Tested up to 1,365 files
- **Sections per File**: Tested up to 92 sections
- **Total Sections**: 19,207 sections in production
- **Search Index**: FTS5 handles full corpus efficiently
- **Vector Index**: Supabase ivfflat HNSW for similarity search

---

## Security Considerations

### Secrets Management

```python
from core.secret_manager import SecretManager

# Secrets stored in ~/.claude/secrets.json
secret_manager = SecretManager()
supabase_key = secret_manager.get_secret("SUPABASE_KEY")
```

### SQL Injection Prevention

- All queries use parameterized statements
- User input is validated before database operations
- FTS5 queries are preprocessed to prevent injection

### File Access Control

- Checkout/checkin system tracks file deployments
- User attribution for all operations
- Safe rollback on failed operations

---

## Testing Strategy

### Test Coverage

- **518 Total Tests** (as of Phase 02 completion)
- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component workflows
- **Round-trip Tests**: Byte-perfect verification
- **Real-world Tests**: Production database validation

### Test Categories

```mermaid
graph TB
    subgraph "Core Tests"
        T1[test_parser]
        T2[test_database]
        T3[test_query]
        T4[test_recomposer]
    end

    subgraph "Handler Tests"
        H1[test_plugin_handler]
        H2[test_hook_handler]
        H3[test_config_handler]
        H4[test_script_handlers]
    end

    subgraph "Search Tests"
        S1[test_embedding_service]
        S2[test_hybrid_search]
        S3[test_vector_search]
    end

    subgraph "Integration Tests"
        I1[test_composer_integration]
        I2[test_batch_integration]
        I3[test_checkout_manager]
    end
```

---

## Architecture Decision Records

### ADR-001: SQLite FTS5 for Local Search

**Status**: Accepted

**Context**: Need fast, reliable keyword search without external dependencies.

**Decision**: Use SQLite FTS5 with BM25 ranking for local search.

**Consequences**:
- (+) Fast full-text search (~10ms)
- (+) No external services required
- (+) Portable database files
- (-) Limited to keyword matching (no semantic understanding)

### ADR-002: Supabase + pgvector for Cloud Storage

**Status**: Accepted

**Context**: Need cloud backup with semantic search capabilities.

**Decision**: Use Supabase PostgreSQL with pgvector extension.

**Consequences**:
- (+) Vector similarity search for semantic understanding
- (+) Automatic backups and replication
- (+) Real-time synchronization
- (-) Requires network connectivity
- (-) OpenAI API costs for embeddings

### ADR-003: Hybrid Search with Configurable Weights

**Status**: Accepted

**Context**: Users need both precision (keywords) and discovery (semantic).

**Decision**: Implement hybrid scoring with adjustable vector_weight parameter.

**Consequences**:
- (+) Flexible search behavior
- (+) Best of both approaches
- (-) More complex implementation
- (-) Requires API keys for vector search

### ADR-004: SHA256 Hashing for Integrity Verification

**Status**: Accepted

**Context**: Must guarantee byte-perfect round-trip accuracy.

**Decision**: SHA256 hashing of all files with verification on recomposition.

**Consequences**:
- (+) Detects any data corruption
- (+) Confirms parse/recompose accuracy
- (-) Additional compute overhead

### ADR-005: Factory Pattern for Component Handlers

**Status**: Accepted

**Context**: Need extensible parser architecture for different file types.

**Decision**: Factory pattern with HandlerFactory and BaseHandler abstraction.

**Consequences**:
- (+) Easy to add new file types
- (+) Clean separation of concerns
- (+) Consistent interface
- (-) More boilerplate for new handlers

---

## Future Enhancements

### Planned Features

1. **GraphQL API**: Alternative to REST for complex queries
2. **Web Interface**: Browser-based exploration and composition
3. **Real-time Sync**: WebSocket-based updates
4. **ML-Based Ranking**: Learn from user interactions
5. **Multi-language Support**: Beyond English embeddings

### Under Consideration

- Distributed storage (IPFS)
- Collaborative editing
- Version control integration
- Advanced analytics dashboard

---

## References

- **[README.md](../README.md)**: Complete documentation
- **[CLI_REFERENCE.md](./CLI_REFERENCE.md)**: Command reference
- **[EXAMPLES.md](../EXAMPLES.md)**: Usage examples
- **[DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md)**: Deployment guide

---

*This document is maintained as part of the skill-split project. For questions or contributions, refer to the main project documentation.*
