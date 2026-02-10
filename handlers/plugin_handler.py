"""
Handler for plugin components.

A plugin consists of:
- plugin.json: Main plugin metadata
- .mcp.json: MCP server configuration (optional)
- hooks.json: Hook definitions (optional)
"""

import json
from pathlib import Path
from typing import List, Optional

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
        Parse plugin.json while preserving byte-perfect original content.

        We store the original JSON exactly in frontmatter for exact
        round-trip reconstruction, AND generate sections for progressive
        disclosure (metadata, mcp_config, hooks, permissions).
        """
        plugin_data = json.loads(self.content)
        sections: List[Section] = []

        # Metadata section
        name = plugin_data.get("name", "unknown")
        version = plugin_data.get("version", "unknown")
        description = plugin_data.get("description", "")
        author = plugin_data.get("author")

        metadata_lines = [f"# {name}", f"**Version**: {version}"]
        if description:
            metadata_lines.append(f"**Description**: {description}")
        if author:
            metadata_lines.append(f"**Author**: {author}")
        metadata_content = "\n".join(metadata_lines).strip() + "\n"

        sections.append(Section(
            level=1,
            title="metadata",
            content=metadata_content,
            line_start=1,
            line_end=len(metadata_content.splitlines()),
        ))

        # Permissions section (optional)
        permissions = plugin_data.get("permissions")
        if isinstance(permissions, list) and permissions:
            permission_lines = ["## Permissions"] + [f"- {p}" for p in permissions]
            permissions_content = "\n".join(permission_lines).strip() + "\n"
            sections.append(Section(
                level=1,
                title="permissions",
                content=permissions_content,
                line_start=1,
                line_end=len(permissions_content.splitlines()),
            ))

        # MCP config section (optional)
        mcp_file = self._find_mcp_config()
        if mcp_file:
            mcp_content = mcp_file.read_text()
            sections.append(Section(
                level=1,
                title="mcp_config",
                content=mcp_content,
                line_start=1,
                line_end=len(mcp_content.splitlines()),
            ))

        # Hooks section (optional)
        hooks_file = self._find_hooks_config()
        if hooks_file:
            hooks_content = hooks_file.read_text()
            sections.append(Section(
                level=1,
                title="hooks",
                content=hooks_content,
                line_start=1,
                line_end=len(hooks_content.splitlines()),
            ))

        return ParsedDocument(
            frontmatter=self.content,  # Store original JSON exactly
            sections=sections,
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

    def _find_mcp_config(self) -> Optional[Path]:
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

    def _find_hooks_config(self) -> Optional[Path]:
        """
        Find hooks.json file in plugin directory.

        Returns:
            Path to hooks.json file or None if not found
        """
        plugin_dir = Path(self.file_path).parent
        hooks_file = plugin_dir / "hooks.json"
        return hooks_file if hooks_file.exists() else None
