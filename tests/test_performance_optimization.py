"""Comprehensive tests for performance optimization features."""

import pytest
import json
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading

from docpivot.performance import (
    PerformanceMonitor, PerformanceConfig, PerformanceMetrics,
    BenchmarkSuite, MemoryProfiler, MemoryReport
)
from docpivot.performance.edge_cases import EdgeCaseHandler, EdgeCaseConfig
from docpivot.io.readers.optimized_docling_reader import OptimizedDoclingJsonReader
from docpivot.io.serializers.optimized_lexical_serializer import OptimizedLexicalDocSerializer, OptimizedLexicalParams
from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
from docling_core.types import DoclingDocument


def create_valid_docling_document_data(texts=None, tables=None, groups=None):
    """Create a valid DoclingDocument data structure for testing.
    
    Creates a minimal valid structure with proper parent relationships
    to avoid validation issues in DoclingDocument.model_validate().
    """
    # Use provided parameters or defaults
    if texts is None:
        texts = []
    if tables is None:
        tables = []
    if groups is None:
        groups = []
    
    # Add required fields to text items with proper parent references
    for i, text_item in enumerate(texts):
        if "self_ref" not in text_item:
            text_item["self_ref"] = f"#/texts/{i}"
        if "orig" not in text_item:
            text_item["orig"] = f"#/texts/{i}"
        # Set parent reference to body for proper validation
        text_item["parent"] = {"cref": "#/body"}
            
    # Add required fields to table items with proper parent references
    for i, table_item in enumerate(tables):
        if "self_ref" not in table_item:
            table_item["self_ref"] = f"#/tables/{i}"
        # Set parent reference to body for proper validation
        table_item["parent"] = {"cref": "#/body"}
    
    # Add required fields to group items with proper parent references
    for i, group_item in enumerate(groups):
        if "self_ref" not in group_item:
            group_item["self_ref"] = f"#/groups/{i}"
        # Set parent reference to body for proper validation
        group_item["parent"] = {"cref": "#/body"}
    
    # Create body children references
    body_children = []
    for i in range(len(texts)):
        body_children.append({"cref": f"#/texts/{i}"})
    for i in range(len(tables)):
        body_children.append({"cref": f"#/tables/{i}"})
    for i in range(len(groups)):
        body_children.append({"cref": f"#/groups/{i}"})
    
    return {
        "schema_name": "DoclingDocument",
        "version": "1.4.0",
        "name": "test_document",
        "origin": {
            "mimetype": "application/pdf",
            "binary_hash": 123456789,
            "filename": "test.pdf",
        },
        "furniture": {
            "self_ref": "#/furniture",
            "children": [],
            "content_layer": "furniture",
            "name": "_root_",
            "label": "unspecified",
            # No parent for root elements
        },
        "body": {
            "self_ref": "#/body", 
            "children": body_children,
            "content_layer": "body",
            "name": "_root_",
            "label": "unspecified",
            # No parent for root elements
        },
        "groups": groups,
        "texts": texts,
        "pictures": [],
        "tables": tables,
        "key_value_items": [],
        "pages": {}
    }


class TestPerformanceMonitor:
    """Test suite for PerformanceMonitor."""
    
    def test_performance_config_validation(self):
        """Test PerformanceConfig parameter validation."""
        # Valid config
        config = PerformanceConfig(
            max_file_size_mb=50,
            streaming_threshold_mb=10,
            memory_limit_mb=256
        )
        assert config.max_file_size_mb == 50
        
        # Invalid configs
        with pytest.raises(ValueError):
            PerformanceConfig(max_file_size_mb=0)
        
        with pytest.raises(ValueError):
            PerformanceConfig(streaming_threshold_mb=0)
        
        with pytest.raises(ValueError):
            PerformanceConfig(streaming_threshold_mb=100, max_file_size_mb=50)
    
    def test_performance_metrics_calculations(self):
        """Test PerformanceMetrics calculations."""
        metrics = PerformanceMetrics(
            operation_name="test_op",
            duration_ms=1000.0,
            memory_usage_mb=100.0,
            file_size_bytes=2048000  # 2MB
        )
        
        # Test throughput calculation  
        # 2048000 bytes = 1.953125 MB, 1000ms = 1s, so throughput = 1.953125 MB/s
        assert metrics.throughput_mb_per_second == pytest.approx(1.953125, rel=1e-2)
        
        # Test efficiency score
        # efficiency = throughput / memory_usage = 1.953125 / 100.0 = 0.01953125
        assert metrics.efficiency_score == pytest.approx(0.01953125, rel=1e-2)
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        config = PerformanceConfig(memory_limit_mb=512)
        monitor = PerformanceMonitor(config)
        
        assert monitor.config.memory_limit_mb == 512
        assert len(monitor.metrics_history) == 0
    
    @patch('psutil.Process')
    def test_profile_reader_success(self, mock_process):
        """Test successful reader profiling."""
        # Mock memory monitoring
        mock_memory = Mock()
        mock_memory.rss = 100 * 1024 * 1024  # 100MB
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = mock_memory
        mock_process_instance.memory_percent.return_value = 10.0
        mock_process.return_value = mock_process_instance
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as f:
            test_data = create_valid_docling_document_data()
            json.dump(test_data, f)
            temp_file = Path(f.name)
        
        try:
            monitor = PerformanceMonitor()
            result = monitor.profile_reader(DoclingJsonReader, temp_file)
            
            assert "metrics" in result
            assert "profile_stats" in result
            assert "document" in result
            assert "recommendations" in result
            
            metrics = result["metrics"]
            assert metrics.operation_name == "DoclingJsonReader.load_data"
            assert metrics.duration_ms > 0
            assert len(monitor.metrics_history) == 1
            
        finally:
            temp_file.unlink()
    
    def test_profile_reader_error_handling(self):
        """Test reader profiling error handling."""
        monitor = PerformanceMonitor()
        
        with pytest.raises(Exception):  # Should propagate the underlying error
            monitor.profile_reader(DoclingJsonReader, "nonexistent_file.json")
        
        # Should still record error metrics
        assert len(monitor.metrics_history) == 1
        assert monitor.metrics_history[0].error_occurred
    
    @patch('psutil.Process')
    def test_profile_serializer_success(self, mock_process):
        """Test successful serializer profiling."""
        # Mock memory monitoring
        mock_memory = Mock()
        mock_memory.rss = 50 * 1024 * 1024  # 50MB
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = mock_memory
        mock_process_instance.memory_percent.return_value = 5.0
        mock_process.return_value = mock_process_instance
        
        # Create test document
        doc_data = create_valid_docling_document_data()
        doc = DoclingDocument.model_validate(doc_data)
        
        monitor = PerformanceMonitor()
        result = monitor.profile_serializer(LexicalDocSerializer, doc)
        
        assert "metrics" in result
        assert "profile_stats" in result
        assert "serialization_result" in result
        assert "recommendations" in result
        
        metrics = result["metrics"]
        assert metrics.operation_name == "LexicalDocSerializer.serialize"
        assert metrics.duration_ms > 0
    
    def test_memory_profile_function(self):
        """Test memory profiling of functions."""
        monitor = PerformanceMonitor()
        
        def test_function(x, y):
            return x + y
        
        result = monitor.memory_profile(test_function, 5, 3)
        
        assert result == 8
        assert len(monitor.metrics_history) == 1
        assert "test_function_memory_profile" in monitor.metrics_history[0].operation_name
    
    def test_metrics_summary(self):
        """Test metrics summary generation."""
        monitor = PerformanceMonitor()
        
        # Add some test metrics
        monitor.metrics_history.extend([
            PerformanceMetrics("test_op1", 100.0, 50.0, 1024),
            PerformanceMetrics("test_op2", 200.0, 75.0, 2048),
            PerformanceMetrics("test_op3", 150.0, 60.0, 1536, error_occurred=True)
        ])
        
        summary = monitor.get_metrics_summary()
        
        assert summary["total_operations"] == 3
        assert summary["successful_operations"] == 2
        assert summary["error_rate"] == pytest.approx(1/3, rel=1e-2)
        assert "performance_summary" in summary
        assert "recent_operations" in summary
    
    def test_reset_metrics(self):
        """Test metrics reset functionality."""
        monitor = PerformanceMonitor()
        monitor.metrics_history.append(PerformanceMetrics("test", 100.0, 50.0))
        
        assert len(monitor.metrics_history) == 1
        
        monitor.reset_metrics()
        
        assert len(monitor.metrics_history) == 0


class TestMemoryProfiler:
    """Test suite for MemoryProfiler."""
    
    def test_memory_profiler_initialization(self):
        """Test MemoryProfiler initialization."""
        profiler = MemoryProfiler(
            warning_threshold_mb=100,
            critical_threshold_mb=500,
            sample_interval_ms=50
        )
        
        assert profiler.warning_threshold_mb == 100
        assert profiler.critical_threshold_mb == 500
        assert profiler.sample_interval_ms == 50
    
    @patch('psutil.Process')
    @patch('psutil.virtual_memory')
    def test_memory_profiling_context(self, mock_virtual_memory, mock_process):
        """Test memory profiling context manager."""
        # Mock memory info
        mock_memory = Mock()
        mock_memory.rss = 100 * 1024 * 1024  # 100MB
        mock_memory.vms = 200 * 1024 * 1024  # 200MB
        
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = mock_memory
        mock_process_instance.memory_percent.return_value = 10.0
        mock_process.return_value = mock_process_instance
        
        mock_vm = Mock()
        mock_vm.available = 1024 * 1024 * 1024  # 1GB
        mock_virtual_memory.return_value = mock_vm
        
        profiler = MemoryProfiler()
        
        with profiler.profile_memory("test_operation") as report:
            assert report.operation_name == "test_operation"
            time.sleep(0.1)  # Brief operation
        
        assert report.duration_ms > 0
        assert report.initial_memory_mb > 0
        assert len(profiler.get_reports()) == 1
    
    def test_memory_profiler_without_psutil(self):
        """Test memory profiler fallback when psutil unavailable."""
        # Create profiler and force psutil unavailable mode
        profiler = MemoryProfiler()
        profiler._psutil_available = False
        
        with profiler.profile_memory("test_operation") as report:
            assert report.operation_name == "test_operation"
            time.sleep(0.05)
        
        assert "Basic memory monitoring" in report.warnings[0]
        assert report.duration_ms > 0
    
    def test_profile_function(self):
        """Test function memory profiling."""
        profiler = MemoryProfiler()
        
        def test_func(a, b):
            return [i for i in range(a * b)]  # Create some memory usage
        
        result = profiler.profile_function(test_func, 100, 10)
        
        assert len(result) == 1000
        assert len(profiler.get_reports()) == 1
        
        report = profiler.get_latest_report()
        assert report.operation_name == "test_func_memory_profile"
    
    def test_memory_report_calculations(self):
        """Test MemoryReport calculations."""
        from docpivot.performance.memory_profiler import MemoryUsage
        
        report = MemoryReport(
            operation_name="test",
            start_time=0.0,
            end_time=1.0,
            duration_ms=1000.0,
            initial_memory_mb=50.0,
            peak_memory_mb=100.0,
            final_memory_mb=75.0,
            memory_delta_mb=25.0
        )
        
        # Add some samples
        report.samples = [
            MemoryUsage(0.0, 50.0, 100.0, 5.0),
            MemoryUsage(0.5, 75.0, 150.0, 7.5),
            MemoryUsage(1.0, 75.0, 150.0, 7.5)
        ]
        
        assert report.memory_efficiency == 0.25  # delta/peak
        assert report.average_memory_mb == pytest.approx(66.67, rel=1e-2)
    
    def test_memory_analysis_patterns(self):
        """Test memory usage pattern analysis.""" 
        profiler = MemoryProfiler()
        
        # Add some mock reports
        from docpivot.performance.memory_profiler import MemoryReport
        reports = [
            MemoryReport("op1", 0, 1, 1000, 50, 100, 75, 25),
            MemoryReport("op1", 1, 2, 1500, 60, 120, 80, 20),
            MemoryReport("op2", 2, 3, 800, 40, 80, 60, 20)
        ]
        
        profiler._reports = reports
        analysis = profiler.analyze_memory_patterns()
        
        assert "operations_analyzed" in analysis
        assert analysis["operations_analyzed"] == 2  # op1 and op2
        assert "operation_analysis" in analysis
        assert "op1" in analysis["operation_analysis"]
        assert "op2" in analysis["operation_analysis"]


class TestBenchmarkSuite:
    """Test suite for BenchmarkSuite."""
    
    def test_benchmark_suite_initialization(self):
        """Test BenchmarkSuite initialization."""
        config = PerformanceConfig(max_file_size_mb=50)
        suite = BenchmarkSuite(config, iterations=3)
        
        assert suite.config.max_file_size_mb == 50
        assert suite.iterations == 3
        assert suite.temp_dir is not None
        assert suite.temp_dir.exists()
    
    def test_create_test_docling_file(self):
        """Test test file creation."""
        suite = BenchmarkSuite(iterations=1)
        
        try:
            # Create small test file
            test_file = suite._create_test_docling_file(1024, "simple")
            
            assert test_file.exists()
            assert test_file.suffix == ".json"
            
            # Verify file content
            with open(test_file) as f:
                data = json.load(f)
            
            assert data["schema_name"] == "DoclingDocument"
            assert "texts" in data
            assert "body" in data
            
        finally:
            if hasattr(suite, 'temp_dir') and suite.temp_dir:
                shutil.rmtree(suite.temp_dir, ignore_errors=True)
    
    def test_benchmark_result_performance_score(self):
        """Test BenchmarkResult performance score calculation."""
        from docpivot.performance.benchmarks import BenchmarkResult
        
        result = BenchmarkResult(
            operation_name="test",
            test_case="test_case", 
            iterations=5,
            avg_duration_ms=100.0,
            min_duration_ms=90.0,
            max_duration_ms=110.0,
            std_dev_ms=5.0,
            avg_memory_mb=50.0,
            peak_memory_mb=60.0,
            throughput_mbps=2.0,
            success_rate=1.0,
            error_count=0
        )
        
        score = result.performance_score
        assert score > 0
        assert isinstance(score, float)
    
    @patch('docpivot.performance.benchmarks.BenchmarkSuite._load_document_worker')
    def test_benchmark_readers(self, mock_worker):
        """Test reader benchmarking."""
        # Mock the document loading
        mock_doc = Mock(spec=DoclingDocument)
        mock_doc.texts = [Mock(text="test")]
        mock_doc.tables = []
        mock_worker.return_value = mock_doc
        
        suite = BenchmarkSuite(iterations=1)
        
        try:
            # Mock the reader to avoid file I/O
            with patch('docpivot.io.readers.DoclingJsonReader') as mock_reader_class:
                mock_reader = Mock()
                mock_reader.load_data.return_value = mock_doc
                mock_reader_class.return_value = mock_reader
                
                # Create a dummy test file
                test_file = suite.temp_dir / "test.json"
                test_file.write_text('{"test": "data"}')
                
                # Mock the _create_test_docling_file to return our dummy file
                with patch.object(suite, '_create_test_docling_file', return_value=test_file):
                    results = suite.benchmark_readers()
                
                assert isinstance(results, dict)
                assert len(results) > 0
                
        finally:
            if hasattr(suite, 'temp_dir') and suite.temp_dir:
                shutil.rmtree(suite.temp_dir, ignore_errors=True)


class TestOptimizedDoclingReader:
    """Test suite for OptimizedDoclingReader."""
    
    def test_optimized_reader_initialization(self):
        """Test OptimizedDoclingReader initialization."""
        config = PerformanceConfig(streaming_threshold_mb=5)
        reader = OptimizedDoclingJsonReader(
            performance_config=config,
            use_fast_json=True,
            enable_caching=True
        )
        
        assert reader.performance_config.streaming_threshold_mb == 5
        assert reader.use_fast_json is True
        assert reader.enable_caching is True
    
    def test_json_parser_selection(self):
        """Test JSON parser selection logic."""
        # Test with fast JSON enabled
        reader = OptimizedDoclingJsonReader(use_fast_json=True)
        parser = reader._json_parser
        assert parser is not None
        
        # Test with fast JSON disabled
        reader_no_fast = OptimizedDoclingJsonReader(use_fast_json=False)
        assert reader_no_fast._json_parser.__name__ == 'json'
    
    def test_format_detection_optimization(self):
        """Test optimized format detection."""
        reader = OptimizedDoclingJsonReader()
        
        # Create test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as f:
            json.dump({"schema_name": "DoclingDocument", "version": "1.4.0"}, f)
            docling_file = Path(f.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"schema_name": "DoclingDocument", "version": "1.4.0", "texts": []}, f)
            json_file = Path(f.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Not a JSON file")
            txt_file = Path(f.name)
        
        try:
            # Test format detection
            assert reader.detect_format(docling_file) is True
            assert reader.detect_format(json_file) is True  
            assert reader.detect_format(txt_file) is False
            assert reader.detect_format("nonexistent.json") is False
            
        finally:
            for file in [docling_file, json_file, txt_file]:
                file.unlink()
    
    def test_cache_functionality(self):
        """Test document caching functionality."""
        reader = OptimizedDoclingJsonReader(enable_caching=True)
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as f:
            test_data = create_valid_docling_document_data()
            json.dump(test_data, f)
            temp_file = Path(f.name)
        
        try:
            # First load
            doc1 = reader.load_data(temp_file)
            assert len(reader._document_cache) == 1
            
            # Second load should use cache
            doc2 = reader.load_data(temp_file)
            assert doc2 is doc1  # Same object from cache
            
            # Test cache info
            cache_info = reader.get_cache_info()
            assert cache_info["enabled"] is True
            assert cache_info["size"] == 1
            assert str(temp_file) in cache_info["files"]
            
            # Test cache clearing
            reader.clear_cache()
            assert len(reader._document_cache) == 0
            
        finally:
            temp_file.unlink()
    
    def test_performance_monitoring_context(self):
        """Test performance monitoring context manager."""
        reader = OptimizedDoclingJsonReader()
        
        with reader.performance_monitoring("test_operation"):
            time.sleep(0.05)  # Simulate some work
        
        # Context manager should complete without errors
        assert True
    
    def test_preload_documents(self):
        """Test document preloading functionality."""
        reader = OptimizedDoclingJsonReader(enable_caching=True)
        
        # Create multiple test files
        test_files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as f:
                    texts = [{"text": f"Test content {i}", "label": "paragraph"}]
                    test_data = create_valid_docling_document_data(texts=texts)
                    test_data["name"] = f"test_doc_{i}"
                    json.dump(test_data, f)
                    test_files.append(Path(f.name))
            
            # Add one invalid file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write("invalid json content")
                test_files.append(Path(f.name))
            
            # Preload documents
            results = reader.preload_documents(test_files)
            
            assert len(results) == 4
            # 3 successful, 1 failed
            successful = [r for r in results.values() if isinstance(r, DoclingDocument)]
            failed = [r for r in results.values() if isinstance(r, Exception)]
            
            assert len(successful) == 3
            assert len(failed) == 1
            
        finally:
            for file in test_files:
                file.unlink()


class TestOptimizedLexicalSerializer:
    """Test suite for OptimizedLexicalSerializer."""
    
    def test_optimized_serializer_initialization(self):
        """Test OptimizedLexicalSerializer initialization."""
        # Create test document
        doc_data = create_valid_docling_document_data(texts=[{"text": "Test", "label": "paragraph"}])
        doc = DoclingDocument.model_validate(doc_data)
        
        params = OptimizedLexicalParams(
            enable_streaming=True,
            batch_size=500,
            use_fast_json=True
        )
        
        serializer = OptimizedLexicalDocSerializer(doc=doc, params=params)
        
        assert serializer.params.enable_streaming is True
        assert serializer.params.batch_size == 500
        assert serializer.params.use_fast_json is True
    
    def test_optimized_params_validation(self):
        """Test OptimizedLexicalParams validation."""
        # Valid params
        params = OptimizedLexicalParams(batch_size=100, max_workers=2)
        assert params.batch_size == 100
        assert params.max_workers == 2
        
        # Test default values
        default_params = OptimizedLexicalParams()
        assert default_params.enable_streaming is False
        assert default_params.use_fast_json is True
    
    def test_element_counting(self):
        """Test document element counting."""
        texts = [
            {"text": "Text 1", "label": "paragraph"},
            {"text": "Text 2", "label": "paragraph"}
        ]
        tables = [{"data": {"grid": [[{"text": "Cell"}]]}}]
        doc_data = create_valid_docling_document_data(texts=texts, tables=tables)
        doc = DoclingDocument.model_validate(doc_data)
        
        serializer = OptimizedLexicalDocSerializer(doc=doc)
        total_elements = serializer._count_total_elements()
        
        # 3 body children + 2 texts + 1 table = 6 elements
        assert total_elements == 6
    
    def test_json_encoder_selection(self):
        """Test JSON encoder selection."""
        doc_data = create_valid_docling_document_data()
        doc = DoclingDocument.model_validate(doc_data)
        
        # Test with fast JSON enabled
        params_fast = OptimizedLexicalParams(use_fast_json=True)
        serializer_fast = OptimizedLexicalDocSerializer(doc=doc, params=params_fast)
        encoder_fast = serializer_fast._json_encoder
        assert encoder_fast is not None
        
        # Test with fast JSON disabled
        params_standard = OptimizedLexicalParams(use_fast_json=False)
        serializer_standard = OptimizedLexicalDocSerializer(doc=doc, params=params_standard)
        encoder_standard = serializer_standard._json_encoder
        assert encoder_standard.__name__ == 'json'
    
    def test_optimized_text_processing(self):
        """Test optimized text processing methods."""
        texts = [{"text": "Visit https://example.com for more info", "label": "paragraph"}]
        doc_data = create_valid_docling_document_data(texts=texts)
        doc = DoclingDocument.model_validate(doc_data)
        
        params = OptimizedLexicalParams(optimize_text_formatting=True)
        serializer = OptimizedLexicalDocSerializer(doc=doc, params=params)
        
        text_item = doc.texts[0]
        
        # Test fast link processing
        nodes = serializer._process_text_with_links_fast("Visit https://example.com for more info", text_item)
        assert len(nodes) >= 2  # Should have text and link nodes
        
        # Test fast formatting detection
        format_types = serializer._detect_text_formatting_fast("IMPORTANT MESSAGE", text_item)
        assert "bold" in format_types
    
    def test_performance_statistics(self):
        """Test performance statistics collection."""
        doc_data = create_valid_docling_document_data(texts=[{"text": "Test", "label": "paragraph"}])
        doc = DoclingDocument.model_validate(doc_data)
        
        serializer = OptimizedLexicalDocSerializer(doc=doc)
        
        # Process some elements to update statistics
        serializer._elements_processed = 10
        serializer._start_time = time.time() - 1.0  # 1 second ago
        
        stats = serializer.get_performance_stats()
        
        assert stats["elements_processed"] == 10
        assert stats["duration_ms"] > 0
        assert stats["elements_per_second"] > 0
        assert "configuration" in stats
    
    def test_serialize_optimization_modes(self):
        """Test different serialization optimization modes.""" 
        texts = [
            {"text": "Paragraph 1", "label": "paragraph"},
            {"text": "Paragraph 2", "label": "paragraph"}
        ]
        doc_data = create_valid_docling_document_data(texts=texts)
        doc = DoclingDocument.model_validate(doc_data)
        
        # Test standard optimization mode
        params_standard = OptimizedLexicalParams(
            enable_streaming=False,
            parallel_processing=False
        )
        serializer_standard = OptimizedLexicalDocSerializer(doc=doc, params=params_standard)
        result_standard = serializer_standard.serialize()
        assert result_standard.text is not None
        assert len(result_standard.text) > 0
        
        # Test streaming mode (but with small doc, should use optimized)
        params_streaming = OptimizedLexicalParams(
            enable_streaming=True,
            batch_size=1
        )
        serializer_streaming = OptimizedLexicalDocSerializer(doc=doc, params=params_streaming)
        result_streaming = serializer_streaming.serialize()
        assert result_streaming.text is not None
        
        # Both results should be valid JSON
        import json
        json.loads(result_standard.text)
        json.loads(result_streaming.text)


class TestEdgeCaseHandler:
    """Test suite for EdgeCaseHandler."""
    
    def test_edge_case_config_validation(self):
        """Test EdgeCaseConfig validation."""
        config = EdgeCaseConfig(
            max_file_size_bytes=1000000,
            max_memory_usage_mb=512,
            enable_recovery=True
        )
        
        assert config.max_file_size_bytes == 1000000
        assert config.max_memory_usage_mb == 512
        assert config.enable_recovery is True
    
    def test_handle_empty_document(self):
        """Test empty document handling."""
        handler = EdgeCaseHandler()
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            empty_file = Path(f.name)
        
        try:
            doc = handler.handle_empty_document(empty_file)
            
            assert isinstance(doc, DoclingDocument)
            assert doc.schema_name == "DoclingDocument"
            assert len(doc.texts) == 0
            assert len(doc.tables) == 0
            
        finally:
            empty_file.unlink()
    
    def test_handle_malformed_json(self):
        """Test malformed JSON recovery."""
        handler = EdgeCaseHandler(EdgeCaseConfig(enable_recovery=True))
        
        # Test fixable JSON
        malformed_json = '{"schema_name": "DoclingDocument", "version": "1.4.0", "texts": [],}'  # Trailing comma
        result = handler.handle_malformed_json(malformed_json, "test.json")
        
        assert isinstance(result, dict)
        assert result["schema_name"] == "DoclingDocument"
        
        # Test recovery disabled
        handler_no_recovery = EdgeCaseHandler(EdgeCaseConfig(enable_recovery=False))
        with pytest.raises(ValueError):
            handler_no_recovery.handle_malformed_json("invalid json", "test.json")
    
    def test_handle_deeply_nested_structure(self):
        """Test deeply nested structure handling."""
        handler = EdgeCaseHandler(EdgeCaseConfig(enable_recovery=True))
        
        # Create deeply nested structure
        nested_data = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
        
        # Should not flatten with default max depth
        result = handler.handle_deeply_nested_structure(nested_data, max_depth=10)
        assert result["level1"]["level2"]["level3"]["level4"]["level5"] == "deep"
        
        # Should flatten with low max depth
        result_flattened = handler.handle_deeply_nested_structure(nested_data, max_depth=3)
        assert "truncated" in str(result_flattened["level1"]["level2"]["level3"])
    
    def test_handle_extremely_large_file(self):
        """Test extremely large file handling."""
        handler = EdgeCaseHandler(EdgeCaseConfig(max_file_size_bytes=1000000))  # 1MB limit
        
        # Create mock large file
        large_file = Path("large_file.json")
        strategy = handler.handle_extremely_large_file(large_file, 100000000)  # 100MB
        
        assert strategy["strategy"] in ["chunked_processing", "optimized_processing"]
        assert "use_streaming" in strategy
        
        # Test file too large
        handler_strict = EdgeCaseHandler(EdgeCaseConfig(max_file_size_bytes=1000, enable_recovery=False))
        with pytest.raises(ValueError):
            handler_strict.handle_extremely_large_file(large_file, 100000)
    
    def test_handle_corrupted_document_structure(self):
        """Test corrupted document structure repair."""
        handler = EdgeCaseHandler(EdgeCaseConfig(enable_recovery=True))
        
        # Corrupted document with some salvageable parts
        corrupted_data = {
            "schema_name": "DoclingDocument",
            "texts": [
                {"text": "Valid text 1", "label": "paragraph"},
                {"invalid": "structure"},  # Invalid text item
                {"text": "Valid text 2", "label": "paragraph"}
            ],
            "tables": "invalid_tables",  # Invalid structure
            "body": {
                "children": [
                    {"cref": "#/texts/0"},
                    {"invalid": "child"},  # Invalid child
                    {"cref": "#/texts/2"}
                ]
            }
        }
        
        repaired = handler.handle_corrupted_document_structure(corrupted_data, "test.json")
        
        assert repaired["schema_name"] == "DoclingDocument"
        assert len(repaired["texts"]) == 2  # Only valid texts salvaged
        assert len(repaired["tables"]) == 0  # Invalid tables removed
        assert len(repaired["body"]["children"]) == 2  # Only valid children
    
    def test_file_processing_context_manager(self):
        """Test file processing context manager."""
        handler = EdgeCaseHandler()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_file = Path(f.name)
        
        try:
            # Test successful processing
            with handler.handle_file_processing(temp_file, "test_operation"):
                time.sleep(0.01)  # Simulate processing
            
            # Test with nonexistent file
            with pytest.raises(FileNotFoundError):
                with handler.handle_file_processing("nonexistent.json", "test_operation"):
                    pass
            
        finally:
            temp_file.unlink()
    
    def test_memory_exhaustion_handling(self):
        """Test memory exhaustion handling."""
        handler = EdgeCaseHandler(EdgeCaseConfig(enable_recovery=True))
        
        # Mock the _get_current_memory_usage method to simulate memory decrease after GC
        memory_values = [230.0]  # 230MB after GC (more than 20% improvement from 300MB)
        
        with patch.object(handler, '_get_current_memory_usage', side_effect=memory_values):
            with patch('gc.collect', return_value=100):  # Mock garbage collection
                # Should not raise with successful recovery
                handler.handle_memory_exhaustion("test_operation", 300.0)
    
    def test_processing_timeout_handling(self):
        """Test processing timeout handling."""
        handler = EdgeCaseHandler(EdgeCaseConfig(enable_recovery=True, enable_fallback_modes=True))
        
        # Test timeout with fallback
        with pytest.raises(TimeoutError) as exc_info:
            handler.handle_processing_timeout("test_operation", 600.0)
        
        assert "FALLBACK_REQUIRED" in str(exc_info.value)
        
        # Test timeout without recovery
        handler_no_recovery = EdgeCaseHandler(EdgeCaseConfig(enable_recovery=False))
        with pytest.raises(TimeoutError):
            handler_no_recovery.handle_processing_timeout("test_operation", 600.0)


if __name__ == "__main__":
    pytest.main([__file__])