"""
Handler for configuration files.

Handles:
- settings.json: Claude Code settings
- mcp_config.json: MCP server configuration
"""

import json
from pathlib import Path
from typing import List, Any

from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class ConfigHandler(BaseHandler):
    """
    Handler for configuration files.

    Parses configuration JSON files into structured sections for
    database storage and progressive disclosure.

    Section structure:
    - One section per top-level key
    - Nested objects are formatted as JSON
    - Lists are formatted as bullet lists
    """

    def parse(self) -> ParsedDocument:
        """
        Parse config file - store original JSON in frontmatter.

        For config files (settings.json, mcp_config.json), we store the
        original JSON content as-is without creating sections. This ensures
        byte-perfect round-trip reconstruction.

        Returns:
            ParsedDocument with original JSON content (no sections)

        Raises:
            json.JSONDecodeError: If config file is invalid
        """
        # Validate JSON structure
        config_data = json.loads(self.content)

        # Store original JSON exactly in frontmatter field (no sections)
        # Recomposer will return frontmatter as-is for FileType.CONFIG with no sections
        return ParsedDocument(
            frontmatter=self.content,  # Store original JSON exactly
            sections=[],                # No sections - preserve as single unit
            file_type=FileType.CONFIG,
            format=FileFormat.JSON,
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        """
        Validate config structure.

        Returns:
            ValidationResult with errors/warnings

        Checks:
        - Valid JSON format
        - Known settings keys (for settings.json)
        - MCP server config structure (for mcp_config.json)
        """
        result = ValidationResult(is_valid=True)

        try:
            config_data = json.loads(self.content)

            # Check for known config schemas
            filename = Path(self.file_path).name

            if filename == "settings.json":
                self._validate_settings(config_data, result)
            elif filename == "mcp_config.json":
                self._validate_mcp_config(config_data, result)
            else:
                # Generic JSON config - just validate structure
                if not isinstance(config_data, dict):
                    result.add_error("Config must be a JSON object")

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")

        return result

    def get_related_files(self) -> List[str]:
        """
        Get list of related files.

        Returns:
            Empty list (config files are standalone)
        """
        return []

    def get_file_type(self) -> FileType:
        """Return FileType.CONFIG for this handler."""
        return FileType.CONFIG

    def get_file_format(self) -> FileFormat:
        """Return FileFormat.JSON for configs."""
        return FileFormat.JSON

    def _validate_settings(self, data: dict, result: ValidationResult) -> None:
        """
        Validate settings.json structure.

        Args:
            data: Parsed settings data
            result: ValidationResult to update

        Checks for known settings keys and warns about unknown ones.
        """
        # Known settings keys (may expand over time)
        known_keys = {
            "permissions", "plugins", "mcpServers",
            "voiceCommands", "context", "modes",
            "allowedNetworkDomains", "allowedNetworkHosts"
        }

        if not isinstance(data, dict):
            result.add_error("Settings must be a JSON object")
            return

        for key in data.keys():
            if key not in known_keys:
                result.add_warning(f"Unknown settings key: {key}")

    def _validate_mcp_config(self, data: dict, result: ValidationResult) -> None:
        """
        Validate MCP server configuration.

        Args:
            data: Parsed MCP config data
            result: ValidationResult to update

        Checks that each server has a command or url.
        """
        if not isinstance(data, dict):
            result.add_error("MCP config must be a JSON object")
            return

        if not data:
            result.add_warning("Empty MCP configuration")

        for server_name, server_config in data.items():
            if not isinstance(server_config, dict):
                result.add_error(f"Invalid config for server: {server_name} (must be object)")
                continue

            # Check that server has command or url
            if "command" not in server_config and "url" not in server_config:
                result.add_error(f"Server {server_name} missing 'command' or 'url'")

            # Check for valid args if command present
            if "command" in server_config and "args" in server_config:
                if not isinstance(server_config["args"], list):
                    result.add_error(f"Server {server_name}: 'args' must be an array")

    def _format_config_item(self, key: str, value: Any) -> str:
        """
        Format config item as markdown.

        Args:
            key: Config key name
            value: Config value (any type)

        Returns:
            Formatted string
        """
        if isinstance(value, dict):
            # Format as pretty JSON
            return json.dumps(value, indent=2)
        elif isinstance(value, list):
            # Format as bullet list for simple string lists
            if not value:
                return "(empty list)"
            # Check if list contains only simple types (strings, numbers, booleans)
            if all(isinstance(item, (str, int, float, bool)) or item is None for item in value):
                lines = []
                for item in value:
                    if isinstance(item, bool):
                        lines.append(f"- {'true' if item else 'false'}")
                    elif item is None:
                        lines.append("- null")
                    else:
                        lines.append(f"- {item}")
                return "\n".join(lines)
            # Complex list with nested objects - format as JSON
            return json.dumps(value, indent=2)
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif value is None:
            return "null"
        else:
            return str(value)
