"""
TypeScript handler for skill-split.

This module provides TypeScript-specific parsing by extending the base
ScriptHandler with TypeScript language features.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from handlers.script_handler import ScriptHandler, RegexSymbolFinder
from models import ParsedDocument, Section, FileType, FileFormat


class TypeScriptHandler(ScriptHandler):
    """
    Handler for TypeScript (.ts, .tsx) files.

    Extends ScriptHandler with TypeScript-specific symbol detection including:
    - Interfaces (interface Name {})
    - Type aliases (type Name = ...)
    - Enums (enum Name {})
    - Generic classes and functions
    - Decorators (@decorator)
    - Namespaces (namespace Name {})
    - Modules (export module Name {})
    - Classes with extends/implements
    - Abstract classes and methods
    - Property signatures with access modifiers

    Section structure:
    - Top-level interfaces become sections
    - Top-level type aliases become sections
    - Top-level enums become sections
    - Top-level classes become sections (including abstract classes)
    - Top-level functions become sections (including arrow functions)
    - Methods are nested under their class
    - Module-level docstrings/comments are captured
    """

    # TypeScript-specific patterns (all handle optional 'export' prefix)
    TS_INTERFACE = re.compile(r'^(?:export\s+)?interface\s+(\w+)(?:\s*<[^>]+>)?\s*(?:extends\s+[\w\s,]+)?\s*{?')
    TS_TYPE = re.compile(r'^(?:export\s+)?type\s+(\w+)\s*(?:<[^>]+>)?\s*=')
    TS_ENUM = re.compile(r'^(?:export\s+)?enum\s+(\w+)\s*{?')
    TS_NAMESPACE = re.compile(r'^(?:export\s+)?namespace\s+(\w+)\s*{?')
    TS_DECORATOR = re.compile(r'^@(\w+)(?:\([^)]*\))?')
    TS_EXPORT = re.compile(r'^export\s+(?:(?:default|const|let|var|function|class|interface|type|enum|namespace)\s+)?(\w+)')
    TS_ABSTRACT_CLASS = re.compile(r'^(?:export\s+)?abstract\s+class\s+(\w+)(?:\s*<[^>]+>)?\s*(?:extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*{?')
    TS_CLASS = re.compile(r'^(?:export\s+)?class\s+(\w+)(?:\s*<[^>]+>)?\s*(?:extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*{?')
    TS_FUNCTION = re.compile(r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]+>)?\s*\(')
    TS_ARROW_FUNCTION = re.compile(r'^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::\s*[\w<>,\s]+)?\s*=\s*(?:async\s+)?(?:\([^)]*\)|(?:\w+))\s*=>')
    TS_METHOD = re.compile(r'^\s*(?:public|private|protected|readonly)?\s*(?:abstract\s+)?(?:static\s+)?(?:async\s+)?(\w+)\s*(?:<[^>]+>)?\s*\(')
    # Pattern to match export followed by a declaration
    TS_EXPORT_DECL = re.compile(r'^export\s+(?:async\s+)?function\s+(\w+)')

    def __init__(self, file_path: str):
        """
        Initialize TypeScript handler with file path.

        Args:
            file_path: Path to the TypeScript file (.ts or .tsx)
        """
        super().__init__(file_path, language="typescript")

    def get_file_format(self) -> FileFormat:
        """
        Return TypeScript/JavaScript file format.

        Returns:
            FileFormat.JAVASCRIPT_TYPESCRIPT
        """
        return FileFormat.JAVASCRIPT_TYPESCRIPT

    def _get_symbols_via_regex(self, lines: List[str]) -> List[dict]:
        """
        Get TypeScript symbols using regex-based parsing.

        Overrides the base ScriptHandler method with TypeScript-specific
        patterns for interfaces, types, enums, generics, decorators, etc.

        Args:
            lines: List of file lines

        Returns:
            List of symbol dictionaries with name, kind, line info

        Note:
            This method uses TypeScript-specific regex patterns to find
            symbols without relying on the base JavaScript finder, since
            TypeScript patterns are more comprehensive.
        """
        # Use base JavaScript finder and extend with TypeScript-specific patterns
        symbols = RegexSymbolFinder.find_javascript_symbols(lines)

        # Add TypeScript-specific symbols (interfaces, types, enums, namespaces)
        decorators = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                continue

            # Skip imports (but handle exports below)
            if stripped.startswith('import '):
                continue

            # Track decorators
            decorator_match = self.TS_DECORATOR.match(stripped)
            if decorator_match:
                decorators.append(i)
                continue

            # Check for namespace definition (TypeScript)
            namespace_match = self.TS_NAMESPACE.match(stripped)
            if namespace_match:
                end_line = RegexSymbolFinder._find_brace_end(lines, i)
                symbols.append({
                    "name": namespace_match.group(1),
                    "kind": "namespace",
                    "line_start": (decorators[0] if decorators else i) + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                decorators = []
                continue

            # Check for enum definition (TypeScript)
            enum_match = self.TS_ENUM.match(stripped)
            if enum_match:
                end_line = RegexSymbolFinder._find_brace_end(lines, i)
                symbols.append({
                    "name": enum_match.group(1),
                    "kind": "enum",
                    "line_start": (decorators[0] if decorators else i) + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                decorators = []
                continue

            # Check for interface (TypeScript)
            interface_match = self.TS_INTERFACE.match(stripped)
            if interface_match:
                end_line = RegexSymbolFinder._find_brace_end(lines, i)
                symbols.append({
                    "name": interface_match.group(1),
                    "kind": "interface",
                    "line_start": (decorators[0] if decorators else i) + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                decorators = []
                continue

            # Check for type alias (TypeScript)
            type_match = self.TS_TYPE.match(stripped)
            if type_match:
                end_line = RegexSymbolFinder._find_statement_end(lines, i)
                symbols.append({
                    "name": type_match.group(1),
                    "kind": "type",
                    "line_start": (decorators[0] if decorators else i) + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                decorators = []
                continue

        return symbols

    def _extract_module_docstring(self, lines: List[str]) -> str:
        """
        Extract module-level docstring or header comments for TypeScript.

        TypeScript uses JSDoc comments (/** ... */) for documentation.

        Args:
            lines: List of file lines

        Returns:
            Module docstring or header comments as string
        """
        if not lines:
            return ""

        # Look for JSDoc comment at the start
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            stripped = line.strip()
            if stripped.startswith('/**'):
                # Collect JSDoc comment lines
                comments = []
                for j in range(i, min(i + 50, len(lines))):
                    comments.append(lines[j])
                    if '*/' in lines[j]:
                        break
                return '\n'.join(comments)

            # Also look for regular single-line comments
            if stripped.startswith('//'):
                # Collect consecutive comment lines
                comments = []
                for j in range(i, min(i + 20, len(lines))):
                    if lines[j].strip().startswith('//'):
                        comments.append(lines[j])
                    elif not lines[j].strip():
                        comments.append(lines[j])
                    else:
                        break
                return '\n'.join(comments)

        return ""
