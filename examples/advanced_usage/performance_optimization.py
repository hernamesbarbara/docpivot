#!/usr/bin/env python3
"""Performance Optimization Example - Advanced DocPivot Usage

This example demonstrates techniques for optimizing performance when working
with large documents or batch processing scenarios using DocPivot.
"""

import time
import json
import gc
from pathlib import Path
from memory_profiler import profile
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from docpivot import load_document, load_and_serialize
from docpivot.io.readers import DoclingJsonReader
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer, LexicalParams


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        print(f"⏱️  {self.operation_name}: {duration:.3f} seconds")


def baseline_performance_test():
    """Establish baseline performance metrics."""
    print("=== Baseline Performance Test ===\n")

    sample_file = "data/json/2025-07-03-Test-PDF-Styles.docling.json"

    # Test document loading
    with PerformanceTimer("Document Loading"):
        doc = load_document(sample_file)

    print(f"✓ Loaded document with {len(doc.texts)} text items")

    # Test different serialization formats
    formats = ["markdown", "html", "lexical"]

    for fmt in formats:
        with PerformanceTimer(f"{fmt.capitalize()} Serialization"):
            result = load_and_serialize(sample_file, fmt)
        print(f"✓ {fmt}: {len(result.text)} characters")

    print()


@profile
def memory_optimization_demo():
    """Demonstrate memory optimization techniques."""
    print("=== Memory Optimization Demo ===\n")

    sample_file = "data/json/2025-07-03-Test-PDF-Styles.docling.json"

    # Memory-efficient approach: load once, serialize multiple times
    print("1. Memory-efficient multi-format conversion...")

    with PerformanceTimer("Load Document Once"):
        doc = load_document(sample_file)

    formats = ["markdown", "html", "lexical"]

    for fmt in formats:
        with PerformanceTimer(f"Serialize to {fmt}"):
            from docpivot.io.serializers import SerializerProvider
            provider = SerializerProvider()
            serializer = provider.get_serializer(fmt, doc=doc)
            result = serializer.serialize()

        print(f"✓ {fmt}: {len(result.text)} characters")

        # Force garbage collection between operations
        del result
        del serializer
        gc.collect()

    print()


def lexical_optimization_demo():
    """Demonstrate Lexical JSON serialization optimizations."""
    print("=== Lexical JSON Optimization Demo ===\n")

    sample_file = "data/json/2025-07-03-Test-PDF-Styles.docling.json"
    doc = load_document(sample_file)

    # Configuration 1: Compact output (minimal memory)
    print("1. Compact Configuration (optimized for size)...")
    with PerformanceTimer("Compact Lexical Serialization"):
        compact_params = LexicalParams(
            indent_json=False,  # No indentation saves memory and I/O
            include_metadata=False,  # Skip metadata for smaller output
            preserve_formatting=False  # Skip formatting analysis
        )
        compact_serializer = LexicalDocSerializer(doc=doc, params=compact_params)
        compact_result = compact_serializer.serialize()

    print(f"✓ Compact output: {len(compact_result.text)} characters")

    # Configuration 2: Full-featured (readable but larger)
    print("\n2. Full Configuration (optimized for features)...")
    with PerformanceTimer("Full-featured Lexical Serialization"):
        full_params = LexicalParams(
            indent_json=True,
            include_metadata=True,
            preserve_formatting=True,
            version=2,
            custom_root_attributes={"optimized": True}
        )
        full_serializer = LexicalDocSerializer(doc=doc, params=full_params)
        full_result = full_serializer.serialize()

    print(f"✓ Full-featured output: {len(full_result.text)} characters")

    # Size comparison
    size_ratio = len(full_result.text) / len(compact_result.text)
    print(f"\n📊 Size comparison: Full is {size_ratio:.1f}x larger than compact")

    print()


def streaming_json_optimization():
    """Demonstrate streaming JSON processing for large documents."""
    print("=== Streaming JSON Optimization ===\n")

    sample_file = "data/json/2025-07-03-Test-PDF-Styles.docling.json"

    # Standard approach (loads entire file into memory)
    print("1. Standard JSON Loading...")
    with PerformanceTimer("Standard JSON Load"):
        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

    print(f"✓ Loaded JSON: {len(str(data))} characters in memory")

    # Streaming approach simulation (for very large files)
    print("\n2. Memory-Conscious Loading...")
    with PerformanceTimer("Memory-Conscious Load"):
        # Simulate chunked processing for large files
        reader = DoclingJsonReader()
        doc = reader.load_data(sample_file)

        # Process in chunks to avoid memory spikes
        chunk_size = 1000
        processed_texts = 0

        for i in range(0, len(doc.texts), chunk_size):
            chunk = doc.texts[i:i + chunk_size]
            processed_texts += len(chunk)
            # Simulate processing
            _ = [text.text for text in chunk]

    print(f"✓ Processed {processed_texts} text items in chunks")

    print()


def parallel_processing_demo():
    """Demonstrate parallel processing for batch operations."""
    print("=== Parallel Processing Demo ===\n")

    # Create test scenario with multiple operations
    sample_file = "data/json/2025-07-03-Test-PDF-Styles.docling.json"

    # Operations to perform
    operations = [
        ("markdown", {}),
        ("html", {}),
        ("lexical", {"params": LexicalParams(indent_json=False)}),
        ("lexical", {"params": LexicalParams(indent_json=True, include_metadata=True)}),
    ]

    # Sequential processing (baseline)
    print("1. Sequential Processing...")
    with PerformanceTimer("Sequential Operations"):
        sequential_results = []
        for fmt, kwargs in operations:
            if fmt == "lexical" and "params" in kwargs:
                # Custom Lexical serialization
                doc = load_document(sample_file)
                serializer = LexicalDocSerializer(doc=doc, params=kwargs["params"])
                result = serializer.serialize()
            else:
                result = load_and_serialize(sample_file, fmt, **kwargs)

            sequential_results.append((fmt, len(result.text)))

    # Parallel processing with threads
    print("\n2. Parallel Processing (Threads)...")
    def process_format(args):
        fmt, kwargs = args
        try:
            if fmt == "lexical" and "params" in kwargs:
                doc = load_document(sample_file)
                serializer = LexicalDocSerializer(doc=doc, params=kwargs["params"])
                result = serializer.serialize()
            else:
                result = load_and_serialize(sample_file, fmt, **kwargs)
            return (fmt, len(result.text))
        except Exception as e:
            return (fmt, f"Error: {e}")

    with PerformanceTimer("Parallel Operations (Threads)"):
        with ThreadPoolExecutor(max_workers=4) as executor:
            parallel_results = list(executor.map(process_format, operations))

    # Results comparison
    print("\n📊 Results Comparison:")
    print("Sequential results:")
    for fmt, size in sequential_results:
        print(f"  {fmt}: {size} characters")

    print("\nParallel results:")
    for fmt, size in parallel_results:
        print(f"  {fmt}: {size}")

    print()


def caching_optimization_demo():
    """Demonstrate caching strategies for repeated operations."""
    print("=== Caching Optimization Demo ===\n")

    sample_file = "data/json/2025-07-03-Test-PDF-Styles.docling.json"

    # Scenario: Multiple conversions of the same document
    print("1. Without Caching (load document each time)...")
    formats = ["markdown", "html", "lexical"]

    with PerformanceTimer("No Caching - Multiple Loads"):
        no_cache_results = []
        for fmt in formats:
            result = load_and_serialize(sample_file, fmt)
            no_cache_results.append(len(result.text))

    print(f"✓ Converted to {len(formats)} formats without caching")

    # With document caching
    print("\n2. With Document Caching...")
    with PerformanceTimer("With Caching - Single Load"):
        # Load document once
        cached_doc = load_document(sample_file)

        # Use cached document for multiple serializations
        cached_results = []
        from docpivot.io.serializers import SerializerProvider
        provider = SerializerProvider()

        for fmt in formats:
            serializer = provider.get_serializer(fmt, doc=cached_doc)
            result = serializer.serialize()
            cached_results.append(len(result.text))

    print(f"✓ Converted to {len(formats)} formats with caching")

    # Verify results are identical
    results_match = no_cache_results == cached_results
    print(f"✅ Results verification: {'PASS' if results_match else 'FAIL'}")

    print()


def best_practices_summary():
    """Provide a summary of performance best practices."""
    print("=== Performance Best Practices Summary ===\n")

    practices = [
        ("Document Caching", "Load document once, serialize multiple times"),
        ("Compact Configuration", "Use minimal parameters for smaller output"),
        ("Parallel Processing", "Use threading for I/O-bound batch operations"),
        ("Memory Management", "Explicitly delete large objects and call gc.collect()"),
        ("Streaming Processing", "Process large documents in chunks"),
        ("Format Selection", "Choose the most efficient format for your use case"),
        ("Batch Operations", "Group similar operations to amortize overhead"),
        ("Error Handling", "Implement proper error handling to avoid retries")
    ]

    print("💡 Key optimization strategies:")
    for practice, description in practices:
        print(f"   • {practice}: {description}")

    print("\n📈 Performance impact hierarchy:")
    print("   1. Document caching (highest impact)")
    print("   2. Parallel processing")
    print("   3. Compact configuration")
    print("   4. Memory management")
    print("   5. Streaming/chunking")

    print("\n⚠️  Common performance pitfalls:")
    print("   • Loading the same document multiple times")
    print("   • Using verbose serialization options unnecessarily")
    print("   • Not cleaning up large objects")
    print("   • Processing large batches sequentially")
    print("   • Ignoring memory profiling in production")


def main():
    """Run performance optimization demonstrations."""
    print("DocPivot Performance Optimization Guide\n")
    print("=" * 60)

    try:
        baseline_performance_test()
        memory_optimization_demo()
        lexical_optimization_demo()
        streaming_json_optimization()
        parallel_processing_demo()
        caching_optimization_demo()
        best_practices_summary()

        print("\n" + "=" * 60)
        print("✅ Performance optimization guide completed!")

        print("\n🔧 Tools used in this demo:")
        print("   • PerformanceTimer (custom timing context manager)")
        print("   • memory_profiler (memory usage analysis)")
        print("   • concurrent.futures (parallel processing)")
        print("   • garbage collection (memory management)")

        print("\n📁 Generated files:")
        print("   • Check current directory for any output files")

    except ImportError as e:
        if "memory_profiler" in str(e):
            print("❌ memory_profiler not available. Install with: pip install memory-profiler")
            print("   Running demo without memory profiling...")
            # Re-run without @profile decorator
            main_without_profiling()
        else:
            raise
    except FileNotFoundError as e:
        print(f"❌ Error: Sample file not found - {e}")
        print("   Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


def main_without_profiling():
    """Run demonstrations without memory profiling."""
    baseline_performance_test()
    # Skip memory_optimization_demo() since it uses @profile
    lexical_optimization_demo()
    streaming_json_optimization()
    parallel_processing_demo()
    caching_optimization_demo()
    best_practices_summary()


if __name__ == "__main__":
    main()
