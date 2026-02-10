"""
skill-split API Usage Examples

Demonstrates how to use skill-split as a Python library.
"""

from core.parser import Parser
from core.database import DatabaseStore
from core.query import QueryAPI


def parse_and_store():
    """Parse a markdown file and store it in the database."""
    parser = Parser()
    db = DatabaseStore("~/.claude/databases/skill-split.db")
    
    content = Path("SKILL.md").read_text()
    document = parser.parse(content, "SKILL.md")
    file_id = db.store_document(document)
    print(f"Stored: {file_id}, Sections: {len(document.sections)}")
    return file_id


def progressive_disclosure():
    """Load sections one at a time for token efficiency."""
    query = QueryAPI("~/.claude/databases/skill-split.db")
    
    section = query.get_section(1)
    print(f"First: {section.title}")
    
    current_id = 1
    while True:
        next_section = query.get_next_section(current_id, "SKILL.md")
        if not next_section:
            break
        print(f"Next: {next_section.title}")
        current_id = next_section.id


def search_content(query_text: str):
    """Search for content across all files."""
    query = QueryAPI("~/.claude/databases/skill-split.db")
    results = query.search_sections(query_text)
    print(f"Found {len(results)} results for '{query_text}'")


if __name__ == "__main__":
    print("=== skill-split API Examples ===")
    print("Modify this file to run specific examples.")
