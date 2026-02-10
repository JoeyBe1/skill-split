#!/usr/bin/env python3
"""
Skill Composition Example

Demonstrates how to compose new skills from existing library sections.
"""

from core.database import DatabaseStore
from core.query import QueryAPI
from core.skill_composer import SkillComposer
from core.parser import Parser


def compose_python_guide():
    """Compose a Python handler guide from library sections."""

    db = DatabaseStore("skill_split.db")
    api = QueryAPI(db)
    composer = SkillComposer(db)

    print("📝 Composing Python Handler Guide")
    print("=" * 40)

    # Search for relevant sections
    print("\n1️⃣  Searching for Python handler sections...")
    results = api.search_sections("python handler", limit=10)

    if not results:
        print("❌ No Python handler sections found. Store some first!")
        return

    # Select sections
    section_ids = [r['id'] for r in results[:5]]
    print(f"   Found {len(section_ids)} relevant sections")

    # Compose new skill
    print("\n2️⃣  Composing new skill...")
    new_skill = composer.compose_skill(
        section_ids=section_ids,
        name="Python Handler Guide",
        description="Complete guide to creating Python handlers",
        tags=["python", "handler", "guide"]
    )

    print(f"   Title: {new_skill['frontmatter']['name']}")
    print(f"   Sections: {len(new_skill['sections'])}")

    # Write to file
    output_path = "examples/composed_python_guide.md"
    print(f"\n3️⃣  Writing to {output_path}...")

    with open(output_path, 'w') as f:
        f.write(new_skill['content'])

    print(f"   ✅ Created {output_path}")

    # Validate the composed skill
    print("\n4️⃣  Validating composed skill...")
    parser = Parser()

    with open(output_path) as f:
        content = f.read()

    document = parser.parse(content, output_path)

    print(f"   ✅ Valid structure: {len(document.sections)} sections")

    return output_path


def compose_multi_file_component():
    """Compose a component from multiple files."""

    db = DatabaseStore("skill_split.db")
    api = QueryAPI(db)
    composer = SkillComposer(db)

    print("\n📦 Composing Multi-File Component")
    print("=" * 40)

    # Find plugin-related sections
    print("\n1️⃣  Finding plugin sections...")
    plugin_sections = api.search_sections("plugin", limit=5)

    # Find hook-related sections
    print("\n2️⃣  Finding hook sections...")
    hook_sections = api.search_sections("hook", limit=5)

    # Combine section IDs
    section_ids = []
    section_ids.extend([s['id'] for s in plugin_sections[:3]])
    section_ids.extend([s['id'] for s in hook_sections[:2]])

    print(f"   Selected {len(section_ids)} sections")

    # Compose
    print("\n3️⃣  Composing component...")
    component = composer.compose_skill(
        section_ids=section_ids,
        name="Plugin and Hook Integration",
        description="How plugins and hooks work together",
        tags=["plugin", "hook", "integration"]
    )

    output_path = "examples/composed_plugin_hooks.md"
    with open(output_path, 'w') as f:
        f.write(component['content'])

    print(f"   ✅ Created {output_path}")

    return output_path


def main():
    """Run composition examples."""

    print("🎨 Skill Composition Examples\n")

    # Example 1: Simple guide
    guide_path = compose_python_guide()

    # Example 2: Multi-file component
    component_path = compose_multi_file_component()

    print("\n✅ All composition examples complete!")
    print(f"\nCreated files:")
    print(f"  - {guide_path}")
    print(f"  - {component_path}")


if __name__ == "__main__":
    main()
