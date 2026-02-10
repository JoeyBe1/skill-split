# skill-split Documentation Style Guide

Based on analysis of existing documentation in skill-split, this guide outlines the patterns and conventions to follow for Phase 07 documentation.

---

## 1. Documentation Structure

### Hierarchical Organization
- **Main Sections** Use H1 (`#`) only for the main title
- **Primary Sections** Use H2 (`##`) for main topics
- **Subsections** Use H3 (`###`) for subtopics
- **Sub-subsections** Use H4 (`####`) for detailed breakdowns

### Section Flow Pattern
```
1. Problem Statement
2. Solution Overview
3. Step-by-Step Implementation
4. Examples
5. Benefits
6. Related Commands/Features
```

---

## 2. Writing Style and Tone

### Active Voice
- Use active voice: "**Parse** the file" not "The file is parsed"
- Action-oriented verbs: Create, Store, Navigate, Search, Validate

### Technical Precision
- Be specific about commands and arguments
- Include exact error messages and outputs
- Specify file paths and database locations

### Professional but Accessible
- Avoid jargon where possible
- Explain technical terms when first used
- Maintain professional tone while being approachable

---

## 3. Code Example Formatting

### Command Examples
```markdown
```bash
# Command with clear purpose
./skill_split.py <command> <arguments>

# Output example (with realistic data)
File: /path/to/skill.md
File ID: 1
Hash: abc123def456...
Type: skill
Format: markdown
Sections: 4
```
```

### Python Code Blocks
```python
# For implementation examples
def example_function():
    """Clear docstring explaining purpose"""
    pass
```

### YAML/JSON Examples
```yaml
# For configuration examples
---
name: example-skill
description: A sample skill
version: 1.0.0
---

# Content follows
```

---

## 4. Section Heading Patterns

### Problem/Solution Format
```markdown
### Problem
Describe the specific issue users face with concrete examples.

### Solution
Present the skill-split approach with clear benefits.
```

### Command Reference Format
```markdown
### Command Name

```bash
./skill_split.py <command> <arguments>
```

**Description**: Clear one-line explanation

**Arguments**:
- `arg1`: Description with type (e.g., "Path to file")
- `arg2`: (Optional) Description when needed
- `--flag`: Boolean flag description

**Output**: Description of expected output format

**Examples**:
```bash
# Basic usage
./skill_split.py example --input file.md

# With options
./skill_split.py example --input file.md --output result.md
```
```

### Feature Overview Format
```markdown
## Feature Name

**Best for**: When to use this feature

**Key Features**:
- Feature 1 benefit
- Feature 2 benefit
- Feature 3 benefit

### Usage Examples
```

---

## 5. CLI Command Documentation

### Command Template
```markdown
### Command

```bash
./skill_split.py <command> [options]
```

**Description**: What the command does and why it's useful

**Arguments**:
- `required_arg`: Description of required argument
- `[optional_arg]`: Description of optional argument

**Options**:
- `--option`: Description of boolean flag
- `--value <value>`: Description of option requiring value

**Exit Codes**:
- `0`: Success
- `1`: Error condition

**Examples**:
```

### Output Format
Show realistic output with proper formatting:
```
✓ Round-trip successful
  Original hash:  abc123def456...
  Recomposed hash: abc123def456...
  Match: YES
```

---

## 6. Cross-Referencing Patterns

### Internal Links
```markdown
- See [Main Documentation](../README.md) for installation
- Reference [CLI Commands](#cli-reference) for full command list
- Examples in [EXAMPLES.md](../EXAMPLES.md)

For component handlers, see:
- [Component Handlers](./COMPONENT_HANDLERS.md)
- [Handler Integration](./HANDLER_INTEGRATION.md)
```

### Related Features
```markdown
**Related Commands**:
- `parse` - File structure inspection
- `store` - Database storage
- `tree` - Hierarchical view

**See Also**:
- Progressive disclosure workflows in [EXAMPLES.md](../EXAMPLES.md#progressive-disclosure)
- Search capabilities in [Search & Navigation](#search--navigation)
```

---

## 7. Special Elements

### Status Indicators
Use checkmarks for completed features:
- ✅ Complete - 518 tests passing
- 📋 Planned - Phase 02 search fix
- 🔄 In Progress - Currently implementing

### Tables for Comparison
```markdown
| Use Case | Command | Notes |
|----------|---------|-------|
| Exact keyword match | `search "python"` | Fast, local, no API needed |
| Semantic similarity | `search-semantic "query" --vector-weight 1.0` | Requires API keys |
```

### File Paths
Use absolute paths consistently:
```
~/.claude/skills/my-skill.md
/Users/joey/working/skill-split/test/fixtures/
```

---

## 8. Consistency Checklist

Before finalizing documentation:

1. **Headings**: Follow H1-H4 hierarchy exactly
2. **Commands**: Use `./skill_split.py` prefix
3. **Output**: Show realistic, formatted output
4. **Links**: Verify all internal links work
5. **Examples**: Test all command examples
6. **Tone**: Maintain active, professional voice
7. **Structure**: Follow problem/solution pattern
8. **Formatting**: Consistent code block syntax
9. **Paths**: Use absolute paths throughout
10. **Exit Codes**: Document all possible exit codes

---

## 9. Phase 07 Specific Considerations

For the documentation gap analysis and plan:

- **Follow the existing phase documentation style** in `docs/plans/README.md`
- **Include implementation status** checkmarks (✅/📋/🔄)
- **Reference existing tests** (518 passing as of 2026-02-08)
- **Connect to search workflows** from EXAMPLES.md
- **Maintain focus on progressive disclosure** as a core principle

---

**Based on**: README.md, EXAMPLES.md, docs/plans/README.md
**Created**: 2026-02-10
**Last Updated**: 2026-02-10