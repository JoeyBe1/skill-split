# Hacker News: Show HN

**URL**: https://news.ycombinator.com/submit

---

## Title

```
Show HN: Section-level SQLite library for Claude Code skills (99% token savings)
```

---

## Body

```
I built skill-split to solve a concrete problem with large Claude Code skill libraries: loading full skill files into context is expensive. A typical skill file runs 15–21KB. Multiply that by a dozen skills and you've burned most of your context window before the task starts.

skill-split parses every section of every skill, command, plugin, hook, and script into a SQLite database. Sections average around 200 bytes. Search returns section IDs; you retrieve exactly what you need. Round-trip is byte-perfect — the original file reconstructs exactly from the stored sections. I've tested this on 1,365 files (19,207 sections) with SHA256 verification.

The stack is intentionally minimal: Python, SQLite with FTS5 for BM25 keyword search, and optional OpenAI embeddings for hybrid semantic search. No server required for the core workflow. Checkout deploys individual sections to their target paths; checkin tracks what's deployed. There's also a compose command to assemble new skills from sections across different source files.

Repo: https://github.com/JoeyBe1/skill-split
```

---

## Submission Notes

- Show HN posts perform best on weekdays between 9am–12pm Eastern
- Keep the title under 80 characters (current: 68 chars — good)
- Do not edit the title after submission (HN penalizes edits)
- Post the body text as your first comment immediately after submitting
- Respond to every early comment to drive ranking
- Do not ask for upvotes
