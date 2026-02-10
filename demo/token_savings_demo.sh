#!/bin/bash
# skill-split Token Savings Demonstration
# Shows the value of progressive disclosure for token efficiency

echo "=== skill-split Token Savings Demo ==="
echo ""

# Create a large test file
TEST_FILE="demo_large_skill.md"
echo "Creating test file with 50 sections..."

cat > "$TEST_FILE" << 'CONTENT'
# Large Programming Skill

## Introduction

This skill contains comprehensive programming knowledge.

---

## Section 1: Python Basics

Python is a high-level programming language known for its simplicity.

### Variables

Variables store data values.

### Data Types

Python has several built-in data types: int, float, str, bool.

## Section 2: Control Flow

Control flow statements control the order of execution.

### If Statements

Conditional execution based on conditions.

### Loops

For loops and while loops for iteration.

CONTENT

# Add more sections
for i in {3..50}; do
  cat >> "$TEST_FILE" << CONTENT

## Section $i: Advanced Topic $i

Detailed explanation of programming concept $i.

### Subsection A

First aspect of the topic.

### Subsection B

Second aspect with more details.

### Code Example

\`\`\`python
def example_function_$i():
    # Implementation here
    pass
\`\`\`

CONTENT
done

# Get file size
FILE_SIZE=$(wc -c < "$TEST_FILE" | awk '{print $1}')
echo "Created test file: $FILE_SIZE bytes"
echo ""

# Calculate token estimates
FULL_TOKENS=$((FILE_SIZE / 4))
ONE_SECTION_TOKENS=200
SAVINGS=$((FULL_TOKENS - ONE_SECTION_TOKENS))
SAVINGS_PCT=$((SAVINGS * 100 / FULL_TOKENS))

echo "=== Token Comparison ==="
echo "Full document load: ~$FULL_TOKENS tokens"
echo "One section load:   ~$ONE_SECTION_TOKENS tokens"
echo "Tokens saved:       $SAVINGS tokens ($SAVINGS_PCT%)"
echo ""

# Calculate cost savings
COST_PER_M=3
FULL_COST=$(echo "scale=6; $FULL_TOKENS * $COST_PER_M / 1000000" | bc)
ONE_COST=$(echo "scale=6; $ONE_SECTION_TOKENS * $COST_PER_M / 1000000" | bc)
SAVED_COST=$(echo "scale=6; $SAVINGS * $COST_PER_M / 1000000" | bc)

echo "=== Cost Comparison at \$$COST_PER_M per 1M tokens ==="
echo "Full document cost:  \$$FULL_COST per load"
echo "One section cost:    \$$ONE_COST per load"
echo "Cost savings:        \$$SAVED_COST per load ($SAVINGS_PCT%)"
echo ""

# Show session impact
SESSIONS=100
TOTAL_SAVED=$(echo "scale=2; $SAVED_COST * $SESSIONS" | bc)
echo "=== $SESSIONS Session Impact ==="
echo "Total potential savings: \$$TOTAL_SAVED"
echo ""

echo "=== Progressive Disclosure Value ==="
echo "By loading only the section you need:"
echo "1. Faster responses (less data to transfer)"
echo "2. Lower API costs ($SAVINGS_PCT% savings)"
echo "3. Better focus (relevant content only)"
echo ""

# Cleanup
rm -f "$TEST_FILE"
echo "Demo complete. Cleaned up test file."
