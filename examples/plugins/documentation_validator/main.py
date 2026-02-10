#!/usr/bin/env python3
"""
Documentation Validator Plugin for skill-split

Validates markdown documentation structure, checks for broken sections,
and generates comprehensive validation reports.
"""

import sys
import json
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    severity: ValidationSeverity
    category: str
    message: str
    line_number: Optional[int] = None
    section_id: Optional[int] = None
    suggestion: Optional[str] = None
    context: Optional[str] = None


@dataclass
class ValidationResult:
    """Results of document validation"""
    file_path: str
    is_valid: bool
    has_warnings: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "file_path": self.file_path,
            "is_valid": self.is_valid,
            "has_warnings": self.has_warnings,
            "issue_count": len(self.issues),
            "error_count": sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR),
            "warning_count": sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING),
            "issues": [
                {
                    "severity": i.severity.value,
                    "category": i.category,
                    "message": i.message,
                    "line_number": i.line_number,
                    "section_id": i.section_id,
                    "suggestion": i.suggestion,
                    "context": i.context
                }
                for i in self.issues
            ],
            "metrics": self.metrics
        }


class DocumentationValidator:
    """Main validator class"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validator with configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.max_heading_depth = self.config.get("max_heading_depth", 6)
        self.require_frontmatter = self.config.get("require_frontmatter", True)
        self.check_external_links = self.config.get("check_external_links", True)
        self.link_timeout = self.config.get("link_timeout", 10)

        # Regex patterns
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

    def validate_document(self, file_path: str) -> ValidationResult:
        """
        Validate a single markdown document.

        Args:
            file_path: Path to the markdown file

        Returns:
            ValidationResult with all issues found
        """
        path = Path(file_path)
        if not path.exists():
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                has_warnings=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="file",
                    message=f"File not found: {file_path}"
                )]
            )

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                has_warnings=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="file",
                    message=f"Failed to read file: {str(e)}"
                )]
            )

        issues = []
        metrics = {}

        # Check frontmatter
        if self.require_frontmatter:
            frontmatter_issues = self._validate_frontmatter(content)
            issues.extend(frontmatter_issues)
            metrics["has_frontmatter"] = len(frontmatter_issues) == 0

        # Check heading structure
        heading_issues, heading_metrics = self._validate_headings(content)
        issues.extend(heading_issues)
        metrics.update(heading_metrics)

        # Check links
        link_issues, link_metrics = self._validate_links(content)
        issues.extend(link_issues)
        metrics.update(link_metrics)

        # Check section continuity
        section_issues = self._validate_sections(content)
        issues.extend(section_issues)

        # Check code blocks
        code_issues = self._validate_code_blocks(content)
        issues.extend(code_issues)

        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        has_warnings = any(i.severity == ValidationSeverity.WARNING for i in issues)

        return ValidationResult(
            file_path=str(path),
            is_valid=not has_errors,
            has_warnings=has_warnings,
            issues=issues,
            metrics=metrics
        )

    def _validate_frontmatter(self, content: str) -> List[ValidationIssue]:
        """Validate YAML frontmatter"""
        issues = []
        match = self.frontmatter_pattern.match(content)

        if not match:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="frontmatter",
                message="Missing YAML frontmatter (expected --- delimiters)",
                line_number=1,
                suggestion="Add YAML frontmatter at the start: ---\ntitle: Your Title\n---"
            ))
            return issues

        frontmatter_text = match.group(1)
        lines = frontmatter_text.split('\n')

        # Check for required fields
        required_fields = ['title', 'description']
        present_fields = []

        for line in lines:
            if ':' in line:
                field = line.split(':', 1)[0].strip()
                present_fields.append(field)

        for field in required_fields:
            if field not in present_fields:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="frontmatter",
                    message=f"Missing recommended field: {field}",
                    suggestion=f"Add {field}: <value> to frontmatter"
                ))

        return issues

    def _validate_headings(self, content: str) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Validate heading structure and hierarchy"""
        issues = []
        lines = content.split('\n')
        headings = []

        for idx, line in enumerate(lines, 1):
            match = self.heading_pattern.match(line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    'level': level,
                    'text': text,
                    'line': idx
                })

        metrics = {
            'total_headings': len(headings),
            'max_depth': max((h['level'] for h in headings), default=0)
        }

        if len(headings) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="structure",
                message="No headings found in document",
                suggestion="Add at least one # heading"
            ))
            return issues, metrics

        # Check heading hierarchy
        prev_level = 0
        for heading in headings:
            level = heading['level']
            if level > self.max_heading_depth:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message=f"Heading level {level} exceeds maximum depth {self.max_heading_depth}",
                    line_number=heading['line'],
                    context=heading['text'],
                    suggestion=f"Use heading level {self.max_heading_depth} or lower"
                ))

            if level > prev_level + 1:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="structure",
                    message=f"Heading jump from level {prev_level} to {level}",
                    line_number=heading['line'],
                    context=heading['text'],
                    suggestion=f"Insert level {prev_level + 1} heading first"
                ))

            prev_level = level

        # Check for empty headings
        for heading in headings:
            if not heading['text']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message="Empty heading text",
                    line_number=heading['line'],
                    suggestion="Add descriptive text to heading"
                ))

        return issues, metrics

    def _validate_links(self, content: str) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Validate markdown links"""
        issues = []
        lines = content.split('\n')
        links = []
        internal_links = []

        for idx, line in enumerate(lines, 1):
            matches = self.link_pattern.finditer(line)
            for match in matches:
                link_text = match.group(1)
                link_url = match.group(2)
                links.append({
                    'text': link_text,
                    'url': link_url,
                    'line': idx
                })

                # Track internal links (anchor links)
                if link_url.startswith('#'):
                    internal_links.append({
                        'anchor': link_url[1:],
                        'line': idx
                    })

        metrics = {
            'total_links': len(links),
            'internal_links': len(internal_links),
            'external_links': len(links) - len(internal_links)
        }

        # Check for empty link text
        for link in links:
            if not link['text'].strip():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="links",
                    message="Link with empty text",
                    line_number=link['line'],
                    context=link['url'],
                    suggestion="Add descriptive text for the link"
                ))

        # Check for empty URLs
        for link in links:
            if not link['url'].strip():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="links",
                    message="Link with empty URL",
                    line_number=link['line'],
                    context=link['text'],
                    suggestion="Provide a valid URL for the link"
                ))

        # Note: External link checking would require HTTP requests
        # This is skipped by default but can be enabled

        return issues, metrics

    def _validate_sections(self, content: str) -> List[ValidationIssue]:
        """Validate section continuity and structure"""
        issues = []
        lines = content.split('\n')

        # Check for multiple consecutive blank lines
        blank_count = 0
        for idx, line in enumerate(lines, 1):
            if not line.strip():
                blank_count += 1
            else:
                if blank_count > 2:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="formatting",
                        message=f"Multiple consecutive blank lines ({blank_count})",
                        line_number=idx - 1,
                        suggestion="Reduce to single blank line"
                    ))
                blank_count = 0

        # Check for trailing whitespace
        for idx, line in enumerate(lines, 1):
            if line.rstrip() != line and line.strip():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="formatting",
                    message="Trailing whitespace",
                    line_number=idx,
                    suggestion="Remove trailing whitespace"
                ))

        return issues

    def _validate_code_blocks(self, content: str) -> List[ValidationIssue]:
        """Validate code block delimiters"""
        issues = []
        lines = content.split('\n')
        in_code_block = False
        code_fence = None
        code_start_line = 0

        for idx, line in enumerate(lines, 1):
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Opening fence
                    in_code_block = True
                    code_fence = line.strip()
                    code_start_line = idx

                    # Check for language identifier
                    if len(line.strip()) == 3:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.INFO,
                            category="code",
                            message="Code block missing language identifier",
                            line_number=idx,
                            suggestion="Add language identifier: ```python"
                        ))
                else:
                    # Closing fence
                    if line.strip() != code_fence:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="code",
                            message="Code block fence mismatch",
                            line_number=idx,
                            suggestion=f"Use matching fence: {code_fence}"
                        ))
                    in_code_block = False
                    code_fence = None

        # Check for unclosed code blocks
        if in_code_block:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="code",
                message="Unclosed code block",
                line_number=code_start_line,
                suggestion="Add closing fence: ```"
            ))

        return issues


def format_result(result: ValidationResult, output_format: str = "text") -> str:
    """Format validation result for output"""
    if output_format == "json":
        return json.dumps(result.to_dict(), indent=2)

    if output_format == "html":
        return format_html(result)

    # Default text format
    lines = [
        f"Validation Report: {result.file_path}",
        "=" * 80,
        f"Status: {'PASS ✓' if result.is_valid else 'FAIL ✗'}",
        f"Warnings: {'Yes' if result.has_warnings else 'No'}",
        f"Issues Found: {len(result.issues)}",
        ""
    ]

    if result.metrics:
        lines.append("Metrics:")
        for key, value in result.metrics.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

    if result.issues:
        lines.append("Issues:")
        lines.append("")

        for issue in result.issues:
            icon = {
                ValidationSeverity.ERROR: "✗",
                ValidationSeverity.WARNING: "⚠",
                ValidationSeverity.INFO: "ℹ"
            }[issue.severity]

            lines.append(f"  {icon} [{issue.severity.value.upper()}] {issue.category}")

            if issue.line_number:
                lines.append(f"    Line {issue.line_number}: {issue.message}")
            else:
                lines.append(f"    {issue.message}")

            if issue.context:
                lines.append(f"    Context: {issue.context}")

            if issue.suggestion:
                lines.append(f"    Suggestion: {issue.suggestion}")

            lines.append("")

    return "\n".join(lines)


def format_html(result: ValidationResult) -> str:
    """Format validation result as HTML"""
    issues_html = ""
    for issue in result.issues:
        color = {
            ValidationSeverity.ERROR: "#dc3545",
            ValidationSeverity.WARNING: "#ffc107",
            ValidationSeverity.INFO: "#17a2b8"
        }[issue.severity]

        issues_html += f"""
        <div class="issue" style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background: #f8f9fa;">
            <strong style="color: {color};">[{issue.severity.value.upper()}] {issue.category}</strong>
            <p>{issue.message}</p>
            {f'<p><em>Line {issue.line_number}</em></p>' if issue.line_number else ''}
            {f'<p><code>{issue.context}</code></p>' if issue.context else ''}
            {f'<p><strong>Fix:</strong> {issue.suggestion}</p>' if issue.suggestion else ''}
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Validation Report</title>
        <style>
            body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
            .header {{ padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .pass {{ background: #d4edda; color: #155724; }}
            .fail {{ background: #f8d7da; color: #721c24; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
            .metric {{ background: #e9ecef; padding: 15px; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <h1>Validation Report</h1>
        <div class="header {'pass' if result.is_valid else 'fail'}">
            <h2>{'PASS ✓' if result.is_valid else 'FAIL ✗'}</h2>
            <p>{result.file_path}</p>
        </div>

        <div class="metrics">
            <div class="metric"><strong>Total Issues:</strong> {len(result.issues)}</div>
            <div class="metric"><strong>Errors:</strong> {sum(1 for i in result.issues if i.severity == ValidationSeverity.ERROR)}</div>
            <div class="metric"><strong>Warnings:</strong> {sum(1 for i in result.issues if i.severity == ValidationSeverity.WARNING)}</div>
        </div>

        <h3>Issues</h3>
        {issues_html if result.issues else '<p>No issues found!</p>'}
    </body>
    </html>
    """


def main():
    """Main entry point for plugin"""
    parser = argparse.ArgumentParser(
        description="Documentation Validator Plugin",
        prog="documentation_validator"
    )
    parser.add_argument("command", choices=["validate", "validate-all", "report"],
                        help="Command to execute")
    parser.add_argument("target", nargs="?", help="File path or target")
    parser.add_argument("--strict", action="store_true", help="Enable strict validation")
    parser.add_argument("--output", choices=["text", "json", "html"], default="text",
                        help="Output format")
    parser.add_argument("--suggest", action="store_true", help="Include fix suggestions")
    parser.add_argument("--database", default="./skill_split.db", help="Database path")
    parser.add_argument("--config", help="Path to config file")

    args = parser.parse_args()

    # Load config
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}", file=sys.stderr)

    validator = DocumentationValidator(config)

    # Execute command
    if args.command == "validate":
        if not args.target:
            print("Error: 'validate' command requires a file path", file=sys.stderr)
            return 1

        result = validator.validate_document(args.target)
        print(format_result(result, args.output))

        return 0 if result.is_valid else 1

    elif args.command == "validate-all":
        print(f"Validating all documents in {args.database}")
        print("This feature requires database integration")
        return 0

    elif args.command == "report":
        if not args.target:
            print("Error: 'report' command requires a target", file=sys.stderr)
            return 1

        result = validator.validate_document(args.target)
        report = format_result(result, "html" if args.suggest else "text")

        if args.output and args.output not in ["text", "json", "html"]:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)

        return 0 if result.is_valid else 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
