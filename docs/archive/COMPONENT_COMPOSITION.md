# Skill Composition Guide

**Version**: Phase 11
**Last Updated**: 2026-02-05
**Purpose**: Guide for composing custom skills from existing sections

---

## Overview

The **SkillComposer API** allows you to build custom skills by combining sections from your existing database. This enables:

- **Composition from existing content**: Reuse sections to create new skills without duplication
- **Custom skill creation**: Combine related sections from different files into one cohesive skill
- **Progressive disclosure**: Load and explore sections before composing them
- **Programmatic control**: Use the Python API or CLI for automation

---

## Quick Start

### CLI Composition

#### Basic Composition

```bash
# Find interesting sections first
./skill_split.py search "authentication" --db ~/.claude/databases/skill-split.db

# Compose custom skill from specific sections
./skill_split.py compose \
  --sections 101,205,310 \
  --output ~/.claude/skills/custom-auth.md \
  --title "Custom Auth Patterns" \
  --description "Selected authentication patterns from library"
```

#### Uploading to Supabase

```bash
# Compose and upload in one step
./skill_split.py compose \
  --sections 101,205,310 \
  --output ~/.claude/skills/custom-auth.md \
  --title "Custom Auth Patterns" \
  --upload
```

### Programmatic Composition

#### Basic Python Example

```python
from core.skill_composer import SkillComposer
from core.database import DatabaseStore

# Create composer with database path
db = DatabaseStore("~/.claude/databases/skill-split.db")
composer = SkillComposer(db)

# Compose skill from sections
composed = composer.compose_from_sections(
    section_ids=[101, 205, 310],
    output_path="~/.claude/skills/custom-auth.md",
    title="Custom Auth Patterns",
    description="Selected authentication patterns from library"
)

# Write to filesystem
hash_val = composer.write_to_filesystem(composed)
print(f"Composed skill hash: {hash_val}")
```

#### With Supabase Upload

```python
from core.supabase_store import SupabaseStore
import os

# Create composer
composer = SkillComposer(db)

# Compose skill
composed = composer.compose_from_sections(
    section_ids=[101, 205, 310],
    output_path="~/.claude/skills/custom-auth.md",
    title="Custom Auth Patterns"
)

# Write to filesystem
composer.write_to_filesystem(composed)

# Upload to Supabase
supabase = SupabaseStore(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)
file_id = composer.upload_to_supabase(composed, supabase)
print(f"Uploaded to Supabase: {file_id}")
```

---

## Workflow

### Step 1: Search for Sections

First, find the sections you want to compose.

**Using CLI:**
```bash
# Search for sections containing specific keywords
./skill_split.py search "authentication" --db ~/.claude/databases/skill-split.db

# Search within a file
./skill_split.py search "jwt" --db ~/.claude/databases/skill-split.db --file ~/.claude/skills/auth.md

# Get section tree to explore hierarchy
./skill_split.py list ~/.claude/skills/auth.md --db ~/.claude/databases/skill-split.db
```

**Using Python API:**
```python
from core.query import QueryAPI

query_api = QueryAPI("~/.claude/databases/skill-split.db")

# Search for sections
results = query_api.search_sections(
    query="authentication",
    file_path="~/.claude/skills/auth.md"
)

for section_id, section in results:
    print(f"Section {section_id}: {section.title}")

# Get section hierarchy
tree = query_api.get_section_tree("~/.claude/skills/auth.md")
```

### Step 2: Select Sections

Choose which section IDs you want to include in your composition.

```python
# Get section IDs from search results or manually
section_ids = [101, 205, 310]
```

### Step 3: Compose Skill

Create a new skill by combining the selected sections.

```python
composer = SkillComposer(db)

composed = composer.compose_from_sections(
    section_ids=section_ids,
    output_path="~/.claude/skills/custom.md",
    title="My Custom Skill",
    description="Composed from selected sections"
)
```

### Step 4: Write to Filesystem

Save the composed skill to disk.

```python
hash_val = composer.write_to_filesystem(composed)
print(f"Written to {composed.output_path}")
print(f"Hash: {hash_val}")
```

### Step 5: Upload (Optional)

Push the composed skill to Supabase for remote storage.

```python
file_id = composer.upload_to_supabase(composed, supabase_store)
print(f"Uploaded: {file_id}")
```

---

## CLI Commands

### compose

Compose a new skill from section IDs.

**Syntax:**
```bash
./skill_split.py compose --sections <IDS> --output <PATH> [OPTIONS]
```

**Options:**
- `--sections` (required): Comma-separated section IDs (e.g., `101,205,310`)
- `--output` (required): Output file path (e.g., `~/.claude/skills/custom.md`)
- `--title` (optional): Skill title (auto-generated if not provided)
- `--description` (optional): Skill description (auto-generated if not provided)
- `--upload` (optional): Upload to Supabase immediately

**Examples:**
```bash
# Basic composition
./skill_split.py compose --sections 101,205 --output ~/skills/auth.md

# With metadata
./skill_split.py compose \
  --sections 101,205,310 \
  --output ~/skills/auth.md \
  --title "Authentication Guide" \
  --description "Complete auth patterns"

# With upload
./skill_split.py compose \
  --sections 101,205,310 \
  --output ~/skills/auth.md \
  --upload
```

---

## API Reference

### SkillComposer

Main class for composing skills from sections.

#### `__init__(db_store: Union[DatabaseStore, str])`

Initialize the composer with a database.

**Parameters:**
- `db_store`: DatabaseStore instance or path string

**Example:**
```python
composer = SkillComposer("~/.claude/databases/skill-split.db")
```

#### `compose_from_sections(section_ids, output_path, title="", description="")`

Compose a new skill from section IDs.

**Parameters:**
- `section_ids` (List[int]): Section IDs to include
- `output_path` (str): Output file path
- `title` (str, optional): Skill title
- `description` (str, optional): Skill description

**Returns:**
- `ComposedSkill`: Object representing the composed skill

**Raises:**
- `ValueError`: If section IDs are empty, not found, or path is invalid
- `TypeError`: If parameters are wrong type

**Example:**
```python
composed = composer.compose_from_sections(
    section_ids=[101, 205, 310],
    output_path="~/.claude/skills/custom.md",
    title="Custom Skill",
    description="Composed from sections"
)
```

#### `write_to_filesystem(composed: ComposedSkill) -> str`

Write composed skill to disk.

**Parameters:**
- `composed` (ComposedSkill): Composed skill object

**Returns:**
- `str`: SHA256 hash of the written file

**Raises:**
- `ValueError`: If output path is invalid
- `IOError`: If file writing fails

**Example:**
```python
hash_val = composer.write_to_filesystem(composed)
```

#### `upload_to_supabase(composed: ComposedSkill, supabase_store) -> str`

Upload composed skill to Supabase.

**Parameters:**
- `composed` (ComposedSkill): Composed skill object (must be written to filesystem first)
- `supabase_store`: SupabaseStore instance

**Returns:**
- `str`: File ID (UUID) in Supabase

**Raises:**
- `IOError`: If composed file not found
- `ValueError`: If file cannot be parsed or uploaded

**Example:**
```python
file_id = composer.upload_to_supabase(composed, supabase_store)
```

### ComposedSkill

Data class representing a composed skill.

**Attributes:**
- `section_ids` (List[int]): IDs of included sections
- `sections` (Dict[int, Section]): Section objects by ID
- `output_path` (str): Path where skill will be written
- `frontmatter` (str): YAML frontmatter
- `title` (str): Skill title
- `description` (str): Skill description
- `composed_hash` (str): SHA256 hash (set after writing)

**Methods:**
- `to_dict() -> dict`: Serialize to dictionary

**Example:**
```python
composed.to_dict()
# {
#     'section_ids': [101, 205],
#     'output_path': '~/.claude/skills/custom.md',
#     'title': 'Custom Skill',
#     'description': '...',
#     'frontmatter': 'name: custom-skill\n...',
#     'composed_hash': 'abc123...'
# }
```

---

## Advanced Usage

### Composing with Section Filtering

```python
from core.query import QueryAPI
from core.skill_composer import SkillComposer

query_api = QueryAPI(db_path)
composer = SkillComposer(db_path)

# Find sections matching criteria
results = query_api.search_sections("authentication")
section_ids = [sid for sid, section in results if section.level == 2]

# Compose filtered sections
composed = composer.compose_from_sections(
    section_ids=section_ids,
    output_path="~/skills/auth-headers.md",
    title="Auth Headers Only"
)

composer.write_to_filesystem(composed)
```

### Batch Composition

```python
# Compose multiple skills from different topic areas
topics = {
    'authentication': [101, 205, 310],
    'authorization': [315, 320, 325],
    'security': [330, 335, 340],
}

for topic, section_ids in topics.items():
    composed = composer.compose_from_sections(
        section_ids=section_ids,
        output_path=f"~/skills/{topic}.md",
        title=topic.title(),
        description=f"Skill about {topic}"
    )

    composer.write_to_filesystem(composed)
    print(f"Created ~/skills/{topic}.md")
```

### Composition with Metadata Enrichment

```python
from datetime import datetime

composed = composer.compose_from_sections(
    section_ids=[101, 205, 310],
    output_path="~/skills/custom.md",
    title="Custom Skill",
    description="Composed from multiple sources"
)

# Access the ComposedSkill object for further customization
print(f"Composed {len(composed.section_ids)} sections")
print(f"From file: {composed.sections[101].source_file}")
print(f"Output: {composed.output_path}")

# Write with hash tracking
hash_val = composer.write_to_filesystem(composed)
print(f"Hash: {hash_val}")
```

### Finding Optimal Sections to Compose

```python
from core.query import QueryAPI

query_api = QueryAPI(db_path)

# Find longest sections (more content)
sections = []
with DatabaseStore(db_path) as db:
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT id FROM sections
        WHERE LENGTH(content) > 100
        ORDER BY LENGTH(content) DESC
        LIMIT 10
    """)
    section_ids = [row[0] for row in cursor.fetchall()]

# Compose from most substantial sections
composed = composer.compose_from_sections(
    section_ids=section_ids,
    output_path="~/skills/substantial.md",
    title="Substantial Content"
)
```

---

## Best Practices

### 1. Search Before Composing

Always search and explore sections before composing to ensure you're selecting the right content.

```bash
# Preview sections
./skill_split.py search "topic" --db ~/.claude/databases/skill-split.db

# Look at structure
./skill_split.py list ~/skills/source.md --db ~/.claude/databases/skill-split.db
```

### 2. Use Meaningful Titles and Descriptions

Provide clear metadata for composed skills.

```python
composed = composer.compose_from_sections(
    section_ids=[101, 205, 310],
    output_path="~/skills/jwt-auth.md",
    title="JWT Authentication Patterns",
    description="Complete guide to implementing JWT authentication in modern web applications"
)
```

### 3. Validate Composition Result

Verify the composed skill is valid before uploading.

```bash
# Validate the written file
./skill_split.py validate ~/.claude/skills/custom.md

# Check structure
./skill_split.py list ~/.claude/skills/custom.md --db ~/.claude/databases/skill-split.db
```

### 4. Organize Output Directories

Group related composed skills in organized locations.

```bash
# Create topic-based directories
mkdir -p ~/.claude/skills/composed/authentication
mkdir -p ~/.claude/skills/composed/security
mkdir -p ~/.claude/skills/composed/performance

# Compose into organized locations
./skill_split.py compose \
  --sections 101,205,310 \
  --output ~/.claude/skills/composed/authentication/jwt.md
```

### 5. Track Composition Metadata

Keep notes about what sections were composed and why.

```python
# Store composition metadata
composition_log = {
    'timestamp': datetime.now().isoformat(),
    'sections': [101, 205, 310],
    'title': 'JWT Authentication',
    'source_files': ['auth.md', 'security.md'],
    'hash': hash_val
}

# Save metadata
import json
with open('~/.claude/compositions.json', 'a') as f:
    json.dump(composition_log, f)
    f.write('\n')
```

---

## Troubleshooting

### Section Not Found

**Error**: `ValueError: Section 999 not found in database`

**Solution**: Verify the section ID exists using search.
```bash
./skill_split.py search "keyword" --db ~/.claude/databases/skill-split.db
```

### Invalid Output Path

**Error**: `ValueError: output_path must be a valid file path`

**Solution**: Ensure output path is a valid file path with .md extension.
```python
# Bad
compose_from_sections(..., output_path="/invalid/.md")

# Good
compose_from_sections(..., output_path="~/.claude/skills/custom.md")
```

### Upload Fails

**Error**: `ValueError: Failed to upload to Supabase`

**Solution**: Verify environment variables and database connection.
```bash
# Check environment
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test database
./skill_split.py list ~/.claude/skills/test.md
```

### Empty Section List

**Error**: `ValueError: section_ids list cannot be empty`

**Solution**: Ensure you're providing at least one section ID.
```python
# Bad
compose_from_sections(section_ids=[])

# Good
compose_from_sections(section_ids=[101])
```

---

## Examples

### Example 1: Compose Auth Patterns

```python
from core.skill_composer import SkillComposer

composer = SkillComposer("~/.claude/databases/skill-split.db")

# Compose JWT auth sections
composed = composer.compose_from_sections(
    section_ids=[101, 102, 103, 201, 202],
    output_path="~/.claude/skills/jwt-auth.md",
    title="JWT Authentication Complete Guide",
    description="Comprehensive JWT implementation patterns for Python and JavaScript"
)

# Write and verify
hash_val = composer.write_to_filesystem(composed)
print(f"Created: {composed.output_path}")
print(f"Sections: {len(composed.section_ids)}")
print(f"Hash: {hash_val}")
```

### Example 2: Compose with Upload

```bash
# One-step composition and upload
./skill_split.py compose \
  --sections 301,302,303,304,305 \
  --output ~/.claude/skills/oauth2-flow.md \
  --title "OAuth 2.0 Authorization Flow" \
  --description "Step-by-step OAuth 2.0 implementation" \
  --upload
```

### Example 3: Batch Composition Script

```bash
#!/bin/bash
# Compose multiple skills from different topics

DB="~/.claude/databases/skill-split.db"

# Compose authentication skill
./skill_split.py compose \
  --sections 101,102,103 \
  --output ~/.claude/skills/topic-auth.md \
  --title "Authentication" \
  --upload

# Compose authorization skill
./skill_split.py compose \
  --sections 201,202,203 \
  --output ~/.claude/skills/topic-authz.md \
  --title "Authorization" \
  --upload

# Compose security skill
./skill_split.py compose \
  --sections 301,302,303 \
  --output ~/.claude/skills/topic-security.md \
  --title "Security Best Practices" \
  --upload

echo "Batch composition complete"
```

---

## See Also

- [QueryAPI Guide](./README.md#query-api) - How to search and query sections
- [SupabaseStore Guide](./README.md#supabase-storage) - Remote storage
- [CLI Commands](./README.md#cli-commands) - Full command reference
- [EXAMPLES.md](./EXAMPLES.md) - More usage examples

---

*Last Updated: 2026-02-05*
