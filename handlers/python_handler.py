"""
Python handler for parsing Python (.py) script files.

This module provides a PythonHandler that extends ScriptHandler to
support Python-specific parsing features including decorators,
async functions, and context managers.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

from handlers.script_handler import ScriptHandler, RegexSymbolFinder
from models import FileFormat, Section

if TYPE_CHECKING:
    pass


class PythonHandler(ScriptHandler):
    """
    Handler for Python (.py) script files.

    Extends ScriptHandler to provide Python-specific parsing capabilities:

    Section structure:
    - Top-level classes become sections (including decorated classes)
    - Top-level functions become sections (including async functions)
    - Decorators are preserved and included with the decorated symbol
    - Context managers (__enter__/__exit__) are identified
    - Module-level docstrings are captured

    Python-specific features:
    - Decorator preservation (@decorator, @classmethod, @staticmethod, @property)
    - Async function detection (async def)
    - Class method identification (methods indented under class)
    - Property decorators (@property, @setter, @deleter)
    - Context manager protocols

    Example:
        ```python
        from handlers.python_handler import PythonHandler

        handler = PythonHandler("/path/to/file.py")
        doc = handler.parse()
        ```
    """

    def __init__(self, file_path: str):
        """
        Initialize Python handler with file path.

        Args:
            file_path: Path to the Python (.py) file
        """
        super().__init__(file_path, language="python")

    def _get_symbols_via_regex(self, lines: List[str]) -> List[dict]:
        """
        Get Python symbols using regex-based parsing.

        Extends the base RegexSymbolFinder to handle Python-specific
        features like decorators, async functions, and context managers.

        Args:
            lines: List of file lines

        Returns:
            List of symbol dictionaries with keys:
            - name: Symbol name (str)
            - kind: Symbol kind (str): 'class', 'function', 'async_function'
            - line_start: Starting line number (int, 1-based)
            - line_end: Ending line number (int, 1-based)
            - level: Nesting level (int)
            - decorators: List of decorator names (List[str])
            - is_context_manager: Whether symbol is a context manager (bool)

        Note:
            Uses RegexSymbolFinder.find_python_symbols() as the base
            implementation and adds metadata for decorators and async functions.
        """
        # Get base symbols from RegexSymbolFinder
        base_symbols = RegexSymbolFinder.find_python_symbols(lines)

        # Enhance with Python-specific metadata
        enhanced_symbols = []
        for symbol in base_symbols:
            enhanced = symbol.copy()

            # Extract decorators if present
            start_idx = symbol["line_start"] - 1
            decorators = self._extract_decorators(lines, start_idx)
            if decorators:
                enhanced["decorators"] = decorators

            # Identify async functions
            if enhanced.get("kind") == "function":
                func_line = lines[start_idx]
                if "async def" in func_line:
                    enhanced["kind"] = "async_function"

            # Check for context manager protocol
            if enhanced.get("kind") == "class":
                enhanced["is_context_manager"] = self._has_context_manager_protocol(
                    lines, start_idx, symbol["line_end"] - 1
                )

            enhanced_symbols.append(enhanced)

        return enhanced_symbols

    def _extract_decorators(self, lines: List[str], start_idx: int) -> List[str]:
        """
        Extract decorator names preceding a symbol definition.

        Args:
            lines: List of file lines
            start_idx: Index where symbol definition starts

        Returns:
            List of decorator names (e.g., ['property', 'staticmethod'])

        Note:
            Looks backward from start_idx for consecutive decorator lines.
        """
        decorators = []
        idx = start_idx - 1

        while idx >= 0:
            line = lines[idx].strip()
            if line.startswith("@"):
                # Extract decorator name (e.g., "@property" -> "property")
                decorator_name = line[1:].split("(")[0].strip()
                decorators.insert(0, decorator_name)
                idx -= 1
            elif not line:
                # Skip blank lines between decorators and definition
                idx -= 1
                continue
            else:
                # Found non-decorator, non-blank line
                break

        return decorators

    def _has_context_manager_protocol(
        self, lines: List[str], start_idx: int, end_idx: int
    ) -> bool:
        """
        Check if a class implements the context manager protocol.

        Args:
            lines: List of file lines
            start_idx: Index where class definition starts
            end_idx: Index where class definition ends

        Returns:
            True if class has __enter__ and __exit__ methods

        Note:
            A class is a context manager if it defines both __enter__
            and __exit__ methods.
        """
        has_enter = False
        has_exit = False

        for i in range(start_idx, min(end_idx + 1, len(lines))):
            line = lines[i].strip()
            if "def __enter__" in line:
                has_enter = True
            elif "def __exit__" in line:
                has_exit = True

            if has_enter and has_exit:
                return True

        return False

    def get_file_format(self) -> FileFormat:
        """
        Return the file format for Python scripts.

        Returns:
            FileFormat.PYTHON_SCRIPT
        """
        return FileFormat.PYTHON_SCRIPT
