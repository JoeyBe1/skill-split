"""
Component handlers for skill-split.

This package provides type-specific handlers for different Claude Code
file types beyond the basic markdown/YAML support.

Handlers:
- BaseHandler: Abstract base class for all handlers
- ComponentDetector: Detects file type and returns appropriate handler
- PluginHandler: Handles plugin.json, .mcp.json, hooks.json
- HookHandler: Handles hooks.json + shell scripts
- ConfigHandler: Handles settings.json, mcp_config.json
- ScriptHandler: Base handler for script files (Python, JavaScript, Shell)
- PythonHandler: Handles .py files with decorators, async, context managers
- JavaScriptHandler: Handles .js and .jsx files
- TypeScriptHandler: Handles .ts and .tsx files
- ShellHandler: Handles .sh shell scripts
- HandlerFactory: Factory pattern for handler instantiation
"""

from handlers.base import BaseHandler
from handlers.component_detector import ComponentDetector
from handlers.plugin_handler import PluginHandler
from handlers.hook_handler import HookHandler
from handlers.config_handler import ConfigHandler
from handlers.script_handler import ScriptHandler
from handlers.python_handler import PythonHandler
from handlers.javascript_handler import JavaScriptHandler
from handlers.typescript_handler import TypeScriptHandler
from handlers.shell_handler import ShellHandler
from handlers.factory import HandlerFactory

__all__ = [
    "BaseHandler",
    "ComponentDetector",
    "PluginHandler",
    "HookHandler",
    "ConfigHandler",
    "ScriptHandler",
    "PythonHandler",
    "JavaScriptHandler",
    "TypeScriptHandler",
    "ShellHandler",
    "HandlerFactory",
]
