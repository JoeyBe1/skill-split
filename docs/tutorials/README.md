# skill-split Video Tutorial Scripts

This directory contains comprehensive video tutorial scripts for the skill-split project. Each script is designed to guide viewers through specific aspects of skill-split, from basic setup to advanced integration.

---

## Tutorial Series Overview

### 1. Getting Started Tutorial (~10 minutes)

**File**: `01-getting-started-tutorial.md`

**Target Audience**: Beginners new to skill-split

**Topics Covered**:
- What is progressive disclosure and why it matters
- Installation and setup
- First parse and validation
- Storing files in the database
- Exploring section structure (list, tree)
- Retrieving sections individually
- Basic navigation and search
- Real-world use case demo
- Token savings demonstration (99% context reduction)

**Prerequisites**: None

**Key Takeaways**:
- Understand the progressive disclosure workflow
- Basic CLI commands (parse, validate, store, list, tree)
- Section retrieval for token efficiency
- Introduction to BM25 search

---

### 2. Advanced Search Tutorial (~15 minutes)

**File**: `02-advanced-search-tutorial.md`

**Target Audience**: Developers comfortable with basic skill-split usage

**Topics Covered**:
- BM25 keyword search fundamentals
- FTS5 query syntax (AND, OR, NEAR, phrases)
- BM25 performance characteristics
- When to use BM25 search
- Vector search for semantic understanding
- Setting up OpenAI and Supabase for embeddings
- Vector search commands and examples
- Performance and cost analysis ($0.08 one-time, $0.03-0.05/month)
- When to use vector search
- Hybrid search combining both approaches
- Tuning vector weight (0.0-1.0 scale)
- Real-world performance comparison
- Search tips and best practices

**Prerequisites**: Completed Getting Started tutorial

**Key Takeaways**:
- All three search modes: BM25, Vector, Hybrid
- When to use each search type
- Cost-performance tradeoffs
- Query syntax optimization

---

### 3. Integration Tutorial (~20 minutes)

**File**: `03-integration-tutorial.md`

**Target Audience**: Developers integrating skill-split into applications

**Topics Covered**:
- Python package API usage
- Building a REST API server with FastAPI
- CI/CD integration with GitHub Actions
- CI/CD integration with GitLab CI
- Documentation chatbot example
- Automated backup and restore workflows
- Federated multi-database search
- Performance optimization tips
- Security best practices
- Production deployment considerations

**Prerequisites**: Completed Getting Started and Advanced Search tutorials

**Key Takeaways**:
- Programmatic API usage
- CI/CD pipeline automation
- Building custom applications on skill-split
- Production deployment guidance

---

## How to Use These Scripts

### For Video Creators

Each script includes:
- **Timestamps** for section breaks
- **Screen recording instructions** with specific resolutions and setups
- **Code examples** ready to type or copy
- **Visual cues** for on-screen graphics
- **Audio cues** for emphasis and transitions
- **Post-production notes** with editing checklist
- **Demo preparation** with sample data

**Equipment Needed**:
- Screen resolution: 1920x1080 minimum
- Terminal application (iTerm2, Terminal.app, or Windows Terminal)
- Python IDE (VS Code recommended)
- Clear microphone
- Optional: Browser for GitHub/GitLab demo

**Recording Tips**:
1. Read through the entire script before recording
2. Set up all demo files and databases beforehand
3. Use terminal with visible command history
4. Font size: Terminal 14-16pt, Editor 12-14pt
5. High contrast color scheme (dark background, light text)
6. Pause 2-3 seconds after commands for viewer comprehension

### For Learners

Even if you're not creating videos, these scripts serve as:
- **Comprehensive written tutorials** with step-by-step instructions
- **Code examples** you can copy and run
- **Workflow patterns** for common use cases
- **Best practices** for production deployment

---

## Quick Reference: Command Examples

### Getting Started Commands

```bash
# Parse a file
./skill_split.py parse myfile.md

# Validate structure
./skill_split.py validate myfile.md

# Store in database
./skill_split.py store myfile.md

# List sections
./skill_split.py list myfile.md

# Show tree structure
./skill_split.py tree myfile.md

# Get specific section
./skill_split.py get-section 42

# Navigate to next section
./skill_split.py next 42 myfile.md
```

### Search Commands

```bash
# BM25 keyword search
./skill_split.py search "python handler"

# Exact phrase search
./skill_split.py search '"python handler"'

# AND search
./skill_split.py search "python AND testing"

# Vector/semantic search
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 1.0

# Hybrid search (recommended)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "python error handling" --vector-weight 0.7
```

### Integration Commands

```bash
# Python API
python -c "from core.query import QueryAPI; from core.database import DatabaseStore; api = QueryAPI(DatabaseStore()); print(api.search_sections('test'))"

# Backup
./skill_split.py backup --output my-backup

# Restore
./skill_split.py restore my-backup --db skill-split.db --overwrite

# Check status
./skill_split.py status
```

---

## Environment Variables

```bash
# Database location
export SKILL_SPLIT_DB=~/.claude/databases/skill-split.db

# Enable embeddings for vector search
export ENABLE_EMBEDDINGS=true

# OpenAI API key for embeddings
export OPENAI_API_KEY=sk-your-key-here

# Supabase credentials
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_PUBLISHABLE_KEY=your-anon-key
```

---

## Related Documentation

- [README.md](../../README.md) - Main project documentation
- [CLI_REFERENCE.md](../CLI_REFERENCE.md) - Complete command reference
- [EXAMPLES.md](../../EXAMPLES.md) - Real-world usage examples
- [VECTOR_SEARCH_COSTS.md](../VECTOR_SEARCH_COSTS.md) - Cost analysis for vector search

---

## Tutorial Status

| Tutorial | Script Status | Video Status |
|----------|--------------|--------------|
| Getting Started | Complete | Not recorded |
| Advanced Search | Complete | Not recorded |
| Integration | Complete | Not recorded |

---

## Contributing

Want to contribute tutorials?

1. Create a new markdown file in this directory
2. Follow the existing script format with timestamps and sections
3. Include demo commands and visual cues
4. Update this README with the new tutorial
5. Submit a pull request

**Tutorial Template**:
```markdown
# Tutorial Title - Video Script

**Video Title**: [Title]
**Target Length**: [Duration]
**Target Audience**: [Who is this for?]
**Difficulty Level**: [Beginner/Intermediate/Advanced]

## Script

### [0:00] - Intro
...

### [1:00] - First Section
...

## Post-Production Notes
...
```

---

## Feedback

If you use these scripts to create videos or learn skill-split, we'd love to hear from you:

- **YouTube**: Leave a comment on the videos
- **GitHub**: Open an issue or discussion
- **Twitter**: Mention us with #skillsplit

---

*Last Updated: 2026-02-10*
*Tutorial Series Version: 1.0*
