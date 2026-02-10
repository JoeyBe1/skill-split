# CI/CD Integration with skill-split

This guide shows how to integrate skill-split into continuous integration pipelines for documentation validation and skill testing.

## GitHub Actions Example

### Validate Documentation on Pull Requests

```yaml
name: Validate Documentation

on:
  pull_request:
    paths:
      - '**/*.md'
      - 'skills/**'
      - 'commands/**'

jobs:
  validate-skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install skill-split
        run: |
          pip install -e .
      
      - name: Validate skill files
        run: |
          for file in skills/**/*.md commands/**/*.md; do
            echo "Validating $file..."
            python skill_split.py validate "$file"
          done
      
      - name: Check for broken sections
        run: |
          python skill_split.py store skills/**/*.md --db test.db
          python skill_split.py verify test.db
          
      - name: Test progressive disclosure
        run: |
          # Ensure all sections can be loaded individually
          python skill_split.py list skills/programming/SKILL.md > sections.txt
          while read section_id; do
            python skill_split.py get-section "$section_id" --db test.db
          done < sections.txt
```

### Search Quality Validation

```yaml
name: Search Quality Tests

on:
  push:
    paths:
      - 'skills/**'

jobs:
  search-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -e .
      
      - name: Index skills
        run: |
          python skill_split.py store skills/**/*.md --db production.db
      
      - name: Test search queries
        run: |
          # Define test queries with expected results
          queries=(
            "python handler:3"
            "authentication:2"
            "error handling:5"
          )
          
          for query in "${queries[@]}"; do
            IFS=':' read -r q expected <<< "$query"
            results=$(python skill_split.py search "$q" --db production.db | wc -l)
            
            if [ "$results" -lt "$expected" ]; then
              echo "FAIL: '$q' returned only $results results (expected $expected)"
              exit 1
            fi
          done
      
      - name: Test progressive disclosure
        run: |
          # Verify next section navigation works
          first_id=$(python skill_split.py list skills/programming/SKILL.md | head -1 | awk '{print $1}')
          python skill_split.py next "$first_id" skills/programming/SKILL.md --db production.db
```

### Skill Composition Testing

```yaml
name: Skill Composition Tests

on:
  push:
    paths:
      - 'skills/**'

jobs:
  composition:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install skill-split
        run: pip install -e .
      
      - name: Test skill composition
        run: |
          # Store source skills
          python skill_split.py store skills/**/*.md --db test.db
          
          # Compose new skill from specific sections
          python skill_split.py compose \
            --sections 1,5,10,15,20 \
            --output test_composed_skill.md \
            --db test.db
          
          # Validate composed skill
          python skill_split.py validate test_composed_skill.md
          
          # Verify round-trip
          python skill_split.py store test_composed_skill.md --db test.db
          python skill_split.py verify test_composed_skill.md
```

## GitLab CI Example

```yaml
# .gitlab-ci.yml

stages:
  - validate
  - test
  - compose

validate_docs:
  stage: validate
  script:
    - pip install -e .
    - for file in $(find skills -name "*.md"); do
        python skill_split.py validate "$file" || exit 1
      done
  tags:
    - docker

search_quality:
  stage: test
  script:
    - pip install -e .
    - python skill_split.py store skills/**/*.md --db test.db
    - |
      python skill_split.py search "python" --db test.db | grep -q "Python Handler"
      python skill_split.py search "authentication" --db test.db | grep -q "Auth"
  artifacts:
    paths:
      - test.db
    expire_in: 1 hour

compose_skills:
  stage: compose
  script:
    - pip install -e .
    - python skill_split.py compose --sections 1,5,10 --output composed.md --db test.db
    - python skill_split.py validate composed.md
  dependencies:
    - search_quality
```

## Pre-commit Hook

Add to `.git-pre-commit`:

```bash
#!/bin/bash
# Pre-commit hook for skill-split

echo "Validating markdown files..."

for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.md$'); do
    echo "  Checking $file..."
    python skill_split.py validate "$file" || exit 1
done

echo "✓ All files valid"
```

## Documentation Coverage Report

Generate coverage reports for documentation:

```bash
#!/bin/bash
# Generate documentation coverage report

echo "=== Documentation Coverage ===" > coverage.txt

# Count sections per file
for file in skills/**/*.md; do
    count=$(python skill_split.py list "$file" | wc -l)
    echo "$file: $count sections" >> coverage.txt
done

# Find files with no sections
echo "" >> coverage.txt
echo "Files with < 5 sections:" >> coverage.txt
for file in skills/**/*.md; do
    count=$(python skill_split.py list "$file" | wc -l)
    if [ "$count" -lt 5 ]; then
        echo "  $file ($count sections)" >> coverage.txt
    fi
done

cat coverage.txt
```

## Automated Skill Testing

Test skills programmatically:

```python
#!/usr/bin/env python3
"""Automated skill testing for CI/CD."""

from pathlib import Path
from core.parser import Parser
from core.validator import Validator
from core.database import DatabaseStore

def test_skill_file(file_path: Path) -> bool:
    """Test a skill file for validity and completeness."""
    parser = Parser()
    validator = Validator()
    
    # Parse file
    with open(file_path) as f:
        content = f.read()
    
    document = parser.parse(content, str(file_path))
    
    # Validate structure
    issues = validator.validate_document(document)
    if issues:
        print(f"FAIL: {file_path}")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    # Check minimum sections
    if len(document.sections) < 3:
        print(f"FAIL: {file_path} (only {len(document.sections)} sections)")
        return False
    
    print(f"PASS: {file_path} ({len(document.sections)} sections)")
    return True

def main():
    """Test all skill files."""
    skills_dir = Path("skills")
    passed = 0
    failed = 0
    
    for skill_file in skills_dir.glob("**/*.md"):
        if test_skill_file(skill_file):
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
```

## Best Practices

1. **Validate early** - Run validation on every commit
2. **Test search** - Ensure search finds expected content
3. **Cover sections** - Verify progressive disclosure works
4. **Composition** - Test skill composition for new combinations
5. **Round-trip** - Verify files survive parse/recompose cycle

## Troubleshooting

**CI runs but tests fail locally:**
- Check Python version compatibility
- Ensure database is not locked
- Verify file paths are correct

**Search returns different results:**
- FTS5 configuration may differ
- Check database schema version
- Verify content is indexed

**Performance issues in CI:**
- Use smaller test datasets
- Parallelize independent tests
- Cache database between steps

---

*Integrate skill-split into your CI/CD pipeline for automated documentation quality assurance.*
