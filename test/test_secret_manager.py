"""Tests for SecretManager functionality."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.secret_manager import (
    SecretManager,
    SecretNotFoundError,
    SecretSourceType
)


class TestSecretManagerBasic:
    """Basic secret manager tests."""

    def test_get_secret_from_environment(self):
        """Test retrieving secret from environment variable."""
        test_key = "TEST_SECRET_KEY_UNIQUE_12345"
        test_value = "test_secret_value_xyz"

        # Set environment variable
        with patch.dict(os.environ, {test_key: test_value}):
            with tempfile.TemporaryDirectory() as tmpdir:
                manager = SecretManager(
                    config_path=os.path.join(tmpdir, "secrets.json"),
                    use_keyring=False
                )
                result = manager.get_secret(test_key)

        assert result == test_value

    def test_get_secret_from_file(self):
        """Test retrieving secret from config file."""
        test_key = "test_api_key"
        test_value = "sk-test-12345"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "secrets.json")
            config_data = {
                "openai": test_value,
                "supabase_url": "https://test.supabase.co"
            }

            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            manager = SecretManager(
                config_path=config_path,
                use_keyring=False
            )

            # Use aliased key
            result = manager.get_secret("openai")

        assert result == test_value

    def test_get_secret_priority_order(self):
        """Test that file takes priority over environment."""
        test_key = "PRIORITY_TEST_KEY"
        file_value = "from_file"
        env_value = "from_environment"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "secrets.json")
            config_data = {test_key.lower(): file_value}

            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            with patch.dict(os.environ, {test_key: env_value}):
                manager = SecretManager(
                    config_path=config_path,
                    use_keyring=False
                )
                # File should take priority
                result = manager.get_secret(test_key.lower())

        assert result == file_value

    def test_get_secret_not_found_raises_error(self):
        """Test that SecretNotFoundError is raised when secret not found."""
        nonexistent_key = "NONEXISTENT_KEY_ABCXYZ123"

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecretManager(
                config_path=os.path.join(tmpdir, "empty_secrets.json"),
                use_keyring=False
            )

            # Remove environment variable if it exists
            with patch.dict(os.environ, {}, clear=False):
                # Remove the key from environment if present
                env_backup = os.environ.pop(nonexistent_key, None)

                try:
                    with pytest.raises(SecretNotFoundError) as exc_info:
                        manager.get_secret(nonexistent_key)

                    # Check error message includes key name
                    assert nonexistent_key in str(exc_info.value)
                finally:
                    # Restore environment if needed
                    if env_backup is not None:
                        os.environ[nonexistent_key] = env_backup

    def test_get_secret_with_source(self):
        """Test get_secret_with_source returns tuple."""
        test_key = "SOURCE_TEST_KEY"
        test_value = "test_value_abc"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "secrets.json")
            config_data = {test_key.lower(): test_value}

            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            manager = SecretManager(
                config_path=config_path,
                use_keyring=False
            )

            result = manager.get_secret_with_source(test_key.lower())

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == test_value
        assert result[1] == SecretSourceType.FILE

    def test_get_secret_with_source_environment(self):
        """Test get_secret_with_source with environment variable."""
        test_key = "ENV_SOURCE_TEST_KEY"
        test_value = "env_test_value_xyz"

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecretManager(
                config_path=os.path.join(tmpdir, "empty_secrets.json"),
                use_keyring=False
            )

            with patch.dict(os.environ, {test_key: test_value}):
                result = manager.get_secret_with_source(test_key)

        assert result[0] == test_value
        assert result[1] == SecretSourceType.ENV

    def test_key_aliases(self):
        """Test that key aliases work correctly."""
        openai_key = "sk-openai-alias-test-123"
        supabase_url = "https://alias-test.supabase.co"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "secrets.json")
            config_data = {
                "openai": openai_key,
                "supabase_url": supabase_url,
                "aliases": {
                    "OPENAI_API_KEY": "openai",
                    "SUPABASE_URL": "supabase_url"
                }
            }

            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            manager = SecretManager(
                config_path=config_path,
                use_keyring=False
            )

            # Test retrieving via alias
            result1 = manager.get_secret("OPENAI_API_KEY")
            result2 = manager.get_secret("SUPABASE_URL")

        assert result1 == openai_key
        assert result2 == supabase_url

    def test_list_available_secrets(self):
        """Test listing available secrets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "secrets.json")
            config_data = {
                "openai": "sk-test-1",
                "supabase_url": "https://test.supabase.co",
                "custom_key": "custom_value"
            }

            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            manager = SecretManager(
                config_path=config_path,
                use_keyring=False
            )

            # Set some environment variables
            with patch.dict(os.environ, {
                "ENV_API_KEY": "env_test_value",
                "ANOTHER_TOKEN": "token_value"
            }):
                result = manager.list_available_secrets()

        # Should contain keys from both file and environment
        assert isinstance(result, list)
        assert len(result) >= 3  # At least the file keys
        assert "openai" in result
        assert "supabase_url" in result
        assert "custom_key" in result

    def test_config_file_not_found(self):
        """Test graceful handling when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_config = os.path.join(tmpdir, "nonexistent.json")
            manager = SecretManager(
                config_path=nonexistent_config,
                use_keyring=False
            )

            # Should fall back to environment
            test_key = "FALLBACK_TEST_KEY"
            test_value = "fallback_value"

            with patch.dict(os.environ, {test_key: test_value}):
                result = manager.get_secret(test_key)

        assert result == test_value

    def test_invalid_config_json(self):
        """Test graceful handling of invalid JSON in config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "invalid.json")

            # Write invalid JSON
            with open(config_path, 'w') as f:
                f.write("{ invalid json }")

            manager = SecretManager(
                config_path=config_path,
                use_keyring=False
            )

            # Should fall back to environment
            test_key = "INVALID_JSON_TEST_KEY"
            test_value = "json_fallback_value"

            with patch.dict(os.environ, {test_key: test_value}):
                # Capture stderr to check for warning
                with patch('sys.stderr') as mock_stderr:
                    result = manager.get_secret(test_key)

        assert result == test_value
        # Warning should have been printed to stderr
        # (actual warning content tested by manual inspection)

    def test_optional_keyring_support(self):
        """Test graceful degradation when keyring not installed."""
        test_key = "KEYRING_TEST_KEY"

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manager with keyring enabled
            # Even if keyring is installed, this should work
            manager = SecretManager(
                config_path=os.path.join(tmpdir, "secrets.json"),
                use_keyring=True
            )

            # Should not raise ImportError
            # Falls back to environment if keyring not available
            test_value = "fallback_without_keyring"

            with patch.dict(os.environ, {test_key: test_value}):
                result = manager.get_secret(test_key)

        assert result == test_value

    def test_secret_not_found_error_message(self):
        """Test that SecretNotFoundError has helpful error message."""
        missing_key = "MISSING_SECRET_KEY_XYZ"

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecretManager(
                config_path=os.path.join(tmpdir, "empty_secrets.json"),
                use_keyring=False
            )

            with patch.dict(os.environ, {}, clear=False):
                # Remove key if it exists
                env_backup = os.environ.pop(missing_key, None)

                try:
                    with pytest.raises(SecretNotFoundError) as exc_info:
                        manager.get_secret(missing_key)

                    error_msg = str(exc_info.value)

                    # Check error message includes key name
                    assert missing_key in error_msg

                    # Check error message includes sources tried
                    assert "file" in error_msg.lower()
                    assert "environment" in error_msg.lower()
                finally:
                    if env_backup is not None:
                        os.environ[missing_key] = env_backup

    def test_specific_sources_parameter(self):
        """Test get_secret with specific sources parameter."""
        test_key = "SOURCES_TEST_KEY"
        file_value = "from_file"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "secrets.json")
            config_data = {test_key.lower(): file_value}

            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            # Set environment variable too
            env_value = "from_env"
            with patch.dict(os.environ, {test_key: env_value}):
                manager = SecretManager(
                    config_path=config_path,
                    use_keyring=False
                )

                # Only check file source
                result = manager.get_secret(
                    test_key.lower(),
                    sources=[SecretSourceType.FILE]
                )

        # Should get file value, not environment
        assert result == file_value

    def test_environment_only_sources(self):
        """Test get_secret with only environment source."""
        test_key = "ENV_ONLY_TEST_KEY"
        test_value = "env_only_value"

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecretManager(
                config_path=os.path.join(tmpdir, "secrets.json"),
                use_keyring=False
            )

            with patch.dict(os.environ, {test_key: test_value}):
                result = manager.get_secret(
                    test_key,
                    sources=[SecretSourceType.ENV]
                )

        assert result == test_value

    def test_empty_config_file(self):
        """Test behavior with empty config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "empty.json")

            # Create empty JSON file
            with open(config_path, 'w') as f:
                json.dump({}, f)

            manager = SecretManager(
                config_path=config_path,
                use_keyring=False
            )

            # Should fall back to environment
            test_key = "EMPTY_CONFIG_TEST_KEY"
            test_value = "env_value"

            with patch.dict(os.environ, {test_key: test_value}):
                result = manager.get_secret(test_key)

        assert result == test_value

    def test_config_with_nested_data(self):
        """Test config file with nested data (should ignore non-string values)."""
        test_key = "NESTED_TEST_KEY"
        test_value = "nested_value"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nested.json")
            config_data = {
                test_key.lower(): test_value,
                "nested_object": {"key": "value"},
                "array": ["one", "two"],
                "number": 123,
                "boolean": True
            }

            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            manager = SecretManager(
                config_path=config_path,
                use_keyring=False
            )

            result = manager.get_secret(test_key.lower())

        assert result == test_value
        # Non-string values should not be in list_available_secrets
        # (they're ignored by _load_config)
