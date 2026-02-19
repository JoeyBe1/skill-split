# Demo GIF Script

Record this sequence for the README demo GIF. Each command should run and show real output before moving to the next.

---

## Recording Setup

**Recommended tools:**
- `asciinema` — records as text/JSON, plays back in browser, embeds in README via asciinema.org
- `ttygif` — converts terminal session to GIF directly

**asciinema quickstart:**
```bash
# Install
pip install asciinema

# Record
asciinema rec demo.cast

# (run the commands below, then Ctrl+D to stop)

# Upload to asciinema.org
asciinema upload demo.cast

# Or convert to GIF locally (requires agg)
agg demo.cast demo.gif
```

**ttygif quickstart:**
```bash
# Install (macOS)
brew install ttyrec ttygif

# Record
ttyrec demo.rec

# (run the commands below, then exit)

# Convert to GIF
ttygif demo.rec -f
```

---

## Commands to Run (in order)

### Step 1: Search the library
```bash
./skill_split.py search "python handler" --db ~/.claude/databases/skill-split.db
```
Expected output: BM25 ranked results showing section IDs, titles, and snippet previews.

### Step 2: Retrieve a specific section
```bash
./skill_split.py get-section <ID> --db ~/.claude/databases/skill-split.db
```
Replace `<ID>` with an ID from the Step 1 results. Expected output: The full section content — title, body, metadata.

### Step 3: Browse the library
```bash
./skill_split.py list-library --db ~/.claude/databases/skill-split.db | head -10
```
Expected output: First 10 files in the library with section counts.

### Step 4: Check out a section to disk
```bash
./skill_split.py checkout <ID> --target /tmp/demo-checkout --db ~/.claude/databases/skill-split.db
```
Replace `<ID>` with the same ID from Step 2. Expected output: File written to `/tmp/demo-checkout/`.

---

## GIF Production Notes

- Target duration: 30–45 seconds total
- Use a clean terminal with dark theme (Dracula, Nord, or One Dark)
- Set font size to 14–16px for readability in GIF
- Terminal width: 100 columns (to avoid line wrapping)
- Type at a moderate pace — not too fast, not staged-slow
- Pause 1–2 seconds after each command output before typing the next

---

## README Embed

After recording and uploading, add to README.md:

**For asciinema:**
```markdown
[![Demo](https://asciinema.org/a/YOUR_ID.svg)](https://asciinema.org/a/YOUR_ID)
```

**For GIF:**
```markdown
![Demo](demo.gif)
```

Upload the GIF to the repo root or a `/docs/` directory and reference the relative path.
