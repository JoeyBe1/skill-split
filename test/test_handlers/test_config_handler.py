"""
Unit tests for ConfigHandler.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path

from handlers.config_handler import ConfigHandler
from models import FileType, FileFormat, ValidationResult


class TestConfigHandler:
    """Tests for ConfigHandler class."""

    @pytest.fixture
    def settings_file(self):
        """Create a temporary settings.json file."""
        temp_dir = tempfile.mkdtemp()
        settings_path = Path(temp_dir) / "settings.json"

        settings_data = {
            "permissions": {
                "allowNetwork": True,
                "allowFileSystemRead": True,
                "allowFileSystemWrite": False
            },
            "enabledPlugins": ["plugin1", "plugin2"],  # Changed to simple list
            "mcpServers": {
                "server1": {
                    "command": "node",
                    "args": ["server.js"]
                }
            }
        }
        with open(settings_path, 'w') as f:
            json.dump(settings_data, f, indent=2)

        yield str(settings_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mcp_config_file(self):
        """Create a temporary mcp_config.json file."""
        temp_dir = tempfile.mkdtemp()
        mcp_path = Path(temp_dir) / "mcp_config.json"

        mcp_data = {
            "test-server": {
                "command": "node",
                "args": ["server.js"]
            },
            "remote-server": {
                "url": "http://localhost:3000"
            }
        }
        with open(mcp_path, 'w') as f:
            json.dump(mcp_data, f, indent=2)

        yield str(mcp_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def invalid_config_file(self):
        """Create an invalid config file."""
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / "settings.json"

        with open(config_path, 'w') as f:
            f.write("{ invalid json }")

        yield str(config_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_config_parse_settings(self, settings_file):
        """Test parsing settings.json."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        assert doc.file_type == FileType.CONFIG
        assert doc.format == FileFormat.JSON
        assert len(doc.sections) == 3  # permissions, enabledPlugins, mcpServers

        section_titles = [s.title for s in doc.sections]
        assert "permissions" in section_titles
        assert "enabledPlugins" in section_titles
        assert "mcpServers" in section_titles

    def test_config_parse_mcp_config(self, mcp_config_file):
        """Test parsing mcp_config.json."""
        handler = ConfigHandler(mcp_config_file)
        doc = handler.parse()

        assert len(doc.sections) == 2  # Two servers
        assert doc.sections[0].title == "test-server"
        assert doc.sections[1].title == "remote-server"

    def test_config_validation_valid_settings(self, settings_file):
        """Test validation of valid settings.json."""
        handler = ConfigHandler(settings_file)
        result = handler.validate()

        assert result.is_valid
        assert len(result.errors) == 0

    def test_config_validation_valid_mcp_config(self, mcp_config_file):
        """Test validation of valid mcp_config.json."""
        handler = ConfigHandler(mcp_config_file)
        result = handler.validate()

        assert result.is_valid
        assert len(result.errors) == 0

    def test_config_validation_invalid_json(self, invalid_config_file):
        """Test validation of invalid JSON."""
        handler = ConfigHandler(invalid_config_file)
        result = handler.validate()

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("Invalid JSON" in e for e in result.errors)

    def test_config_validation_invalid_mcp_server(self):
        """Test validation of MCP server without command or url."""
        temp_dir = tempfile.mkdtemp()
        mcp_path = Path(temp_dir) / "mcp_config.json"

        mcp_data = {
            "bad-server": {
                "env": {"TEST": "value"}
                # Missing command and url
            }
        }
        with open(mcp_path, 'w') as f:
            json.dump(mcp_data, f)

        handler = ConfigHandler(str(mcp_path))
        result = handler.validate()

        assert not result.is_valid
        assert any("missing 'command' or 'url'" in e for e in result.errors)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_config_related_files(self, settings_file):
        """Test that config files have no related files."""
        handler = ConfigHandler(settings_file)
        related = handler.get_related_files()

        assert isinstance(related, list)
        assert len(related) == 0

    def test_config_get_file_type(self, settings_file):
        """Test get_file_type returns CONFIG."""
        handler = ConfigHandler(settings_file)
        assert handler.get_file_type() == FileType.CONFIG

    def test_config_get_file_format(self, settings_file):
        """Test get_file_format returns JSON."""
        handler = ConfigHandler(settings_file)
        assert handler.get_file_format() == FileFormat.JSON

    def test_config_format_dict(self, settings_file):
        """Test that dict values are formatted as JSON."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        permissions_section = next(s for s in doc.sections if s.title == "permissions")
        content = permissions_section.content

        assert "allowNetwork" in content
        assert "true" in content

    def test_config_format_list(self, settings_file):
        """Test that list values are formatted as bullet lists."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        enabled_plugins_section = next(s for s in doc.sections if s.title == "enabledPlugins")
        content = enabled_plugins_section.content

        assert "- plugin1" in content
        assert "- plugin2" in content

    def test_config_recompute_hash(self, settings_file):
        """Test hash computation for config files."""
        handler = ConfigHandler(settings_file)
        hash1 = handler.recompute_hash()
        hash2 = handler.recompute_hash()

        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_config_recompose(self, settings_file):
        """Test recompose functionality."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        recomposed = handler.recompose(doc.sections)

        assert recomposed
        # The recomposed output should have content from all sections
        assert "allowNetwork" in recomposed  # From permissions section
        assert "plugin1" in recomposed  # From enabledPlugins section
        assert "server1" in recomposed  # From mcpServers section

    def test_config_frontmatter(self, settings_file):
        """Test that frontmatter includes file type."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        frontmatter_data = json.loads(doc.frontmatter)
        assert frontmatter_data["type"] == "config"
        assert frontmatter_data["file_type"] == "settings.json"
