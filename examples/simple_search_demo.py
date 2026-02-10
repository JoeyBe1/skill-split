#!/usr/bin/env python3
"""
Simple Search Demo

Demonstrates basic skill-split search functionality.
Run after storing some files in the database.
"""

from core.database import DatabaseStore
from core.query import QueryAPI
from core.parser import Parser


def main():
    """Demonstrate progressive disclosure search."""

    # Initialize
    db = DatabaseStore("skill_split.db")
    parser = Parser()
    api = QueryAPI(db)

    print("🔍 skill-split Simple Search Demo")
    print("=" * 40)

    # Example 1: List all files
    print("\n📁 Files in database:")
    files = api.list_files()
    for file_info in files[:5]:  # Show first 5
        print(f"  - {file_info['path']} ({file_info['section_count']} sections)")

    # Example 2: Search for content
    query = "search"  # Change this to search for different terms
    print(f"\n🔎 Searching for: '{query}'")

    results = api.search_sections(query, limit=5)

    print(f"   Found {len(results)} results:")
    for result in results:
        print(f"  [{result['id']}] {result['heading']}")
        print(f"      File: {result['file_path']}")

    # Example 3: Get specific section
    if results:
        section_id = results[0]['id']
        print(f"\n📖 Loading section {section_id}:")

        section = api.get_section(section_id)
        if section:
            print(f"   Heading: {section.heading}")
            print(f"   Content preview: {section.content[:100]}...")

    # Example 4: Navigate to next section
    if results:
        section_id = results[0]['id']
        print(f"\n➡️  Next section after {section_id}:")

        next_section = api.get_next_section(section_id, results[0]['file_path'])
        if next_section:
            print(f"   [{next_section.id}] {next_section.heading}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
