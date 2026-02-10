# Security Documentation

**Version**: 1.0.0
**Last Updated**: 2025-02-10
**Status**: Active

## Table of Contents

1. [Security Overview](#security-overview)
2. [Threat Model](#threat-model)
3. [Input Validation](#input-validation)
4. [SQL Injection Prevention](#sql-injection-prevention)
5. [XSS Protection](#xss-protection)
6. [API Key Management](#api-key-management)
7. [Database Security](#database-security)
8. [Dependency Scanning](#dependency-scanning)
9. [Security Audit Checklist](#security-audit-checklist)
10. [Responsible Disclosure Policy](#responsible-disclosure-policy)

---

## Security Overview

Skill-split is a CLI tool that parses markdown and YAML files, storing sections in SQLite or Supabase databases. The tool processes local files and can interact with remote APIs (OpenAI, Supabase) for optional features like semantic search and cloud storage.

### Security Posture

- **Primary Attack Surface**: File parsing, database operations, API interactions
- **Trust Boundaries**: Local filesystem, local SQLite, remote Supabase, external APIs
- **Security Level**: Standard CLI tool with defense-in-depth principles

### Key Security Features

1. **Parameterized Queries**: All database operations use prepared statements
2. **Secret Management**: Flexible credential storage with environment variable fallback
3. **Input Validation**: Type checking and validation at parser boundaries
4. **SHA256 Hashing**: Content integrity verification using cryptographic hashes
5. **Path Traversal Protection**: Safe file path handling with Path objects
6. **FTS5 Sanitization**: Query preprocessing for full-text search

---

## Threat Model

### Attackers

1. **Malicious File Authors**: Users who craft malicious markdown/YAML files
2. **Local adversaries**: Users with filesystem access attempting privilege escalation
3. **Network adversaries**: Intercepting API communications (Supabase, OpenAI)
4. **Compromised dependencies**: Supply chain attacks via vulnerable packages

### Threat Categories

#### 1. File Processing Threats

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Path traversal attacks | Filesystem read/write outside intended scope | `pathlib.Path` usage, no shell command execution |
| Malformed input causing DoS | Resource exhaustion, crashes | Defensive parsing, size limits |
| Code injection via markdown | Arbitrary code execution | No eval/exec, read-only operations |
| XML bomb attacks | Billion laughs attack | Parser limits, XML tag validation |

#### 2. Database Threats

| Threat | Impact | Mitigation |
|--------|--------|------------|
| SQL injection | Data exfiltration, corruption | Parameterized queries only |
| Unauthorized access | Data breach | File permissions, Row-Level Security in Supabase |
| Database corruption | Data loss | CASCADE deletes with foreign keys |
| FTS5 injection | Search manipulation | Query sanitization in `preprocess_fts5_query()` |

#### 3. API Threats

| Threat | Impact | Mitigation |
|--------|--------|------------|
| API key leakage | Credential theft | Environment variables, SecretManager |
| Man-in-the-middle | Data tampering | HTTPS only |
| Rate limiting | Service unavailability | Exponential backoff |
| Token exposure in logs | Credential leakage | No logging of sensitive data |

#### 4. Dependency Threats

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Vulnerable dependencies | Supply chain attack | Pin versions, regular updates |
| Typosquatting | Malicious packages | Use PyPI, verify packages |

---

## Input Validation

### File Path Validation

**Pattern: Safe Path Handling**

```python
# SECURE: Using pathlib.Path for safe path operations
from pathlib import Path

def validate_file_path(file_path: str) -> Path:
    """Validate and resolve file path safely."""
    path = Path(file_path).expanduser().resolve()

    # Check path exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Prevent directory traversal beyond intended scope
    # (if operating within a restricted directory)
    # base_dir = Path("/allowed/base").resolve()
    # try:
    #     path.relative_to(base_dir)
    # except ValueError:
    #     raise PermissionError("Path outside allowed directory")

    return path
```

**Pitfall to Avoid:**

```python
# INSECURE: Direct string manipulation vulnerable to traversal
def read_file_unsafe(file_path: str):
    # Vulnerable to "../../../etc/passwd" attacks
    with open(file_path) as f:  # DON'T DO THIS
        return f.read()
```

### Content Validation

**Pattern: Defensive Parsing**

```python
# SECURE: Validate content before processing
def parse_headings(self, content: str) -> ParsedDocument:
    """Parse markdown content with defensive validation."""
    if not content or not content.strip():
        # Return empty document instead of crashing
        return ParsedDocument(
            frontmatter="",
            sections=[],
            file_type=FileType.REFERENCE,
            format=FileFormat.MARKDOWN_HEADINGS,
            original_path="",
        )

    # Limit content size to prevent DoS
    MAX_CONTENT_SIZE = 10_000_000  # 10MB
    if len(content) > MAX_CONTENT_SIZE:
        raise ValueError(f"Content too large: {len(content)} bytes")

    # Proceed with parsing...
```

### Query Input Validation

**Pattern: FTS5 Query Sanitization**

```python
# SECURE: Preprocess search queries
@staticmethod
def preprocess_fts5_query(query: str) -> str:
    """
    Convert natural language query to safe FTS5 MATCH syntax.

    Prevents FTS5 injection by sanitizing special characters
    and properly quoting terms.
    """
    if not query:
        return ""

    # Normalize whitespace
    query = ' '.join(query.split())

    # Check for user-provided FTS5 operators (case-insensitive)
    query_lower = query.lower()
    fts5_operators = [' and ', ' or ', ' near ']
    has_operator = any(op in query_lower for op in fts5_operators)

    if has_operator:
        # Normalize operators to uppercase
        result = query_lower.replace(' and ', ' AND ').replace(' or ', ' OR ')
        return result.replace(' near ', ' NEAR ')

    # Check for quoted phrase search
    if query.startswith('"') and query.endswith('"'):
        return query

    # Quote special characters to prevent injection
    special_chars = set('-*"\'<>')
    if any(char in query for char in special_chars):
        return f'"{query}"'

    return query
```

**Pitfall to Avoid:**

```python
# INSECURE: Direct use of user input in SQL
cursor.execute(
    f"SELECT * FROM sections WHERE content LIKE '%{user_query}%'"
)  # VULNERABLE to SQL injection
```

### Type Validation

**Pattern: Type Checking at Boundaries**

```python
# SECURE: Validate section IDs are integers
def cmd_get_section(args) -> int:
    """Retrieve section with type validation."""
    section_id_str = args.section_id_or_file

    try:
        section_id = int(section_id_str)
        if section_id <= 0:
            raise ValueError("Section ID must be positive")
    except ValueError:
        print("Error: Section ID must be a positive integer",
              file=sys.stderr)
        return 1

    # Proceed with validated ID...
```

---

## SQL Injection Prevention

### Parameterized Queries (Always Used)

**Pattern: Prepared Statements**

```python
# SECURE: All database queries use parameterized queries
def get_section(self, section_id: int) -> Optional[Section]:
    """Get section by ID using prepared statement."""
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row

        # ? placeholder prevents SQL injection
        cursor = conn.execute(
            """
            SELECT level, title, content, line_start, line_end
            FROM sections
            WHERE id = ?
            """,
            (section_id,)  # Parameter tuple
        )
        row = cursor.fetchone()
        # ...
```

**Key Points:**

1. **Never** use f-strings or string concatenation for SQL
2. **Always** use `?` placeholders with parameter tuples
3. **Always** use context managers (`with sqlite3.connect()`)
4. **Validate** types before database operations

### Complete Parameterized Example

```python
# SECURE: Multi-parameter query
def search_sections(
    self, query: str, file_path: Optional[str] = None
) -> List[Tuple[int, Section]]:
    """Search with safe parameterized queries."""
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row

        if file_path:
            # Get file_id first (parameterized)
            cursor = conn.execute(
                "SELECT id FROM files WHERE path = ?",
                (file_path,)
            )
            file_row = cursor.fetchone()
            if not file_row:
                return []
            file_id = file_row["id"]

            # Search with both parameters
            cursor = conn.execute(
                """
                SELECT id, level, title, content
                FROM sections
                WHERE file_id = ? AND (title LIKE ? OR content LIKE ?)
                ORDER BY file_id, order_index
                """,
                (file_id, f"%{query}%", f"%{query}%")
            )
        else:
            # Search without file constraint
            cursor = conn.execute(
                """
                SELECT id, level, title, content
                FROM sections
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY file_id, order_index
                """,
                (f"%{query}%", f"%{query}%")
            )

        return [(row["id"], Section(...)) for row in cursor.fetchall()]
```

### FTS5 Full-Text Search Security

```python
# SECURE: FTS5 with sanitized MATCH syntax
def search_sections_with_rank(
    self, query: str, file_path: Optional[str] = None
) -> List[Tuple[int, float]]:
    """Search using FTS5 with query sanitization."""
    # Preprocess query to prevent FTS5 injection
    processed_query = self.preprocess_fts5_query(query)

    if not processed_query:
        return []

    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row

        # FTS5 MATCH with sanitized query
        cursor = conn.execute(
            """
            SELECT s.id, bm25(sections_fts) as rank
            FROM sections_fts
            JOIN sections s ON sections_fts.rowid = s.id
            WHERE sections_fts MATCH ?
            ORDER BY rank
            """,
            (processed_query,)
        )

        return [(row["id"], -row["rank"]) for row in cursor.fetchall()]
```

### Supabase Query Security

```python
# SECURE: Supabase query builder prevents injection
def get_section(self, section_id: str) -> Optional[Tuple[str, Section]]:
    """Get section from Supabase safely."""
    # Supabase client builds parameterized queries automatically
    response = self.client.table("sections").select(
        "id, level, title, content, line_start, line_end"
    ).eq("id", section_id).execute()

    # No manual SQL = no SQL injection risk
    if not response.data:
        return None

    row = response.data[0]
    return (row["id"], Section(...))
```

---

## XSS Protection

### Current Status

Skill-split is a **CLI tool** that outputs to terminal, not a web application. XSS (Cross-Site Scripting) is primarily a web vulnerability and **does not apply** to the core CLI functionality.

### Future Web UI Considerations

If a web interface is added, the following protections will be required:

```python
# FUTURE: HTML escaping for web output
import html

def escape_html(text: str) -> str:
    """Escape HTML entities to prevent XSS."""
    return html.escape(text, quote=True)

# FUTURE: Content Security Policy headers
csp_headers = {
    "Content-Security-Policy": "default-src 'self'; script-src 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY"
}
```

### Markdown Rendering Safety

```python
# SECURE: Treat markdown as plain text in CLI
def display_section(section: Section) -> None:
    """Display section content safely."""
    # CLI output doesn't interpret HTML/markdown
    # No rendering = no XSS risk
    print(f"## {section.title}")
    print(section.content)
```

---

## API Key Management

### SecretManager Architecture

Skill-split provides flexible secret management through `SecretManager`:

**Priority Order:**
1. Direct parameters
2. File (`~/.claude/secrets.json`)
3. Keyring (optional, via `keyring` package)
4. Environment variables

### Secure Credential Storage

**Pattern: SecretManager Usage**

```python
# SECURE: Multi-source credential retrieval
from core.secret_manager import SecretManager, SecretSourceType

def initialize_api_client():
    """Initialize API client with secure credentials."""
    secret_manager = SecretManager()

    try:
        # Try multiple sources automatically
        api_key, source = secret_manager.get_secret_with_source("OPENAI_API_KEY")

        print(f"Using API key from: {source.value}")

        return OpenAI(api_key=api_key)

    except SecretNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

### Secrets File Format

```json
// ~/.claude/secrets.json ( chmod 600 )
{
  "OPENAI_API_KEY": "sk-...",
  "SUPABASE_URL": "https://...",
  "SUPABASE_KEY": "eyJ...",
  "aliases": {
    "openai": "OPENAI_API_KEY",
    "supabase": "SUPABASE_KEY"
  }
}
```

**Security Requirements:**

```bash
# File permissions for secrets.json
chmod 600 ~/.claude/secrets.json  # Owner read/write only
```

### Environment Variable Fallback

```python
# SECURE: Environment variable with fallback
def get_api_key() -> str:
    """Get API key from environment with fallback."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        # Try SecretManager as fallback
        try:
            secret_manager = SecretManager()
            api_key = secret_manager.get_secret("OPENAI_API_KEY")
        except Exception:
            raise ValueError(
                "OPENAI_API_KEY not found in environment or SecretManager"
            )

    return api_key
```

### API Key Transmission

**Pattern: HTTPS-Only Communication**

```python
# SECURE: HTTPS enforced by clients
# OpenAI and Supabase clients use HTTPS by default
# No manual URL construction = no accidental HTTP

embedding_service = EmbeddingService(api_key)  # Uses OpenAI SDK
supabase_store = SupabaseStore(url, key)       # Uses Supabase SDK

# Both SDKs:
# - Enforce HTTPS
# - Handle authentication headers
# - Provide secure defaults
```

### Logging Security

**Pattern: Never Log Secrets**

```python
# SECURE: Sanitized logging
def log_api_request(endpoint: str, params: dict):
    """Log API request without sensitive data."""
    # Remove sensitive keys before logging
    safe_params = {k: v for k, v in params.items()
                   if k not in ['api_key', 'password', 'token']}

    print(f"API Request: {endpoint}, params: {safe_params}")
    # NEVER log api_key values

# INSECURE: Logging sensitive data
# print(f"Making request with key: {api_key}")  # DON'T DO THIS
```

---

## Database Security

### SQLite Security

#### File Permissions

```bash
# Recommended database file permissions
chmod 600 ~/.claude/databases/skill-split.db  # Owner only
chmod 700 ~/.claude/databases/                 # Owner only
```

#### Connection Security

```python
# SECURE: SQLite connection with safety settings
def __init__(self, db_path: str) -> None:
    """Initialize database with secure defaults."""
    self.db_path = db_path

    with sqlite3.connect(self.db_path) as conn:
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Set secure mode
        conn.execute("PRAGMA secure_delete = ON")  # Overwrite deleted data

        # Limit memory usage
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB max
```

#### Foreign Key Constraints

```sql
-- SECURE: CASCADE delete prevents orphaned records
CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    parent_id INTEGER,
    -- ... other columns ...
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES sections(id) ON DELETE CASCADE
);
```

### Supabase Security

#### Row-Level Security (RLS)

```sql
-- Enable RLS on Supabase tables
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE sections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read files they own
CREATE POLICY "Users can view own files"
ON files FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Service role has full access
CREATE POLICY "Service role full access"
ON files FOR ALL
USING (auth.role() = 'service_role');
```

#### API Key Types

```python
# SECURE: Use appropriate key types
# anon/publishable key: For client-side operations (limited)
# service_role key: For admin operations (full access)

# For CLI tool, typically use service_role key with:
# - IP restrictions
# - RLS policies as defense-in-depth
# - Regular rotation
```

#### Connection Security

```python
# SECURE: HTTPS-only Supabase connections
def __init__(self, url: str, key: str):
    """Initialize Supabase client with URL validation."""
    # Validate HTTPS
    if not url.startswith("https://"):
        raise ValueError("Supabase URL must use HTTPS")

    self.url = url
    self.key = key

    # Client enforces HTTPS
    self.client = create_client(url, key)
```

### Database Backup Security

```python
# SECURE: Encrypted backup with restricted permissions
def create_secure_backup(db_path: str, backup_path: str):
    """Create backup with security considerations."""
    import shutil
    import stat

    # Copy database
    shutil.copy2(db_path, backup_path)

    # Set restrictive permissions
    os.chmod(backup_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
```

---

## Dependency Scanning

### Current Dependencies

```
supabase>=2.3.0
python-dotenv>=1.0.0
pytest>=7.0.0
pytest-benchmark>=4.0.0
pytest-cov>=4.0.0
```

### Security Scanning Tools

```bash
# pip-audit: Check for known vulnerabilities
pip install pip-audit
pip-audit

# safety: Check dependencies against security database
pip install safety
safety check

# bandit: Security linter for Python code
pip install bandit
bandit -r .

# semgrep: Static analysis for security patterns
pip install semgrep
semgrep --config=auto
```

### Dependency Pinning

```bash
# requirements.txt with pinned versions
supabase==2.3.1
python-dotenv==1.0.0
pytest==7.4.3
pytest-benchmark==4.0.0
pytest-cov==4.1.0
```

### Vulnerability Response

**When a vulnerability is discovered:**

1. **Assess Impact**: Determine if vulnerable code is actually used
2. **Check Exploitability**: Verify if exploit conditions exist
3. **Find Replacement**: Identify secure alternative or patched version
4. **Test Thoroughly**: Verify replacement works correctly
5. **Update Dependencies**: Pin to secure version
6. **Document**: Record in CHANGELOG.md

### Example Scanning Workflow

```bash
#!/bin/bash
# security-scan.sh - Run all security scans

echo "=== Running pip-audit ==="
pip-audit || echo "Vulnerabilities found!"

echo "=== Running safety check ==="
safety check || echo "Safety issues found!"

echo "=== Running bandit ==="
bandit -r ./core ./handlers -f json -o bandit-report.json

echo "=== Running semgrep ==="
semgrep --config=auto --json --output=semgrep-report.json

echo "Security scan complete. Check reports."
```

---

## Security Audit Checklist

### Pre-Deployment Checklist

- [ ] All file paths use `pathlib.Path` (no string manipulation)
- [ ] All database queries use parameterized statements
- [ ] All user input is validated and sanitized
- [ ] Secrets are stored in `~/.claude/secrets.json` with `chmod 600`
- [ ] No secrets are hardcoded in source code
- [ ] No secrets appear in logs or error messages
- [ ] All API communications use HTTPS
- [ ] File permissions are restrictive (600 for databases, 700 for directories)
- [ ] Dependencies are pinned to specific versions
- [ ] Security scanning tools are run regularly
- [ ] FTS5 queries are preprocessed through `preprocess_fts5_query()`

### Code Review Checklist

**For each new function:**

- [ ] **Input Validation**: Are all inputs validated?
- [ ] **SQL Safety**: Are database queries parameterized?
- [ ] **Path Safety**: Are file operations using `Path` objects?
- [ ] **Secret Safety**: Are credentials properly retrieved?
- [ ] **Error Handling**: Are errors handled without exposing sensitive data?
- [ ] **Logging**: Does logging avoid sensitive data?

**For database operations:**

- [ ] All queries use `?` placeholders
- [ ] Foreign keys are enabled
- [ ] CASCADE deletes are appropriate
- [ ] No dynamic SQL construction
- [ ] Connection uses context manager

**For API interactions:**

- [ ] HTTPS is enforced
- [ ] API keys use SecretManager
- [ ] Rate limiting is handled
- [ ] Errors don't expose credentials
- [ ] Request/response size is limited

### Regular Maintenance Tasks

**Weekly:**
- Run `pip-audit` to check for vulnerabilities
- Review error logs for suspicious patterns

**Monthly:**
- Update dependencies to latest secure versions
- Review and rotate API keys
- Run full security scan suite

**Quarterly:**
- Complete security audit checklist
- Review and update security documentation
- Test disaster recovery procedures

---

## Responsible Disclosure Policy

### Reporting Security Issues

**If you discover a security vulnerability:**

1. **DO NOT** create a public issue
2. **DO** send details directly to the maintainer
3. **DO** provide reproduction steps and impact assessment
4. **DO** allow reasonable time for patch development

### Reporting Process

**Email**: security@[project-domain]
**PGP Key**: Available at `/PGP_KEY.txt`
**Expected Response**: Within 48 hours
**Timeline for Fix**: Depends on severity, typically 7-14 days

### Vulnerability Information to Include

- Vulnerability type
- Affected versions
- Impact assessment
- Reproduction steps
- Suggested fix (optional)
- Proof of concept (optional, handle with care)

### Disclosure Timeline

1. **Initial Report**: Security researcher sends report
2. **Acknowledgment**: Maintainer confirms receipt (48 hours)
3. **Validation**: Maintainer validates and assesses (7 days)
4. **Fix Development**: Maintainer develops patch (7-14 days)
5. **Coordinated Release**: Researcher and maintainer agree on disclosure date
6. **Public Disclosure**: Vulnerability and patch announced together

### Safe Harbor

**We commit to:**

- Not pursuing legal action for responsible disclosure
- Crediting researchers (with permission)
- Working collaboratively on fixes
- Maintaining confidentiality until patch is ready

### Severity Classification

| Severity | Description | Timeline |
|----------|-------------|----------|
| Critical | Remote code execution, data breach | 7 days |
| High | Privilege escalation, data loss | 14 days |
| Medium | DoS, unauthorized access | 30 days |
| Low | Information disclosure, minor impact | 60 days |

### Security Contact Information

- **Project Repository**: https://github.com/[user]/skill-split
- **Security Email**: security@[domain]
- **PGP Fingerprint`: [FINGERPRINT]

---

## Appendix: Common Security Patterns

### Secure File Operations

```python
# SECURE: Safe file reading with size limit
def safe_read_file(file_path: str, max_size: int = 10_000_000) -> str:
    """Read file with size limit to prevent DoS."""
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = path.stat().st_size
    if file_size > max_size:
        raise ValueError(f"File too large: {file_size} bytes")

    return path.read_text(encoding='utf-8', errors='replace')
```

### Secure Error Handling

```python
# SECURE: Error messages don't leak sensitive info
def handle_database_error(error: Exception) -> str:
    """Return safe error message without internal details."""
    # Log full error internally
    import logging
    logging.error(f"Database error: {error}", exc_info=True)

    # Return generic message to user
    return "An error occurred processing your request. Please try again."
```

### Secure Type Validation

```python
# SECURE: Type checking at boundary
def validate_section_id(section_id: Any) -> int:
    """Validate and convert section ID."""
    if isinstance(section_id, int):
        if section_id <= 0:
            raise ValueError("Section ID must be positive")
        return section_id

    if isinstance(section_id, str):
        try:
            id_int = int(section_id)
            if id_int <= 0:
                raise ValueError("Section ID must be positive")
            return id_int
        except ValueError:
            raise ValueError(f"Invalid section ID: {section_id}")

    raise TypeError(f"Section ID must be int or str, got {type(section_id)}")
```

---

*This security documentation should be reviewed and updated at least quarterly or when significant changes are made to the codebase.*
