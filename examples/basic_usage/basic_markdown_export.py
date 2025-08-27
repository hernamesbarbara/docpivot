#!/usr/bin/env python3
"""Basic Markdown Export Example - PRD Pattern Implementation

This example demonstrates the basic DocPivot workflow from the PRD:
Loading a Docling JSON file and converting it to Markdown.
"""

from docpivot.io.readers import DoclingJsonReader
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer


def main():
    """Demonstrate basic markdown export workflow."""
    print("=== Basic Markdown Export (PRD Example) ===\n")
    
    # PRD Example Implementation:
    # from docpivot.io.readers import DoclingJsonReader
    # from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
    #
    # doc = DoclingJsonReader().load_data("sample.docling.json")
    # serializer = MarkdownDocSerializer(doc=doc)
    # ser_result = serializer.serialize()
    # print(ser_result.text)
    
    try:
        # Load document using DocPivot reader
        print("1. Loading Docling JSON document...")
        doc = DoclingJsonReader().load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")
        print(f"   ✓ Loaded document: {doc.name}")
        print(f"   ✓ Text items: {len(doc.texts)}")
        print(f"   ✓ Tables: {len(doc.tables)}")
        print(f"   ✓ Pictures: {len(doc.pictures)}")
        
        # Serialize to Markdown using Docling's serializer
        print("\n2. Converting to Markdown...")
        serializer = MarkdownDocSerializer(doc=doc)
        ser_result = serializer.serialize()
        
        print(f"   ✓ Generated {len(ser_result.text)} characters of Markdown")
        
        # Display preview
        print("\n3. Markdown Preview:")
        print("-" * 50)
        lines = ser_result.text.split('\n')
        for i, line in enumerate(lines[:20]):  # Show first 20 lines
            print(f"{i+1:2d}: {line}")
        
        if len(lines) > 20:
            print(f"    ... ({len(lines) - 20} more lines)")
        print("-" * 50)
        
        # Save to file
        output_file = "output_basic_markdown.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ser_result.text)
        print(f"\n4. Saved to: {output_file}")
        
        print("\n✅ Basic markdown export completed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Input file not found - {e}")
        print("   Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()