#!/usr/bin/env python3
"""Advanced usage examples for DocPivot v2.0.0

This example demonstrates advanced features including batch processing,
custom configurations, and integration patterns.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from docpivot import DocPivotEngine, get_performance_config, get_debug_config

# Optional imports
try:
    from docling_core.types import DoclingDocument
    HAS_DOCLING_CORE = True
except ImportError:
    HAS_DOCLING_CORE = False


def batch_processing_example():
    """Process multiple files in batch."""
    print("\n" + "=" * 60)
    print("Batch Processing Example")
    print("=" * 60)

    # Use performance configuration for batch processing
    engine = DocPivotEngine(lexical_config=get_performance_config())

    # Find all Docling JSON files
    input_dir = Path("data")
    output_dir = Path("output/batch")
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(input_dir.glob("*.docling.json"))
    if not json_files:
        print(f"ℹ️  No .docling.json files found in {input_dir}")
        return

    print(f"Found {len(json_files)} files to process")

    # Process each file
    results = []
    for input_file in json_files:
        try:
            # Define output path
            output_file = output_dir / f"{input_file.stem}.lexical.json"

            # Convert file
            result = engine.convert_file(
                input_file,
                output_path=output_file
            )

            results.append({
                "input": input_file.name,
                "output": output_file.name,
                "size": len(result.content),
                "elements": result.metadata.get("elements_count", 0)
            })

            print(f"✓ Processed: {input_file.name}")

        except Exception as e:
            print(f"✗ Failed: {input_file.name} - {e}")

    # Summary
    if results:
        print("\nBatch Processing Summary:")
        print("-" * 40)
        for r in results:
            print(f"  {r['input']} → {r['output']}")
            print(f"    Size: {r['size']:,} bytes, Elements: {r['elements']}")


def debug_mode_example():
    """Use debug configuration for troubleshooting."""
    print("\n" + "=" * 60)
    print("Debug Mode Example")
    print("=" * 60)

    # Create engine with debug configuration
    engine = DocPivotEngine(lexical_config=get_debug_config())

    print("Debug configuration enabled:")
    print("  • Pretty printing: ON")
    print("  • Full metadata: ON")
    print("  • 4-space indentation")
    print("  • All content types enabled")

    if HAS_DOCLING_CORE:
        # Create a sample document
        doc = DoclingDocument(name="debug_test")

        # Convert with full debug output
        result = engine.convert_to_lexical(doc)

        # Show metadata
        print("\nDocument Metadata:")
        for key, value in result.metadata.items():
            print(f"  {key}: {value}")

        # Show formatted output sample
        print("\nFormatted Output (first 500 chars):")
        print("-" * 40)
        print(result.content[:500])
    else:
        print("ℹ️  Install docling-core to run this example")


def custom_processing_pipeline():
    """Build a custom document processing pipeline."""
    print("\n" + "=" * 60)
    print("Custom Processing Pipeline")
    print("=" * 60)

    class DocumentProcessor:
        """Custom processor with pre/post processing."""

        def __init__(self):
            self.engine = DocPivotEngine()
            self.stats = {"processed": 0, "failed": 0}

        def preprocess(self, file_path: Path) -> Dict[str, Any]:
            """Validate and prepare file."""
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            file_size = file_path.stat().st_size
            if file_size > 10_000_000:  # 10MB limit
                raise ValueError(f"File too large: {file_size} bytes")

            return {"file": file_path, "size": file_size}

        def process(self, file_path: Path) -> Dict[str, Any]:
            """Process the document."""
            # Preprocess
            info = self.preprocess(file_path)

            # Convert
            result = self.engine.convert_file(file_path)

            # Postprocess
            return self.postprocess(result, info)

        def postprocess(self, result, info: Dict[str, Any]) -> Dict[str, Any]:
            """Enhance results with additional metadata."""
            self.stats["processed"] += 1

            # Parse content to get statistics
            try:
                content_data = json.loads(result.content)
                node_count = self._count_nodes(content_data)
            except:
                node_count = 0

            return {
                "file": info["file"].name,
                "original_size": info["size"],
                "converted_size": len(result.content),
                "compression_ratio": len(result.content) / info["size"]
                if info["size"] > 0 else 0,
                "node_count": node_count,
                "format": result.format
            }

        def _count_nodes(self, data: Any) -> int:
            """Recursively count nodes in the Lexical structure."""
            if isinstance(data, dict):
                count = 1
                for value in data.values():
                    count += self._count_nodes(value)
                return count
            elif isinstance(data, list):
                return sum(self._count_nodes(item) for item in data)
            return 0

    # Use the custom processor
    processor = DocumentProcessor()

    # Process a sample file
    sample = Path("data/sample.docling.json")
    if sample.exists():
        try:
            result = processor.process(sample)
            print("Pipeline Results:")
            print("-" * 40)
            for key, value in result.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        except Exception as e:
            print(f"✗ Pipeline failed: {e}")
    else:
        print(f"ℹ️  Sample file not found: {sample}")


def memory_efficient_processing():
    """Process large documents with memory efficiency."""
    print("\n" + "=" * 60)
    print("Memory-Efficient Processing")
    print("=" * 60)

    # Use minimal configuration for memory efficiency
    from docpivot import get_minimal_config

    engine = DocPivotEngine(lexical_config=get_minimal_config())

    print("Using minimal configuration:")
    print("  • No pretty printing")
    print("  • Minimal metadata")
    print("  • Optimized for large documents")

    # Process large file if available
    large_file = Path("data/large_document.docling.json")
    if large_file.exists():
        try:
            # Convert without loading entire result into memory
            output_path = Path("output/large_converted.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            result = engine.convert_file(
                large_file,
                output_path=output_path
            )

            file_size_mb = output_path.stat().st_size / 1_000_000
            print(f"✓ Processed large file: {file_size_mb:.2f} MB")
            print(f"✓ Output saved to: {output_path}")

        except Exception as e:
            print(f"✗ Failed to process: {e}")
    else:
        print(f"ℹ️  Large file not found: {large_file}")
        print("  This example would process files efficiently")
        print("  by streaming to disk instead of memory")


def error_handling_example():
    """Demonstrate proper error handling."""
    print("\n" + "=" * 60)
    print("Error Handling Example")
    print("=" * 60)

    engine = DocPivotEngine()

    # Example 1: Handle missing file
    try:
        result = engine.convert_file("non_existent.json")
    except FileNotFoundError as e:
        print(f"✓ Caught FileNotFoundError: {e}")

    # Example 2: Handle invalid format
    invalid_file = Path("data/invalid.txt")
    if invalid_file.exists():
        try:
            result = engine.convert_file(invalid_file)
        except Exception as e:
            print(f"✓ Caught format error: {type(e).__name__}")

    # Example 3: Handle PDF without docling
    if not HAS_DOCLING_CORE:
        try:
            result = engine.convert_pdf("sample.pdf")
        except ImportError as e:
            print(f"✓ Caught ImportError for PDF: Package not installed")

    print("\nError handling patterns:")
    print("  • Always wrap conversions in try-except")
    print("  • Check file existence before processing")
    print("  • Validate input formats")
    print("  • Handle missing dependencies gracefully")


def main():
    """Run all advanced examples."""
    print("\n" + "=" * 60)
    print("DocPivot v2.0.0 - Advanced Usage Examples")
    print("=" * 60)

    batch_processing_example()
    debug_mode_example()
    custom_processing_pipeline()
    memory_efficient_processing()
    error_handling_example()

    print("\n" + "=" * 60)
    print("Advanced Features Summary:")
    print("=" * 60)
    print("• Batch processing with performance config")
    print("• Debug mode for troubleshooting")
    print("• Custom processing pipelines")
    print("• Memory-efficient large file handling")
    print("• Comprehensive error handling")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()