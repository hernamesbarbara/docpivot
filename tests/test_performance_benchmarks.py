"""Comprehensive tests for performance benchmarks module."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from docling_core.types import DoclingDocument

from docpivot.performance.benchmarks import (
    BenchmarkResult,
    BenchmarkSuite,
    ReaderBenchmark,
    SerializerBenchmark,
    DEFAULT_ITERATIONS,
    BENCHMARK_FILE_SIZES,
    BENCHMARK_COMPLEXITIES,
)
from docpivot.performance.monitor import PerformanceConfig
from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer


class TestBenchmarkResult(unittest.TestCase):
    """Test BenchmarkResult dataclass."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_result = BenchmarkResult(
            operation_name="test_operation",
            test_case="test_case",
            iterations=5,
            avg_duration_ms=100.0,
            min_duration_ms=80.0,
            max_duration_ms=120.0,
            std_dev_ms=15.0,
            avg_memory_mb=50.0,
            peak_memory_mb=75.0,
            throughput_mbps=10.0,
            success_rate=1.0,
            error_count=0,
        )

    def test_benchmark_result_initialization(self):
        """Test BenchmarkResult initialization."""
        self.assertEqual(self.sample_result.operation_name, "test_operation")
        self.assertEqual(self.sample_result.test_case, "test_case")
        self.assertEqual(self.sample_result.iterations, 5)
        self.assertEqual(self.sample_result.avg_duration_ms, 100.0)
        self.assertEqual(self.sample_result.error_count, 0)
        self.assertEqual(len(self.sample_result.errors), 0)
        self.assertEqual(len(self.sample_result.context), 0)

    def test_performance_score_calculation(self):
        """Test performance score calculation."""
        score = self.sample_result.performance_score
        # Base score = throughput * 100 = 10 * 100 = 1000
        # Memory penalty = min(75/100, 1.0) = 0.75
        # Error penalty = (1.0 - 1.0) * 50 = 0
        # Stability bonus = max(0, 10 - (15/100) * 100) = max(0, -5) = 0
        expected = max(0, 1000 - 0.75 - 0 + 0)
        self.assertAlmostEqual(score, expected, places=2)

    def test_performance_score_with_errors(self):
        """Test performance score with errors."""
        result = BenchmarkResult(
            operation_name="test",
            test_case="test",
            iterations=5,
            avg_duration_ms=100.0,
            min_duration_ms=80.0,
            max_duration_ms=120.0,
            std_dev_ms=5.0,
            avg_memory_mb=50.0,
            peak_memory_mb=60.0,
            throughput_mbps=5.0,
            success_rate=0.8,  # 20% error rate
            error_count=1,
        )
        score = result.performance_score
        # Base = 5 * 100 = 500
        # Memory penalty = min(60/100, 1.0) = 0.6
        # Error penalty = (1.0 - 0.8) * 50 = 10
        # Stability bonus = max(0, 10 - (5/100) * 100) = max(0, 5) = 5
        expected = max(0, 500 - 0.6 - 10 + 5)
        self.assertAlmostEqual(score, expected, places=2)

    def test_performance_score_zero_duration(self):
        """Test performance score when duration is zero."""
        result = BenchmarkResult(
            operation_name="test",
            test_case="test",
            iterations=1,
            avg_duration_ms=0.0,
            min_duration_ms=0.0,
            max_duration_ms=0.0,
            std_dev_ms=0.0,
            avg_memory_mb=0.0,
            peak_memory_mb=0.0,
            throughput_mbps=0.0,
            success_rate=1.0,
            error_count=0,
        )
        self.assertEqual(result.performance_score, 0.0)


class TestBenchmarkSuite(unittest.TestCase):
    """Test BenchmarkSuite class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PerformanceConfig()
        
    def tearDown(self):
        """Clean up after tests."""
        # Clean up any temporary directories
        if hasattr(self, 'suite') and self.suite.temp_dir and self.suite.temp_dir.exists():
            import shutil
            shutil.rmtree(self.suite.temp_dir, ignore_errors=True)

    def test_benchmark_suite_initialization(self):
        """Test BenchmarkSuite initialization."""
        suite = BenchmarkSuite(config=self.config, iterations=3)
        self.suite = suite  # Store for cleanup
        
        self.assertEqual(suite.iterations, 3)
        self.assertIsNotNone(suite.monitor)
        self.assertIsNotNone(suite.memory_profiler)
        self.assertEqual(len(suite.results), 0)
        self.assertIsNotNone(suite.temp_dir)
        self.assertTrue(suite.temp_dir.exists())

    @patch('docpivot.performance.benchmarks.shutil.rmtree')
    @patch('docpivot.performance.benchmarks.logger')
    def test_benchmark_suite_cleanup(self, mock_logger, mock_rmtree):
        """Test BenchmarkSuite cleanup on deletion."""
        suite = BenchmarkSuite()
        temp_dir = suite.temp_dir
        
        # Simulate deletion
        suite.__del__()
        
        mock_rmtree.assert_called_once_with(temp_dir)
        mock_logger.info.assert_called()

    @patch('docpivot.performance.benchmarks.shutil.rmtree')
    @patch('docpivot.performance.benchmarks.logger')
    def test_benchmark_suite_cleanup_error(self, mock_logger, mock_rmtree):
        """Test BenchmarkSuite cleanup error handling."""
        suite = BenchmarkSuite()
        mock_rmtree.side_effect = Exception("Permission denied")
        
        # Should not raise, just warn
        suite.__del__()
        
        mock_logger.warning.assert_called()

    @patch.object(BenchmarkSuite, 'benchmark_concurrency')
    @patch.object(BenchmarkSuite, 'benchmark_scaling')
    @patch.object(BenchmarkSuite, 'benchmark_memory_usage')
    @patch.object(BenchmarkSuite, 'benchmark_serializers')
    @patch.object(BenchmarkSuite, 'benchmark_readers')
    def test_run_full_suite(self, mock_readers, mock_serializers, 
                           mock_memory, mock_scaling, mock_concurrency):
        """Test run_full_suite method."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        # Mock return values
        mock_readers.return_value = {"reader": "results"}
        mock_serializers.return_value = {"serializer": "results"}
        mock_memory.return_value = {"memory": "results"}
        mock_scaling.return_value = {"scaling": "results"}
        mock_concurrency.return_value = {"concurrency": "results"}
        
        # Add some test results
        suite.results = [
            BenchmarkResult(
                operation_name="test",
                test_case="test",
                iterations=1,
                avg_duration_ms=100,
                min_duration_ms=100,
                max_duration_ms=100,
                std_dev_ms=0,
                avg_memory_mb=50,
                peak_memory_mb=50,
                throughput_mbps=10,
                success_rate=1.0,
                error_count=0,
            )
        ]
        
        report = suite.run_full_suite()
        
        self.assertIn("benchmark_summary", report)
        self.assertIn("reader_benchmarks", report)
        self.assertIn("serializer_benchmarks", report)
        self.assertIn("memory_benchmarks", report)
        self.assertIn("scaling_benchmarks", report)
        self.assertIn("concurrency_benchmarks", report)
        self.assertIn("recommendations", report)
        
        mock_readers.assert_called_once()
        mock_serializers.assert_called_once()
        mock_memory.assert_called_once()
        mock_scaling.assert_called_once()
        mock_concurrency.assert_called_once()

    @patch.object(BenchmarkSuite, 'benchmark_readers')
    def test_run_full_suite_error(self, mock_readers):
        """Test run_full_suite error handling."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        mock_readers.side_effect = Exception("Test error")
        
        with self.assertRaises(Exception) as ctx:
            suite.run_full_suite()
        
        self.assertIn("Test error", str(ctx.exception))

    def test_create_test_docling_file_simple(self):
        """Test creating a simple test DoclingDocument file."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        file_path = suite._create_test_docling_file(1024, "simple")
        
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.name.endswith(".docling.json"))
        
        # Verify content
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["schema_name"], "DoclingDocument")
        self.assertEqual(data["version"], "2.0.0")
        self.assertIn("texts", data)
        self.assertIn("tables", data)
        self.assertEqual(len(data["tables"]), 0)  # Simple has no tables

    def test_create_test_docling_file_complex(self):
        """Test creating a complex test DoclingDocument file."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        file_path = suite._create_test_docling_file(10240, "complex")
        
        self.assertTrue(file_path.exists())
        
        # Verify content
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["schema_name"], "DoclingDocument")
        self.assertEqual(len(data["tables"]), 5)  # Complex has 5 tables
        self.assertGreater(len(data["texts"]), 0)

    @patch('docpivot.performance.benchmarks.DoclingJsonReader')
    def test_create_test_document(self, mock_reader_cls):
        """Test creating a test DoclingDocument."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        mock_reader = Mock()
        mock_reader_cls.return_value = mock_reader
        mock_doc = Mock(spec=DoclingDocument)
        mock_reader.load_data.return_value = mock_doc
        
        doc = suite._create_test_document("medium")
        
        self.assertEqual(doc, mock_doc)
        mock_reader.load_data.assert_called_once()

    def test_calculate_std_dev(self):
        """Test standard deviation calculation."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        # Test with multiple values
        values = [10, 20, 30, 40, 50]
        std_dev = suite._calculate_std_dev(values)
        self.assertAlmostEqual(std_dev, 15.811, places=2)
        
        # Test with single value
        self.assertEqual(suite._calculate_std_dev([10]), 0.0)
        
        # Test with empty list
        self.assertEqual(suite._calculate_std_dev([]), 0.0)

    def test_get_memory_usage_with_psutil(self):
        """Test get_memory_usage with psutil available."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        # psutil is imported inside the function, so patch it there
        with patch('psutil.Process') as mock_process_cls:
            mock_process = Mock()
            mock_process.memory_info.return_value = Mock(rss=104857600)  # 100 MB
            mock_process_cls.return_value = mock_process
            
            memory = suite._get_memory_usage()
            self.assertEqual(memory, 100.0)

    def test_get_memory_usage_without_psutil(self):
        """Test get_memory_usage without psutil."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        with patch('builtins.__import__', side_effect=ImportError):
            memory = suite._get_memory_usage()
            self.assertEqual(memory, 0.0)

    @patch('docpivot.performance.benchmarks.DoclingJsonReader')
    def test_load_document_worker(self, mock_reader_cls):
        """Test document loading worker function."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        mock_reader = Mock()
        mock_reader_cls.return_value = mock_reader
        mock_doc = Mock(spec=DoclingDocument)
        mock_reader.load_data.return_value = mock_doc
        
        test_path = Path("test.json")
        doc = suite._load_document_worker(test_path)
        
        self.assertEqual(doc, mock_doc)
        mock_reader.load_data.assert_called_once_with(test_path)

    def test_generate_recommendations_no_data(self):
        """Test recommendation generation with no data."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        recommendations = suite._generate_recommendations()
        self.assertEqual(len(recommendations), 1)
        self.assertIn("No benchmark data", recommendations[0])

    def test_generate_recommendations_with_data(self):
        """Test recommendation generation with benchmark data."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        # Add various results to trigger different recommendations
        suite.results = [
            BenchmarkResult(
                operation_name="slow_op",
                test_case="test1",
                iterations=1,
                avg_duration_ms=5000,
                min_duration_ms=5000,
                max_duration_ms=5000,
                std_dev_ms=0,
                avg_memory_mb=250,
                peak_memory_mb=300,  # High memory
                throughput_mbps=0.1,  # Low throughput
                success_rate=0.5,  # High error rate
                error_count=2,
            ),
            BenchmarkResult(
                operation_name="fast_op",
                test_case="test2",
                iterations=1,
                avg_duration_ms=10,
                min_duration_ms=10,
                max_duration_ms=10,
                std_dev_ms=0,
                avg_memory_mb=10,
                peak_memory_mb=15,
                throughput_mbps=100,
                success_rate=1.0,
                error_count=0,
            ),
        ]
        
        recommendations = suite._generate_recommendations()
        
        # Should have multiple recommendations based on the data
        self.assertGreater(len(recommendations), 0)
        
        # Check for specific recommendation types
        recommendations_text = " ".join(recommendations)
        self.assertTrue(
            "below-average performance" in recommendations_text or
            "memory" in recommendations_text or
            "error rate" in recommendations_text or 
            "throughput" in recommendations_text
        )

    @patch.object(BenchmarkSuite, '_benchmark_reader')
    def test_benchmark_readers(self, mock_benchmark_reader):
        """Test benchmark_readers method."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        mock_result = Mock(spec=BenchmarkResult)
        mock_benchmark_reader.return_value = mock_result
        
        results = suite.benchmark_readers()
        
        # Should test different file sizes and complexities
        self.assertIn("docling_1024_bytes", results)
        self.assertIn("docling_simple", results)
        self.assertIn("docling_medium", results)
        self.assertIn("docling_complex", results)
        
        # Verify benchmark_reader was called
        self.assertGreater(mock_benchmark_reader.call_count, 0)

    @patch.object(BenchmarkSuite, '_benchmark_serializer')
    @patch.object(BenchmarkSuite, '_create_test_document')
    def test_benchmark_serializers(self, mock_create_doc, mock_benchmark_serializer):
        """Test benchmark_serializers method."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        mock_doc = Mock(spec=DoclingDocument)
        mock_create_doc.return_value = mock_doc
        
        mock_result = Mock(spec=BenchmarkResult)
        mock_benchmark_serializer.return_value = mock_result
        
        results = suite.benchmark_serializers()
        
        # Check results structure
        for complexity in BENCHMARK_COMPLEXITIES:
            self.assertIn(f"lexical_{complexity}_compact", results)
            self.assertIn(f"lexical_{complexity}_standard", results)
            self.assertIn(f"lexical_{complexity}_minimal", results)
        
        # Verify methods were called
        self.assertEqual(mock_create_doc.call_count, len(BENCHMARK_COMPLEXITIES))
        self.assertGreater(mock_benchmark_serializer.call_count, 0)

    @patch('docpivot.performance.benchmarks.LexicalDocSerializer')
    @patch('docpivot.performance.benchmarks.DoclingJsonReader')
    def test_benchmark_memory_usage(self, mock_reader_cls, mock_serializer_cls):
        """Test benchmark_memory_usage method."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        # Setup mocks
        mock_reader = Mock()
        mock_reader_cls.return_value = mock_reader
        mock_doc = Mock(spec=DoclingDocument)
        mock_reader.load_data.return_value = mock_doc
        
        mock_serializer = Mock()
        mock_serializer_cls.return_value = mock_serializer
        mock_result = Mock()
        mock_result.text = "serialized content"
        mock_serializer.serialize.return_value = mock_result
        
        # Mock memory profiler
        with patch.object(suite.memory_profiler, 'profile_memory') as mock_profile:
            mock_report = Mock()
            mock_report.peak_memory_mb = 100
            mock_report.memory_delta_mb = 50
            mock_report.warnings = []
            mock_report.memory_efficiency = 0.5
            mock_profile.return_value.__enter__ = Mock(return_value=mock_report)
            mock_profile.return_value.__exit__ = Mock(return_value=None)
            
            results = suite.benchmark_memory_usage()
        
        # Check results
        self.assertGreater(len(results), 0)
        for key, value in results.items():
            if "error" not in value:
                self.assertIn("peak_memory_mb", value)
                self.assertIn("memory_delta_mb", value)
                self.assertIn("efficiency", value)

    @patch('docpivot.performance.benchmarks.LexicalDocSerializer')
    def test_benchmark_scaling(self, mock_serializer_cls):
        """Test benchmark_scaling method."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        mock_serializer = Mock()
        mock_serializer_cls.return_value = mock_serializer
        mock_result = Mock()
        mock_result.text = "serialized"
        mock_serializer.serialize.return_value = mock_result
        
        with patch.object(suite, '_create_test_document') as mock_create:
            mock_create.return_value = Mock(spec=DoclingDocument)
            
            with patch.object(suite, '_get_memory_usage') as mock_memory:
                mock_memory.return_value = 100.0
                
                results = suite.benchmark_scaling()
        
        # Check results for different document counts
        self.assertIn("doc_count_1", results)
        self.assertIn("doc_count_5", results)
        
        for key, value in results.items():
            if value.get("success"):
                self.assertIn("duration_ms", value)
                self.assertIn("throughput_docs_per_sec", value)

    @patch('docpivot.performance.benchmarks.as_completed')
    @patch('docpivot.performance.benchmarks.ThreadPoolExecutor')
    @patch('docpivot.performance.benchmarks.DoclingJsonReader')
    def test_benchmark_concurrency(self, mock_reader_cls, mock_executor_cls, mock_as_completed):
        """Test benchmark_concurrency method."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        
        # Setup mocks
        mock_reader = Mock()
        mock_reader_cls.return_value = mock_reader
        mock_doc = Mock(spec=DoclingDocument)
        mock_reader.load_data.return_value = mock_doc
        
        # Mock executor
        mock_executor = Mock()
        mock_executor_cls.return_value.__enter__ = Mock(return_value=mock_executor)
        mock_executor_cls.return_value.__exit__ = Mock(return_value=None)
        
        # Mock futures
        mock_future = Mock()
        mock_future.result.return_value = mock_doc
        mock_executor.submit.return_value = mock_future
        mock_as_completed.return_value = [mock_future]
        
        results = suite.benchmark_concurrency()
        
        # Check results structure
        self.assertIn("workers_1", results)  # Sequential processing
        self.assertIn("workers_2", results)
        
        for key, value in results.items():
            if value.get("success"):
                self.assertIn("duration_ms", value)
                self.assertIn("documents_processed", value)
                self.assertIn("throughput_docs_per_sec", value)

    def test_benchmark_reader_method(self):
        """Test _benchmark_reader method."""
        suite = BenchmarkSuite(iterations=2)
        self.suite = suite  # Store for cleanup
        
        # Create a test file
        test_file = suite._create_test_docling_file(1024, "simple")
        
        with patch('docpivot.performance.benchmarks.DoclingJsonReader') as mock_reader_cls:
            mock_reader_cls.__name__ = "DoclingJsonReader"  # Add __name__ attribute
            mock_reader = Mock()
            mock_reader_cls.return_value = mock_reader
            mock_doc = Mock(spec=DoclingDocument)
            mock_reader.load_data.return_value = mock_doc
            
            # Mock memory profiler
            with patch.object(suite.memory_profiler, 'profile_memory') as mock_profile:
                mock_report = Mock()
                mock_report.peak_memory_mb = 50
                mock_profile.return_value.__enter__ = Mock(return_value=mock_report)
                mock_profile.return_value.__exit__ = Mock(return_value=None)
                
                result = suite._benchmark_reader(
                    mock_reader_cls,
                    test_file,
                    "test_reader",
                    {"test": "context"}
                )
        
        self.assertIsInstance(result, BenchmarkResult)
        self.assertEqual(result.test_case, "test_reader")
        self.assertEqual(result.iterations, 2)
        self.assertEqual(result.context["test"], "context")
        self.assertIn(result, suite.results)

    def test_benchmark_reader_with_errors(self):
        """Test _benchmark_reader with errors."""
        suite = BenchmarkSuite(iterations=3)
        self.suite = suite  # Store for cleanup
        
        test_file = suite._create_test_docling_file(1024, "simple")
        
        with patch('docpivot.performance.benchmarks.DoclingJsonReader') as mock_reader_cls:
            mock_reader_cls.__name__ = "DoclingJsonReader"  # Add __name__ attribute
            # Make first iteration fail, others succeed
            mock_reader = Mock()
            mock_reader.load_data.side_effect = [
                Exception("Test error"),
                Mock(spec=DoclingDocument),
                Mock(spec=DoclingDocument),
            ]
            mock_reader_cls.return_value = mock_reader
            
            with patch.object(suite.memory_profiler, 'profile_memory') as mock_profile:
                mock_report = Mock()
                mock_report.peak_memory_mb = 50
                mock_profile.return_value.__enter__ = Mock(return_value=mock_report)
                mock_profile.return_value.__exit__ = Mock(return_value=None)
                
                result = suite._benchmark_reader(
                    mock_reader_cls,
                    test_file,
                    "test_with_errors"
                )
        
        self.assertEqual(result.error_count, 1)
        self.assertEqual(result.success_rate, 2/3)
        self.assertIn("Test error", result.errors[0])

    def test_benchmark_serializer_method(self):
        """Test _benchmark_serializer method."""
        suite = BenchmarkSuite(iterations=2)
        self.suite = suite  # Store for cleanup
        
        mock_doc = Mock(spec=DoclingDocument)
        
        with patch('docpivot.performance.benchmarks.LexicalDocSerializer') as mock_serializer_cls:
            mock_serializer_cls.__name__ = "LexicalDocSerializer"  # Add __name__ attribute
            mock_serializer = Mock()
            mock_serializer_cls.return_value = mock_serializer
            mock_result = Mock()
            mock_result.text = "serialized content"
            mock_serializer.serialize.return_value = mock_result
            
            with patch.object(suite.memory_profiler, 'profile_memory') as mock_profile:
                mock_report = Mock()
                mock_report.peak_memory_mb = 60
                mock_profile.return_value.__enter__ = Mock(return_value=mock_report)
                mock_profile.return_value.__exit__ = Mock(return_value=None)
                
                result = suite._benchmark_serializer(
                    mock_serializer_cls,
                    mock_doc,
                    "test_serializer",
                    {"indent_json": True},
                    {"custom": "context"}
                )
        
        self.assertIsInstance(result, BenchmarkResult)
        self.assertEqual(result.test_case, "test_serializer")
        self.assertEqual(result.iterations, 2)
        self.assertIn("avg_output_size", result.context)
        self.assertEqual(result.context["custom"], "context")

    def test_temp_dir_not_initialized_error(self):
        """Test error when temp_dir is not initialized."""
        suite = BenchmarkSuite(iterations=1)
        self.suite = suite  # Store for cleanup
        suite.temp_dir = None
        
        with self.assertRaises(RuntimeError) as ctx:
            suite._create_test_docling_file(1024, "simple")
        
        self.assertIn("temp_dir not initialized", str(ctx.exception))


class TestReaderBenchmark(unittest.TestCase):
    """Test ReaderBenchmark class."""

    def test_reader_benchmark_initialization(self):
        """Test ReaderBenchmark initialization."""
        config = PerformanceConfig()
        benchmark = ReaderBenchmark(config)
        
        self.assertEqual(benchmark.config, config)
        self.assertIsNotNone(benchmark.suite)
        
        # Clean up
        if benchmark.suite.temp_dir and benchmark.suite.temp_dir.exists():
            import shutil
            shutil.rmtree(benchmark.suite.temp_dir, ignore_errors=True)

    @patch.object(BenchmarkSuite, '_benchmark_reader')
    @patch.object(BenchmarkSuite, '_create_test_docling_file')
    def test_benchmark_file_sizes(self, mock_create_file, mock_benchmark):
        """Test benchmark_file_sizes method."""
        benchmark = ReaderBenchmark()
        
        mock_create_file.return_value = Path("test.json")
        mock_result = Mock(spec=BenchmarkResult)
        mock_benchmark.return_value = mock_result
        
        with patch('docpivot.performance.benchmarks.DoclingJsonReader') as mock_reader_cls:
            results = benchmark.benchmark_file_sizes(mock_reader_cls)
        
        # Check all file sizes were tested
        for size in BENCHMARK_FILE_SIZES:
            self.assertIn(f"{size}_bytes", results)
        
        self.assertEqual(mock_create_file.call_count, len(BENCHMARK_FILE_SIZES))
        self.assertEqual(mock_benchmark.call_count, len(BENCHMARK_FILE_SIZES))
        
        # Clean up
        if benchmark.suite.temp_dir and benchmark.suite.temp_dir.exists():
            import shutil
            shutil.rmtree(benchmark.suite.temp_dir, ignore_errors=True)

    @patch.object(BenchmarkSuite, '_benchmark_reader')
    @patch.object(BenchmarkSuite, '_create_test_docling_file')
    def test_benchmark_document_complexity(self, mock_create_file, mock_benchmark):
        """Test benchmark_document_complexity method."""
        benchmark = ReaderBenchmark()
        
        mock_create_file.return_value = Path("test.json")
        mock_result = Mock(spec=BenchmarkResult)
        mock_benchmark.return_value = mock_result
        
        with patch('docpivot.performance.benchmarks.DoclingJsonReader') as mock_reader_cls:
            results = benchmark.benchmark_document_complexity(mock_reader_cls)
        
        # Check all complexities were tested
        for complexity in BENCHMARK_COMPLEXITIES:
            self.assertIn(complexity, results)
        
        self.assertEqual(mock_create_file.call_count, len(BENCHMARK_COMPLEXITIES))
        self.assertEqual(mock_benchmark.call_count, len(BENCHMARK_COMPLEXITIES))
        
        # Clean up
        if benchmark.suite.temp_dir and benchmark.suite.temp_dir.exists():
            import shutil
            shutil.rmtree(benchmark.suite.temp_dir, ignore_errors=True)


class TestSerializerBenchmark(unittest.TestCase):
    """Test SerializerBenchmark class."""

    def test_serializer_benchmark_initialization(self):
        """Test SerializerBenchmark initialization."""
        config = PerformanceConfig()
        benchmark = SerializerBenchmark(config)
        
        self.assertEqual(benchmark.config, config)
        self.assertIsNotNone(benchmark.suite)
        
        # Clean up
        if benchmark.suite.temp_dir and benchmark.suite.temp_dir.exists():
            import shutil
            shutil.rmtree(benchmark.suite.temp_dir, ignore_errors=True)

    @patch.object(BenchmarkSuite, '_benchmark_serializer')
    def test_benchmark_serialization_options(self, mock_benchmark):
        """Test benchmark_serialization_options method."""
        benchmark = SerializerBenchmark()
        
        mock_doc = Mock(spec=DoclingDocument)
        mock_result = Mock(spec=BenchmarkResult)
        mock_benchmark.return_value = mock_result
        
        with patch('docpivot.performance.benchmarks.LexicalDocSerializer') as mock_serializer_cls:
            results = benchmark.benchmark_serialization_options(mock_serializer_cls, mock_doc)
        
        # Check all config options were tested
        expected_configs = ["minimal", "compact", "standard", "full_featured"]
        for config_name in expected_configs:
            self.assertIn(config_name, results)
        
        self.assertEqual(mock_benchmark.call_count, len(expected_configs))
        
        # Verify parameters passed to benchmark
        for call in mock_benchmark.call_args_list:
            _, test_name, params = call[0][1:4]
            self.assertIn("config_", test_name)
            self.assertIn("indent_json", params)
        
        # Clean up
        if benchmark.suite.temp_dir and benchmark.suite.temp_dir.exists():
            import shutil
            shutil.rmtree(benchmark.suite.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()