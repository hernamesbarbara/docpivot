"""Memory profiling utilities for DocPivot operations."""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, TypeVar
from contextlib import contextmanager

from ..logging_config import get_logger

logger = get_logger(__name__)
T = TypeVar("T")

# Memory thresholds
DEFAULT_MEMORY_WARNING_MB = 500
DEFAULT_MEMORY_CRITICAL_MB = 1000
DEFAULT_SAMPLE_INTERVAL_MS = 100


@dataclass
class MemoryUsage:
    """Represents memory usage at a point in time."""

    timestamp: float
    rss_mb: float  # Resident set size
    vms_mb: float  # Virtual memory size
    percent: float  # Memory usage percentage
    available_mb: float = 0.0


@dataclass
class MemoryReport:
    """Comprehensive memory usage report."""

    operation_name: str
    start_time: float
    end_time: float
    duration_ms: float
    initial_memory_mb: float
    peak_memory_mb: float
    final_memory_mb: float
    memory_delta_mb: float
    samples: List[MemoryUsage] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def memory_efficiency(self) -> float:
        """Calculate memory efficiency score (lower delta is better)."""
        if self.peak_memory_mb > 0:
            return self.memory_delta_mb / self.peak_memory_mb
        return 0.0

    @property
    def average_memory_mb(self) -> float:
        """Calculate average memory usage during operation."""
        if self.samples:
            return sum(sample.rss_mb for sample in self.samples) / len(self.samples)
        return 0.0


class MemoryProfiler:
    """Advanced memory profiling for DocPivot operations."""

    def __init__(
        self,
        warning_threshold_mb: int = DEFAULT_MEMORY_WARNING_MB,
        critical_threshold_mb: int = DEFAULT_MEMORY_CRITICAL_MB,
        sample_interval_ms: int = DEFAULT_SAMPLE_INTERVAL_MS,
    ):
        """Initialize memory profiler.

        Args:
            warning_threshold_mb: Memory threshold for warnings
            critical_threshold_mb: Memory threshold for critical alerts
            sample_interval_ms: Sampling interval in milliseconds
        """
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.sample_interval_ms = sample_interval_ms
        self._reports: List[MemoryReport] = []

        # Check if psutil is available
        try:
            import psutil

            self._psutil_available = True
            logger.debug("psutil available for advanced memory monitoring")
        except ImportError:
            self._psutil_available = False
            logger.warning("psutil not available - using basic memory monitoring")

    @contextmanager
    def profile_memory(self, operation_name: str):
        """Context manager for memory profiling.

        Args:
            operation_name: Name of the operation being profiled

        Yields:
            MemoryReport: Live memory report that updates during operation
        """
        if not self._psutil_available:
            # Fallback to basic monitoring
            with self._basic_memory_profile(operation_name) as report:
                yield report
            return

        import psutil
        import os

        process = psutil.Process(os.getpid())
        start_time = time.time()

        # Initial memory reading
        initial_memory = process.memory_info()
        initial_memory_mb = initial_memory.rss / (1024 * 1024)

        # Create report object
        report = MemoryReport(
            operation_name=operation_name,
            start_time=start_time,
            end_time=0.0,
            duration_ms=0.0,
            initial_memory_mb=initial_memory_mb,
            peak_memory_mb=initial_memory_mb,
            final_memory_mb=0.0,
            memory_delta_mb=0.0,
        )

        # Start monitoring thread
        stop_event = threading.Event()
        monitoring_thread = threading.Thread(
            target=self._monitor_memory, args=(process, report, stop_event), daemon=True
        )
        monitoring_thread.start()

        try:
            logger.info(
                f"Starting memory profiling for {operation_name} (initial: {initial_memory_mb:.2f} MB)"
            )
            yield report

        finally:
            # Stop monitoring and finalize report
            stop_event.set()
            monitoring_thread.join(timeout=1.0)

            end_time = time.time()
            final_memory = process.memory_info()
            final_memory_mb = final_memory.rss / (1024 * 1024)

            report.end_time = end_time
            report.duration_ms = (end_time - start_time) * 1000
            report.final_memory_mb = final_memory_mb
            report.memory_delta_mb = final_memory_mb - initial_memory_mb

            # Add to reports history
            self._reports.append(report)

            # Generate warnings
            self._check_memory_thresholds(report)

            logger.info(
                f"Memory profiling complete for {operation_name}: "
                f"peak {report.peak_memory_mb:.2f} MB, "
                f"delta {report.memory_delta_mb:+.2f} MB"
            )

    def _monitor_memory(
        self, process, report: MemoryReport, stop_event: threading.Event
    ):
        """Monitor memory usage in a separate thread."""
        try:
            import psutil

            sample_interval_sec = self.sample_interval_ms / 1000.0

            while not stop_event.is_set():
                try:
                    memory_info = process.memory_info()
                    memory_percent = process.memory_percent()

                    # Get system memory info
                    system_memory = psutil.virtual_memory()

                    rss_mb = memory_info.rss / (1024 * 1024)
                    vms_mb = memory_info.vms / (1024 * 1024)
                    available_mb = system_memory.available / (1024 * 1024)

                    # Create usage sample
                    usage = MemoryUsage(
                        timestamp=time.time(),
                        rss_mb=rss_mb,
                        vms_mb=vms_mb,
                        percent=memory_percent,
                        available_mb=available_mb,
                    )

                    # Update report
                    report.samples.append(usage)
                    report.peak_memory_mb = max(report.peak_memory_mb, rss_mb)

                    # Check thresholds
                    if rss_mb > self.critical_threshold_mb:
                        warning = f"CRITICAL: Memory usage {rss_mb:.2f} MB exceeds critical threshold {self.critical_threshold_mb} MB"
                        if warning not in report.warnings:
                            report.warnings.append(warning)
                            logger.critical(f"Memory profiler: {warning}")

                    elif rss_mb > self.warning_threshold_mb:
                        warning = f"WARNING: Memory usage {rss_mb:.2f} MB exceeds warning threshold {self.warning_threshold_mb} MB"
                        if warning not in report.warnings:
                            report.warnings.append(warning)
                            logger.warning(f"Memory profiler: {warning}")

                    # Wait for next sample
                    stop_event.wait(sample_interval_sec)

                except psutil.Error as e:
                    logger.warning(f"Memory monitoring error: {e}")
                    break

        except Exception as e:
            logger.error(f"Memory monitoring thread error: {e}")

    @contextmanager
    def _basic_memory_profile(self, operation_name: str):
        """Basic memory profiling fallback when psutil is not available."""
        import gc
        import sys

        start_time = time.time()

        # Force garbage collection for baseline
        gc.collect()

        # Basic report without detailed monitoring
        report = MemoryReport(
            operation_name=operation_name,
            start_time=start_time,
            end_time=0.0,
            duration_ms=0.0,
            initial_memory_mb=0.0,
            peak_memory_mb=0.0,
            final_memory_mb=0.0,
            memory_delta_mb=0.0,
        )

        report.warnings.append(
            "Basic memory monitoring - install psutil for detailed profiling"
        )

        try:
            logger.info(f"Starting basic memory profiling for {operation_name}")
            yield report

        finally:
            end_time = time.time()
            gc.collect()

            report.end_time = end_time
            report.duration_ms = (end_time - start_time) * 1000

            # Add to reports
            self._reports.append(report)

            logger.info(f"Basic memory profiling complete for {operation_name}")

    def _check_memory_thresholds(self, report: MemoryReport):
        """Check memory usage against thresholds and add warnings."""
        if report.peak_memory_mb > self.critical_threshold_mb:
            report.warnings.append(
                f"Peak memory usage {report.peak_memory_mb:.2f} MB exceeded critical threshold {self.critical_threshold_mb} MB"
            )
        elif report.peak_memory_mb > self.warning_threshold_mb:
            report.warnings.append(
                f"Peak memory usage {report.peak_memory_mb:.2f} MB exceeded warning threshold {self.warning_threshold_mb} MB"
            )

        # Check for memory leaks (large positive delta without cleanup)
        if report.memory_delta_mb > 50:  # 50MB threshold for potential leaks
            report.warnings.append(
                f"Potential memory leak detected: {report.memory_delta_mb:.2f} MB increase not released"
            )

        # Check memory efficiency
        if report.memory_efficiency > 0.5:  # More than 50% memory overhead
            report.warnings.append(
                f"Low memory efficiency: {report.memory_efficiency:.2f} (high overhead relative to peak usage)"
            )

    def profile_function(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Profile memory usage of a single function call.

        Args:
            func: Function to profile
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result along with memory profiling
        """
        operation_name = f"{func.__name__}_memory_profile"

        with self.profile_memory(operation_name) as report:
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                report.warnings.append(f"Function execution failed: {e}")
                raise

    def get_reports(self) -> List[MemoryReport]:
        """Get all memory profiling reports."""
        return self._reports.copy()

    def get_latest_report(self) -> Optional[MemoryReport]:
        """Get the most recent memory profiling report."""
        return self._reports[-1] if self._reports else None

    def clear_reports(self):
        """Clear all stored memory reports."""
        self._reports.clear()
        logger.info("Memory profiling reports cleared")

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all memory profiling data."""
        if not self._reports:
            return {"message": "No memory profiling data available"}

        # Calculate aggregates
        total_operations = len(self._reports)
        peak_memories = [r.peak_memory_mb for r in self._reports]
        deltas = [r.memory_delta_mb for r in self._reports]
        efficiencies = [
            r.memory_efficiency for r in self._reports if r.memory_efficiency > 0
        ]

        warnings_count = sum(len(r.warnings) for r in self._reports)

        return {
            "total_operations": total_operations,
            "memory_statistics": {
                "avg_peak_memory_mb": sum(peak_memories) / len(peak_memories),
                "max_peak_memory_mb": max(peak_memories),
                "min_peak_memory_mb": min(peak_memories),
                "avg_memory_delta_mb": sum(deltas) / len(deltas),
                "max_memory_delta_mb": max(deltas),
                "min_memory_delta_mb": min(deltas),
                "avg_efficiency": (
                    sum(efficiencies) / len(efficiencies) if efficiencies else 0.0
                ),
            },
            "warnings_total": warnings_count,
            "recent_reports": (
                self._reports[-5:] if len(self._reports) >= 5 else self._reports
            ),
            "thresholds": {
                "warning_mb": self.warning_threshold_mb,
                "critical_mb": self.critical_threshold_mb,
            },
        }

    def analyze_memory_patterns(self) -> Dict[str, Any]:
        """Analyze memory usage patterns across all reports."""
        if not self._reports:
            return {"message": "No data to analyze"}

        # Group by operation name
        operations: dict[str, list[MemoryReport]] = {}
        for report in self._reports:
            op_name = report.operation_name
            if op_name not in operations:
                operations[op_name] = []
            operations[op_name].append(report)

        # Analyze each operation type
        analysis = {}
        for op_name, reports in operations.items():
            peaks = [r.peak_memory_mb for r in reports]
            deltas = [r.memory_delta_mb for r in reports]
            durations = [r.duration_ms for r in reports]

            analysis[op_name] = {
                "total_runs": len(reports),
                "memory_stats": {
                    "avg_peak_mb": sum(peaks) / len(peaks),
                    "max_peak_mb": max(peaks),
                    "std_dev_peak": self._calculate_std_dev(peaks),
                    "avg_delta_mb": sum(deltas) / len(deltas),
                    "memory_correlation": (
                        self._calculate_correlation(durations, peaks)
                        if len(peaks) > 1
                        else 0.0
                    ),
                },
                "warnings": sum(len(r.warnings) for r in reports),
                "recommendations": self._generate_memory_recommendations(reports),
            }

        return {
            "operations_analyzed": len(operations),
            "total_reports": len(self._reports),
            "operation_analysis": analysis,
            "overall_recommendations": self._generate_overall_recommendations(),
        }

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance**0.5

    def _calculate_correlation(
        self, x_values: List[float], y_values: List[float]
    ) -> float:
        """Calculate correlation coefficient between two value lists."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)

        denominator = (
            (n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)
        ) ** 0.5

        if denominator == 0:
            return 0.0

        return (n * sum_xy - sum_x * sum_y) / denominator

    def _generate_memory_recommendations(
        self, reports: List[MemoryReport]
    ) -> List[str]:
        """Generate memory optimization recommendations for specific operation."""
        recommendations = []

        avg_peak = sum(r.peak_memory_mb for r in reports) / len(reports)
        avg_delta = sum(r.memory_delta_mb for r in reports) / len(reports)

        if avg_peak > self.warning_threshold_mb:
            recommendations.append(
                "Consider implementing streaming or chunked processing"
            )

        if avg_delta > 20:  # 20MB average increase
            recommendations.append("Potential memory leak - review object lifecycle")

        warning_rate = sum(len(r.warnings) for r in reports) / len(reports)
        if warning_rate > 1:
            recommendations.append(
                "Frequent memory warnings - consider lowering memory footprint"
            )

        return recommendations

    def _generate_overall_recommendations(self) -> List[str]:
        """Generate overall memory optimization recommendations."""
        recommendations = []

        if not self._psutil_available:
            recommendations.append("Install psutil for detailed memory profiling")

        if any(len(r.warnings) > 0 for r in self._reports):
            recommendations.append("Address memory warnings to improve stability")

        avg_peak = sum(r.peak_memory_mb for r in self._reports) / len(self._reports)
        if avg_peak > self.warning_threshold_mb * 0.8:
            recommendations.append(
                "Consider increasing available memory or optimizing algorithms"
            )

        return recommendations
