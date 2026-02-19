# Reddit Post: r/ClaudeAI

**Subreddit**: r/ClaudeAI
**URL**: https://www.reddit.com/r/ClaudeAI/

---

## Title

```
I built a section-level skill library for Claude Code — 99% token savings
```

---

## Body

```
If you use Claude Code with a large skill or command library, you've probably run into the context tax: loading a full 21KB skill file to answer one question burns thousands of tokens before you've even started the task. I built skill-split to fix that.

**skill-split** stores every section of every skill, command, plugin, hook, and script in a SQLite database. Search returns individual sections — around 200 bytes each — instead of entire files. That's where the 99% token savings number comes from: you get exactly what you need, nothing more.

The workflow is: search with a keyword or semantic query, get back the matching section ID, check it out to a target directory, and use it. You can also compose new skills by assembling sections from different files. It handles YAML frontmatter, markdown headings, XML tags, Python/JS/TS/shell scripts, and Claude Code-specific formats like plugin.json and hooks.json.

I've ingested 1,365 skill files (19,207 sections) and verified byte-perfect round-trips. Runs fully local with SQLite — no external services required for the core search.

Repo: https://github.com/JoeyBe1/skill-split
```

---

## Post Notes

- Post as a text post, not a link post (more engagement)
- Cross-post to r/ClaudeDev if that sub exists
- Reply to early comments quickly to boost ranking
- If the post gets traction, pin a comment with the demo GIF link once it's recorded
