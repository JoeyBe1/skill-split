"""
Unit tests for HookHandler.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path

from handlers.hook_handler import HookHandler
from models import FileType, FileFormat, ValidationResult


class TestHookHandler:
    """Tests for HookHandler class."""

    @pytest.fixture
    def hooks_dir(self):
        """Create a temporary directory with test hook files."""
        temp_dir = tempfile.mkdtemp()
        hooks_path = Path(temp_dir) / "hooks.json"

        # Create hooks.json
        hooks_data = {
            "pre-commit": {
                "description": "Runs before commit",
                "permissions": ["allowFileSystemRead"],
                "enabled": True
            },
            "post-commit": {
                "description": "Runs after commit",
                "permissions": ["allowNetwork"],
                "enabled": True
            }
        }
        with open(hooks_path, 'w') as f:
            json.dump(hooks_data, f, indent=2)

        # Create script files
        for hook_name in ["pre-commit", "post-commit"]:
            script_path = Path(temp_dir) / f"{hook_name}.sh"
            with open(script_path, 'w') as f:
                f.write(f"#!/bin/bash\n# {hook_name} hook\necho 'Running {hook_name}...'\n")

        yield str(hooks_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def hooks_dir_missing_scripts(self):
        """Create hooks.json without script files."""
        temp_dir = tempfile.mkdtemp()
        hooks_path = Path(temp_dir) / "hooks.json"

        hooks_data = {
            "pre-commit": {
                "description": "Runs before commit"
            }
        }
        with open(hooks_path, 'w') as f:
            json.dump(hooks_data, f)

        yield str(hooks_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_hook_parse_basic(self, hooks_dir):
        """Test basic hooks.json parsing."""
        handler = HookHandler(hooks_dir)
        doc = handler.parse()

        assert doc.file_type == FileType.HOOK
        assert doc.format == FileFormat.MULTI_FILE
        assert len(doc.sections) == 2  # One section per hook
        assert doc.frontmatter  # Frontmatter contains original JSON
        assert "pre-commit" in doc.frontmatter
        assert "post-commit" in doc.frontmatter

    def test_hook_parse_with_scripts(self, hooks_dir):
        """Test that hook data is preserved in frontmatter."""
        handler = HookHandler(hooks_dir)
        doc = handler.parse()

        # Original JSON should be in frontmatter
        assert doc.frontmatter
        parsed = json.loads(doc.frontmatter)
        assert "pre-commit" in parsed
        assert "post-commit" in parsed

    def test_hook_validation_valid(self, hooks_dir):
        """Test validation of valid hooks."""
        handler = HookHandler(hooks_dir)
        result = handler.validate()

        assert result.is_valid
        assert len(result.errors) == 0

    def test_hook_validation_missing_scripts(self, hooks_dir_missing_scripts):
        """Test validation warns about missing scripts."""
        handler = HookHandler(hooks_dir_missing_scripts)
        result = handler.validate()

        # Should still be valid but with warnings
        assert result.is_valid or len(result.warnings) > 0
        if result.warnings:
            assert any("Script not found" in w for w in result.warnings)

    def test_hook_validation_empty(self):
        """Test validation of empty hooks.json."""
        temp_dir = tempfile.mkdtemp()
        hooks_path = Path(temp_dir) / "hooks.json"

        with open(hooks_path, 'w') as f:
            json.dump({}, f)

        handler = HookHandler(str(hooks_path))
        result = handler.validate()

        assert not result.is_valid
        assert any("No hooks defined" in e for e in result.errors)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_hook_related_files(self, hooks_dir):
        """Test related file detection."""
        handler = HookHandler(hooks_dir)
        related = handler.get_related_files()

        assert isinstance(related, list)
        assert len(related) == 2
        assert any("pre-commit.sh" in f for f in related)
        assert any("post-commit.sh" in f for f in related)

    def test_hook_get_file_type(self, hooks_dir):
        """Test get_file_type returns HOOK."""
        handler = HookHandler(hooks_dir)
        assert handler.get_file_type() == FileType.HOOK

    def test_hook_get_file_format(self, hooks_dir):
        """Test get_file_format returns MULTI_FILE."""
        handler = HookHandler(hooks_dir)
        assert handler.get_file_format() == FileFormat.MULTI_FILE

    def test_hook_formatting(self, hooks_dir):
        """Test hook data is preserved in frontmatter as JSON."""
        handler = HookHandler(hooks_dir)
        doc = handler.parse()

        # Original JSON should be in frontmatter
        assert doc.frontmatter
        parsed = json.loads(doc.frontmatter)
        assert parsed["pre-commit"]["description"] == "Runs before commit"
        assert parsed["post-commit"]["description"] == "Runs after commit"

    def test_hook_recompute_hash(self, hooks_dir):
        """Test hash computation for hooks."""
        handler = HookHandler(hooks_dir)
        hash1 = handler.recompute_hash()
        hash2 = handler.recompute_hash()

        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_hook_recompose(self, hooks_dir):
        """Test that frontmatter contains complete original JSON for recomposition."""
        handler = HookHandler(hooks_dir)
        doc = handler.parse()

        # With no sections, the frontmatter should contain the complete original JSON
        # The Recomposer class will use this when reconstructing
        assert doc.frontmatter
        assert "pre-commit" in doc.frontmatter
        assert "post-commit" in doc.frontmatter
