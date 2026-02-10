# Deployment Guide

**Last Updated:** 2026-02-10

Guide for deploying skill-split in various environments.

---

## Table of Contents

- [Deployment Options](#deployment-options)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Container Deployment](#container-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring](#monitoring)

---

## Deployment Options

### Standalone CLI

Deploy as a command-line tool on local machines or servers.

**Best for:**
- Development workflows
- CI/CD pipelines
- Local documentation management

### Python Package

Install as a Python package for programmatic access.

**Best for:**
- Python applications
- Jupyter notebooks
- Automated workflows

### Web Service

Deploy as a REST API for web applications.

**Best for:**
- Multi-user environments
- Web interfaces
- Remote access

---

## Local Development

### Installation

```bash
# Clone repository
git clone https://github.com/user/skill-split.git
cd skill-split

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest test/ -v
```

### Configuration

```bash
# Set environment variables
export SKILL_SPLIT_DB="$HOME/.skill-split/db"
export OPENAI_API_KEY="sk-..."  # For semantic search
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-key"
```

---

## Production Deployment

### System Requirements

- **Python:** 3.10 or higher
- **RAM:** 512MB minimum, 2GB recommended for large databases
- **Disk:** 100MB for application + database size
- **OS:** Linux, macOS, or Windows

### Installation

```bash
# Install as package
pip install skill-split

# Or install from source
pip install git+https://github.com/user/skill-split.git
```

### Database Setup

```bash
# Create database directory
mkdir -p /var/lib/skill-split

# Initialize database
skill-split init --db /var/lib/skill-split/skills.db

# Set permissions
chmod 755 /var/lib/skill-split
```

### Configuration File

Create `/etc/skill-split/config.yaml`:

```yaml
database:
  path: /var/lib/skill-split/skills.db
  cache_size: 64000  # 64MB
  wal_mode: true

search:
  default_limit: 10
  max_results: 100

embeddings:
  enabled: true
  model: text-embedding-3-small
  cache_size: 1000

supabase:
  url: ${SUPABASE_URL}
  key: ${SUPABASE_KEY}
```

### Service Setup (systemd)

Create `/etc/systemd/system/skill-split.service`:

```ini
[Unit]
Description=skill-split documentation server
After=network.target

[Service]
Type=simple
User=skill-split
Group=skill-split
WorkingDirectory=/opt/skill-split
Environment="SKILL_SPLIT_CONFIG=/etc/skill-split/config.yaml"
ExecStart=/usr/bin/python -m skill_split.server --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable skill-split
sudo systemctl start skill-split
sudo systemctl status skill-split
```

---

## Container Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create database directory
RUN mkdir -p /data

# Set environment
ENV SKILL_SPLIT_DB=/data/skills.db

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "-m", "skill_split.server", "--port", "8080"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  skill-split:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
      - ./docs:/docs:ro
    environment:
      - SKILL_SPLIT_DB=/data/skills.db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    restart: unless-stopped

  # Optional: PostgreSQL for production
  postgres:
    image: postgres:16
    environment:
      - POSTGRES_DB=skill_split
      - POSTGRES_USER=skill_split
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Running

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Cloud Deployment

### AWS Lambda

```python
import json
from core.database import DatabaseStore
from core.query import QueryAPI

def lambda_handler(event, context):
    """AWS Lambda handler."""
    db = DatabaseStore("/tmp/skills.db")
    api = QueryAPI(db)

    query = event.get('query', '')
    results = api.search_sections(query, limit=10)

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
```

### Google Cloud Functions

```python
def search_docs(request):
    """HTTP Cloud Function."""
    from flask import jsonify
    from core.database import DatabaseStore
    from core.query import QueryAPI

    db = DatabaseStore("/tmp/skills.db")
    api = QueryAPI(db)

    request_json = request.get_json()
    query = request_json.get('query', '')

    results = api.search_sections(query)
    return jsonify(results)
```

### Azure Functions

```python
import azure.functions as func
from core.database import DatabaseStore
from core.query import QueryAPI

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function handler."""
    db = DatabaseStore("/tmp/skills.db")
    api = QueryAPI(db)

    query = req.params.get('query')
    results = api.search_sections(query)

    return func.HttpResponse(
        json.dumps(results),
        status_code=200,
        mimetype="application/json"
    )
```

---

## Monitoring

### Health Checks

```bash
# Check service status
curl http://localhost:8080/health

# Expected response
{"status": "healthy", "database": "/data/skills.db"}
```

### Metrics Endpoint

```bash
# Get metrics
curl http://localhost:8080/metrics

# Response includes
{
  "files": 1365,
  "sections": 19207,
  "queries_today": 1234,
  "avg_query_time_ms": 45.2
}
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/skill-split/app.log'),
        logging.StreamHandler()
    ]
)
```

### Performance Monitoring

```bash
# Enable query logging
export SKILL_SPLIT_LOG_QUERIES=true

# Monitor database performance
sqlite3 skills.db "EXPLAIN QUERY PLAN SELECT * FROM sections_fts WHERE content MATCH 'query';"
```

---

## Backup Strategy

### Database Backup

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/skill-split"
DB_PATH="/var/lib/skill-split/skills.db"

mkdir -p "$BACKUP_DIR"
cp "$DB_PATH" "$BACKUP_DIR/skills_$DATE.db"

# Keep last 30 days
find "$BACKUP_DIR" -name "skills_*.db" -mtime +30 -delete
```

### Automated Backup (cron)

```cron
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-skill-split.sh
```

---

## Security Considerations

### File Permissions

```bash
# Restrict database access
chmod 600 /var/lib/skill-split/skills.db

# Restrict config file
chmod 600 /etc/skill-split/config.yaml
```

### API Keys

```bash
# Use environment variables, never hardcode
export OPENAI_API_KEY="sk-..."
export SUPABASE_KEY="your-key"

# Or use secret management
# AWS Secrets Manager
# Azure Key Vault
# Google Secret Manager
```

### Network Security

```bash
# Firewall rules
ufw allow 8080/tcp  # Only allow necessary ports
ufw enable
```

---

## Troubleshooting

### Database Locked

```bash
# Check for locks
lsof | grep skills.db

# Remove WAL files
rm -f skills.db-wal skills.db-shm
```

### Out of Memory

```bash
# Reduce cache size
sqlite3 skills.db "PRAGMA cache_size = -16000;"  # 16MB

# Or increase system swap
swapon /swapfile
```

### Slow Queries

```bash
# Rebuild FTS5 index
sqlite3 skills.db "INSERT INTO sections_fts(sections_fts) VALUES('rebuild');"

# Analyze query plan
EXPLAIN QUERY PLAN SELECT ...
```

---

*For more information, see [MONITORING.md](./MONITORING.md)*
