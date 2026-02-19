# API Documentation

This document provides comprehensive documentation for the skill-split programmatic API.

## Table of Contents

- [Overview](#overview)
- [Core Modules](#core-modules)
- [Data Models](#data-models)
- [Query API](#query-api)
- [Component Handlers](#component-handlers)
- [Examples](#examples)

## Overview

skill-split provides a Python API for:

- Parsing structured documents (YAML, Markdown, XML)
- Storing sections in SQLite
- Progressive disclosure retrieval
- Full-text search with relevance ranking
- Component-specific parsing (plugins, hooks, configs)
- Skill composition

### Quick Import

```python
from core.parser import parse_document, parse_file
from core.database import DatabaseStore
from core.query import QueryAPI
from core.recomposer import recompose_document
from core.skill_composer import SkillComposer
from models import Section, ParsedDocument, FileType, FileFormat
```

## Core Modules

### Parser Module (`core/parser.py`)

The parser module extracts structured sections from documents.

#### `parse_document(content: str, path: str) -> ParsedDocument`

Parse a document string into structured sections.

**Parameters:**
- `content` (str): The document content to parse
- `path` (str): File path for type detection and error reporting

**Returns:** `ParsedDocument` with sections and metadata

**Raises:**
- `ValueError`: If content is invalid or parsing fails

**Example:**

```python
from core.parser import parse_document

content = """---
name: my-skill
version: 1.0.0
---

# Installation

Install the package.

## Usage

Use the command.
"""

doc = parse_document(content, "skill.md")
print(doc.frontmatter)  # "name: my-skill\nversion: 1.0.0\n"
print(doc.file_type)    # FileType.SKILL
print(doc.sections)     # List of Section objects
```

#### `parse_file(path: str) -> ParsedDocument`

Parse a file directly from disk.

**Parameters:**
- `path` (str): Path to the file

**Returns:** `ParsedDocument`

**Example:**

```python
from core.parser import parse_file

doc = parse_file("~/skills/programming.md")
for section in doc.sections:
    print(f"{section.title}: {section.content[:50]}...")
```

### Database Module (`core/database.py`)

The database module handles SQLite storage and retrieval.

#### `DatabaseStore(db_path: str)`

Main class for database operations.

**Constructor:**
- `db_path` (str): Path to SQLite database file

**Methods:**

##### `store_document(document: ParsedDocument) -> int`

Store a parsed document in the database.

**Parameters:**
- `document` (ParsedDocument): The document to store

**Returns:** `int` - The file ID

**Example:**

```python
from core.database import DatabaseStore
from core.parser import parse_file

store = DatabaseStore("skill-split.db")
doc = parse_file("skill.md")
file_id = store.store_document(doc)
print(f"Stored with ID: {file_id}")
```

##### `get_section(section_id: int) -> Optional[Section]`

Retrieve a single section by ID.

**Parameters:**
- `section_id` (int): Section ID

**Returns:** `Section` or `None`

##### `get_section_tree(path: str) -> List[Section]`

Get full hierarchical tree for a file.

**Parameters:**
- `path` (str): File path

**Returns:** List of top-level `Section` objects with populated children

##### `search_sections_with_rank(query: str, file_path: Optional[str] = None) -> List[tuple[int, float]]`

Search sections with BM25 relevance ranking.

**Parameters:**
- `query` (str): FTS5 search query
- `file_path` (Optional[str]): Limit to specific file

**Returns:** List of `(section_id, rank)` tuples

**Example:**

```python
from core.database import DatabaseStore

store = DatabaseStore("skill-split.db")
results = store.search_sections_with_rank("python handler")

for section_id, rank in results:
    print(f"Section {section_id}: relevance {rank:.2f}")
```

### Query API (`core/query.py`)

High-level API for progressive disclosure.

#### `QueryAPI(db_path: str)`

Query interface for progressive section disclosure.

**Constructor:**
- `db_path` (str): Path to SQLite database

**Methods:**

##### `get_section(section_id: int) -> Optional[Section]`

Retrieve a single section by ID.

**Parameters:**
- `section_id` (int): Section ID

**Returns:** `Section` or `None`

**Example:**

```python
from core.query import QueryAPI

api = QueryAPI("skill-split.db")
section = api.get_section(42)
if section:
    print(f"{section.title}\n{section.content}")
```

##### `get_next_section(current_id: int, file_path: str, first_child: bool = False) -> Optional[Section]`

Navigate to next section for progressive disclosure.

**Parameters:**
- `current_id` (int): Current section ID
- `file_path` (str): File path
- `first_child` (bool): If True, return first child instead of next sibling

**Returns:** Next `Section` or `None`

**Example:**

```python
# Get next sibling
next_section = api.get_next_section(42, "skill.md")

# Drill into first child
child_section = api.get_next_section(42, "skill.md", first_child=True)
```

##### `get_section_tree(file_path: str) -> List[Section]`

Get full hierarchical tree.

**Parameters:**
- `file_path` (str): File path

**Returns:** List of top-level `Section` objects

##### `search_sections(query: str, file_path: Optional[str] = None) -> List[tuple[int, Section]]`

Search sections by content.

**Parameters:**
- `query` (str): Search query
- `file_path` (Optional[str]): Limit to specific file

**Returns:** List of `(section_id, Section)` tuples

**Example:**

```python
# Search all files
results = api.search_sections("authentication")

for section_id, section in results:
    print(f"[{section_id}] {section.title}")

# Search specific file
results = api.search_sections("python", file_path="skills/programming.md")
```

### Recomposer Module (`core/recomposer.py`)

#### `recompose_document(sections: List[Section], frontmatter: str = "") -> str`

Recompose a document from sections.

**Parameters:**
- `sections` (List[Section]): List of sections (usually from `get_section_tree`)
- `frontmatter` (str): YAML frontmatter to prepend

**Returns:** Complete document as string

**Example:**

```python
from core.recomposer import recompose_document
from core.query import QueryAPI

api = QueryAPI("skill-split.db")
sections = api.get_section_tree("skill.md")
frontmatter = api.store.get_file_metadata("skill.md").frontmatter

recomposed = recompose_document(sections, frontmatter)
with open("recomposed.md", "w") as f:
    f.write(recomposed)
```

### Skill Composer Module (`core/skill_composer.py`)

#### `SkillComposer(db_path: str)`

Compose new skills from existing sections.

**Constructor:**
- `db_path` (str): Path to SQLite database

**Methods:**

##### `compose_from_sections(section_ids: List[int], output_path: str, metadata: dict) -> ComposedSkill`

Compose a new skill from sections.

**Parameters:**
- `section_ids` (List[int]): List of section IDs to compose
- `output_path` (str): Output file path
- `metadata` (dict): Metadata for frontmatter (title, description, etc.)

**Returns:** `ComposedSkill` object

**Example:**

```python
from core.skill_composer import SkillComposer

composer = SkillComposer("skill-split.db")
metadata = {
    "title": "Combined Python Guide",
    "description": "Essential Python patterns and best practices",
    "version": "1.0.0"
}

result = composer.compose_from_sections(
    section_ids=[42, 156, 203],
    output_path="combined-python.md",
    metadata=metadata
)

print(f"Created: {result.output_path}")
print(f"Hash: {result.composed_hash}")
```

## Data Models

### Section

Represents a parsed section of a document.

```python
@dataclass
class Section:
    level: int              # Heading level (1-6) or -1 for XML
    title: str              # Section title
    content: str            # Section content (excluding children)
    line_start: int         # Starting line number
    line_end: int           # Ending line number
    closing_tag_prefix: str # Whitespace before closing tag
    children: List[Section] # Nested subsections
    parent: Optional[Section] # Parent section
    file_id: Optional[str]  # Origin file ID
    file_type: Optional[FileType] # Origin file type
```

**Methods:**

- `add_child(child: Section)`: Add a child section
- `get_all_content() -> str`: Get content including all descendants
- `to_dict() -> dict`: Convert to dictionary

### ParsedDocument

Represents a fully parsed document.

```python
@dataclass
class ParsedDocument:
    frontmatter: str        # YAML frontmatter
    sections: List[Section] # Top-level sections
    file_type: FileType     # File type (SKILL, COMMAND, etc.)
    format: FileFormat      # Format (MARKDOWN_HEADINGS, XML_TAGS, etc.)
    original_path: str      # Original file path
```

**Methods:**

- `get_section_by_title(title: str) -> Optional[Section]`: Find section by title
- `to_dict() -> dict`: Convert to dictionary

### FileType (Enum)

File type based on location/purpose.

```python
class FileType(Enum):
    SKILL = "skill"
    COMMAND = "command"
    REFERENCE = "reference"
    AGENT = "agent"
    PLUGIN = "plugin"
    HOOK = "hook"
    CONFIG = "config"
    SCRIPT = "script"
    DOCUMENTATION = "documentation"
```

### FileFormat (Enum)

Detected file structure type.

```python
class FileFormat(Enum):
    MARKDOWN_HEADINGS = "markdown_headings"
    XML_TAGS = "xml_tags"
    MIXED = "mixed"
    JSON = "json"
    JSON_SCHEMA = "json_schema"
    SHELL_SCRIPT = "shell"
    MULTI_FILE = "multi_file"
    PYTHON_SCRIPT = "python"
    JAVASCRIPT_TYPESCRIPT = "javascript_typescript"
```

### ComposedSkill

Represents a skill composed from multiple sections.

```python
@dataclass
class ComposedSkill:
    section_ids: List[int]      # Source section IDs
    sections: Dict[int, Section] # Section data
    output_path: str             # Output file path
    frontmatter: str             # Generated frontmatter
    title: str                   # Skill title
    description: str             # Skill description
    composed_hash: str           # SHA256 hash
```

## Component Handlers

### Handler Factory

```python
from handlers.factory import HandlerFactory
from handlers.base import BaseHandler
```

#### `HandlerFactory.create_handler(path: str) -> Optional[BaseHandler]`

Create appropriate handler for file type.

**Parameters:**
- `path` (str): File path

**Returns:** `BaseHandler` subclass or `None`

**Example:**

```python
from handlers.factory import HandlerFactory

handler = HandlerFactory.create_handler("plugin.json")
if handler:
    sections = handler.parse()
```

### Plugin Handler

```python
from handlers.plugin_handler import PluginHandler
```

Parse `plugin.json` files with MCP config and hooks.

**Example:**

```python
from handlers.plugin_handler import PluginHandler

handler = PluginHandler("~/.claude/plugins/my-plugin/plugin.json")
sections = handler.parse()

# Get related files
related = handler.get_related_files()  # [.mcp.json, hooks.json]
```

### Script Handlers

```python
from handlers.python_handler import PythonHandler
from handlers.javascript_handler import JavaScriptHandler
from handlers.shell_handler import ShellHandler
```

Parse script files by language.

**Example:**

```python
from handlers.python_handler import PythonHandler

handler = PythonHandler("script.py")
sections = handler.parse()

for section in sections:
    print(f"{section.title}: {section.line_start}-{section.line_end}")
```

## Examples

### Complete Workflow: Parse, Store, Query

```python
from core.parser import parse_file
from core.database import DatabaseStore
from core.query import QueryAPI

# Parse a file
doc = parse_file("~/skills/programming.md")
print(f"Parsed {len(doc.sections)} sections")

# Store in database
store = DatabaseStore("skill-split.db")
file_id = store.store_document(doc)
print(f"Stored with file ID: {file_id}")

# Query for specific sections
api = QueryAPI("skill-split.db")

# Get a specific section
section = api.get_section(42)
print(section.title)
print(section.content)

# Search for content
results = api.search_sections("authentication")
for section_id, section in results:
    print(f"[{section_id}] {section.title}")

# Get file tree
tree = api.get_section_tree("~/skills/programming.md")
for section in tree:
    print(f"{'  ' * (section.level - 1)}{section.title}")
```

### Progressive Disclosure Workflow

```python
from core.query import QueryAPI

api = QueryAPI("skill-split.db")
file_path = "skills/programming.md"

# Start with first section
current_id = 1  # First section ID

while True:
    section = api.get_section(current_id)
    if not section:
        break

    print(f"\n{'#' * section.level} {section.title}")
    print(section.content)

    # Check if user wants to continue
    response = input("\nNext? (n=next, c=child, q=quit): ")

    if response == 'q':
        break
    elif response == 'c':
        # Drill into first child
        next_section = api.get_next_section(current_id, file_path, first_child=True)
        if next_section:
            current_id = api.store.get_section_id_by_title(
                next_section.title, file_path
            )
        else:
            print("No children found")
    else:
        # Get next sibling
        next_section = api.get_next_section(current_id, file_path)
        if next_section:
            current_id = api.store.get_section_id_by_title(
                next_section.title, file_path
            )
        else:
            print("No more sections")
            break
```

### Skill Composition

```python
from core.skill_composer import SkillComposer
from core.query import QueryAPI

# Search for relevant sections
api = QueryAPI("skill-split.db")
results = api.search_sections("python best practices")

# Select sections to compose
section_ids = [sid for sid, _ in results[:5]]

# Compose new skill
composer = SkillComposer("skill-split.db")
metadata = {
    "title": "Python Best Practices",
    "description": "Essential Python patterns and conventions",
    "version": "1.0.0",
    "author": "skill-split"
}

result = composer.compose_from_sections(
    section_ids=section_ids,
    output_path="python-best-practices.md",
    metadata=metadata
)

print(f"Created skill: {result.output_path}")
print(f"Sections: {len(result.section_ids)}")
```

### Custom Handler Implementation

```python
from handlers.base import BaseHandler
from models import Section, ParsedDocument, FileType, FileFormat

class CustomHandler(BaseHandler):
    """Custom handler for specific file format."""

    def parse(self) -> ParsedDocument:
        """Parse custom file format."""
        # Your parsing logic here
        sections = []

        # Extract sections from self.content
        # ...

        return ParsedDocument(
            frontmatter="",
            sections=sections,
            file_type=FileType.DOCUMENTATION,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path=self.path
        )

    def get_related_files(self) -> list[str]:
        """Return list of related files."""
        return []

# Register with factory (modify factory.py)
# HandlerFactory._handlers['.custom'] = CustomHandler
```

## Error Handling

```python
from core.parser import parse_document, ParseError
from core.database import DatabaseStore

try:
    doc = parse_document(content, "file.md")
except ParseError as e:
    print(f"Parse error: {e}")
    print(f"  Line: {e.line_number}")
    print(f"  Context: {e.context}")

try:
    store = DatabaseStore("skill-split.db")
    store.store_document(doc)
except DatabaseError as e:
    print(f"Database error: {e}")
```

## Best Practices

1. **Always use context managers for database operations:**
   ```python
   with sqlite3.connect(db_path) as conn:
       # operations
   ```

2. **Check for None returns:**
   ```python
   section = api.get_section(id)
   if section is None:
       return "Section not found"
   ```

3. **Use type hints for clarity:**
   ```python
   def process_section(section: Section) -> str:
       return section.content.upper()
   ```

4. **Handle exceptions gracefully:**
   ```python
   try:
       doc = parse_file(path)
   except (IOError, ParseError) as e:
       logger.error(f"Failed to parse {path}: {e}")
       return None
   ```

---

**Last Updated:** 2026-02-10
