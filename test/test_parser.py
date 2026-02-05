"""
Unit tests for Parser class.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.parser import Parser
from core.detector import FormatDetector
from models import FileFormat, FileType, Section


class TestFormatDetector:
    """Test format detection."""

    def setup_method(self):
        """Setup test fixtures."""
        self.detector = FormatDetector()

    def test_detect_skill_file(self):
        """Test detection of skill files from path."""
        file_type, file_format = self.detector.detect(
            "/skills/test-skill/SKILL.md",
            "# Test\n\nContent"
        )
        assert file_type == FileType.SKILL
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_command_file(self):
        """Test detection of command files from path."""
        file_type, file_format = self.detector.detect(
            "/commands/sc/brainstorm.md",
            "# Test\n\nContent"
        )
        assert file_type == FileType.COMMAND

    def test_detect_markdown_headings(self):
        """Test detection of markdown heading format."""
        _, file_format = self.detector.detect(
            "test.md",
            "# Heading 1\n\n## Heading 2\n\nContent"
        )
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_empty_content(self):
        """Test detection of empty content."""
        _, file_format = self.detector.detect("test.md", "")
        assert file_format == FileFormat.UNKNOWN


class TestParserFrontmatter:
    """Test frontmatter extraction."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = Parser()

    def test_extract_valid_frontmatter(self):
        """Test extraction of valid YAML frontmatter."""
        content = """---
name: test
version: 1.0
---

# Content"""
        frontmatter, body = self.parser.extract_frontmatter(content)
        assert frontmatter == "name: test\nversion: 1.0\n"
        assert body == "\n# Content"

    def test_extract_no_frontmatter(self):
        """Test file without frontmatter."""
        content = "# Just content\n\nNo frontmatter here."
        frontmatter, body = self.parser.extract_frontmatter(content)
        assert frontmatter == ""
        assert body == content

    def test_extract_malformed_frontmatter(self):
        """Test malformed frontmatter (opening but no closing)."""
        content = """---
name: test
version: 1.0
# Content"""
        frontmatter, body = self.parser.extract_frontmatter(content)
        # Should treat entire thing as body (defensive)
        assert frontmatter == ""
        assert body == content

    def test_extract_empty_file(self):
        """Test empty file."""
        frontmatter, body = self.parser.extract_frontmatter("")
        assert frontmatter == ""
        assert body == ""


class TestParserHeadings:
    """Test heading-based parsing."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = Parser()

    def test_parse_simple_headings(self):
        """Test parsing simple heading structure."""
        content = """# Title

Content under title.

## Section 1

Content under section 1.

## Section 2

Content under section 2."""
        doc = self.parser.parse_headings(content)

        assert len(doc.sections) == 1
        assert doc.sections[0].title == "Title"
        assert doc.sections[0].level == 1

        # Check children (level 2 headings)
        assert len(doc.sections[0].children) == 2
        assert doc.sections[0].children[0].title == "Section 1"
        assert doc.sections[0].children[1].title == "Section 2"

    def test_parse_with_frontmatter(self):
        """Test parsing with frontmatter present."""
        content = """---
name: test
---

# Title

Content."""
        doc = self.parser.parse_headings(content)

        assert doc.frontmatter == "name: test\n"
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "Title"

    def test_code_block_not_split(self):
        """Test that headings in code blocks are not parsed."""
        content = """# Title

```python
# This is a comment, not a heading
def foo():
    pass

## Also not a heading
```

## Real Heading

Real content."""
        doc = self.parser.parse_headings(content)

        # Should only have "Title" and "Real Heading"
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "Title"
        assert len(doc.sections[0].children) == 1
        assert doc.sections[0].children[0].title == "Real Heading"

    def test_heading_level_jump(self):
        """Test handling of heading level jumps."""
        content = """# Level 1

### Level 3 (skipped level 2)

## Level 2 (back to normal)

# Level 1 again"""
        doc = self.parser.parse_headings(content)

        assert len(doc.sections) == 2  # Two level-1 headings
        assert doc.sections[0].level == 1
        assert doc.sections[0].children[0].level == 3
        assert doc.sections[0].children[1].level == 2

    def test_consecutive_headings(self):
        """Test consecutive headings with no content."""
        content = """# Heading 1

# Heading 2

## Subheading

Content here."""
        doc = self.parser.parse_headings(content)

        assert len(doc.sections) == 2
        # First section has empty content (just newline before next heading)
        assert doc.sections[0].title == "Heading 1"
        assert doc.sections[1].title == "Heading 2"


class TestRoundTrip:
    """Test round-trip parsing and recomposition."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = Parser()
        self.detector = FormatDetector()

    def test_round_trip_simple_skill(self):
        """Test round-trip of simple skill file."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "simple_skill.md"
        )
        with open(fixture_path) as f:
            original = f.read()

        # Parse
        file_type, file_format = self.detector.detect(fixture_path, original)
        doc = self.parser.parse(fixture_path, original, file_type, file_format)

        # Verify frontmatter preserved
        assert doc.frontmatter == """name: test-skill
description: A simple test skill
version: 1.0.0
"""

        # Verify structure
        assert len(doc.sections) >= 1

    def test_round_trip_no_frontmatter(self):
        """Test round-trip of file without frontmatter."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "no_frontmatter.md"
        )
        with open(fixture_path) as f:
            original = f.read()

        # Parse
        file_type, file_format = self.detector.detect(fixture_path, original)
        doc = self.parser.parse(fixture_path, original, file_type, file_format)

        # Verify no frontmatter
        assert doc.frontmatter == ""
        assert len(doc.sections) >= 1


class TestParserXmlTags:
    """Test XML tag-based parsing (Phase 4)."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = Parser()
        self.detector = FormatDetector()

    def test_detect_xml_tag_format(self):
        """Test detection of XML tag format."""
        content = """<example>
Content here.
</example>"""
        _, file_format = self.detector.detect("test.md", content)
        assert file_format == FileFormat.XML_TAGS

    def test_parse_simple_xml_tags(self):
        """Test parsing simple XML tag structure."""
        content = """<example>
This is example content.
</example>"""
        doc = self.parser.parse_xml_tags(content)

        assert len(doc.sections) == 1
        assert doc.sections[0].title == "example"
        assert doc.sections[0].level == -1  # XML tags use level=-1
        assert "This is example content." in doc.sections[0].content

    def test_parse_nested_xml_tags(self):
        """Test parsing nested XML tags."""
        content = """<outer>
Outer content.

<inner>
Inner content.
</inner>
</outer>"""
        doc = self.parser.parse_xml_tags(content)

        assert len(doc.sections) == 1
        assert doc.sections[0].title == "outer"
        assert len(doc.sections[0].children) == 1
        assert doc.sections[0].children[0].title == "inner"
        assert doc.sections[0].children[0].level == -1

    def test_parse_multiple_xml_tags(self):
        """Test parsing multiple top-level XML tags."""
        content = """<first>
First content.
</first>

<second>
Second content.
</second>"""
        doc = self.parser.parse_xml_tags(content)

        assert len(doc.sections) == 2
        assert doc.sections[0].title == "first"
        assert doc.sections[1].title == "second"

    def test_parse_xml_with_frontmatter(self):
        """Test parsing XML tags with frontmatter."""
        content = """---
name: test
---

<tag>
Content.
</tag>"""
        frontmatter, body = self.parser.extract_frontmatter(content)
        doc = self.parser.parse_xml_tags(content)

        assert doc.frontmatter == "name: test\n"
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "tag"

    def test_xml_round_trip_fixture(self):
        """Test round-trip of XML tag fixture file."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "xml_tags.md"
        )
        with open(fixture_path) as f:
            original = f.read()

        # Parse
        file_type, file_format = self.detector.detect(fixture_path, original)
        assert file_format == FileFormat.XML_TAGS

        doc = self.parser.parse(fixture_path, original, file_type, file_format)

        # Verify structure
        assert len(doc.sections) == 4  # example, nested, multiple, multiple (top-level)
        assert doc.sections[0].title == "example"
        assert doc.sections[1].title == "nested"
        assert len(doc.sections[1].children) == 1  # inner is a child
        assert doc.sections[1].children[0].title == "inner"
        assert doc.sections[2].title == "multiple"
        assert doc.sections[3].title == "multiple"


def run_tests():
    """Run all tests."""
    import traceback

    test_classes = [
        TestFormatDetector,
        TestParserFrontmatter,
        TestParserHeadings,
        TestParserXmlTags,
        TestRoundTrip,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                method = getattr(instance, method_name)
                try:
                    instance.setup_method()
                    method()
                    passed += 1
                    print(f"✓ {test_class.__name__}.{method_name}")
                except AssertionError as e:
                    failed += 1
                    print(f"✗ {test_class.__name__}.{method_name}")
                    print(f"  {e}")
                except Exception as e:
                    failed += 1
                    print(f"✗ {test_class.__name__}.{method_name}")
                    print(f"  ERROR: {e}")
                    traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
