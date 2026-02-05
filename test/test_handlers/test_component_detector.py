"""
Unit tests for ComponentDetector.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from handlers.component_detector import ComponentDetector
from models import FileType, FileFormat


class TestComponentDetector:
    """Tests for ComponentDetector class."""

    def test_detect_plugin_json(self):
        """Test detection of plugin.json."""
        file_type, file_format = ComponentDetector.detect("plugin.json")

        assert file_type == FileType.PLUGIN
        assert file_format == FileFormat.JSON

    def test_detect_hooks_json(self):
        """Test detection of hooks.json."""
        file_type, file_format = ComponentDetector.detect("hooks.json")

        assert file_type == FileType.HOOK
        assert file_format == FileFormat.JSON

    def test_detect_settings_json(self):
        """Test detection of settings.json."""
        file_type, file_format = ComponentDetector.detect("settings.json")

        assert file_type == FileType.CONFIG
        assert file_format == FileFormat.JSON

    def test_detect_mcp_config_json(self):
        """Test detection of mcp_config.json."""
        file_type, file_format = ComponentDetector.detect("mcp_config.json")

        assert file_type == FileType.CONFIG
        assert file_format == FileFormat.JSON

    def test_detect_readme_md(self):
        """Test detection of README.md."""
        file_type, file_format = ComponentDetector.detect("README.md")

        assert file_type == FileType.DOCUMENTATION
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_claude_md(self):
        """Test detection of CLAUDE.md."""
        file_type, file_format = ComponentDetector.detect("CLAUDE.md")

        assert file_type == FileType.DOCUMENTATION
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_skill_md(self):
        """Test detection of SKILL.md in skills directory."""
        file_type, file_format = ComponentDetector.detect("/skills/my-skill/SKILL.md")

        assert file_type == FileType.SKILL
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_command_md(self):
        """Test detection of command markdown."""
        file_type, file_format = ComponentDetector.detect("/commands/my-command/command.md")

        assert file_type == FileType.COMMAND
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_agent_md(self):
        """Test detection of agent markdown."""
        file_type, file_format = ComponentDetector.detect("/agents/my-agent/agent.md")

        assert file_type == FileType.AGENT
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_output_style(self):
        """Test detection of output-style markdown."""
        file_type, file_format = ComponentDetector.detect("/output-styles/my-style.md")

        assert file_type == FileType.OUTPUT_STYLE
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_reference_md(self):
        """Test detection of reference markdown."""
        file_type, file_format = ComponentDetector.detect("/get-shit-done/references/my-ref.md")

        assert file_type == FileType.REFERENCE
        assert file_format == FileFormat.MARKDOWN_HEADINGS

    def test_detect_shell_script(self):
        """Test detection of shell script."""
        file_type, file_format = ComponentDetector.detect("my-script.sh")

        assert file_type == FileType.HOOK
        assert file_format == FileFormat.SHELL_SCRIPT

    def test_get_handler_for_plugin(self):
        """Test getting handler for plugin.json."""
        temp_dir = tempfile.mkdtemp()
        plugin_path = Path(temp_dir) / "plugin.json"

        # Create minimal plugin.json
        plugin_path.write_text('{"name": "test", "version": "1.0.0", "description": "test"}')

        handler = ComponentDetector.get_handler(str(plugin_path))

        assert handler is not None
        assert handler.__class__.__name__ == "PluginHandler"

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_get_handler_for_markdown_returns_none(self):
        """Test that markdown files return None handler."""
        temp_dir = tempfile.mkdtemp()
        readme_path = Path(temp_dir) / "README.md"

        readme_path.write_text("# Test README")

        handler = ComponentDetector.get_handler(str(readme_path))

        # Markdown files should return None to use existing Parser
        assert handler is None

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_get_handler_for_unknown_json(self):
        """Test that unknown JSON files get ConfigHandler."""
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / "unknown.json"

        config_path.write_text('{"key": "value"}')

        handler = ComponentDetector.get_handler(str(config_path))

        assert handler is not None
        assert handler.__class__.__name__ == "ConfigHandler"

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_is_markdown_file_for_readme(self):
        """Test is_markdown_file for README.md."""
        assert ComponentDetector.is_markdown_file("README.md") is True

    def test_is_markdown_file_for_plugin(self):
        """Test is_markdown_file for plugin.json."""
        assert ComponentDetector.is_markdown_file("plugin.json") is False

    def test_is_markdown_file_for_skill(self):
        """Test is_markdown_file for SKILL.md."""
        assert ComponentDetector.is_markdown_file("/skills/test/SKILL.md") is True

    def test_detect_with_windows_paths(self):
        """Test detection with Windows-style paths."""
        file_type, file_format = ComponentDetector.detect("C:\\users\\test\\plugin.json")

        # Should still detect correctly despite Windows path separators
        assert file_type == FileType.PLUGIN
        assert file_format == FileFormat.JSON

    def test_detect_nested_plugin_json(self):
        """Test detection of plugin.json in nested directory."""
        file_type, file_format = ComponentDetector.detect("/path/to/plugin.json")

        assert file_type == FileType.PLUGIN
        assert file_format == FileFormat.JSON
