# Quick Start: Ingest Your First Skills

This 5-minute guide demonstrates skill-split's value with 2 high-utility skills.

## Why Use skill-split?

- **Load progressively**: See structure first, load sections on-demand
- **Save tokens**: 70-90% reduction by loading only what you need
- **Search efficiently**: Find content across multiple skills instantly

## Demo: 2 Essential Skills

### 1. Creating Output Styles (Recommended First)

**Why**: Clean structure, immediately useful, shows token savings

```bash
# Parse to preview structure
/skill-split parse ~/.claude/skills/creating-output-styles/SKILL.md

# Store in database
/skill-split store ~/.claude/skills/creating-output-styles/SKILL.md

# View hierarchy with IDs
/skill-split tree ~/.claude/skills/creating-output-styles/SKILL.md

# Search within this skill
/skill-split search "persona" --file ~/.claude/skills/creating-output-styles/SKILL.md

# Load only the section you need
/skill-split get-section ~/.claude/skills/creating-output-styles/SKILL.md 3
```

**Token savings demonstrated**: 114-line file → 10-line tree view → 15-line section = 87% reduction

---

### 2. Prompt Engineering

**Why**: Pure knowledge base, shows cross-file search value

```bash
/skill-split store ~/.claude/skills/prompt-engineering/SKILL.md
/skill-split search "temperature"  # Searches ALL ingested skills
```

**Value demonstrated**: Cross-file search finds "temperature" across both skills instantly

---

## Validation Checklist

- [ ] Both skills parsed successfully
- [ ] Database created at `~/.claude/databases/skill-split.db`
- [ ] Tree output shows section IDs and hierarchy
- [ ] Search returns relevant sections
- [ ] Section retrieval displays correct content

## Next Steps

- **Add your own skills**: `/skill-split store ~/.claude/skills/your-skill/SKILL.md`
- **Browse all sections**: `/skill-split list --db ~/.claude/databases/skill-split.db`
- **Team collaboration**: See Supabase commands for shared libraries
