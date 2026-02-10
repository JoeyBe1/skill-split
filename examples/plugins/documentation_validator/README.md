# Documentation Validator Plugin

Validates markdown documentation structure and integrity within skill-split.

## Features

- **Structure Validation**: Ensures proper markdown heading hierarchy
- **Section Integrity**: Checks for broken or orphaned sections
- **Link Verification**: Validates internal and external links
- **Frontmatter Checks**: Validates YAML frontmatter completeness
- **Reporting**: Generates detailed validation reports

## Installation

```bash
# Copy to your skill-split plugins directory
cp -r examples/plugins/documentation_validator ~/.claude/plugins/
```

## Usage

```bash
# Validate a specific file
./skill_split.py plugin documentation_validator validate <file>

# Validate all files in database
./skill_split.py plugin documentation_validator validate-all

# Generate report with suggestions
./skill_split.py plugin documentation_validator report <file> --suggest
```

## API

### validate_document(file_path: str) -> ValidationResult

Validates a single document and returns detailed results.

### validate_database(db_path: str) -> DatabaseValidationResult

Validates all documents in the database.

## Exit Codes

- `0`: Validation passed
- `1`: Validation failed with errors
- `2`: Validation passed with warnings

## Requirements

- skill-split >= 1.0
- Python >= 3.9

## License

MIT
