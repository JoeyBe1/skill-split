# skill-split Usage Examples

This document demonstrates three practical scenarios for using skill-split to manage large skill and command files through progressive disclosure.

---

## Scenario 1: Progressive Skill Disclosure

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

## Scenario 2: Searching Across Skills

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

## Scenario 3: Section Tree Navigation

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

## Key Features Demonstrated

1. **Progressive Disclosure** - Load metadata first, then sections on-demand
2. **Cross-File Management** - Store and retrieve multiple files from single database
3. **Nested Navigation** - Handle both markdown and XML section hierarchies
4. **Integrity Verification** - SHA256 hashing ensures byte-perfect preservation
5. **Token Efficiency** - Split large files into manageable pieces

## Next Steps

- See [README.md](./README.md) for installation and setup
- See [CLAUDE.md](./CLAUDE.md) for project context
- Run test suite: `pytest test/ -v`
