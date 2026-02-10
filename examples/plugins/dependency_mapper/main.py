#!/usr/bin/env python3
"""
Dependency Mapper Plugin for skill-split

Analyzes and maps cross-references and dependencies between
documentation sections and files.
"""

import sys
import json
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, deque


@dataclass
class Dependency:
    """Represents a single dependency"""
    source: str  # Source section/file
    target: str  # Target section/file
    type: str  # Type of dependency (link, include, import, etc.)
    line_number: Optional[int] = None
    context: Optional[str] = None


@dataclass
class Node:
    """Represents a node in the dependency graph"""
    id: str
    type: str  # section, file, external
    title: Optional[str] = None
    level: Optional[int] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class DependencyMap:
    """Complete dependency mapping"""
    nodes: Dict[str, Node] = field(default_factory=dict)
    dependencies: List[Dependency] = field(default_factory=list)
    external_links: List[Dependency] = field(default_factory=list)
    reverse_deps: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    def add_dependency(self, dep: Dependency):
        """Add a dependency to the map"""
        self.dependencies.append(dep)
        self.reverse_deps[dep.target].add(dep.source)

    def get_dependencies(self, node_id: str) -> List[Dependency]:
        """Get all dependencies from a node"""
        return [d for d in self.dependencies if d.source == node_id]

    def get_dependents(self, node_id: str) -> Set[str]:
        """Get all nodes that depend on this node"""
        return self.reverse_deps.get(node_id, set())

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "nodes": {id: {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "level": n.level,
                "metadata": n.metadata
            } for id, n in self.nodes.items()},
            "dependencies": [
                {
                    "source": d.source,
                    "target": d.target,
                    "type": d.type,
                    "line_number": d.line_number,
                    "context": d.context
                }
                for d in self.dependencies
            ],
            "external_links": [
                {
                    "source": d.source,
                    "target": d.target,
                    "type": d.type
                }
                for d in self.external_links
            ]
        }


class DependencyMapper:
    """Main dependency mapper class"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_depth = self.config.get("max_depth", 50)

        # Regex patterns
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.wiki_link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        self.include_pattern = re.compile(r'!include\s+(.+?)(?:\s|$)')
        self.reference_pattern = re.compile(r'@ref\s+(.+?)(?:\s|$)')
        self.anchor_pattern = re.compile(r'^#{1,6}\s+(.+)$')

    def map_document(self, file_path: str, include_external: bool = False) -> DependencyMap:
        """
        Map all dependencies within a document.

        Args:
            file_path: Path to the document
            include_external: Include external links in map

        Returns:
            DependencyMap containing all dependencies
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        dep_map = DependencyMap()

        # Parse structure
        lines = content.split('\n')
        sections = self._parse_sections(lines)

        # Create nodes
        for section_id, section in sections.items():
            node = Node(
                id=section_id,
                type="section",
                title=section["title"],
                level=section["level"],
                metadata={"line_start": section["line_start"]}
            )
            dep_map.nodes[section_id] = node

        # Find dependencies
        for section_id, section in sections.items():
            section_content = section["content"]

            # Find markdown links
            for match in self.link_pattern.finditer(section_content):
                link_text = match.group(1)
                link_url = match.group(2)

                if link_url.startswith('#'):
                    # Internal anchor link
                    target = self._resolve_anchor(link_url[1:], sections)
                    if target:
                        dep_map.add_dependency(Dependency(
                            source=section_id,
                            target=target,
                            type="anchor_link",
                            line_number=section.get("line_start"),
                            context=link_text
                        ))

                elif link_url.startswith('./') or link_url.startswith('../'):
                    # Relative file link
                    target_path = str((path.parent / link_url).resolve())
                    dep_map.add_dependency(Dependency(
                        source=section_id,
                        target=target_path,
                        type="file_link",
                        line_number=section.get("line_start"),
                        context=link_text
                    ))

                elif include_external and link_url.startswith('http'):
                    # External link
                    dep_map.external_links.append(Dependency(
                        source=section_id,
                        target=link_url,
                        type="external_link",
                        line_number=section.get("line_start"),
                        context=link_text
                    ))

            # Find wiki-style links
            for match in self.wiki_link_pattern.finditer(section_content):
                target = match.group(1)
                dep_map.add_dependency(Dependency(
                    source=section_id,
                    target=target,
                    type="wiki_link",
                    line_number=section.get("line_start"),
                    context=target
                ))

            # Find includes
            for match in self.include_pattern.finditer(section_content):
                target = match.group(1).strip()
                dep_map.add_dependency(Dependency(
                    source=section_id,
                    target=target,
                    type="include",
                    line_number=section.get("line_start"),
                    context=target
                ))

            # Find references
            for match in self.reference_pattern.finditer(section_content):
                target = match.group(1).strip()
                dep_map.add_dependency(Dependency(
                    source=section_id,
                    target=target,
                    type="reference",
                    line_number=section.get("line_start"),
                    context=target
                ))

        return dep_map

    def _parse_sections(self, lines: List[str]) -> Dict[str, Dict]:
        """Parse document into sections"""
        sections = {}
        current_section = None
        section_content = []
        section_counter = 0

        for line_num, line in enumerate(lines, 1):
            match = self.heading_pattern.match(line)

            if match:
                # Save previous section
                if current_section:
                    current_section["content"] = '\n'.join(section_content)
                    sections[current_section["id"]] = current_section

                # Start new section
                level = len(match.group(1))
                title = match.group(2).strip()

                # Generate section ID
                section_id = f"section_{section_counter}"
                section_counter += 1

                current_section = {
                    "id": section_id,
                    "title": title,
                    "level": level,
                    "line_start": line_num,
                    "anchor": self._generate_anchor(title)
                }
                section_content = []

            else:
                if current_section:
                    section_content.append(line)

        # Save last section
        if current_section:
            current_section["content"] = '\n'.join(section_content)
            sections[current_section["id"]] = current_section

        return sections

    def _generate_anchor(self, title: str) -> str:
        """Generate anchor ID from title"""
        # Convert to lowercase, replace spaces with hyphens
        anchor = title.lower()
        anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
        anchor = re.sub(r'\s+', '-', anchor)
        return anchor.strip('-')

    def _resolve_anchor(self, anchor: str, sections: Dict[str, Dict]) -> Optional[str]:
        """Resolve an anchor to a section ID"""
        # Try exact match first
        for section_id, section in sections.items():
            if section["anchor"] == anchor:
                return section_id

        # Try partial match
        for section_id, section in sections.items():
            if anchor in section["anchor"] or section["anchor"] in anchor:
                return section_id

        return None

    def find_circular_references(self, dep_map: DependencyMap) -> List[List[str]]:
        """
        Find circular dependency chains using DFS.

        Args:
            dep_map: Dependency map to analyze

        Returns:
            List of circular chains
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node_id: str):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for dep in dep_map.get_dependencies(node_id):
                if dep.target in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep.target)
                    cycle = path[cycle_start:] + [dep.target]
                    cycles.append(cycle)
                elif dep.target not in visited:
                    dfs(dep.target)

            path.pop()
            rec_stack.remove(node_id)

        for node_id in dep_map.nodes:
            if node_id not in visited:
                dfs(node_id)

        return cycles

    def find_orphan_sections(self, dep_map: DependencyMap) -> List[str]:
        """
        Find sections that are not referenced by any other section.

        Args:
            dep_map: Dependency map to analyze

        Returns:
            List of orphan section IDs
        """
        orphans = []

        for node_id in dep_map.nodes:
            dependents = dep_map.get_dependents(node_id)

            # Check if anything references this section
            # (excluding self-references)
            external_refs = [d for d in dependents if d != node_id]

            if not external_refs and node_id != "section_0":
                # Section 0 is usually the root, not an orphan
                orphans.append(node_id)

        return orphans

    def find_entry_points(self, dep_map: DependencyMap) -> List[str]:
        """
        Find entry point sections (no incoming dependencies).

        Args:
            dep_map: Dependency map to analyze

        Returns:
            List of entry point section IDs
        """
        entry_points = []

        for node_id in dep_map.nodes:
            dependents = dep_map.get_dependents(node_id)
            if not dependents:
                entry_points.append(node_id)

        return entry_points

    def generate_graph(
        self,
        dep_map: DependencyMap,
        format: str = "dot"
    ) -> str:
        """
        Generate dependency graph in specified format.

        Args:
            dep_map: Dependency map to visualize
            format: Output format (dot, mermaid, json)

        Returns:
            Graph representation as string
        """
        if format == "json":
            return json.dumps(dep_map.to_dict(), indent=2)

        elif format == "mermaid":
            return self._generate_mermaid(dep_map)

        elif format == "dot":
            return self._generate_dot(dep_map)

        else:
            raise ValueError(f"Unknown format: {format}")

    def _generate_dot(self, dep_map: DependencyMap) -> str:
        """Generate Graphviz DOT format"""
        lines = [
            "digraph dependencies {",
            "  rankdir=TB;",
            "  node [shape=box, style=rounded];",
            ""
        ]

        # Add nodes
        for node_id, node in dep_map.nodes.items():
            label = node.title or node_id
            label = label.replace('"', '\\"')

            if node.type == "section":
                if node.level == 1:
                    lines.append(f'  "{node_id}" [label="{label}", style="filled", fillcolor="lightblue"];')
                elif node.level == 2:
                    lines.append(f'  "{node_id}" [label="{label}", style="filled", fillcolor="lightgray"];')
                else:
                    lines.append(f'  "{node_id}" [label="{label}"];')

        # Add edges
        for dep in dep_map.dependencies:
            style = ""
            if dep.type == "include":
                style = " [style=dashed, color=blue]"
            elif dep.type == "reference":
                style = " [style=dotted, color=green]"

            lines.append(f'  "{dep.source}" -> "{dep.target}"{style};')

        lines.append("}")
        return "\\n".join(lines)

    def _generate_mermaid(self, dep_map: DependencyMap) -> str:
        """Generate Mermaid diagram format"""
        lines = ["graph TD"]

        # Add nodes
        for node_id, node in dep_map.nodes.items():
            label = node.title or node_id
            # Escape special characters
            label = label.replace('"', '#quot;')

            node_id_safe = node_id.replace("-", "_")

            if node.level == 1:
                lines.append(f'  {node_id_safe}["{label}"]:::root')
            else:
                lines.append(f'  {node_id_safe}["{label}"]')

        # Add edges
        for dep in dep_map.dependencies:
            source_safe = dep.source.replace("-", "_")
            target_safe = dep.target.replace("-", "_")

            if dep.type == "include":
                lines.append(f'  {source_safe} -.->|include| {target_safe}')
            elif dep.type == "reference":
                lines.append(f'  {source_safe} ==>|ref| {target_safe}')
            else:
                lines.append(f'  {source_safe} --> {target_safe}')

        # Add styles
        lines.append("")
        lines.append("  classDef root fill:# lightblue,stroke:#333,stroke-width:2px")

        return "\\n".join(lines)


def format_dependency_map(dep_map: DependencyMap, output_format: str = "text") -> str:
    """Format dependency map for output"""
    if output_format == "json":
        return json.dumps(dep_map.to_dict(), indent=2)

    lines = [
        "Dependency Map",
        "=" * 80,
        f"Nodes: {len(dep_map.nodes)}",
        f"Dependencies: {len(dep_map.dependencies)}",
        f"External Links: {len(dep_map.external_links)}",
        ""
    ]

    # Group dependencies by source
    by_source = defaultdict(list)
    for dep in dep_map.dependencies:
        by_source[dep.source].append(dep)

    for source, deps in sorted(by_source.items()):
        source_node = dep_map.nodes.get(source)
        source_title = source_node.title if source_node else source

        lines.append(f"From: {source_title} ({source})")

        for dep in deps:
            target_node = dep_map.nodes.get(dep.target)
            target_title = target_node.title if target_node else dep.target

            lines.append(f"  -> {target_title} ({dep.type})")

            if dep.context:
                lines.append(f"     Context: {dep.context}")

        lines.append("")

    return "\\n".join(lines)


def format_cycles(cycles: List[List[str]], dep_map: DependencyMap) -> str:
    """Format circular references for output"""
    if not cycles:
        return "No circular references found."

    lines = [
        f"Found {len(cycles)} circular reference(s):",
        ""
    ]

    for i, cycle in enumerate(cycles, 1):
        lines.append(f"Cycle {i}:")

        for j, node_id in enumerate(cycle):
            node = dep_map.nodes.get(node_id)
            title = node.title if node else node_id

            if j < len(cycle) - 1:
                lines.append(f"  {title} ->")
            else:
                lines.append(f"  {title} (closes loop)")

        lines.append("")

    return "\\n".join(lines)


def format_orphans(orphans: List[str], dep_map: DependencyMap) -> str:
    """Format orphan sections for output"""
    if not orphans:
        return "No orphan sections found."

    lines = [
        f"Found {len(orphans)} orphan section(s) (unreferenced):",
        ""
    ]

    for orphan_id in orphans:
        node = dep_map.nodes.get(orphan_id)
        title = node.title if node else orphan_id
        lines.append(f"- {title} ({orphan_id})")

    return "\\n".join(lines)


def main():
    """Main entry point for plugin"""
    parser = argparse.ArgumentParser(
        description="Dependency Mapper Plugin for skill-split",
        prog="dependency_mapper"
    )
    parser.add_argument("command", choices=["map", "circular", "orphans", "graph", "cross-db", "analyze"],
                        help="Command to execute")
    parser.add_argument("target", help="File path or database path")
    parser.add_argument("--output", choices=["text", "json", "dot", "mermaid"],
                        help="Output format")
    parser.add_argument("--format", choices=["dot", "mermaid", "json"],
                        help="Graph format")
    parser.add_argument("--include-external", action="store_true",
                        help="Include external links in map")
    parser.add_argument("--report", action="store_true",
                        help="Generate detailed report")
    parser.add_argument("--out-file", help="Output file path")

    args = parser.parse_args()

    mapper = DependencyMapper()

    # Execute command
    if args.command == "map":
        output_format = args.output or "text"
        dep_map = mapper.map_document(args.target, args.include_external)

        if output_format == "json":
            print(json.dumps(dep_map.to_dict(), indent=2))
        else:
            print(format_dependency_map(dep_map, output_format))

    elif args.command == "circular":
        dep_map = mapper.map_document(args.target)
        cycles = mapper.find_circular_references(dep_map)

        if args.output == "json":
            print(json.dumps({"cycles": cycles}, indent=2))
        else:
            print(format_cycles(cycles, dep_map))

        return 1 if cycles else 0

    elif args.command == "orphans":
        dep_map = mapper.map_document(args.target)
        orphans = mapper.find_orphan_sections(dep_map)

        if args.output == "json":
            print(json.dumps({"orphans": orphans}, indent=2))
        else:
            print(format_orphans(orphans, dep_map))

        return 1 if orphans else 0

    elif args.command == "graph":
        graph_format = args.format or "dot"
        dep_map = mapper.map_document(args.target)
        graph = mapper.generate_graph(dep_map, graph_format)

        if args.out_file:
            with open(args.out_file, 'w') as f:
                f.write(graph)
            print(f"Graph saved to {args.out_file}")
        else:
            print(graph)

    elif args.command == "analyze":
        dep_map = mapper.map_document(args.target)

        print("Dependency Analysis Report")
        print("=" * 80)
        print(f"Total sections: {len(dep_map.nodes)}")
        print(f"Total dependencies: {len(dep_map.dependencies)}")
        print(f"External links: {len(dep_map.external_links)}")
        print()

        # Find entry points
        entry_points = mapper.find_entry_points(dep_map)
        print(f"Entry points: {len(entry_points)}")
        for ep in entry_points:
            node = dep_map.nodes.get(ep)
            print(f"  - {node.title if node else ep}")
        print()

        # Find orphans
        orphans = mapper.find_orphan_sections(dep_map)
        print(f"Orphan sections: {len(orphans)}")
        if orphans and args.report:
            print(format_orphans(orphans, dep_map))
        print()

        # Find cycles
        cycles = mapper.find_circular_references(dep_map)
        print(f"Circular references: {len(cycles)}")
        if cycles and args.report:
            print(format_cycles(cycles, dep_map))

        return 1 if cycles else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
