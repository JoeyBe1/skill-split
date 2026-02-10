"""Secret manager for secure API key retrieval from multiple sources."""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SecretNotFoundError(Exception):
    """Raised when a secret cannot be found in any configured source."""

    def __init__(self, key: str, sources: List[str]):
        """
        Initialize secret not found error.

        Args:
            key: The secret key that was not found
            sources: List of sources that were tried
        """
        self.key = key
        self.sources = sources
        sources_str = ", ".join(sources)
        super().__init__(
            f"Secret '{key}' not found in any source. Tried: {sources_str}"
        )


class SecretSourceType(Enum):
    """Types of secret sources."""

    ENV = "environment"
    FILE = "file"
    KEYRING = "keyring"
    VAULT = "vault"


class SecretManager:
    """
    Manages secret retrieval from multiple sources with fallback.

    Priority order:
    1. File (~/.claude/secrets.json)
    2. Keyring (if use_keyring=True and keyring available)
    3. Environment variables

    This enables secure credential management without requiring
    environment variables for all secrets.
    """

    DEFAULT_CONFIG_PATH = "~/.claude/secrets.json"

    def __init__(
        self,
        config_path: Optional[str] = None,
        use_keyring: bool = False
    ):
        """
        Initialize secret manager.

        Args:
            config_path: Path to JSON file with secret mappings.
                        Defaults to ~/.claude/secrets.json
            use_keyring: Whether to try system keyring for secrets.
                        Defaults to False.
        """
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_PATH).expanduser()
        self.use_keyring = use_keyring

        # Try to import keyring if requested
        self._keyring = None
        if use_keyring:
            try:
                import keyring
                self._keyring = keyring
            except ImportError:
                # keyring not installed, will fall back to other sources
                pass

        # Ensure config directory exists
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        config_dir = self.config_path.parent
        if not config_dir.exists():
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                # If we can't create the directory, file source will fail gracefully
                pass

    def _load_config(self) -> Dict[str, str]:
        """
        Load secrets from config file.

        Returns:
            Dictionary of secret key to value mappings

        Raises:
            json.JSONDecodeError: If config file is invalid JSON
        """
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            # Extract secrets (excluding aliases)
            secrets = {}
            aliases = data.get("aliases", {})

            for key, value in data.items():
                if key != "aliases" and isinstance(value, str):
                    secrets[key] = value

            # Also add aliases as valid keys
            for alias, target_key in aliases.items():
                if target_key in secrets:
                    secrets[alias] = secrets[target_key]

            return secrets

        except json.JSONDecodeError as e:
            # Print warning to stderr for debugging
            import sys
            print(
                f"Warning: Invalid JSON in {self.config_path}: {e}",
                file=sys.stderr
            )
            return {}
        except Exception as e:
            # Log error but don't fail - other sources may work
            import sys
            print(
                f"Warning: Failed to load config from {self.config_path}: {e}",
                file=sys.stderr
            )
            return {}

    def _get_from_file(self, key: str) -> Optional[str]:
        """
        Get secret from config file.

        Args:
            key: Secret key to retrieve

        Returns:
            Secret value or None if not found
        """
        secrets = self._load_config()
        return secrets.get(key)

    def _get_from_keyring(self, key: str) -> Optional[str]:
        """
        Get secret from system keyring.

        Args:
            key: Secret key to retrieve

        Returns:
            Secret value or None if not found/keyring unavailable
        """
        if self._keyring is None:
            return None

        try:
            # Try to get password from keyring
            # Use "skill-split" as the service name
            password = self._keyring.get_password("skill-split", key)
            return password
        except Exception:
            # Keyring access failed, fall back silently
            return None

    def _get_from_environment(self, key: str) -> Optional[str]:
        """
        Get secret from environment variable.

        Args:
            key: Secret key to retrieve

        Returns:
            Secret value or None if not found
        """
        return os.getenv(key)

    def get_secret(
        self,
        key: str,
        sources: Optional[List[SecretSourceType]] = None
    ) -> str:
        """
        Get secret value from configured sources.

        Searches for secret in priority order:
        1. File (if enabled)
        2. Keyring (if enabled)
        3. Environment

        Args:
            key: Secret key to retrieve (e.g., "OPENAI_API_KEY")
            sources: Optional list of sources to check.
                     If None, checks all enabled sources.

        Returns:
            Secret value

        Raises:
            SecretNotFoundError: If secret not found in any source
        """
        if sources is None:
            sources = [
                SecretSourceType.FILE,
                SecretSourceType.KEYRING if self.use_keyring else None,
                SecretSourceType.ENV
            ]
            sources = [s for s in sources if s is not None]

        sources_tried = []

        # Try file source
        if SecretSourceType.FILE in sources:
            sources_tried.append("file")
            value = self._get_from_file(key)
            if value:
                return value

        # Try keyring source
        if SecretSourceType.KEYRING in sources and self.use_keyring:
            sources_tried.append("keyring")
            value = self._get_from_keyring(key)
            if value:
                return value

        # Try environment source
        if SecretSourceType.ENV in sources:
            sources_tried.append("environment")
            value = self._get_from_environment(key)
            if value:
                return value

        # Secret not found
        raise SecretNotFoundError(key, sources_tried)

    def get_secret_with_source(
        self,
        key: str
    ) -> Tuple[str, SecretSourceType]:
        """
        Get secret value along with its source.

        Useful for debugging and logging to understand where
        credentials are coming from.

        Args:
            key: Secret key to retrieve

        Returns:
            Tuple of (secret_value, source_type)

        Raises:
            SecretNotFoundError: If secret not found in any source
        """
        # Try file source
        value = self._get_from_file(key)
        if value:
            return (value, SecretSourceType.FILE)

        # Try keyring source
        if self.use_keyring:
            value = self._get_from_keyring(key)
            if value:
                return (value, SecretSourceType.KEYRING)

        # Try environment source
        value = self._get_from_environment(key)
        if value:
            return (value, SecretSourceType.ENV)

        # Secret not found
        sources = ["file"]
        if self.use_keyring:
            sources.append("keyring")
        sources.append("environment")
        raise SecretNotFoundError(key, sources)

    def list_available_secrets(self) -> List[str]:
        """
        List all secret keys that can be retrieved.

        Checks all configured sources and returns a deduplicated
        list of available secret keys.

        Returns:
            List of secret key names
        """
        keys_set = set()

        # Check file source
        try:
            file_secrets = self._load_config()
            keys_set.update(file_secrets.keys())
        except Exception:
            pass

        # Check keyring source
        if self.use_keyring and self._keyring:
            try:
                # Try to list all passwords for "skill-split" service
                # Note: keyring doesn't have a standard list method,
                # so we'll just check for known keys
                for key in ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]:
                    if self._keyring.get_password("skill-split", key):
                        keys_set.add(key)
            except Exception:
                pass

        # Check environment source
        # Add common API key environment variables
        for key in os.environ:
            if "API_KEY" in key or "TOKEN" in key or "SECRET" in key:
                keys_set.add(key)

        return sorted(list(keys_set))
