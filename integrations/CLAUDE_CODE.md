# Using skill-split with Claude Code

This guide shows how to use skill-split within Claude Code sessions for maximum token efficiency.

## Progressive Disclosure Workflow

### Step 1: Store Your Skills

```bash
# Store large skill files for progressive disclosure
./skill_split.py store ~/.claude/skills/programming/SKILL.md
./skill_split.py store ~/.claude/skills/agent/SKILL.md
```

### Step 2: Search Before Loading

```bash
# Find relevant sections first
./skill_split.py search "python handler"
./skill_split.py search-semantic "authentication" --vector-weight 0.7
```

### Step 3: Load Only What You Need

```bash
# Get specific section by ID
./skill_split.py get-section 42

# Navigate progressively
./skill_split.py next 42 ~/.claude/skills/programming/SKILL.md
./skill_split.py next 42 ~/.claude/skills/programming/SKILL.md --child
```

## Token Savings Example

**Without skill-split:**
```
Loading entire SKILL.md (21KB) → ~5,000 tokens
Cost per session: $0.015
```

**With skill-split:**
```
Loading one section (204 bytes) → ~50 tokens
Cost per session: $0.00015
Savings: 99% (100x cheaper)
```

## Claude Code Integration Tips

### 1. Reference Sections in Prompts

Instead of:
```
"Look at the programming skill and tell me about Python handlers"
```

Use:
```
"Section 42 covers Python handlers. Here's the content:
[paste section content]
Explain how it works."
```

### 2. Search-First Approach

```bash
# Before asking Claude to analyze code:
./skill_split.py search "error handling"
./skill_split.py search-semantic "validation patterns"

# Then provide specific sections in your prompt
```

### 3. Compose Custom Skills

```bash
# Create focused skills for specific tasks
./skill_split.py compose --sections 42,57,103 --output debugging_skill.md

# Load the composed skill
./skill_split.py store debugging_skill.md
```

## Example Session Workflow

```bash
# 1. Search for relevant content
./skill_split.py search "database optimization"
# Returns: Section 845, 1023, 4567

# 2. Load first section
./skill_split.py get-section 845
# Content: Discusses indexing strategies

# 3. Navigate to related sections
./skill_split.py next 845 path/to/file.md --child
# Content: Specific implementation details

# 4. Compose new skill from findings
./skill_split.py compose --sections 845,1023,4567 --output optimization_guide.md
```

## Best Practices

1. **Always search first** - Find relevant sections before loading
2. **Use semantic search** - `search-semantic` finds concepts, not just keywords
3. **Navigate progressively** - Use `next` with `--child` to drill down
4. **Compose focused skills** - Combine relevant sections for specific tasks
5. **Reference by ID** - Once you find a useful section, reference it by ID

## Advanced: Hybrid Search

```bash
# Combine keyword and semantic search
./skill_split.py search-semantic "async patterns" --vector-weight 0.5

# Lower vector-weight = more keyword influence
# Higher vector-weight = more semantic influence
```

## Integration with Custom Commands

Create shell aliases for common workflows:

```bash
# In ~/.zshrc
alias ss-search='./skill_split.py search'
alias ss-semantic='./skill_split.py search-semantic'
alias ss-get='./skill_split.py get-section'
alias ss-next='./skill_split.py next'
```

Then in Claude Code:
```bash
ss-search "python class definitions"
ss-get 234
```

## Troubleshooting

**Problem**: Search returns no results
**Solution**: Try `search-semantic` for concept-based search

**Problem**: Section content seems incomplete
**Solution**: Use `--child` flag to include subsections

**Problem**: Can't find section by ID
**Solution**: Use `list` command to see all section IDs for a file
