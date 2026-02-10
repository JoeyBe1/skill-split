# skill-split Comparison Matrix

**skill-split vs alternatives - Feature comparison and positioning**

---

## Quick Comparison

| Feature | skill-split | Obsidian | Foam | Logseq | Notion |
|---------|-------------|----------|------|--------|--------|
| Local Storage | ✅ SQLite | ✅ Local | ✅ Local | ✅ Local | ❌ Cloud only |
| Search | ✅ 3 modes | ✅ Basic | ✅ Basic | ✅ Basic | ✅ Advanced |
| Semantic Search | ✅ OpenAI | ❌ | ❌ | ❌ | ✅ Proprietary |
| Progressive Disclosure | ✅ 99% savings | ❌ | ❌ | ❌ | ❌ |
| API Access | ✅ Python + CLI | ❌ | ❌ | ❌ | ✅ REST API |
| Round-trip Integrity | ✅ SHA256 | N/A | N/A | N/A | N/A |
| Open Source | ✅ MIT | ❌ Custom | ❌ Custom | ❌ Custom | ❌ Proprietary |
| Extensible | ✅ Plugins | ✅ Plugins | ✅ Plugins | ✅ Plugins | ❌ Limited |
| CI/CD Integration | ✅ Native | ❌ | ❌ | ❌ | ✅ Limited |
| CLI Tool | ✅ 16 commands | ❌ | ❌ | ❌ | ❌ |
| Cloud Storage | ✅ Supabase | ✅ Sync | ✅ Sync | ✅ Sync | ✅ Native |

---

## Detailed Comparison

### skill-split

**Best for:** Developers, technical documentation, AI workflows

**Strengths:**
- 99% token savings through progressive disclosure
- Three search modes (BM25, Vector, Hybrid)
- Byte-perfect round-trip integrity
- Extensible plugin system
- Complete Python API
- Production-ready CI/CD

**Weaknesses:**
- Markdown focused (limited format support)
- Requires Python 3.10+
- New project (smaller community)

**Use when:**
- Building AI workflows
- Need programmatic access
- Want local-first with cloud option
- Require customizable search

---

### Obsidian

**Best for:** Personal knowledge management, note-taking

**Strengths:**
- Rich plugin ecosystem
- Visual graph view
- Daily notes
- Cross-platform
- Active community

**Weaknesses:**
- Not API-driven
- Limited search options
- No semantic search
- Closed-source (app is proprietary)

**Use when:**
- Personal note-taking
- Want visual knowledge graphs
- Don't need API access

---

### Foam (VS Code)

**Best for:** Developers using VS Code, markdown-based PKM

**Strengths:**
- VS Code integration
- Backlinking
- Graph visualization
- Open source

**Weaknesses:**
- VS Code dependency
- Basic search only
- No semantic search
- Limited automation

**Use when:**
- Already using VS Code
- Want simple PKM
- Don't need advanced search

---

### Logseq

**Best for:** Outliner-style note-taking, collaborative knowledge

**Strengths:**
- Outliner interface
- Block-based editing
- Collaboration features
- PDF annotation

**Weaknesses:**
- Not API-driven
- Limited search
- No semantic search
- Learning curve

**Use when:**
- Prefer outliner workflow
- Need collaboration
- Want PDF annotation

---

### Notion

**Best for:** Teams wanting all-in-one workspace

**Strengths:**
- All-in-one (docs, databases, wikis)
- Powerful databases
- Collaboration features
- Beautiful UI

**Weaknesses:**
- Cloud-only (no local storage)
- Expensive for teams
- Limited API
- Not developer-focused
- Privacy concerns

**Use when:**
- Want all-in-one solution
- Need collaboration
- Budget allows
- OK with cloud-only

---

## Feature Deep Dive

### Search Capabilities

| Feature | skill-split | Others |
|---------|-------------|--------|
| BM25 (keyword) | ✅ Fast, local | Some |
| Vector (semantic) | ✅ OpenAI | Notion only |
| Hybrid search | ✅ Tunable weights | None |
| FTS5 optimization | ✅ SQLite native | Varies |
| Search by file | ✅ | Some |
| Search by tag | ✅ Via handlers | Most |
| Regex search | ✅ SQLite regex | Some |

**Winner:** skill-split (most flexible search)

### Token Efficiency

| Tool | Full File Load | Single Section | Savings |
|------|---------------|----------------|---------|
| skill-split | 2,500 tokens | 25 tokens | **99%** |
| Obsidian | All content | All content | 0% |
| Notion API | All content | All content | 0% |
| Foam | All content | All content | 0% |

**Winner:** skill-split (unique progressive disclosure)

### Developer Experience

| Feature | skill-split | Others |
|---------|-------------|--------|
| CLI | ✅ 16 commands | ❌ |
| Python API | ✅ Complete | ❌ |
| CI/CD | ✅ GitHub Actions | ❌ |
| Pre-commit hooks | ✅ Included | ❌ |
| Docker support | ✅ Multi-stage | ❌ |
| Extensible | ✅ Plugin system | Varies |

**Winner:** skill-split (developer-focused)

### Data Ownership

| Feature | skill-split | Obsidian | Foam | Logseq | Notion |
|---------|-------------|----------|------|--------|--------|
| Local-first | ✅ | ✅ | ✅ | ✅ | ❌ |
| Export | ✅ SQL/MD | ✅ MD | ✅ MD | ✅ MD | ⚠️ Limited |
| Open format | ✅ SQLite | ⚠️ Proprietary | ✅ MD | ✅ Org | ❌ Proprietary |
| Self-host | ✅ | ❌ | ❌ | ❌ | ❌ |
| Backup | ✅ Built-in | Manual | Manual | Manual | ❌ |

**Winner:** skill-split, Obsidian, Foam, Logseq (tie) - Notion loses

### Extensibility

| Feature | skill-split | Obsidian | Foam | Logseq | Notion |
|---------|-------------|----------|------|--------|--------|
| Plugins | ✅ Python handlers | ✅ JS plugins | ✅ Extensions | ⚠️ Limited | ❌ |
| Custom formats | ✅ Add handlers | ⚠️ Limited | ❌ | ❌ | ❌ |
| API | ✅ Python + CLI | ❌ | ❌ | ❌ | ⚠️ REST |
| Webhooks | ❌ | ❌ | ❌ | ❌ | ✅ |
| Scripts | ✅ Shell/Python | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited | ❌ |

**Winner:** skill-split (programmatic extensibility)

---

## Cost Comparison

### Tool Costs (Annual)

| Tool | Free | Paid | Total (annual) |
|------|------|------|----------------|
| skill-split | ✅ Full | N/A | **$0** |
| Obsidian | ✅ Personal | $50 (Sync) | $0-$50 |
| Foam | ✅ Full | N/A | **$0** |
| Logseq | ✅ Full | N/A | **$0** |
| Notion | ⚠️ Limited | $8-15/user | $96-180/user |

### Infrastructure Costs

| Tool | Storage | Compute | Search | Total (10K docs) |
|------|---------|---------|--------|------------------|
| skill-split | $0 | $0 | $0.02 (one-time) | **$0.02** |
| Obsidian Sync | $50 | $0 | $0 | $50 |
| Notion | $0 | $0 | $0 | $96+ |

**Winner:** skill-split (lowest cost)

---

## Use Case Recommendations

### Use skill-split if you:

- ✅ Are a developer or technical user
- ✅ Want to integrate with AI workflows
- ✅ Need programmatic access (CLI/API)
- ✅ Want flexible search options
- ✅ Value data ownership
- ✅ Need CI/CD integration
- ✅ Want to extend functionality

### Use Obsidian if you:

- ✅ Want a polished UI
- ✅ Need visual graph views
- ✅ Want a large plugin ecosystem
- ✅ Are non-technical
- ✅ Don't need API access

### Use Notion if you:

- ✅ Need an all-in-one workspace
- ✅ Require team collaboration
- ✅ Want beautiful databases
- ✅ Have budget for paid plans
- ✅ Are OK with cloud-only

---

## Summary Table

| Criteria | skill-split | Obsidian | Foam | Logseq | Notion |
|----------|-------------|----------|------|--------|--------|
| Developer Experience | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Search Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Token Efficiency | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| Extensibility | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Ease of Use | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Data Ownership | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Cost | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**Overall Winner for Developers:** skill-split

**Overall Winner for Non-Tech Users:** Obsidian

**Overall Winner for Teams:** Notion

---

## Conclusion

skill-split occupies a unique position:
- **Developer-focused** (unlike PKM tools)
- **API-driven** (unlike traditional tools)
- **Token-efficient** (unique progressive disclosure)
- **Extensible** (plugin system)
- **Production-ready** (CI/CD, Docker, testing)

**Choose skill-split when:**
You want a powerful, programmable documentation tool that integrates with AI workflows and respects data ownership.

---

*skill-split - Progressive disclosure for AI workflows*
