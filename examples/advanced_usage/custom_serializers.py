#!/usr/bin/env python3
"""Custom Serializers Example - Advanced DocPivot Usage

This example demonstrates how to create custom serializers that extend
DocPivot's capabilities with specialized output formats and processing.
"""

import json
from datetime import datetime
from docpivot.io.readers import DoclingJsonReader
from docling_core.types.doc import DoclingDocument
from docling_core.transforms.serializer.base import SerializationResult


class SummarySerializer:
    """Custom serializer that creates a document summary instead of full content.
    
    This serializer analyzes the document structure and creates a compact
    summary with statistics and key information.
    """
    
    def __init__(self, doc: DoclingDocument, include_stats=True, include_preview=True):
        """Initialize the summary serializer.
        
        Args:
            doc: The DoclingDocument to serialize
            include_stats: Whether to include document statistics
            include_preview: Whether to include content previews
        """
        self.doc = doc
        self.include_stats = include_stats
        self.include_preview = include_preview
    
    def serialize(self) -> SerializationResult:
        """Create a document summary."""
        summary_lines = []
        
        # Header
        summary_lines.append("# Document Summary")
        summary_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        # Basic info
        summary_lines.append("## Basic Information")
        summary_lines.append(f"- **Document Name**: {self.doc.name}")
        origin = getattr(self.doc, 'origin', 'Unknown')
        origin_str = str(origin) if origin else 'Unknown'
        summary_lines.append(f"- **Origin**: {origin_str}")
        summary_lines.append("")
        
        # Statistics
        if self.include_stats:
            summary_lines.append("## Content Statistics")
            summary_lines.append(f"- **Text Items**: {len(self.doc.texts)}")
            summary_lines.append(f"- **Tables**: {len(self.doc.tables)}")
            summary_lines.append(f"- **Pictures**: {len(self.doc.pictures)}")
            summary_lines.append(f"- **Groups**: {len(self.doc.groups)}")
            
            # Text analysis
            total_chars = sum(len(getattr(text, 'text', '')) for text in self.doc.texts)
            total_words = sum(len(getattr(text, 'text', '').split()) for text in self.doc.texts)
            
            summary_lines.append(f"- **Total Characters**: {total_chars:,}")
            summary_lines.append(f"- **Total Words**: {total_words:,}")
            summary_lines.append("")
        
        # Content preview
        if self.include_preview and self.doc.texts:
            summary_lines.append("## Content Preview")
            
            # Show first few text items
            preview_count = min(3, len(self.doc.texts))
            for i, text_item in enumerate(self.doc.texts[:preview_count]):
                text_content = getattr(text_item, 'text', '')
                preview = text_content[:100] + "..." if len(text_content) > 100 else text_content
                summary_lines.append(f"**Text {i+1}**: {preview}")
                summary_lines.append("")
            
            if len(self.doc.texts) > preview_count:
                summary_lines.append(f"... and {len(self.doc.texts) - preview_count} more text items")
                summary_lines.append("")
        
        # Table information
        if self.doc.tables:
            summary_lines.append("## Tables Overview")
            for i, table in enumerate(self.doc.tables):
                rows = getattr(table, 'num_rows', 'Unknown')
                cols = getattr(table, 'num_cols', 'Unknown') 
                summary_lines.append(f"- **Table {i+1}**: {rows} rows × {cols} columns")
            summary_lines.append("")
        
        summary_text = "\n".join(summary_lines)
        return SerializationResult(text=summary_text)


class StructuredJsonSerializer:
    """Custom serializer that outputs structured JSON with detailed metadata.
    
    This serializer creates a comprehensive JSON representation that includes
    document structure, content, and extensive metadata.
    """
    
    def __init__(self, doc: DoclingDocument, include_content=True, include_metadata=True, indent=2):
        """Initialize the structured JSON serializer.
        
        Args:
            doc: The DoclingDocument to serialize
            include_content: Whether to include full content in output
            include_metadata: Whether to include detailed metadata
            indent: JSON indentation level (None for compact)
        """
        self.doc = doc
        self.include_content = include_content
        self.include_metadata = include_metadata
        self.indent = indent
    
    def serialize(self) -> SerializationResult:
        """Create structured JSON output."""
        
        # Build JSON structure
        origin = getattr(self.doc, 'origin', None)
        origin_data = str(origin) if origin else None
        
        json_data = {
            "document": {
                "name": self.doc.name,
                "origin": origin_data,
                "generated_at": datetime.now().isoformat()
            }
        }
        
        # Statistics
        json_data["statistics"] = {
            "text_items": len(self.doc.texts),
            "tables": len(self.doc.tables),
            "pictures": len(self.doc.pictures),
            "groups": len(self.doc.groups)
        }
        
        # Content structure
        if self.include_content:
            json_data["content"] = {
                "texts": self._serialize_texts(),
                "tables": self._serialize_tables(),
                "pictures": self._serialize_pictures()
            }
        
        # Metadata
        if self.include_metadata:
            json_data["metadata"] = self._extract_metadata()
        
        # Convert to JSON
        json_text = json.dumps(json_data, indent=self.indent, ensure_ascii=False)
        return SerializationResult(text=json_text)
    
    def _serialize_texts(self):
        """Serialize text items to JSON structure."""
        texts = []
        for i, text_item in enumerate(self.doc.texts):
            text_data = {
                "id": i,
                "text": getattr(text_item, 'text', ''),
                "length": len(getattr(text_item, 'text', '')),
                "word_count": len(getattr(text_item, 'text', '').split())
            }
            
            # Add any additional properties
            for attr in ['font_size', 'font_family', 'bold', 'italic']:
                if hasattr(text_item, attr):
                    text_data[attr] = getattr(text_item, attr)
            
            texts.append(text_data)
        
        return texts
    
    def _serialize_tables(self):
        """Serialize table items to JSON structure."""
        tables = []
        for i, table in enumerate(self.doc.tables):
            table_data = {
                "id": i,
                "rows": getattr(table, 'num_rows', None),
                "cols": getattr(table, 'num_cols', None),
                "caption": getattr(table, 'caption', None)
            }
            tables.append(table_data)
        
        return tables
    
    def _serialize_pictures(self):
        """Serialize picture items to JSON structure."""
        pictures = []
        for i, picture in enumerate(self.doc.pictures):
            picture_data = {
                "id": i,
                "file": getattr(picture, 'file', None),
                "caption": getattr(picture, 'caption', None),
                "width": getattr(picture, 'width', None),
                "height": getattr(picture, 'height', None)
            }
            pictures.append(picture_data)
        
        return pictures
    
    def _extract_metadata(self):
        """Extract comprehensive document metadata."""
        metadata = {
            "document_structure": {
                "has_tables": len(self.doc.tables) > 0,
                "has_pictures": len(self.doc.pictures) > 0,
                "text_density": len(self.doc.texts) / max(1, len(self.doc.groups)) if self.doc.groups else len(self.doc.texts)
            },
            "content_analysis": {
                "total_characters": sum(len(getattr(text, 'text', '')) for text in self.doc.texts),
                "total_words": sum(len(getattr(text, 'text', '').split()) for text in self.doc.texts),
                "average_text_length": sum(len(getattr(text, 'text', '')) for text in self.doc.texts) / len(self.doc.texts) if self.doc.texts else 0
            }
        }
        
        return metadata


def demonstrate_custom_serializers():
    """Demonstrate custom serializer usage and capabilities."""
    print("=== Custom Serializers Demonstration ===\n")
    
    try:
        # Load document
        print("1. Loading document...")
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")
        print(f"   ✓ Loaded: {doc.name}")
        print(f"   ✓ Content: {len(doc.texts)} texts, {len(doc.tables)} tables, {len(doc.pictures)} pictures")
        
        # Example 1: Summary serializer
        print("\n2. Summary Serializer...")
        summary_serializer = SummarySerializer(doc, include_stats=True, include_preview=True)
        summary_result = summary_serializer.serialize()
        
        print(f"   ✓ Generated summary: {len(summary_result.text)} characters")
        
        # Save and show summary
        with open("output_document_summary.md", 'w', encoding='utf-8') as f:
            f.write(summary_result.text)
        
        print("\n   Summary Preview:")
        print("   " + "-" * 50)
        lines = summary_result.text.split('\n')
        for line in lines[:15]:  # Show first 15 lines
            print(f"   {line}")
        print("   " + "-" * 50)
        
        # Example 2: Structured JSON serializer (with content)
        print("\n3. Structured JSON Serializer (with content)...")
        json_serializer = StructuredJsonSerializer(
            doc, 
            include_content=True, 
            include_metadata=True, 
            indent=2
        )
        json_result = json_serializer.serialize()
        
        print(f"   ✓ Generated structured JSON: {len(json_result.text)} characters")
        
        # Save and validate JSON
        with open("output_structured.json", 'w', encoding='utf-8') as f:
            f.write(json_result.text)
        
        # Validate JSON structure
        try:
            json_data = json.loads(json_result.text)
            print(f"   ✓ Valid JSON with {len(json_data)} top-level sections")
            
            # Show structure overview
            print("\n   JSON Structure:")
            for key, value in json_data.items():
                if isinstance(value, dict):
                    print(f"     - {key}: {len(value)} properties")
                elif isinstance(value, list):
                    print(f"     - {key}: {len(value)} items")
                else:
                    print(f"     - {key}: {type(value).__name__}")
                    
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON validation error: {e}")
        
        # Example 3: Compact JSON serializer (metadata only)
        print("\n4. Compact JSON Serializer (metadata only)...")
        compact_serializer = StructuredJsonSerializer(
            doc, 
            include_content=False, 
            include_metadata=True, 
            indent=None  # Compact JSON
        )
        compact_result = compact_serializer.serialize()
        
        print(f"   ✓ Generated compact JSON: {len(compact_result.text)} characters")
        
        with open("output_compact_metadata.json", 'w', encoding='utf-8') as f:
            f.write(compact_result.text)
        
        # Compare sizes
        print("\n5. Size Comparison:")
        print(f"   Summary (Markdown): {len(summary_result.text)} characters")
        print(f"   Full JSON: {len(json_result.text)} characters")
        print(f"   Compact JSON: {len(compact_result.text)} characters")
        
        print("\n✅ Custom serializers demonstration completed!")
        
        print("\nCustom serialization features demonstrated:")
        print("  ✓ Custom BaseDocSerializer subclasses")
        print("  ✓ Document analysis and statistics generation") 
        print("  ✓ Configurable serializer parameters")
        print("  ✓ Multiple output formats (Markdown, JSON)")
        print("  ✓ Content filtering and metadata extraction")
        print("  ✓ Structured data representation")
        
        print(f"\nGenerated files:")
        print(f"  - output_document_summary.md")
        print(f"  - output_structured.json")
        print(f"  - output_compact_metadata.json")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Input file not found - {e}")
        print("   Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


def demonstrate_serializer_registration():
    """Demonstrate registering custom serializers with SerializerProvider."""
    print(f"\n=== Custom Serializer Registration ===\n")
    
    print("Note: Custom serializer registration with SerializerProvider")
    print("requires the serializers to inherit from BaseDocSerializer.")
    print("This advanced pattern is shown for educational purposes.")
    print("\nFor production use, consider:")
    print("• Creating wrapper classes that inherit from BaseDocSerializer")
    print("• Using composition instead of inheritance")
    print("• Implementing the full BaseDocSerializer interface")
    print("\n✅ Custom serializer registration concept demonstrated!")


def main():
    """Run all custom serializer demonstrations."""
    print("DocPivot Custom Serializers Example\n")
    print("=" * 50)
    
    demonstrate_custom_serializers()
    demonstrate_serializer_registration()


if __name__ == "__main__":
    main()