#!/usr/bin/env python3
"""
Skill Template Generator

Creates a new skill file with proper frontmatter and structure.

Usage:
    python scripts/create_skill_template.py "My Skill" "skills/my_skill.md"
"""

import sys
import argparse
from datetime import datetime


def create_skill_template(name, output_path, description=""):
    """Create a new skill file with template structure."""

    slug = name.lower().replace(" ", "-").replace("_", "-")

    frontmatter = f'''---
name: {slug}
description: {description or f"Skill for {name}"}

# INVOCATION CONTROL
disable-model-invocation: false
user-invocable: true

# ARGUMENT HINTS
argument-hint: "[optional-argument]"

# TOOL RESTRICTIONS
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion

# MODEL OVERRIDE
model: inherit

# SUBAGENT EXECUTION
context: inline

# LIFECYCLE HOOKS
hooks:
  PreToolUse:
    - matcher: "Read|Write|Edit"
      hooks:
        - type: prompt
          prompt: "Always preserve brand guidelines when editing files."

  Stop:
    - hooks:
        - type: prompt
          prompt: "Verify all changes align with the skill's purpose."
---

# {name}

**Purpose**: {description or f"A comprehensive skill for {name}"}

## When to Use

Use this skill when:
- You need to {name.lower()}
- Working with {name.lower()} related tasks
- Automating {name.lower()} workflows

## What It Does

1. **Primary Function**
   - Description here

2. **Secondary Functions**
   - Additional capabilities
   - Related features

## Usage

```bash
/{slug}
```

With arguments:
```bash
/{slug} argument-value
```

## Examples

### Example 1: Basic Usage
**Input**: Standard command
**Output**: Expected result

### Example 2: Advanced Usage
**Input**: Command with arguments
**Output**: Advanced result

## Configuration

Edit the configuration section at the top of this file:

```yaml
name: {slug}          # Skill name (lowercase, hyphens)
description: "..."    # One-line description
user-invocable: true  # Can users invoke this skill?
```

## Implementation

```python
def main():
    """Main entry point for {slug}."""
    # Your implementation here
    pass


if __name__ == "__main__":
    main()
```

## Testing

Test cases:
- [ ] Basic functionality works
- [ ] Edge cases handled
- [ ] Error conditions covered

## See Also

- [Related Skill](other-skill.md)
- [Documentation](../../docs/)
'''

    with open(output_path, 'w') as f:
        f.write(frontmatter)

    print(f"✅ Created skill template: {output_path}")
    print(f"   Name: {name}")
    print(f"   Slug: {slug}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Create a new skill file with template"
    )
    parser.add_argument("name", help="Skill name (e.g., 'My Skill')")
    parser.add_argument("output", help="Output path (e.g., 'skills/my_skill.md')")
    parser.add_argument("--description", default="", help="Skill description")

    args = parser.parse_args()

    create_skill_template(args.name, args.output, args.description)


if __name__ == "__main__":
    main()
