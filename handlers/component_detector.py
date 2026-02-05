"""
Component detector for identifying file types and returning appropriate handlers.

This module provides the ComponentDetector class which analyzes file paths
and content to determine the component type and returns the appropriate
handler instance.
"""

import re
from pathlib import Path
from typing import Tuple, Optional, TYPE_CHECKING

from models import FileType, FileFormat

# Avoid circular imports
if TYPE_CHECKING:
    from handlers.base import BaseHandler


class ComponentDetector:
    """
    Detects component type and returns appropriate handler.

    Detection strategy:
    1. Path-based: Use file location patterns
    2. Extension-based: Use file extension
    3. Content-based: Analyze file structure (future enhancement)

    The detector maintains a registry of file type patterns and
    associates each pattern with the appropriate handler class.
    """

    # Path patterns for component detection
    # Ordered from most specific to least specific
    PATTERNS = {
        FileType.SKILL: re.compile(r"(/skills/[^/]+/SKILL\.md|/SKILL\.md$)"),
        FileType.COMMAND: re.compile(r"/commands/[^/]+/[^/]+\.md$"),
        FileType.AGENT: re.compile(r"/agents/[^/]+/[^/]+\.md$"),
        FileType.REFERENCE: re.compile(r"/get-shit-done/references/[^/]+\.md$"),  # More specific path
        FileType.PLUGIN: re.compile(r"plugin\.json$"),
        FileType.HOOK: re.compile(r"hooks\.json$"),
        FileType.OUTPUT_STYLE: re.compile(r"/output-styles/[^/]+\.md$"),
        FileType.CONFIG: re.compile(r"(settings\.json|mcp_config\.json)$"),
        FileType.DOCUMENTATION: re.compile(r"(README\.md|CLAUDE\.md|/references/[^/]+\.md$)"),  # Generic references
    }

    # Handler imports (lazy to avoid circular dependency)
    _handler_classes = {}

    @classmethod
    def detect(cls, file_path: str) -> Tuple[FileType, FileFormat]:
        """
        Detect component type and format from file path.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (FileType, FileFormat)

        Examples:
            >>> detector = ComponentDetector()
            >>> file_type, file_format = detector.detect("plugin.json")
            >>> print(file_type)  # FileType.PLUGIN
            >>> print(file_format)  # FileFormat.JSON
        """
        path = Path(file_path)
        # Normalize path for consistent pattern matching
        normalized_path = str(path).replace("\\", "/")

        # Check patterns in order
        for file_type, pattern in cls.PATTERNS.items():
            if pattern.search(normalized_path):
                file_format = cls._detect_format(path)
                return file_type, file_format

        # Fallback: check extension
        if path.suffix == ".json":
            return FileType.CONFIG, FileFormat.JSON

        if path.suffix == ".md":
            return FileType.DOCUMENTATION, FileFormat.MARKDOWN_HEADINGS

        if path.suffix == ".sh":
            return FileType.HOOK, FileFormat.SHELL_SCRIPT

        # Default: reference document
        return FileType.REFERENCE, FileFormat.UNKNOWN

    @classmethod
    def _detect_format(cls, path: Path) -> FileFormat:
        """
        Detect format from file extension and content.

        Args:
            path: Path object for the file

        Returns:
            Detected FileFormat
        """
        suffix = path.suffix.lower()

        if suffix == ".json":
            return FileFormat.JSON

        if suffix == ".sh":
            return FileFormat.SHELL_SCRIPT

        if suffix == ".md":
            # Will use existing FormatDetector for markdown
            return FileFormat.MARKDOWN_HEADINGS

        return FileFormat.UNKNOWN

    @classmethod
    def get_handler(cls, file_path: str) -> Optional["BaseHandler"]:
        """
        Get appropriate handler for file.

        Args:
            file_path: Path to the file

        Returns:
            Handler instance, or None if file should use existing Parser

        Raises:
            ValueError: If file type is known but handler class not available
            FileNotFoundError: If file does not exist

        Examples:
            >>> handler = ComponentDetector.get_handler("plugin.json")
            >>> doc = handler.parse()
        """
        file_type, _ = cls.detect(file_path)

        # Import handlers lazily to avoid circular dependencies
        handler_map = cls._get_handler_map()

        handler_class = handler_map.get(file_type)

        if handler_class is not None:
            return handler_class(file_path)

        # For markdown files, return None to indicate use of existing Parser
        # This includes: SKILL, COMMAND, AGENT, OUTPUT_STYLE, DOCUMENTATION, REFERENCE
        markdown_types = {
            FileType.SKILL, FileType.COMMAND, FileType.AGENT,
            FileType.OUTPUT_STYLE, FileType.DOCUMENTATION, FileType.REFERENCE
        }

        if file_type in markdown_types:
            return None

        # Unknown file type
        raise ValueError(f"No handler available for file type: {file_type}")

    @classmethod
    def _get_handler_map(cls) -> dict:
        """
        Get the mapping of FileTypes to handler classes.

        Returns:
            Dictionary mapping FileType to handler class

        Note:
            Uses lazy import to avoid circular dependencies.
        """
        if not cls._handler_classes:
            from handlers.plugin_handler import PluginHandler
            from handlers.hook_handler import HookHandler
            from handlers.config_handler import ConfigHandler

            cls._handler_classes = {
                FileType.PLUGIN: PluginHandler,
                FileType.HOOK: HookHandler,
                FileType.CONFIG: ConfigHandler,
            }

        return cls._handler_classes

    @classmethod
    def is_markdown_file(cls, file_path: str) -> bool:
        """
        Check if file should be handled by existing Parser.

        Args:
            file_path: Path to the file

        Returns:
            True if file is a markdown file that should use Parser

        Examples:
            >>> ComponentDetector.is_markdown_file("README.md")
            True
            >>> ComponentDetector.is_markdown_file("plugin.json")
            False
        """
        file_type, _ = cls.detect(file_path)

        markdown_types = {
            FileType.SKILL, FileType.COMMAND, FileType.AGENT,
            FileType.OUTPUT_STYLE, FileType.DOCUMENTATION, FileType.REFERENCE
        }

        return file_type in markdown_types
