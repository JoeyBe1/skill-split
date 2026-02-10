# Auto-Tagger Plugin

Automatically analyzes section content and suggests relevant tags/keywords for skill-split documents.

## Features

- **Content Analysis**: Analyzes text using NLP techniques
- **Tag Suggestions**: Suggests relevant tags based on content
- **Keyword Extraction**: Extracts important keywords and phrases
- **Frontmatter Updates**: Automatically updates document frontmatter
- **Tag Consistency**: Maintains consistent tagging across documents

## Installation

```bash
# Copy to your skill-split plugins directory
cp -r examples/plugins/auto_tagger ~/.claude/plugins/
```

## Usage

```bash
# Suggest tags for a file
./skill_split.py plugin auto_tagger suggest <file>

# Update frontmatter with suggested tags
./skill_split.py plugin auto_tagger update <file>

# Show tag statistics
./skill_split.py plugin auto_tagger stats

# Find similar documents by tags
./skill_split.py plugin auto_tagger similar <file> --limit 5
```

## API

### suggest_tags(file_path: str, count: int = 10) -> List[str]

Suggests tags for a document based on content analysis.

### update_frontmatter(file_path: str, tags: List[str]) -> bool

Updates the document's frontmatter with the provided tags.

### extract_keywords(text: str, count: int = 5) -> List[str]

Extracts important keywords from text.

## Tag Categories

- **Technology**: Programming languages, frameworks, tools
- **Concept**: Algorithms, patterns, methodologies
- **Domain**: Application areas, use cases
- **Difficulty**: Beginner, intermediate, advanced
- **Type**: Tutorial, reference, example

## Requirements

- skill-split >= 1.0
- Python >= 3.9

## License

MIT
