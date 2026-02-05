"""
Handler for plugin components.

A plugin consists of:
- plugin.json: Main plugin metadata
- .mcp.json: MCP server configuration (optional)
- hooks.json: Hook definitions (optional)
"""

import json
from pathlib import Path
from typing import List

from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class PluginHandler(BaseHandler):
    """
    Handler for plugin components.

    Parses plugin.json and related files (.mcp.json, hooks.json) into
    structured sections for database storage and progressive disclosure.

    Section structure:
    - metadata: Plugin name, version, description, author
    - mcp_config: MCP server configuration (if exists)
    - hooks: Hook definitions (if exists)
    - permissions: Required permissions (if defined)
    """

    def parse(self) -> ParsedDocument:
        """
        Parse plugin.json - store original content for byte-perfect reconstruction.

        For plugin.json files, we store the original JSON content as-is without
        creating sections. This ensures byte-perfect round-trip reconstruction.

        Returns:
            ParsedDocument with original JSON content (no sections)

        Raises:
            json.JSONDecodeError: If plugin.json is invalid
        """
        # Validate JSON structure
        plugin_data = json.loads(self.content)

        # Store original JSON exactly in frontmatter field (no sections)
        # Recomposer will return frontmatter as-is for FileType.PLUGIN with no sections
        return ParsedDocument(
            frontmatter=self.content,  # Store original JSON exactly
            sections=[],                # No sections - preserve as single unit
            file_type=FileType.PLUGIN,
            format=FileFormat.MULTI_FILE,
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        """
        Validate plugin structure.

        Returns:
            ValidationResult with errors/warnings

        Checks:
        - Required fields (name, version, description)
        - MCP config file exists if referenced
        - Hooks file exists if referenced
        - Valid JSON format
        """
        result = ValidationResult(is_valid=True)

        try:
            plugin_data = json.loads(self.content)

            # Required fields
            required = ["name", "version", "description"]
            for field in required:
                if field not in plugin_data:
                    result.add_error(f"Missing required field: {field}")

            # Check MCP config if referenced
            if "mcpServers" in plugin_data:
                mcp_file = self._find_mcp_config()
                if not mcp_file:
                    result.add_warning("MCP servers referenced but no .mcp.json found")
                else:
                    # Validate MCP config file
                    try:
                        with open(mcp_file, 'r') as f:
                            mcp_data = json.load(f)
                            if not isinstance(mcp_data, dict):
                                result.add_error("MCP config must be a dictionary")
                    except json.JSONDecodeError as e:
                        result.add_error(f"Invalid JSON in .mcp.json: {e}")

            # Check hooks if referenced
            if "hooks" in plugin_data:
                hooks_file = self._find_hooks_config()
                if not hooks_file:
                    result.add_warning("Hooks referenced but no hooks.json found")
                else:
                    # Validate hooks file
                    try:
                        with open(hooks_file, 'r') as f:
                            hooks_data = json.load(f)
                            if not isinstance(hooks_data, dict):
                                result.add_error("Hooks config must be a dictionary")
                    except json.JSONDecodeError as e:
                        result.add_error(f"Invalid JSON in hooks.json: {e}")

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON in plugin.json: {e}")

        return result

    def get_related_files(self) -> List[str]:
        """
        Get list of related plugin files.

        Returns:
            List of absolute file paths

        Related files:
        - .mcp.json (if exists)
        - hooks.json (if exists)
        """
        related = []
        plugin_dir = Path(self.file_path).parent

        # Find .mcp.json
        mcp_file = self._find_mcp_config()
        if mcp_file:
            related.append(str(mcp_file.absolute()))

        # Find hooks.json
        hooks_file = self._find_hooks_config()
        if hooks_file:
            related.append(str(hooks_file.absolute()))

        return related

    def get_file_type(self) -> FileType:
        """Return FileType.PLUGIN for this handler."""
        return FileType.PLUGIN

    def get_file_format(self) -> FileFormat:
        """Return FileFormat.MULTI_FILE for plugins."""
        return FileFormat.MULTI_FILE

    def _find_mcp_config(self) -> Path | None:
        """
        Find .mcp.json file in plugin directory.

        Returns:
            Path to .mcp.json file or None if not found

        Note:
            Looks for any file matching *.mcp.json pattern in the plugin directory.
        """
        plugin_dir = Path(self.file_path).parent

        # Look for any .mcp.json file in the directory
        for mcp_file in plugin_dir.glob("*.mcp.json"):
            if mcp_file.is_file():
                return mcp_file

        return None

    def _find_hooks_config(self) -> Path | None:
        """
        Find hooks.json file in plugin directory.

        Returns:
            Path to hooks.json file or None if not found
        """
        plugin_dir = Path(self.file_path).parent
        hooks_file = plugin_dir / "hooks.json"
        return hooks_file if hooks_file.exists() else None
