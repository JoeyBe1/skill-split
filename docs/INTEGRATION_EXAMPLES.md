# skill-split Integration Examples

**Real-world integration patterns and examples**

---

## Python Application Integration

### Pattern 1: Chatbot Context

```python
from skill_split import SkillSplit
from core.database import Database
from core.query import QueryAPI

class Chatbot:
    def __init__(self):
        self.ss = SkillSplit()
        self.db = Database()
        self.query = QueryAPI(self.db)

    def get_context(self, question: str) -> str:
        """Get minimal context for question."""
        # Search first (0 tokens)
        results = self.query.search_sections(question, limit=3)

        # Load only relevant sections
        sections = [self.query.get_section(r.section.id) for r in results]

        # Return as context
        return "\n\n".join(s.content for s in sections)

    def ask(self, question: str) -> str:
        """Answer question with minimal context."""
        context = self.get_context(question)

        # Token cost: ~150 (vs 5,000 for full docs)
        response = llm.ask(question, context=context)
        return response

# Usage
bot = Chatbot()
answer = bot.ask("How do I authenticate?")
```

### Pattern 2: Code Assistant

```python
from skill_split import SkillSplit
from core.query import QueryAPI

class CodeAssistant:
    def __init__(self):
        self.query = QueryAPI(Database())

    def find_examples(self, task: str, language: str) -> list:
        """Find code examples for a task."""
        query = f"{task} {language}"
        results = self.query.search_sections(query, limit=5)

        # Load examples (only what we need)
        examples = []
        for r in results:
            section = self.query.get_section(r.section.id)
            if "```" in section.content:  # Contains code block
                examples.append(section)

        return examples

    def generate_code(self, task: str, language: str) -> str:
        """Generate code based on examples."""
        examples = self.find_examples(task, language)

        # Token cost: ~300 (vs 15,000 for full codebase)
        code = llm.code_generate(task, examples, language)
        return code

# Usage
assistant = CodeAssistant()
code = assistant.generate_code("authentication", "python")
```

### Pattern 3: Documentation Search API

```python
from fastapi import FastAPI, HTTPException
from core.query import QueryAPI

app = FastAPI()
query = QueryAPI(Database())

@app.get("/api/search")
async def search(q: str, mode: str = "hybrid", limit: int = 10):
    """Search documentation API."""
    if mode == "bm25":
        results = query.search_sections(q, limit=limit)
    elif mode == "vector":
        results = query.hybrid_search(q, vector_weight=1.0, limit=limit)
    else:  # hybrid
        results = query.hybrid_search(q, vector_weight=0.7, limit=limit)

    return {
        "query": q,
        "mode": mode,
        "results": [
            {
                "id": r.section.id,
                "heading": r.section.heading,
                "score": r.score,
                "preview": r.section.content[:100]
            }
            for r in results
        ]
    }

@app.get("/api/sections/{section_id}")
async def get_section(section_id: int):
    """Get section by ID API."""
    try:
        section = query.get_section(section_id)
        return {
            "id": section.id,
            "heading": section.heading,
            "level": section.level,
            "content": section.content
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## CI/CD Integration

### GitHub Actions: Documentation Validation

```yaml
name: Validate Documentation

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install skill-split
        run: pip install skill-split

      - name: Parse all docs
        run: |
          for file in docs/**/*.md; do
            skill-split validate "$file"
          done

      - name: Check round-trip integrity
        run: |
          for file in docs/**/*.md; do
            skill-split parse "$file" | tee /tmp/parsed.txt
            # Verify can be reconstructed
            if ! grep -q "Parse successful" /tmp/parsed.txt; then
              echo "Failed to parse $file"
              exit 1
            fi
          done
```

### Pre-commit Hook: Documentation Check

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if markdown files changed
CHANGED_MD=$(git diff --cached --name-only | grep "\.md$" || true)

if [ -n "$CHANGED_MD" ]; then
    echo "Validating documentation..."

    for file in $CHANGED_MD; do
        # Validate structure
        if ! skill-split validate "$file" 2>/dev/null; then
            echo "❌ $file has validation errors"
            exit 1
        fi
    done

    echo "✅ All documentation valid"
fi
```

---

## AI/ML Pipeline Integration

### LangChain Integration

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from core.query import QueryAPI

class SkillSplitTool(BaseTool):
    """skill-split search tool for LangChain."""
    name = "skill_split_search"
    description = "Search documentation using skill-split"

    query_api: QueryAPI = Field(default_factory=lambda: QueryAPI(Database()))

    def _run(self, query: str) -> str:
        """Search and return results."""
        results = self.query_api.search_sections(query, limit=3)

        output = []
        for r in results:
            section = self.query_api.get_section(r.section.id)
            output.append(f"## {section.heading}\n{section.content[:200]}...")

        return "\n\n".join(output)

# Usage in LangChain
from langchain.agents import initialize_agent, Tool

tools = [
    SkillSplitTool()
]
agent = initialize_agent(tools, llm)
result = agent.run("How do I set up OAuth?")
```

### LlamaIndex Integration

```python
from llama_index import Document, SimpleDirectoryReader
from skill_split import SkillSplit
from core.query import QueryAPI

class SkillSplitReader:
    """skill-split reader for LlamaIndex."""

    def __init__(self):
        self.query = QueryAPI(Database())

    def load_data(self, query: str) -> list[Document]:
        """Load relevant documents for query."""
        results = self.query.search_sections(query, limit=5)

        documents = []
        for r in results:
            section = self.query.get_section(r.section.id)
            doc = Document(
                text=section.content,
                metadata={
                    "id": section.id,
                    "heading": section.heading,
                    "file": section.file_path
                }
            )
            documents.append(doc)

        return documents

# Usage
reader = SkillSplitReader()
documents = reader.load_data("authentication")
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("How do I authenticate?")
```

---

## VS Code Extension Integration

### Extension Command: Search Documentation

```typescript
import * as vscode from 'vscode';
import { execSync } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    const searchCommand = vscode.commands.registerCommand(
        'skill-split.search',
        async () => {
            // Get search query from user
            const query = await vscode.window.showInputBox({
                prompt: 'Search documentation',
                placeHolder: 'Enter search query'
            });

            if (!query) return;

            // Execute skill-split search
            const output = execSync(
                `skill-split search "${query}"`,
                { encoding: 'utf-8' }
            );

            // Parse results
            const results = parseResults(output);

            // Show quick pick
            const selected = await vscode.window.showQuickPick(
                results.map(r => ({
                    label: r.heading,
                    detail: r.preview,
                    id: r.id
                }))
            );

            if (selected) {
                // Get section content
                const section = execSync(
                    `skill-split get-section ${selected.id}`,
                    { encoding: 'utf-8' }
                );

                // Show in new document
                const doc = await vscode.workspace.openTextDocument({
                    content: section,
                    language: 'markdown'
                });
                await vscode.window.showTextDocument(doc);
            }
        }
    );

    context.subscriptions.push(searchCommand);
}

function parseResults(output: string): SearchResult[] {
    // Parse skill-split output format
    const lines = output.split('\n');
    const results: SearchResult[] = [];

    for (const line of lines) {
        const match = line.match(/\[(\d+)\]\s+\(([\d.]+)\)\s+(.+)/);
        if (match) {
            results.push({
                id: parseInt(match[1]),
                score: parseFloat(match[2]),
                heading: match[3],
                preview: extractPreview(match[3])
            });
        }
    }

    return results;
}
```

---

## Docker Integration

### Docker Compose: Documentation Service

```yaml
version: '3.8'

services:
  skill-split-api:
    build: .
    container_name: skill-split-api
    volumes:
      - ./docs:/docs:ro
      - skill-split-db:/data
    environment:
      - SKILL_SPLIT_DB=/data/skill-split.db
      - ENABLE_EMBEDDINGS=true
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8080:8080"
    command: python -m uvicorn api:app --host 0.0.0.0 --port 8080

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - skill-split-api

volumes:
  skill-split-db:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skill-split
spec:
  replicas: 3
  selector:
    matchLabels:
      app: skill-split
  template:
    metadata:
      labels:
        app: skill-split
    spec:
      containers:
      - name: skill-split
        image: skill-split:latest
        ports:
        - containerPort: 8080
        env:
        - name: SKILL_SPLIT_DB
          value: /data/skill-split.db
        - name: ENABLE_EMBEDDINGS
          value: "true"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: skill-split-data
---
apiVersion: v1
kind: Service
metadata:
  name: skill-split
spec:
  selector:
    app: skill-split
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

---

## Monitoring Integration

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge
from skill_split import SkillSplit

# Metrics
search_counter = Counter('skill_split_search_total', 'Total searches')
search_duration = Histogram('skill_split_search_duration_seconds', 'Search duration')
db_size = Gauge('skill_split_db_size_sections', 'Database size in sections')

class MonitoredSkillSplit(SkillSplit):
    """skill-split with Prometheus monitoring."""

    def __init__(self):
        super().__init__()
        self.query = QueryAPI(Database())

    def search_monitored(self, query: str):
        """Search with monitoring."""
        search_counter.inc()

        with search_duration.time():
            results = self.query.search_sections(query)

        db_size.set(len(self.query.list_sections()))

        return results

# Usage
app = MonitoredSkillSplit()
results = app.search_monitored("authentication")
```

---

## Web Framework Examples

### Flask Integration

```python
from flask import Flask, request, jsonify
from skill_split import SkillSplit
from core.query import QueryAPI

app = Flask(__name__)
query = QueryAPI(Database())

@app.route('/api/search')
def search_api():
    q = request.args.get('q', '')
    mode = request.args.get('mode', 'hybrid')
    limit = int(request.args.get('limit', 10))

    if mode == 'bm25':
        results = query.search_sections(q, limit=limit)
    elif mode == 'vector':
        results = query.hybrid_search(q, vector_weight=1.0, limit=limit)
    else:
        results = query.hybrid_search(q, vector_weight=0.7, limit=limit)

    return jsonify({
        'query': q,
        'results': [
            {'id': r.section.id, 'heading': r.section.heading, 'score': r.score}
            for r in results
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
```

### Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core.query import QueryAPI

query = QueryAPI(Database())

@require_http_methods(["GET"])
def search_view(request):
    q = request.GET.get('q', '')
    results = query.search_sections(q, limit=10)

    return JsonResponse({
        'results': [
            {
                'id': r.section.id,
                'heading': r.section.heading,
                'content': r.section.content[:200]
            }
            for r in results
        ]
    })

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/search/', views.search_view),
]
```

---

## Summary

**Integration patterns covered:**
- Python applications (chatbots, code assistants)
- CI/CD pipelines (GitHub Actions, pre-commit)
- AI/ML frameworks (LangChain, LlamaIndex)
- VS Code extensions
- Docker/Kubernetes deployment
- Monitoring (Prometheus)
- Web frameworks (Flask, Django)

**Key benefits:**
- Minimal code changes
- Token-efficient by default
- Production-ready examples
- Multiple language support

---

*skill-split - Progressive disclosure for AI workflows*
