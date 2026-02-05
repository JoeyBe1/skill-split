"""
Unit tests for PluginHandler.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path

from handlers.plugin_handler import PluginHandler
from models import FileType, FileFormat, ValidationResult


class TestPluginHandler:
    """Tests for PluginHandler class."""

    @pytest.fixture
    def plugin_dir(self):
        """Create a temporary directory with test plugin files."""
        temp_dir = tempfile.mkdtemp()
        plugin_path = Path(temp_dir) / "plugin.json"

        # Create plugin.json
        plugin_data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "permissions": ["allowNetwork", "allowFileSystemRead"],
        }
        with open(plugin_path, 'w') as f:
            json.dump(plugin_data, f, indent=2)

        yield str(plugin_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def plugin_with_mcp(self):
        """Create a temporary directory with plugin and MCP config."""
        temp_dir = tempfile.mkdtemp()
        plugin_path = Path(temp_dir) / "plugin.json"
        mcp_path = Path(temp_dir) / "test-plugin.mcp.json"

        # Create plugin.json
        plugin_data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "A test plugin with MCP",
            "mcpServers": {"server1": {}}
        }
        with open(plugin_path, 'w') as f:
            json.dump(plugin_data, f, indent=2)

        # Create .mcp.json
        mcp_data = {
            "mcpServers": {
                "server1": {
                    "command": "node",
                    "args": ["server.js"]
                }
            }
        }
        with open(mcp_path, 'w') as f:
            json.dump(mcp_data, f, indent=2)

        yield str(plugin_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def plugin_with_hooks(self):
        """Create a temporary directory with plugin and hooks."""
        temp_dir = tempfile.mkdtemp()
        plugin_path = Path(temp_dir) / "plugin.json"
        hooks_path = Path(temp_dir) / "hooks.json"

        # Create plugin.json
        plugin_data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "A test plugin with hooks",
            "hooks": ["pre-commit"]
        }
        with open(plugin_path, 'w') as f:
            json.dump(plugin_data, f, indent=2)

        # Create hooks.json
        hooks_data = {
            "pre-commit": {
                "description": "Runs before commit"
            }
        }
        with open(hooks_path, 'w') as f:
            json.dump(hooks_data, f, indent=2)

        yield str(plugin_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_plugin_parse_basic(self, plugin_dir):
        """Test basic plugin.json parsing."""
        handler = PluginHandler(plugin_dir)
        doc = handler.parse()

        assert doc.file_type == FileType.PLUGIN
        assert doc.format == FileFormat.MULTI_FILE
        assert len(doc.sections) >= 1
        assert doc.sections[0].title == "metadata"
        assert "test-plugin" in doc.sections[0].content

    def test_plugin_parse_with_mcp(self, plugin_with_mcp):
        """Test plugin parsing with MCP config."""
        handler = PluginHandler(plugin_with_mcp)
        doc = handler.parse()

        assert len(doc.sections) >= 2
        section_titles = [s.title for s in doc.sections]
        assert "metadata" in section_titles
        assert "mcp_config" in section_titles

    def test_plugin_parse_with_hooks(self, plugin_with_hooks):
        """Test plugin parsing with hooks config."""
        handler = PluginHandler(plugin_with_hooks)
        doc = handler.parse()

        assert len(doc.sections) >= 2
        section_titles = [s.title for s in doc.sections]
        assert "metadata" in section_titles
        assert "hooks" in section_titles

    def test_plugin_validation_valid(self, plugin_dir):
        """Test validation of valid plugin."""
        handler = PluginHandler(plugin_dir)
        result = handler.validate()

        assert result.is_valid
        assert len(result.errors) == 0

    def test_plugin_validation_missing_fields(self):
        """Test validation with missing required fields."""
        temp_dir = tempfile.mkdtemp()
        plugin_path = Path(temp_dir) / "plugin.json"

        # Create plugin with missing fields
        plugin_data = {"name": "incomplete"}
        with open(plugin_path, 'w') as f:
            json.dump(plugin_data, f)

        handler = PluginHandler(str(plugin_path))
        result = handler.validate()

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("version" in e for e in result.errors)
        assert any("description" in e for e in result.errors)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_plugin_related_files(self, plugin_with_mcp):
        """Test related file detection."""
        handler = PluginHandler(plugin_with_mcp)
        related = handler.get_related_files()

        assert isinstance(related, list)
        assert len(related) >= 1
        assert any("mcp.json" in f for f in related)

    def test_plugin_get_file_type(self, plugin_dir):
        """Test get_file_type returns PLUGIN."""
        handler = PluginHandler(plugin_dir)
        assert handler.get_file_type() == FileType.PLUGIN

    def test_plugin_get_file_format(self, plugin_dir):
        """Test get_file_format returns MULTI_FILE."""
        handler = PluginHandler(plugin_dir)
        assert handler.get_file_format() == FileFormat.MULTI_FILE

    def test_plugin_metadata_formatting(self, plugin_dir):
        """Test metadata is formatted as markdown."""
        handler = PluginHandler(plugin_dir)
        doc = handler.parse()

        metadata_content = doc.sections[0].content
        assert "# test-plugin" in metadata_content
        assert "1.0.0" in metadata_content
        assert "A test plugin" in metadata_content

    def test_plugin_recompute_hash_single_file(self, plugin_dir):
        """Test hash computation for single file."""
        handler = PluginHandler(plugin_dir)
        hash1 = handler.recompute_hash()
        hash2 = handler.recompute_hash()

        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
