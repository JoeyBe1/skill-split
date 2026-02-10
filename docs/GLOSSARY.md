# skill-split Glossary

**Key terms and concepts**

---

## Core Concepts

### Progressive Disclosure

**Definition:** Loading only the specific information needed, rather than entire documents.

**Example:** Instead of loading a 5,000-token documentation file, load a single 50-token section.

**Benefit:** 99% token savings, faster responses, lower costs.

### Section

**Definition:** A logical unit of content, typically defined by markdown headings.

**Structure:**
```
# Heading 1 (Level 1)
## Heading 2 (Level 2)
### Heading 3 (Level 3)
```

**Properties:** id, heading, level, content, line_start, line_end, parent_id

### Round-Trip Integrity

**Definition:** The ability to parse a file, store it, retrieve it, and reconstruct it exactly byte-for-byte.

**Verification:** SHA256 hash comparison between original and reconstructed content.

### BM25 Search

**Definition:** BM25 (Best Matching 25) is a ranking function used by search engines to estimate the relevance of documents to search queries.

**Characteristics:** Fast, local, no API cost, exact keyword matching.

**Best for:** Exact matches, code references, specific terms.

### Vector Search

**Definition:** Search using semantic similarity via vector embeddings.

**Characteristics:** Slower, requires API, conceptual matching.

**Best for:** Concepts, ideas, related topics.

### Hybrid Search

**Definition:** Combining BM25 (keyword) and Vector (semantic) search with tunable weights.

**Default:** 70% vector, 30% keyword (`--vector-weight 0.7`)

**Best for:** General queries, balanced relevance.

---

## Database Terms

### SQLite

**Definition:** Lightweight, embedded SQL database engine.

**Benefits:** No server needed, local-first, reliable.

### FTS5

**Definition:** Full-Text Search extension for SQLite, with BM25 ranking built-in.

**Benefits:** Fast keyword search, no external dependencies.

### WAL Mode

**Definition:** Write-Ahead Logging journal mode for SQLite.

**Benefits:** Better concurrency, faster writes.

### CASCADE Delete

**Definition:** Database constraint that automatically deletes related records.

**Example:** Deleting a file automatically deletes all its sections.

---

## Component Terms

### Handler

**Definition:** A class that parses a specific file type (Python, JavaScript, etc.).

**Types:** Plugin, Hook, Config, Script handlers.

### Factory Pattern

**Definition:** Design pattern for creating objects without specifying exact classes.

**Usage:** `HandlerFactory.create(file_type)` returns appropriate handler.

### Frontmatter

**Definition:** YAML metadata at the beginning of a markdown file.

**Format:**
```yaml
---
title: Document Title
author: Name
tags: [tag1, tag2]
---
```

---

## Search Terms

### Token

**Definition:** Smallest unit of text processed by LLMs (roughly 4 characters).

**Context:** GPT-4 costs ~$30 per 1M tokens.

### Embedding

**Definition:** Vector representation of text that captures semantic meaning.

**Model:** `text-embedding-3-small` (OpenAI, $0.02 per 1M tokens).

### Semantic Search

**Definition:** Search based on meaning rather than exact keywords.

**Example:** Searching "login" finds "authentication" and "sign-in".

---

## CLI Terms

### CLI Command

**Definition:** Command-line interface command.

**Examples:** `parse`, `store`, `search`, `get-section`, `next`.

### Flag

**Definition:** Command-line option passed to a command.

**Examples:** `--db`, `--limit`, `--vector-weight`, `--verbose`.

---

## Development Terms

### Test Coverage

**Definition:** Percentage of code executed by tests.

**Target:** 95%+ for skill-split.

### Benchmark

**Definition:** Performance measurement against a baseline.

**Tool:** pytest-benchmark.

### Pre-commit Hook

**Definition:** Script that runs automatically before each git commit.

**Purpose:** Catch issues early, maintain code quality.

---

## Integration Terms

### Supabase

**Definition:** Open-source Firebase alternative with PostgreSQL.

**Usage:** Cloud storage for skill-split with pgvector support.

### CI/CD

**Definition:** Continuous Integration / Continuous Deployment.

**Examples:** GitHub Actions, GitLab CI.

### Docker

**Definition:** Container platform for packaging applications.

**Benefit:** Consistent environments across machines.

---

## Performance Terms

### Latency

**Definition:** Time delay for an operation.

**Target:** < 10ms for search queries.

### Throughput

**Definition:** Operations per second.

**Benchmark:** 1.7M searches/sec on 10K section database.

### Scalability

**Definition:** Ability to handle growing data volumes.

**Tested:** 19,207 sections, 1,365 files (production database).

---

## Security Terms

### SHA256

**Definition:** Cryptographic hash function for integrity verification.

**Usage:** `hashlib.sha256(content.encode()).hexdigest()`

### SQL Injection

**Definition:** Attack where malicious SQL is injected into queries.

**Prevention:** Parameterized queries.

### API Key

**Definition:** Secret token for authenticating to external APIs.

**Storage:** Environment variables, never hardcoded.

---

## AI/ML Terms

### Context Window

**Definition:** Maximum tokens an LLM can process at once.

**Examples:** GPT-4 (128K), Claude Opus (200K).

### LLM

**Definition:** Large Language Model.

**Examples:** GPT-4, Claude, LLaMA.

### RAG (Retrieval Augmented Generation)

**Definition:** AI pattern combining search with generation.

**skill-split role:** Provides retrieval component.

---

## Acronyms

| Acronym | Full Form | Meaning |
|---------|-----------|---------|
| BM25 | Best Matching 25 | Ranking algorithm |
| FTS5 | Full-Text Search 5 | SQLite extension |
| WAL | Write-Ahead Logging | Journal mode |
| SHA256 | Secure Hash Algorithm 256 | Hashing algorithm |
| API | Application Programming Interface | Code interface |
| CLI | Command-Line Interface | Terminal tool |
| YAML | YAML Ain't Markup Language | Config format |
| SQL | Structured Query Language | Database language |
| ROI | Return on Investment | Financial metric |

---

## Quick Reference

### File Size Impact

| Size | Tokens | Sections | Parse Time |
|------|--------|----------|------------|
| 1KB | 250 | ~3 | 0.013ms |
| 10KB | 2,500 | ~25 | 0.13ms |
| 100KB | 25,000 | ~250 | 1.3ms |

### Search Comparison

| Mode | Speed | Cost | Best For |
|------|-------|------|---------|
| BM25 | 5.8ms | $0 | Exact matches |
| Vector | 22ms | $0.0001 | Concepts |
| Hybrid | 8.5ms | $0.00001 | Balanced |

### Token Savings

| Method | Tokens | Savings |
|--------|--------|---------|
| Full file | 5,000 | 0% |
| Progressive | 50 | **99%** |

---

**Have a term not listed?** Check `docs/QUICK_REFERENCE.md`

---

*skill-split - Progressive disclosure for AI workflows*
