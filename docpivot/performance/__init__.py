"""Performance monitoring and optimization tools for DocPivot."""

from .monitor import PerformanceMonitor, PerformanceConfig, PerformanceMetrics
from .memory_profiler import MemoryProfiler, MemoryUsage, MemoryReport

__all__ = [
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

# Lazy import to avoid circular dependencies
def get_benchmark_suite():
    """Get BenchmarkSuite class (lazy import to avoid circular dependencies)."""
    from .benchmarks import BenchmarkSuite
    return BenchmarkSuite

def get_reader_benchmark():
    """Get ReaderBenchmark class (lazy import to avoid circular dependencies)."""
    from .benchmarks import ReaderBenchmark
    return ReaderBenchmark

def get_serializer_benchmark():
    """Get SerializerBenchmark class (lazy import to avoid circular dependencies)."""
    from .benchmarks import SerializerBenchmark
    return SerializerBenchmark


def __getattr__(name):
    """Lazy import for benchmark classes to avoid circular dependencies."""
    if name == "BenchmarkSuite":
        from .benchmarks import BenchmarkSuite
        return BenchmarkSuite
    elif name == "ReaderBenchmark":
        from .benchmarks import ReaderBenchmark
        return ReaderBenchmark
    elif name == "SerializerBenchmark":
        from .benchmarks import SerializerBenchmark
        return SerializerBenchmark
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
