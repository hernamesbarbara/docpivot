"""DEPRECATED: OptimizedDoclingJsonReader - use DoclingJsonReader with performance options instead."""

import warnings
from typing import Any, Optional, Callable

from .doclingjsonreader import DoclingJsonReader, DEFAULT_STREAMING_THRESHOLD_BYTES, DEFAULT_LARGE_FILE_THRESHOLD_BYTES
from docpivot.performance import PerformanceConfig

# Re-export constants for backward compatibility
STREAMING_THRESHOLD_BYTES = DEFAULT_STREAMING_THRESHOLD_BYTES
LARGE_FILE_THRESHOLD_BYTES = DEFAULT_LARGE_FILE_THRESHOLD_BYTES


class OptimizedDoclingJsonReader(DoclingJsonReader):
    """DEPRECATED: Use DoclingJsonReader with performance options instead.

    This class is maintained for backward compatibility but emits a deprecation
    warning. All functionality has been merged into the unified DoclingJsonReader.

    Migration example:
        # Old (deprecated):
        reader = OptimizedDoclingJsonReader(enable_caching=True)

        # New (recommended):
        reader = DoclingJsonReader(
            use_fast_json=True,
            enable_caching=True,
            use_streaming=None  # auto-detect
        )
    """

    def __init__(
        self,
        performance_config: Optional[PerformanceConfig] = None,
        use_streaming: Optional[bool] = None,
        use_fast_json: bool = True,
        enable_caching: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with deprecation warning.

        Args:
            performance_config: Performance configuration object
            use_streaming: Force streaming mode (auto-detected if None)
            use_fast_json: Whether to use fast JSON libraries when available
            enable_caching: Whether to enable document caching
            progress_callback: Callback for progress updates (receives 0.0-1.0)
            **kwargs: Additional configuration parameters
        """
        warnings.warn(
            "OptimizedDoclingJsonReader is deprecated and will be removed in a future version. "
            "Use DoclingJsonReader with performance options instead. "
            "See the class docstring for migration examples.",
            DeprecationWarning,
            stacklevel=2
        )

        # Set performance defaults that match old optimized behavior
        kwargs.setdefault('use_fast_json', use_fast_json)
        kwargs.setdefault('enable_caching', enable_caching)
        kwargs.setdefault('use_streaming', use_streaming)
        kwargs.setdefault('performance_config', performance_config)
        kwargs.setdefault('progress_callback', progress_callback)

        # Initialize the unified reader with optimized defaults
        super().__init__(**kwargs)

    def performance_monitoring(self, operation_name: str):
        """Performance monitoring context manager (deprecated functionality).

        Args:
            operation_name: Name of the operation being monitored

        Returns:
            Context manager for performance monitoring
        """
        from contextlib import contextmanager

        @contextmanager
        def monitor():
            # Simple stub that just yields - the actual performance monitoring
            # is handled by the underlying DoclingJsonReader
            try:
                yield
            finally:
                pass

        return monitor()

    def preload_documents(self, file_paths: list) -> dict:
        """Preload multiple documents (deprecated functionality).

        Args:
            file_paths: List of file paths to preload

        Returns:
            Dictionary mapping file paths to loaded documents or exceptions
        """
        results = {}
        for file_path in file_paths:
            try:
                # Use the inherited load_data method
                doc = self.load_data(str(file_path))
                results[file_path] = doc
            except Exception as e:
                results[file_path] = e
        return results
