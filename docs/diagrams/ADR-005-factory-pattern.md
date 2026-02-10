# ADR-005: Factory Pattern for Component Handlers

**Status**: Accepted
**Date**: 2025-02-10
**Context**: Phase 09 - Component Handlers

## Context

As skill-split evolved to support multiple file types (plugins, hooks, configs, scripts), we needed:
1. **Extensibility**: Easy to add new file type handlers
2. **Consistency**: Uniform interface for all handlers
3. **Separation of Concerns**: Clear boundaries between parsing logic
4. **Discoverability**: Automatic detection of appropriate handler

The initial approach of conditional logic in the main parser became unwieldy as new file types were added.

## Decision

Implement Factory Pattern with HandlerFactory and BaseHandler abstraction for component-specific parsers.

### Technical Details

- **BaseHandler**: Abstract base class defining handler interface
- **HandlerFactory**: Factory for creating handler instances based on file type
- **ComponentDetector**: Detects file type and determines appropriate handler
- **Specialized Handlers**: Concrete implementations for each file type

### Implementation

```python
# Abstract base class
class BaseHandler(ABC):
    @abstractmethod
    def parse(self) -> ParsedDocument:
        """Parse the file and return structured document."""
        pass

    @abstractmethod
    def validate(self) -> ValidationResult:
        """Validate the parsed structure."""
        pass

    @abstractmethod
    def get_file_type(self) -> FileType:
        """Return the file type enum."""
        pass

    @abstractmethod
    def get_file_format(self) -> FileFormat:
        """Return the file format enum."""
        pass

    def get_related_files(self) -> List[str]:
        """Return list of related files (for multi-file components)."""
        return []

# Factory class
class HandlerFactory:
    @staticmethod
    def create_handler(file_path: str) -> Optional[BaseHandler]:
        """Create appropriate handler for the given file."""
        file_type, _ = ComponentDetector.detect(file_path)

        handler_classes = {
            FileType.PLUGIN: PluginHandler,
            FileType.HOOK: HookHandler,
            FileType.CONFIG: ConfigHandler,
            FileType.SCRIPT: _get_script_handler_for_path(file_path),
        }

        handler_class = handler_classes.get(file_type)
        return handler_class(file_path) if handler_class else None

# Specialized handler example
class PluginHandler(BaseHandler):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.plugin_data = self._load_plugin_json()

    def parse(self) -> ParsedDocument:
        # Plugin-specific parsing logic
        sections = self._extract_sections()
        return ParsedDocument(
            frontmatter=json.dumps(self.plugin_data),
            sections=sections,
            file_type=FileType.PLUGIN,
            file_format=FileFormat.JSON,
            original_path=self.file_path
        )
```

### Handler Hierarchy

```
BaseHandler (abstract)
├── PluginHandler
├── HookHandler
├── ConfigHandler
└── ScriptHandler (abstract)
    ├── PythonHandler
    ├── JavaScriptHandler
    ├── TypeScriptHandler
    └── ShellHandler
```

## Rationale

### Advantages

1. **Extensibility**: Add new handlers by implementing BaseHandler
2. **Consistency**: Uniform interface across all file types
3. **Separation**: Each handler encapsulates its parsing logic
4. **Testability**: Handlers can be tested in isolation
5. **Discoverability**: Automatic routing to appropriate handler
6. **Open/Closed**: Open for extension, closed for modification

### Alternatives Considered

1. **Conditional Logic in Parser**
   - Rejected: Violates Single Responsibility Principle
   - Parser becomes god object
   - Hard to test individual file types
   - Violates Open/Closed Principle

2. **Strategy Pattern (Parser passed to constructor)**
   - Rejected: More complex than needed
   - Requires client to choose strategy
   - Less discoverability
   - No automatic routing

3. **Separate Commands per File Type**
   - Rejected: More complex CLI
   - Code duplication
   - No unified interface
   - Harder to maintain

## Consequences

### Positive

- New file types can be added without modifying existing code
- Clear separation of parsing logic
- Consistent interface for all handlers
- Easy to test individual handlers
- Automatic file type detection and routing

### Negative

- More boilerplate for new handlers
- Additional abstraction layer
- Need to maintain handler registry
- Slightly more complex class hierarchy

### Mitigation

- BaseHandler provides template and documentation
- HandlerFactory centralizes registration
- Clear naming conventions reduce confusion
- Comprehensive test suite ensures correctness

## Adding a New Handler

1. **Create handler class**:

```python
class MyHandler(BaseHandler):
    def parse(self) -> ParsedDocument:
        # Implementation
        pass

    def validate(self) -> ValidationResult:
        # Implementation
        pass

    def get_file_type(self) -> FileType:
        return FileType.MY_TYPE

    def get_file_format(self) -> FileFormat:
        return FileFormat.CUSTOM
```

2. **Add FileType enum value**:

```python
class FileType(Enum):
    MY_TYPE = "my_type"
```

3. **Register in ComponentDetector**:

```python
def detect(self, file_path: str) -> tuple[FileType, FileFormat]:
    if file_path.endswith('.myext'):
        return FileType.MY_TYPE, FileFormat.CUSTOM
```

4. **Register in HandlerFactory**:

```python
handler_classes = {
    # ... existing handlers
    FileType.MY_TYPE: MyHandler,
}
```

## Usage

```python
# Automatic handler creation
handler = HandlerFactory.create_handler("plugin.json")
if handler:
    doc = handler.parse()
    result = handler.validate()
```

## Related Decisions

- [ADR-004](./ADR-004-sha256-hashing.md): SHA256 Hashing for Integrity Verification

## References

- [Factory Pattern (Refactoring Guru)](https://refactoring.guru/design-patterns/factory-method)
- [Handler Implementation](../../handlers/)
- [Component Detection](../../handlers/component_detector.py)
