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
        assert len(doc.sections) == 3  # One section per top-level key
        assert doc.frontmatter  # Frontmatter contains original JSON
        assert "permissions" in doc.frontmatter

    def test_config_parse_mcp_config(self, mcp_config_file):
        """Test parsing mcp_config.json."""
        handler = ConfigHandler(mcp_config_file)
        doc = handler.parse()

        assert len(doc.sections) == 2  # One section per top-level key
        assert doc.frontmatter  # Frontmatter contains original JSON
        assert "test-server" in doc.frontmatter
        assert "remote-server" in doc.frontmatter

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
        """Test that original JSON is preserved in frontmatter."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        # Original JSON is in frontmatter
        assert "permissions" in doc.frontmatter
        assert "allowNetwork" in doc.frontmatter

    def test_config_format_list(self, settings_file):
        """Test that original JSON is preserved in frontmatter."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        # Original JSON is in frontmatter
        assert "enabledPlugins" in doc.frontmatter
        assert "plugin1" in doc.frontmatter
        assert "plugin2" in doc.frontmatter

    def test_config_recompute_hash(self, settings_file):
        """Test hash computation for config files."""
        handler = ConfigHandler(settings_file)
        hash1 = handler.recompute_hash()
        hash2 = handler.recompute_hash()

        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_config_recompose(self, settings_file):
        """Test that frontmatter contains complete original JSON for recomposition."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        # With no sections, the frontmatter should contain the complete original JSON
        # The Recomposer class will use this when reconstructing
        assert doc.frontmatter  # Frontmatter should not be empty

        # The frontmatter should be valid JSON with all content
        assert "permissions" in doc.frontmatter  # All original keys should be present
        assert "enabledPlugins" in doc.frontmatter
        assert "mcpServers" in doc.frontmatter

    def test_config_frontmatter(self, settings_file):
        """Test that frontmatter contains original JSON content."""
        handler = ConfigHandler(settings_file)
        doc = handler.parse()

        # Frontmatter should be valid JSON (the original file content)
        parsed = json.loads(doc.frontmatter)
        assert isinstance(parsed, dict)
        assert "permissions" in parsed
        assert "enabledPlugins" in parsed
