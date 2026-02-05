"""
Handler for shell script files using regex-based parsing.

This module provides a ShellHandler that extends ScriptHandler to
parse shell script files into structured sections based on function
definitions and shell-specific features.

Supported shell types:
- Bash (.sh, .bash)
- POSIX shell (.sh)
- Zsh (.zsh)
- Fish (.fish)

Section structure:
- Shebang line captured in module docstring
- Function definitions become sections
- Comments are preserved within function blocks
- Shell keywords (if, then, else, fi, for, while, do, done, case, esac) are tracked
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from handlers.script_handler import ScriptHandler, RegexSymbolFinder
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class ShellHandler(ScriptHandler):
    """
    Handler for shell script files.

    Parses shell scripts by identifying function definitions and
    shell-specific constructs. Uses regex-based parsing for broad
    compatibility across different shell dialects.

    Shell-specific features handled:
    - Shebang (#!/bin/bash, #!/usr/bin/env zsh, etc.)
    - Function definitions (name() { ... } or function name { ... })
    - Single-line comments (# ...)
    - Shell keywords (if, then, else, fi, for, while, do, done, case, esac)
    - Here documents
    - Command substitutions $(...) or `...`

    Section structure:
    - Module section contains shebang and header comments
    - Each function becomes a named section
    - Function content includes the full definition and body
    """

    def __init__(self, file_path: str):
        """
        Initialize shell handler with file path.

        Args:
            file_path: Path to the shell script file

        Raises:
            FileNotFoundError: If the file does not exist
        """
        super().__init__(file_path, language="shell")

    # Use base class parse() method - it handles module/footer sections correctly

    def validate(self) -> ValidationResult:
        """
        Validate shell script structure.

        Returns:
            ValidationResult with errors/warnings

        Checks:
        - File is not empty
        - Has proper shebang line (warns if missing)
        - No syntax errors in function definitions
        - Proper line endings (LF preferred)
        """
        result = super().validate()

        # Check for shebang
        if self.content.strip():
            first_line = self.content.strip().split('\n')[0]
            if not first_line.startswith('#!'):
                result.add_warning("Missing shebang (#!/bin/bash or similar)")

        # Check for common shell syntax issues
        lines = self.content.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for tabs vs spaces inconsistency
            if '\t' in line and '    ' in line:
                result.add_warning(f"Mixed tabs and spaces on line {i+1}")
                break

            # Check for dangerous commands (informational)
            dangerous = ['rm -rf /', 'rm -rf /*', ':(){ :|:& };:', 'dd if=/dev/zero']
            for dangerous_cmd in dangerous:
                if dangerous_cmd in stripped:
                    result.add_warning(f"Potentially dangerous command on line {i+1}: {stripped[:50]}")

        return result

    def get_file_format(self) -> FileFormat:
        """
        Return FileFormat.SHELL_SCRIPT for shell handlers.

        Returns:
            FileFormat.SHELL_SCRIPT enum value
        """
        return FileFormat.SHELL_SCRIPT

    def _get_symbols_via_regex(self, lines: List[str]) -> List[dict]:
        """
        Get shell symbols using regex-based parsing.

        Args:
            lines: List of file lines

        Returns:
            List of symbol dictionaries with name, kind, line info

        Shell-specific patterns:
        - POSIX functions: name() { ... }
        - Bash functions: function name { ... }
        - Named sections in comments: ## Section Name
        """
        # Use base class helper for shell symbols
        return RegexSymbolFinder.find_shell_symbols(lines)

    def _find_header_end(self, lines: List[str]) -> int:
        """
        Find the end of the header section (shebang + comments).

        Args:
            lines: List of file lines

        Returns:
            Line number (1-based) where header ends
        """
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Stop at first non-comment, non-empty line after shebang
            if i > 0 and stripped and not stripped.startswith('#'):
                return i + 1

        return len(lines)

    def _detect_shell_type(self) -> str:
        """
        Detect the shell type from shebang or file extension.

        Returns:
            Shell type string (bash, zsh, sh, fish, etc.)
        """
        # Check shebang
        for line in self.content.split('\n')[:5]:
            if line.startswith('#!'):
                shebang = line.lower()
                if 'bash' in shebang:
                    return 'bash'
                elif 'zsh' in shebang:
                    return 'zsh'
                elif 'fish' in shebang:
                    return 'fish'
                elif 'sh' in shebang:
                    return 'sh'

        # Fall back to file extension
        path = Path(self.file_path)
        suffix = path.suffix.lower()

        extension_map = {
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            '.sh': 'sh',
        }

        return extension_map.get(suffix, 'unknown')

    def recompose(self, sections: List[Section]) -> str:
        """
        Reconstruct shell script from sections.

        Args:
            sections: List of sections from database

        Returns:
            Complete shell script content as string

        Note:
            For shell scripts, we preserve the exact original structure
            by joining sections with single newlines.
        """
        # Use parent class implementation which handles line-based reconstruction
        return super().recompose(sections)


# Import regex for _find_shell_function_end
import re
