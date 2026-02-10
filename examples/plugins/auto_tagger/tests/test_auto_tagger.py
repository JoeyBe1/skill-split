#!/usr/bin/env python3
"""
Tests for Auto-Tagger Plugin
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import (
    AutoTagger,
    TextAnalyzer,
    TagSuggestion,
    format_suggestions
)


class TestTagSuggestion:
    """Test TagSuggestion dataclass"""

    def test_create_suggestion(self):
        """Test creating a tag suggestion"""
        suggestion = TagSuggestion(
            tag="python",
            confidence=0.9,
            category="technology",
            source="frequency"
        )

        assert suggestion.tag == "python"
        assert suggestion.confidence == 0.9
        assert suggestion.category == "technology"
        assert suggestion.source == "frequency"


class TestTextAnalyzer:
    """Test TextAnalyzer class"""

    def test_init_default(self):
        """Test analyzer initialization with defaults"""
        analyzer = TextAnalyzer()

        assert analyzer.min_tag_length == 3
        assert analyzer.max_tag_length == 30
        assert len(analyzer.stop_words) > 0

    def test_init_with_config(self):
        """Test analyzer with custom config"""
        config = {"min_tag_length": 2, "max_tag_length": 20}
        analyzer = TextAnalyzer(config)

        assert analyzer.min_tag_length == 2
        assert analyzer.max_tag_length == 20

    def test_extract_words(self):
        """Test word extraction"""
        analyzer = TextAnalyzer()
        text = "Python is a great programming language for data science."

        words = analyzer.extract_words(text)

        assert "python" in words
        assert "great" in words
        assert "programming" in words
        assert "language" in words
        assert "data" in words
        assert "science" in words

        # Stop words should be filtered
        assert "is" not in words
        assert "a" not in words
        assert "for" not in words

    def test_extract_words_from_code(self):
        """Test word extraction from code blocks"""
        analyzer = TextAnalyzer()
        text = """
        # Python Tutorial

        ```python
        def hello():
            print("Hello, World!")
        ```

        Learn Python programming today.
        """

        words = analyzer.extract_words(text)

        # Code block content should be handled
        assert "python" in words
        assert "tutorial" in words
        assert "learn" in words
        assert "programming" in words

    def test_extract_ngrams(self):
        """Test n-gram extraction"""
        analyzer = TextAnalyzer()
        words = ["python", "programming", "language", "data", "science"]

        bigrams = analyzer.extract_ngrams(words, 2)

        assert "python programming" in bigrams
        assert "programming language" in bigrams
        assert "data science" in bigrams

    def test_extract_ngrams_with_stop_words(self):
        """Test n-gram extraction filters stop words"""
        analyzer = TextAnalyzer()
        words = ["python", "is", "great", "programming", "language"]

        bigrams = analyzer.extract_ngrams(words, 2)

        # Should not include n-grams with stop words
        assert "python is" not in bigrams
        assert "is great" not in bigrams
        assert "great programming" in bigrams


class TestAutoTagger:
    """Test AutoTagger class"""

    def test_init(self):
        """Test auto-tagger initialization"""
        tagger = AutoTagger()

        assert isinstance(tagger.analyzer, TextAnalyzer)
        assert len(tagger.category_patterns) > 0

    def test_suggest_tags_basic(self):
        """Test basic tag suggestion"""
        tagger = AutoTagger()
        content = """
        # Python Programming Tutorial

        Python is a popular programming language used for web development,
        data science, and automation. Learn Python programming basics.
        """

        suggestions = tagger.suggest_tags(content, count=5)

        assert len(suggestions) <= 5
        assert len(suggestions) > 0

        # Check for expected tags
        tags = [s.tag for s in suggestions]
        assert "python" in tags or "programming" in tags

    def test_suggest_tags_with_code(self):
        """Test tag suggestion from code blocks"""
        tagger = AutoTagger()
        content = """
        # React Tutorial

        ```javascript
        import React from 'react';

        function App() {
            return <div>Hello React</div>;
        }
        ```
        """

        suggestions = tagger.suggest_tags(content, count=10)

        tags = [s.tag for s in suggestions]
        assert "javascript" in tags or "react" in tags

    def test_suggest_tags_categorization(self):
        """Test that tags are categorized"""
        tagger = AutoTagger()
        content = """
        Learn Docker containerization and Kubernetes orchestration.
        Use Git for version control.
        """

        suggestions = tagger.suggest_tags(content, count=10)

        # Some suggestions should have categories
        categorized = [s for s in suggestions if s.category is not None]
        assert len(categorized) > 0

    def test_extract_keywords(self):
        """Test keyword extraction"""
        tagger = AutoTagger()
        content = """
        Python is a great programming language for data science and
        machine learning applications.
        """

        keywords = tagger.extract_keywords(content, count=5)

        assert len(keywords) <= 5
        assert len(keywords) > 0
        assert isinstance(keywords[0], str)

    def test_categorize_term(self):
        """Test term categorization"""
        tagger = AutoTagger()

        assert tagger._categorize_term("python") == "technology"
        assert tagger._categorize_term("react") == "framework"
        assert tagger._categorize_term("docker") == "tool"
        assert tagger._categorize_term("api") == "concept"

    def test_update_frontmatter_create(self):
        """Test creating frontmatter with tags"""
        content = "# My Document\\n\\nSome content here."

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()

            tagger = AutoTagger()
            success = tagger.update_frontmatter(
                f.name,
                ["python", "tutorial"],
                backup=False
            )

            assert success is True

            # Verify file was updated
            with open(f.name, 'r') as rf:
                updated = rf.read()

            assert "---" in updated
            assert "python" in updated
            assert "tutorial" in updated

            Path(f.name).unlink()

    def test_update_frontmatter_existing(self):
        """Test updating existing frontmatter"""
        content = """---
title: My Document
---

# Content

Some content.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()

            tagger = AutoTagger()
            success = tagger.update_frontmatter(
                f.name,
                ["python", "tutorial"],
                backup=False
            )

            assert success is True

            # Verify file was updated
            with open(f.name, 'r') as rf:
                updated = rf.read()

            assert "python" in updated
            assert "tutorial" in updated
            assert "title" in updated  # Original field preserved

            Path(f.name).unlink()

    def test_update_frontmatter_with_backup(self):
        """Test that backup is created"""
        content = "# My Document\\n\\nContent"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            original_path = f.name

            tagger = AutoTagger()
            success = tagger.update_frontmatter(
                original_path,
                ["python"],
                backup=True
            )

            assert success is True

            # Find backup file
            backup_files = list(Path(original_path).parent.glob(f"{Path(original_path).stem}.bak.*"))
            assert len(backup_files) > 0

            # Cleanup
            Path(original_path).unlink()
            for bf in backup_files:
                bf.unlink()

    def test_parse_simple_yaml(self):
        """Test simple YAML parsing"""
        tagger = AutoTagger()

        yaml_text = """title: Test Document
description: A test
tags: [python, tutorial]
author: Test Author
"""

        parsed = tagger._parse_simple_yaml(yaml_text)

        assert parsed["title"] == "Test Document"
        assert parsed["description"] == "A test"
        assert "python" in parsed["tags"]
        assert parsed["author"] == "Test Author"

    def test_build_frontmatter(self):
        """Test frontmatter building"""
        tagger = AutoTagger()

        data = {
            "title": "Test",
            "tags": ["python", "tutorial"]
        }

        frontmatter = tagger._build_frontmatter(data)

        assert frontmatter.startswith("---")
        assert frontmatter.endswith("---\n")
        assert "title: Test" in frontmatter
        assert "- python" in frontmatter
        assert "- tutorial" in frontmatter


class TestFormatSuggestions:
    """Test suggestion formatting"""

    def test_format_text(self):
        """Test text format"""
        suggestions = [
            TagSuggestion(tag="python", confidence=0.9, category="technology"),
            TagSuggestion(tag="tutorial", confidence=0.7, source="frequency")
        ]

        output = format_suggestions(suggestions, "text")

        assert "Suggested Tags" in output
        assert "python" in output
        assert "tutorial" in output
        assert "90.00%" in output or "90%" in output

    def test_format_json(self):
        """Test JSON format"""
        suggestions = [
            TagSuggestion(tag="python", confidence=0.9, category="technology")
        ]

        output = format_suggestions(suggestions, "json")
        data = json.loads(output)

        assert len(data) == 1
        assert data[0]["tag"] == "python"
        assert data[0]["confidence"] == 0.9
        assert data[0]["category"] == "technology"


class TestIntegration:
    """Integration tests"""

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing"""
        content = """---
title: Python Data Science Tutorial
description: Learn data science with Python
---

# Introduction

Python is a powerful programming language for data science.

## Libraries

Popular libraries include:

- NumPy for numerical computing
- Pandas for data manipulation
- Matplotlib for visualization

```python
import pandas as pd
import numpy as np

data = pd.DataFrame({'values': [1, 2, 3]})
```

## Getting Started

Start your Python data science journey today!
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            yield f.name

        Path(f.name).unlink()

    def test_full_workflow(self, sample_document):
        """Test complete workflow: suggest -> update -> verify"""
        tagger = AutoTagger()

        # Step 1: Read content and suggest tags
        with open(sample_document, 'r') as f:
            content = f.read()

        suggestions = tagger.suggest_tags(content, count=5)
        assert len(suggestions) > 0

        # Step 2: Update frontmatter
        tags = [s.tag for s in suggestions[:3]]
        success = tagger.update_frontmatter(
            sample_document,
            tags,
            backup=False
        )
        assert success is True

        # Step 3: Verify update
        with open(sample_document, 'r') as f:
            updated = f.read()

        for tag in tags:
            assert tag in updated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
