#!/usr/bin/env python3
"""
Test component handlers on REAL Claude Code files.

Tests PluginHandler, HookHandler, and ConfigHandler on actual files
from the user's Claude Code installation.
"""

import json
import sys
from pathlib import Path

# Add handlers to path
sys.path.insert(0, str(Path(__file__).parent))

from handlers.plugin_handler import PluginHandler
from handlers.hook_handler import HookHandler
from handlers.config_handler import ConfigHandler
from core.hashing import compute_file_hash
from core.database import DatabaseStore
from core.query import QueryAPI
from models import FileType


def test_plugin_handler():
    """Test PluginHandler on real plugin.json file."""
    print("\n" + "="*80)
    print("TEST 1: PLUGIN HANDLER")
    print("="*80)

    # Use compound-engineering plugin as test case
    plugin_path = Path.home() / ".claude/plugins/marketplaces/every-marketplace/plugins/compound-engineering/.claude-plugin/plugin.json"

    if not plugin_path.exists():
        print(f"❌ Plugin file not found: {plugin_path}")
        return False

    print(f"📁 File path: {plugin_path}")
    print(f"📏 File size: {plugin_path.stat().st_size} bytes")

    # Compute hash of file
    original_hash = compute_file_hash(str(plugin_path))
    print(f"🔐 Original SHA256: {original_hash[:16]}...")

    # Create handler and parse (handler reads file itself)
    handler = PluginHandler(str(plugin_path))

    # Parse
    print("\n--- PARSE ---")
    try:
        doc = handler.parse()
        print(f"✅ Parse successful!")
        print(f"   - Sections: {len(doc.sections)}")
        print(f"   - File type: {doc.file_type.value}")
        print(f"   - Format: {doc.format.value}")
        print(f"   - Frontmatter: {doc.frontmatter[:100]}...")

        for section in doc.sections:
            print(f"   - Section '{section.title}': {len(section.content)} chars")
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        return False

    # Validate
    print("\n--- VALIDATE ---")
    validation = handler.validate()
    print(f"✅ Valid: {validation.is_valid}")
    if validation.errors:
        print(f"   Errors: {validation.errors}")
    if validation.warnings:
        print(f"   Warnings: {validation.warnings}")

    # Check related files
    print("\n--- RELATED FILES ---")
    related = handler.get_related_files()
    print(f"✅ Related files: {len(related)}")
    for rel_path in related:
        rel_file = Path(rel_path)
        print(f"   - {rel_file.name} ({rel_file.stat().st_size} bytes)")

    return True


def test_hook_handler():
    """Test HookHandler on real hooks.json file."""
    print("\n" + "="*80)
    print("TEST 2: HOOK HANDLER")
    print("="*80)

    # Use ralph hooks as test case
    hook_path = Path.home() / ".claude/hooks/ralph/hooks.json"

    if not hook_path.exists():
        print(f"❌ Hook file not found: {hook_path}")
        return False

    print(f"📁 File path: {hook_path}")
    print(f"📏 File size: {hook_path.stat().st_size} bytes")

    # Compute hash of file
    original_hash = compute_file_hash(str(hook_path))
    print(f"🔐 Original SHA256: {original_hash[:16]}...")

    # Create handler and parse (handler reads file itself)
    handler = HookHandler(str(hook_path))

    # Parse
    print("\n--- PARSE ---")
    try:
        doc = handler.parse()
        print(f"✅ Parse successful!")
        print(f"   - Sections: {len(doc.sections)}")
        print(f"   - File type: {doc.file_type.value}")
        print(f"   - Format: {doc.format.value}")
        print(f"   - Frontmatter: {doc.frontmatter[:100]}...")

        for section in doc.sections:
            print(f"   - Section '{section.title}': {len(section.content)} chars")
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Validate
    print("\n--- VALIDATE ---")
    validation = handler.validate()
    print(f"✅ Valid: {validation.is_valid}")
    if validation.errors:
        print(f"   Errors: {validation.errors}")
    if validation.warnings:
        print(f"   Warnings: {validation.warnings}")

    # Check related files
    print("\n--- RELATED FILES ---")
    related = handler.get_related_files()
    print(f"✅ Related files: {len(related)}")
    for rel_path in related:
        rel_file = Path(rel_path)
        print(f"   - {rel_file.name} ({rel_file.stat().st_size} bytes)")

    return True


def test_config_handler():
    """Test ConfigHandler on real settings.json file."""
    print("\n" + "="*80)
    print("TEST 3: CONFIG HANDLER")
    print("="*80)

    # Use settings.json as test case
    config_path = Path.home() / ".claude/settings.json"

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False

    print(f"📁 File path: {config_path}")
    print(f"📏 File size: {config_path.stat().st_size} bytes")

    # Compute hash of file
    original_hash = compute_file_hash(str(config_path))
    print(f"🔐 Original SHA256: {original_hash[:16]}...")

    # Create handler and parse (handler reads file itself)
    handler = ConfigHandler(str(config_path))

    # Parse
    print("\n--- PARSE ---")
    try:
        doc = handler.parse()
        print(f"✅ Parse successful!")
        print(f"   - Sections: {len(doc.sections)}")
        print(f"   - File type: {doc.file_type.value}")
        print(f"   - Format: {doc.format.value}")
        print(f"   - Frontmatter: {doc.frontmatter[:100]}...")

        for section in doc.sections:
            print(f"   - Section '{section.title}': {len(section.content)} chars")
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Validate
    print("\n--- VALIDATE ---")
    validation = handler.validate()
    print(f"✅ Valid: {validation.is_valid}")
    if validation.errors:
        print(f"   Errors: {validation.errors}")
    if validation.warnings:
        print(f"   Warnings (first 5):")
        for warning in validation.warnings[:5]:
            print(f"      - {warning}")
        if len(validation.warnings) > 5:
            print(f"      ... and {len(validation.warnings) - 5} more")

    # Check related files
    print("\n--- RELATED FILES ---")
    related = handler.get_related_files()
    print(f"✅ Related files: {len(related)} (none expected for configs)")

    return True


def test_database_storage(db_path: str):
    """Test storing parsed components to database."""
    print("\n" + "="*80)
    print("TEST 4: DATABASE STORAGE")
    print("="*80)

    # Clean test database
    test_db = Path(db_path)
    if test_db.exists():
        test_db.unlink()

    db = DatabaseStore(str(test_db))

    # Test storing a config file
    config_path = Path.home() / ".claude/settings.json"

    handler = ConfigHandler(str(config_path))
    doc = handler.parse()
    content_hash = compute_file_hash(str(config_path))

    print(f"📁 Storing: {config_path.name}")
    file_id = db.store_file(str(config_path), doc, content_hash)

    if file_id:
        print(f"✅ Stored successfully! File ID: {file_id}")
    else:
        print(f"❌ Store failed!")
        return False

    # Test retrieval (get_file expects path, not ID)
    print("\n--- RETRIEVAL ---")
    retrieved = db.get_file(str(config_path))

    if retrieved:
        print(f"✅ Retrieved successfully!")
        metadata, sections = retrieved
        print(f"   - Metadata: {metadata.path}")
        print(f"   - Sections: {len(sections)}")
        for section in sections[:3]:  # Show first 3
            print(f"      - {section.title} ({len(section.content)} chars)")
    else:
        print(f"❌ Retrieval failed!")
        return False

    # Test search
    print("\n--- SEARCH ---")
    query_api = QueryAPI(str(test_db))
    search_results = query_api.search_sections("permissions")

    print(f"✅ Found {len(search_results)} matching sections")
    for section_id, section in search_results[:3]:
        print(f"   - [{section_id}] {section.title}")

    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("REAL COMPONENT HANDLER TEST SUITE")
    print("="*80)
    print("\nTesting on actual Claude Code installation files:")
    print(f"  - Plugin: ~/.claude/plugins/marketplaces/*/plugins/*/.claude-plugin/plugin.json")
    print(f"  - Hook:   ~/.claude/hooks/*/hooks.json")
    print(f"  - Config: ~/.claude/settings.json")

    results = {}

    # Test 1: Plugin Handler
    try:
        results['plugin'] = test_plugin_handler()
    except Exception as e:
        print(f"\n❌ PLUGIN TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results['plugin'] = False

    # Test 2: Hook Handler
    try:
        results['hook'] = test_hook_handler()
    except Exception as e:
        print(f"\n❌ HOOK TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results['hook'] = False

    # Test 3: Config Handler
    try:
        results['config'] = test_config_handler()
    except Exception as e:
        print(f"\n❌ CONFIG TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results['config'] = False

    # Test 4: Database Storage
    try:
        db_path = Path(__file__).parent / "test-components.db"
        results['database'] = test_database_storage(str(db_path))
    except Exception as e:
        print(f"\n❌ DATABASE TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results['database'] = False

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper():12} {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} tests passed")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
