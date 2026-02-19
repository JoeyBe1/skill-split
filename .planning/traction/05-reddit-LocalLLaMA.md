# Reddit Post: r/LocalLLaMA

**Subreddit**: r/LocalLLaMA
**URL**: https://www.reddit.com/r/LocalLLaMA/

---

## Title

```
Section-level SQLite index for LLM skill libraries — 99% token reduction per query
```

---

## Body

```
Context window efficiency is the core constraint on what you can do with a local or API-limited model. I built skill-split to address one specific drain: loading full skill/tool/plugin files into context when you only need one section.

**The problem**: A typical Claude Code skill file is 15–21KB. A library of 50 skills is a megabyte of context you're paying for on every session. Most of that content is irrelevant to the current task.

**The approach**: skill-split parses every section of every file into SQLite (FTS5 with BM25 ranking). A search query returns individual sections averaging ~200 bytes — a 99% reduction vs. loading the full file. You get exactly the relevant section, not the whole document.

The architecture is intentionally offline-first: BM25 keyword search runs fully local with no API calls. If you want semantic search, you can layer in vector embeddings (OpenAI or any compatible endpoint), but the core system requires nothing external. SQLite FTS5 handles multi-word queries with OR logic and supports AND/OR/NEAR boolean operators.

I've validated it against 1,365 files (19,207 sections) with byte-perfect round-trip verification using SHA256. It handles markdown headings, YAML frontmatter, XML tags, Python/JS/TS/shell scripts, and JSON configs — anything structured enough to split into meaningful sections.

Could be adapted for any local LLM skill/tool library beyond Claude Code. The parser and SQLite layer are generic.

Repo: https://github.com/JoeyBe1/skill-split
```

---

## Post Notes

- r/LocalLLaMA audience cares about: token efficiency, offline-first, concrete benchmarks
- Lead with the numbers and the local-first angle — this audience is skeptical of cloud dependencies
- Avoid marketing language; be direct about tradeoffs (e.g., semantic search requires embeddings API)
- Be ready to discuss the BM25 vs. vector tradeoffs in comments
- Post as a text post for better ranking in this sub
