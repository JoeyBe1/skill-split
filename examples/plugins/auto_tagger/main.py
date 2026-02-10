#!/usr/bin/env python3
"""
Auto-Tagger Plugin for skill-split

Automatically analyzes section content and suggests relevant tags/keywords.
Updates document frontmatter with generated tags.
"""

import sys
import json
import re
import argparse
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime


@dataclass
class TagSuggestion:
    """Represents a tag suggestion"""
    tag: str
    confidence: float
    category: Optional[str] = None
    source: Optional[str] = None


@dataclass
class TagStats:
    """Statistics about tags"""
    tag: str
    count: int
    documents: List[str]


class TextAnalyzer:
    """Analyzes text content for keyword extraction"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_tag_length = self.config.get("min_tag_length", 3)
        self.max_tag_length = self.config.get("max_tag_length", 30)
        self.stop_words = set(self.config.get("stop_words", [
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall", "can"
        ]))

        # Technical term patterns
        self.code_pattern = re.compile(r'```(\w+)?')
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
        self.url_pattern = re.compile(r'https?://[^\s]+')
        self.word_pattern = re.compile(r'\b[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]\b')

    def extract_words(self, text: str) -> List[str]:
        """Extract words from text, filtering stop words"""
        # Remove code blocks and inline code
        text = self.code_pattern.sub(' ', text)
        text = self.inline_code_pattern.sub(' ', text)
        text = self.url_pattern.sub(' ', text)

        # Extract words
        words = self.word_pattern.findall(text.lower())

        # Filter by length and stop words
        filtered = [
            w for w in words
            if self.min_tag_length <= len(w) <= self.max_tag_length
            and w not in self.stop_words
        ]

        return filtered

    def extract_ngrams(self, words: List[str], n: int = 2) -> List[str]:
        """Extract n-grams (multi-word phrases)"""
        if len(words) < n:
            return []

        ngrams = []
        for i in range(len(words) - n + 1):
            phrase = ' '.join(words[i:i + n])
            # Check if any word is a stop word
            if not any(w in self.stop_words for w in words[i:i + n]):
                ngrams.append(phrase)

        return ngrams

    def calculate_tfidf(self, documents: List[List[str]]) -> Dict[str, float]:
        """Calculate TF-IDF scores for terms"""
        # Simple implementation - in production use scikit-learn
        doc_count = len(documents)
        term_doc_count = defaultdict(int)
        term_freq = defaultdict(int)

        for doc in documents:
            seen_terms = set()
            for term in doc:
                term_freq[term] += 1
                if term not in seen_terms:
                    term_doc_count[term] += 1
                    seen_terms.add(term)

        # Calculate TF-IDF
        tfidf = {}
        for term, freq in term_freq.items():
            tf = freq / sum(len(doc) for doc in documents)
            idf = doc_count / (1 + term_doc_count[term])
            tfidf[term] = tf * idf

        return tfidf


class AutoTagger:
    """Main auto-tagger class"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.analyzer = TextAnalyzer(config)
        self.tag_categories = self.config.get("tag_categories", {})

        # Predefined category patterns
        self.category_patterns = {
            "technology": re.compile(r'\b(python|javascript|typescript|java|go|rust|c\+\+|c#|php|ruby|swift|kotlin)\b', re.I),
            "framework": re.compile(r'\b(react|vue|angular|django|flask|fastapi|spring|express|laravel|rails)\b', re.I),
            "tool": re.compile(r'\b(git|docker|kubernetes|terraform|ansible|jenkins|github|gitlab)\b', re.I),
            "concept": re.compile(r'\b(api|rest|graphql|database|sql|nosql|authentication|authorization|testing|ci/cd|devops)\b', re.I),
            "pattern": re.compile(r'\b(mvc|singleton|observer|factory|strategy|decorator|adapter)\b', re.I)
        }

    def suggest_tags(self, content: str, count: int = 10) -> List[TagSuggestion]:
        """
        Suggest tags based on content analysis.

        Args:
            content: Document content
            count: Number of tags to suggest

        Returns:
            List of TagSuggestion objects
        """
        suggestions = []

        # Extract words and bigrams
        words = self.analyzer.extract_words(content)
        bigrams = self.analyzer.extract_ngrams(words, 2)
        trigrams = self.analyzer.extract_ngrams(words, 3)

        # Count frequencies
        word_counts = Counter(words)
        bigram_counts = Counter(bigrams)
        trigram_counts = Counter(trigrams)

        # Get top terms
        top_words = word_counts.most_common(count * 2)
        top_bigrams = bigram_counts.most_common(count)
        top_trigrams = trigram_counts.most_common(count // 2)

        # Score and categorize
        for word, freq in top_words:
            category = self._categorize_term(word)
            confidence = min(1.0, freq / 10)

            suggestions.append(TagSuggestion(
                tag=word,
                confidence=confidence,
                category=category,
                source="frequency"
            ))

        for bigram, freq in top_bigrams:
            if freq >= 2:
                suggestions.append(TagSuggestion(
                    tag=bigram,
                    confidence=min(1.0, freq / 5),
                    source="bigram"
                ))

        for trigram, freq in top_trigrams:
            if freq >= 2:
                suggestions.append(TagSuggestion(
                    tag=trigram,
                    confidence=min(1.0, freq / 3),
                    source="trigram"
                ))

        # Extract code languages
        code_blocks = self.analyzer.code_pattern.findall(content)
        for lang in set(code_blocks):
            if lang:
                suggestions.append(TagSuggestion(
                    tag=lang.lower(),
                    confidence=0.9,
                    category="technology",
                    source="code_block"
                ))

        # Sort by confidence and deduplicate
        seen = set()
        unique_suggestions = []
        for sugg in sorted(suggestions, key=lambda x: x.confidence, reverse=True):
            tag_lower = sugg.tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_suggestions.append(sugg)

        return unique_suggestions[:count]

    def extract_keywords(self, content: str, count: int = 5) -> List[str]:
        """
        Extract important keywords from content.

        Args:
            content: Document content
            count: Number of keywords to extract

        Returns:
            List of keyword strings
        """
        suggestions = self.suggest_tags(content, count * 2)

        # Prioritize higher confidence and categorized tags
        prioritized = sorted(
            suggestions,
            key=lambda x: (x.category is not None, x.confidence),
            reverse=True
        )

        return [s.tag for s in prioritized[:count]]

    def _categorize_term(self, term: str) -> Optional[str]:
        """Categorize a term into a category"""
        term_lower = term.lower()

        for category, pattern in self.category_patterns.items():
            if pattern.search(term):
                return category

        return None

    def update_frontmatter(
        self,
        file_path: str,
        tags: List[str],
        force: bool = False,
        backup: bool = True
    ) -> bool:
        """
        Update document frontmatter with tags.

        Args:
            file_path: Path to the document
            tags: Tags to add
            force: Overwrite existing tags
            backup: Create backup before updating

        Returns:
            True if successful, False otherwise
        """
        path = Path(file_path)

        if not path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return False

        # Read file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create backup if requested
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = path.with_suffix(f'.bak.{timestamp}')
            shutil.copy2(path, backup_path)
            print(f"Backup created: {backup_path}")

        # Check for existing frontmatter
        frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = frontmatter_pattern.match(content)

        if match:
            # Existing frontmatter
            frontmatter_text = match.group(1)
            rest = content[match.end():]

            # Parse YAML (simple implementation)
            frontmatter = self._parse_simple_yaml(frontmatter_text)

            # Update tags
            if force or 'tags' not in frontmatter:
                existing_tags = frontmatter.get('tags', [])
                all_tags = list(set(existing_tags + tags))
                frontmatter['tags'] = all_tags

                # Reconstruct frontmatter
                new_frontmatter = self._build_frontmatter(frontmatter)

                # Write updated content
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_frontmatter + rest)

                print(f"Updated {len(all_tags)} tags in {file_path}")
                return True
            else:
                print(f"Tags already exist. Use --force to overwrite.")
                return False
        else:
            # No frontmatter, create it
            frontmatter = {
                'title': path.stem,
                'tags': tags
            }

            new_frontmatter = self._build_frontmatter(frontmatter)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_frontmatter + content)

            print(f"Created frontmatter with {len(tags)} tags in {file_path}")
            return True

    def _parse_simple_yaml(self, yaml_text: str) -> Dict[str, any]:
        """Simple YAML parser for frontmatter"""
        result = {}

        for line in yaml_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Handle lists (simple case)
                if value.startswith('['):
                    try:
                        value = json.loads(value.replace("'", '"'))
                    except:
                        value = [v.strip() for v in value[1:-1].split(',')]
                elif value.startswith('-'):
                    value = [value[1:].strip()]

                result[key] = value

        return result

    def _build_frontmatter(self, data: Dict[str, any]) -> str:
        """Build YAML frontmatter from dictionary"""
        lines = ['---']

        for key, value in data.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")

        lines.append('---')
        lines.append('')

        return '\n'.join(lines)

    def get_similar_documents(
        self,
        file_path: str,
        database_path: str,
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find documents with similar tags.

        Args:
            file_path: Reference document path
            database_path: Path to skill-split database
            limit: Number of results

        Returns:
            List of (document_path, similarity) tuples
        """
        # This would integrate with the skill-split database
        # For now, return empty list
        print("Note: Document similarity requires database integration")
        return []


def format_suggestions(suggestions: List[TagSuggestion], output_format: str = "text") -> str:
    """Format tag suggestions for output"""
    if output_format == "json":
        return json.dumps([
            {
                "tag": s.tag,
                "confidence": s.confidence,
                "category": s.category,
                "source": s.source
            }
            for s in suggestions
        ], indent=2)

    # Text format
    lines = ["Suggested Tags:", "=" * 60, ""]

    for i, sugg in enumerate(suggestions, 1):
        category_str = f" [{sugg.category}]" if sugg.category else ""
        source_str = f" ({sugg.source})" if sugg.source else ""

        lines.append(
            f"{i:2}. {sugg.tag}{category_str} - {sugg.confidence:.2%}{source_str}"
        )

    return "\n".join(lines)


def main():
    """Main entry point for plugin"""
    parser = argparse.ArgumentParser(
        description="Auto-Tagger Plugin for skill-split",
        prog="auto_tagger"
    )
    parser.add_argument("command", choices=["suggest", "update", "extract", "stats", "similar"],
                        help="Command to execute")
    parser.add_argument("file_path", nargs="?", help="Path to document file")
    parser.add_argument("--count", type=int, default=10, help="Number of tags/keywords")
    parser.add_argument("--tags", help="Comma-separated list of tags")
    parser.add_argument("--force", action="store_true", help="Overwrite existing tags")
    parser.add_argument("--no-backup", action="store_true", help="Don't create backup")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--database", default="./skill_split.db", help="Database path")
    parser.add_argument("--limit", type=int, default=5, help="Result limit")
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

    tagger = AutoTagger(config)

    # Execute command
    if args.command == "suggest":
        if not args.file_path:
            print("Error: 'suggest' command requires a file path", file=sys.stderr)
            return 1

        with open(args.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        suggestions = tagger.suggest_tags(content, args.count)
        print(format_suggestions(suggestions, args.output))

        return 0

    elif args.command == "update":
        if not args.file_path:
            print("Error: 'update' command requires a file path", file=sys.stderr)
            return 1

        if args.tags:
            tags = [t.strip() for t in args.tags.split(',')]
        else:
            with open(args.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tags = [s.tag for s in tagger.suggest_tags(content, args.count)]

        success = tagger.update_frontmatter(
            args.file_path,
            tags,
            force=args.force,
            backup=not args.no_backup
        )

        return 0 if success else 1

    elif args.command == "extract":
        if not args.file_path:
            print("Error: 'extract' command requires a file path", file=sys.stderr)
            return 1

        with open(args.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        keywords = tagger.extract_keywords(content, args.count)

        if args.output == "json":
            print(json.dumps(keywords, indent=2))
        else:
            print("Extracted Keywords:")
            for kw in keywords:
                print(f"  - {kw}")

        return 0

    elif args.command == "stats":
        print(f"Tag statistics for {args.database}")
        print("This feature requires database integration")
        return 0

    elif args.command == "similar":
        if not args.file_path:
            print("Error: 'similar' command requires a file path", file=sys.stderr)
            return 1

        similar = tagger.get_similar_documents(
            args.file_path,
            args.database,
            args.limit
        )

        print(f"Documents similar to {args.file_path}:")
        for doc, similarity in similar:
            print(f"  {similarity:.2%} - {doc}")

        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
