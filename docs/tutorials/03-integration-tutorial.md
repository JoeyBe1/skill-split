# Integration Guide for skill-split - Video Tutorial Script

**Video Title**: Integrating skill-split: Python Package, CI/CD, and Custom Workflows
**Target Length**: ~20 minutes
**Target Audience**: Developers integrating skill-split into applications
**Difficulty Level**: Advanced

---

## Video Metadata

- **Total Duration**: 20:00
- **Prerequisites**: Completed "Getting Started" and "Advanced Search" tutorials
- **Recording Date**: [Fill in when recording]
- **Presenter**: [Your Name]

---

## Equipment & Setup Requirements

**For Recording:**
- Screen resolution: 1920x1080 (minimum)
- Python IDE (VS Code with Python extension recommended)
- Terminal with multiple tabs
- Browser for GitHub/GitLab interface

**Demo Environment:**
- Python 3.8+ virtual environment
- GitHub or GitLab account
- Sample project repository
- CI/CD pipeline configuration

---

## Script

### [0:00] - Intro & Overview

**Visual**: Title card showing integration layers

**Audio**:
> "Welcome to the final video in our skill-split series. We've covered getting started and advanced search techniques. Now, let's integrate skill-split into real applications and workflows."

**Visual**: Architecture diagram showing integration points
```
┌─────────────────────────────────────────────────────────┐
│                    Your Application                     │
├─────────────────────────────────────────────────────────┤
│  Python API  │  CLI Wrapper  │  CI/CD Pipeline          │
└───────┬───────┴───────┬───────┴────────────────────────┘
        │               │
        └───────────────┴────────────────┐
                                       │
                    ┌───────────────────┴──────────────┐
                    │       skill-split Library        │
                    ├──────────────────────────────────┤
                    │ Parser │ Database │ Search │ API │
                    └──────────────────────────────────┘
```

**Audio**:
> "In this video, we'll cover three integration approaches:
> 1. Using skill-split as a Python package in your applications
> 2. Setting up CI/CD pipelines for automated documentation processing
> 3. Building custom workflows with the Query API

By the end, you'll have skill-split working seamlessly in your development workflow."

---

### [1:30] - Python Package Integration

**Visual**: VS Code with Python project open

**Audio**:
> "Let's start with Python package integration. skill-split is designed to be used programmatically, not just through the CLI."

**Visual**: Create new Python file

**Audio**:
> "First, install skill-split in your Python environment:"

**Terminal Commands**:
```bash
pip install -e /path/to/skill-split
```

**Audio**:
> "The `-e` flag installs it in editable mode, so changes to the code are immediately available. For production, you can install from PyPI or your private package repository."

---

### [2:15] - Basic Python API Usage

**Visual**: Python file in editor

**Audio**:
> "Let's create a simple Python script that uses skill-split to parse and search documentation. I'll create a file called `search_docs.py`:"

**Python Code** (type in editor):
```python
#!/usr/bin/env python3
"""Search documentation using skill-split."""

from pathlib import Path
from core.parser import Parser
from core.detector import FormatDetector
from core.database import DatabaseStore
from core.query import QueryAPI

def main():
    # Initialize components
    db_path = Path.home() / ".claude" / "databases" / "skill-split.db"
    db = DatabaseStore(db_path)
    query_api = QueryAPI(db)

    # Search for sections
    results = query_api.search_sections("python handler")

    # Display results
    for section_id, score, title in results:
        print(f"[{score:.2f}] {title} (ID: {section_id})")

if __name__ == "__main__":
    main()
```

**Audio**:
> "This script demonstrates the core API: initialize the database, create a QueryAPI instance, and search for sections. Let's run it:"

**Terminal Commands**:
```bash
python search_docs.py
```

**Visual**: Output showing search results

**Audio**:
> "The results are returned as tuples we can process programmatically. This is the foundation for building custom applications on top of skill-split."

---

### [3:45] - Advanced Python API: Progressive Disclosure

**Visual**: Continue editing Python file

**Audio**:
> "Let's build a more sophisticated example that demonstrates progressive disclosure - showing structure first, then loading content on demand:"

**Python Code** (add to file):
```python
def progressive_disclosure_demo(file_path: str):
    """Demonstrate progressive disclosure workflow."""
    db = DatabaseStore()
    query_api = QueryAPI(db)

    # Step 1: Show file structure
    print(f"=== Structure of {file_path} ===")
    tree = query_api.get_section_tree(file_path)
    for section in tree:
        indent = "  " * (section['level'] - 1)
        print(f"{indent}- [{section['id']}] {section['title']}")

    # Step 2: Get specific section
    section_id = int(input("\nEnter section ID to load: "))
    section = query_api.get_section(section_id)

    print(f"\n=== {section['title']} ===")
    print(section['content'])

    # Step 3: Navigate to next section
    next_section = query_api.get_next_section(section_id, file_path)
    if next_section:
        print(f"\n=== Next: {next_section['title']} ===")
        print(next_section['content'])
```

**Audio**:
> "This function shows the tree structure first, lets the user choose a section, loads that section, and then offers navigation to the next section. This is progressive disclosure in action."

**Terminal Commands**:
```bash
python search_docs.py
# (interactive demo)
```

**Visual**: Interactive terminal session

**Audio**:
> "The user sees the structure first, makes an informed choice, and only loads the content they need. This workflow is perfect for chatbots, documentation browsers, or any interface where token efficiency matters."

---

### [5:30] - Building a REST API Wrapper

**Visual**: Create new Python file `api_server.py`

**Audio**:
> "Now let's build a simple REST API server using FastAPI that exposes skill-split functionality over HTTP:"

**Python Code**:
```python
#!/usr/bin/env python3
"""REST API server for skill-split."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from core.database import DatabaseStore
from core.query import QueryAPI

app = FastAPI(title="skill-split API")
db = DatabaseStore()
query_api = QueryAPI(db)

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SectionRequest(BaseModel):
    section_id: int

@app.get("/")
async def root():
    return {"message": "skill-split API", "version": "1.0.0"}

@app.post("/search")
async def search(request: SearchRequest):
    """Search sections by query."""
    try:
        results = query_api.search_sections(request.query)
        return {
            "query": request.query,
            "results": [
                {"id": r[0], "score": r[1], "title": r[2]}
                for r in results[:request.limit]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/section")
async def get_section(request: SectionRequest):
    """Get section by ID."""
    try:
        section = query_api.get_section(request.section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        return section
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tree/{file_path:path}")
async def get_tree(file_path: str):
    """Get section tree for a file."""
    try:
        tree = query_api.get_section_tree(file_path)
        return {"file": file_path, "sections": tree}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Audio**:
> "This FastAPI server exposes three endpoints: search, get section, and get tree. Let's start the server and test it:"

**Terminal Commands**:
```bash
python api_server.py
```

**Visual**: Server output showing startup

**Audio**:
> "Now let's test the API using curl:"

**Terminal Commands** (new terminal tab):
```bash
# Search for sections
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "python handler", "limit": 5}'

# Get a specific section
curl -X POST "http://localhost:8000/section" \
  -H "Content-Type: application/json" \
  -d '{"section_id": 42}'

# Get file tree
curl "http://localhost:8000/tree/~/.claude/skills/my-skill.md"
```

**Visual**: JSON responses from API

**Audio**:
> "The API returns JSON responses that can be consumed by any application - web frontends, mobile apps, or other services. This makes skill-split functionality accessible across your entire infrastructure."

---

### [8:00] - CI/CD Integration: GitHub Actions

**Visual**: Browser showing GitHub repository

**Audio**:
> "Let's set up automated documentation processing in a CI/CD pipeline. We'll use GitHub Actions to automatically parse and validate documentation on every push."

**Visual**: Create `.github/workflows/docs.yml`

**Audio**:
> "Create a workflow file in `.github/workflows/docs.yml`:"

**YAML Code**:
```yaml
name: Documentation Checks

on:
  push:
    branches: [main, develop]
    paths:
      - 'docs/**'
      - 'skills/**'
      - '*.md'
  pull_request:
    branches: [main]
    paths:
      - 'docs/**'
      - 'skills/**'
      - '*.md'

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install skill-split
        run: |
          git clone https://github.com/yourusername/skill-split.git
          cd skill-split
          pip install -r requirements.txt
          pip install -e .

      - name: Validate all markdown files
        run: |
          find docs skills -name "*.md" -exec skill-split validate {} \;

      - name: Verify round-trip integrity
        run: |
          for file in $(find docs skills -name "*.md"); do
            echo "Verifying $file..."
            skill-split verify "$file" || exit 1
          done

      - name: Store in database
        run: |
          mkdir -p ~/.claude/databases
          for file in $(find docs skills -name "*.md"); do
            skill-split store "$file" --db ~/docs.db
          done

      - name: Upload database artifact
        uses: actions/upload-artifact@v3
        with:
          name: documentation-db
          path: ~/docs.db
```

**Audio**:
> "This workflow runs on every push and pull request affecting documentation files. It validates all markdown files, verifies round-trip integrity, stores them in a database, and uploads the database as an artifact."

**Visual**: GitHub Actions UI showing workflow run

**Audio**:
> "The workflow provides immediate feedback if documentation is malformed. It also creates a searchable database artifact that can be downloaded and used for documentation search."

---

### [10:30] - CI/CD Integration: Automated Search Index

**Visual**: Continue editing workflow

**Audio**:
> "Let's extend the workflow to generate a search index and create a documentation search website:"

**YAML Code** (add to workflow):
```yaml
  build-search-index:
    needs: validate-docs
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Download database artifact
        uses: actions/download-artifact@v3
        with:
          name: documentation-db
          path: ~/

      - name: Generate search index
        run: |
          # Export sections as JSON for web search
          python scripts/export_search.py ~/docs.db > search-index.json

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs-site
```

**Audio**:
> "This additional job downloads the database artifact, exports a search index as JSON, and deploys a documentation search site to GitHub Pages. Users get instant search across all your documentation."

---

### [11:45] - GitLab CI Example

**Visual**: Browser showing GitLab repository

**Audio**:
> "For GitLab users, here's the equivalent `.gitlab-ci.yml` configuration:"

**YAML Code**:
```yaml
stages:
  - validate
  - build
  - deploy

validate-docs:
  stage: validate
  image: python:3.10
  script:
    - pip install skill-split
    - find docs -name "*.md" -exec skill-split validate {} \;
  only:
    changes:
      - docs/**/*
      - "*.md"

build-search-index:
  stage: build
  image: python:3.10
  script:
    - pip install skill-split
    - mkdir -p output
    - skill-split store docs/*.md --db output/docs.db
    - python scripts/export_search.py output/docs.db > search-index.json
  artifacts:
    paths:
      - output/
      - search-index.json

deploy-pages:
  stage: deploy
  image: alpine:latest
  script:
    - mv search-index.json public/
  artifacts:
    paths:
      - public
  only:
    - main
```

**Audio**:
> "GitLab's pipeline is similar but uses a different syntax. The key stages are validation, building the search index, and deploying to GitLab Pages."

---

### [12:30] - Custom Workflow: Documentation Chatbot

**Visual**: Create new Python file `chatbot.py`

**Audio**:
> "Let's build a practical application: a documentation chatbot that uses skill-split for efficient context management:"

**Python Code**:
```python
#!/usr/bin/env python3
"""Documentation chatbot with progressive disclosure."""

from core.database import DatabaseStore
from core.query import QueryAPI
from typing import List, Tuple

class DocChatbot:
    """Chatbot that answers questions using progressive disclosure."""

    def __init__(self, db_path: str = None):
        self.db = DatabaseStore(db_path)
        self.api = QueryAPI(self.db)
        self.context = []  # Track loaded sections

    def answer(self, question: str) -> str:
        """Answer a question using relevant documentation."""
        # Step 1: Search for relevant sections
        results = self.api.search_sections(question, limit=5)

        if not results:
            return "I couldn't find any relevant documentation."

        # Step 2: Load top sections progressively
        sections = []
        for section_id, score, title in results:
            section = self.api.get_section(section_id)
            sections.append(section)
            self.context.append(section_id)

        # Step 3: Generate answer from sections
        # (In production, send sections to LLM)
        answer = self._generate_answer(question, sections)
        return answer

    def _generate_answer(self, question: str, sections: List[dict]) -> str:
        """Generate answer from loaded sections."""
        # Simple template-based answer
        # In production: Use OpenAI API or similar
        relevant = "\n\n".join([
            f"From {s['title']}:\n{s['content'][:200]}..."
            for s in sections[:3]
        ])
        return f"""Based on the documentation, here's what I found:

{relevant}

Would you like me to expand on any of these sections?"""

    def expand(self, section_id: int) -> str:
        """Expand on a specific section."""
        section = self.api.get_section(section_id)
        if not section:
            return "Section not found."

        # Load related subsections
        subsections = self._get_subsections(section_id)
        content = f"{section['content']}\n\n"

        for sub in subsections:
            content += f"\n## {sub['title']}\n{sub['content']}\n"

        return content

    def _get_subsections(self, section_id: int) -> List[dict]:
        """Get child subsections."""
        # Navigate to first child repeatedly
        subsections = []
        current = self.api.get_next_section(section_id, "", child=True)
        while current:
            subsections.append(current)
            current = self.api.get_next_section(current['id'], "", child=True)
        return subsections

# Usage
if __name__ == "__main__":
    bot = DocChatbot()
    print("DocChatbot ready! Ask me about your documentation.")
    print("(Type 'quit' to exit)")

    while True:
        question = input("\nYour question: ")
        if question.lower() == 'quit':
            break

        answer = bot.answer(question)
        print(f"\nBot: {answer}")
```

**Audio**:
> "This chatbot demonstrates a real-world integration pattern. It searches for relevant sections, loads them progressively, and can expand on specific sections. The context tracking ensures we don't reload the same sections."

**Terminal Commands**:
```bash
python chatbot.py
# (interactive demo)
```

**Visual**: Interactive chatbot session

**Audio**:
> "The chatbot shows how skill-split enables efficient documentation interaction. Instead of feeding entire documents to an LLM, we provide only relevant sections, dramatically reducing token usage and improving response quality."

---

### [15:00] - Custom Workflow: Backup & Restore Automation

**Visual**: Create backup script

**Audio**:
> "Let's create an automated backup workflow that protects your documentation database:"

**Bash Script** (`backup_docs.sh`):
```bash
#!/bin/bash
"""Automated backup workflow for skill-split databases."""

set -e

# Configuration
DB_PATH="${SKILL_SPLIT_DB:-~/.claude/databases/skill-split.db}"
BACKUP_DIR="${BACKUP_DIR:-~/.claude/backups}"
RETENTION_DAYS=30

# Create backup with timestamp
BACKUP_NAME="docs-backup-$(date +%Y%m%d-%H%M%S)"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME.sql.gz"

echo "Creating backup: $BACKUP_NAME"

# Backup using skill-split
skill-split backup --output "$BACKUP_NAME" --db "$DB_PATH"

# Verify backup was created
if [ ! -f "$BACKUP_PATH" ]; then
    echo "Error: Backup failed!"
    exit 1
fi

echo "Backup created successfully: $BACKUP_PATH"
echo "Size: $(du -h "$BACKUP_PATH" | cut -f1)"

# Clean up old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "docs-backup-*.sql.gz" -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/docs-backup-*.sql.gz 2>/dev/null || echo "No backups found"

echo "Backup complete!"
```

**Audio**:
> "This script creates timestamped backups, verifies they were created successfully, and cleans up old backups beyond the retention period. Let's set it up as a cron job:"

**Terminal Commands**:
```bash
# Make script executable
chmod +x backup_docs.sh

# Add to crontab (runs daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /path/to/backup_docs.sh >> ~/backup.log 2>&1
```

**Audio**:
> "Now your documentation database is automatically backed up daily, with automatic cleanup of old backups. Set it and forget it."

---

### [16:30] - Custom Workflow: Multi-Database Search

**Visual**: Create federated search script

**Audio**:
> "For advanced use cases, you might want to search across multiple skill-split databases. Here's a federated search implementation:"

**Python Code** (`federated_search.py`):
```python
#!/usr/bin/env python3
"""Federated search across multiple skill-split databases."""

from pathlib import Path
from core.database import DatabaseStore
from core.query import QueryAPI
from typing import List, Dict, Any
import heapq

class FederatedSearch:
    """Search across multiple databases and merge results."""

    def __init__(self, db_paths: List[str]):
        self.databases = []
        for path in db_paths:
            db = DatabaseStore(path)
            api = QueryAPI(db)
            self.databases.append({
                'path': path,
                'db': db,
                'api': api
            })

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search across all databases and merge results."""
        all_results = []

        for db_info in self.databases:
            results = db_info['api'].search_sections(query)
            for section_id, score, title in results:
                all_results.append({
                    'database': db_info['path'],
                    'section_id': section_id,
                    'score': score,
                    'title': title
                })

        # Sort by score (descending) and limit
        all_results.sort(key=lambda x: x['score'], reverse=True)
        return all_results[:limit]

    def get_section(self, database: str, section_id: int) -> dict:
        """Get section from specific database."""
        for db_info in self.databases:
            if db_info['path'] == database:
                return db_info['api'].get_section(section_id)
        return None

# Usage
if __name__ == "__main__":
    # Search across multiple documentation sets
    databases = [
        '~/.claude/databases/skill-split.db',
        '~/company/docs.db',
        '~/project/internal.db'
    ]

    searcher = FederatedSearch(databases)
    results = searcher.search("authentication", limit=10)

    print(f"Found {len(results)} results across {len(databases)} databases:")
    for r in results:
        db_name = Path(r['database']).stem
        print(f"[{r['score']:.2f}] {r['title']} (from {db_name})")
```

**Audio**:
> "Federated search lets you maintain separate databases for different projects or teams while providing unified search across all of them. Results are merged and ranked by relevance, so users get the best matches regardless of which database they're in."

---

### [17:45] - Performance Optimization Tips

**Visual**: Performance checklist

**Audio**:
> "When integrating skill-split into production applications, keep these optimization tips in mind:"

**Screen Text** (optimization tips):
```
Performance Optimization:

1. Connection Pooling
   - Reuse DatabaseStore instances
   - Avoid creating new connections per request

2. Caching
   - Cache section trees and metadata
   - Invalidate on file changes

3. Lazy Loading
   - Load content only when needed
   - Use progressive disclosure

4. Batch Operations
   - Store multiple files in one transaction
   - Batch embedding generation

5. Index Maintenance
   - Rebuild FTS5 index periodically
   - Update embeddings on content changes

6. Async Operations
   - Use async/await for I/O operations
   - Parallelize independent searches
```

**Audio**:
> "For high-traffic applications, consider implementing connection pooling, caching frequently accessed sections, and using async operations. The progressive disclosure pattern itself is a performance optimization - load only what you need, when you need it."

---

### [18:30] - Security Considerations

**Visual**: Security checklist

**Audio**:
> "When integrating skill-split, especially in web applications, consider these security aspects:"

**Screen Text** (security tips):
```
Security Best Practices:

1. Input Validation
   - Validate section IDs (prevent injection)
   - Sanitize file paths (prevent directory traversal)

2. Access Control
   - Implement authentication for API endpoints
   - Restrict database file permissions (600)
   - Use environment variables for secrets

3. API Keys
   - Never commit API keys to git
   - Use SecretManager for production
   - Rotate keys periodically

4. Database Security
   - Encrypt sensitive data before storing
   - Use separate databases per tenant
   - Implement row-level security

5. Rate Limiting
   - Limit search requests per user
   - Implement backoff for excessive queries
```

**Audio**:
> "Always validate user input, implement proper authentication, and never commit secrets to version control. The skill-split database may contain sensitive documentation, so secure it appropriately."

---

### [19:15] - Summary & Next Steps

**Visual**: Integration checklist

**Audio**:
> "Let's recap what we've covered in this integration tutorial:"

**Screen Text** (recap):
```
Integration Patterns Covered:

✓ Python Package API
  - Parser, Database, QueryAPI classes
  - Programmatic search and retrieval

✓ REST API Server
  - FastAPI wrapper
  - JSON endpoints for web apps

✓ CI/CD Pipelines
  - GitHub Actions validation
  - GitLab CI deployment
  - Automated documentation checks

✓ Custom Workflows
  - Documentation chatbot
  - Automated backup/restore
  - Federated multi-database search

✓ Production Considerations
  - Performance optimization
  - Security best practices
```

**Audio**:
> "You now have everything you need to integrate skill-split into your development workflow. From simple Python scripts to complex CI/CD pipelines, skill-split provides the building blocks for efficient documentation management."

**Visual**: End card with resources

**Audio**:
> "For more information, check out the resources below. Thanks for watching this complete skill-split tutorial series. Happy splitting!"

**Screen Text**:
```
Resources:
- GitHub: https://github.com/yourusername/skill-split
- CLI Reference: docs/CLI_REFERENCE.md
- Examples: EXAMPLES.md
- Architecture: README.md#architecture

Complete Tutorial Series:
1. Getting Started ✓
2. Advanced Search ✓
3. Integration ✓
```

---

## Post-Production Notes

**Visual Elements to Add:**
- [ ] Code syntax highlighting with proper colors
- [ ] API endpoint diagrams for REST section
- [ ] CI/CD pipeline flow animations
- [ ] Performance metrics overlays
- [ ] Security checklist graphics

**Audio Enhancements:**
- [ ] Keyboard typing sounds for code sections
- [ ] Distinct audio cues for different integration types
- [ ] Emphasis on security warnings
- [ ] Background music during code demonstrations

**Editing Checklist:**
- [ ] Synchronize code typing with narration
- [ ] Add zoom highlights for key code sections
- [ ] Create chapter markers for each integration pattern
- [ ] Include pause points for viewer comprehension
- [ ] Add closed captions for technical content

---

## Demo Code Preparation

Before recording, create these files:

**1. REST API Server** (`api_server.py`):
```python
# Complete code from script above
```

**2. GitHub Actions Workflow** (`.github/workflows/docs.yml`):
```yaml
# Complete workflow from script above
```

**3. Chatbot Example** (`chatbot.py`):
```bash
# Create sample data first
cat > /tmp/sample_docs.md << 'EOF'
---
name: api-documentation
description: Sample API docs for chatbot
version: 1.0.0
---

# Authentication

## API Keys

Generate API keys in the dashboard.

## OAuth Flow

Implement OAuth2 for third-party access.

# Endpoints

## GET /users

List all users with pagination.

## POST /users

Create a new user account.
EOF

# Store for demo
./skill_split.py store /tmp/sample_docs.md
```

---

## CI/CD Pipeline Testing

Before recording, test the CI/CD workflows:

```bash
# Test validation workflow
find . -name "*.md" -exec ./skill_split.py validate {} \;

# Test backup workflow
./skill_split.py backup --output test-backup

# Test restore workflow
./skill_split.py restore test-backup --db test-restore.db --overwrite
```

---

## Recording Tips

1. **Code Pacing**: Type code at a natural pace, don't rush
2. **Error Handling**: Show common errors and fixes
3. **API Testing**: Have curl commands ready in a separate terminal
4. **CI/CD Demo**: Use a test repository, not your main one
5. **Multiple Tabs**: Use multiple terminal tabs for different services
6. **Visual Cues**: Use color highlighting for key code sections

---

## Troubleshooting Common Issues

**Import Errors**:
```bash
# Ensure skill-split is in Python path
export PYTHONPATH="/path/to/skill-split:$PYTHONPATH"
```

**Database Lock Errors**:
```bash
# Close all connections before backup
./skill_split.py status
```

**CI/CD Failures**:
```bash
# Test workflow locally
act -j validate-docs  # (uses act for local GitHub Actions)
```

---

## Related Videos in Series

1. **Getting Started** - Installation and basic usage
2. **Advanced Search** - BM25, Vector, and Hybrid search
3. **Integration** (this video) - Python package and CI/CD

---

## Additional Resources

**Documentation**:
- [CLI Reference](./CLI_REFERENCE.md)
- [Examples](../EXAMPLES.md)
- [Component Handlers](../COMPONENT_HANDLERS.md)

**Community**:
- GitHub Issues
- Discussion Forum
- Discord Server (if available)

**Contributing**:
- Pull Request Guidelines
- Code of Conduct
- Development Setup

---

*Last Updated: 2026-02-10*
*Script Version: 1.0*
