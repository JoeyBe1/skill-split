#!/usr/bin/env python3
"""
Web Integration Example

Demonstrates using skill-split with a web framework (Flask).
Shows how to build a simple documentation search API.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# This is a demonstration - Flask not required for skill-split
# pip install flask to run this example

# Example API structure (pseudo-code for reference)
API_STRUCTURE = """
from flask import Flask, request, jsonify
from skill_split import SkillSplit
from core.database import Database
from core.query import QueryAPI

app = Flask(__name__)
ss = SkillSplit()
db = Database()
query = QueryAPI(db)

@app.route('/api/search')
def search():
    '''Search documentation with multiple modes.'''
    q = request.args.get('q', '')
    mode = request.args.get('mode', 'bm25')  # bm25, vector, hybrid
    limit = int(request.args.get('limit', 10))

    if mode == 'bm25':
        results = query.search_sections(q, limit=limit)
    elif mode == 'vector':
        results = query.hybrid_search(q, vector_weight=1.0, limit=limit)
    else:  # hybrid
        results = query.hybrid_search(q, vector_weight=0.7, limit=limit)

    return jsonify({
        'query': q,
        'mode': mode,
        'results': [
            {
                'id': r.section.id,
                'heading': r.section.heading,
                'score': r.score,
                'content': r.section.content[:200] + '...'
            }
            for r in results
        ]
    })

@app.route('/api/sections/<int:section_id>')
def get_section(section_id):
    '''Get a specific section by ID.'''
    section = query.get_section(section_id)
    return jsonify({
        'id': section.id,
        'heading': section.heading,
        'content': section.content,
        'level': section.level,
        'file_path': section.file_path
    })

@app.route('/api/files/<path:filename>')
def list_file(filename):
    '''List all sections in a file.'''
    sections = query.list_sections(filename)
    return jsonify({
        'file': filename,
        'sections': [
            {
                'id': s.id,
                'heading': s.heading,
                'level': s.level
            }
            for s in sections
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
"""

# REST API Response Examples
RESPONSE_EXAMPLES = """
# Search API Response
GET /api/search?q=authentication&mode=hybrid&limit=5

{
  "query": "authentication",
  "mode": "hybrid",
  "results": [
    {
      "id": 42,
      "heading": "Authentication",
      "score": 0.95,
      "content": "# Authentication\n\nTo authenticate..."
    },
    {
      "id": 127,
      "heading": "OAuth Setup",
      "score": 0.87,
      "content": "## OAuth Setup\n\nConfigure OAuth..."
    }
  ]
}

# Section API Response
GET /api/sections/42

{
  "id": 42,
  "heading": "Authentication",
  "content": "# Authentication\n\nTo authenticate...",
  "level": 1,
  "file_path": "docs/api.md"
}

# File Tree API Response
GET /api/files/README.md

{
  "file": "README.md",
  "sections": [
    {"id": 1, "heading": "Introduction", "level": 1},
    {"id": 5, "heading": "Installation", "level": 1},
    {"id": 12, "heading": "Quick Start", "level": 2}
  ]
}
"""

# Integration patterns
INTEGRATION_PATTERNS = """
## Integration Patterns

### 1. FastAPI (Recommended for Production)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="skill-split API")

class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid"
    limit: int = 10

@app.post("/api/search")
async def search(req: SearchRequest):
    results = query.hybrid_search(
        req.query,
        vector_weight=0.7 if req.mode == "hybrid" else 1.0,
        limit=req.limit
    )
    return {"results": results}

### 2. Django Integration

# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def search_view(request):
    q = request.GET.get('q', '')
    results = query.search_sections(q)
    return JsonResponse({'results': results})

### 3. Serverless Functions (AWS Lambda)

import json

def lambda_handler(event, context):
    query_str = event.get('queryStringParameters', {}).get('q', '')
    results = query.search_sections(query_str)

    return {
        'statusCode': 200,
        'body': json.dumps([r.section.heading for r in results])
    }

### 4. Background Worker (Celery)

from celery import Celery

app = Celery('tasks')

@app.task
def index_document(file_path: str):
    ss = SkillSplit()
    doc = ss.parse_file(file_path)
    db.store_document(doc)
    return f"Indexed {len(doc.sections)} sections"
"""


def print_example(title: str, content: str):
    """Print a formatted example."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)
    print(content)


def main():
    """Display web integration examples."""
    print_section("skill-split Web Integration Examples")

    print_section("Flask API Example")
    print(API_STRUCTURE)

    print_section("API Response Examples")
    print(RESPONSE_EXAMPLES)

    print_section("Integration Patterns")
    print(INTEGRATION_PATTERNS)

    print_section("Configuration Tips")
    tips = """
## Production Configuration

1. **Database**: Use PostgreSQL or Supabase for cloud
2. **Caching**: Add Redis for frequently accessed sections
3. **Rate Limiting**: Protect search endpoints
4. **Monitoring**: Track query performance and errors
5. **Scaling**: Use connection pooling for database

## Security Considerations

1. Sanitize all user input
2. Validate section IDs
3. Use environment variables for API keys
4. Implement CORS for web clients
5. Add authentication for private docs

## Performance Tips

1. Enable database connection pooling
2. Cache search results for identical queries
3. Use pagination for large result sets
4. Consider async I/O for concurrent requests
5. Monitor memory usage with large datasets
"""
    print(tips)

    print("\n" + "=" * 60)
    print("  For more examples, see:")
    print("  - docs/tutorials/03-integration-tutorial.md")
    print("  - integrations/ directory")
    print("=" * 60)


if __name__ == "__main__":
    main()
