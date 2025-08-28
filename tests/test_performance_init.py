"""Tests for docpivot.performance.__init__ module.

This test module focuses on testing the lazy import functions and __getattr__ method
that were not previously covered, improving the overall test coverage.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys

from docpivot.performance import (
    PerformanceMonitor,
    PerformanceConfig,
    PerformanceMetrics,
    MemoryProfiler,
    MemoryUsage,
    MemoryReport,
)

# Import the module to access the functions
import docpivot.performance as perf_module


class TestPerformanceLazyImports(unittest.TestCase):
    """Test the lazy import functions in the performance __init__ module."""

    def test_get_benchmark_suite(self):
        """Test the get_benchmark_suite lazy import function."""
        BenchmarkSuite = perf_module.get_benchmark_suite()

        # Verify it returns the correct class
        self.assertIsNotNone(BenchmarkSuite)
        self.assertEqual(BenchmarkSuite.__name__, "BenchmarkSuite")

        # Verify it's the same class from direct import
        from docpivot.performance.benchmarks import BenchmarkSuite as DirectBenchmarkSuite
        self.assertIs(BenchmarkSuite, DirectBenchmarkSuite)

    def test_get_reader_benchmark(self):
        """Test the get_reader_benchmark lazy import function."""
        ReaderBenchmark = perf_module.get_reader_benchmark()

        # Verify it returns the correct class
        self.assertIsNotNone(ReaderBenchmark)
        self.assertEqual(ReaderBenchmark.__name__, "ReaderBenchmark")

        # Verify it's the same class from direct import
        from docpivot.performance.benchmarks import ReaderBenchmark as DirectReaderBenchmark
        self.assertIs(ReaderBenchmark, DirectReaderBenchmark)

    def test_get_serializer_benchmark(self):
        """Test the get_serializer_benchmark lazy import function."""
        SerializerBenchmark = perf_module.get_serializer_benchmark()

        # Verify it returns the correct class
        self.assertIsNotNone(SerializerBenchmark)
        self.assertEqual(SerializerBenchmark.__name__, "SerializerBenchmark")

        # Verify it's the same class from direct import
        from docpivot.performance.benchmarks import SerializerBenchmark as DirectSerializerBenchmark
        self.assertIs(SerializerBenchmark, DirectSerializerBenchmark)

    def test_multiple_calls_return_same_class(self):
        """Test that multiple calls to lazy import functions return the same class."""
        # Call each function twice
        suite1 = perf_module.get_benchmark_suite()
        suite2 = perf_module.get_benchmark_suite()

        reader1 = perf_module.get_reader_benchmark()
        reader2 = perf_module.get_reader_benchmark()

        serializer1 = perf_module.get_serializer_benchmark()
        serializer2 = perf_module.get_serializer_benchmark()

        # Verify same class is returned
        self.assertIs(suite1, suite2)
        self.assertIs(reader1, reader2)
        self.assertIs(serializer1, serializer2)


class TestPerformanceGetattr(unittest.TestCase):
    """Test the __getattr__ method for lazy imports."""

    def test_getattr_benchmark_suite(self):
        """Test __getattr__ for BenchmarkSuite."""
        # Access the attribute through getattr
        BenchmarkSuite = perf_module.BenchmarkSuite

        # Verify it returns the correct class
        self.assertIsNotNone(BenchmarkSuite)
        self.assertEqual(BenchmarkSuite.__name__, "BenchmarkSuite")

        # Verify it's the same class from direct import
        from docpivot.performance.benchmarks import BenchmarkSuite as DirectBenchmarkSuite
        self.assertIs(BenchmarkSuite, DirectBenchmarkSuite)

    def test_getattr_reader_benchmark(self):
        """Test __getattr__ for ReaderBenchmark."""
        # Access the attribute through getattr
        ReaderBenchmark = perf_module.ReaderBenchmark

        # Verify it returns the correct class
        self.assertIsNotNone(ReaderBenchmark)
        self.assertEqual(ReaderBenchmark.__name__, "ReaderBenchmark")

        # Verify it's the same class from direct import
        from docpivot.performance.benchmarks import ReaderBenchmark as DirectReaderBenchmark
        self.assertIs(ReaderBenchmark, DirectReaderBenchmark)

    def test_getattr_serializer_benchmark(self):
        """Test __getattr__ for SerializerBenchmark."""
        # Access the attribute through getattr
        SerializerBenchmark = perf_module.SerializerBenchmark

        # Verify it returns the correct class
        self.assertIsNotNone(SerializerBenchmark)
        self.assertEqual(SerializerBenchmark.__name__, "SerializerBenchmark")

        # Verify it's the same class from direct import
        from docpivot.performance.benchmarks import SerializerBenchmark as DirectSerializerBenchmark
        self.assertIs(SerializerBenchmark, DirectSerializerBenchmark)

    def test_getattr_invalid_attribute(self):
        """Test __getattr__ raises AttributeError for invalid attributes."""
        with self.assertRaises(AttributeError) as context:
            _ = perf_module.NonExistentClass

        self.assertIn("module 'docpivot.performance' has no attribute 'NonExistentClass'",
                      str(context.exception))

    def test_getattr_various_invalid_names(self):
        """Test __getattr__ with various invalid attribute names."""
        invalid_names = [
            "InvalidClass",
            "test_attribute",
            "_private_attr",
            "__dunder_attr__",
            "12345",
            "benchmark_suite",  # lowercase
            "BENCHMARKSUITE",   # all caps
        ]

        for name in invalid_names:
            with self.assertRaises(AttributeError) as context:
                getattr(perf_module, name)

            self.assertIn(f"module 'docpivot.performance' has no attribute '{name}'",
                          str(context.exception))

    def test_getattr_caching_behavior(self):
        """Test that __getattr__ properly integrates with module caching."""
        # First access through __getattr__
        BenchmarkSuite1 = perf_module.BenchmarkSuite

        # Second access should use cached value
        BenchmarkSuite2 = perf_module.BenchmarkSuite

        # They should be the same object
        self.assertIs(BenchmarkSuite1, BenchmarkSuite2)


class TestPerformanceModuleImports(unittest.TestCase):
    """Test that all advertised exports are accessible."""

    def test_all_exports(self):
        """Test that all items in __all__ are importable."""
        expected_exports = [
            "PerformanceMonitor",
            "PerformanceConfig",
            "PerformanceMetrics",
            "MemoryProfiler",
            "MemoryUsage",
            "MemoryReport",
            "BenchmarkSuite",
            "ReaderBenchmark",
            "SerializerBenchmark",
        ]

        # Verify __all__ contains expected exports
        self.assertEqual(set(perf_module.__all__), set(expected_exports))

        # Verify all exports are accessible
        for export_name in expected_exports:
            self.assertTrue(hasattr(perf_module, export_name),
                            f"Module should have attribute '{export_name}'")

            # Get the attribute
            attr = getattr(perf_module, export_name)
            self.assertIsNotNone(attr, f"Attribute '{export_name}' should not be None")

    def test_direct_imports_work(self):
        """Test that direct imports from the module work correctly."""
        # These should already be imported at module level
        self.assertIsNotNone(PerformanceMonitor)
        self.assertIsNotNone(PerformanceConfig)
        self.assertIsNotNone(PerformanceMetrics)
        self.assertIsNotNone(MemoryProfiler)
        self.assertIsNotNone(MemoryUsage)
        self.assertIsNotNone(MemoryReport)

    def test_lazy_imports_consistency(self):
        """Test that lazy imports via functions match __getattr__ access."""
        # Get classes via functions
        suite_func = perf_module.get_benchmark_suite()
        reader_func = perf_module.get_reader_benchmark()
        serializer_func = perf_module.get_serializer_benchmark()

        # Get classes via __getattr__
        suite_attr = perf_module.BenchmarkSuite
        reader_attr = perf_module.ReaderBenchmark
        serializer_attr = perf_module.SerializerBenchmark

        # They should be the same objectts
        self.assertIs(suite_func, suite_attr)
        self.assertIs(reader_func, reader_attr)
        self.assertIs(serializer_func, serializer_attr)


class TestCircularDependencyPrevention(unittest.TestCase):
    """Test that lazy imports prevent circular dependencies."""

    def test_import_order_independence(self):
        """Test that imports work regardless of order."""
        # Clear the module from cache to test fresh import
        module_name = 'docpivot.performance'
        if module_name in sys.modules:
            # Store the original module
            original_module = sys.modules[module_name]

            # Remove from cache temporarily
            del sys.modules[module_name]

            try:
                # Re-import the module
                import docpivot.performance as fresh_perf_module

                # Test that lazy imports still work
                BenchmarkSuite = fresh_perf_module.get_benchmark_suite()
                self.assertIsNotNone(BenchmarkSuite)

                # Test __getattr__ still works
                ReaderBenchmark = fresh_perf_module.ReaderBenchmark
                self.assertIsNotNone(ReaderBenchmark)

            finally:
                # Restore the original module
                sys.modules[module_name] = original_module

    @patch('docpivot.performance.benchmarks.BenchmarkSuite')
    def test_lazy_import_with_mocked_class(self, mock_benchmark_suite):
        """Test lazy import behavior with mocked classes."""
        # Configure the mock
        mock_benchmark_suite.__name__ = "BenchmarkSuite"

        # The get function should still work
        suite = perf_module.get_benchmark_suite()
        self.assertIsNotNone(suite)


if __name__ == '__main__':
    unittest.main()
