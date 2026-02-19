#!/usr/bin/env python3
"""
skill-split Interactive Shell

A REPL for exploring skill-split functionality interactively.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_split import SkillSplit
from core.database import Database
from core.query import QueryAPI


class SkillSplitShell:
    """Interactive shell for skill-split."""

    def __init__(self):
        self.ss = SkillSplit()
        self.db = Database(":memory:")
        self.query = QueryAPI(self.db)
        self.running = True

    def cmd_help(self, args=None):
        """Show available commands."""
        commands = [
            ("parse <file>", "Parse a markdown file"),
            ("store <file>", "Store file in database"),
            ("list [file]", "List sections in file"),
            ("get <id>", "Get section by ID"),
            ("search <query>", "BM25 keyword search"),
            ("next <id> [file]", "Get next section"),
            ("tree <file>", "Show section tree"),
            ("stats", "Show database stats"),
            ("quit", "Exit shell"),
        ]
        print("\nAvailable commands:")
        for cmd, desc in commands:
            print(f"  {cmd:<30} {desc}")
        print()

    def cmd_parse(self, args):
        """Parse a file."""
        if not args:
            print("Usage: parse <file>")
            return
        try:
            doc = self.ss.parse_file(args)
            print(f"Parsed {len(doc.sections)} sections from {args}")
            print(f"Title: {doc.metadata.frontmatter.get('title', 'N/A')}")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_store(self, args):
        """Store a file in database."""
        if not args:
            print("Usage: store <file>")
            return
        try:
            doc = self.ss.parse_file(args)
            self.db.store_document(doc)
            print(f"Stored {len(doc.sections)} sections")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_list(self, args):
        """List sections."""
        filename = args if args else None
        try:
            sections = self.query.list_sections(filename) if filename else self.query.list_sections()
            for section in sections[:20]:  # Limit output
                indent = "  " * (section.level - 1)
                print(f"{indent}[{section.id}] {section.heading}")
            if len(sections) > 20:
                print(f"... and {len(sections) - 20} more")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_get(self, args):
        """Get section by ID."""
        if not args or not args.isdigit():
            print("Usage: get <id>")
            return
        try:
            section = self.query.get_section(int(args))
            print(f"\n[{section.id}] {section.heading}")
            print(f"Level: {section.level}")
            print(f"Lines: {section.line_start}-{section.line_end}")
            print(f"\n{section.content}\n")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_search(self, args):
        """Search sections."""
        if not args:
            print("Usage: search <query>")
            return
        try:
            results = self.query.search_sections(args, limit=10)
            print(f"\nFound {len(results)} results for '{args}':\n")
            for result in results:
                section = result.section
                print(f"[{section.id}] ({result.score:.3f}) {section.heading}")
                print(f"  {section.content[:80]}...\n")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_next(self, args):
        """Get next section."""
        parts = args.split() if args else []
        if len(parts) < 2:
            print("Usage: next <id> <file> [--child]")
            return
        try:
            section_id = int(parts[0])
            filename = parts[1]
            child = "--child" in parts
            section = self.query.get_next_section(section_id, filename, child=child)
            if section:
                print(f"[{section.id}] {section.heading}")
            else:
                print("No more sections")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_tree(self, args):
        """Show section tree."""
        if not args:
            print("Usage: tree <file>")
            return
        try:
            sections = self.query.list_sections(args)
            print(f"\nSection tree for {args}:\n")
            for section in sections:
                indent = "  " * (section.level - 1)
                prefix = "├─" if section.level > 1 else ""
                print(f"{indent}{prefix} [{section.id}] {section.heading}")
            print()
        except Exception as e:
            print(f"Error: {e}")

    def cmd_stats(self, args=None):
        """Show database statistics."""
        try:
            sections = self.query.list_sections()
            print(f"\nDatabase Statistics:")
            print(f"  Total sections: {len(sections)}")
            print(f"  Files: {len(set(s.file_path for s in sections))}")
            print(f"  Avg section size: {sum(len(s.content) for s in sections) // len(sections)} bytes")
            print()
        except Exception as e:
            print(f"Error: {e}")

    def cmd_quit(self, args=None):
        """Exit shell."""
        self.running = False
        print("Goodbye!")

    def run(self):
        """Run the interactive shell."""
        print("╔════════════════════════════════════════════════╗")
        print("║     skill-split Interactive Shell v1.0.0      ║")
        print("║    Type 'help' for available commands          ║")
        print("╚════════════════════════════════════════════════╝")
        print()

        while self.running:
            try:
                cmd_input = input("skill-split> ").strip()
                if not cmd_input:
                    continue

                parts = cmd_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                method = getattr(self, f"cmd_{command}", None)
                if method:
                    method(args)
                else:
                    print(f"Unknown command: {command}. Type 'help' for commands.")

            except (KeyboardInterrupt, EOFError):
                print("\nUse 'quit' to exit.")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    shell = SkillSplitShell()
    shell.run()
