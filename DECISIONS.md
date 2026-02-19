# Architectural Decisions

> Plain-language record of the key choices made in building skill-split — and why.

---

## 1. Store by Section, Not by File

**Decision:** Split every file into its individual sections (headings) and store each one separately.

**Why it matters:** When Claude Code needs to know how to write a hook, it doesn't need the entire 22KB skill file — it needs the 300-byte section titled "Hook Lifecycle." Storing by section means you can load exactly what's relevant.

**The result:** Loading a full skill file costs ~5,400 tokens. Loading one section costs ~75 tokens. That's a **99% reduction** — confirmed on live Anthropic-published skill files (22,827 bytes → 67–317 bytes per section).

**What was sacrificed:** A simpler "store the whole file" approach. The tradeoff is worth it: context windows are finite and expensive.

---

## 2. SQLite, Not a Cloud Database

**Decision:** Use SQLite (a local file database) as the primary store, with optional Supabase cloud sync.

**Why it matters:** Claude Code runs on your machine. A tool that requires internet access, API keys, and a cloud account to function adds friction and failure points. SQLite works with zero infrastructure — the database is a single `.db` file.

**The result:** Install, run, done. No accounts. No latency. No cost per query. Works offline. The optional Supabase path exists for teams who need shared access.

**What was sacrificed:** Real-time sync across machines by default. That's a deliberate choice — local-first, cloud-optional.

---

## 3. BM25 Keyword Search as the Default

**Decision:** Use SQLite's built-in FTS5 full-text search (BM25 ranking) as the default search method.

**Why it matters:** BM25 is the same algorithm that powers Elasticsearch and Solr. It handles multi-word queries, partial matches, and ranking by relevance — with no API keys, no cost, and no latency. Measured on live data: **0.3ms** to search 171 sections across 4 files.

**The result:** Search that works instantly, locally, and for free. Typing `search "progressive disclosure"` returns 9 ranked results before you can blink.

**What was sacrificed:** Semantic understanding ("find things about managing AI context" won't match "context window"). That's addressed by the optional vector/hybrid search layer.

---

## 4. Optional Vector Search, Never Required

**Decision:** Semantic (vector) search using OpenAI embeddings is opt-in, not default. The tool works fully without it.

**Why it matters:** Requiring an OpenAI API key to run a local file management tool is the wrong tradeoff. Most queries are keyword-based. Semantic search is a power feature for edge cases — finding conceptually related content that doesn't share exact words.

**The result:** Zero required API keys. The `ENABLE_EMBEDDINGS=true` flag unlocks semantic search for users who want it. Tests that depend on the `openai` package are automatically skipped in CI when the package isn't installed (`pytest.importorskip`).

**What was sacrificed:** Out-of-the-box semantic search. The install-to-useful path is kept clean.

---

## 5. Byte-Perfect Round-Trip with SHA256 Verification

**Decision:** Every file stored can be reconstructed to the exact original — byte for byte. Every reconstruction is verified with a SHA256 hash.

**Why it matters:** A tool that modifies your files without you knowing is a liability, not an asset. The round-trip guarantee means skill-split can be used without fear: what goes in comes out identical.

**The result:** Tested on 92-section files with complex nested structures. The hash match is enforced — a mismatch is an error, not a warning.

**What was sacrificed:** Flexibility to "clean up" or normalize content on storage. That's intentional: the tool stores, not edits.

---

## 6. Progressive Disclosure API

**Decision:** Build a query API designed for incremental loading: search first, then navigate, then load.

**Why it matters:** The typical pattern for retrieving knowledge in an AI session is: "I need something about X" → find the section → read it → maybe go deeper. The API reflects that pattern with three layers: `search_sections()` (find by keyword), `get_section()` (load by ID), `get_next_section()` / `get_section_tree()` (navigate).

**The result:** An AI agent can start with a 5-word query and load only what it needs, never the entire library. This compounds the token savings from Decision 1.

**What was sacrificed:** Simplicity of "just load the whole file." The added API surface is justified by the efficiency gain.

---

## 7. Handlers for Every Claude Code Component Type

**Decision:** Build specialized parsers (handlers) for each Claude Code component: skills, commands, plugins, hooks, configs, Python, JavaScript, TypeScript, and shell scripts.

**Why it matters:** Claude Code's component ecosystem is heterogeneous. A plugin's `plugin.json` has different structure than a `SKILL.md`. A Python file has classes and methods; a shell script has function blocks. Treating them all as generic markdown loses the structure.

**The result:** 10 handler types, each producing properly structured sections with correct hierarchy. A TypeScript file gets its interfaces, classes, and methods as individually queryable sections.

**What was sacrificed:** A simpler "one parser for everything" approach. The complexity is contained in the handler layer and tested independently (623 tests, all passing).

---

*Numbers above come from live measurements against publicly available Anthropic-published skill files from the `anthropics/claude-code` repository.*
