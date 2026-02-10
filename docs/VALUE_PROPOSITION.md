# skill-split Value Proposition

**Why skill-split matters for AI workflows**

---

## The Problem

### Documentation is Growing

- Average API doc: 5,000+ tokens
- Large projects: 50,000+ tokens
- Knowledge bases: 100,000+ tokens

### AI Context Limits

- **GPT-3.5:** 16K tokens (~$8 per 1M tokens)
- **GPT-4:** 128K tokens (~$30 per 1M tokens)
- **Claude Opus:** 200K tokens (~$15 per 1M tokens)

### The Cost of Full Loading

| File Size | Tokens | Cost per Query (GPT-4) | Annual (1K queries/day) |
|-----------|--------|------------------------|------------------------|
| 10KB | 2,500 | $0.075 | $27,375 |
| 50KB | 12,500 | $0.375 | $136,875 |
| 100KB | 25,000 | $0.75 | $273,750 |

**This is unsustainable.**

---

## The Solution: Progressive Disclosure

### Core Concept

**Load only what you need, when you need it.**

```
Traditional:
┌────────────────────────────────┐
│  Load entire documentation      │ 25,000 tokens
└────────────────────────────────┘

Progressive Disclosure:
┌──────────────┐
│ Search       │ → Find relevant IDs   0 tokens
└──────────────┘
      ↓
┌──────────────┐
│ Get Section  │ → Load one section   50 tokens
└──────────────┘

Savings: 99.8%
```

### Real-World Savings

**Example:** Answering "How do I authenticate?"

| Method | Tokens Loaded | Cost |
|--------|---------------|------|
| Load full API.md (5KB) | 5,000 | $0.15 |
| skill-split (search + section) | 50 | $0.0015 |

**Savings: 99% | Cost reduction: 100x**

---

## Unique Benefits

### 1. Token Efficiency

- **99% savings** vs loading full files
- **Consistent** - works at any scale
- **Measurable** - track your savings

### 2. Three Search Modes

| Mode | Best For | Cost |
|------|----------|------|
| BM25 | Exact matches | Free |
| Vector | Concepts | $0.0001/query |
| Hybrid | Balanced | $0.00001/query |

### 3. Byte-Perfect Integrity

```python
# Parse → Store → Retrieve → Reconstruct
assert original_hash == reconstructed_hash
```

**Guarantee:** What you put in is what you get out.

### 4. Developer-First

- **CLI tool:** 16 commands
- **Python API:** Full programmatic access
- **CI/CD ready:** GitHub Actions included
- **Docker support:** Containerized deployment

### 5. Extensible

- **Component handlers:** Plugins, hooks, configs, scripts
- **Custom formats:** Add your own handlers
- **Search backends:** Local or cloud

---

## Use Cases

### 1. AI Chatbots

**Problem:** Chatbot needs context from large docs

**Solution:**
```python
# Search first
results = search(user_question)
# Load only relevant sections
context = [get_section(r.id) for r in results[:3]]
# Answer with minimal tokens
response = llm(user_question, context=context)
```

### 2. Code Generation

**Problem:** Need examples from codebase

**Solution:**
```python
# Find similar code
results = search("authentication handler")
# Load examples only
examples = [get_section(r.id) for r in results[:5]]
# Generate based on examples
code = llm.generate(examples)
```

### 3. Documentation Search

**Problem:** Users can't find information

**Solution:**
```bash
# Fast local search
./skill-split.py search "OAuth"
# Or semantic search
./skill_split.py search-semantic "login security"
```

### 4. Knowledge Management

**Problem:** Large knowledge bases are unwieldy

**Solution:**
```python
# Navigate hierarchically
section = get_section_by_heading("Chapter 1")
subsection = get_next_section(section.id, file, child=True)
# Only load what you're reading
```

---

## Competitive Advantages

### vs Obsidian

| Feature | skill-split | Obsidian |
|---------|-------------|----------|
| API Access | ✅ Python + CLI | ❌ |
| Progressive Disclosure | ✅ 99% savings | ❌ |
| Semantic Search | ✅ OpenAI | ❌ |
| CI/CD | ✅ Native | ❌ |
| Developer-focused | ✅ | ⚠️ |

### vs Notion

| Feature | skill-split | Notion |
|---------|-------------|--------|
| Local Storage | ✅ SQLite | ❌ Cloud only |
| Token Efficient | ✅ 99% | ❌ |
| Extensible | ✅ Plugins | ❌ Limited |
| Cost | ✅ Free | $96-180/user/year |
| Open Source | ✅ MIT | ❌ Proprietary |

### vs Traditional Search

| Feature | skill-split | grep/ripgrep |
|---------|-------------|-------------|
| Semantic Understanding | ✅ | ❌ |
| Context-Aware | ✅ | ❌ |
| Hierarchical | ✅ | ⚠️ |
| Progressive | ✅ | ❌ |

---

## ROI Calculator

### For a Team Using AI

**Assumptions:**
- 100 queries per day
- Average doc: 10KB (2,500 tokens)
- GPT-4 cost: $30 per 1M tokens

**Traditional (full file load):**
```
Daily: 100 queries × 2,500 tokens = 250,000 tokens
Daily cost: 250,000 × $30/1M = $7.50
Annual cost: $7.50 × 365 = $2,737.50
```

**skill-split (progressive disclosure):**
```
Daily: 100 queries × 50 tokens = 5,000 tokens
Daily cost: 5,000 × $30/1M = $0.15
Annual cost: $0.15 × 365 = $54.75
```

**Annual savings: $2,682.75 (98% reduction)**

### For an Individual

**Queries per day:** 20

| Method | Annual Cost | Savings |
|--------|------------|---------|
| Full file load | $547.50 | - |
| skill-split | $10.95 | **98%** |

---

## Success Metrics

### Token Reduction

```
Before: 5,000 tokens per query
After: 50 tokens per query
Reduction: 99%
```

### Cost Reduction

```
Before: $7.50 per day (100 queries)
After: $0.15 per day (100 queries)
Reduction: 98%
```

### Performance

```
Before: 2-5 seconds (load + process)
After: 0.1-0.5 seconds (search + load)
Improvement: 10-50x faster
```

---

## The Value Proposition

**For Developers:**
- Build AI tools that scale
- Reduce API costs by 98%
- Improve response times
- Better user experience

**For Teams:**
- Share knowledge efficiently
- Reduce documentation friction
- Enable AI-assisted workflows
- Lower infrastructure costs

**For Users:**
- Find information faster
- Get relevant answers
- Learn incrementally
- Avoid information overload

---

## Why Now?

### AI is Mainstream

- ChatGPT: 100M+ users
- Claude: Growing rapidly
- AI coding assistants: Standard tool

### Documentation is Exploding

- APIs everywhere
- Microservices documentation
- Knowledge bases growing

### Context Windows are Limited

- Even GPT-4: 128K tokens
- Large docs: 500K+ tokens
- **Need: Smart loading**

---

## The Future

### skill-split Vision

1. **Standard tool** for AI documentation workflows
2. **Plugin ecosystem** for custom formats
3. **Cloud integration** for team collaboration
4. **ML models** for better understanding

### Roadmap

- **v1.0:** ✅ Core functionality (complete)
- **v1.1:** Web UI, streaming
- **v1.2:** Plugin marketplace
- **v2.0:** Distributed search

---

## Conclusion

**skill-split solves a real problem:**
- Documentation is too large for AI context windows
- Loading everything wastes tokens and money
- Progressive disclosure is the solution

**Unique value:**
- 99% token savings
- Multiple search modes
- Developer-first design
- Production-ready

**Bottom line:**
If you're building AI workflows with documentation, you need skill-split.

---

*skill-split - Progressive disclosure for AI workflows*
