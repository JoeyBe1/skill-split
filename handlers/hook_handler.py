"""
Handler for hook components.

A hook consists of:
- hooks.json: Hook definitions
- Associated shell scripts: One per hook
"""

import json
from pathlib import Path
from typing import List

from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class HookHandler(BaseHandler):
    """
    Handler for hook components.

    Parses hooks.json and associated shell scripts into structured
    sections for database storage and progressive disclosure.

    Section structure:
    - One section per hook name
    - Each section contains hook config and script content
    """

    def parse(self) -> ParsedDocument:
        """
        Parse hooks.json - store original content for byte-perfect reconstruction.

        For hooks.json files, we store the original JSON content as-is without
        creating sections. This ensures byte-perfect round-trip reconstruction.

        Returns:
            ParsedDocument with original JSON content (no sections)

        Raises:
            json.JSONDecodeError: If hooks.json is invalid
        """
        # Validate JSON structure
        hooks_data = json.loads(self.content)

        # Store original JSON exactly in frontmatter field (no sections)
        # Recomposer will return frontmatter as-is for FileType.HOOK with no sections
        return ParsedDocument(
            frontmatter=self.content,  # Store original JSON exactly
            sections=[],                # No sections - preserve as single unit
            file_type=FileType.HOOK,
            format=FileFormat.MULTI_FILE,
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        """
        Validate hook structure.

        Returns:
            ValidationResult with errors/warnings

        Checks:
        - At least one hook defined
        - Script files exist for each hook
        - Hook config is valid
        - Descriptions present
        """
        result = ValidationResult(is_valid=True)

        try:
            hooks_data = json.loads(self.content)

            if not hooks_data:
                result.add_error("No hooks defined")

            for hook_name, hook_config in hooks_data.items():
                # Check for script file
                hook_dir = Path(self.file_path).parent
                script_file = hook_dir / f"{hook_name}.sh"

                if not script_file.exists():
                    result.add_warning(f"Script not found for hook: {hook_name}")

                # Validate hook config
                if not isinstance(hook_config, dict):
                    result.add_error(f"Invalid config for hook: {hook_name} (must be object)")
                    continue

                if "description" not in hook_config:
                    result.add_warning(f"No description for hook: {hook_name}")

                # Check for executable permission
                if script_file.exists():
                    if not script_file.stat().st_mode & 0o111:
                        result.add_warning(f"Script not executable: {hook_name}.sh")

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON in hooks.json: {e}")

        return result

    def get_related_files(self) -> List[str]:
        """
        Get list of hook script files.

        Returns:
            List of absolute file paths to shell scripts

        Related files:
        - {hook_name}.sh for each hook in hooks.json
        """
        related = []
        hook_dir = Path(self.file_path).parent

        try:
            hooks_data = json.loads(self.content)
            for hook_name in hooks_data.keys():
                script_file = hook_dir / f"{hook_name}.sh"
                if script_file.exists():
                    related.append(str(script_file.absolute()))
        except json.JSONDecodeError:
            # Invalid JSON, return empty list
            pass

        return related

    def get_file_type(self) -> FileType:
        """Return FileType.HOOK for this handler."""
        return FileType.HOOK

    def get_file_format(self) -> FileFormat:
        """Return FileFormat.MULTI_FILE for hooks."""
        return FileFormat.MULTI_FILE
