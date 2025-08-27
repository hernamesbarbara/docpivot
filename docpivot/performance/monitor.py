"""Performance monitoring infrastructure for DocPivot operations."""

import time
import cProfile
import pstats
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar
from contextlib import contextmanager
from io import StringIO

from docling_core.types import DoclingDocument

from ..logging_config import get_logger, PerformanceLogger

logger = get_logger(__name__)
T = TypeVar('T')

# Performance thresholds and defaults
DEFAULT_MAX_FILE_SIZE_MB = 100
DEFAULT_STREAMING_THRESHOLD_MB = 10
DEFAULT_MEMORY_LIMIT_MB = 500
DEFAULT_CHUNK_SIZE = 8192
MIN_FILE_SIZE_BYTES = 1024
MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024  # 1GB


@dataclass
class PerformanceConfig:
    """Configuration options for performance optimization."""
    
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    streaming_threshold_mb: int = DEFAULT_STREAMING_THRESHOLD_MB
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB
    enable_caching: bool = True
    enable_progress_callbacks: bool = False
    chunk_size: int = DEFAULT_CHUNK_SIZE
    use_fast_json: bool = True
    enable_compression: bool = False
    parallel_processing: bool = False
    max_workers: int = 4
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        if self.streaming_threshold_mb <= 0:
            raise ValueError("streaming_threshold_mb must be positive") 
        if self.streaming_threshold_mb > self.max_file_size_mb:
            raise ValueError("streaming_threshold_mb cannot exceed max_file_size_mb")
        if self.memory_limit_mb <= 0:
            raise ValueError("memory_limit_mb must be positive")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation."""
    
    operation_name: str
    duration_ms: float
    memory_usage_mb: float = 0.0
    file_size_bytes: Optional[int] = None
    throughput_mbps: float = 0.0
    cpu_time_ms: float = 0.0
    peak_memory_mb: float = 0.0
    error_occurred: bool = False
    error_message: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def throughput_mb_per_second(self) -> float:
        """Calculate throughput in MB/s if file size is available."""
        if self.file_size_bytes and self.duration_ms > 0:
            file_size_mb = self.file_size_bytes / (1024 * 1024)
            duration_seconds = self.duration_ms / 1000
            return file_size_mb / duration_seconds
        return 0.0
    
    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score (throughput / memory usage)."""
        if self.memory_usage_mb > 0:
            return self.throughput_mb_per_second / self.memory_usage_mb
        return 0.0


class PerformanceMonitor:
    """Comprehensive performance monitoring and profiling tool."""
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        """Initialize performance monitor with configuration.
        
        Args:
            config: Optional performance configuration
        """
        self.config = config or PerformanceConfig()
        self.metrics_history: List[PerformanceMetrics] = []
        self.metrics = self.metrics_history  # Alias for backward compatibility
        self._active_profiles: Dict[str, cProfile.Profile] = {}
        self._perf_logger = PerformanceLogger(logger)
        self._lock = threading.RLock()
        
    def profile_reader(self, reader_cls, file_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """Profile reader performance with comprehensive metrics.
        
        Args:
            reader_cls: Reader class to profile
            file_path: Path to file to read
            **kwargs: Additional arguments for reader
            
        Returns:
            Dictionary with profiling results and metrics
        """
        file_path = Path(file_path)
        operation_name = f"{reader_cls.__name__}.load_data"
        
        logger.info(f"Profiling reader: {operation_name} on {file_path.name}")
        
        # Get file size for throughput calculations
        file_size = file_path.stat().st_size if file_path.exists() else 0
        
        with self._profile_context(operation_name) as profiler:
            try:
                # Initialize reader and load data
                reader = reader_cls(**kwargs)
                start_time = time.time()
                
                # Monitor memory during operation
                with self._memory_monitor() as memory_tracker:
                    document = reader.load_data(file_path)
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Create metrics
                metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_tracker.peak_usage_mb,
                    file_size_bytes=file_size,
                    context={
                        "file_path": str(file_path),
                        "reader_class": reader_cls.__name__,
                        "document_texts": len(document.texts),
                        "document_tables": len(document.tables) if hasattr(document, 'tables') else 0,
                        "kwargs": kwargs
                    }
                )
                
                # Add to history
                with self._lock:
                    self.metrics_history.append(metrics)
                
                # Generate profile stats
                stats = self._generate_profile_stats(profiler)
                
                result = {
                    "metrics": metrics,
                    "profile_stats": stats,
                    "document": document,
                    "recommendations": self._generate_reader_recommendations(metrics)
                }
                
                logger.info(f"Reader profiling complete: {duration_ms:.2f}ms, {metrics.throughput_mb_per_second:.2f} MB/s")
                return result
                
            except Exception as e:
                # Record error metrics
                error_metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_occurred=True,
                    error_message=str(e),
                    file_size_bytes=file_size,
                    context={
                        "file_path": str(file_path),
                        "reader_class": reader_cls.__name__,
                        "error": str(e),
                        "kwargs": kwargs
                    }
                )
                
                with self._lock:
                    self.metrics_history.append(error_metrics)
                
                logger.error(f"Reader profiling failed: {e}")
                raise
    
    def profile_serializer(self, serializer_cls, doc: DoclingDocument, **kwargs) -> Dict[str, Any]:
        """Profile serializer performance with comprehensive metrics.
        
        Args:
            serializer_cls: Serializer class to profile
            doc: DoclingDocument to serialize
            **kwargs: Additional arguments for serializer
            
        Returns:
            Dictionary with profiling results and metrics
        """
        operation_name = f"{serializer_cls.__name__}.serialize"
        
        logger.info(f"Profiling serializer: {operation_name}")
        
        # Estimate document size for throughput calculations
        doc_size_estimate = len(doc.texts) * 100  # Rough estimate
        
        with self._profile_context(operation_name) as profiler:
            try:
                # Initialize serializer
                serializer = serializer_cls(doc=doc, **kwargs)
                start_time = time.time()
                
                # Monitor memory during operation
                with self._memory_monitor() as memory_tracker:
                    result = serializer.serialize()
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Calculate output size
                output_size = len(result.text) if hasattr(result, 'text') else len(str(result))
                
                # Create metrics
                metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_tracker.peak_usage_mb,
                    file_size_bytes=output_size,
                    context={
                        "serializer_class": serializer_cls.__name__,
                        "input_texts": len(doc.texts),
                        "input_tables": len(doc.tables) if hasattr(doc, 'tables') else 0,
                        "output_size": output_size,
                        "kwargs": kwargs
                    }
                )
                
                # Add to history
                with self._lock:
                    self.metrics_history.append(metrics)
                
                # Generate profile stats
                stats = self._generate_profile_stats(profiler)
                
                result_dict = {
                    "metrics": metrics,
                    "profile_stats": stats,
                    "serialization_result": result,
                    "recommendations": self._generate_serializer_recommendations(metrics)
                }
                
                logger.info(f"Serializer profiling complete: {duration_ms:.2f}ms, {output_size} chars output")
                return result_dict
                
            except Exception as e:
                # Record error metrics
                error_metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_occurred=True,
                    error_message=str(e),
                    context={
                        "serializer_class": serializer_cls.__name__,
                        "input_texts": len(doc.texts),
                        "error": str(e),
                        "kwargs": kwargs
                    }
                )
                
                with self._lock:
                    self.metrics_history.append(error_metrics)
                
                logger.error(f"Serializer profiling failed: {e}")
                raise
    
    def memory_profile(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Monitor memory usage during function execution.
        
        Args:
            func: Function to profile
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
        """
        operation_name = f"{func.__name__}_memory_profile"
        
        with self._memory_monitor() as memory_tracker:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Create metrics
                metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_tracker.peak_usage_mb,
                    peak_memory_mb=memory_tracker.peak_usage_mb,
                    context={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    }
                )
                
                with self._lock:
                    self.metrics_history.append(metrics)
                
                logger.info(f"Memory profiling complete for {func.__name__}: {memory_tracker.peak_usage_mb:.2f} MB peak")
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    duration_ms=duration_ms,
                    memory_usage_mb=memory_tracker.peak_usage_mb,
                    error_occurred=True,
                    error_message=str(e),
                    context={
                        "function": func.__name__,
                        "error": str(e)
                    }
                )
                
                with self._lock:
                    self.metrics_history.append(error_metrics)
                
                logger.error(f"Memory profiling failed for {func.__name__}: {e}")
                raise
    
    @contextmanager
    def _profile_context(self, operation_name: str):
        """Context manager for cProfile profiling."""
        profiler = cProfile.Profile()
        self._active_profiles[operation_name] = profiler
        
        try:
            profiler.enable()
            yield profiler
        finally:
            profiler.disable()
            self._active_profiles.pop(operation_name, None)
    
    @contextmanager 
    def _memory_monitor(self):
        """Context manager for memory monitoring."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss / (1024 * 1024)  # MB
            peak_memory = start_memory
            
            class MemoryTracker:
                def __init__(self):
                    self.peak_usage_mb = start_memory
                    
                def update(self):
                    current = process.memory_info().rss / (1024 * 1024)
                    self.peak_usage_mb = max(self.peak_usage_mb, current)
                    
            tracker = MemoryTracker()
            
            # Start monitoring thread
            stop_monitoring = threading.Event()
            
            def monitor():
                while not stop_monitoring.is_set():
                    tracker.update()
                    time.sleep(0.1)  # Check every 100ms
                    
            monitor_thread = threading.Thread(target=monitor, daemon=True)
            monitor_thread.start()
            
            try:
                yield tracker
            finally:
                stop_monitoring.set()
                monitor_thread.join(timeout=1.0)
                tracker.update()  # Final update
                
        except ImportError:
            # Fallback if psutil not available
            logger.warning("psutil not available for memory monitoring")
            
            class DummyTracker:
                peak_usage_mb = 0.0
                
            yield DummyTracker()
    
    def _generate_profile_stats(self, profiler: cProfile.Profile) -> Dict[str, Any]:
        """Generate readable profile statistics."""
        try:
            stats_stream = StringIO()
            stats = pstats.Stats(profiler, stream=stats_stream)
            stats.sort_stats('cumulative')
            stats.print_stats(20)  # Top 20 functions
            
            return {
                "stats_text": stats_stream.getvalue(),
                "total_calls": stats.total_calls,
                "total_time": stats.total_tt
            }
        except Exception as e:
            logger.warning(f"Failed to generate profile stats: {e}")
            return {"error": str(e)}
    
    def _generate_reader_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate performance recommendations for readers."""
        recommendations = []
        
        # File size recommendations
        if metrics.file_size_bytes and metrics.file_size_bytes > self.config.streaming_threshold_mb * 1024 * 1024:
            recommendations.append("Consider using streaming mode for large files")
        
        # Memory usage recommendations
        if metrics.memory_usage_mb > self.config.memory_limit_mb * 0.8:
            recommendations.append("Memory usage is high - consider chunked processing")
        
        # Performance recommendations
        if metrics.duration_ms > 10000:  # 10 seconds
            recommendations.append("Long processing time - consider parallel processing or optimization")
        
        # Throughput recommendations
        if metrics.throughput_mb_per_second < 1.0:
            recommendations.append("Low throughput - check I/O performance and JSON parsing efficiency")
        
        return recommendations
    
    def _generate_serializer_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate performance recommendations for serializers."""
        recommendations = []
        
        # Memory usage recommendations
        if metrics.memory_usage_mb > self.config.memory_limit_mb * 0.8:
            recommendations.append("High memory usage - consider streaming serialization")
        
        # Output size recommendations
        output_size = metrics.context.get("output_size", 0)
        if output_size > 10 * 1024 * 1024:  # 10MB
            recommendations.append("Large output size - consider compact serialization options")
        
        # Performance recommendations
        if metrics.duration_ms > 5000:  # 5 seconds
            recommendations.append("Long serialization time - consider optimization or parallel processing")
        
        return recommendations
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected performance metrics."""
        with self._lock:
            if not self.metrics_history:
                return {"message": "No metrics collected"}
            
            # Calculate aggregates
            total_operations = len(self.metrics_history)
            successful_operations = len([m for m in self.metrics_history if not m.error_occurred])
            error_rate = (total_operations - successful_operations) / total_operations
            
            durations = [m.duration_ms for m in self.metrics_history if not m.error_occurred]
            memory_usage = [m.memory_usage_mb for m in self.metrics_history if not m.error_occurred]
            throughputs = [m.throughput_mb_per_second for m in self.metrics_history if m.throughput_mb_per_second > 0]
            
            return {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "error_rate": error_rate,
                "performance_summary": {
                    "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                    "max_duration_ms": max(durations) if durations else 0,
                    "min_duration_ms": min(durations) if durations else 0,
                    "avg_memory_mb": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                    "max_memory_mb": max(memory_usage) if memory_usage else 0,
                    "avg_throughput_mbps": sum(throughputs) / len(throughputs) if throughputs else 0,
                    "max_throughput_mbps": max(throughputs) if throughputs else 0
                },
                "recent_operations": self.metrics_history[-10:]  # Last 10 operations
            }
    
    def reset_metrics(self):
        """Reset all collected metrics."""
        with self._lock:
            self.metrics_history.clear()
        logger.info("Performance metrics reset")
    
    def export_metrics(self, file_path: Union[str, Path], format: str = "json"):
        """Export metrics to file.
        
        Args:
            file_path: Path to export file
            format: Export format ("json" or "csv")
        """
        import json
        import csv
        
        file_path = Path(file_path)
        
        with self._lock:
            if format.lower() == "json":
                with open(file_path, 'w') as f:
                    json.dump([
                        {
                            "operation_name": m.operation_name,
                            "duration_ms": m.duration_ms,
                            "memory_usage_mb": m.memory_usage_mb,
                            "file_size_bytes": m.file_size_bytes,
                            "throughput_mbps": m.throughput_mb_per_second,
                            "error_occurred": m.error_occurred,
                            "error_message": m.error_message,
                            "context": m.context
                        }
                        for m in self.metrics_history
                    ], f, indent=2)
            
            elif format.lower() == "csv":
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "operation_name", "duration_ms", "memory_usage_mb", 
                        "file_size_bytes", "throughput_mbps", "error_occurred", "error_message"
                    ])
                    
                    for m in self.metrics_history:
                        writer.writerow([
                            m.operation_name, m.duration_ms, m.memory_usage_mb,
                            m.file_size_bytes, m.throughput_mb_per_second,
                            m.error_occurred, m.error_message
                        ])
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Exported {len(self.metrics_history)} metrics to {file_path}")