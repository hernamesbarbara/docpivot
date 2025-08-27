"""Performance benchmarking suite for DocPivot operations."""

import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Type, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import tempfile
import shutil

from docling_core.types import DoclingDocument

from .monitor import PerformanceMonitor, PerformanceConfig, PerformanceMetrics
from .memory_profiler import MemoryProfiler
from ..io.readers.basereader import BaseReader
from ..io.readers.doclingjsonreader import DoclingJsonReader
from ..io.serializers.lexicaldocserializer import LexicalDocSerializer
from ..logging_config import get_logger

logger = get_logger(__name__)

# Benchmark constants
DEFAULT_ITERATIONS = 5
BENCHMARK_FILE_SIZES = [1024, 10*1024, 100*1024, 1024*1024, 10*1024*1024]  # 1KB to 10MB
BENCHMARK_COMPLEXITIES = ["simple", "medium", "complex"]


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    
    operation_name: str
    test_case: str
    iterations: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    std_dev_ms: float
    avg_memory_mb: float
    peak_memory_mb: float
    throughput_mbps: float
    success_rate: float
    error_count: int
    errors: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def performance_score(self) -> float:
        """Calculate overall performance score (higher is better)."""
        if self.avg_duration_ms == 0:
            return 0.0
        
        # Base score from throughput
        base_score = self.throughput_mbps * 100
        
        # Penalty for high memory usage
        memory_penalty = min(self.peak_memory_mb / 100, 1.0)
        
        # Penalty for errors
        error_penalty = (1.0 - self.success_rate) * 50
        
        # Stability bonus (lower std dev is better)
        if self.avg_duration_ms > 0:
            stability_bonus = max(0, 10 - (self.std_dev_ms / self.avg_duration_ms) * 100)
        else:
            stability_bonus = 0
        
        return max(0, base_score - memory_penalty - error_penalty + stability_bonus)


@dataclass
class BenchmarkSuite:
    """Comprehensive benchmarking suite for DocPivot."""
    
    config: PerformanceConfig = field(default_factory=PerformanceConfig)
    iterations: int = DEFAULT_ITERATIONS
    temp_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Initialize benchmarking suite."""
        self.monitor = PerformanceMonitor(self.config)
        self.memory_profiler = MemoryProfiler()
        self.results: List[BenchmarkResult] = []
        
        # Create temporary directory for test files
        self.temp_dir = Path(tempfile.mkdtemp(prefix="docpivot_benchmark_"))
        logger.info(f"Benchmark temp directory: {self.temp_dir}")
    
    def __del__(self):
        """Cleanup temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up benchmark temp directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup benchmark temp directory: {e}")
    
    def run_full_suite(self) -> Dict[str, Any]:
        """Run the complete benchmark suite.
        
        Returns:
            Comprehensive benchmark report
        """
        logger.info("Starting full DocPivot benchmark suite")
        start_time = time.time()
        
        try:
            # Run reader benchmarks
            logger.info("Running reader benchmarks...")
            reader_results = self.benchmark_readers()
            
            # Run serializer benchmarks 
            logger.info("Running serializer benchmarks...")
            serializer_results = self.benchmark_serializers()
            
            # Run memory benchmarks
            logger.info("Running memory benchmarks...")
            memory_results = self.benchmark_memory_usage()
            
            # Run scaling benchmarks
            logger.info("Running scaling benchmarks...")
            scaling_results = self.benchmark_scaling()
            
            # Run concurrent benchmarks
            logger.info("Running concurrency benchmarks...")
            concurrency_results = self.benchmark_concurrency()
            
            total_time = time.time() - start_time
            
            # Generate comprehensive report
            report = {
                "benchmark_summary": {
                    "total_duration_sec": total_time,
                    "total_tests": len(self.results),
                    "successful_tests": len([r for r in self.results if r.success_rate == 1.0]),
                    "failed_tests": len([r for r in self.results if r.success_rate < 1.0]),
                    "avg_performance_score": sum(r.performance_score for r in self.results) / len(self.results) if self.results else 0
                },
                "reader_benchmarks": reader_results,
                "serializer_benchmarks": serializer_results, 
                "memory_benchmarks": memory_results,
                "scaling_benchmarks": scaling_results,
                "concurrency_benchmarks": concurrency_results,
                "recommendations": self._generate_recommendations(),
                "detailed_results": self.results
            }
            
            logger.info(f"Benchmark suite completed in {total_time:.2f} seconds")
            return report
            
        except Exception as e:
            logger.error(f"Benchmark suite failed: {e}")
            raise
    
    def benchmark_readers(self) -> Dict[str, Any]:
        """Benchmark reader performance across different scenarios."""
        logger.info("Benchmarking reader performance")
        
        reader_results = {}
        
        # Test DoclingJsonReader with different file sizes
        for size_bytes in BENCHMARK_FILE_SIZES:
            test_file = self._create_test_docling_file(size_bytes)
            
            result = self._benchmark_reader(
                DoclingJsonReader,
                test_file,
                f"docling_reader_{size_bytes}_bytes",
                {"file_size": size_bytes}
            )
            
            reader_results[f"docling_{size_bytes}_bytes"] = result
        
        # Test with different document complexities
        for complexity in BENCHMARK_COMPLEXITIES:
            test_file = self._create_test_docling_file(100 * 1024, complexity=complexity)
            
            result = self._benchmark_reader(
                DoclingJsonReader,
                test_file, 
                f"docling_reader_{complexity}",
                {"complexity": complexity, "file_size": 100 * 1024}
            )
            
            reader_results[f"docling_{complexity}"] = result
        
        return reader_results
    
    def benchmark_serializers(self) -> Dict[str, Any]:
        """Benchmark serializer performance across different scenarios."""
        logger.info("Benchmarking serializer performance")
        
        serializer_results = {}
        
        # Test LexicalDocSerializer with different document sizes
        for complexity in BENCHMARK_COMPLEXITIES:
            doc = self._create_test_document(complexity=complexity)
            
            # Test with different serialization parameters
            test_configs = [
                ("compact", {"indent_json": False, "include_metadata": False, "preserve_formatting": False}),
                ("standard", {"indent_json": True, "include_metadata": True, "preserve_formatting": True}),
                ("minimal", {"indent_json": False, "include_metadata": False, "preserve_formatting": False})
            ]
            
            for config_name, params in test_configs:
                result = self._benchmark_serializer(
                    LexicalDocSerializer,
                    doc,
                    f"lexical_{complexity}_{config_name}",
                    params,
                    {"complexity": complexity, "config": config_name}
                )
                
                serializer_results[f"lexical_{complexity}_{config_name}"] = result
        
        return serializer_results
    
    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage patterns."""
        logger.info("Benchmarking memory usage patterns")
        
        memory_results = {}
        
        # Test memory usage with increasing file sizes
        for size_bytes in BENCHMARK_FILE_SIZES[-3:]:  # Test largest files only
            test_file = self._create_test_docling_file(size_bytes)
            
            with self.memory_profiler.profile_memory(f"memory_test_{size_bytes}") as report:
                try:
                    reader = DoclingJsonReader()
                    doc = reader.load_data(test_file)
                    
                    serializer = LexicalDocSerializer(doc=doc)
                    result = serializer.serialize()
                    
                    memory_results[f"memory_{size_bytes}_bytes"] = {
                        "peak_memory_mb": report.peak_memory_mb,
                        "memory_delta_mb": report.memory_delta_mb,
                        "warnings": report.warnings,
                        "efficiency": report.memory_efficiency,
                        "output_size": len(result.text)
                    }
                    
                except Exception as e:
                    memory_results[f"memory_{size_bytes}_bytes"] = {
                        "error": str(e),
                        "peak_memory_mb": report.peak_memory_mb
                    }
        
        return memory_results
    
    def benchmark_scaling(self) -> Dict[str, Any]:
        """Benchmark scaling behavior with increasing load."""
        logger.info("Benchmarking scaling behavior")
        
        scaling_results = {}
        
        # Test document count scaling
        doc_counts = [1, 5, 10, 25, 50]
        base_doc = self._create_test_document("medium")
        
        for count in doc_counts:
            start_time = time.time()
            memory_start = self._get_memory_usage()
            
            try:
                # Simulate processing multiple documents
                results = []
                for i in range(count):
                    serializer = LexicalDocSerializer(doc=base_doc)
                    result = serializer.serialize()
                    results.append(result)
                
                duration = (time.time() - start_time) * 1000
                memory_peak = self._get_memory_usage()
                
                scaling_results[f"doc_count_{count}"] = {
                    "duration_ms": duration,
                    "memory_usage_mb": memory_peak - memory_start,
                    "throughput_docs_per_sec": count / (duration / 1000) if duration > 0 else 0,
                    "avg_duration_per_doc_ms": duration / count if count > 0 else 0,
                    "success": True
                }
                
            except Exception as e:
                scaling_results[f"doc_count_{count}"] = {
                    "error": str(e),
                    "success": False
                }
        
        return scaling_results
    
    def benchmark_concurrency(self) -> Dict[str, Any]:
        """Benchmark concurrent processing performance."""
        logger.info("Benchmarking concurrency performance")
        
        concurrency_results = {}
        
        # Test different worker counts
        worker_counts = [1, 2, 4, 8]
        test_files = [self._create_test_docling_file(50 * 1024) for _ in range(20)]
        
        for workers in worker_counts:
            start_time = time.time()
            
            try:
                if workers == 1:
                    # Sequential processing
                    results = []
                    for file_path in test_files:
                        reader = DoclingJsonReader()
                        doc = reader.load_data(file_path)
                        results.append(doc)
                else:
                    # Parallel processing
                    results = []
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = []
                        for file_path in test_files:
                            future = executor.submit(self._load_document_worker, file_path)
                            futures.append(future)
                        
                        for future in as_completed(futures):
                            results.append(future.result())
                
                duration = (time.time() - start_time) * 1000
                
                concurrency_results[f"workers_{workers}"] = {
                    "duration_ms": duration,
                    "documents_processed": len(results),
                    "throughput_docs_per_sec": len(results) / (duration / 1000) if duration > 0 else 0,
                    "speedup": concurrency_results.get("workers_1", {}).get("duration_ms", duration) / duration if "workers_1" in concurrency_results else 1.0,
                    "efficiency": (concurrency_results.get("workers_1", {}).get("duration_ms", duration) / duration) / workers if "workers_1" in concurrency_results else 1.0 / workers,
                    "success": True
                }
                
            except Exception as e:
                concurrency_results[f"workers_{workers}"] = {
                    "error": str(e),
                    "success": False
                }
        
        return concurrency_results
    
    def _benchmark_reader(self, reader_cls: Type[BaseReader], file_path: Path, test_name: str, context: Dict[str, Any] = None) -> BenchmarkResult:
        """Benchmark a specific reader."""
        context = context or {}
        durations = []
        memory_usages = []
        errors = []
        successful_runs = 0
        
        logger.debug(f"Benchmarking {test_name} with {self.iterations} iterations")
        
        for i in range(self.iterations):
            try:
                with self.memory_profiler.profile_memory(f"{test_name}_iter_{i}") as memory_report:
                    start_time = time.time()
                    
                    reader = reader_cls()
                    doc = reader.load_data(file_path)
                    
                    duration_ms = (time.time() - start_time) * 1000
                    durations.append(duration_ms)
                    memory_usages.append(memory_report.peak_memory_mb)
                    successful_runs += 1
                    
            except Exception as e:
                errors.append(str(e))
                logger.warning(f"Benchmark iteration {i} failed: {e}")
        
        # Calculate statistics
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            std_dev = self._calculate_std_dev(durations)
            avg_memory = sum(memory_usages) / len(memory_usages)
            peak_memory = max(memory_usages) if memory_usages else 0
        else:
            avg_duration = min_duration = max_duration = std_dev = avg_memory = peak_memory = 0
        
        # Calculate throughput
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        throughput = (file_size_mb / (avg_duration / 1000)) if avg_duration > 0 else 0
        
        success_rate = successful_runs / self.iterations
        
        result = BenchmarkResult(
            operation_name=f"{reader_cls.__name__}_benchmark",
            test_case=test_name,
            iterations=self.iterations,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            std_dev_ms=std_dev,
            avg_memory_mb=avg_memory,
            peak_memory_mb=peak_memory,
            throughput_mbps=throughput,
            success_rate=success_rate,
            error_count=len(errors),
            errors=errors[:5],  # Keep first 5 errors
            context=context
        )
        
        self.results.append(result)
        return result
    
    def _benchmark_serializer(self, serializer_cls, doc: DoclingDocument, test_name: str, serializer_params: Dict[str, Any], context: Dict[str, Any] = None) -> BenchmarkResult:
        """Benchmark a specific serializer."""
        context = context or {}
        durations = []
        memory_usages = []
        output_sizes = []
        errors = []
        successful_runs = 0
        
        logger.debug(f"Benchmarking serializer {test_name} with {self.iterations} iterations")
        
        for i in range(self.iterations):
            try:
                with self.memory_profiler.profile_memory(f"{test_name}_iter_{i}") as memory_report:
                    start_time = time.time()
                    
                    serializer = serializer_cls(doc=doc, **serializer_params)
                    result = serializer.serialize()
                    
                    duration_ms = (time.time() - start_time) * 1000
                    durations.append(duration_ms)
                    memory_usages.append(memory_report.peak_memory_mb)
                    output_sizes.append(len(result.text))
                    successful_runs += 1
                    
            except Exception as e:
                errors.append(str(e))
                logger.warning(f"Serializer benchmark iteration {i} failed: {e}")
        
        # Calculate statistics
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            std_dev = self._calculate_std_dev(durations)
            avg_memory = sum(memory_usages) / len(memory_usages)
            peak_memory = max(memory_usages) if memory_usages else 0
            avg_output_size = sum(output_sizes) / len(output_sizes) if output_sizes else 0
        else:
            avg_duration = min_duration = max_duration = std_dev = avg_memory = peak_memory = avg_output_size = 0
        
        # Calculate throughput (based on output size)
        output_size_mb = avg_output_size / (1024 * 1024)
        throughput = (output_size_mb / (avg_duration / 1000)) if avg_duration > 0 else 0
        
        success_rate = successful_runs / self.iterations
        
        context.update({"avg_output_size": avg_output_size})
        
        result = BenchmarkResult(
            operation_name=f"{serializer_cls.__name__}_benchmark",
            test_case=test_name,
            iterations=self.iterations,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            std_dev_ms=std_dev,
            avg_memory_mb=avg_memory,
            peak_memory_mb=peak_memory,
            throughput_mbps=throughput,
            success_rate=success_rate,
            error_count=len(errors),
            errors=errors[:5],
            context=context
        )
        
        self.results.append(result)
        return result
    
    def _create_test_docling_file(self, size_bytes: int, complexity: str = "medium") -> Path:
        """Create a test DoclingDocument JSON file of specified size and complexity."""
        # Base document structure
        base_doc = {
            "schema_name": "DoclingDocument",
            "version": "2.0.0",
            "name": f"test_doc_{size_bytes}_{complexity}",
            "texts": [],
            "tables": [],
            "groups": [],
            "body": {"children": []}
        }
        
        # Calculate number of text items needed for target size
        if complexity == "simple":
            text_length = 100
            table_count = 0
        elif complexity == "medium": 
            text_length = 200
            table_count = 2
        else:  # complex
            text_length = 300
            table_count = 5
        
        # Estimate size per text item (JSON overhead)
        estimated_item_size = text_length + 150  # JSON structure overhead
        target_text_items = max(1, (size_bytes - 1000) // estimated_item_size)  # Reserve 1KB for structure
        
        # Generate text items
        for i in range(target_text_items):
            text_item = {
                "label": "paragraph" if i % 3 != 0 else "section_header",
                "text": f"This is test text item {i}. " * (text_length // 20),
                "bbox": {"l": 0, "t": i * 20, "r": 500, "b": (i + 1) * 20}
            }
            base_doc["texts"].append(text_item)
            base_doc["body"]["children"].append({"cref": f"#/texts/{i}"})
        
        # Add tables for complexity
        for i in range(table_count):
            table_data = {
                "label": "table",
                "data": {
                    "grid": [
                        [{"text": f"Header {j}"} for j in range(3)],
                        [{"text": f"Row {i} Col {j}"} for j in range(3)]
                    ]
                }
            }
            base_doc["tables"].append(table_data)
            base_doc["body"]["children"].append({"cref": f"#/tables/{i}"})
        
        # Write to file
        file_path = self.temp_dir / f"test_{size_bytes}_{complexity}.docling.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(base_doc, f, indent=2 if complexity != "simple" else None)
        
        # Verify file size is approximately correct
        actual_size = file_path.stat().st_size
        logger.debug(f"Created test file {file_path.name}: {actual_size} bytes (target: {size_bytes})")
        
        return file_path
    
    def _create_test_document(self, complexity: str = "medium") -> DoclingDocument:
        """Create a test DoclingDocument for serialization benchmarks."""
        test_file = self._create_test_docling_file(50 * 1024, complexity)
        reader = DoclingJsonReader()
        return reader.load_data(test_file)
    
    def _load_document_worker(self, file_path: Path) -> DoclingDocument:
        """Worker function for concurrent document loading."""
        reader = DoclingJsonReader()
        return reader.load_data(file_path)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on benchmark results."""
        recommendations = []
        
        if not self.results:
            return ["No benchmark data available for recommendations"]
        
        # Analyze performance scores
        avg_score = sum(r.performance_score for r in self.results) / len(self.results)
        low_performers = [r for r in self.results if r.performance_score < avg_score * 0.7]
        
        if low_performers:
            recommendations.append(f"Found {len(low_performers)} operations with below-average performance")
        
        # Memory usage analysis
        high_memory_ops = [r for r in self.results if r.peak_memory_mb > 200]  # 200MB threshold
        if high_memory_ops:
            recommendations.append(f"{len(high_memory_ops)} operations use >200MB memory - consider optimization")
        
        # Error rate analysis
        error_rate = sum(r.error_count for r in self.results) / len(self.results)
        if error_rate > 0.1:
            recommendations.append(f"High error rate ({error_rate:.2%}) - investigate failure causes")
        
        # Throughput analysis
        avg_throughput = sum(r.throughput_mbps for r in self.results) / len(self.results)
        if avg_throughput < 1.0:
            recommendations.append("Low average throughput <1 MB/s - consider I/O optimization")
        
        return recommendations


# Specialized benchmark classes for different operation types
class ReaderBenchmark:
    """Specialized benchmarking for reader operations."""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.suite = BenchmarkSuite(self.config)
    
    def benchmark_file_sizes(self, reader_cls: Type[BaseReader]) -> Dict[str, Any]:
        """Benchmark reader with various file sizes."""
        results = {}
        
        for size in BENCHMARK_FILE_SIZES:
            test_file = self.suite._create_test_docling_file(size)
            result = self.suite._benchmark_reader(reader_cls, test_file, f"size_{size}")
            results[f"{size}_bytes"] = result
        
        return results
    
    def benchmark_document_complexity(self, reader_cls: Type[BaseReader]) -> Dict[str, Any]:
        """Benchmark reader with different document complexities.""" 
        results = {}
        
        for complexity in BENCHMARK_COMPLEXITIES:
            test_file = self.suite._create_test_docling_file(100 * 1024, complexity)
            result = self.suite._benchmark_reader(reader_cls, test_file, f"complexity_{complexity}")
            results[complexity] = result
        
        return results


class SerializerBenchmark:
    """Specialized benchmarking for serializer operations."""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig() 
        self.suite = BenchmarkSuite(self.config)
    
    def benchmark_serialization_options(self, serializer_cls, doc: DoclingDocument) -> Dict[str, Any]:
        """Benchmark serializer with different configuration options."""
        results = {}
        
        configs = {
            "minimal": {"indent_json": False, "include_metadata": False, "preserve_formatting": False},
            "compact": {"indent_json": False, "include_metadata": True, "preserve_formatting": False}, 
            "standard": {"indent_json": True, "include_metadata": True, "preserve_formatting": True},
            "full_featured": {"indent_json": True, "include_metadata": True, "preserve_formatting": True, "version": 2}
        }
        
        for config_name, params in configs.items():
            result = self.suite._benchmark_serializer(serializer_cls, doc, f"config_{config_name}", params)
            results[config_name] = result
        
        return results