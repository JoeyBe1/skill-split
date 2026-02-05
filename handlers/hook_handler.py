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
        Parse hooks.json and associated scripts into sections.

        Returns:
            ParsedDocument with hook structure

        Each hook becomes a section with:
        - Hook name as title
        - Hook description and config
        - Shell script content (if exists)

        Raises:
            json.JSONDecodeError: If hooks.json is invalid
        """
        hooks_data = json.loads(self.content)
        sections = []

        # Handle different hook file formats
        # Format 1: { "hook_name": { "description": "...", "hooks": {...} } }
        # Format 2: { "description": "...", "hooks": { "Event": [...] } }

        if "hooks" in hooks_data and isinstance(hooks_data["hooks"], dict):
            # Format 2: Plugin-style hooks file
            description = hooks_data.get("description", "Hook configuration")
            hooks_obj = hooks_data["hooks"]

            # Create overview section
            sections.append(Section(
                level=1,
                title="overview",
                content=f"# Hook Configuration\n\n**Description**: {description}\n\n**Events**: {', '.join(hooks_obj.keys())}",
                line_start=1,
                line_end=self.content.count('\n') + 1,
            ))

            # Create section for each event
            for event_name, event_hooks in hooks_obj.items():
                event_content = json.dumps(event_hooks, indent=2)
                sections.append(Section(
                    level=1,
                    title=event_name,
                    content=event_content,
                    line_start=1,
                    line_end=self.content.count('\n') + 1,
                ))
        else:
            # Format 1: Traditional hooks file - each hook is a top-level key
            for hook_name, hook_config in hooks_data.items():
                hook_dir = Path(self.file_path).parent

                # Find script file
                script_file = hook_dir / f"{hook_name}.sh"
                script_content = ""

                if script_file.exists():
                    with open(script_file, 'r', encoding='utf-8') as f:
                        script_content = f.read()

                # Handle both dict and string hook_config
                if isinstance(hook_config, str):
                    hook_config = {"description": hook_config}

                # Create section for this hook
                sections.append(Section(
                    level=1,
                    title=hook_name,
                    content=self._format_hook(hook_name, hook_config, script_content),
                    line_start=1,
                    line_end=script_content.count('\n') + 1 if script_content else 1,
                ))

        return ParsedDocument(
            frontmatter=json.dumps({
                "type": "hooks",
                "count": len(sections)
            }, indent=2),
            sections=sections,
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

    def _format_hook(self, name: str, config: dict, script: str) -> str:
        """
        Format hook as markdown with script.

        Args:
            name: Hook name
            config: Hook configuration dict
            script: Shell script content

        Returns:
            Formatted markdown string
        """
        lines = [
            f"# {name}",
            "",
            f"**Description**: {config.get('description', 'No description')}",
            "",
        ]

        if "permissions" in config:
            lines.append("**Permissions**:")
            for perm in config["permissions"]:
                lines.append(f"- {perm}")
            lines.append("")

        if "enabled" in config:
            status = "enabled" if config["enabled"] else "disabled"
            lines.append(f"**Status**: {status}")
            lines.append("")

        if script:
            lines.append("## Script")
            lines.append("")
            lines.append("```bash")
            lines.append(script)
            # Handle scripts that don't end with newline
            if not script.endswith('\n'):
                lines.append("")
            lines.append("```")

        return "\n".join(lines)
