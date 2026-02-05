"""
Handler factory for creating handler instances.

This module provides the HandlerFactory class which implements the
factory pattern for creating appropriate handler instances based on
file type detection.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from models import FileType, FileFormat

# Avoid circular imports
if TYPE_CHECKING:
    from handlers.base import BaseHandler


class HandlerFactory:
    """
    Factory for creating handler instances.

    This factory provides a clean interface for obtaining the appropriate
    handler for a given file, abstracting away the detection logic.

    Usage:
        >>> handler = HandlerFactory.create_handler("plugin.json")
        >>> doc = handler.parse()
    """

    @staticmethod
    def create_handler(file_path: str) -> Optional["BaseHandler"]:
        """
        Create appropriate handler for the given file.

        Args:
            file_path: Path to the file

        Returns:
            Handler instance, or None if file should use existing Parser

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file type is not supported

        Examples:
            >>> handler = HandlerFactory.create_handler("plugin.json")
            >>> isinstance(handler, PluginHandler)
            True

            >>> handler = HandlerFactory.create_handler("README.md")
            >>> handler is None  # Use existing Parser
            True
        """
        # Delegate to ComponentDetector
        from handlers.component_detector import ComponentDetector

        return ComponentDetector.get_handler(file_path)

    @staticmethod
    def detect_file_type(file_path: str) -> tuple[FileType, FileFormat]:
        """
        Detect file type and format.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (FileType, FileFormat)

        Examples:
            >>> file_type, file_format = HandlerFactory.detect_file_type("plugin.json")
            >>> print(file_type)  # FileType.PLUGIN
            >>> print(file_format)  # FileFormat.JSON
        """
        from handlers.component_detector import ComponentDetector

        return ComponentDetector.detect(file_path)

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """
        Check if file type is supported by handlers.

        Args:
            file_path: Path to the file

        Returns:
            True if file has a handler, False if it should use Parser

        Examples:
            >>> HandlerFactory.is_supported("plugin.json")
            True

            >>> HandlerFactory.is_supported("README.md")
            False  # Use existing Parser
        """
        from handlers.component_detector import ComponentDetector

        file_type, _ = ComponentDetector.detect(file_path)

        # Files with dedicated handlers
        handler_types = {FileType.PLUGIN, FileType.HOOK, FileType.CONFIG}

        return file_type in handler_types

    @staticmethod
    def get_handler_for_type(file_type: FileType, file_path: str) -> Optional["BaseHandler"]:
        """
        Get handler instance for a specific file type.

        Args:
            file_type: The FileType enum value
            file_path: Path to the file

        Returns:
            Handler instance or None if type not supported

        Raises:
            FileNotFoundError: If file does not exist

        Note:
            This method bypasses detection and directly returns
            the handler for the specified type. Use with caution.
        """
        from handlers.plugin_handler import PluginHandler
        from handlers.hook_handler import HookHandler
        from handlers.config_handler import ConfigHandler

        handler_classes = {
            FileType.PLUGIN: PluginHandler,
            FileType.HOOK: HookHandler,
            FileType.CONFIG: ConfigHandler,
        }

        handler_class = handler_classes.get(file_type)

        if handler_class:
            return handler_class(file_path)

        return None

    @classmethod
    def list_supported_types(cls) -> list[str]:
        """
        List all supported file types.

        Returns:
            List of file type names

        Examples:
            >>> HandlerFactory.list_supported_types()
            ['plugin', 'hook', 'config']
        """
        return [ft.value for ft in [FileType.PLUGIN, FileType.HOOK, FileType.CONFIG]]

    @classmethod
    def list_supported_extensions(cls) -> list[str]:
        """
        List all supported file extensions.

        Returns:
            List of file extensions

        Examples:
            >>> HandlerFactory.list_supported_extensions()
            ['.json']
        """
        return ['.json']  # All handlers currently support JSON
