# API Quick Reference

**Complete API: See [API.md](API.md)**

## Python API

### Core Classes

```python
from skill_split import SkillSplit
from core.database import Database
from core.query import QueryAPI
```

### Initialization

```python
# Default initialization
ss = SkillSplit()

# Custom database
db = Database(path="/path/to/database.db")
```

### Parsing

```python
# Parse file
doc = ss.parse_file("README.md")

# Parse string
doc = ss.parse_string(content)
```

### Storage

```python
# Store document
db.store_document(doc)

# Store sections
db.store_sections(doc.sections, doc.metadata)
```

### Querying

```python
# Initialize query API
query = QueryAPI(db)

# Get section by ID
section = query.get_section(42)

# Get next section
next_section = query.get_next_section(42, filename="README.md")

# Search (BM25)
results = query.search_sections("query", limit=10)

# Hybrid search
results = query.hybrid_search(
    query="search term",
    vector_weight=0.7,
    limit=10
)
```

## CLI API

### Core Commands

```bash
# Parse
./skill_split.py parse <file>

# Validate
./skill_split.py validate <file>

# Store
./skill_split.py store <file>

# List sections
./skill_split.py list <file>

# Get section
./skill_split.py get-section <id>

# Navigate
./skill_split.py next <id> <file> [--child]
```

### Search Commands

```bash
# BM25 (keyword)
./skill_split.py search "query"

# Vector (semantic)
./skill_split.py search-semantic "query" --vector-weight 1.0

# Hybrid
./skill_split.py search-semantic "query" --vector-weight 0.7
```

### Database Commands

```bash
# Status
./skill_split.py status

# Backup
./skill_split.py backup <path>

# Restore
./skill_split.py restore <path>
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--db` | Database path | `./skill_split.db` |
| `--verbose` | Verbose output | `false` |
| `--limit` | Result limit | `10` |
| `--vector-weight` | Hybrid weight | `0.7` |
| `--batch-size` | Batch size | `100` |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SKILL_SPLIT_DB` | Database path | No |
| `OPENAI_API_KEY` | OpenAI API key | Vector search |
| `SUPABASE_URL` | Supabase URL | Supabase |
| `SUPABASE_KEY` | Supabase key | Supabase |
| `ENABLE_EMBEDDINGS` | Enable vectors | No |

## Output Formats

### Section Object

```python
{
    "id": 42,
    "file_path": "README.md",
    "heading": "Installation",
    "level": 2,
    "content": "# Installation\n\n...",
    "line_start": 10,
    "line_end": 25,
    "parent_id": 4,
    "hash": "abc123..."
}
```

### Search Result

```python
{
    "section": {...},
    "score": 0.95,
    "rank": 1
}
```

## Error Handling

```python
try:
    section = query.get_section(999)
except SectionNotFoundError:
    print("Section not found")

try:
    db.store_document(doc)
except DatabaseError as e:
    print(f"Database error: {e}")
```

---

**See [API.md](API.md) for complete API documentation**

*skill-split - Progressive disclosure for AI workflows*
