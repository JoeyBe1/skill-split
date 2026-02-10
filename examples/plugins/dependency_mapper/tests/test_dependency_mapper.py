#!/usr/bin/env python3
"""
Tests for Dependency Mapper Plugin
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import (
    DependencyMapper,
    DependencyMap,
    Dependency,
    Node,
    format_dependency_map,
    format_cycles,
    format_orphans
)


class TestDependency:
    """Test Dependency dataclass"""

    def test_create_dependency(self):
        """Test creating a dependency"""
        dep = Dependency(
            source="section_1",
            target="section_2",
            type="link",
            line_number=10,
            context="See section 2"
        )

        assert dep.source == "section_1"
        assert dep.target == "section_2"
        assert dep.type == "link"
        assert dep.line_number == 10
        assert dep.context == "See section 2"


class TestNode:
    """Test Node dataclass"""

    def test_create_node(self):
        """Test creating a node"""
        node = Node(
            id="section_1",
            type="section",
            title="Introduction",
            level=1,
            metadata={"line_start": 1}
        )

        assert node.id == "section_1"
        assert node.type == "section"
        assert node.title == "Introduction"
        assert node.level == 1
        assert node.metadata["line_start"] == 1


class TestDependencyMap:
    """Test DependencyMap class"""

    def test_create_map(self):
        """Test creating a dependency map"""
        dep_map = DependencyMap()

        assert len(dep_map.nodes) == 0
        assert len(dep_map.dependencies) == 0
        assert len(dep_map.external_links) == 0

    def test_add_dependency(self):
        """Test adding a dependency"""
        dep_map = DependencyMap()
        dep = Dependency(source="A", target="B", type="link")

        dep_map.add_dependency(dep)

        assert len(dep_map.dependencies) == 1
        assert dep_map.dependencies[0] == dep

    def test_add_dependency_updates_reverse(self):
        """Test that adding dependency updates reverse mapping"""
        dep_map = DependencyMap()
        dep = Dependency(source="A", target="B", type="link")

        dep_map.add_dependency(dep)

        assert "A" in dep_map.reverse_deps["B"]

    def test_get_dependencies(self):
        """Test getting dependencies from a node"""
        dep_map = DependencyMap()
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))
        dep_map.add_dependency(Dependency(source="A", target="C", type="link"))
        dep_map.add_dependency(Dependency(source="B", target="C", type="link"))

        deps_a = dep_map.get_dependencies("A")
        assert len(deps_a) == 2
        assert deps_a[0].target == "B"
        assert deps_a[1].target == "C"

    def test_get_dependents(self):
        """Test getting dependents of a node"""
        dep_map = DependencyMap()
        dep_map.add_dependency(Dependency(source="A", target="C", type="link"))
        dep_map.add_dependency(Dependency(source="B", target="C", type="link"))

        dependents_c = dep_map.get_dependents("C")
        assert "A" in dependents_c
        assert "B" in dependents_c

    def test_to_dict(self):
        """Test converting map to dictionary"""
        dep_map = DependencyMap()
        dep_map.nodes["section_1"] = Node(
            id="section_1",
            type="section",
            title="Test"
        )
        dep_map.add_dependency(Dependency(
            source="section_1",
            target="section_2",
            type="link"
        ))

        data = dep_map.to_dict()

        assert "nodes" in data
        assert "dependencies" in data
        assert len(data["nodes"]) == 1
        assert len(data["dependencies"]) == 1


class TestDependencyMapper:
    """Test DependencyMapper class"""

    def test_init(self):
        """Test mapper initialization"""
        mapper = DependencyMapper()

        assert mapper.max_depth == 50

    def test_init_with_config(self):
        """Test mapper with custom config"""
        config = {"max_depth": 100}
        mapper = DependencyMapper(config)

        assert mapper.max_depth == 100

    def test_generate_anchor(self):
        """Test anchor generation"""
        mapper = DependencyMapper()

        assert mapper._generate_anchor("Hello World") == "hello-world"
        assert mapper._generate_anchor("Test@123!") == "test123"
        assert mapper._generate_anchor("  Spaces  ") == "spaces"

    @pytest.fixture
    def sample_document(self):
        """Create a sample document with dependencies"""
        content = """# Main Document

This is the main section.

## Section One

See [Section Two](#section-two) for more info.

## Section Two

Referenced from section one.

## Section Three

Links to [Section One](#section-one).

## Orphan Section

This section is not linked to anywhere.
"""
        return content

    def test_map_document(self, sample_document):
        """Test document mapping"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_document)
            f.flush()

            mapper = DependencyMapper()
            dep_map = mapper.map_document(f.name)

            assert len(dep_map.nodes) > 0
            assert len(dep_map.dependencies) > 0

            Path(f.name).unlink()

    def test_map_document_finds_links(self, sample_document):
        """Test that document mapping finds internal links"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_document)
            f.flush()

            mapper = DependencyMapper()
            dep_map = mapper.map_document(f.name)

            # Should find internal anchor links
            anchor_links = [d for d in dep_map.dependencies if d.type == "anchor_link"]
            assert len(anchor_links) >= 2

            Path(f.name).unlink()

    def test_find_circular_references(self):
        """Test circular reference detection"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section")
        dep_map.nodes["B"] = Node(id="B", type="section")
        dep_map.nodes["C"] = Node(id="C", type="section")

        # Create circular dependency: A -> B -> C -> A
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))
        dep_map.add_dependency(Dependency(source="B", target="C", type="link"))
        dep_map.add_dependency(Dependency(source="C", target="A", type="link"))

        mapper = DependencyMapper()
        cycles = mapper.find_circular_references(dep_map)

        assert len(cycles) == 1
        assert len(cycles[0]) == 4  # A -> B -> C -> A (4 nodes in cycle)

    def test_find_circular_references_none(self):
        """Test circular reference detection with no cycles"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section")
        dep_map.nodes["B"] = Node(id="B", type="section")
        dep_map.nodes["C"] = Node(id="C", type="section")

        # Linear dependency: A -> B -> C
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))
        dep_map.add_dependency(Dependency(source="B", target="C", type="link"))

        mapper = DependencyMapper()
        cycles = mapper.find_circular_references(dep_map)

        assert len(cycles) == 0

    def test_find_orphan_sections(self):
        """Test orphan section detection"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section")
        dep_map.nodes["B"] = Node(id="B", type="section")
        dep_map.nodes["C"] = Node(id="C", type="section", title="Orphan")

        # A -> B, nothing references C
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))

        mapper = DependencyMapper()
        orphans = mapper.find_orphan_sections(dep_map)

        assert len(orphans) >= 1
        assert "C" in orphans

    def test_find_entry_points(self):
        """Test entry point detection"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section")
        dep_map.nodes["B"] = Node(id="B", type="section")
        dep_map.nodes["C"] = Node(id="C", type="section")

        # B -> A, C -> A, nothing references B or C
        dep_map.add_dependency(Dependency(source="B", target="A", type="link"))
        dep_map.add_dependency(Dependency(source="C", target="A", type="link"))

        mapper = DependencyMapper()
        entry_points = mapper.find_entry_points(dep_map)

        assert "B" in entry_points
        assert "C" in entry_points
        assert "A" not in entry_points

    def test_generate_dot_graph(self):
        """Test DOT graph generation"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section", title="Section A", level=1)
        dep_map.nodes["B"] = Node(id="B", type="section", title="Section B", level=2)
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))

        mapper = DependencyMapper()
        dot = mapper._generate_dot(dep_map)

        assert "digraph dependencies" in dot
        assert '"A"' in dot or '"Section A"' in dot
        assert "->" in dot

    def test_generate_mermaid_graph(self):
        """Test Mermaid graph generation"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section", title="Section A", level=1)
        dep_map.nodes["B"] = Node(id="B", type="section", title="Section B", level=2)
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))

        mapper = DependencyMapper()
        mermaid = mapper._generate_mermaid(dep_map)

        assert "graph TD" in mermaid
        assert "Section A" in mermaid or "A" in mermaid
        assert "-->" in mermaid

    def test_generate_json_graph(self):
        """Test JSON graph generation"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section", title="Section A")
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))

        mapper = DependencyMapper()
        json_str = mapper.generate_graph(dep_map, "json")
        data = json.loads(json_str)

        assert "nodes" in data
        assert "dependencies" in data
        assert len(data["nodes"]) == 1

    def test_map_document_with_file_links(self):
        """Test mapping document with file links"""
        content = """# Main

See [Other File](./other.md) for details.

## Section

Content here.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='/tmp') as f:
            f.write(content)
            f.flush()

            mapper = DependencyMapper()
            dep_map = mapper.map_document(f.name, include_external=False)

            # Should find file link
            file_links = [d for d in dep_map.dependencies if d.type == "file_link"]
            assert len(file_links) >= 1

            Path(f.name).unlink()

    def test_map_document_with_external_links(self):
        """Test mapping document with external links"""
        content = """# Main

Visit [Example](https://example.com) for more.

## Section

Content here.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()

            mapper = DependencyMapper()
            dep_map = mapper.map_document(f.name, include_external=True)

            # Should find external link
            assert len(dep_map.external_links) >= 1
            assert dep_map.external_links[0].type == "external_link"

            Path(f.name).unlink()


class TestFormatters:
    """Test output formatting functions"""

    def test_format_dependency_map_text(self):
        """Test text format of dependency map"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section", title="Section A")
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))

        output = format_dependency_map(dep_map, "text")

        assert "Dependency Map" in output
        assert "Section A" in output

    def test_format_dependency_map_json(self):
        """Test JSON format of dependency map"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section", title="Section A")
        dep_map.add_dependency(Dependency(source="A", target="B", type="link"))

        output = format_dependency_map(dep_map, "json")
        data = json.loads(output)

        assert "nodes" in data

    def test_format_cycles(self):
        """Test cycle formatting"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section", title="A")
        dep_map.nodes["B"] = Node(id="B", type="section", title="B")

        cycles = [["A", "B", "A"]]

        output = format_cycles(cycles, dep_map)

        assert "circular reference" in output.lower()
        assert "A" in output

    def test_format_cycles_none(self):
        """Test cycle formatting with no cycles"""
        output = format_cycles([], None)

        assert "No circular references" in output

    def test_format_orphans(self):
        """Test orphan formatting"""
        dep_map = DependencyMap()
        dep_map.nodes["A"] = Node(id="A", type="section", title="Orphan Section")

        orphans = ["A"]

        output = format_orphans(orphans, dep_map)

        assert "orphan" in output.lower()
        assert "Orphan Section" in output

    def test_format_orphans_none(self):
        """Test orphan formatting with no orphans"""
        output = format_orphans([], None)

        assert "No orphan" in output


class TestIntegration:
    """Integration tests"""

    @pytest.fixture
    def complex_document(self):
        """Create a complex document with various dependencies"""
        content = """# API Reference

Complete API documentation.

## Authentication

See [Tokens](#tokens) for authentication details.

## Tokens

Authentication tokens are described in [Authentication](#authentication).

## Endpoints

API endpoints:

- [Users](#users-api)
- [Posts](#posts-api)

## Users API

User management endpoints.

## Posts API

Post management endpoints.

## Unused Section

This section is not linked anywhere.
"""
        return content

    def test_full_analysis_workflow(self, complex_document):
        """Test complete analysis workflow"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(complex_document)
            f.flush()

            mapper = DependencyMapper()

            # Step 1: Map document
            dep_map = mapper.map_document(f.name)
            assert len(dep_map.nodes) > 0

            # Step 2: Find circular references
            cycles = mapper.find_circular_references(dep_map)
            # Should find the Authentication <-> Tokens cycle
            assert len(cycles) > 0

            # Step 3: Find orphans
            orphans = mapper.find_orphan_sections(dep_map)
            # Should find "Unused Section"
            assert len(orphans) > 0

            # Step 4: Generate graph
            dot = mapper.generate_graph(dep_map, "dot")
            assert "digraph" in dot

            Path(f.name).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
