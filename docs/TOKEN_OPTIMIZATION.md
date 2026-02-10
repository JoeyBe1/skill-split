# skill-split Token Optimization Guide

**Maximize token efficiency in AI workflows**

---

## The Token Problem

AI models have context limits:
- **GPT-4:** 128K tokens (~$50 per 1M tokens)
- **Claude Opus:** 200K tokens (~$15 per 1M tokens)
- **GPT-3.5:** 16K tokens (~$0.50 per 1M tokens)

Loading large documentation wastes tokens and money.

---

## skill-split Solution

### Progressive Disclosure

Load only what you need, when you need it.

```
Traditional Approach:
┌─────────────────────────────────┐
│  Load entire file (2,500 tokens) │
└─────────────────────────────────┘

skill-split Approach:
┌─────────────┐
│  Search     │ → Find relevant section IDs
└─────────────┘
       ↓
┌─────────────┐
│  Get section│ → Load 1 section (25 tokens)
└─────────────┘

Savings: 99%
```

### Real-World Example

**File:** `API.md` (695 lines, ~20KB)

**Traditional:**
- Load entire file: ~5,000 tokens
- Cost per query: ~$0.75 (GPT-4)

**skill-split:**
1. Search: "authentication" → Find section ID
2. Get section: 42 → Load 50 tokens
3. Cost per query: ~$0.0075 (GPT-4)

**Savings:** 99% | **Cost reduction:** 100x

---

## Optimization Strategies

### 1. Search First, Load Later

```python
# Bad: Load everything
with open("large_doc.md") as f:
    content = f.read()  # 25,000 tokens
    # Process content

# Good: Search first
results = search("specific topic")  # 0 tokens
section_id = results[0].id
section = get_section(section_id)  # 50 tokens
# Process section
```

### 2. Use Hierarchical Navigation

```python
# Start with top-level
section = get_section_by_heading("Chapter 1")  # 50 tokens

# Drill down as needed
if needs_detail:
    subsection = get_next_section(section.id, file, child=True)  # 30 tokens

# Savings: Only load what you need
```

### 3. Batch Similar Queries

```python
# Bad: Multiple loads
for topic in topics:
    section = search_and_load(topic)  # 50 tokens each

# Good: Load once, process multiple times
section = load_section(section_id)  # 50 tokens once
for topic in topics:
    process(section, topic)  # Reuse loaded section
```

### 4. Cache Frequently Used Sections

```python
# In-memory cache
CACHE = {}

def get_section_cached(section_id):
    if section_id not in CACHE:
        CACHE[section_id] = get_section(section_id)
    return CACHE[section_id]

# Subsequent loads: 0 tokens
```

### 5. Summarize Before Loading

```python
# Get metadata first
section = get_section_metadata(section_id)  # 5 tokens
size = section.content_length

# Only load if reasonable
if size < 1000:
    content = get_section(section_id)  # 50 tokens
else:
    summary = get_summary(section_id)  # 100 tokens
```

---

## Search Strategy

### BM25 Search (Keyword)

**Best for:** Exact matches, code references, specific terms

```bash
# Fast, no API cost
./skill_split.py search "authentication error"
```

**Token cost:** 0 (local search)

### Vector Search (Semantic)

**Best for:** Concepts, ideas, related topics

```bash
# Finds related concepts
./skill_split.py search-semantic "security" --vector-weight 1.0
```

**Token cost:** 10 (for query embedding)

### Hybrid Search (Balanced)

**Best for:** General queries, relevance ranking

```bash
# Combines both
./skill_split.py search-semantic "login" --vector-weight 0.7
```

**Token cost:** 10 (for query embedding)

---

## Workflow Patterns

### Pattern 1: Question Answering

```python
# User question: "How do I authenticate?"

# Step 1: Search (0 tokens)
results = search("authenticate")

# Step 2: Get best match (50 tokens)
section = get_section(results[0].id)

# Step 3: Answer with context
answer = llm(f"Answer using this: {section.content}")
```

**Total tokens:** ~60 (vs 5,000 for full file)

### Pattern 2: Code Generation

```python
# Task: Generate code for specific feature

# Step 1: Search for similar code (0 tokens)
results = search("authentication handler python")

# Step 2: Get examples (150 tokens for 3 sections)
examples = [get_section(r.id).content for r in results[:3]]

# Step 3: Generate code
code = llm(f"Generate code based on: {examples}")
```

**Total tokens:** ~170 (vs 15,000 for full codebase)

### Pattern 3: Documentation Update

```python
# Task: Update API documentation

# Step 1: Find relevant section (0 tokens)
section = get_section_by_heading("Authentication API")

# Step 2: Load section (50 tokens)
content = get_section(section.id).content

# Step 3: Generate update
updated = llm(f"Update this: {content}")

# Step 4: Store updated section
update_section(section.id, updated.content)
```

**Total tokens:** ~60 (vs 5,000 for full doc)

---

## Cost Calculator

### Estimates per 1K Queries

| Method | Tokens per Query | Total Tokens | Cost (GPT-4) |
|--------|------------------|--------------|---------------|
| Load full file (5KB) | 5,000 | 5,000,000 | ~$150 |
| BM25 + load section | 50 | 50,000 | ~$1.50 |
| Hybrid + load section | 60 | 60,000 | ~$1.80 |

**Savings:** 98-99% | **Cost reduction:** 80-100x

### Annual Savings

Assumptions:
- 1,000 queries per day
- Average file: 5KB
- Full file cost: $0.15 per query

| Method | Daily Cost | Annual Cost |
|--------|------------|-------------|
| Load full file | $150 | **$54,750** |
| skill-split | $1.50 | **$547** |

**Annual savings: $54,203**

---

## Best Practices

### DO:
✅ Search before loading
✅ Use progressive disclosure
✅ Cache frequently accessed sections
✅ Batch similar operations
✅ Use BM25 for exact matches
✅ Load metadata first when possible

### DON'T:
❌ Load entire files by default
❌ Skip the search step
❌ Load sections you won't use
❌ Re-load the same section multiple times
❌ Use vector search for exact matches
❌ Ignore content size

---

## Implementation Examples

### Claude Code Integration

```python
# In your Claude Code workflow

from skill_split import SkillSplit
ss = SkillSplit()

# When asked about code
def find_relevant_code(query):
    # Search first
    results = ss.search(query)

    # Load only top matches
    sections = [ss.get_section(r.id) for r in results[:3]]

    # Return minimal context
    return "\n\n".join(s.content for s in sections)
```

### AI Assistant Integration

```python
# For AI/LLM applications

def get_context(query):
    """Get minimal context for query."""
    # Search
    results = hybrid_search(query, limit=5)

    # Load sections
    sections = [get_section(r.id) for r in results]

    # Return as context
    return {
        "query": query,
        "context": sections,
        "tokens": sum(len(s.content) for s in sections)
    }
```

---

## Summary

**Key takeaways:**
1. **Search first** - Find what you need before loading
2. **Load specific** - Only load relevant sections
3. **Cache aggressively** - Reuse loaded sections
4. **Use right search** - BM25 for exact, Vector for concepts
5. **Monitor usage** - Track token consumption

**With skill-split, you can:**
- Reduce token usage by 99%
- Cut costs by 100x
- Improve response times
- Scale to larger documentation sets

---

**Progressive disclosure is the key to efficient AI workflows.**

---

*skill-split - Progressive disclosure for AI workflows*
