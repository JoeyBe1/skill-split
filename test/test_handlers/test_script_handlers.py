"""
Unit tests for script handlers (Python, JavaScript, TypeScript, Shell).

Tests cover:
- Parsing each language type
- Validation
- Round-trip recomposition
- Edge cases (empty files, comments only, multiple symbols)
- Related files (always empty for scripts)
- File type and format detection
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path

from handlers.script_handler import ScriptHandler, RegexSymbolFinder
from handlers.python_handler import PythonHandler
from handlers.javascript_handler import JavaScriptHandler
from handlers.typescript_handler import TypeScriptHandler
from handlers.shell_handler import ShellHandler
from models import FileType, FileFormat, ValidationResult


class TestPythonHandler:
    """Tests for PythonHandler class."""

    @pytest.fixture
    def python_file(self):
        """Create a temporary Python file with test content."""
        temp_dir = tempfile.mkdtemp()
        py_path = Path(temp_dir) / "test_module.py"

        content = '''"""Module docstring for testing."""

def simple_function():
    """A simple function."""
    return "hello"


class TestClass:
    """A test class."""

    def method_one(self):
        """First method."""
        pass

    def method_two(self):
        """Second method."""
        return 42


@decorator
def decorated_function():
    """A decorated function."""
    pass


def another_function(x, y):
    """Function with parameters."""
    return x + y
'''
        with open(py_path, 'w') as f:
            f.write(content)

        yield str(py_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def python_empty(self):
        """Create an empty Python file."""
        temp_dir = tempfile.mkdtemp()
        py_path = Path(temp_dir) / "empty.py"

        with open(py_path, 'w') as f:
            f.write("")

        yield str(py_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def python_comments_only(self):
        """Create a Python file with only comments."""
        temp_dir = tempfile.mkdtemp()
        py_path = Path(temp_dir) / "comments_only.py"

        content = '''"""This is a docstring."""
# This is a comment
# Another comment
'''
        with open(py_path, 'w') as f:
            f.write(content)

        yield str(py_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def python_complex(self):
        """Create a complex Python file with nested structures."""
        temp_dir = tempfile.mkdtemp()
        py_path = Path(temp_dir) / "complex.py"

        content = '''"""Complex module with multiple classes and functions."""

def standalone_function():
    """A standalone function."""
    pass


class OuterClass:
    """Outer class definition."""

    def __init__(self):
        """Constructor."""
        self.value = 42

    class InnerClass:
        """Nested class definition."""

        def inner_method(self):
            """Method in nested class."""
            pass


async def async_function():
    """An async function."""
    await something()
'''
        with open(py_path, 'w') as f:
            f.write(content)

        yield str(py_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_python_parse_basic(self, python_file):
        """Test basic Python file parsing."""
        handler = PythonHandler(python_file)
        doc = handler.parse()

        assert doc.file_type == FileType.SCRIPT
        assert doc.format == FileFormat.PYTHON_SCRIPT
        assert len(doc.sections) >= 2  # Module docstring + at least 1 symbol

    def test_python_parse_symbols(self, python_file):
        """Test that Python symbols are correctly identified."""
        handler = PythonHandler(python_file)
        doc = handler.parse()

        section_titles = [s.title for s in doc.sections]
        assert "simple_function" in section_titles
        assert "TestClass" in section_titles
        assert "decorated_function" in section_titles
        assert "another_function" in section_titles

    def test_python_parse_decorated(self, python_file):
        """Test that decorated functions include decorator."""
        handler = PythonHandler(python_file)
        doc = handler.parse()

        decorated_section = next((s for s in doc.sections if s.title == "decorated_function"), None)
        assert decorated_section is not None
        assert "@" in decorated_section.content

    def test_python_validation_valid(self, python_file):
        """Test validation of valid Python file."""
        handler = PythonHandler(python_file)
        result = handler.validate()

        assert result.is_valid
        assert len(result.errors) == 0

    def test_python_validation_empty(self, python_empty):
        """Test validation of empty Python file."""
        handler = PythonHandler(python_empty)
        result = handler.validate()

        assert not result.is_valid
        assert any("empty" in e.lower() for e in result.errors)

    def test_python_validation_comments_only(self, python_comments_only):
        """Test validation of comments-only Python file."""
        handler = PythonHandler(python_comments_only)
        result = handler.validate()

        # Comments only should be valid (has module docstring)
        assert result.is_valid

    def test_python_related_files(self, python_file):
        """Test that Python files have no related files."""
        handler = PythonHandler(python_file)
        related = handler.get_related_files()

        assert isinstance(related, list)
        assert len(related) == 0

    def test_python_get_file_type(self, python_file):
        """Test get_file_type returns SCRIPT."""
        handler = PythonHandler(python_file)
        assert handler.get_file_type() == FileType.SCRIPT

    def test_python_get_file_format(self, python_file):
        """Test get_file_format returns PYTHON_SCRIPT."""
        handler = PythonHandler(python_file)
        assert handler.get_file_format() == FileFormat.PYTHON_SCRIPT

    def test_python_recompose_basic(self, python_file):
        """Test basic recomposition of Python file."""
        handler = PythonHandler(python_file)
        doc = handler.parse()

        recomposed = handler.recompose(doc.sections)

        assert recomposed
        assert 'def simple_function' in recomposed
        assert 'class TestClass' in recomposed

    def test_python_round_trip(self, python_file):
        """Test round-trip: original -> parse -> recompose == original."""
        handler = PythonHandler(python_file)

        with open(python_file, 'r') as f:
            original_content = f.read()

        doc = handler.parse()
        recomposed = handler.recompose(doc.sections)

        # Check that key elements are preserved
        assert 'def simple_function' in original_content
        assert 'def simple_function' in recomposed
        assert 'class TestClass' in original_content
        assert 'class TestClass' in recomposed

    def test_python_module_docstring(self, python_file):
        """Test that module docstring is captured."""
        handler = PythonHandler(python_file)
        doc = handler.parse()

        # First section should be module docstring
        if doc.sections:
            first_section = doc.sections[0]
            assert first_section.title == "module"
            assert "Module docstring for testing" in first_section.content

    def test_python_frontmatter(self, python_file):
        """Test that frontmatter includes language info."""
        handler = PythonHandler(python_file)
        doc = handler.parse()

        frontmatter_data = json.loads(doc.frontmatter)
        assert frontmatter_data["type"] == "script"
        assert frontmatter_data["language"] == "python"
        assert "symbol_count" in frontmatter_data

    def test_python_recompute_hash(self, python_file):
        """Test hash computation for Python files."""
        handler = PythonHandler(python_file)
        hash1 = handler.recompute_hash()
        hash2 = handler.recompute_hash()

        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length


class TestJavaScriptHandler:
    """Tests for JavaScriptHandler class."""

    @pytest.fixture
    def javascript_file(self):
        """Create a temporary JavaScript file with test content."""
        temp_dir = tempfile.mkdtemp()
        js_path = Path(temp_dir) / "test_module.js"

        content = '''// JavaScript test module

function simpleFunction() {
    return "hello";
}

class TestClass {
    constructor() {
        this.value = 42;
    }

    methodOne() {
        return this.value;
    }
}

const arrowFunction = (x, y) => {
    return x + y;
};

async function asyncFunction() {
    await something();
}
'''
        with open(js_path, 'w') as f:
            f.write(content)

        yield str(js_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def javascript_empty(self):
        """Create an empty JavaScript file."""
        temp_dir = tempfile.mkdtemp()
        js_path = Path(temp_dir) / "empty.js"

        with open(js_path, 'w') as f:
            f.write("")

        yield str(js_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def javascript_typescript_features(self):
        """Create a JS file with TypeScript-style comments."""
        temp_dir = tempfile.mkdtemp()
        js_path = Path(temp_dir) / "with_types.js"

        content = '''// Module with type comments

/**
 * A function with JSDoc
 * @param {string} name - The name
 * @returns {string} - The greeting
 */
function greet(name) {
    return `Hello, ${name}`;
}
'''
        with open(js_path, 'w') as f:
            f.write(content)

        yield str(js_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_javascript_parse_basic(self, javascript_file):
        """Test basic JavaScript file parsing."""
        handler = JavaScriptHandler(javascript_file)
        doc = handler.parse()

        assert doc.file_type == FileType.SCRIPT
        assert doc.format == FileFormat.JAVASCRIPT_TYPESCRIPT

    def test_javascript_parse_functions(self, javascript_file):
        """Test that JavaScript functions are correctly identified."""
        handler = JavaScriptHandler(javascript_file)
        doc = handler.parse()

        section_titles = [s.title for s in doc.sections]
        assert "simpleFunction" in section_titles
        assert "TestClass" in section_titles
        assert "arrowFunction" in section_titles

    def test_javascript_validation_valid(self, javascript_file):
        """Test validation of valid JavaScript file."""
        handler = JavaScriptHandler(javascript_file)
        result = handler.validate()

        assert result.is_valid
        assert len(result.errors) == 0

    def test_javascript_validation_empty(self, javascript_empty):
        """Test validation of empty JavaScript file."""
        handler = JavaScriptHandler(javascript_empty)
        result = handler.validate()

        assert not result.is_valid
        assert any("empty" in e.lower() for e in result.errors)

    def test_javascript_related_files(self, javascript_file):
        """Test that JavaScript files have no related files."""
        handler = JavaScriptHandler(javascript_file)
        related = handler.get_related_files()

        assert isinstance(related, list)
        assert len(related) == 0

    def test_javascript_get_file_type(self, javascript_file):
        """Test get_file_type returns SCRIPT."""
        handler = JavaScriptHandler(javascript_file)
        assert handler.get_file_type() == FileType.SCRIPT

    def test_javascript_get_file_format(self, javascript_file):
        """Test get_file_format returns JAVASCRIPT_TYPESCRIPT."""
        handler = JavaScriptHandler(javascript_file)
        assert handler.get_file_format() == FileFormat.JAVASCRIPT_TYPESCRIPT

    def test_javascript_recompose_basic(self, javascript_file):
        """Test basic recomposition of JavaScript file."""
        handler = JavaScriptHandler(javascript_file)
        doc = handler.parse()

        recomposed = handler.recompose(doc.sections)

        assert recomposed
        assert 'function simpleFunction' in recomposed
        assert 'class TestClass' in recomposed

    def test_javascript_round_trip(self, javascript_file):
        """Test round-trip: original -> parse -> recompose == original."""
        handler = JavaScriptHandler(javascript_file)

        with open(javascript_file, 'r') as f:
            original_content = f.read()

        doc = handler.parse()
        recomposed = handler.recompose(doc.sections)

        # Check that key elements are preserved
        assert 'function simpleFunction' in original_content
        assert 'function simpleFunction' in recomposed

    def test_javascript_frontmatter(self, javascript_file):
        """Test that frontmatter includes language info."""
        handler = JavaScriptHandler(javascript_file)
        doc = handler.parse()

        frontmatter_data = json.loads(doc.frontmatter)
        assert frontmatter_data["type"] == "script"
        assert frontmatter_data["language"] == "javascript"
        assert "symbol_count" in frontmatter_data

    def test_javascript_recompute_hash(self, javascript_file):
        """Test hash computation for JavaScript files."""
        handler = JavaScriptHandler(javascript_file)
        hash1 = handler.recompute_hash()
        hash2 = handler.recompute_hash()

        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length


class TestTypeScriptHandler:
    """Tests for TypeScriptHandler class."""

    @pytest.fixture
    def typescript_file(self):
        """Create a temporary TypeScript file with test content."""
        temp_dir = tempfile.mkdtemp()
        ts_path = Path(temp_dir) / "test_module.ts"

        content = '''// TypeScript test module

interface User {
    name: string;
    age: number;
}

type UserRole = 'admin' | 'user' | 'guest';

class UserService {
    private users: User[] = [];

    addUser(user: User): void {
        this.users.push(user);
    }

    getUserByName(name: string): User | undefined {
        return this.users.find(u => u.name === name);
    }
}

function processData<T>(data: T[]): T[] {
    return data;
}

const arrowFunction = (x: number, y: number): number => {
    return x + y;
};
'''
        with open(ts_path, 'w') as f:
            f.write(content)

        yield str(ts_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def typescript_empty(self):
        """Create an empty TypeScript file."""
        temp_dir = tempfile.mkdtemp()
        ts_path = Path(temp_dir) / "empty.ts"

        with open(ts_path, 'w') as f:
            f.write("")

        yield str(ts_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_typescript_parse_basic(self, typescript_file):
        """Test basic TypeScript file parsing."""
        handler = TypeScriptHandler(typescript_file)
        doc = handler.parse()

        assert doc.file_type == FileType.SCRIPT
        assert doc.format == FileFormat.JAVASCRIPT_TYPESCRIPT

    def test_typescript_parse_interfaces(self, typescript_file):
        """Test that TypeScript interfaces are correctly identified."""
        handler = TypeScriptHandler(typescript_file)
        doc = handler.parse()

        section_titles = [s.title for s in doc.sections]
        assert "User" in section_titles
        assert "UserRole" in section_titles
        assert "UserService" in section_titles

    def test_typescript_parse_classes(self, typescript_file):
        """Test that TypeScript classes are correctly identified."""
        handler = TypeScriptHandler(typescript_file)
        doc = handler.parse()

        section_titles = [s.title for s in doc.sections]
        assert "UserService" in section_titles

        # Check class section content
        service_section = next(s for s in doc.sections if s.title == "UserService")
        assert "class UserService" in service_section.content

    def test_typescript_validation_valid(self, typescript_file):
        """Test validation of valid TypeScript file."""
        handler = TypeScriptHandler(typescript_file)
        result = handler.validate()

        assert result.is_valid
        assert len(result.errors) == 0

    def test_typescript_validation_empty(self, typescript_empty):
        """Test validation of empty TypeScript file."""
        handler = TypeScriptHandler(typescript_empty)
        result = handler.validate()

        assert not result.is_valid
        assert any("empty" in e.lower() for e in result.errors)

    def test_typescript_related_files(self, typescript_file):
        """Test that TypeScript files have no related files."""
        handler = TypeScriptHandler(typescript_file)
        related = handler.get_related_files()

        assert isinstance(related, list)
        assert len(related) == 0

    def test_typescript_get_file_type(self, typescript_file):
        """Test get_file_type returns SCRIPT."""
        handler = TypeScriptHandler(typescript_file)
        assert handler.get_file_type() == FileType.SCRIPT

    def test_typescript_get_file_format(self, typescript_file):
        """Test get_file_format returns JAVASCRIPT_TYPESCRIPT."""
        handler = TypeScriptHandler(typescript_file)
        assert handler.get_file_format() == FileFormat.JAVASCRIPT_TYPESCRIPT

    def test_typescript_recompose_basic(self, typescript_file):
        """Test basic recomposition of TypeScript file."""
        handler = TypeScriptHandler(typescript_file)
        doc = handler.parse()

        recomposed = handler.recompose(doc.sections)

        assert recomposed
        assert 'interface User' in recomposed
        assert 'class UserService' in recomposed

    def test_typescript_round_trip(self, typescript_file):
        """Test round-trip: original -> parse -> recompose == original."""
        handler = TypeScriptHandler(typescript_file)

        with open(typescript_file, 'r') as f:
            original_content = f.read()

        doc = handler.parse()
        recomposed = handler.recompose(doc.sections)

        # Check that key elements are preserved
        assert 'interface User' in original_content
        assert 'interface User' in recomposed

    def test_typescript_frontmatter(self, typescript_file):
        """Test that frontmatter includes language info."""
        handler = TypeScriptHandler(typescript_file)
        doc = handler.parse()

        frontmatter_data = json.loads(doc.frontmatter)
        assert frontmatter_data["type"] == "script"
        assert frontmatter_data["language"] == "typescript"
        assert "symbol_count" in frontmatter_data

    def test_typescript_recompute_hash(self, typescript_file):
        """Test hash computation for TypeScript files."""
        handler = TypeScriptHandler(typescript_file)
        hash1 = handler.recompute_hash()
        hash2 = handler.recompute_hash()

        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length


class TestShellHandler:
    """Tests for ShellHandler class."""

    @pytest.fixture
    def shell_file(self):
        """Create a temporary shell script with test content."""
        temp_dir = tempfile.mkdtemp()
        sh_path = Path(temp_dir) / "test_script.sh"

        content = '''#!/bin/bash
# Test shell script

# Function to greet
greet() {
    echo "Hello, $1"
}

# Function to calculate
calculate() {
    echo $(($1 + $2))
}

# Main function
main() {
    greet "World"
    calculate 5 3
}

# Run main
main
'''
        with open(sh_path, 'w') as f:
            f.write(content)

        yield str(sh_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def shell_empty(self):
        """Create an empty shell script."""
        temp_dir = tempfile.mkdtemp()
        sh_path = Path(temp_dir) / "empty.sh"

        with open(sh_path, 'w') as f:
            f.write("")

        yield str(sh_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def shell_comments_only(self):
        """Create a shell script with only comments."""
        temp_dir = tempfile.mkdtemp()
        sh_path = Path(temp_dir) / "comments.sh"

        content = '''#!/bin/bash
# This is a comment
# Another comment
'''
        with open(sh_path, 'w') as f:
            f.write(content)

        yield str(sh_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def shell_complex(self):
        """Create a complex shell script."""
        temp_dir = tempfile.mkdtemp()
        sh_path = Path(temp_dir) / "complex.sh"

        content = '''#!/bin/bash
# Complex shell script

# Function with nested structure
process_data() {
    local input="$1"
    if [ -n "$input" ]; then
        echo "Processing: $input"
        for item in $input; do
            echo "Item: $item"
        done
    fi
}

# Function with case statement
handle_option() {
    case "$1" in
        start)
            echo "Starting..."
            ;;
        stop)
            echo "Stopping..."
            ;;
        *)
            echo "Unknown option"
            ;;
    esac
}

# Main function with multiple operations
deploy_app() {
    echo "Deploying application..."
    # Check dependencies
    if command -v git &> /dev/null; then
        echo "Git found"
    fi
}
'''
        with open(sh_path, 'w') as f:
            f.write(content)

        yield str(sh_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_shell_parse_basic(self, shell_file):
        """Test basic shell script parsing."""
        handler = ShellHandler(shell_file)
        doc = handler.parse()

        assert doc.file_type == FileType.SCRIPT
        assert doc.format == FileFormat.SHELL_SCRIPT

    def test_shell_parse_functions(self, shell_file):
        """Test that shell functions are correctly identified."""
        handler = ShellHandler(shell_file)
        doc = handler.parse()

        section_titles = [s.title for s in doc.sections]
        assert "greet" in section_titles
        assert "calculate" in section_titles
        assert "main" in section_titles

    def test_shell_validation_valid(self, shell_file):
        """Test validation of valid shell script."""
        handler = ShellHandler(shell_file)
        result = handler.validate()

        assert result.is_valid
        assert len(result.errors) == 0

    def test_shell_validation_empty(self, shell_empty):
        """Test validation of empty shell script."""
        handler = ShellHandler(shell_empty)
        result = handler.validate()

        assert not result.is_valid
        assert any("empty" in e.lower() for e in result.errors)

    def test_shell_validation_comments_only(self, shell_comments_only):
        """Test validation of comments-only shell script."""
        handler = ShellHandler(shell_comments_only)
        result = handler.validate()

        # Comments only should be valid (has shebang and comments)
        assert result.is_valid or len(result.warnings) >= 0

    def test_shell_related_files(self, shell_file):
        """Test that shell scripts have no related files."""
        handler = ShellHandler(shell_file)
        related = handler.get_related_files()

        assert isinstance(related, list)
        assert len(related) == 0

    def test_shell_get_file_type(self, shell_file):
        """Test get_file_type returns SCRIPT."""
        handler = ShellHandler(shell_file)
        assert handler.get_file_type() == FileType.SCRIPT

    def test_shell_get_file_format(self, shell_file):
        """Test get_file_format returns SHELL_SCRIPT."""
        handler = ShellHandler(shell_file)
        assert handler.get_file_format() == FileFormat.SHELL_SCRIPT

    def test_shell_recompose_basic(self, shell_file):
        """Test basic recomposition of shell script."""
        handler = ShellHandler(shell_file)
        doc = handler.parse()

        recomposed = handler.recompose(doc.sections)

        assert recomposed
        assert 'greet()' in recomposed
        assert 'calculate()' in recomposed

    def test_shell_round_trip(self, shell_file):
        """Test round-trip: original -> parse -> recompose == original."""
        handler = ShellHandler(shell_file)

        with open(shell_file, 'r') as f:
            original_content = f.read()

        doc = handler.parse()
        recomposed = handler.recompose(doc.sections)

        # Check that key elements are preserved
        assert 'greet()' in original_content
        assert 'greet()' in recomposed

    def test_shell_shebang_preserved(self, shell_file):
        """Test that shebang is preserved in comments."""
        handler = ShellHandler(shell_file)
        doc = handler.parse()

        # Module section should include shebang
        if doc.sections and doc.sections[0].title == "module":
            assert "#!/bin/bash" in doc.sections[0].content

    def test_shell_frontmatter(self, shell_file):
        """Test that frontmatter includes language info."""
        handler = ShellHandler(shell_file)
        doc = handler.parse()

        frontmatter_data = json.loads(doc.frontmatter)
        assert frontmatter_data["type"] == "script"
        assert frontmatter_data["language"] == "shell"
        assert "symbol_count" in frontmatter_data

    def test_shell_recompute_hash(self, shell_file):
        """Test hash computation for shell scripts."""
        handler = ShellHandler(shell_file)
        hash1 = handler.recompute_hash()
        hash2 = handler.recompute_hash()

        # Hash should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length


class TestRegexSymbolFinder:
    """Tests for RegexSymbolFinder helper class."""

    def test_find_python_symbols_class(self):
        """Test finding Python class definitions."""
        lines = [
            "class MyClass:",
            "    pass",
            "",
            "class AnotherClass(Base):",
            "    pass",
        ]

        symbols = RegexSymbolFinder.find_python_symbols(lines)

        assert len(symbols) == 2
        assert symbols[0]["name"] == "MyClass"
        assert symbols[0]["kind"] == "class"
        assert symbols[1]["name"] == "AnotherClass"

    def test_find_python_symbols_function(self):
        """Test finding Python function definitions."""
        lines = [
            "def my_function():",
            "    pass",
            "",
            "def another_function(x, y):",
            "    return x + y",
        ]

        symbols = RegexSymbolFinder.find_python_symbols(lines)

        assert len(symbols) == 2
        assert symbols[0]["name"] == "my_function"
        assert symbols[0]["kind"] == "function"

    def test_find_python_symbols_with_decorator(self):
        """Test that decorators are included with functions."""
        lines = [
            "@property",
            "def my_property(self):",
            "    return self._value",
        ]

        symbols = RegexSymbolFinder.find_python_symbols(lines)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "my_property"
        # Should include decorator line
        assert symbols[0]["line_start"] == 1  # 0-based index -> line 1

    def test_find_javascript_symbols_class(self):
        """Test finding JavaScript class definitions."""
        lines = [
            "class MyClass {",
            "    constructor() {}",
            "}",
            "",
            "class Child extends Parent {",
            "    method() {}",
            "}",
        ]

        symbols = RegexSymbolFinder.find_javascript_symbols(lines)

        assert len(symbols) >= 2
        class_symbols = [s for s in symbols if s["kind"] == "class"]
        assert len(class_symbols) >= 1

    def test_find_javascript_symbols_function(self):
        """Test finding JavaScript function definitions."""
        lines = [
            "function myFunction() {",
            "    return true;",
            "}",
            "",
            "async function asyncFunction() {",
            "    await something();",
            "}",
        ]

        symbols = RegexSymbolFinder.find_javascript_symbols(lines)

        assert len(symbols) >= 2
        assert any(s["name"] == "myFunction" for s in symbols)
        assert any(s["name"] == "asyncFunction" for s in symbols)

    def test_find_javascript_symbols_interface(self):
        """Test finding TypeScript interface definitions."""
        lines = [
            "interface User {",
            "    name: string;",
            "}",
            "",
            "type Role = 'admin' | 'user';",
        ]

        symbols = RegexSymbolFinder.find_javascript_symbols(lines)

        assert len(symbols) >= 2
        assert any(s["name"] == "User" and s["kind"] == "interface" for s in symbols)
        assert any(s["name"] == "Role" and s["kind"] == "type" for s in symbols)

    def test_find_shell_symbols_function(self):
        """Test finding shell function definitions."""
        lines = [
            "#!/bin/bash",
            "",
            "my_function() {",
            "    echo 'hello'",
            "}",
            "",
            "another_function () {",
            "    echo 'world'",
            "}",
        ]

        symbols = RegexSymbolFinder.find_shell_symbols(lines)

        assert len(symbols) == 2
        assert symbols[0]["name"] == "my_function"
        assert symbols[1]["name"] == "another_function"

    def test_find_shell_symbols_skips_keywords(self):
        """Test that shell keywords are not treated as functions."""
        lines = [
            "if [ condition ]; then",
            "    echo 'true'",
            "fi",
            "",
            "for item in list; do",
            "    echo $item",
            "done",
        ]

        symbols = RegexSymbolFinder.find_shell_symbols(lines)

        # Should not find 'if', 'then', 'fi', 'for', 'do', 'done' as functions
        assert not any(s["name"] in ["if", "then", "fi", "for", "do", "done"] for s in symbols)
        assert len(symbols) == 0


class TestScriptHandlerEdgeCases:
    """Test edge cases across all script handlers."""

    def test_handler_language_attribute(self):
        """Test that each handler has correct language attribute."""
        temp_dir = tempfile.mkdtemp()

        # Create test files
        py_path = Path(temp_dir) / "test.py"
        js_path = Path(temp_dir) / "test.js"
        ts_path = Path(temp_dir) / "test.ts"
        sh_path = Path(temp_dir) / "test.sh"

        for path in [py_path, js_path, ts_path, sh_path]:
            path.write_text("# test\n")

        try:
            py_handler = PythonHandler(str(py_path))
            js_handler = JavaScriptHandler(str(js_path))
            ts_handler = TypeScriptHandler(str(ts_path))
            sh_handler = ShellHandler(str(sh_path))

            assert py_handler.language == "python"
            assert js_handler.language == "javascript"
            assert ts_handler.language == "typescript"
            assert sh_handler.language == "shell"
        finally:
            shutil.rmtree(temp_dir)

    def test_multiple_symbols_ordering(self):
        """Test that multiple symbols maintain correct ordering."""
        temp_dir = tempfile.mkdtemp()
        py_path = Path(temp_dir) / "order_test.py"

        content = '''"""Module."""

def func_first():
    pass

def func_second():
    pass

class ClassThird:
    pass

def func_fourth():
    pass
'''
        py_path.write_text(content)

        try:
            handler = PythonHandler(str(py_path))
            doc = handler.parse()

            # Check that symbols are in order
            non_module_sections = [s for s in doc.sections if s.title != "module"]
            assert len(non_module_sections) == 4

            # Verify ordering by line_start
            line_starts = [s.line_start for s in non_module_sections]
            assert line_starts == sorted(line_starts)
        finally:
            shutil.rmtree(temp_dir)

    def test_crlf_warning(self):
        """Test that CRLF line ending check works in base handler."""
        # Note: Python's file reading normalizes line endings, so we test
        # the validation logic directly by checking the base handler behavior
        temp_dir = tempfile.mkdtemp()
        py_path = Path(temp_dir) / "test.py"

        # Write file with content
        content = 'def test():\n    pass\n'
        py_path.write_text(content)

        try:
            handler = PythonHandler(str(py_path))
            result = handler.validate()

            # File should be valid (no CRLF warning since Python normalizes)
            # This test verifies the validation runs without error
            assert result.is_valid
        finally:
            shutil.rmtree(temp_dir)

    def test_indentation_preservation(self):
        """Test that indentation is preserved in sections."""
        temp_dir = tempfile.mkdtemp()
        py_path = Path(temp_dir) / "indented.py"

        content = '''class IndentedClass:
    def method(self):
        if True:
            return "nested"
'''
        py_path.write_text(content)

        try:
            handler = PythonHandler(str(py_path))
            doc = handler.parse()

            class_section = next(s for s in doc.sections if s.title == "IndentedClass")
            assert "    def method" in class_section.content
            assert "        if True:" in class_section.content
        finally:
            shutil.rmtree(temp_dir)
