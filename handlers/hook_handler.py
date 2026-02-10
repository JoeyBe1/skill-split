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
        Parse hooks.json while preserving byte-perfect original content.

        We store the original JSON exactly in frontmatter for exact
        round-trip reconstruction, AND generate sections for progressive
        disclosure (one per hook, plus optional overview).
        """
        hooks_data = json.loads(self.content)
        sections: List[Section] = []

        # Detect plugin-style hook file: { "description": "...", "hooks": {...} }
        hook_map = hooks_data
        if isinstance(hooks_data, dict) and "hooks" in hooks_data and isinstance(hooks_data.get("hooks"), dict):
            description = hooks_data.get("description")
            overview_lines = ["# overview"]
            if description:
                overview_lines.append(f"**Description**: {description}")
            overview_content = "\n".join(overview_lines).strip() + "\n"
            sections.append(Section(
                level=1,
                title="overview",
                content=overview_content,
                line_start=1,
                line_end=len(overview_content.splitlines()),
            ))
            hook_map = hooks_data.get("hooks", {})

        if isinstance(hook_map, dict):
            for hook_name, hook_config in hook_map.items():
                section_lines = [f"# {hook_name}"]

                if isinstance(hook_config, dict):
                    if "description" in hook_config:
                        section_lines.append(f"**Description**: {hook_config.get('description')}")
                    # Include full config as JSON for clarity
                    section_lines.append("## Config")
                    section_lines.append(json.dumps(hook_config, indent=2))
                else:
                    # Non-dict config, include raw value
                    section_lines.append("## Config")
                    section_lines.append(json.dumps(hook_config, indent=2))

                # Include script content if present
                script_path = Path(self.file_path).parent / f"{hook_name}.sh"
                if script_path.exists():
                    section_lines.append("## Script")
                    section_lines.append("```bash")
                    section_lines.append(script_path.read_text().rstrip("\n"))
                    section_lines.append("```")

                section_content = "\n".join(section_lines).strip() + "\n"
                sections.append(Section(
                    level=1,
                    title=hook_name,
                    content=section_content,
                    line_start=1,
                    line_end=len(section_content.splitlines()),
                ))

        return ParsedDocument(
            frontmatter=self.content,  # Store original JSON exactly
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
