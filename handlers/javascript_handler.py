"""
JavaScript/TypeScript handler for script files using LSP-based parsing.

This module provides JavaScriptHandler and TypeScriptHandler that extend
ScriptHandler to accurately parse JavaScript and TypeScript files into
structured sections based on their symbol definitions.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from handlers.script_handler import ScriptHandler, RegexSymbolFinder
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class JavaScriptHandler(ScriptHandler):
    """
    Handler for JavaScript (.js, .jsx) files.

    This handler parses JavaScript files using regex-based symbol discovery
    to extract classes, functions, arrow functions, and other code structures
    into progressive disclosure sections.

    Supported features:
    - Classes (with extends)
    - Function declarations
    - Async functions
    - Arrow functions (const/let/var x = () => {})
    - Interface definitions (TypeScript in .js files)
    - Type definitions (TypeScript in .js files)
    - Module exports

    Section structure:
    - Top-level classes become sections
    - Top-level functions become sections
    - Arrow functions at module level become sections
    - Interfaces and types become sections
    - Module-level comments are captured as documentation
    """

    def __init__(self, file_path: str, is_typescript: bool = False):
        """
        Initialize JavaScript handler with file path.

        Args:
            file_path: Path to the JavaScript/TypeScript file
            is_typescript: Whether this is a TypeScript file (.ts, .tsx)
        """
        language = "typescript" if is_typescript else "javascript"
        super().__init__(file_path, language)
        self.is_typescript = is_typescript

    # Use base class parse() method - it handles module/footer sections correctly

    def _get_symbols_via_regex(self, lines: List[str]) -> List[dict]:
        """
        Get JavaScript/TypeScript symbols using regex-based parsing.

        Args:
            lines: List of file lines

        Returns:
            List of symbol dictionaries

        This method uses RegexSymbolFinder.find_javascript_symbols()
        which handles:
        - Classes (with extends support)
        - Function declarations
        - Async functions
        - Arrow functions
        - Interface definitions (TypeScript)
        - Type definitions (TypeScript)
        - Export statements
        """
        return RegexSymbolFinder.find_javascript_symbols(lines)

    def get_file_format(self) -> FileFormat:
        """
        Return JAVASCRIPT_TYPESCRIPT format for JavaScript/TypeScript handlers.

        Returns:
            FileFormat.JAVASCRIPT_TYPESCRIPT
        """
        return FileFormat.JAVASCRIPT_TYPESCRIPT

    def validate(self) -> ValidationResult:
        """
        Validate JavaScript/TypeScript file structure.

        Returns:
            ValidationResult with errors/warnings

        Checks:
        - File is not empty
        - Proper encoding (utf-8)
        - Line ending consistency
        - Trailing whitespace issues
        - ES module/CommonJS import/export syntax
        """
        result = super().validate()

        # Check for mixed module systems
        has_es_import = any('import ' in line for line in self.content.split('\n'))
        has_cjs_import = any('require(' in line for line in self.content.split('\n'))

        if has_es_import and has_cjs_import:
            result.add_warning("Mixing ES modules and CommonJS (require/import)")

        # Check for TypeScript-specific issues
        if self.is_typescript:
            # Check for any type usage
            if ':' not in self.content and 'interface ' not in self.content:
                result.add_warning("TypeScript file lacks type annotations")

        return result
