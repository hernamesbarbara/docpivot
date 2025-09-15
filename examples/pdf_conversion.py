#!/usr/bin/env python3
"""PDF to multiple format conversion with DocPivot v2.0.0

This example demonstrates a complete PDF conversion workflow similar to
direct Docling usage, but with DocPivot's simplified API and additional
output format (Lexical).
"""

import os
import sys
import json
import html
from pathlib import Path

# DocPivot simplified API
from docpivot import DocPivotEngine

# Optional Docling imports for PDF conversion
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.document import ConversionResult
    from docling_core.types import DoclingDocument
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False
    print("Error: docling package required for PDF conversion")
    print("Install with: pip install docling")
    sys.exit(1)


def convert_pdf_to_multiple_formats(pdf_path: Path, output_dir: Path):
    """Convert a PDF to Docling JSON, Markdown, and Lexical formats.

    This mirrors the workflow from TEMP_pdf2docling.py but adds
    Lexical format conversion using DocPivot.
    """
    print("=" * 60)
    print(f"Converting: {pdf_path.name}")
    print("=" * 60)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Convert PDF using Docling
    converter = DocumentConverter()
    print(f"\n1. Reading PDF: {pdf_path}")
    conv_result: ConversionResult = converter.convert(str(pdf_path))

    # Get the document and filename
    doc_filename = conv_result.input.file.stem
    dl_doc: DoclingDocument = conv_result.document

    print(f"   ✓ Converted to DoclingDocument")
    print(f"   Document name: {dl_doc.name}")

    # Step 2: Export to Markdown (native Docling)
    print("\n2. Exporting to Markdown (native Docling):")
    output_md = html.unescape(dl_doc.export_to_markdown())

    outfile_md = output_dir / f"{doc_filename}.md"
    with outfile_md.open("w", encoding="utf-8") as fp:
        fp.write(output_md)

    print(f"   ✓ Saved: {outfile_md}")
    print(f"   Size: {len(output_md):,} characters")

    # Show first 500 chars of markdown
    print("\n   Preview (first 500 chars):")
    print("   " + "-" * 40)
    preview = output_md[:500].replace("\n", "\n   ")
    print(f"   {preview}")
    print("   " + "-" * 40)

    # Step 3: Export to Docling JSON (native Docling)
    print("\n3. Exporting to Docling JSON (native Docling):")
    output_json = dl_doc.export_to_dict()

    outfile_json = output_dir / f"{doc_filename}.docling.json"
    with outfile_json.open("w", encoding="utf-8") as fp:
        json.dump(output_json, fp, indent=2)

    print(f"   ✓ Saved: {outfile_json}")
    print(f"   Size: {outfile_json.stat().st_size:,} bytes")

    # Step 4: Export to Lexical JSON using DocPivot
    print("\n4. Exporting to Lexical JSON (via DocPivot):")

    # Create DocPivot engine with pretty printing for readability
    engine = DocPivotEngine(lexical_config={
        "pretty": True,
        "indent": 2,
        "include_metadata": True,
        "handle_images": True,
        "handle_tables": True,
        "handle_lists": True
    })

    # Convert to Lexical format
    result = engine.convert_to_lexical(dl_doc)

    outfile_lexical = output_dir / f"{doc_filename}.lexical.json"
    with outfile_lexical.open("w", encoding="utf-8") as fp:
        fp.write(result.content)

    print(f"   ✓ Saved: {outfile_lexical}")
    print(f"   Size: {len(result.content):,} characters")
    print(f"   Elements: {result.metadata.get('elements_count', 'N/A')}")

    # Show summary
    print("\n" + "=" * 60)
    print("Conversion Summary:")
    print("=" * 60)
    print(f"Input PDF: {pdf_path.name}")
    print(f"\nOutput files in {output_dir}:")
    print(f"  1. {doc_filename}.md (Markdown)")
    print(f"  2. {doc_filename}.docling.json (Docling JSON)")
    print(f"  3. {doc_filename}.lexical.json (Lexical Editor JSON)")

    return {
        "markdown": outfile_md,
        "docling_json": outfile_json,
        "lexical_json": outfile_lexical
    }


def batch_convert_pdfs(input_dir: Path, output_dir: Path):
    """Convert all PDFs in a directory."""
    print("\n" + "=" * 60)
    print("Batch PDF Conversion")
    print("=" * 60)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files to convert\n")

    results = []
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
        print("-" * 40)

        try:
            # Create subdirectory for each PDF's outputs
            pdf_output_dir = output_dir / pdf_path.stem
            outputs = convert_pdf_to_multiple_formats(pdf_path, pdf_output_dir)
            results.append({
                "pdf": pdf_path.name,
                "status": "success",
                "outputs": outputs
            })
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results.append({
                "pdf": pdf_path.name,
                "status": "failed",
                "error": str(e)
            })

    # Print summary
    print("\n" + "=" * 60)
    print("Batch Conversion Complete")
    print("=" * 60)

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]

    print(f"✓ Successful: {len(successful)}")
    for r in successful:
        print(f"  - {r['pdf']}")

    if failed:
        print(f"\n✗ Failed: {len(failed)}")
        for r in failed:
            print(f"  - {r['pdf']}: {r['error']}")


def main():
    """Main entry point demonstrating PDF conversion workflows."""

    if not HAS_DOCLING:
        return

    # Example 1: Single PDF conversion (similar to TEMP_pdf2docling.py)
    print("\n" + "=" * 60)
    print("Example 1: Single PDF Conversion")
    print("=" * 60)

    # You can change this to your PDF path
    pdf_file = Path("data/pdf/email.pdf")

    output_dir = Path("./output/pdf_conversion/")

    if pdf_file.exists():
        convert_pdf_to_multiple_formats(pdf_file, output_dir)
    else:
        print(f"PDF not found: {pdf_file}")
        print("\nTo run this example, place a PDF file at:")
        print(f"  {pdf_file.absolute()}")
        print("\nOr modify the pdf_file path in the script.")

    # Example 2: Batch conversion
    print("\n" + "=" * 60)
    print("Example 2: Batch PDF Conversion")
    print("=" * 60)

    batch_input_dir = Path("data/pdfs/")
    batch_output_dir = Path("./output/batch_pdfs/")

    if batch_input_dir.exists():
        batch_convert_pdfs(batch_input_dir, batch_output_dir)
    else:
        print(f"Batch input directory not found: {batch_input_dir}")
        print("\nTo run batch conversion, create the directory and add PDFs:")
        print(f"  mkdir -p {batch_input_dir}")
        print(f"  cp your_pdfs/*.pdf {batch_input_dir}/")

    print("\n" + "=" * 60)
    print("Key Features Demonstrated:")
    print("=" * 60)
    print("• Direct PDF to multiple format conversion")
    print("• Native Docling Markdown export")
    print("• Native Docling JSON export")
    print("• DocPivot Lexical JSON export")
    print("• Batch processing of multiple PDFs")
    print("• Organized output directory structure")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
