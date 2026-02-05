#!/usr/bin/env python3
"""
Demo of script handler functionality.

This demo shows how to parse and decompose Python, JavaScript,
TypeScript, and Shell files for progressive disclosure.
"""

import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.python_handler import PythonHandler
from handlers.javascript_handler import JavaScriptHandler
from handlers.typescript_handler import TypeScriptHandler
from handlers.shell_handler import ShellHandler


def demo_python_handler():
    """Demonstrate Python handler with class and function parsing."""
    print("\n" + "=" * 60)
    print("PYTHON HANDLER DEMO")
    print("=" * 60)

    # Create a sample Python file
    sample_python = '''"""Module docstring example."""

from typing import List


class DataProcessor:
    """Process data with various methods."""

    def __init__(self, name: str):
        self.name = name

    def process(self, data: List[str]) -> List[str]:
        """Process the input data."""
        return [d.upper() for d in data]


def helper_function(x: int) -> int:
    """A helper function."""
    return x * 2
'''

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_python)
        temp_path = f.name

    try:
        # Parse with PythonHandler
        handler = PythonHandler(temp_path)
        doc = handler.parse()

        print(f"\nSections found: {len(doc.sections)}")
        for section in doc.sections:
            print(f"\n  [{section.level}] {section.title}")
            print(f"     Lines: {section.line_start}-{section.line_end}")
            kind_attr = getattr(section, 'kind', 'N/A')
            print(f"     Kind: {kind_attr}")
    finally:
        os.unlink(temp_path)


def demo_javascript_handler():
    """Demonstrate JavaScript handler with ES6+ syntax."""
    print("\n" + "=" * 60)
    print("JAVASCRIPT HANDLER DEMO")
    print("=" * 60)

    sample_js = '''/**
 * JSDoc module header
 */

class UserService {
    constructor(apiClient) {
        this.apiClient = apiClient;
    }

    async getUser(id) {
        return await this.apiClient.get(`/users/${id}`);
    }
}

const processData = (data) => {
    return data.map(x => x * 2);
};
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(sample_js)
        temp_path = f.name

    try:
        handler = JavaScriptHandler(temp_path)
        doc = handler.parse()

        print(f"\nSections found: {len(doc.sections)}")
        for section in doc.sections:
            print(f"\n  [{section.level}] {section.title}")
            print(f"     Lines: {section.line_start}-{section.line_end}")
    finally:
        os.unlink(temp_path)


def demo_typescript_handler():
    """Demonstrate TypeScript handler with interfaces and types."""
    print("\n" + "=" * 60)
    print("TYPESCRIPT HANDLER DEMO")
    print("=" * 60)

    sample_ts = '''/**
 * TypeScript module with interfaces and types
 */

interface User {
    id: number;
    name: string;
    email: string;
}

type UserRole = 'admin' | 'user' | 'guest';

class UserService {
    private users: Map<number, User> = new Map();

    getUser(id: number): User | undefined {
        return this.users.get(id);
    }
}
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
        f.write(sample_ts)
        temp_path = f.name

    try:
        handler = TypeScriptHandler(temp_path)
        doc = handler.parse()

        print(f"\nSections found: {len(doc.sections)}")
        for section in doc.sections:
            print(f"\n  [{section.level}] {section.title}")
            print(f"     Lines: {section.line_start}-{section.line_end}")
    finally:
        os.unlink(temp_path)


def demo_shell_handler():
    """Demonstrate Shell handler with function parsing."""
    print("\n" + "=" * 60)
    print("SHELL HANDLER DEMO")
    print("=" * 60)

    sample_shell = '''#!/bin/bash
#
# Shell script demo
#

## Configuration Section
CONFIG_FILE="/etc/config"

deploy_app() {
    echo "Deploying application..."
    # deployment logic here
}

check_status() {
    if [ -f "$CONFIG_FILE" ]; then
        echo "Config found"
    fi
}
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(sample_shell)
        temp_path = f.name

    try:
        handler = ShellHandler(temp_path)
        doc = handler.parse()

        print(f"\nSections found: {len(doc.sections)}")
        for section in doc.sections:
            print(f"\n  [{section.level}] {section.title}")
            print(f"     Lines: {section.line_start}-{section.line_end}")
    finally:
        os.unlink(temp_path)


def demo_round_trip():
    """Demonstrate byte-perfect round-trip verification."""
    print("\n" + "=" * 60)
    print("ROUND-TRIP VERIFICATION DEMO")
    print("=" * 60)

    original = '''"""Test module."""


class TestClass:
    """A test class."""

    def test_method(self):
        """Test method."""
        return 42
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(original)
        temp_path = f.name

    try:
        handler = PythonHandler(temp_path)
        doc = handler.parse()
        recomposed = handler.recompose(doc.sections)

        if recomposed == original:
            print("\n✓ Round-trip successful!")
            print("  Original and recomposed content match byte-for-byte")
        else:
            print("\n✗ Round-trip failed")
            print(f"  Original length: {len(original)}")
            print(f"  Recomposed length: {len(recomposed)}")
    finally:
        os.unlink(temp_path)


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("SCRIPT HANDLERS DEMO")
    print("Demonstrating progressive disclosure for code files")
    print("=" * 60)

    demo_python_handler()
    demo_javascript_handler()
    demo_typescript_handler()
    demo_shell_handler()
    demo_round_trip()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Features:")
    print("  • Parse code files by symbol (classes, functions, interfaces)")
    print("  • Support for Python, JavaScript, TypeScript, Shell")
    print("  • Byte-perfect round-trip verification")
    print("  • Progressive disclosure via section-based storage")
    print("  • LSP-ready architecture for future enhancements")
    print()


if __name__ == "__main__":
    main()
