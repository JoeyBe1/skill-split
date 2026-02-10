# Getting Started with skill-split - Video Tutorial Script

**Video Title**: Getting Started with skill-split: Progressive Disclosure for Documentation
**Target Length**: ~10 minutes
**Target Audience**: Developers, technical writers, Claude Code users
**Difficulty Level**: Beginner

---

## Video Metadata

- **Total Duration**: 10:00
- **Recording Date**: [Fill in when recording]
- **Presenter**: [Your Name]
- **GitHub Repository**: https://github.com/yourusername/skill-split

---

## Equipment & Setup Requirements

**For Recording:**
- Screen resolution: 1920x1080 (minimum)
- Font size: Terminal (14-16pt), Editor (12-14pt)
- Terminal theme: High contrast (dark background, light text)
- Microphone: USB or built-in (clear audio quality)

**Demo Environment:**
- Python 3.8+ installed
- Git clone of skill-split repository
- Terminal application (iTerm2, Terminal.app, or Windows Terminal)
- Text editor (VS Code recommended)

---

## Script

### [0:00] - Intro & Title Card

**Visual**: Title card with skill-split logo, tagline "Intelligent Section Splitting for Progressive Disclosure"

**Audio**:
> "Hi everyone! In this video, I'll show you how to get started with skill-split, a tool that transforms how you work with large documentation files. If you've ever struggled with massive markdown files eating up your token budget, or wished you could search and load just the section you need instead of entire documents, then this tool is for you."

**Visual**: Split screen showing large markdown file on left vs. skill-split section view on right

**Audio**:
> "skill-split intelligently splits your YAML and markdown files into sections, stores them in a lightweight SQLite database, and lets you load exactly what you need through progressive disclosure. The result? Up to 99% reduction in context usage. Let's dive in."

---

### [1:00] - What is Progressive Disclosure?

**Visual**: Animated diagram showing:
1. Large file (50KB) → Arrow → Full Context (expensive)
2. Large file → skill-split → Section Preview → Single Section (204 bytes)

**Audio**:
> "First, let's talk about progressive disclosure. Instead of loading an entire 50-section skill file every time you need information, progressive disclosure lets you see the structure first, then load only the specific sections you need."

**Visual**: Terminal showing tree structure of a file

**Audio**:
> "Think of it like this: You get a table of contents first. Then you click on just the chapter you want to read. For Claude Code workflows, this means massive token savings and more focused interactions."

**Screen Text**:
```
Traditional Approach: 50,000 tokens per query
Progressive Disclosure: 200-500 tokens per query
Savings: 99% context reduction
```

---

### [1:45] - Installation & Setup

**Visual**: Terminal window, clean directory

**Audio**:
> "Let's get skill-split installed. First, clone the repository and navigate to the project directory."

**Terminal Commands**:
```bash
git clone https://github.com/yourusername/skill-split.git
cd skill-split
```

**Audio**:
> "skill-split is written in pure Python with minimal dependencies. Install the requirements:"

**Terminal Commands**:
```bash
pip install -r requirements.txt
```

**Audio**:
> "Verify your installation by checking the help command:"

**Terminal Commands**:
```bash
./skill_split.py --help
```

**Visual**: Output showing all 16 commands organized by category

**Audio**:
> "You should see 16 commands organized into four categories: Core commands for parsing and storage, Query commands for search and navigation, Supabase commands for cloud storage, and Component handlers for plugins and configs."

---

### [3:00] - Your First Parse

**Visual**: Create a sample markdown file

**Audio**:
> "Let's start with a simple example. I've created a sample skill file with multiple sections. Let's parse it to see the structure."

**Terminal Commands**:
```bash
./skill_split.py parse demo/sample_skill.md
```

**Visual**: Output showing file structure with sections and line numbers

**Audio**:
> "The parse command shows us the file structure without storing anything. We can see the YAML frontmatter at the top, followed by sections organized by heading levels. Each section shows its line numbers, so we know exactly where it appears in the original file."

**Screen Text** (highlighted in output):
```
File: demo/sample_skill.md
Type: skill
Format: markdown

Frontmatter:
---
name: sample-skill
description: A demonstration skill
version: 1.0.0
---

Sections:
# Overview
  Lines: 7-15
## Features
  Lines: 17-25
## Installation
  Lines: 27-40
```

**Audio**:
> "Notice how skill-split detected the YAML frontmatter and separated it from the markdown sections. This frontmatter is preserved and can be retrieved independently."

---

### [4:15] - Validation & Round-Trip Integrity

**Visual**: Same terminal window

**Audio**:
> "Before storing any file, it's good practice to validate it. skill-split checks that your file structure is parseable and will survive a round-trip without data loss."

**Terminal Commands**:
```bash
./skill_split.py validate demo/sample_skill.md
```

**Visual**: Output showing validation passed

**Audio**:
> "Great! The file is valid. Now let's verify the round-trip integrity. This confirms that parsing and recomposing produces an exact byte-for-byte match."

**Terminal Commands**:
```bash
./skill_split.py verify demo/sample_skill.md
```

**Visual**: Output showing SHA256 hash comparison

**Audio**:
> "skill-split uses SHA256 hashing to verify integrity. You can see both hashes match exactly. This guarantees zero data loss during the parse-store-recompose cycle. Your formatting, whitespace, and every byte is preserved perfectly."

**Screen Text** (important concept):
```
Byte-Perfect Round-Trip
Original Hash:    3f8c2a91d7e4b5c6a9f1e2d3c4b5a6f7
Recomposed Hash: 3f8c2a91d7e4b5c6a9f1e2d3c4b5a6f7
Match: YES ✓
```

---

### [5:30] - Storing Files in the Database

**Visual**: Terminal window

**Audio**:
> "Now let's store our file in the SQLite database. This enables all the progressive disclosure features."

**Terminal Commands**:
```bash
./skill_split.py store demo/sample_skill.md
```

**Visual**: Output showing file ID, hash, and section count

**Audio**:
> "The file is now stored with a unique file ID and SHA256 hash. skill-split tracks all sections individually, making them available for on-demand retrieval."

**Audio**:
> "By default, skill-split uses a database in your home directory under `.claude/databases/skill-split.db`. You can also specify a custom database with the `--db` flag."

**Terminal Commands**:
```bash
./skill_split.py store demo/sample_skill.md --db ./my_custom.db
```

---

### [6:30] - Exploring Section Structure

**Visual**: Terminal window

**Audio**:
> "Once stored, you can explore the file structure in multiple ways. The `list` command shows all sections with their IDs:"

**Terminal Commands**:
```bash
./skill_split.py list demo/sample_skill.md
```

**Visual**: Output showing section ID, title, and level

**Audio**:
> "Each section has a unique ID that we'll use for retrieval. The level indicates the heading depth, so you can see the hierarchy at a glance."

**Audio**:
> "For a visual tree representation, use the `tree` command:"

**Terminal Commands**:
```bash
./skill_split.py tree demo/sample_skill.md
```

**Visual**: ASCII tree showing nested sections

**Audio**:
> "The tree view makes it easy to understand the document structure before diving into details. This is progressive disclosure in action - structure first, content on demand."

---

### [7:30] - Retrieving Sections

**Visual**: Terminal window

**Audio**:
> "Now the powerful part: retrieving individual sections. Use the `get-section` command with a section ID:"

**Terminal Commands**:
```bash
./skill_split.py get-section 1
```

**Visual**: Output showing just the requested section content

**Audio**:
> "Notice how we get only the content for section 1, not the entire file. This is the token efficiency in action. Instead of loading a 21KB file, we load just 204 bytes - that's a 99% reduction!"

**Screen Text** (token comparison):
```
Full File:  21,000 bytes (~5,250 tokens)
Section 1:    204 bytes (~51 tokens)
Savings: 99% context reduction
```

**Audio**:
> "You can also retrieve specific sections by title using the `get` command:"

**Terminal Commands**:
```bash
./skill_split.py get demo/sample_skill.md "Installation"
```

---

### [8:30] - Navigation & Search

**Visual**: Terminal window

**Audio**:
> "For sequential navigation through a document, use the `next` command. This retrieves the next sibling section:"

**Terminal Commands**:
```bash
./skill_split.py next 1 demo/sample_skill.md
```

**Visual**: Output showing section 2

**Audio**:
> "To drill down into subsections, add the `--child` flag:"

**Terminal Commands**:
```bash
./skill_split.py next 1 demo/sample_skill.md --child
```

**Audio**:
> "For searching across all stored files, use the `search` command with FTS5 full-text search:"

**Terminal Commands**:
```bash
./skill_split.py search "installation"
```

**Visual**: Output showing ranked results with relevance scores

**Audio**:
> "Search results are ranked by relevance using BM25 scoring. You get the most relevant sections first, without loading entire files."

---

### [9:15] - Real-World Use Case

**Visual**: Split screen: Claude Code chat window + terminal

**Audio**:
> "Let's look at a real-world use case. You're working in Claude Code and need to reference a specific part of your documentation. Instead of pasting the entire file, you:"

**Step-by-step overlay**:
```
1. Search: ./skill_split.py search "configuration"
2. List: ./skill_split.py list my-skill.md
3. Retrieve: ./skill_split.py get-section 42
4. Paste: Only the section you need
```

**Audio**:
> "First, search to find relevant sections. Then list the file to see structure. Retrieve the specific section ID. Finally, paste just that section into your conversation. Your token usage drops dramatically, and Claude can focus on the exact context you need."

---

### [9:45] - Summary & Next Steps

**Visual**: Summary slide with key points

**Audio**:
> "To summarize what we've covered:
> - skill-split splits markdown and YAML files into sections
> - Stores them in SQLite for on-demand retrieval
> - Provides progressive disclosure through list, tree, and get commands
> - Offers full-text search across all sections
> - Ensures byte-perfect round-trip integrity"

**Visual**: Next steps slide

**Audio**:
> "In the next video, we'll dive deep into advanced search techniques including BM25 keyword search, vector semantic search, and hybrid search that combines both approaches for the best results."

**Visual**: End card with links

**Audio**:
> "Check out the links below to access the repository, documentation, and join the discussion. Thanks for watching, and happy splitting!"

**Screen Text**:
```
Links:
- GitHub: https://github.com/yourusername/skill-split
- Docs: https://github.com/yourusername/skill-split/blob/main/README.md
- Examples: EXAMPLES.md
- CLI Reference: docs/CLI_REFERENCE.md

Next Video: Advanced Search Tutorial
```

---

## Post-Production Notes

**Visual Elements to Add:**
- [ ] Screen zoom highlights for command outputs
- [ ] Animated transitions between sections
- [ ] Progress bar during video showing time remaining
- [ ] Keyboard shortcut overlays (Cmd/Ctrl + text)

**Audio Enhancements:**
- [ ] Background music (low volume, ambient)
- [ ] Sound effects for section transitions
- [ ] Volume normalization for consistent levels

**Editing Checklist:**
- [ ] Remove pauses and "umms"
- [ ] Add captions/subtitles
- [ ] Include chapter markers for navigation
- [ ] Create thumbnail for video platform

---

## Demo File Preparation

Create the following demo file before recording:

```bash
# File: demo/sample_skill.md
---
name: sample-skill
description: A demonstration skill for getting started
version: 1.0.0
author: Your Name
---

# Overview

This is a sample skill file demonstrating the basic structure
that skill-split can parse and manage.

## Features

- YAML frontmatter detection
- Markdown heading parsing
- Section-level retrieval
- Full-text search capability

## Installation

Install skill-split using pip:

```bash
pip install skill-split
```

Or from source:

```bash
git clone https://github.com/yourusername/skill-split.git
cd skill-split
pip install -e .
```

### Requirements

- Python 3.8 or higher
- Click library
- pytest for testing

## Usage

Basic usage example:

```bash
./skill_split.py parse myfile.md
./skill_split.py store myfile.md
./skill_split.py get myfile.md "Installation"
```

### Advanced Options

See the CLI reference for all available commands and options.

## Troubleshooting

### File not parsing correctly

Ensure your markdown follows standard heading format with # symbols.

### Database errors

Check file permissions and database path configuration.
```

---

## Recording Tips

1. **Terminal Setup**: Use a terminal with visible scrollback history
2. **Font**: Use monospaced font at least 14pt for readability
3. **Color Scheme**: High contrast (dark background, light text)
4. **Window Positioning**: Keep terminal in left 2/3, reserve right 1/3 for overlays
5. **Command Pacing**: Pause 2-3 seconds after each command for viewer comprehension
6. **Error Handling**: If errors occur, explain them and show the fix

---

## Related Videos in Series

1. **Getting Started** (this video) - Installation and basic usage
2. **Advanced Search** - BM25, Vector, and Hybrid search techniques
3. **Integration Tutorial** - Python package usage and CI/CD integration

---

*Last Updated: 2026-02-10*
*Script Version: 1.0*
