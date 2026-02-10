# skill-split Integration Guides

This directory contains comprehensive guides for integrating skill-split with various tools and platforms.

## Available Integrations

### [CLAUDE_CODE.md](./CLAUDE_CODE.md)
Using skill-split within Claude Code sessions for progressive disclosure of large documentation files.

**Topics Covered:**
- Progressive disclosure workflow
- Search before loading pattern
- Token efficiency (99% savings)
- Custom command integration
- Session memory integration

**Best For:** Claude Code users working with large skill/command/reference files

### [VSCODE.md](./VSCODE.md)
Concept and implementation guide for a VS Code extension using Language Server Protocol.

**Topics Covered:**
- Extension architecture
- Section tree view
- Search panel with webview
- LSP server integration
- Keyboard shortcuts

**Best For:** Developers building VS Code extensions or IDE integrations

### [PYTHON_PACKAGE.md](./PYTHON_PACKAGE.md)
Using skill-split as a Python library in your applications.

**Topics Covered:**
- Core API usage (Parser, DatabaseStore, QueryAPI)
- Progressive disclosure interface
- Semantic search integration
- Document composition
- Web API example (FastAPI)

**Best For:** Python developers building documentation systems, search interfaces, or custom tools

### [CI_CD.md](./CI_CD.md)
GitHub Actions and GitLab CI integration for documentation validation and skill testing.

**Topics Covered:**
- GitHub Actions workflows
- GitLab CI pipelines
- Pre-commit hooks
- Documentation coverage reports
- Automated skill testing

**Best For:** DevOps engineers maintaining documentation quality in CI/CD pipelines

## Quick Reference

### Token Efficiency Comparison

| Method | Tokens Loaded | Cost Factor |
|--------|--------------|-------------|
| Full file | ~5,000 | 1.0x |
| Single section | ~50 | 0.01x |
| **Savings** | **99%** | **100x cheaper** |

### Search Modes

| Mode | Command | Use Case |
|------|---------|----------|
| BM25 Keywords | `search "query"` | Fast, precise matches |
| Vector Semantic | `search-semantic "query" --vector-weight 1.0` | Concept-based search |
| Hybrid | `search-semantic "query" --vector-weight 0.7` | Best of both worlds |

## Integration Patterns

### Pattern 1: Search-First Workflow

```bash
# 1. Search for relevant content
./skill_split.py search "error handling"

# 2. Load specific section
./skill_split.py get-section 42

# 3. Navigate progressively
./skill_split.py next 42 file.md --child
```

### Pattern 2: Custom Skills Composition

```bash
# Compose from existing sections
./skill_split.py compose \
  --sections 42,57,103 \
  --output custom_skill.md

# Validate the result
./skill_split.py validate custom_skill.md
```

### Pattern 3: CI/CD Validation

```yaml
- name: Validate documentation
  run: |
    pip install -e .
    for file in skills/**/*.md; do
      python skill_split.py validate "$file"
    done
```

## Environment Setup

```bash
# Database location
export SKILL_SPLIT_DB="$HOME/.claude/databases/skill-split.db"

# Optional: For semantic search
export OPENAI_API_KEY="sk-..."
export SUPABASE_URL="https://..."
export SUPABASE_KEY="..."
```

## Common Use Cases

### 1. Documentation Site Backend
- Use skill-split as Python library
- Expose REST API for section retrieval
- Implement progressive disclosure in frontend
- See: [PYTHON_PACKAGE.md](./PYTHON_PACKAGE.md)

### 2. IDE Extension
- Build VS Code extension with LSP
- Show section hierarchy in tree view
- Enable search across all files
- See: [VSCODE.md](./VSCODE.md)

### 3. Automated Quality Checks
- Validate documentation structure in CI/CD
- Test search quality on every commit
- Ensure progressive disclosure works
- See: [CI_CD.md](./CI_CD.md)

### 4. Claude Code Sessions
- Index skills and commands
- Search before loading full files
- Reference specific sections in prompts
- See: [CLAUDE_CODE.md](./CLAUDE_CODE.md)

## Contributing

Have an integration to share? Contributions welcome!

1. Create a new guide following the existing pattern
2. Include working examples and code samples
3. Add troubleshooting section
4. Update this README

## Performance Tips

1. **Batch Operations**: Parse multiple files at once
2. **Index Optimization**: FTS5 is automatically indexed
3. **Query Limits**: Always limit search results
4. **Connection Pooling**: Reuse DatabaseStore instances

## See Also

- [../README.md](../README.md) - Main documentation
- [../EXAMPLES.md](../EXAMPLES.md) - Usage examples
- [../CLAUDE.md](../CLAUDE.md) - Project rules

---

*Last Updated: 2025-02-10*
