# Commit Message Guide

**Standardized commit messages for skill-split project**

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types

| Type | Purpose | Examples |
|------|---------|----------|
| `feat` | New feature | feat(search): add hybrid search with vector weights |
| `fix` | Bug fix | fix(parser): handle empty frontmatter correctly |
| `docs` | Documentation | docs(api): add search method examples |
| `test` | Tests | test(query): add hybrid search integration tests |
| `refactor` | Refactoring | refactor(database): simplify connection pooling |
| `perf` | Performance | perf(search): add FTS5 index for faster queries |
| `chore` | Maintenance | chore(deps): update pyyaml to 6.0.1 |
| `ci` | CI/CD | ci(github): add python 3.13 to test matrix |
| `style` | Style | style(lint): fix line length violations |

## Scopes

Common scopes:
- `parser` - File parsing logic
- `database` - Storage and queries
- `search` - BM25, vector, hybrid search
- `cli` - Command-line interface
- `api` - Python API
- `handlers` - Component handlers
- `embedding` - Vector embeddings
- `supabase` - Cloud storage
- `docs` - Documentation
- `tests` - Test suite
- `examples` - Example plugins/scripts
- `docker` - Container configuration
- `ci` - CI/CD workflows

## Examples

### Feature
```
feat(search): add hybrid search with configurable vector weights

Implements hybrid search combining BM25 keyword matching with
vector semantic search. Vector weight is configurable via
--vector-weight flag (default: 0.7).

Closes #42
```

### Bug Fix
```
fix(parser): handle empty frontmatter without crashing

Previously, files with empty frontmatter (---\n---) would
cause a parser error. Now treats empty frontmatter as valid
with no metadata.

Fixes #87
```

### Documentation
```
docs(api): add comprehensive search method examples

Added examples for BM25, vector, and hybrid search methods
including parameter explanations and expected output formats.
```

### Performance
```
perf(database): add FTS5 index on content column

Added FTS5 full-text index on sections.content for faster
BM25 searches. Query time reduced from 50ms to 5ms on
10K section database.

Benchmarks: before=50ms, after=5ms (10x improvement)
```

### Refactoring
```
refactor(handlers): extract common logic to base class

Moved duplicate file reading and validation logic from
PythonHandler and JavaScriptHandler into BaseHandler.

No functional changes, reduces code duplication.
```

## Commit Message Body

**When to include:**
- Bug fixes (explain what was broken and how it's fixed)
- Features (explain why and what it does)
- Breaking changes (explain migration path)
- Performance changes (include before/after metrics)

**Format:**
- Wrap at 72 characters
- Use imperative mood
- Explain what and why, not how

## Commit Message Footer

**Breaking Changes:**
```
BREAKING CHANGE: --vector-weight now defaults to 0.7 (was 0.5)

Migration: Update scripts explicitly using default to specify
--vector-weight 0.7 or set to desired value.
```

**Closes/References:**
```
Closes #123
Refs #456
See also #789
```

**Co-authored-by:**
```
Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## Multi-Line Commits

Use heredoc for proper formatting:

```bash
git commit -m "$(cat <<'EOF'
feat(search): add hybrid search

Combines BM25 and vector search with configurable weights.

Closes #42

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

## Commit Workflow

1. Stage specific files (not `git add .`)
2. Write commit message following format
3. Include body for non-trivial changes
4. Reference issues when applicable
5. Add co-author if AI assistance used

## Prohibited

- **No:** `git commit -m "update"` (too vague)
- **No:** `git commit -m "fixed stuff"` (unprofessional)
- **No:** `git commit -m "wip"` (work in progress)
- **No:** Commits without proper type/scope

---

*skill-split - Progressive disclosure for AI workflows*
