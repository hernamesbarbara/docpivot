#!/usr/bin/env python3
"""Customized Markdown Export Example - PRD Pattern Implementation

This example demonstrates customized markdown serialization using:
- Custom table serializers
- Parameter objects (MarkdownParams)
- Component serializer configuration
"""

from docpivot.io.readers import DoclingJsonReader
from docling_core.transforms.chunker.hierarchical_chunker import TripletTableSerializer
from docling_core.transforms.serializer.markdown import MarkdownParams, MarkdownDocSerializer


def main():
    """Demonstrate customized markdown export with parameters and component serializers."""
    print("=== Customized Markdown Export (PRD Example) ===\n")

    # PRD Example Implementation:
    # from docling_core.transforms.chunker.hierarchical_chunker import TripletTableSerializer
    # from docling_core.transforms.serializer.markdown import MarkdownParams, MarkdownDocSerializer
    #
    # serializer = MarkdownDocSerializer(
    #     doc=doc,
    #     table_serializer=TripletTableSerializer(),
    #     params=MarkdownParams(image_placeholder="(no image)")
    # )
    # ser_result = serializer.serialize()
    # print(ser_result.text)

    try:
        # Load document
        print("1. Loading Docling JSON document...")
        doc = DoclingJsonReader().load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")
        print(f"   ✓ Loaded document: {doc.name}")
        print(f"   ✓ Text items: {len(doc.texts)}")
        print(f"   ✓ Tables: {len(doc.tables)}")
        print(f"   ✓ Pictures: {len(doc.pictures)}")

        # Example 1: Basic customization with parameters
        print("\n2. Basic Customization with MarkdownParams...")
        basic_params = MarkdownParams(image_placeholder="(no image)")
        basic_serializer = MarkdownDocSerializer(
            doc=doc,
            params=basic_params
        )
        basic_result = basic_serializer.serialize()
        print(f"   ✓ Generated {len(basic_result.text)} characters")

        # Example 2: Advanced customization with component serializers
        print("\n3. Advanced Customization with TripletTableSerializer...")
        advanced_serializer = MarkdownDocSerializer(
            doc=doc,
            table_serializer=TripletTableSerializer(),
            params=MarkdownParams(image_placeholder="(no image)")
        )
        advanced_result = advanced_serializer.serialize()
        print(f"   ✓ Generated {len(advanced_result.text)} characters")

        # Example 3: Full customization
        print("\n4. Full Customization Example...")
        full_params = MarkdownParams(
            image_placeholder="[Image not available]",
            strict_text_mode=False
        )
        full_serializer = MarkdownDocSerializer(
            doc=doc,
            table_serializer=TripletTableSerializer(),
            params=full_params
        )
        full_result = full_serializer.serialize()
        print(f"   ✓ Generated {len(full_result.text)} characters")

        # Compare outputs
        print("\n5. Output Comparison:")
        print(f"   Basic customization: {len(basic_result.text)} characters")
        print(f"   Advanced (with table serializer): {len(advanced_result.text)} characters")
        print(f"   Full customization: {len(full_result.text)} characters")

        # Show a preview of the customized output
        print("\n6. Customized Markdown Preview:")
        print("-" * 50)
        lines = advanced_result.text.split('\n')
        for i, line in enumerate(lines[:15]):  # Show first 15 lines
            print(f"{i+1:2d}: {line}")

        if len(lines) > 15:
            print(f"    ... ({len(lines) - 15} more lines)")
        print("-" * 50)

        # Save outputs
        outputs = [
            ("output_basic_customized_markdown.md", basic_result.text),
            ("output_advanced_customized_markdown.md", advanced_result.text),
            ("output_full_customized_markdown.md", full_result.text)
        ]

        for filename, content in outputs:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   Saved: {filename}")

        print("\n✅ Customized markdown export completed successfully!")
        print("\nCustomization features demonstrated:")
        print("  ✓ MarkdownParams for basic configuration")
        print("  ✓ TripletTableSerializer for advanced table handling")
        print("  ✓ Custom image placeholders")
        print("  ✓ Component serializer integration")

    except FileNotFoundError as e:
        print(f"❌ Error: Input file not found - {e}")
        print("   Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
