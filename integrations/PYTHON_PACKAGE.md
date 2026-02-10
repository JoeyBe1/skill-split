# Using skill-split as a Python Package

skill-split can be imported and used programmatically in your Python projects.

## Installation

```bash
pip install -e /path/to/skill-split
```

## Basic Usage

### Parsing Files

```python
from core.parser import Parser

parser = Parser()
with open("document.md") as f:
    content = f.read()

document = parser.parse(content, "document.md")

print(f"Found {len(document.sections)} sections")
for section in document.sections:
    print(f"  - {section.title} (level {section.level})")
```

### Database Storage

```python
from core.database import DatabaseStore

db = DatabaseStore("~/.claude/databases/skill-split.db")
file_id = db.store_document(document)
print(f"Stored with ID: {file_id}")
```

### Querying Sections

```python
from core.query import QueryAPI

query = QueryAPI("~/.claude/databases/skill-split.db")

# Get specific section
section = query.get_section(42)
print(section.content)

# Search for content
results = query.search_sections("python handler")
for section_id, title, content in results:
    print(f"{title}: {content[:100]}...")

# Progressive disclosure
next_section = query.get_next_section(42, "document.md")
next_child = query.get_next_section(42, "document.md", first_child=True)
```

### Skill Composition

```python
from core.skill_composer import SkillComposer

composer = SkillComposer("~/.claude/databases/skill-split.db")
composed = composer.compose_skill(
    section_ids=[1, 5, 10],
    title="My Custom Skill",
    description="Combines best practices",
    author="Your Name"
)

# Write to file
from pathlib import Path
Path("custom_skill.md").write_text(composed.content)
```

### Semantic Search

```python
from core.embedding_service import EmbeddingService
from core.query import QueryAPI

embedding_service = EmbeddingService()
query = QueryAPI("~/.claude/databases/skill-split.db")

# Generate query embedding
query_embedding = embedding_service.embed_text("authentication patterns")

# Search by vector
results = query.search_by_vector(query_embedding, limit=10)
```

## Advanced: Custom Handlers

Create custom handlers for new file types:

```python
from handlers.base import Handler
from models import Section, FileMetadata, FileType

class MyCustomHandler(Handler):
    """Handler for custom file format."""
    
    def can_handle(self, file_path: str) -> bool:
        return file_path.endswith(".myformat")
    
    def parse(self, content: str, file_path: str) -> list[Section]:
        sections = []
        # Your parsing logic here
        return sections

# Register handler
from handlers.factory import HandlerFactory
HandlerFactory.register("myformat", MyCustomHandler)
```

## Error Handling

```python
from core.parser import Parser
from core.database import DatabaseStore

try:
    parser = Parser()
    document = parser.parse(content, "file.md")
except ValueError as e:
    print(f"Parse error: {e}")

try:
    db = DatabaseStore("database.db")
    file_id = db.store_document(document)
except sqlite3.Error as e:
    print(f"Database error: {e}")
```

## Batch Processing

```python
from pathlib import Path
from core.parser import Parser
from core.database import DatabaseStore

parser = Parser()
db = DatabaseStore("database.db")

for file_path in Path("skills/").glob("*.md"):
    content = file_path.read_text()
    document = parser.parse(content, str(file_path))
    file_id = db.store_document(document)
    print(f"Processed {file_path}: {len(document.sections)} sections")
```

## Working with Section Trees

```python
from core.query import QueryAPI

query = QueryAPI("database.db")

def print_tree(section, indent=0):
    print("  " * indent + f"- {section.title}")
    for child in section.children:
        print_tree(child, indent + 1)

tree = query.get_section_tree("document.md")
for root_section in tree:
    print_tree(root_section)
```

## Integration Example: Discord Bot

```python
import discord
from core.query import QueryAPI
from core.parser import Parser

bot = discord.Client()
query = QueryAPI("~/.claude/databases/skill-split.db")
parser = Parser()

@bot.event
async def on_message(message):
    if message.content.startswith("!search"):
        query_text = message.content[8:]
        results = query.search_sections(query_text)
        
        response = f"Found {len(results)} results:\n"
        for section_id, title, _ in results[:5]:
            response += f"- {title} (ID: {section_id})\n"
        
        await message.channel.send(response)
    
    elif message.content.startswith("!section"):
        section_id = int(message.content.split()[1])
        section = query.get_section(section_id)
        await message.channel.send(f"## {section.title}\n\n{section.content}")
```
