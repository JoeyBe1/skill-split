# skill-split Brand Guidelines

**Last Updated:** 2026-02-10

Guidelines for maintaining brand consistency in skill-split documentation and communications.

---

## Brand Identity

### Name

**skill-split**
- Always lowercase: `skill-split`
- Never: `Skill-Split`, `SkillSplit`, `SKILL_SPLIT`
- Code/commands: `skill_split` (underscore for Python)

### Tagline

> *Split documentation into searchable sections for progressive disclosure.*

### Elevator Pitch

> skill-split is a Python tool that splits YAML and Markdown files into searchable SQLite sections. It enables progressive disclosure for 94-99% token savings in AI workflows while maintaining byte-perfect round-trip integrity.

---

## Tone & Voice

### Core Attributes

| Attribute | Description |
|-----------|-------------|
| **Precise** | Technical accuracy, no fluff |
| **Efficient** | Token-conscious, concise |
| **Practical** | Real-world examples |
| **Developer-focused** | CLI-first, automation-friendly |

### Voice Guidelines

**Do:**
- Be direct and concise
- Use active voice
- Provide working examples
- Show before/after comparisons
- Use YAML for structured output
- Include performance metrics

**Don't:**
- Use marketing fluff
- Make unsupported claims
- Use exclamation marks (!)
- Over-explain simple concepts
- Use emojis (unless in user's context)

### Example Phrases

**Good:**
```
BM25 search: 10-50ms for exact keyword matching
Token savings: 94-99% when loading single sections
Round-trip integrity: SHA256 verified byte-perfect reconstruction
```

**Bad:**
```
Amazing search functionality!!! 🚀
Incredible token savings!!!
Perfect round-trip guarantee!!!
```

---

## Visual Style

### Code Blocks

Use fenced code blocks with language specified:

````markdown
```bash
./skill_split.py search "query"
```
````

```python
from core.parser import Parser
parser = Parser()
```
````

### Tables

Use markdown tables for comparisons:

```markdown
| Mode | Speed | Best For |
|------|-------|----------|
| BM25 | 10-50ms | Exact matches |
| Vector | 100-200ms | Concepts |
```

### Emphasis

- **Bold**: For command names, key concepts
- `Code font`: For file paths, commands, variables
- *Italic*: For emphasis only (rarely used)

---

## Documentation Structure

### Standard Sections

Every feature document should include:

1. **Purpose** (1 paragraph)
2. **Usage** (code examples)
3. **Options** (table format)
4. **Examples** (working commands)
5. **Performance** (metrics)
6. **Troubleshooting** (common issues)

### File Naming

```
FEATURE_NAME.md        # Uppercase, underscore separated
TROUBLESHOOTING.md     # For guides
quick_reference.md     # For quick reference
```

### Headings

```markdown
# Main Heading (H1) - File title only

## Section Heading (H2) - Major sections

### Subsection (H3) - Within sections

#### Detail (H4) - Rarely used
```

---

## Command Documentation Format

### Template

```markdown
## `command-name`

**Purpose**: One-line description

### Usage

```bash
skill-split command-name [arguments] [options]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `file` | path | Yes | Input file path |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output` | path | - | Output file path |
| `--limit` | int | 10 | Max results |

### Examples

```bash
# Basic usage
skill-split command-name file.md

# With options
skill-split command-name file.md --output result.md --limit 20
```

### Performance

- Typical: Xms
- Large files: Yms
- Optimization tips

### See Also

- [Related Command](other-command.md)
- [Integration Guide](../integrations/)
```

---

## API Documentation Format

### Template

```markdown
## `ClassName.method_name()`

**Purpose**: One-line description

### Signature

```python
def method_name(param1: type1, param2: type2 = default) -> ReturnType:
    """Method description."""
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `param1` | type1 | Yes | Description |
| `param2` | type2 | No | Description |

### Returns

`ReturnType` - Description of return value

### Raises

- `ErrorType`: When this happens

### Example

```python
result = ClassName.method_name("value")
print(result)
```

### Performance

- Time complexity: O(n)
- Space complexity: O(1)
```

---

## Performance Reporting

### Format

All performance claims must include:

```markdown
### Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Parse 1KB | <1ms | Default parser |
| Search 10K | 50-100ms | FTS5 indexed |

### Environment

- CPU: Intel i7-12700K
- RAM: 32GB DDR4
- Python: 3.13.5
- Database: 1,365 files, 19,207 sections
```

---

## Color Scheme (Optional)

If colors are needed (ASCII art, diagrams):

| Purpose | Color | Hex |
|---------|-------|-----|
| Primary | Blue | #3B82F6 |
| Success | Green | #10B981 |
| Warning | Yellow | #F59E0B |
| Error | Red | #EF4444 |
| Info | Gray | #6B7280 |

---

## Logo Usage

### Text Logo

```
skill-split
```

### Text Logo with Tagline

```
skill-split
Progressive disclosure for documentation
```

### ASCII Logo (Optional)

```
   _____ __  _____________
  / ___// / / / ____/ ___/
  \__ \/ /_/ / __/  \__ \
 ___/ / __  / /___ ___/ /
/____/_/ /_/_____/____/

skill-split
```

---

## Content Guidelines

### Technical Accuracy

1. **Verify all claims**: Run tests before documenting
2. **Include version info**: "As of v1.0.0"
3. **Update regularly**: Remove outdated info
4. **Test examples**: All code must run

### Accessibility

1. **Alt text**: Describe images and diagrams
2. **Contrast**: High contrast for readability
3. **Font size**: Minimum 12px for web
4. **Structure**: Use semantic HTML/headings

### Inclusivity

1. **Pronouns**: Use "they/them" or avoid
2. **Examples**: Diverse names and scenarios
3. **Language**: Clear, no jargon without explanation
4. **Locale**: Consider international users

---

## Communication Style

### Issues

**Title**: `component: brief description`

```yaml
# Template
component: affected-component
summary: one-line summary
steps_to_reproduce: |
  1. Step one
  2. Step two
expected_behavior: What should happen
actual_behavior: What actually happens
environment: |
  OS: macOS 14.0
  Python: 3.13.5
  skill-split: v1.0.0
```

### Pull Requests

**Title**: `type(scope): brief description`

```yaml
# Types: feat, fix, docs, refactor, perf, test, chore
# Scopes: parser, database, query, cli, docs

# Example
feat(parser): add XML comment support
```

**Description Template:**
```markdown
## What
Brief description of changes

## Why
Reason for the change

## How
Implementation approach

## Testing
How this was tested

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
```

### Commits

```
type(scope): description

# Detailed description

# Footer
Closes #123
Co-Authored-By: Contributor <email>
```

---

## Writing Guidelines

### Clarity

1. **One concept per sentence**
2. **Active voice**: "Store the document" not "The document is stored"
3. **Specific over general**: "Returns Section object" not "Returns an object"
4. **Examples first**: Show usage, then explain

### Brevity

1. **Delete filler words**: "Basically", "actually", "just"
2. **Avoid redundancy**: Don't repeat what's obvious from code
3. **Trust the reader**: Don't over-explain simple concepts
4. **Link, don't repeat**: Reference existing docs instead of duplicating

### Precision

1. **Exact numbers**: "10-50ms" not "~50ms"
2. **Version specific**: "In v1.0.0" not "Currently"
3. **Reproducible**: Include exact commands
4. **Tested**: Verify all examples

---

## Common Patterns

### Feature Announcement

```markdown
## Feature: Feature Name

**What**: One-line description

**Why**: Business value

**How**: Technical approach

**Example**:
```bash
# Usage
command example here
```

**Performance**: Metrics if applicable

**Migration**: Any breaking changes
```

### Release Notes

```markdown
# Release v1.0.0

## Added
- New feature 1
- New feature 2

## Changed
- Updated behavior

## Fixed
- Bug fix 1

## Performance
- 20% faster search

## Migration
See MIGRATION.md for details
```

---

## Quality Checklist

Before publishing any content:

- [ ] All code examples tested
- [ ] All links verified
- [ ] All commands run successfully
- [ ] Performance claims backed by data
- [ ] Spelling and grammar checked
- [ ] Formatting consistent
- [ ] Version numbers correct
- [ ] Contact info accurate

---

## Contact

**Brand Questions**: Open an issue with `brand` label
**Documentation**: Use standard contribution flow
**Press**: Contact via GitHub issue

---

*Consistent branding builds trust. Follow these guidelines to maintain quality across all skill-split communications.*
