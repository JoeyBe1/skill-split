#!/usr/bin/env python3
"""
Complete skill-split Workflow Example

Demonstrates a complete end-to-end workflow:
1. Parse documentation
2. Store in database
3. Search using multiple modes
4. Navigate sections progressively
5. Reconstruct with verification
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_split import SkillSplit
from core.database import Database
from core.query import QueryAPI
from core.recomposer import Recomposer


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main():
    """Run complete workflow example."""
    print_section("skill-split Complete Workflow Example")

    # Initialize
    print("\n1. Initializing...")
    ss = SkillSplit()
    db = Database(":memory:")  # Use in-memory for demo
    query = QueryAPI(db)
    recomposer = Recomposer()

    # Sample markdown content
    sample_md = """---
title: Example Document
author: skill-split
version: 1.0.0
---

# Introduction

This is a sample document demonstrating skill-split's capabilities.

## Features

- Progressive disclosure
- Byte-perfect round-trip
- Multi-mode search

### Token Savings

Load only what you need, save up to 99% on tokens.

## Performance

Fast parsing and indexing for large documentation sets.

### Benchmarks

- Parse 1KB: 0.013ms
- Search: 5.8ms average

# Conclusion

skill-split enables efficient documentation workflows.
"""

    # Parse
    print_section("2. Parsing Document")
    doc = ss.parse_string(sample_md)
    print(f"✓ Parsed {len(doc.sections)} sections")
    print(f"✓ Title: {doc.metadata.frontmatter.get('title', 'N/A')}")

    # Store
    print_section("3. Storing in Database")
    db.store_document(doc)
    print(f"✓ Stored {len(doc.sections)} sections")
    print(f"✓ Database: {db.db_path}")

    # List sections
    print_section("4. Section Hierarchy")
    all_sections = query.list_sections("example.md")
    for section in all_sections:
        indent = "  " * (section.level - 1)
        print(f"{indent}├─ [{section.id}] {section.heading}")

    # Search - BM25
    print_section("5. BM25 Keyword Search")
    print("Searching for: 'performance'")
    bm25_results = query.search_sections("performance", limit=3)
    for result in bm25_results:
        section = result.section
        print(f"  [{result.rank}] Score: {result.score:.3f}")
        print(f"      Section: {section.heading}")
        print(f"      Preview: {section.content[:60]}...")

    # Search - Semantic
    print_section("6. Semantic Vector Search")
    print("Searching for: 'speed and efficiency'")
    try:
        semantic_results = query.hybrid_search(
            query="speed and efficiency",
            vector_weight=1.0,
            limit=3
        )
        for result in semantic_results:
            section = result.section
            print(f"  [{result.rank}] Score: {result.score:.3f}")
            print(f"      Section: {section.heading}")
    except Exception as e:
        print(f"  (Skipped - requires API key: {e})")

    # Progressive disclosure
    print_section("7. Progressive Disclosure")
    intro_section = query.get_section_by_heading("Introduction")
    if intro_section:
        print(f"Loaded: '{intro_section.heading}'")
        print(f"Content size: {len(intro_section.content)} bytes")
        print(f"Content:\n{intro_section.content}")

    # Navigate to next
    print_section("8. Navigation")
    next_section = query.get_next_section(intro_section.id, "example.md")
    if next_section:
        print(f"Next sibling: '{next_section.heading}'")

    # Drill down
    features_section = query.get_section_by_heading("Features")
    if features_section:
        first_child = query.get_next_section(
            features_section.id,
            "example.md",
            child=True
        )
        if first_child:
            print(f"First child: '{first_child.heading}'")

    # Round-trip verification
    print_section("9. Round-Trip Verification")
    all_sections = query.list_sections("example.md")
    reconstructed = recomposer.recompose(all_sections)
    print(f"✓ Original: {len(sample_md)} bytes")
    print(f"✓ Reconstructed: {len(reconstructed)} bytes")
    print(f"✓ Match: {sample_md == reconstructed}")

    # Statistics
    print_section("10. Database Statistics")
    total_sections = len(query.list_sections())
    print(f"  Total sections: {total_sections}")
    print(f"  Avg section size: {sum(len(s.content) for s in all_sections) // total_sections} bytes")

    print_section("Example Complete!")
    print("\nTry these commands:")
    print("  ./skill_split.py parse README.md")
    print("  ./skill_split.py search 'query'")
    print("  ./skill_split.py get-section <id>")


if __name__ == "__main__":
    main()
