#!/usr/bin/env python3
"""Basic usage examples for DocPivot v2.0.0

This example demonstrates the simplified DocPivotEngine API for
common document conversion tasks.
"""

from pathlib import Path

from docpivot import DocPivotEngine

# Optional imports for different input types
try:
    from docling_core.types import DoclingDocument
    HAS_DOCLING_CORE = True
except ImportError:
    HAS_DOCLING_CORE = False

try:
    from docling.document_converter import DocumentConverter
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False


def example_1_simple_conversion():
    """Example 1: Simplest possible conversion."""
    print("\n" + "=" * 60)
    print("Example 1: Simple Conversion")
    print("=" * 60)

    # Create engine with defaults
    engine = DocPivotEngine()

    # Convert a DoclingDocument (if you have one)
    if HAS_DOCLING_CORE:
        # In real usage, you'd have a DoclingDocument from docling
        # For demo, we'll create a mock one
        doc = DoclingDocument(name="sample.pdf")

        # One-line conversion!
        result = engine.convert_to_lexical(doc)

        print(f"✓ Converted to {result.format}")
        print(f"✓ Content length: {len(result.content)} characters")
    else:
        print("ℹ️  Install docling-core to run this example")


def example_2_file_conversion():
    """Example 2: Convert files directly."""
    print("\n" + "=" * 60)
    print("Example 2: File Conversion")
    print("=" * 60)

    engine = DocPivotEngine()

    # Convert from a Docling JSON file
    input_file = Path("data/sample.docling.json")
    if input_file.exists():
        result = engine.convert_file(input_file)
        print(f"✓ Converted {input_file.name}")
        print(f"✓ Format: {result.format}")
        print(f"✓ Elements: {result.metadata.get('elements_count', 'N/A')}")
    else:
        print(f"ℹ️  Sample file not found: {input_file}")

    # Convert and save to a specific output file
    output_file = Path("output/converted.lexical.json")
    if input_file.exists():
        output_file.parent.mkdir(parents=True, exist_ok=True)
        result = engine.convert_file(
            input_file,
            output_path=output_file,
            pretty=True  # Make output human-readable
        )
        print(f"✓ Saved to: {result.metadata['output_path']}")


def example_3_pdf_conversion():
    """Example 3: Direct PDF conversion (requires docling)."""
    print("\n" + "=" * 60)
    print("Example 3: PDF Conversion")
    print("=" * 60)

    if not HAS_DOCLING:
        print("ℹ️  Install docling package for PDF conversion:")
        print("    pip install docling")
        return

    engine = DocPivotEngine()

    pdf_file = Path("data/sample.pdf")
    if pdf_file.exists():
        # Convert PDF directly
        result = engine.convert_pdf(pdf_file)

        print(f"✓ Converted PDF: {pdf_file.name}")
        print(f"✓ Format: {result.format}")
        print(f"✓ Document name: {result.metadata.get('document_name', 'N/A')}")

        # Save with pretty printing
        output = Path("output/from_pdf.lexical.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result.content)
        print(f"✓ Saved to: {output}")
    else:
        print(f"ℹ️  Sample PDF not found: {pdf_file}")


def example_4_custom_configuration():
    """Example 4: Custom configuration."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Configuration")
    print("=" * 60)

    # Create engine with custom settings
    engine = DocPivotEngine(
        lexical_config={
            "pretty": True,
            "indent": 4,
            "include_metadata": True,
            "handle_images": True,
            "handle_tables": True,
            "handle_lists": True
        }
    )

    print("✓ Created engine with custom configuration:")
    print("  - Pretty printing with 4-space indent")
    print("  - Including metadata")
    print("  - Handling images, tables, and lists")

    # Use it for conversion
    if HAS_DOCLING_CORE:
        doc = DoclingDocument(name="custom_example")
        result = engine.convert_to_lexical(doc)
        print("✓ Converted with custom settings")


def example_5_pretty_printing():
    """Example 5: Pretty printing for debugging."""
    print("\n" + "=" * 60)
    print("Example 5: Pretty Printing")
    print("=" * 60)

    engine = DocPivotEngine()

    if HAS_DOCLING_CORE:
        doc = DoclingDocument(name="debug_example")

        # Convert with pretty printing for debugging
        result = engine.convert_to_lexical(doc, pretty=True, indent=2)

        print("✓ Pretty-printed output (first 300 chars):")
        print("-" * 40)
        print(result.content[:300])
        print("-" * 40)
    else:
        print("ℹ️  Install docling-core to run this example")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("DocPivot v2.0.0 - Basic Usage Examples")
    print("=" * 60)

    example_1_simple_conversion()
    example_2_file_conversion()
    example_3_pdf_conversion()
    example_4_custom_configuration()
    example_5_pretty_printing()

    print("\n" + "=" * 60)
    print("Key Takeaways:")
    print("=" * 60)
    print("• One-line conversion: engine.convert_to_lexical(doc)")
    print("• Direct file support: engine.convert_file(path)")
    print("• PDF support: engine.convert_pdf(path)")
    print("• Smart defaults work for 90% of use cases")
    print("• Easy customization when needed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
