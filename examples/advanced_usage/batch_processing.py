#!/usr/bin/env python3
"""Batch Processing Example - Advanced DocPivot Usage

This example demonstrates batch processing capabilities for converting
multiple documents and formats efficiently.
"""

import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from docpivot import load_and_serialize, load_document
from docpivot.io.serializers import SerializerProvider
from docling_core.transforms.serializer.markdown import MarkdownParams


def process_single_file(input_file, output_format, output_dir="batch_output"):
    """Process a single file conversion.

    Args:
        input_file: Path to input file
        output_format: Target format (markdown, html, lexical, etc.)
        output_dir: Directory for output files

    Returns:
        dict: Processing result with file info and status
    """
    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(exist_ok=True)

        # Convert document
        result = load_and_serialize(input_file, output_format)

        # Generate output filename
        input_path = Path(input_file)
        output_filename = f"{input_path.stem}_{output_format}.{_get_extension(output_format)}"
        output_file = Path(output_dir) / output_filename

        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.text)

        return {
            "input_file": input_file,
            "output_file": str(output_file),
            "format": output_format,
            "status": "success",
            "size": len(result.text),
            "error": None
        }

    except Exception as e:
        return {
            "input_file": input_file,
            "output_file": None,
            "format": output_format,
            "status": "error",
            "size": 0,
            "error": str(e)
        }


def _get_extension(format_name):
    """Get appropriate file extension for format."""
    extensions = {
        "markdown": "md",
        "html": "html",
        "lexical": "json",
        "text": "txt",
        "doctags": "xml"
    }
    return extensions.get(format_name, "txt")


def batch_process_parallel(input_files, output_formats, max_workers=4):
    """Process multiple files in parallel.

    Args:
        input_files: List of input file paths
        output_formats: List of target formats
        max_workers: Maximum number of parallel workers

    Returns:
        list: Processing results for all combinations
    """
    print("=== Parallel Batch Processing ===")
    print(f"Files: {len(input_files)}, Formats: {len(output_formats)}")
    print(f"Total tasks: {len(input_files) * len(output_formats)}")
    print(f"Max workers: {max_workers}\n")

    # Create all file-format combinations
    tasks = []
    for input_file in input_files:
        for output_format in output_formats:
            tasks.append((input_file, output_format))

    results = []

    # Process with thread pool
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(process_single_file, input_file, output_format): (input_file, output_format)
            for input_file, output_format in tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_task):
            input_file, output_format = future_to_task[future]
            try:
                result = future.result()
                results.append(result)

                if result["status"] == "success":
                    print(f"✓ {Path(input_file).name} → {output_format} ({result['size']} chars)")
                else:
                    print(f"❌ {Path(input_file).name} → {output_format}: {result['error']}")

            except Exception as e:
                print(f"❌ {Path(input_file).name} → {output_format}: Executor error: {e}")

    return results


def batch_process_with_custom_config(input_files):
    """Demonstrate batch processing with custom serializer configurations.

    Args:
        input_files: List of input file paths
    """
    print("\n=== Custom Configuration Batch Processing ===\n")

    # Define different configurations for different use cases
    configurations = [
        {
            "name": "web_optimized",
            "format": "html",
            "description": "HTML optimized for web display"
        },
        {
            "name": "print_ready",
            "format": "markdown",
            "description": "Markdown optimized for printing",
            "params": MarkdownParams(image_placeholder="[Print Version - Image Omitted]")
        },
        {
            "name": "compact_lexical",
            "format": "lexical",
            "description": "Compact Lexical JSON"
        }
    ]

    results = {}

    for input_file in input_files:
        print(f"Processing: {Path(input_file).name}")
        file_results = {}

        try:
            # Load document once
            doc = load_document(input_file)

            # Apply each configuration
            for config in configurations:
                try:
                    # Get configured serializer
                    provider = SerializerProvider()
                    serializer_kwargs = {"doc": doc}

                    if "params" in config:
                        serializer_kwargs["params"] = config["params"]

                    serializer = provider.get_serializer(
                        config["format"],
                        **serializer_kwargs
                    )

                    # Serialize
                    result = serializer.serialize()

                    # Save output
                    output_dir = Path("batch_output") / "custom_configs"
                    output_dir.mkdir(parents=True, exist_ok=True)

                    input_stem = Path(input_file).stem
                    output_file = output_dir / f"{input_stem}_{config['name']}.{_get_extension(config['format'])}"

                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result.text)

                    file_results[config["name"]] = {
                        "status": "success",
                        "size": len(result.text),
                        "output_file": str(output_file),
                        "description": config["description"]
                    }

                    print(f"  ✓ {config['name']}: {len(result.text)} chars → {output_file.name}")

                except Exception as e:
                    file_results[config["name"]] = {
                        "status": "error",
                        "error": str(e),
                        "description": config["description"]
                    }
                    print(f"  ❌ {config['name']}: {e}")

            results[input_file] = file_results

        except Exception as e:
            print(f"  ❌ Failed to load document: {e}")
            results[input_file] = {"error": f"Document load failed: {e}"}

    return results


def analyze_batch_results(results):
    """Analyze and summarize batch processing results.

    Args:
        results: List of processing results from batch operations
    """
    print("\n=== Batch Processing Analysis ===\n")

    # Count successes and failures
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]

    print("Summary:")
    print(f"  ✓ Successful conversions: {len(successful)}")
    print(f"  ❌ Failed conversions: {len(failed)}")
    print(f"  📊 Success rate: {len(successful) / len(results) * 100:.1f}%")

    if successful:
        # Analyze by format
        format_stats = {}
        for result in successful:
            fmt = result["format"]
            if fmt not in format_stats:
                format_stats[fmt] = {"count": 0, "total_size": 0, "sizes": []}

            format_stats[fmt]["count"] += 1
            format_stats[fmt]["total_size"] += result["size"]
            format_stats[fmt]["sizes"].append(result["size"])

        print("\nFormat Statistics:")
        for fmt, stats in format_stats.items():
            avg_size = stats["total_size"] / stats["count"]
            min_size = min(stats["sizes"])
            max_size = max(stats["sizes"])

            print(f"  {fmt}:")
            print(f"    Conversions: {stats['count']}")
            print(f"    Average size: {avg_size:.0f} characters")
            print(f"    Size range: {min_size} - {max_size} characters")

    if failed:
        print("\nError Analysis:")
        error_types = {}
        for result in failed:
            error_msg = result["error"]
            error_type = error_msg.split(":")[0] if ":" in error_msg else error_msg
            error_types[error_type] = error_types.get(error_type, 0) + 1

        for error_type, count in error_types.items():
            print(f"  {error_type}: {count} occurrences")


def main():
    """Demonstrate comprehensive batch processing workflows."""
    print("DocPivot Batch Processing Example\n")
    print("=" * 50)

    # Define input files (adjust paths as needed)
    input_files = [
        "data/json/2025-07-03-Test-PDF-Styles.docling.json"
    ]

    # Check if input files exist
    existing_files = [f for f in input_files if os.path.exists(f)]

    if not existing_files:
        print("❌ No input files found. Please ensure sample files are available.")
        print("Expected files:")
        for f in input_files:
            print(f"  - {f}")
        return

    print(f"Found {len(existing_files)} input file(s) to process\n")

    # Example 1: Parallel processing multiple formats
    output_formats = ["markdown", "html", "lexical"]

    parallel_results = batch_process_parallel(existing_files, output_formats)
    analyze_batch_results(parallel_results)

    # Example 2: Custom configuration processing
    custom_results = batch_process_with_custom_config(existing_files)

    print("\n✅ Batch processing demonstration completed!")
    print("\nOutput directories created:")
    print("  - batch_output/")
    print("  - batch_output/custom_configs/")

    print("\nBatch processing features demonstrated:")
    print("  ✓ Parallel processing with ThreadPoolExecutor")
    print("  ✓ Multiple input files and output formats")
    print("  ✓ Custom serializer configurations")
    print("  ✓ Error handling and reporting")
    print("  ✓ Results analysis and statistics")
    print("  ✓ Organized output directory structure")


if __name__ == "__main__":
    main()
