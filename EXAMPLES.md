# skill-split Usage Examples

This document demonstrates practical scenarios for using skill-split to manage files through progressive disclosure, including search capabilities and component handler support for plugins, hooks, and configuration files.

---

## Search Workflows

### Finding Relevant Skills

**Scenario:** You need a git setup command but don't know which skill has it.

```bash
# Search for git-related content (BM25 keyword search)
./skill_split.py search "git setup"
```

**Result:**
```
Found 8 section(s) matching 'git setup':

ID      Score   Title                                         File
-------- -------- -------------------------------------------- ----------------------------------------
156     3.42    Clone Repository                              /skills/version-control/SKILL.md
42      2.85    Initial Setup                                 /skills/workflow/SKILL.md
203     2.18    Configuration                                 /skills/version-control/SKILL.md
```

Now you can load the specific section:

```bash
./skill_split.py get-section 156
```

### Exact Phrase Search

**Scenario:** You need the exact "python handler" implementation, not sections about python OR handlers.

```bash
# Use quotes for exact phrase
./skill_split.py search '"python handler"'
```

### Narrowing Results with AND

**Scenario:** You want sections about both "python" AND "testing".

```bash
# Explicit AND for narrow results
./skill_split.py search "python AND testing"
```

### Broad Discovery with OR

**Scenario:** You want to find anything related to "repository" OR "storage".

```bash
# Multi-word automatically uses OR (broad discovery)
./skill_split.py search "repository storage"

# Or explicit OR
./skill_split.py search "repository OR storage"
```

### Semantic Search (Vector)

**Scenario:** You want to find content about "code execution" even if those exact words aren't used.

```bash
# Requires OPENAI_API_KEY and Supabase
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 1.0
```

This finds semantically similar content like "running scripts", "execute commands", "process execution", etc.

### Hybrid Search (Best of Both)

**Scenario:** You want comprehensive results combining keywords and semantic meaning.

```bash
# 70% semantic, 30% keyword (default)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "python error handling" --vector-weight 0.7
```

This finds sections with "python" and "error" keywords, plus semantically similar content about exceptions, debugging, troubleshooting, etc.

## Progressive Disclosure Workflows

### Loading Large Skills Token-Efficiently

**Scenario:** A skill has 50 sections. You only need the specific "Configuration" section.

```bash
# Step 1: List file structure
./skill_split.py list /skills/programming/SKILL.md

# Output shows:
# ID  Title
# --- ----------------------------------
# 1  Overview
# 2  Installation
# 3  Basic Usage
# 4  Advanced Usage
# 5  Configuration              <-- This is what you want
# 6  Troubleshooting

# Step 2: Load just the Configuration section
./skill_split.py get-section 5 --db ~/.claude/databases/skill-split.db

# Output:
# --- Section Configuration (Level 1) ---
#
# Configuration options include:
# - timeout: Request timeout in milliseconds
# - retries: Number of retry attempts
# ...
```

**Token savings:** Instead of loading the entire 50-section skill (21KB), you load just one section (204 bytes) - **99% context savings**.

### Hierarchical Navigation

**Scenario:** A skill has nested sections. You want to explore subsections under "Advanced Topics".

```bash
# Step 1: Find the parent section ID
./skill_split.py list /skills/programming/SKILL.md | grep -i advanced

# Output: 4  Advanced Topics                    1

# Step 2: Navigate to first child subsection
./skill_split.py next 4 /skills/programming/SKILL.md --child

# Output: Shows first subsection under Advanced Topics

# Step 3: Continue navigating through siblings
./skill_split.py next <subsection_id> /skills/programming/SKILL.md
```

### Sequential Reading Workflow

**Scenario:** Reading through a tutorial skill section by section.

```bash
# Start with first section
./skill_split.py get-section 1

# Read sequentially
./skill_split.py next 1 /skills/tutorial/SKILL.md
./skill_split.py next 2 /skills/tutorial/SKILL.md
./skill_split.py next 3 /skills/tutorial/SKILL.md
# ... continue as needed
```

## Combined Search + Navigation Workflow

### Finding and Exploring Related Content

**Scenario:** You're working on database optimization and want to find related skills, then explore them.

```bash
# Step 1: Search for database content
./skill_split.py search "database optimization"

# Result shows section 156 in /skills/backend/SKILL.md with score 3.42

# Step 2: Load that section
./skill_split.py get-section 156

# Step 3: See what else is in that skill
./skill_split.py list /skills/backend/SKILL.md

# Step 4: Explore related sections
./skill_split.py next 156 /skills/backend/SKILL.md
./skill_split.py next 156 /skills/backend/SKILL.md --child  # Drill into subsections
```

### Cross-File Research

**Scenario:** Researching how different skills handle error handling.

```bash
# Search across all files
./skill_split.py search "error handling"

# Results show sections from multiple files:
# - /skills/backend/SKILL.md (section 42)
# - /skills/frontend/SKILL.md (section 87)
# - /skills/api/SKILL.md (section 15)

# Compare approaches
./skill_split.py get-section 42  # Backend approach
./skill_split.py get-section 87  # Frontend approach
./skill_split.py get-section 15  # API approach
```

---

## Component Handler Workflows

The following scenarios demonstrate component handler support for plugins, hooks, and configuration files, building on the search and progressive disclosure workflows shown above.

### Scenario 1: Progressive Skill Disclosure

**Use Case**: Load a skill incrementally to stay within token budgets and improve focus.

### Problem

You have a large 50+ section skill file. Reading it all at once uses too many tokens. You want to:
1. Parse and store the file
2. View its structure
3. Retrieve specific sections progressively

### Commands

```bash
# Step 1: Parse the skill file to understand its structure
cd /Users/joey/working/skill-split
./skill_split.py parse test/fixtures/simple_skill.md
```

**Output:**
```
File: test/fixtures/simple_skill.md
Type: skill
Format: markdown

Frontmatter:
---
name: test-skill
description: A simple test skill
version: 1.0.0
---

Sections:
# Test Skill
  Lines: 7-9
  ## Overview
    Lines: 11-13
    ### Details
      Lines: 15-17
  ## Usage
    Lines: 19-21
```

```bash
# Step 2: Store the file in the database
./skill_split.py store test/fixtures/simple_skill.md
```

**Output:**
```
File: test/fixtures/simple_skill.md
File ID: 1
Hash: 3f8c2a91d7e4b5c6a9f1e2d3c4b5a6f7
Type: skill
Format: markdown
Sections: 4
```

```bash
# Step 3: View the section tree to understand hierarchy
./skill_split.py tree test/fixtures/simple_skill.md
```

**Output:**
```
File: test/fixtures/simple_skill.md

Sections:
# Test Skill
  Lines: 7-9
  ## Overview
    Lines: 11-13
    ### Details
      Lines: 15-17
  ## Usage
    Lines: 19-21
```

```bash
# Step 4: Retrieve file metadata and frontmatter
./skill_split.py get test/fixtures/simple_skill.md
```

**Output:**
```
File: test/fixtures/simple_skill.md
Type: skill
Hash: 3f8c2a91d7e4b5c6a9f1e2d3c4b5a6f7
Frontmatter:
---
name: test-skill
description: A simple test skill
version: 1.0.0
---
Sections: 4
```

### Benefits

- **Token Efficiency**: Load section metadata first (small), then fetch sections on-demand
- **Better Focus**: See full outline before diving into details
- **Integrity Verified**: Hash stored with file for integrity checking
- **Database-Backed**: Multiple queries against same file don't re-parse

---

### Scenario 2: Searching Across Skills

**Use Case**: Find and manage multiple command/skill files organized by type.

### Problem

You maintain several Claude Code skills and commands in a directory:
- `skills/authentication.md` - Auth patterns (150 lines)
- `skills/database.md` - DB integration (200 lines)
- `commands/test-runner.md` - Test execution (80 lines)
- `references/api-guide.md` - API reference (300 lines)

You want to ingest them all and manage them centrally.

### Commands

```bash
# Step 1: Create sample skill files
cat > /tmp/skill_database.md << 'EOF'
---
name: database-skill
description: Database integration patterns
version: 1.0.0
---

# Database Integration

## Connection Pools

Connection pooling for efficient database access.

## Transactions

ACID transaction handling.
EOF

cat > /tmp/skill_auth.md << 'EOF'
---
name: auth-skill
description: Authentication patterns
version: 1.0.0
---

# Authentication

## JWT Tokens

JWT token generation and validation.

## OAuth2 Flow

OAuth2 integration guide.
EOF

# Step 2: Parse and store each skill
./skill_split.py store /tmp/skill_database.md
./skill_split.py store /tmp/skill_auth.md
```

**Output:**
```
File: /tmp/skill_database.md
File ID: 1
Hash: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Type: skill
Format: markdown
Sections: 3

File: /tmp/skill_auth.md
File ID: 2
Hash: x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4
Type: skill
Format: markdown
Sections: 3
```

```bash
# Step 3: View tree for each file
./skill_split.py tree /tmp/skill_database.md
./skill_split.py tree /tmp/skill_auth.md
```

**Output:**
```
File: /tmp/skill_database.md

Sections:
# Database Integration
  Lines: 7-9
  ## Connection Pools
    Lines: 11-13
  ## Transactions
    Lines: 15-17

File: /tmp/skill_auth.md

Sections:
# Authentication
  Lines: 7-9
  ## JWT Tokens
    Lines: 11-13
  ## OAuth2 Flow
    Lines: 15-17
```

### Benefits

- **Centralized Index**: All skills indexed in one database
- **Metadata Preserved**: Frontmatter stored separately for quick lookup
- **Cross-Cutting Search**: Find related sections across multiple files
- **Version Control**: Hash stored allows change detection

---

### Scenario 3: Section Tree Navigation

**Use Case**: Navigate complex nested section hierarchies with XML tags.

### Problem

You have a reference file with deeply nested sections using both markdown headings and XML tags:

```
<database-guide>
  Configuration
  <connection>
    Connection pooling
  </connection>
  <transactions>
    Transaction handling
  </transactions>
</database-guide>
```

You want to understand the full structure and validate it.

### Commands

```bash
# Step 1: Parse file with XML tags
./skill_split.py parse test/fixtures/xml_tags.md
```

**Output:**
```
File: test/fixtures/xml_tags.md
Type: reference
Format: xml

Sections:
<example> (XML)
  Lines: 1-4
<nested> (XML)
  Lines: 6-12
  <inner> (XML)
    Lines: 10-11
<multiple> (XML)
  Lines: 14-16
<multiple> (XML)
  Lines: 18-21
```

```bash
# Step 2: Validate the file structure
./skill_split.py validate test/fixtures/xml_tags.md
```

**Output:**
```
Validating: test/fixtures/xml_tags.md
Type: reference, Format: xml

✓ No issues found
```

```bash
# Step 3: Store in database for progressive retrieval
./skill_split.py store test/fixtures/xml_tags.md
```

**Output:**
```
File: test/fixtures/xml_tags.md
File ID: 3
Hash: m1n2o3p4q5r6s7t8u9v0w1x2y3z4a5b6
Type: reference
Format: xml
Sections: 5
```

```bash
# Step 4: View the hierarchical tree
./skill_split.py tree test/fixtures/xml_tags.md
```

**Output:**
```
File: test/fixtures/xml_tags.md

Sections:
<example> (XML)
  Lines: 1-4
<nested> (XML)
  Lines: 6-12
  <inner> (XML)
    Lines: 10-11
<multiple> (XML)
  Lines: 14-16
<multiple> (XML)
  Lines: 18-21
```

```bash
# Step 5: Verify round-trip integrity
./skill_split.py verify test/fixtures/xml_tags.md
```

**Output:**
```
File: test/fixtures/xml_tags.md
File ID: 3
Type: reference
Format: xml

Valid

original_hash:    m1n2o3p4q5r6s7t8u9v0w1x2y3z4a5b6
recomposed_hash:  m1n2o3p4q5r6s7t8u9v0w1x2y3z4a5b6
```

### Benefits

- **Nested Navigation**: Understand complex hierarchies at a glance
- **Multi-Format Support**: Handles both markdown headings and XML tags
- **Integrity Guaranteed**: Hash verification ensures no data loss
- **Byte-Perfect**: Recomposed file matches original exactly
- **Debug-Friendly**: Line numbers help locate sections in original file

---

## Combined Workflow Example

Here's a complete end-to-end workflow combining all three scenarios:

```bash
#!/bin/bash
# Complete skill management workflow

cd /Users/joey/working/skill-split

# 1. Ingest all skill files
echo "=== Ingesting Skills ==="
./skill_split.py store test/fixtures/simple_skill.md
./skill_split.py store test/fixtures/test_command.md
./skill_split.py store test/fixtures/xml_tags.md

# 2. View structure of each
echo ""
echo "=== Viewing Structures ==="
./skill_split.py tree test/fixtures/simple_skill.md
./skill_split.py tree test/fixtures/test_command.md

# 3. Retrieve and inspect metadata
echo ""
echo "=== Retrieving Metadata ==="
./skill_split.py get test/fixtures/simple_skill.md
./skill_split.py get test/fixtures/test_command.md

# 4. Verify integrity
echo ""
echo "=== Verifying Integrity ==="
./skill_split.py verify test/fixtures/simple_skill.md
./skill_split.py verify test/fixtures/test_command.md

echo ""
echo "=== Workflow Complete ==="
```

---

### Scenario 4: Component Handler - Plugin Management

**Use Case**: Store and retrieve Claude Code plugins with progressive disclosure.

### Problem

You have a plugin with multiple configuration files:
- `plugin.json`: Main plugin metadata
- `my-plugin.mcp.json`: MCP server configuration
- `hooks.json`: Hook definitions

You want to manage these as a single component while loading sections on-demand.

### Commands

```bash
# Step 1: Store the plugin
./skill_split.py store ~/.claude/plugins/my-plugin/plugin.json
```

**Output:**
```
File: /Users/joey/.claude/plugins/my-plugin/plugin.json
File ID: 3
Hash: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Type: plugin
Format: multi_file
Sections: 3
  - metadata
  - mcp_config
  - hooks
```

```bash
# Step 2: View plugin structure
./skill_split.py tree ~/.claude/plugins/my-plugin/plugin.json
```

**Output:**
```
File: /Users/joey/.claude/plugins/my-plugin/plugin.json

Sections:
metadata
  Lines: 1-10
mcp_config
  Lines: 1-25
hooks
  Lines: 1-15
```

```bash
# Step 3: Get specific section
./skill_split.py get-section 4 --db skill-split.db
```

**Output:**
```
=== metadata (Level 1, Section ID: 4) ===

# My Plugin

**Version**: 1.0.0
**Description**: A sample plugin for demonstration

## Permissions
- allowNetwork
- allowFileSystemRead
```

### Benefits

- **Multi-file tracking**: Automatically includes .mcp.json and hooks.json
- **Combined hashing**: Hash includes all related files for integrity
- **Type-specific validation**: Checks required fields and schema
- **Progressive disclosure**: Load only the sections you need

---

### Scenario 5: Component Handler - Configuration Search

**Use Case**: Search across configuration files to find specific settings.

### Problem

You have multiple configuration files and want to find all references to a specific setting or MCP server.

### Commands

```bash
# Store all configuration files
./skill_split.py store ~/.claude/settings.json
./skill_split.py store ~/.claude/mcp_config.json

# Search for specific setting
./skill_split.py search "mcpServers" --db skill-split.db
```

**Output:**
```
Searching for: mcpServers

Found 2 matches:

File: /Users/joey/.claude/settings.json
Section: mcpServers (ID: 7)
Content:
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
  }
}

File: /Users/joey/.claude/mcp_config.json
Section: mcpServers (ID: 10)
Content:
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"]
  }
}
```

### Benefits

- **Cross-config search**: Find settings across multiple files
- **Section-level results**: Get specific sections, not entire files
- **Token efficiency**: Load only matching sections
- **Unified interface**: Single search for all component types

---

### Scenario 6: Component Handler - Hook Inspection

**Use Case**: Inspect hook definitions and scripts without loading entire plugin.

### Problem

You want to understand what hooks are defined and view specific hook scripts without loading the entire plugin configuration.

### Commands

```bash
# Step 1: Store hooks configuration
./skill_split.py store ~/.claude/plugins/my-plugin/hooks.json
```

**Output:**
```
File: /Users/joey/.claude/plugins/my-plugin/hooks.json
File ID: 4
Hash: x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4
Type: hook
Format: multi_file
Sections: 3
  - pre-commit
  - post-checkout
  - on-file-change
```

```bash
# Step 2: View hook structure
./skill_split.py tree ~/.claude/plugins/my-plugin/hooks.json
```

**Output:**
```
File: /Users/joey/.claude/plugins/my-plugin/hooks.json

Sections:
pre-commit
  Lines: 1-25
post-checkout
  Lines: 26-50
on-file-change
  Lines: 51-75
```

```bash
# Step 3: Get specific hook with script
./skill_split.py get-section 11 --db skill-split.db
```

**Output:**
```
=== pre-commit (Level 1, Section ID: 11) ===

# pre-commit

**Description**: Runs before creating a git commit

## Script

```bash
#!/bin/bash
# Pre-commit hook for linting
npm run lint
npm test
```
```

### Benefits

- **Script inclusion**: Shell scripts included in sections
- **Metadata preservation**: Descriptions and permissions preserved
- **Validation**: Checks for missing scripts and executable permissions
- **Progressive loading**: View hooks individually

---

## Key Features Demonstrated

1. **Progressive Disclosure** - Load metadata first, then sections on-demand
2. **Cross-File Management** - Store and retrieve multiple files from single database
3. **Nested Navigation** - Handle both markdown and XML section hierarchies
4. **Integrity Verification** - SHA256 hashing ensures byte-perfect preservation
5. **Token Efficiency** - Split large files into manageable pieces
6. **Component Handlers** - Type-specific parsing for plugins, hooks, configs
7. **Multi-File Support** - Track related files with combined hashing
8. **Cross-Component Search** - Search across all component types

## Next Steps

- See [README.md](./README.md) for installation and setup
- See [CLAUDE.md](./CLAUDE.md) for project context
- See [COMPONENT_HANDLERS.md](./COMPONENT_HANDLERS.md) for complete component handler guide
- See [HANDLER_INTEGRATION.md](./HANDLER_INTEGRATION.md) for integration details
- Run test suite: `pytest test/ -v`
