# Component Handler Architecture for skill-split

**Date**: 2026-02-04
**Status**: DESIGN DOCUMENT (Not Implemented)
**Task**: #12 - Design extensible component handler architecture

## Executive Summary

This document outlines the design for extending skill-split to handle **ALL Claude Code file types** beyond the current markdown/YAML support. The architecture introduces a new **Component Handler System** that wraps existing Parser, DatabaseStore, and QueryAPI functionality while adding type-specific handlers for non-markdown formats.

## Design Constraints

**CRITICAL**: This design must NOT modify existing skill-split code. All new functionality will be implemented as separate modules that extend the existing system.

### Existing Components (Preserved As-Is)

```
core/
  ├── parser.py         # YAML/markdown/XML parser - NO CHANGES
  ├── database.py       # SQLite storage - NO CHANGES
  ├── query.py          # QueryAPI - NO CHANGES
  ├── recomposer.py     # Round-trip verification - NO CHANGES
  ├── detector.py       # Format detection - NO CHANGES
  ├── hashing.py        # SHA256 verification - NO CHANGES
  ├── validator.py      # Validation - NO CHANGES
  ├── supabase_store.py # Remote storage - NO CHANGES
  └── checkout_manager.py # File deployment - NO CHANGES

models.py               # Data classes - MINIMAL EXTENSIONS ONLY
skill_split.py          # CLI - NEW COMMANDS ONLY
```

## Target File Types

| Type | File Patterns | Format | Current Support | New Handler |
|------|---------------|--------|-----------------|-------------|
| SKILL | `*/SKILL.md` | Markdown + YAML | ✅ Already works | N/A |
| COMMAND | `commands/*/*.md` | Markdown + YAML | ✅ Already works | N/A |
| AGENT | `agents/*/*.md` | Markdown + optional YAML | ✅ Already works | N/A |
| PLUGIN | `plugin.json` + `.mcp.json` + `hooks.json` | JSON | ❌ Not supported | `PluginHandler` |
| HOOK | `hooks.json` + shell scripts | JSON + Shell | ❌ Not supported | `HookHandler` |
| OUTPUT-STYLE | `output-styles/*.md` | Markdown + YAML | ✅ Already works | N/A |
| CONFIG | `settings.json`, `mcp_config.json` | JSON | ❌ Not supported | `ConfigHandler` |
| DOCUMENTATION | `README.md`, `CLAUDE.md`, `reference/*.md` | Markdown | ✅ Already works | N/A |

## Architecture Overview

### New Module Structure

```
skill-split/
├── core/                    # Existing modules - NO CHANGES
├── handlers/                # NEW: Component handlers
│   ├── __init__.py
│   ├── base.py              # Base handler interface
│   ├── component_detector.py # File type detection
│   ├── plugin_handler.py    # Plugin files (JSON)
│   ├── hook_handler.py      # Hook files (JSON + shell)
│   ├── config_handler.py    # Config files (JSON)
│   └── factory.py           # Handler factory
├── models.py                # EXTEND: New file types
├── skill_split.py           # EXTEND: New CLI commands
└── ARCHITECTURE.md          # This document
```

### Component Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                          │
│                      (skill_split.py)                            │
│                                                                   │
│  Existing Commands:                                              │
│  • parse, validate, store, get, tree, verify                    │
│  • get-section, next, list, search                              │
│  • ingest, checkout, checkin, list-library, status, search-lib  │
│                                                                   │
│  New Commands:                                                   │
│  • store-component, get-component, list-components              │
│  • search-components, verify-component                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ComponentDetector (NEW)                      │
│                                                                   │
│  • Detect file type by path pattern + content                   │
│  • Return appropriate handler instance                          │
│  • Fallback to existing Parser for markdown files               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                           ↓
┌──────────────────────┐                  ┌──────────────────────┐
│   BaseHandler (NEW)  │                  │   Existing Parser    │
│                      │                  │   (markdown files)    │
│  Methods:            │                  │                      │
│  • parse()           │                  │  • parse_headings()  │
│  • validate()        │                  │  • parse_xml_tags()  │
│  • get_sections()    │                  └──────────────────────┘
│  • recompose()       │
└──────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Type-Specific Handlers                        │
│                                                                   │
│  PluginHandler    → Parse plugin.json, .mcp.json, hooks.json   │
│  HookHandler      → Parse hooks.json + associated shell scripts │
│  ConfigHandler    → Parse settings.json, mcp_config.json        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Extended DatabaseStore (NO CODE CHANGES)           │
│                                                                   │
│  • Files table: Already supports any file path                  │
│  • Sections table: Already stores arbitrary section content     │
│  • Works with new handlers via ParsedDocument                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Extended QueryAPI (NO CODE CHANGES)                │
│                                                                   │
│  • get_section() → Works for any component type                 │
│  • search_sections() → Cross-component search                   │
│  • get_section_tree() → Component hierarchy                     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Model Extensions

### Extended FileType Enum

```python
# In models.py - EXTEND existing enum

class FileType(Enum):
    """Type of file based on its location/purpose."""

    # Existing types (PRESERVED)
    SKILL = "skill"           # /skills/*/SKILL.md
    COMMAND = "command"       # /commands/*/*.md
    REFERENCE = "reference"   # /get-shit-done/references/*.md

    # NEW types
    AGENT = "agent"           # /agents/*/*.md
    PLUGIN = "plugin"         # plugin.json + .mcp.json + hooks.json
    HOOK = "hook"             # hooks.json + shell scripts
    OUTPUT_STYLE = "output_style"  # /output-styles/*.md
    CONFIG = "config"         # settings.json, mcp_config.json
    DOCUMENTATION = "documentation"  # README.md, CLAUDE.md, reference/*.md
```

### Extended FileFormat Enum

```python
# In models.py - EXTEND existing enum

class FileFormat(Enum):
    """Detected file structure type."""

    # Existing formats (PRESERVED)
    MARKDOWN_HEADINGS = "markdown_headings"
    XML_TAGS = "xml_tags"
    MIXED = "mixed"
    UNKNOWN = "unknown"

    # NEW formats
    JSON = "json"             # JSON files (config, plugins, hooks)
    JSON_SCHEMA = "json_schema"  # JSON with known schema
    SHELL_SCRIPT = "shell"    # Shell scripts
    MULTI_FILE = "multi_file"  # Component spanning multiple files
```

### New ComponentMetadata Model

```python
# In models.py - NEW model

@dataclass
class ComponentMetadata:
    """
    Metadata for non-markdown components.

    For multi-file components (plugins, hooks), tracks
    related files and their relationships.
    """
    component_type: FileType
    primary_file: str           # Main file path
    related_files: List[str]    # Associated file paths
    schema_version: str         # For validation
    dependencies: List[str]     # Other components this depends on

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "component_type": self.component_type.value,
            "primary_file": self.primary_file,
            "related_files": self.related_files,
            "schema_version": self.schema_version,
            "dependencies": self.dependencies,
        }
```

## Handler API Design

### BaseHandler Interface

```python
# handlers/base.py

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from pathlib import Path

from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class BaseHandler(ABC):
    """
    Abstract base class for component handlers.

    All type-specific handlers must implement this interface.
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize handler with file path.

        Args:
            file_path: Path to the primary file for this component
        """
        self.file_path = file_path
        self.content = self._read_content()

    def _read_content(self) -> str:
        """Read file content from disk."""
        with open(self.file_path, 'r') as f:
            return f.read()

    @abstractmethod
    def parse(self) -> ParsedDocument:
        """
        Parse the component into structured sections.

        Returns:
            ParsedDocument with component-specific structure

        Must create sections that make sense for progressive disclosure:
        - For JSON: Top-level keys become sections
        - For plugins: Each config section becomes a section
        - For hooks: Each hook definition becomes a section
        """
        pass

    @abstractmethod
    def validate(self) -> ValidationResult:
        """
        Validate component structure and schema.

        Returns:
            ValidationResult with errors/warnings

        Should check:
        - Required fields present
        - Correct data types
        - Valid schema version
        - Referenced files exist
        """
        pass

    @abstractmethod
    def get_related_files(self) -> List[str]:
        """
        Get list of related files for multi-file components.

        Returns:
            List of file paths (relative or absolute)

        For single-file components: Return empty list
        For multi-file components: Return paths to all related files
        """
        pass

    def recompute_hash(self) -> str:
        """
        Compute hash for component verification.

        For multi-file components, hash includes all related files.

        Returns:
            SHA256 hash string
        """
        from core.hashing import compute_file_hash

        if not self.get_related_files():
            return compute_file_hash(self.file_path)

        # Multi-file: combine hashes
        import hashlib
        combined = hashlib.sha256()
        combined.update(compute_file_hash(self.file_path).encode())

        for related in self.get_related_files():
            combined.update(compute_file_hash(related).encode())

        return combined.hexdigest()

    def recompose(self, sections: List[Section]) -> str:
        """
        Reconstruct component from sections.

        Args:
            sections: List of sections from database

        Returns:
            Complete component content as string

        Default implementation joins section content.
        Override for custom recomposition logic.
        """
        return "\n".join(s.content for s in sections)
```

### ComponentDetector

```python
# handlers/component_detector.py

import re
from pathlib import Path
from typing import Tuple, Optional

from models import FileType, FileFormat
from handlers.base import BaseHandler
from handlers.plugin_handler import PluginHandler
from handlers.hook_handler import HookHandler
from handlers.config_handler import ConfigHandler


class ComponentDetector:
    """
    Detects component type and returns appropriate handler.

    Detection strategy:
    1. Path-based: Use file location patterns
    2. Extension-based: Use file extension
    3. Content-based: Analyze file structure
    """

    # Path patterns for component detection
    PATTERNS = {
        FileType.SKILL: re.compile(r"(/skills/[^/]+/SKILL\.md|SKILL\.md$)"),
        FileType.COMMAND: re.compile(r"/commands/[^/]+/[^/]+\.md$"),
        FileType.AGENT: re.compile(r"/agents/[^/]+/[^/]+\.md$"),
        FileType.PLUGIN: re.compile(r"plugin\.json$"),
        FileType.HOOK: re.compile(r"hooks\.json$"),
        FileType.OUTPUT_STYLE: re.compile(r"/output-styles/[^/]+\.md$"),
        FileType.CONFIG: re.compile(r"(settings\.json|mcp_config\.json)$"),
        FileType.DOCUMENTATION: re.compile(r"(README\.md|CLAUDE\.md|/references/[^/]+\.md)$"),
        FileType.REFERENCE: re.compile(r"/get-shit-done/references/[^/]+\.md|/references/[^/]+\.md$"),
    }

    @classmethod
    def detect(cls, file_path: str) -> Tuple[FileType, FileFormat]:
        """
        Detect component type and format from file path.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (FileType, FileFormat)
        """
        path = Path(file_path)
        normalized_path = str(path).replace("\\", "/")

        # Check patterns
        for file_type, pattern in cls.PATTERNS.items():
            if pattern.search(normalized_path):
                file_format = cls._detect_format(path)
                return file_type, file_format

        # Fallback: check extension
        if path.suffix == ".json":
            return FileType.CONFIG, FileFormat.JSON

        if path.suffix == ".md":
            return FileType.DOCUMENTATION, FileFormat.MARKDOWN_HEADINGS

        # Default
        return FileType.REFERENCE, FileFormat.UNKNOWN

    @classmethod
    def _detect_format(cls, path: Path) -> FileFormat:
        """Detect format from file extension and content."""
        if path.suffix == ".json":
            return FileFormat.JSON

        if path.suffix == ".sh":
            return FileFormat.SHELL_SCRIPT

        if path.suffix == ".md":
            # Will use existing FormatDetector for markdown
            return FileFormat.MARKDOWN_HEADINGS

        return FileFormat.UNKNOWN

    @classmethod
    def get_handler(cls, file_path: str) -> BaseHandler:
        """
        Get appropriate handler for file.

        Args:
            file_path: Path to the file

        Returns:
            Handler instance

        Raises:
            ValueError: If no handler available for file type
        """
        file_type, _ = cls.detect(file_path)

        handler_map = {
            FileType.PLUGIN: PluginHandler,
            FileType.HOOK: HookHandler,
            FileType.CONFIG: ConfigHandler,
        }

        handler_class = handler_map.get(file_type)

        if handler_class:
            return handler_class(file_path)

        # For markdown files, use existing Parser
        # Return None to indicate use of existing system
        return None
```

## Type-Specific Handlers

### PluginHandler

```python
# handlers/plugin_handler.py

import json
from typing import List

from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class PluginHandler(BaseHandler):
    """
    Handler for plugin components.

    A plugin consists of:
    - plugin.json: Main plugin metadata
    - .mcp.json: MCP server configuration (optional)
    - hooks.json: Hook definitions (optional)
    """

    def parse(self) -> ParsedDocument:
        """
        Parse plugin.json and related files into sections.

        Sections:
        - metadata: Plugin name, version, description
        - mcp_config: MCP server configuration (if exists)
        - hooks: Hook definitions (if exists)
        - permissions: Required permissions
        """
        plugin_data = json.loads(self.content)

        sections = []

        # Metadata section
        sections.append(Section(
            level=1,
            title="metadata",
            content=self._format_metadata(plugin_data),
            line_start=1,
            line_end=self.content.count('\n') + 1,
        ))

        # Check for MCP config
        mcp_file = self._find_mcp_config()
        if mcp_file:
            with open(mcp_file) as f:
                mcp_data = json.load(f)
            sections.append(Section(
                level=1,
                title="mcp_config",
                content=json.dumps(mcp_data, indent=2),
                line_start=1,
                line_end=0,  # Not applicable for multi-file
            ))

        # Check for hooks
        hooks_file = self._find_hooks_config()
        if hooks_file:
            with open(hooks_file) as f:
                hooks_data = json.load(f)
            sections.append(Section(
                level=1,
                title="hooks",
                content=json.dumps(hooks_data, indent=2),
                line_start=1,
                line_end=0,
            ))

        return ParsedDocument(
            frontmatter=json.dumps({"type": "plugin"}, indent=2),
            sections=sections,
            file_type=FileType.PLUGIN,
            format=FileFormat.MULTI_FILE,
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        """Validate plugin structure."""
        result = ValidationResult(is_valid=True)

        try:
            plugin_data = json.loads(self.content)

            # Required fields
            required = ["name", "version", "description"]
            for field in required:
                if field not in plugin_data:
                    result.add_error(f"Missing required field: {field}")

            # Check MCP config if referenced
            if "mcpServers" in plugin_data:
                mcp_file = self._find_mcp_config()
                if not mcp_file:
                    result.add_warning("MCP servers referenced but no .mcp.json found")

            # Check hooks if referenced
            if "hooks" in plugin_data:
                hooks_file = self._find_hooks_config()
                if not hooks_file:
                    result.add_warning("Hooks referenced but no hooks.json found")

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")

        return result

    def get_related_files(self) -> List[str]:
        """Get list of related plugin files."""
        related = []
        plugin_dir = Path(self.file_path).parent

        # Find .mcp.json
        mcp_file = self._find_mcp_config()
        if mcp_file:
            related.append(mcp_file)

        # Find hooks.json
        hooks_file = self._find_hooks_config()
        if hooks_file:
            related.append(hooks_file)

        return related

    def _find_mcp_config(self) -> str:
        """Find .mcp.json file in plugin directory."""
        plugin_dir = Path(self.file_path).parent
        mcp_file = plugin_dir / f"{plugin_dir.name}.mcp.json"
        return str(mcp_file) if mcp_file.exists() else None

    def _find_hooks_config(self) -> str:
        """Find hooks.json file in plugin directory."""
        plugin_dir = Path(self.file_path).parent
        hooks_file = plugin_dir / "hooks.json"
        return str(hooks_file) if hooks_file.exists() else None

    def _format_metadata(self, plugin_data: dict) -> str:
        """Format plugin metadata as markdown."""
        lines = [
            f"# {plugin_data.get('name', 'Unknown Plugin')}",
            "",
            f"**Version**: {plugin_data.get('version', 'unknown')}",
            f"**Description**: {plugin_data.get('description', 'No description')}",
            "",
        ]

        if "author" in plugin_data:
            lines.append(f"**Author**: {plugin_data['author']}")

        if "permissions" in plugin_data:
            lines.append("")
            lines.append("## Permissions")
            for perm in plugin_data["permissions"]:
                lines.append(f"- {perm}")

        return "\n".join(lines)
```

### HookHandler

```python
# handlers/hook_handler.py

import json
from pathlib import Path
from typing import List

from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class HookHandler(BaseHandler):
    """
    Handler for hook components.

    A hook consists of:
    - hooks.json: Hook definitions
    - Associated shell scripts: One per hook
    """

    def parse(self) -> ParsedDocument:
        """
        Parse hooks.json and associated scripts into sections.

        Each hook becomes a section with its script content.
        """
        hooks_data = json.loads(self.content)
        sections = []

        for hook_name, hook_config in hooks_data.items():
            hook_dir = Path(self.file_path).parent

            # Find script file
            script_file = hook_dir / f"{hook_name}.sh"
            script_content = ""

            if script_file.exists():
                with open(script_file) as f:
                    script_content = f.read()

            # Create section for this hook
            sections.append(Section(
                level=1,
                title=hook_name,
                content=self._format_hook(hook_name, hook_config, script_content),
                line_start=1,
                line_end=script_content.count('\n') + 1 if script_content else 1,
            ))

        return ParsedDocument(
            frontmatter=json.dumps({"type": "hooks"}, indent=2),
            sections=sections,
            file_type=FileType.HOOK,
            format=FileFormat.MULTI_FILE,
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        """Validate hook structure."""
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
                    result.add_error(f"Invalid config for hook: {hook_name}")

                if "description" not in hook_config:
                    result.add_warning(f"No description for hook: {hook_name}")

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")

        return result

    def get_related_files(self) -> List[str]:
        """Get list of hook script files."""
        related = []
        hook_dir = Path(self.file_path).parent

        try:
            hooks_data = json.loads(self.content)
            for hook_name in hooks_data.keys():
                script_file = hook_dir / f"{hook_name}.sh"
                if script_file.exists():
                    related.append(str(script_file))
        except json.JSONDecodeError:
            pass

        return related

    def _format_hook(self, name: str, config: dict, script: str) -> str:
        """Format hook as markdown with script."""
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

        if script:
            lines.append("## Script")
            lines.append("")
            lines.append("```bash")
            lines.append(script)
            lines.append("```")

        return "\n".join(lines)
```

### ConfigHandler

```python
# handlers/config_handler.py

import json
from typing import List

from handlers.base import BaseHandler
from models import ParsedDocument, Section, FileType, FileFormat, ValidationResult


class ConfigHandler(BaseHandler):
    """
    Handler for configuration files.

    Handles:
    - settings.json: Claude Code settings
    - mcp_config.json: MCP server configuration
    """

    def parse(self) -> ParsedDocument:
        """
        Parse config file into sections.

        Each top-level key becomes a section.
        """
        config_data = json.loads(self.content)
        sections = []

        for key, value in config_data.items():
            sections.append(Section(
                level=1,
                title=key,
                content=self._format_config_item(key, value),
                line_start=1,
                line_end=self.content.count('\n') + 1,
            ))

        return ParsedDocument(
            frontmatter=json.dumps({
                "type": "config",
                "file_type": Path(self.file_path).name
            }, indent=2),
            sections=sections,
            file_type=FileType.CONFIG,
            format=FileFormat.JSON,
            original_path=self.file_path,
        )

    def validate(self) -> ValidationResult:
        """Validate config structure."""
        result = ValidationResult(is_valid=True)

        try:
            config_data = json.loads(self.content)

            # Check for known config schemas
            filename = Path(self.file_path).name

            if filename == "settings.json":
                self._validate_settings(config_data, result)
            elif filename == "mcp_config.json":
                self._validate_mcp_config(config_data, result)

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")

        return result

    def get_related_files(self) -> List[str]:
        """Config files are standalone."""
        return []

    def _validate_settings(self, data: dict, result: ValidationResult) -> None:
        """Validate settings.json structure."""
        # Known settings keys
        known_keys = {
            "permissions", "plugins", "mcpServers",
            "voiceCommands", "context", "modes"
        }

        for key in data.keys():
            if key not in known_keys:
                result.add_warning(f"Unknown settings key: {key}")

    def _validate_mcp_config(self, data: dict, result: ValidationResult) -> None:
        """Validate MCP server configuration."""
        if not isinstance(data, dict):
            result.add_error("MCP config must be a dictionary")

        for server_name, server_config in data.items():
            if not isinstance(server_config, dict):
                result.add_error(f"Invalid config for server: {server_name}")

            if "command" not in server_config and "url" not in server_config:
                result.add_error(f"Server {server_name} missing command or url")

    def _format_config_item(self, key: str, value) -> str:
        """Format config item as markdown."""
        if isinstance(value, dict):
            return json.dumps(value, indent=2)
        elif isinstance(value, list):
            return "\n".join(f"- {item}" for item in value)
        else:
            return str(value)
```

## CLI Extensions

### New Commands

```python
# In skill_split.py - ADD to existing CLI

def cmd_store_component(args) -> int:
    """Store any component type in database."""
    file_path = args.file
    db_path = args.db or get_default_db_path()

    # Detect component type
    detector = ComponentDetector()
    file_type, file_format = detector.detect(file_path)

    # Get appropriate handler
    handler = detector.get_handler(file_path)

    if handler is None:
        # Use existing Parser for markdown files
        from core.parser import Parser
        parser = Parser()
        with open(file_path) as f:
            content = f.read()
        doc = parser.parse(file_path, content, file_type, file_format)
    else:
        # Use component handler
        doc = handler.parse()

    # Compute hash
    content_hash = handler.recompute_hash() if handler else compute_file_hash(file_path)

    # Store in database
    store = DatabaseStore(db_path)
    file_id = store.store_file(file_path, doc, content_hash)

    print(f"Stored: {file_path}")
    print(f"Type: {file_type.value}")
    print(f"Format: {file_format.value}")
    print(f"File ID: {file_id}")

    return 0


def cmd_list_components(args) -> int:
    """List all components by type."""
    db_path = args.db or get_default_db_path()
    component_type = args.type

    store = DatabaseStore(db_path)

    # Query files by type
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        if component_type:
            cursor = conn.execute(
                "SELECT * FROM files WHERE type = ?",
                (component_type,)
            )
        else:
            cursor = conn.execute("SELECT * FROM files")

        files = cursor.fetchall()

    # Display results
    print(f"{'ID':<6} {'Type':<15} {'Path':<50}")
    print("-" * 71)

    for file in files:
        print(f"{file['id']:<6} {file['type']:<15} {file['path']:<50}")

    return 0


def cmd_search_components(args) -> int:
    """Search across all component types."""
    query = args.query
    db_path = args.db or get_default_db_path()

    query_api = QueryAPI(db_path)
    results = query_api.search_sections(query)

    # Display results
    print(f"Found {len(results)} section(s) matching '{query}':")
    print()
    print(f"{'ID':<6} {'Title':<40} {'Level':<6}")
    print("-" * 52)

    for section_id, section in results:
        title = section.title[:37] + "..." if len(section.title) > 40 else section.title
        print(f"{section_id:<6} {title:<40} {section.level:<6}")

    return 0


def cmd_verify_component(args) -> int:
    """Verify component round-trip integrity."""
    file_path = args.file
    db_path = args.db or get_default_db_path()

    # Get handler
    detector = ComponentDetector()
    handler = detector.get_handler(file_path)

    if handler is None:
        # Use existing verification for markdown
        return cmd_verify(args)

    # Parse and store
    doc = handler.parse()
    content_hash = handler.recompute_hash()

    store = DatabaseStore(db_path)
    file_id = store.store_file(file_path, doc, content_hash)

    # Recompose and verify
    recomposer = Recomposer(store)
    recomposed = recomposer.recompose(file_path)

    from core.hashing import compute_content_hash
    recomposed_hash = compute_content_hash(recomposed)

    # Display results
    print(f"File: {file_path}")
    print(f"Original hash:    {content_hash}")
    print(f"Recomposed hash:  {recomposed_hash}")
    print()

    if content_hash == recomposed_hash:
        print("✓ Round-trip successful")
        return 0
    else:
        print("✗ Round-trip failed")
        return 1
```

### Argument Parser Additions

```python
# In main() function - ADD to existing subparsers

# Store-component command
store_component_parser = subparsers.add_parser(
    "store-component", help="Store any component type in database"
)
store_component_parser.add_argument("file", help="Path to component file")
store_component_parser.add_argument(
    "--db", default=get_default_db_path(), help="Path to database"
)
store_component_parser.set_defaults(func=cmd_store_component)

# List-components command
list_components_parser = subparsers.add_parser(
    "list-components", help="List all components by type"
)
list_components_parser.add_argument(
    "--type", help="Filter by component type (optional)"
)
list_components_parser.add_argument(
    "--db", default=get_default_db_path(), help="Path to database"
)
list_components_parser.set_defaults(func=cmd_list_components)

# Search-components command
search_components_parser = subparsers.add_parser(
    "search-components", help="Search across all component types"
)
search_components_parser.add_argument("query", help="Search query")
search_components_parser.add_argument(
    "--db", default=get_default_db_path(), help="Path to database"
)
search_components_parser.set_defaults(func=cmd_search_components)

# Verify-component command
verify_component_parser = subparsers.add_parser(
    "verify-component", help="Verify component round-trip integrity"
)
verify_component_parser.add_argument("file", help="Path to component file")
verify_component_parser.add_argument(
    "--db", default=get_default_db_path(), help="Path to database"
)
verify_component_parser.set_defaults(func=cmd_verify_component)
```

## Database Schema

### No Schema Changes Required

The existing database schema supports all component types without modification:

```sql
-- Files table (unchanged)
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,          -- Will store new FileType values
    frontmatter TEXT,            -- JSON metadata for components
    hash TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Sections table (unchanged)
CREATE TABLE sections (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    parent_id INTEGER,
    level INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,       -- Component section content
    order_index INTEGER NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES sections(id) ON DELETE CASCADE
);
```

### Section Storage by Component Type

| Component Type | Section Structure | Content Format |
|----------------|-------------------|----------------|
| PLUGIN | metadata, mcp_config, hooks | JSON or markdown |
| HOOK | One section per hook name | Markdown with script |
| CONFIG | One section per top-level key | JSON or formatted text |
| SKILL/COMMAND/AGENT | Heading hierarchy (existing) | Markdown |

## Progressive Disclosure Strategy

### Section Granularity by Type

```
PLUGIN (3 sections):
├── [1] metadata         → Plugin name, version, description
├── [2] mcp_config       → MCP server configuration (if exists)
└── [3] hooks            → Hook definitions (if exists)

HOOK (N sections):
├── [1] hook_name_1      → Hook config + script
├── [2] hook_name_2      → Hook config + script
└── ...

CONFIG (N sections):
├── [1] permissions      → Permission settings
├── [2] plugins          → Plugin configuration
├── [3] mcpServers       → MCP server settings
└── ...

SKILL (existing):
├── [1] Overview         → Level 1 heading
├── [2] Installation     → Level 1 heading
│   ├── [3] Prerequisites → Level 2 subsection
│   └── [4] Setup         → Level 2 subsection
└── ...
```

### QueryAPI Integration

All existing QueryAPI methods work with new component types:

```python
# Get single section (works for any component type)
section = query_api.get_section(section_id)

# Progressive disclosure (works for any component type)
next_section = query_api.get_next_section(current_id, file_path)

# Full hierarchy (works for any component type)
tree = query_api.get_section_tree(file_path)

# Cross-component search
results = query_api.search_sections("authentication", file_path=None)
```

## Integration with Existing System

### Backward Compatibility

- ✅ All existing commands work unchanged
- ✅ All existing tests pass without modification
- ✅ Database schema unchanged
- ✅ Parser, DatabaseStore, QueryAPI unchanged
- ✅ New commands are additive only

### Handler Selection Flow

```python
# In CLI commands

def process_file(file_path: str):
    detector = ComponentDetector()
    file_type, file_format = detector.detect(file_path)

    handler = detector.get_handler(file_path)

    if handler is None:
        # Use existing Parser for markdown files
        parser = Parser()
        doc = parser.parse(file_path, content, file_type, file_format)
    else:
        # Use new component handler
        doc = handler.parse()

    # Store using existing DatabaseStore
    store.store_file(file_path, doc, content_hash)
```

### Supabase Integration

The new handlers work with existing SupabaseStore:

```python
# Store component in Supabase
handler = PluginHandler("plugin.json")
doc = handler.parse()
content_hash = handler.recompute_hash()

supabase_store.store_file(
    storage_path=file_path,
    name="my-plugin",
    doc=doc,
    content_hash=content_hash
)
```

## Test Strategy

### Test Structure

```
test/
├── test_handlers/           # NEW: Handler tests
│   ├── test_plugin_handler.py
│   ├── test_hook_handler.py
│   ├── test_config_handler.py
│   ├── test_component_detector.py
│   └── fixtures/
│       ├── test_plugin.json
│       ├── test_hooks.json
│       └── test_settings.json
├── test_parser.py           # EXISTING: No changes
├── test_database.py         # EXISTING: No changes
└── test_cli.py              # EXISTING: No changes
```

### Test Cases

#### PluginHandler Tests

```python
def test_plugin_parse():
    """Test plugin.json parsing."""
    handler = PluginHandler("test/fixtures/test_plugin.json")
    doc = handler.parse()

    assert doc.file_type == FileType.PLUGIN
    assert len(doc.sections) >= 1
    assert doc.sections[0].title == "metadata"

def test_plugin_validation():
    """Test plugin validation."""
    handler = PluginHandler("test/fixtures/test_plugin.json")
    result = handler.validate()

    assert result.is_valid
    assert len(result.errors) == 0

def test_plugin_related_files():
    """Test related file detection."""
    handler = PluginHandler("test/fixtures/test_plugin.json")
    related = handler.get_related_files()

    assert isinstance(related, list)
    # Should find .mcp.json and hooks.json if they exist
```

#### HookHandler Tests

```python
def test_hook_parse():
    """Test hooks.json parsing."""
    handler = HookHandler("test/fixtures/test_hooks.json")
    doc = handler.parse()

    assert doc.file_type == FileType.HOOK
    # Each hook becomes a section
    assert len(doc.sections) > 0

def test_hook_script_inclusion():
    """Test that hook scripts are included."""
    handler = HookHandler("test/fixtures/test_hooks.json")
    doc = handler.parse()

    # Sections should contain script content
    for section in doc.sections:
        assert "```bash" in section.content or section.content == ""
```

#### ConfigHandler Tests

```python
def test_config_parse():
    """Test settings.json parsing."""
    handler = ConfigHandler("test/fixtures/test_settings.json")
    doc = handler.parse()

    assert doc.file_type == FileType.CONFIG
    # Each top-level key becomes a section
    assert len(doc.sections) > 0

def test_config_validation():
    """Test config validation."""
    handler = ConfigHandler("test/fixtures/test_settings.json")
    result = handler.validate()

    # Should validate known settings keys
    assert result.is_valid or len(result.warnings) >= 0
```

#### ComponentDetector Tests

```python
def test_detect_plugin():
    """Test plugin detection."""
    file_type, file_format = ComponentDetector.detect("plugin.json")
    assert file_type == FileType.PLUGIN
    assert file_format == FileFormat.JSON

def test_detect_hook():
    """Test hook detection."""
    file_type, file_format = ComponentDetector.detect("hooks.json")
    assert file_type == FileType.HOOK
    assert file_format == FileFormat.JSON

def test_detect_config():
    """Test config detection."""
    file_type, file_format = ComponentDetector.detect("settings.json")
    assert file_type == FileType.CONFIG
    assert file_format == FileFormat.JSON

def test_get_handler_returns_none_for_markdown():
    """Test that markdown files return None handler."""
    handler = ComponentDetector.get_handler("README.md")
    assert handler is None  # Use existing Parser
```

#### Integration Tests

```python
def test_store_and_retrieve_component():
    """Test full round-trip for component."""
    handler = PluginHandler("test/fixtures/test_plugin.json")
    doc = handler.parse()

    store = DatabaseStore(":memory:")
    file_id = store.store_file("test_plugin.json", doc, "test_hash")

    # Retrieve
    metadata, sections = store.get_file("test_plugin.json")

    assert metadata.type == FileType.PLUGIN
    assert len(sections) == len(doc.sections)

def test_cross_component_search():
    """Test searching across component types."""
    # Store multiple component types
    # Search for common term
    # Verify results from all types
    pass
```

### Test Fixtures

```
test/fixtures/
├── test_plugin.json
│   └── content: {"name": "test-plugin", "version": "1.0.0", ...}
├── test_plugin.mcp.json
│   └── content: {"mcpServers": {...}}
├── test_hooks.json
│   └── content: {"hook1": {...}, "hook2": {...}}
├── hook1.sh
├── hook2.sh
├── test_settings.json
│   └── content: {"permissions": [...], "plugins": [...]}
└── test_mcp_config.json
    └── content: {"server1": {...}, "server2": {...}}
```

## Implementation Phases

### Phase 1: Foundation (Priority: HIGH)
1. Create `handlers/` directory structure
2. Implement `BaseHandler` interface
3. Implement `ComponentDetector`
4. Extend `FileType` and `FileFormat` enums
5. Add `ComponentMetadata` model

### Phase 2: Handlers (Priority: HIGH)
1. Implement `PluginHandler`
2. Implement `HookHandler`
3. Implement `ConfigHandler`
4. Write unit tests for each handler

### Phase 3: CLI Integration (Priority: MEDIUM)
1. Add `store-component` command
2. Add `list-components` command
3. Add `search-components` command
4. Add `verify-component` command

### Phase 4: Integration Testing (Priority: MEDIUM)
1. Test with real Claude Code plugins
2. Test with real hooks files
3. Test with real config files
4. Verify Supabase integration

### Phase 5: Documentation (Priority: LOW)
1. Update README.md with new commands
2. Create handler development guide
3. Document component type detection
4. Add usage examples

## Design Decisions

### Why Handler Architecture?

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Extend Parser | Single interface | Parser becomes complex | ❌ Rejected |
| Handler per type | Clean separation | More files | ✅ **ACCEPTED** |
| Metadata-driven | Flexible | Harder to validate | ❌ Rejected |

### Why No Database Schema Changes?

The existing schema is sufficiently generic:
- `files.type` can store any FileType value
- `files.frontmatter` can store JSON metadata
- `sections.content` can store any section content
- No migration required for existing users

### Why Separate CLI Commands?

New commands (`store-component`, etc.) vs. extending existing commands:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Extend existing | Fewer commands | Confusing behavior | ❌ Rejected |
| Separate commands | Clear intent | More commands | ✅ **ACCEPTED** |

### Why BaseHandler Returns ParsedDocument?

Ensures compatibility with existing DatabaseStore:
```python
store.store_file(file_path, doc, hash)  # Works for all types
```

## Open Questions

1. **Multi-file hash computation**: Should we hash related files separately or combined?
   - **Decision**: Combined hash for simplicity

2. **Section content format**: Should sections store JSON or formatted markdown?
   - **Decision**: Handler-specific (markdown for display, JSON for config)

3. **Shell script parsing**: Should we parse shell scripts into functions?
   - **Decision**: Not in Phase 1 - store as whole content

4. **MCP server detection**: How to detect which servers a plugin uses?
   - **Decision**: Parse from .mcp.json if exists

5. **Component dependencies**: How to track dependencies between components?
   - **Decision**: Add to ComponentMetadata in Phase 2

## Future Enhancements

### Phase 2+ Features

1. **Dependency tracking**: Track which components depend on others
2. **Version management**: Track component versions and updates
3. **Validation schemas**: JSON schema validation for configs
4. **Shell script parsing**: Parse shell scripts into functions
5. **Component composition**: Assemble plugins from reusable parts
6. **Type-specific search**: Search by component type, metadata
7. **Component relationships**: Visualize component dependencies

### Potential New Handlers

1. **AgentHandler**: For agent definition files
2. **OutputStyleHandler**: For output-style definitions
3. **TemplateHandler**: For template files
4. **WorkflowHandler**: For workflow definitions

## Success Criteria

### Functional Requirements
- ✅ All 8 component types can be stored and retrieved
- ✅ Progressive disclosure works for all types
- ✅ Round-trip verification passes for all types
- ✅ Cross-component search returns relevant results
- ✅ Existing functionality unchanged

### Non-Functional Requirements
- ✅ No breaking changes to existing API
- ✅ All existing tests pass
- ✅ New test coverage > 80%
- ✅ CLI documentation complete
- ✅ Performance comparable to existing system

### User Experience
- ✅ Intuitive command names
- ✅ Clear error messages
- ✅ Helpful progress indicators
- ✅ Consistent output format

## Appendix

### File Type Detection Matrix

| Path Pattern | Type | Format | Handler |
|--------------|------|--------|---------|
| `*/SKILL.md` | SKILL | MARKDOWN_HEADINGS | Parser (existing) |
| `*/commands/*/*.md` | COMMAND | MARKDOWN_HEADINGS | Parser (existing) |
| `*/agents/*/*.md` | AGENT | MARKDOWN_HEADINGS | Parser (existing) |
| `plugin.json` | PLUGIN | MULTI_FILE | PluginHandler |
| `hooks.json` | HOOK | MULTI_FILE | HookHandler |
| `settings.json` | CONFIG | JSON | ConfigHandler |
| `mcp_config.json` | CONFIG | JSON | ConfigHandler |
| `*/output-styles/*.md` | OUTPUT_STYLE | MARKDOWN_HEADINGS | Parser (existing) |
| `README.md` | DOCUMENTATION | MARKDOWN_HEADINGS | Parser (existing) |
| `CLAUDE.md` | DOCUMENTATION | MARKDOWN_HEADINGS | Parser (existing) |
| `*/references/*.md` | REFERENCE | MARKDOWN_HEADINGS | Parser (existing) |

### Section Creation Examples

#### Plugin Section Creation
```python
# Input: plugin.json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Does something cool",
  "mcpServers": {"server1": {...}}
}

# Output Sections:
[0] title="metadata", content="# my-plugin\n\n**Version**: 1.0.0\n..."
[1] title="mcp_config", content='{"server1": {...}}'
```

#### Hook Section Creation
```python
# Input: hooks.json
{
  "pre-commit": {
    "description": "Runs before commit",
    "script": "pre-commit.sh"
  }
}

# Output Sections:
[0] title="pre-commit", content="# pre-commit\n\n## Script\n\n```bash\n#!/bin/bash\n..."
```

#### Config Section Creation
```python
# Input: settings.json
{
  "permissions": {
    "allowNetwork": true
  },
  "plugins": {
    "enabled": ["plugin1", "plugin2"]
  }
}

# Output Sections:
[0] title="permissions", content='{"allowNetwork": true}'
[1] title="plugins", content="- plugin1\n- plugin2"
```

---

**Document Status**: Ready for review
**Next Steps**: Implement Phase 1 (Foundation)
**Last Updated**: 2026-02-04
