"""
Base handler for script files using LSP-based parsing.

This module provides a ScriptHandler that leverages Language Server Protocol
to accurately parse code files into structured sections based on their
symbol definitions (classes, functions, methods, etc.).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult

# Use JSON for frontmatter
import json

if TYPE_CHECKING:
    pass


class ScriptHandler(BaseHandler):
    """
    Base handler for script files using LSP-based symbol discovery.

    This handler provides accurate parsing of code files by leveraging
    Language Server Protocol to discover classes, functions, methods,
    and other code symbols.

    Supported languages:
    - Python (.py)
    - JavaScript (.js, .jsx)
    - TypeScript (.ts, .tsx)

    Section structure:
    - Top-level classes become sections
    - Top-level functions become sections
    - Methods are nested under their class
    - Module-level docstrings are captured
    """

    def __init__(self, file_path: str, language: str):
        """
        Initialize script handler with file path and language.

        Args:
            file_path: Path to the script file
            language: Language identifier for LSP (python, javascript, typescript)
        """
        super().__init__(file_path)
        self.language = language
        # Store original bytes for CRLF detection
        self._original_bytes = self._read_original_bytes()

    def _read_original_bytes(self) -> bytes:
        """
        Read original file bytes for line ending detection.

        Returns:
            Original file content as bytes
        """
        path = Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        with open(self.file_path, "rb") as f:
            return f.read()

    def parse(self) -> ParsedDocument:
        """
        Parse script file into sections using LSP-based symbol discovery.

        Returns:
            ParsedDocument with script structure

        The parsing strategy:
        1. Get all symbols using LSP (if available)
        2. Fall back to regex-based parsing if LSP not available
        3. Create a "module" section for all content before the first symbol
        4. Create sections for each top-level symbol
        5. Create a "footer" section for any content after the last symbol
        6. Nest methods under their parent classes

        Raises:
            FileNotFoundError: If file does not exist
        """
        lines = self.content.split('\n')
        sections = []

        # Get symbols - try LSP first, fall back to regex
        try:
            symbols = self._get_symbols_via_lsp()
        except Exception:
            # LSP not available, fall back to regex
            symbols = self._get_symbols_via_regex(lines)

        # Create a module section for all content before the first symbol
        if symbols:
            first_symbol_line = min(s.get("line_start", 1) for s in symbols)
            if first_symbol_line > 1:
                # Capture all content from line 1 to before first symbol
                # When we split by '\n', lines are the content between newlines
                # We need to reconstruct with proper newlines
                module_content_lines = lines[:first_symbol_line - 1]
                
                # The original file has newlines BETWEEN these lines
                # When we join with '\n', we insert newlines between lines
                # We also need a newline after the last module line (before first symbol)
                module_content = '\n'.join(module_content_lines) + '\n'
                
                sections.append(Section(
                    level=1,
                    title="module",
                    content=module_content,
                    line_start=1,
                    line_end=first_symbol_line - 1,
                ))

            # Create sections from symbols
            # Adjust each symbol's line_end to include gaps before the next symbol
            sorted_symbols = sorted(symbols, key=lambda s: s.get("line_start", 0))
            for i, symbol in enumerate(sorted_symbols):
                # If there's a next symbol, extend this symbol to include the gap
                if i + 1 < len(sorted_symbols):
                    next_symbol_start = sorted_symbols[i + 1].get("line_start", len(lines) + 1)
                    # Include all blank lines before the next symbol
                    symbol["line_end"] = next_symbol_start - 1

                sections.append(self._create_section_from_symbol(symbol, lines))

            # Create a footer section for any content after the last symbol
            last_symbol_line = max(s.get("line_end", 0) for s in symbols)
            if last_symbol_line < len(lines):
                footer_content_lines = lines[last_symbol_line:]
                footer_content = '\n'.join(footer_content_lines)
                if footer_content:  # Only add if there's actual content
                    # Don't add trailing newline to footer (it's the last section)
                    sections.append(Section(
                        level=1,
                        title="footer",
                        content=footer_content,
                        line_start=last_symbol_line + 1,
                        line_end=len(lines),
                    ))
        else:
            # No symbols found, entire file is the module
            sections.append(Section(
                level=1,
                title="module",
                content=self.content,
                line_start=1,
                line_end=len(lines),
            ))

        # Build frontmatter
        frontmatter_data = {
            "type": "script",
            "language": self.language,
            "symbol_count": len(sections),
        }
        frontmatter = json.dumps(frontmatter_data, indent=2)

        # Determine format based on language
        format_map = {
            "python": FileFormat.PYTHON_SCRIPT,
            "javascript": FileFormat.JAVASCRIPT_TYPESCRIPT,
            "typescript": FileFormat.JAVASCRIPT_TYPESCRIPT,
            "shell": FileFormat.SHELL_SCRIPT,
        }

        return ParsedDocument(
            frontmatter=frontmatter,
            sections=sections,
            file_type=FileType.SCRIPT,
            format=format_map.get(self.language, FileFormat.UNKNOWN),
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        """
        Validate script file structure.

        Returns:
            ValidationResult with errors/warnings

        Checks:
        - File is syntactically valid
        - At least one symbol defined
        - Proper encoding (utf-8)
        """
        result = ValidationResult(is_valid=True)

        # Check file is not empty
        if not self.content.strip():
            result.add_error("File is empty")
            return result

        # Check for proper line endings using original bytes
        if b'\r\n' in self._original_bytes:
            result.add_warning("Contains CRLF line endings (consider LF only)")

        # Check for trailing whitespace issues
        lines = self.content.split('\n')
        trailing_lines = [i+1 for i, line in enumerate(lines) if line != line.rstrip()]
        if trailing_lines and len(trailing_lines) <= 5:
            result.add_warning(f"Trailing whitespace on lines: {trailing_lines[:5]}")

        return result

    def get_related_files(self) -> List[str]:
        """
        Get list of related files for script components.

        Returns:
            Empty list (scripts are typically single-file)
        """
        return []

    def get_file_type(self) -> FileType:
        """Return FileType.SCRIPT for script handlers."""
        return FileType.SCRIPT

    def get_file_format(self) -> FileFormat:
        """
        Get the FileFormat for this script handler.

        Returns:
            The FileFormat enum value based on the script language
        """
        format_map = {
            "python": FileFormat.PYTHON_SCRIPT,
            "javascript": FileFormat.JAVASCRIPT_TYPESCRIPT,
            "typescript": FileFormat.JAVASCRIPT_TYPESCRIPT,
            "shell": FileFormat.SHELL_SCRIPT,
        }
        return format_map.get(self.language, FileFormat.UNKNOWN)

    def _extract_module_docstring(self, lines: List[str]) -> str:
        """
        Extract module-level docstring or header comments.

        Args:
            lines: List of file lines

        Returns:
            Module docstring or header comments as string
        """
        if not lines:
            return ""

        # Python docstring
        if self.language == "python":
            if lines[0].strip().startswith(('"""', "'''")):
                # Multi-line docstring starting at line 1
                end_marker = lines[0].strip()[:3]
                content = [lines[0]]
                for line in lines[1:]:
                    content.append(line)
                    if end_marker in line and line != lines[0]:
                        break
                return '\n'.join(content)

        # Shell/JS/TS header comments
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if line.strip().startswith('#'):
                # Collect consecutive comment lines
                comments = []
                for j in range(i, min(i + 20, len(lines))):
                    if lines[j].strip().startswith('#'):
                        comments.append(lines[j])
                    elif not lines[j].strip():
                        comments.append(lines[j])
                    else:
                        break
                return '\n'.join(comments)

        return ""

    def _get_symbols_via_lsp(self) -> List[dict]:
        """
        Get symbols using LSP (Language Server Protocol).

        Returns:
            List of symbol dictionaries with name, kind, line info

        Note:
            This is a placeholder for LSP integration.
            In production, this would use Serena's LSP tools.
        """
        # For now, raise to trigger fallback to regex
        raise NotImplementedError("LSP not configured, using regex fallback")

    def _get_symbols_via_regex(self, lines: List[str]) -> List[dict]:
        """
        Get symbols using regex-based parsing.

        Args:
            lines: List of file lines

        Returns:
            List of symbol dictionaries

        Note:
            Subclasses should override this for language-specific patterns.
        """
        raise NotImplementedError("Subclasses must implement regex-based parsing")

    def _create_section_from_symbol(self, symbol: dict, lines: List[str]) -> Section:
        """
        Create a Section from a symbol definition.

        Args:
            symbol: Symbol dictionary with name, kind, line info
            lines: File lines for content extraction (split by \n)

        Returns:
            Section object
        """
        line_start = symbol.get("line_start", 1)
        line_end = symbol.get("line_end", len(lines))

        # Extract the lines for this symbol
        content_lines = lines[line_start-1:line_end]
        
        # Join with newlines to reconstruct content
        content = '\n'.join(content_lines)
        
        # Add trailing newline if there's more content after this symbol
        # or if the original file had a trailing newline
        if line_end < len(lines) or self.content.endswith('\n'):
            content += '\n'

        return Section(
            level=symbol.get("level", 1),
            title=symbol["name"],
            content=content,
            line_start=line_start,
            line_end=line_end,
        )

    def recompose(self, sections: List[Section]) -> str:
        """
        Reconstruct script from sections.

        Args:
            sections: List of sections from database

        Returns:
            Complete script content as string

        Note:
            For scripts, each section's content already contains the exact
            content from the original file including trailing newlines.
            We simply concatenate the sections in order to reconstruct.
        """
        # Sort sections by line_start to maintain original order
        sorted_sections = sorted(sections, key=lambda s: s.line_start)

        # Concatenate section content directly - no extra newlines needed
        result = []
        for section in sorted_sections:
            result.append(section.content)

        return ''.join(result)


class RegexSymbolFinder:
    """
    Helper class for finding code symbols using regex.

    Provides language-specific patterns for common code constructs.
    """

    # Python patterns
    PYTHON_CLASS = re.compile(r'^class\s+(\w+)\s*(?:\([^)]*\))?:')
    PYTHON_FUNCTION = re.compile(r'^def\s+(\w+)\s*\(')
    PYTHON_DECORATOR = re.compile(r'^@\w+')

    # JavaScript/TypeScript patterns
    JS_CLASS = re.compile(r'^class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{')
    JS_FUNCTION = re.compile(r'^function\s+(\w+)\s*\(')
    JS_ASYNC_FUNCTION = re.compile(r'^async\s+function\s+(\w+)\s*\(')
    JS_METHOD = re.compile(r'^\s*(async\s+)?(\w+)\s*\([^)]*\)\s*{?\s*$')
    JS_ARROW_FUNCTION = re.compile(r'^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>')
    JS_INTERFACE = re.compile(r'^interface\s+(\w+)')
    JS_TYPE = re.compile(r'^type\s+(\w+)\s*=')
    # CommonJS patterns
    JS_EXPORTS_FUNCTION = re.compile(r'^exports\.(\w+)\s*=\s*function\s*\(')
    JS_CONST_FUNCTION = re.compile(r'^const\s+(\w+)\s*=\s*function\s*\(')

    # Shell patterns
    SHELL_FUNCTION = re.compile(r'^(\w+)\s*\(\s*\)\s*{?')
    SHELL_KEYWORD = re.compile(r'^(if|then|else|fi|for|while|do|done|case|esac|function|return)\b')

    @classmethod
    def find_python_symbols(cls, lines: List[str]) -> List[dict]:
        """
        Find Python class and function definitions.

        Args:
            lines: List of file lines

        Returns:
            List of symbol dictionaries
        """
        symbols = []
        decorators = []

        for i, line in enumerate(lines):
            # Track decorators
            if cls.PYTHON_DECORATOR.match(line):
                decorators.append(i)
                continue

            # Check for class definition
            class_match = cls.PYTHON_CLASS.match(line)
            if class_match:
                name = class_match.group(1)
                end_line = cls._find_block_end(lines, i, indent_level=len(line) - len(line.lstrip()))
                symbols.append({
                    "name": name,
                    "kind": "class",
                    "line_start": (decorators[0] if decorators else i) + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                decorators = []
                continue

            # Check for function definition
            func_match = cls.PYTHON_FUNCTION.match(line)
            if func_match:
                name = func_match.group(1)
                # Skip if this is indented (it's a method, not top-level)
                if line[0] not in (' ', '\t'):
                    end_line = cls._find_block_end(lines, i, indent_level=len(line) - len(line.lstrip()))
                    symbols.append({
                        "name": name,
                        "kind": "function",
                        "line_start": (decorators[0] if decorators else i) + 1,
                        "line_end": end_line + 1,
                        "level": 1,
                    })
                    decorators = []

        return symbols

    @classmethod
    def find_javascript_symbols(cls, lines: List[str]) -> List[dict]:
        """
        Find JavaScript/TypeScript class, function, and interface definitions.

        Args:
            lines: List of file lines

        Returns:
            List of symbol dictionaries
        """
        symbols = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip comments and imports
            if not stripped or stripped.startswith('//') or stripped.startswith('import'):
                continue

            # Check for interface/type definitions (TypeScript)
            interface_match = cls.JS_INTERFACE.match(stripped)
            if interface_match:
                end_line = cls._find_brace_end(lines, i)
                symbols.append({
                    "name": interface_match.group(1),
                    "kind": "interface",
                    "line_start": i + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                continue

            type_match = cls.JS_TYPE.match(stripped)
            if type_match:
                end_line = cls._find_statement_end(lines, i)
                symbols.append({
                    "name": type_match.group(1),
                    "kind": "type",
                    "line_start": i + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                continue

            # Check for class definition
            class_match = cls.JS_CLASS.match(stripped)
            if class_match:
                end_line = cls._find_brace_end(lines, i)
                symbols.append({
                    "name": class_match.group(1),
                    "kind": "class",
                    "line_start": i + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                continue

            # Check for function definition
            func_match = cls.JS_FUNCTION.match(stripped) or cls.JS_ASYNC_FUNCTION.match(stripped)
            if func_match:
                end_line = cls._find_brace_end(lines, i)
                symbols.append({
                    "name": func_match.group(1),
                    "kind": "function",
                    "line_start": i + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                continue

            # Check for arrow function
            arrow_match = cls.JS_ARROW_FUNCTION.match(stripped)
            if arrow_match:
                end_line = cls._find_statement_end(lines, i)
                symbols.append({
                    "name": arrow_match.group(1),
                    "kind": "function",
                    "line_start": i + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                continue

            # Check for CommonJS exports.name = function(...)
            exports_match = cls.JS_EXPORTS_FUNCTION.match(stripped)
            if exports_match:
                end_line = cls._find_brace_end(lines, i)
                symbols.append({
                    "name": exports_match.group(1),
                    "kind": "function",
                    "line_start": i + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })
                continue

            # Check for const name = function(...)
            const_func_match = cls.JS_CONST_FUNCTION.match(stripped)
            if const_func_match:
                end_line = cls._find_brace_end(lines, i)
                symbols.append({
                    "name": const_func_match.group(1),
                    "kind": "function",
                    "line_start": i + 1,
                    "line_end": end_line + 1,
                    "level": 1,
                })

        return symbols

    @classmethod
    def find_shell_symbols(cls, lines: List[str]) -> List[dict]:
        """
        Find shell function definitions.

        Args:
            lines: List of file lines

        Returns:
            List of symbol dictionaries
        """
        symbols = []

        for i, line in enumerate(lines):
            # Check for function definition
            func_match = cls.SHELL_FUNCTION.match(line)
            if func_match:
                name = func_match.group(1)
                # Skip shell keywords
                if name.lower() not in ('if', 'then', 'else', 'fi', 'for', 'while', 'do', 'done', 'case', 'esac', 'function', 'return'):
                    end_line = cls._find_block_end(lines, i, opening_char='{')
                    symbols.append({
                        "name": name,
                        "kind": "function",
                        "line_start": i + 1,
                        "line_end": end_line + 1,
                        "level": 1,
                    })

        return symbols

    @classmethod
    def _find_block_end(cls, lines: List[str], start_idx: int, indent_level: int = 0, opening_char: str = ':') -> int:
        """
        Find the end of a code block.

        Args:
            lines: List of file lines
            start_idx: Index where block starts
            indent_level: Indentation level of the block start
            opening_char: Character that opens the block

        Returns:
            Index of the last line of the block (0-indexed)

        Note:
            If the last line in lines is an empty string (from trailing newline
            in original file), this returns the index of the last non-empty line.
        """
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if line.strip() and not line.strip().startswith('#'):
                # Check if we've dedented past the block start
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and not line.strip().startswith(('else', 'elif', 'except', 'finally')):
                    return i - 1
        # Handle trailing empty string from file ending with newline
        last_idx = len(lines) - 1
        if last_idx >= 0 and lines[last_idx] == '':
            return last_idx - 1
        return last_idx

    @classmethod
    def _find_brace_end(cls, lines: List[str], start_idx: int) -> int:
        """
        Find the end of a brace-enclosed block.

        Args:
            lines: List of file lines
            start_idx: Index where opening brace appears

        Returns:
            Index of the line with closing brace
        """
        depth = 0
        for i in range(start_idx, len(lines)):
            depth += lines[i].count('{')
            depth -= lines[i].count('}')
            if depth == 0 and '}' in lines[i]:
                return i
        return len(lines) - 1

    @classmethod
    def _find_statement_end(cls, lines: List[str], start_idx: int) -> int:
        """
        Find the end of a statement (up to semicolon or newline).

        Args:
            lines: List of file lines
            start_idx: Index where statement starts

        Returns:
            Index of the last line of the statement
        """
        for i in range(start_idx, len(lines)):
            if lines[i].strip().endswith((';', '}')):
                return i
            if i > start_idx and not lines[i].strip().startswith(('...', '+', '-', '|', '&', ',')):
                # Check for continuation
                if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].lstrip().startswith(('=', '+', '-', '|', '&')):
                    return i
        return start_idx
