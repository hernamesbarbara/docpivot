#!/usr/bin/env python3
"""Custom Readers Example - Integration Patterns

This example demonstrates how to create custom readers that extend
DocPivot's input capabilities for new document formats.
"""

import json
import re
from pathlib import Path
from docpivot.io.readers import BaseReader
from docpivot.io.readers.exceptions import UnsupportedFormatError
from docling_core.types.doc import DoclingDocument, NodeItem, TextItem


class PlainTextReader(BaseReader):
    """Custom reader for plain text files.

    This reader demonstrates basic custom reader implementation by
    converting plain text files into DoclingDocument format.
    """

    def can_read(self, file_path: str) -> bool:
        """Check if this reader can handle the given file."""
        return file_path.endswith(('.txt', '.text'))

    def detect_format(self, file_path: str) -> bool:
        """Detect if file is a supported plain text format."""
        if not self.can_read(file_path):
            return False

        try:
            # Basic validation - ensure it's readable as text
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to read first 1KB to validate text format
                sample = f.read(1024)
                # Simple heuristic: if most characters are printable, it's text
                printable_ratio = sum(1 for c in sample if c.isprintable() or c.isspace()) / len(sample)
                return printable_ratio > 0.8
        except (UnicodeDecodeError, IOError):
            return False

    def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
        """Load plain text file and convert to DoclingDocument."""
        if not self.can_read(file_path):
            raise UnsupportedFormatError(f"Cannot read {file_path}: Not a supported text format")

        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create DoclingDocument
        doc = DoclingDocument(name=Path(file_path).name)

        # Split content into paragraphs (basic text structure)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # Convert each paragraph to a TextItem
        for i, paragraph in enumerate(paragraphs):
            text_item = TextItem(
                label=f"text_{i}",
                text=paragraph
            )
            doc.texts.append(text_item)

        return doc


class SimpleJsonReader(BaseReader):
    """Custom reader for simple JSON documents.

    This reader handles JSON files with a simple text-based structure,
    demonstrating how to process structured data into DoclingDocument.
    """

    def can_read(self, file_path: str) -> bool:
        """Check if this reader can handle JSON files."""
        return file_path.endswith('.json') and not file_path.endswith(('.docling.json', '.lexical.json'))

    def detect_format(self, file_path: str) -> bool:
        """Detect if file is a supported simple JSON format."""
        if not self.can_read(file_path):
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check for simple JSON structure we can handle
            return (
                isinstance(data, dict) and
                any(key in data for key in ['title', 'content', 'text', 'body'])
            )
        except (json.JSONDecodeError, IOError):
            return False

    def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
        """Load simple JSON file and convert to DoclingDocument."""
        if not self.can_read(file_path):
            raise UnsupportedFormatError(f"Cannot read {file_path}: Not a supported JSON format")

        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise UnsupportedFormatError("JSON must be an object/dictionary")

        # Create DoclingDocument
        doc_name = data.get('title', Path(file_path).name)
        doc = DoclingDocument(name=doc_name)

        # Extract content from various possible fields
        content_sources = ['content', 'text', 'body', 'description']

        text_index = 0

        # Add title if available and different from content
        title = data.get('title')
        if title:
            title_item = TextItem(
                label=f"title_{text_index}",
                text=title
            )
            doc.texts.append(title_item)
            text_index += 1

        # Add main content
        for field in content_sources:
            if field in data:
                content = data[field]

                if isinstance(content, str):
                    # Single text content
                    text_item = TextItem(
                        label=f"text_{text_index}",
                        text=content
                    )
                    doc.texts.append(text_item)
                    text_index += 1

                elif isinstance(content, list):
                    # Multiple content items
                    for item in content:
                        if isinstance(item, str):
                            text_item = TextItem(
                                label=f"text_{text_index}",
                                text=item
                            )
                            doc.texts.append(text_item)
                            text_index += 1
                        elif isinstance(item, dict) and 'text' in item:
                            text_item = TextItem(
                                label=f"text_{text_index}",
                                text=item['text']
                            )
                            doc.texts.append(text_item)
                            text_index += 1

        return doc


class MarkdownReader(BaseReader):
    """Custom reader for Markdown files.

    This reader demonstrates parsing structured text formats and
    converting them to DoclingDocument with preserved structure.
    """

    def can_read(self, file_path: str) -> bool:
        """Check if this reader can handle Markdown files."""
        return file_path.endswith(('.md', '.markdown'))

    def detect_format(self, file_path: str) -> bool:
        """Detect if file is a Markdown format."""
        if not self.can_read(file_path):
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(512)  # Check first 512 characters

            # Look for common Markdown patterns
            markdown_patterns = [
                r'^#+\s',  # Headers
                r'^\*\s|\+\s|-\s',  # Lists
                r'\*\*.*\*\*',  # Bold
                r'\*.*\*',  # Italic
                r'\[.*\]\(.*\)',  # Links
            ]

            for pattern in markdown_patterns:
                if re.search(pattern, content, re.MULTILINE):
                    return True

            return False

        except (UnicodeDecodeError, IOError):
            return False

    def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
        """Load Markdown file and convert to DoclingDocument."""
        if not self.can_read(file_path):
            raise UnsupportedFormatError(f"Cannot read {file_path}: Not a supported Markdown format")

        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create DoclingDocument
        doc = DoclingDocument(name=Path(file_path).name)

        # Simple Markdown parsing (basic implementation)
        lines = content.split('\n')
        current_text = []
        text_index = 0

        for line in lines:
            line = line.strip()

            if not line:
                # Empty line - end current text block
                if current_text:
                    text_item = TextItem(
                        label=f"text_{text_index}",
                        text='\n'.join(current_text)
                    )
                    doc.texts.append(text_item)
                    text_index += 1
                    current_text = []
            else:
                # Add line to current text block
                current_text.append(line)

        # Handle any remaining text
        if current_text:
            text_item = TextItem(
                label=f"text_{text_index}",
                text='\n'.join(current_text)
            )
            doc.texts.append(text_item)

        return doc


def create_sample_files():
    """Create sample files for testing custom readers."""
    print("Creating sample files for custom reader testing...\n")

    # Create sample plain text file
    with open("sample_text.txt", 'w', encoding='utf-8') as f:
        f.write("""This is a sample plain text document.

It contains multiple paragraphs separated by blank lines.

Each paragraph will be converted to a separate text item in the DoclingDocument.

This demonstrates how custom readers can process simple text formats.""")

    # Create sample JSON file
    sample_json = {
        "title": "Sample JSON Document",
        "content": [
            "This is the first paragraph of content.",
            "This is the second paragraph.",
            "And this is the third paragraph with more text."
        ],
        "metadata": {
            "author": "DocPivot Example",
            "created": "2025-01-01"
        }
    }

    with open("sample_document.json", 'w', encoding='utf-8') as f:
        json.dump(sample_json, f, indent=2)

    # Create sample Markdown file
    with open("sample_document.md", 'w', encoding='utf-8') as f:
        f.write("""# Sample Markdown Document

This is a sample markdown document to demonstrate custom reader capabilities.

## Features

- **Bold text** formatting
- *Italic text* formatting
- [Links](https://example.com)

## Content

This document contains multiple sections and demonstrates how a custom
Markdown reader can parse structured text and convert it to DoclingDocument format.

### Subsection

More content here to show the hierarchical structure.""")

    print("✓ Created sample_text.txt")
    print("✓ Created sample_document.json")
    print("✓ Created sample_document.md")
    print()


def demonstrate_custom_readers():
    """Demonstrate custom reader functionality."""
    print("=== Custom Readers Demonstration ===\n")

    # Create sample files first
    create_sample_files()

    # Initialize custom readers
    readers = [
        ("Plain Text Reader", PlainTextReader(), "sample_text.txt"),
        ("Simple JSON Reader", SimpleJsonReader(), "sample_document.json"),
        ("Markdown Reader", MarkdownReader(), "sample_document.md")
    ]

    for reader_name, reader, sample_file in readers:
        print(f"Testing {reader_name}...")

        try:
            # Test format detection
            if reader.detect_format(sample_file):
                print(f"  ✓ Format detected for {sample_file}")

                # Load document
                doc = reader.load_data(sample_file)
                print(f"  ✓ Document loaded: {doc.name}")
                print(f"  ✓ Text items: {len(doc.texts)}")

                # Show first text item preview
                if doc.texts:
                    first_text = doc.texts[0].text
                    preview = first_text[:100] + "..." if len(first_text) > 100 else first_text
                    print(f"  ✓ First text preview: {preview}")

                # Test serialization with loaded document
                from docling_core.transforms.serializer.markdown import MarkdownDocSerializer

                serializer = MarkdownDocSerializer(doc=doc)
                result = serializer.serialize()

                # Save output
                output_file = f"output_{reader_name.lower().replace(' ', '_')}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.text)

                print(f"  ✓ Serialized to {output_file} ({len(result.text)} chars)")

            else:
                print(f"  ❌ Format not detected for {sample_file}")

        except Exception as e:
            print(f"  ❌ Error: {type(e).__name__}: {e}")

        print()


def demonstrate_reader_factory_integration():
    """Demonstrate integrating custom readers with ReaderFactory."""
    print("=== Reader Factory Integration ===\n")

    try:
        from docpivot.io.readers import ReaderFactory

        # Create factory and add custom readers
        factory = ReaderFactory()

        print("1. Registering custom readers with factory...")

        # Note: In actual implementation, you'd extend ReaderFactory
        # to support dynamic registration. This shows the concept.
        custom_readers = [
            PlainTextReader(),
            SimpleJsonReader(),
            MarkdownReader()
        ]

        # Test custom readers with factory-like behavior
        test_files = ["sample_text.txt", "sample_document.json", "sample_document.md"]

        print("2. Testing custom reader selection...")

        for file_path in test_files:
            print(f"\nProcessing: {file_path}")

            # Find appropriate reader
            selected_reader = None
            for reader in custom_readers:
                if reader.detect_format(file_path):
                    selected_reader = reader
                    break

            if selected_reader:
                print(f"  ✓ Selected: {type(selected_reader).__name__}")

                # Load and process
                doc = selected_reader.load_data(file_path)
                print(f"  ✓ Loaded: {doc.name} with {len(doc.texts)} text items")

            else:
                print("  ❌ No suitable reader found")

        print("\n✅ Reader factory integration demonstration completed!")

    except ImportError as e:
        print(f"❌ ReaderFactory integration not available: {e}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


def cleanup_sample_files():
    """Clean up created sample files."""
    print("\nCleaning up sample files...")

    sample_files = [
        "sample_text.txt",
        "sample_document.json",
        "sample_document.md",
        "output_plain_text_reader.md",
        "output_simple_json_reader.md",
        "output_markdown_reader.md"
    ]

    for file_path in sample_files:
        try:
            Path(file_path).unlink(missing_ok=True)
            print(f"  ✓ Removed {file_path}")
        except Exception as e:
            print(f"  ❌ Could not remove {file_path}: {e}")


def main():
    """Run custom readers demonstration."""
    print("DocPivot Custom Readers Example\n")
    print("=" * 50)

    try:
        demonstrate_custom_readers()
        demonstrate_reader_factory_integration()

        print("\n" + "=" * 50)
        print("✅ Custom readers demonstration completed!")

        print("\nCustom reader features demonstrated:")
        print("  ✓ BaseReader subclass implementation")
        print("  ✓ Format detection methods")
        print("  ✓ Document loading and conversion")
        print("  ✓ Plain text, JSON, and Markdown readers")
        print("  ✓ Integration with existing serializers")
        print("  ✓ Error handling for unsupported formats")

        # Ask user if they want to clean up
        response = input("\nRemove sample files? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            cleanup_sample_files()
        else:
            print("Sample files preserved for inspection.")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
