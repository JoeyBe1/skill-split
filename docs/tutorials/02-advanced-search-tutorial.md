# Advanced Search with skill-split - Video Tutorial Script

**Video Title**: Advanced Search: BM25, Vector, and Hybrid Search in skill-split
**Target Length**: ~15 minutes
**Target Audience**: Developers who completed Getting Started tutorial
**Difficulty Level**: Intermediate

---

## Video Metadata

- **Total Duration**: 15:00
- **Prerequisites**: Completed "Getting Started with skill-split"
- **Recording Date**: [Fill in when recording]
- **Presenter**: [Your Name]

---

## Equipment & Setup Requirements

**For Recording:**
- Screen resolution: 1920x1080 (minimum)
- Terminal with command history
- Browser with Supabase dashboard (optional)
- Text editor for configuration files

**Demo Environment:**
- skill-split installed and configured
- Sample database with multiple files
- OpenAI API key (for vector search demo)
- Supabase project (for vector storage demo)

---

## Script

### [0:00] - Intro & Overview

**Visual**: Title card with three search icons: BM25, Vector, Hybrid

**Audio**:
> "Welcome back! In our previous video, we covered the basics of skill-split - parsing, storing, and retrieving sections. Today, we're diving deep into search capabilities."

**Visual**: Three-column comparison graphic
```
┌─────────┬──────────────┬─────────────┐
│  BM25   │    Vector    │   Hybrid    │
│ Keywords│  Semantic    │   Combined  │
│   Fast  │   Smart      │    Best     │
│  Local  │ Requires API │  Tunable    │
└─────────┴──────────────┴─────────────┘
```

**Audio**:
> "skill-split offers three powerful search modes: BM25 for exact keyword matching, Vector search for semantic understanding, and Hybrid search that combines both for the best results. We'll explore each one, show you when to use them, and demonstrate real-world performance differences."

---

### [1:15] - BM25 Search: The Foundation

**Visual**: Terminal showing search command

**Audio**:
> "Let's start with BM25 search, the foundation of skill-split's search capabilities. BM25 is a ranking function used in full-text search that estimates the relevance of documents to a search query."

**Terminal Commands**:
```bash
./skill_split.py search "python handler"
```

**Visual**: Output showing ranked results with scores

**Audio**:
> "The search returns ranked results with BM25 relevance scores. Higher scores indicate better matches. Notice how sections containing both 'python' and 'handler' appear at the top."

**Screen Text** (explain scores):
```
BM25 Score Interpretation:
- 3.0+ : Excellent match (both terms, high frequency)
- 2.0-3.0 : Good match (both terms, moderate frequency)
- 1.0-2.0 : Fair match (one term, high frequency)
- <1.0 : Weak match (one term, low frequency)
```

**Audio**:
> "BM25 scores are based on term frequency - how often the search terms appear in the section - and inverse document frequency - how unique those terms are across all sections. This means rare but relevant terms get higher scores."

---

### [2:45] - BM25 Query Syntax

**Visual**: Terminal with various search examples

**Audio**:
> "BM25 search supports powerful query syntax. Let's explore the different options:"

**Example 1 - Single word**:
```bash
./skill_split.py search "authentication"
```
**Audio**:
> "Single word searches find exact matches. Simple and direct."

**Example 2 - Multi-word (OR)**:
```bash
./skill_split.py search "git setup"
```
**Audio**:
> "Multi-word searches use OR logic by default. This finds sections with 'git' OR 'setup', which is great for discovery when you're not sure of the exact terms."

**Example 3 - Exact phrase**:
```bash
./skill_split.py search '"python handler"'
```
**Audio**:
> "Use quotes for exact phrase matching. This finds sections containing the exact phrase 'python handler' in that order."

**Example 4 - AND search**:
```bash
./skill_split.py search "python AND testing"
```
**Audio**:
> "Explicit AND searches require both terms. This is more restrictive and gives narrower, more focused results."

**Example 5 - NEAR search**:
```bash
./skill_split.py search "git NEAR repository"
```
**Audio**:
> "NEAR searches find terms within proximity of each other. The exact distance depends on your SQLite configuration, but typically within a few sentences."

**Example 6 - Complex queries**:
```bash
./skill_split.py search '"python handler" OR configuration'
```
**Audio**:
> "You can combine operators for complex searches. This finds the exact phrase 'python handler' OR any sections about configuration."

---

### [4:30] - BM25 Performance Characteristics

**Visual**: Performance metrics dashboard

**Audio**:
> "Let's talk about BM25 performance. BM25 search is incredibly fast because it runs locally using SQLite's FTS5 full-text search engine."

**Screen Text** (performance data):
```
BM25 Performance Metrics:
- Query Latency: 5-50ms
- Index Size: ~10% of original text
- Setup Time: Instant (built during store)
- API Required: No
- Cost: Free
```

**Audio**:
> "Typical queries complete in 5-50 milliseconds, even across thousands of sections. The full-text index is built automatically when you store files, requiring no additional setup."

**Audio**:
> "BM25 is ideal when you know the exact keywords, need fast results, or don't have API keys configured. It's the workhorse of everyday search."

---

### [5:30] - When to Use BM25

**Visual**: Decision tree graphic

**Audio**:
> "Here's when to choose BM25 search:"

**Screen Text** (use cases):
```
Use BM25 When:
✓ You know exact keywords
✓ Need fast local search
✓ No API keys available
✓ Boolean operators needed
✓ Searching technical terms
✓ Exact phrase matching

Avoid BM25 When:
✗ Need semantic understanding
✗ Terms vary in wording
✗ Concept-based search needed
✗ Synonyms should match
```

**Audio**:
> "BM25 excels at technical searches where terminology is precise - like API names, function signatures, or configuration keys. It struggles when meaning matters more than exact words."

---

### [6:15] - Vector Search: Semantic Understanding

**Visual**: Animated vector space diagram with words plotted

**Audio**:
> "Now let's explore vector search, which brings semantic understanding to your queries. Instead of matching exact words, vector search understands meaning and concepts."

**Audio**:
> "Vector search works by converting text into numerical embeddings - multi-dimensional vectors that capture semantic meaning. Similar concepts end up close together in vector space, even if they use different words."

**Screen Text** (concept example):
```
Query: "code execution"

Vector Search Finds:
- "running scripts" ✓
- "execute commands" ✓
- "process execution" ✓
- "command runner" ✓

BM25 Would Miss:
- "running scripts" ✗ (no exact word match)
- "execute commands" ✗ (no exact word match)
```

**Audio**:
> "This is powerful for discovering related content that uses different terminology. When you search for 'code execution', vector search finds sections about 'running scripts' and 'execute commands' - concepts that mean the same thing without sharing exact words."

---

### [7:30] - Setting Up Vector Search

**Visual**: Terminal showing configuration

**Audio**:
> "Vector search requires some setup. You'll need an OpenAI API key for generating embeddings and a Supabase project for storing vectors."

**Terminal Commands** (setting environment variables):
```bash
export OPENAI_API_KEY="sk-your-key-here"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_PUBLISHABLE_KEY="your-anon-key"
export ENABLE_EMBEDDINGS=true
```

**Audio**:
> "Set these environment variables, then enable embeddings. You can also add them to your `.env` file for persistence."

**Visual**: .env file example

**Audio**:
> "Once configured, vector search is ready to use. The first search automatically generates embeddings for any sections that don't have them yet."

---

### [8:15] - Vector Search Commands

**Visual**: Terminal with vector search examples

**Audio**:
> "Vector search uses the `search-semantic` command. Let's try it:"

**Terminal Commands**:
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 1.0
```

**Visual**: Output showing semantic search results

**Audio**:
> "The `--vector-weight 1.0` flag specifies pure vector search. Results show similarity scores from 0 to 1, where 1 is perfect semantic match."

**Audio**:
> "Notice how the results include conceptually related content even without exact word matches. This is the power of semantic search."

**Terminal Commands** (another example):
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "error handling" --vector-weight 1.0
```

**Audio**:
> "Search for 'error handling' and you'll find sections about exceptions, debugging, troubleshooting, and error recovery - all related concepts without sharing the exact phrase."

---

### [9:30] - Vector Search Performance & Costs

**Visual**: Cost breakdown graphic

**Audio**:
> "Vector search has costs to consider. Let's break down the economics:"

**Screen Text** (cost breakdown):
```
Vector Search Costs:

One-Time Setup:
- Generate embeddings: ~$0.08 for 19K sections
- Database storage: ~$3-5/month additional

Ongoing Monthly:
- New section embeddings: ~$0.0001
- Search queries: ~$0.03 for 100 queries/day

Total Monthly: $0.03-0.05
```

**Audio**:
> "The good news is that vector search is very affordable. Initial setup costs about eight cents for a library of 19,000 sections. Monthly ongoing costs are typically three to five cents even with active usage."

**Screen Text** (performance metrics):
```
Vector Search Performance:
- Query Latency: 20-50ms
- Setup Time: ~5 minutes (initial embeddings)
- API Required: Yes (OpenAI)
- Relevance Improvement: 40-60% over BM25
```

**Audio**:
> "Performance is excellent at 20-50 milliseconds per query. The main tradeoff is the requirement for API keys and initial setup time for generating embeddings."

---

### [10:15] - When to Use Vector Search

**Visual**: Comparison graphic

**Audio**:
> "Vector search shines in specific scenarios:"

**Screen Text** (use cases):
```
Use Vector Search When:
✓ Meaning matters more than exact words
✓ Synonyms should match
✓ Exploring concepts
✓ API keys configured
✓ Discovering related content
✓ Natural language queries

Avoid Vector Search When:
✗ Need exact keyword matches
✗ No API keys available
✗ Searching technical identifiers
✗ Need boolean operators
```

**Audio**:
> "Choose vector search when you're exploring concepts, not hunting for exact terms. It's perfect for natural language queries like 'how do I handle errors' versus exact searches like 'error handling function'."

---

### [11:00] - Hybrid Search: Best of Both Worlds

**Visual**: Animated diagram showing BM25 + Vector = Hybrid

**Audio**:
> "Hybrid search combines BM25 keyword matching with vector semantic understanding, giving you the best of both approaches. It's the recommended default for most use cases."

**Terminal Commands**:
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "python error handling" --vector-weight 0.7
```

**Audio**:
> "The `--vector-weight 0.7` means 70% semantic, 30% keyword. This balanced approach captures both exact terminology and conceptual meaning."

---

### [11:45] - Tuning Vector Weight

**Visual**: Slider graphic showing 0.0 to 1.0 scale

**Audio**:
> "The vector weight parameter lets you tune the balance between semantic and keyword matching:"

**Screen Text** (weight guide):
```
Vector Weight Tuning:

1.0 = Pure Vector (semantic only)
     Best for: Concept exploration, natural language

0.7 = Hybrid Recommended (70% semantic, 30% keyword)
     Best for: General purpose, balanced results

0.5 = Equal Balance (50% each)
     Best for: Uncertain intent, discovery

0.3 = Keyword-Focused (30% semantic, 70% keyword)
     Best for: Technical terms with some flexibility

0.0 = Pure BM25 (keyword only)
     Best for: Exact matches, no API needed
```

**Audio**:
> "Start with 0.7 for general use. Adjust toward 1.0 for more semantic discovery, or toward 0.0 for more precise keyword matching."

---

### [12:30] - Performance Comparison: Real-World Demo

**Visual**: Split screen showing three search types for same query

**Audio**:
> "Let's see all three search types in action with the same query to understand the differences:"

**Query**: "managing git repositories"

**Terminal** (BM25):
```bash
./skill_split.py search "managing git repositories"
```
**Results**: Exact phrase matches only

**Terminal** (Vector):
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "managing git repositories" --vector-weight 1.0
```
**Results**: Semantic matches (version control, code management, repo handling)

**Terminal** (Hybrid):
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "managing git repositories" --vector-weight 0.7
```
**Results**: Combined exact and semantic matches

**Audio**:
> "Notice the difference. BM25 finds only exact matches. Vector discovers related concepts. Hybrid gives you both, ranked by combined relevance."

---

### [13:15] - Search Tips & Best Practices

**Visual**: Tips checklist

**Audio**:
> "Here are my top tips for effective searching with skill-split:"

**Screen Text** (tips):
```
Search Best Practices:

1. Start with BM25 for exact keyword searches
2. Use Hybrid (0.7) for general discovery
3. Use Vector (1.0) for concept exploration
4. Quote phrases for exact matching: '"exact phrase"'
5. Use AND for narrow results: "term1 AND term2"
6. Use OR (default) for broad discovery
7. Adjust vector weight based on results
8. Search before loading sections (token savings)
```

**Audio**:
> "Remember: search first, then load. This progressive disclosure approach is where the real token savings happen. Find the right sections, then retrieve only what you need."

---

### [13:45] - Summary & Next Steps

**Visual**: Summary table

**Audio**:
> "Let's recap the three search modes:"

**Screen Text** (comparison table):
```
┌───────────┬──────────┬──────────┬────────────┐
│           │   BM25   │  Vector  │   Hybrid   │
├───────────┼──────────┼──────────┼────────────┤
│ Best For  │ Keywords │ Semantic │ Combined   │
│ Speed     │ 5-50ms   │ 20-50ms  │ 30-100ms   │
│ Cost      │ Free     │ $0.03/mo │ $0.03/mo   │
│ API       │ None     │ OpenAI   │ OpenAI     │
│ Operators │ AND/OR/  │ None     │ BM25 ops   │
│           │ NEAR     │          │ + semantic │
│ Relevance │ 60%      │ 85-95%   │ 95%+       │
│ Default   │ Yes      │ No       │ Recommended│
└───────────┴──────────┴──────────┴────────────┘
```

**Audio**:
> "Choose BM25 for fast, exact keyword searches. Use Vector when meaning matters more than words. Default to Hybrid for the best overall results."

**Visual**: Next steps slide

**Audio**:
> "In the next video, we'll cover integration techniques - using skill-split as a Python package in your applications, setting up CI/CD workflows, and building custom search pipelines."

---

### [14:30] - End Card

**Visual**: End card with links

**Audio**:
> "Thanks for watching! Check out the resources below for more information, and join the discussion on GitHub. Happy searching!"

**Screen Text**:
```
Resources:
- Vector Search Costs: docs/VECTOR_SEARCH_COSTS.md
- CLI Reference: docs/CLI_REFERENCE.md
- Examples: EXAMPLES.md
- GitHub Issues: Report bugs and request features

Previous: Getting Started Tutorial
Next: Integration Tutorial
```

---

## Post-Production Notes

**Visual Elements to Add:**
- [ ] Animated vector space visualization
- [ ] Side-by-side search result comparisons
- [ ] Performance metrics overlays
- [ ] Cost calculator animation
- [ ] Color-coded result highlighting (BM25=blue, Vector=green, Hybrid=purple)

**Audio Enhancements:**
- [ ] Subtle whoosh for search transitions
- [ ] Different audio tone for each search type
- [ ] Emphasis on key metrics
- [ ] Closed captions for technical terms

**Editing Checklist:**
- [ ] Synchronize terminal output with narration
- [ ] Add zoom highlights for score explanations
- [ ] Create chapter markers for each search type
- [ ] Include pause points for viewer comprehension

---

## Demo Data Preparation

Before recording, prepare a test database with diverse content:

```bash
# Create sample files
cat > /tmp/test_skill1.md << 'EOF'
---
name: git-skills
description: Git version control patterns
version: 1.0.0
---

# Git Repository Management

## Clone Repository

Clone a remote repository to your local machine.

## Initialize New Repo

Start a new version control project.

## Branch Management

Create and switch between branches for parallel development.

## Commit Workflow

Stage changes and create commits with meaningful messages.

EOF

cat > /tmp/test_skill2.md << 'EOF'
---
name: error-handling
description: Python error patterns
version: 1.0.0
---

# Exception Handling

## Try-Except Blocks

Catch and handle runtime exceptions gracefully.

## Debugging Techniques

Debug code and identify error sources.

## Logging Strategy

Implement logging for troubleshooting and monitoring.
EOF

# Store files
./skill_split.py store /tmp/test_skill1.md
./skill_split.py store /tmp/test_skill2.md
```

---

## Search Query Examples for Demo

Prepare these queries in advance:

**BM25 Examples:**
```bash
./skill_split.py search "repository"
./skill_split.py search "git AND branch"
./skill_split.py search '"python handler"'
./skill_split.py search "git NEAR repository"
```

**Vector Examples:**
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 1.0
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "managing code versions" --vector-weight 1.0
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "troubleshooting errors" --vector-weight 1.0
```

**Hybrid Examples:**
```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "git branch" --vector-weight 0.7
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "exception handling" --vector-weight 0.5
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "version control repository" --vector-weight 0.7
```

---

## Recording Tips

1. **Pre-compute Embeddings**: Generate vector embeddings before recording to avoid waiting during demo
2. **Clear Terminal**: Start each section with a clear terminal for clarity
3. **Highlight Scores**: Use terminal color or overlays to highlight relevance scores
4. **Compare Results**: Show same query across all three search types for comparison
5. **Explain Ranks**: Pause to explain why results are ranked certain ways
6. **Cost Transparency**: Show actual cost breakdown from your usage

---

## Troubleshooting Common Issues

**Embeddings Generation Fails:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Verify Supabase connection
./skill_split.py status
```

**Vector Search Falls Back to BM25:**
```bash
# Verify embeddings enabled
echo $ENABLE_EMBEDDINGS

# Check section has embeddings
./skill_split.py search-semantic "test" --vector-weight 1.0
```

**Slow First Search:**
```bash
# First search generates embeddings for all sections
# Subsequent searches will be fast
```

---

## Related Videos in Series

1. **Getting Started** - Installation and basic usage
2. **Advanced Search** (this video) - BM25, Vector, and Hybrid search
3. **Integration Tutorial** - Python package usage and CI/CD integration

---

*Last Updated: 2026-02-10*
*Script Version: 1.0*
