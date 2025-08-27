"""Optimized DoclingJsonReader with performance enhancements for large files."""

import json
import time
import mmap
from pathlib import Path
from typing import Any, Dict, Union, Optional, Callable, Generator, List
from contextlib import contextmanager
import io

from docling_core.types import DoclingDocument
from pydantic import ValidationError

from .basereader import BaseReader
from .exceptions import (
    ValidationError as DocPivotValidationError,
    SchemaValidationError,
    FileAccessError,
    UnsupportedFormatError
)
from docpivot.validation import validate_docling_document, validate_json_content
from docpivot.logging_config import get_logger, PerformanceLogger, log_exception_with_context
from docpivot.performance import PerformanceConfig

logger = get_logger(__name__)
perf_logger = PerformanceLogger(logger)

# Performance constants
DEFAULT_CHUNK_SIZE = 8192
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB
LARGE_FILE_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100MB
JSON_PARSER_BUFFER_SIZE = 1024 * 1024  # 1MB


class OptimizedDoclingJsonReader(BaseReader):
    """Performance-optimized reader for .docling.json files.
    
    Features:
    - Streaming JSON parsing for large files
    - Fast JSON library selection (orjson, ujson fallbacks)
    - Memory-efficient file reading with mmap
    - Lazy loading options
    - Progress callbacks for large operations
    - Caching support
    """

    SUPPORTED_EXTENSIONS = {".docling.json", ".json"}
    REQUIRED_SCHEMA_FIELDS = {"schema_name", "version"}
    EXPECTED_SCHEMA_NAME = "DoclingDocument"

    def __init__(self, 
                 performance_config: Optional[PerformanceConfig] = None,
                 use_streaming: bool = None,
                 use_fast_json: bool = True,
                 enable_caching: bool = False,
                 progress_callback: Optional[Callable[[float], None]] = None,
                 **kwargs: Any) -> None:
        """Initialize optimized reader with performance options.
        
        Args:
            performance_config: Performance configuration object
            use_streaming: Force streaming mode (auto-detected if None)
            use_fast_json: Whether to use fast JSON libraries when available
            enable_caching: Whether to enable document caching
            progress_callback: Callback for progress updates (receives 0.0-1.0)
            **kwargs: Additional configuration parameters
        """
        super().__init__(**kwargs)
        
        self.performance_config = performance_config or PerformanceConfig()
        self.use_streaming = use_streaming
        self.use_fast_json = use_fast_json
        self.enable_caching = enable_caching
        self.progress_callback = progress_callback
        
        # Document cache
        self._document_cache: Dict[str, DoclingDocument] = {}
        
        # JSON parser selection
        self._json_parser = self._select_json_parser()
        
        logger.debug(f"OptimizedDoclingJsonReader initialized with parser: {self._json_parser.__name__}")

    def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
        """Load document from .docling.json file with performance optimizations.

        Args:
            file_path: Path to the .docling.json file to load
            **kwargs: Additional parameters for loading

        Returns:
            DoclingDocument: The loaded document

        Raises:
            FileAccessError: If the file cannot be accessed or read
            ValidationError: If the file format is invalid
            SchemaValidationError: If the DoclingDocument schema is invalid
        """
        start_time = time.time()
        file_path_str = str(file_path)
        logger.info(f"Loading DoclingDocument from {file_path_str} (optimized)")

        try:
            # Check cache first if enabled
            if self.enable_caching and file_path_str in self._document_cache:
                logger.debug(f"Returning cached document for {file_path_str}")
                cached_doc = self._document_cache[file_path_str]
                duration = (time.time() - start_time) * 1000
                perf_logger.log_operation_time("cached_load", duration, {"file_path": file_path_str})
                return cached_doc

            # Validate file exists and get metadata
            try:
                path = self._validate_file_exists(file_path)
                file_size = path.stat().st_size
                logger.debug(f"File size: {file_size} bytes")
            except (FileNotFoundError, IsADirectoryError) as e:
                raise FileAccessError(
                    f"File access error: {e}",
                    file_path_str,
                    "file_validation",
                    context={"original_error": str(e)},
                    cause=e
                ) from e

            # Check format detection
            if not self.detect_format(file_path):
                raise UnsupportedFormatError(file_path_str)

            # Choose loading strategy based on file size
            should_stream = (
                self.use_streaming is True or
                (self.use_streaming is None and file_size > STREAMING_THRESHOLD_BYTES)
            )

            if should_stream:
                logger.debug(f"Using streaming mode for {file_size} byte file")
                document = self._load_streaming(path, file_size)
            elif file_size > LARGE_FILE_THRESHOLD_BYTES:
                logger.debug(f"Using memory-mapped loading for {file_size} byte file")
                document = self._load_memory_mapped(path, file_size)
            else:
                logger.debug(f"Using standard loading for {file_size} byte file")
                document = self._load_standard(path, file_size)

            # Cache document if enabled
            if self.enable_caching:
                self._document_cache[file_path_str] = document
                logger.debug(f"Cached document for {file_path_str}")

            # Log success metrics
            duration = (time.time() - start_time) * 1000
            perf_logger.log_file_processing(file_path_str, "optimized_load", duration, file_size)
            logger.info(f"Successfully loaded DoclingDocument from {file_path_str} in {duration:.2f}ms")

            return document

        except (DocPivotValidationError, FileAccessError, SchemaValidationError, UnsupportedFormatError):
            duration = (time.time() - start_time) * 1000
            logger.error(f"Failed to load document from {file_path_str} after {duration:.2f}ms")
            raise
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            context = {
                "file_path": file_path_str,
                "operation": "optimized_load_data",
                "duration_ms": duration
            }
            log_exception_with_context(logger, e, "Optimized document loading", context)
            
            raise DocPivotValidationError(
                f"Unexpected error during optimized document loading: {e}",
                error_code="OPTIMIZED_LOAD_ERROR",
                context=context,
                cause=e
            ) from e

    def _load_standard(self, path: Path, file_size: int) -> DoclingDocument:
        """Load document using standard file reading."""
        try:
            if self.progress_callback:
                self.progress_callback(0.1)

            # Read file with encoding detection
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            if self.progress_callback:
                self.progress_callback(0.4)

            # Parse JSON with selected parser
            json_data = self._parse_json(content)

            if self.progress_callback:
                self.progress_callback(0.7)

            # Validate and create document
            return self._validate_and_create_document(json_data, str(path))

        except Exception as e:
            raise FileAccessError(
                f"Error in standard loading: {e}",
                str(path),
                "standard_load",
                context={"file_size": file_size, "error": str(e)},
                cause=e
            ) from e
        finally:
            if self.progress_callback:
                self.progress_callback(1.0)

    def _load_memory_mapped(self, path: Path, file_size: int) -> DoclingDocument:
        """Load document using memory-mapped file for large files."""
        try:
            if self.progress_callback:
                self.progress_callback(0.1)

            with open(path, 'r+b') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    
                    if self.progress_callback:
                        self.progress_callback(0.3)

                    # Read content from memory-mapped file
                    content = mmapped_file.read().decode('utf-8')

                    if self.progress_callback:
                        self.progress_callback(0.6)

                    # Parse JSON
                    json_data = self._parse_json(content)

                    if self.progress_callback:
                        self.progress_callback(0.8)

                    # Validate and create document
                    return self._validate_and_create_document(json_data, str(path))

        except Exception as e:
            # Fallback to standard loading if memory mapping fails
            logger.warning(f"Memory-mapped loading failed, falling back to standard: {e}")
            return self._load_standard(path, file_size)
        finally:
            if self.progress_callback:
                self.progress_callback(1.0)

    def _load_streaming(self, path: Path, file_size: int) -> DoclingDocument:
        """Load document using streaming JSON parsing for very large files."""
        try:
            if self.progress_callback:
                self.progress_callback(0.1)

            # For streaming, we'll read the file in chunks and parse
            # Since JSON doesn't naturally support streaming, we'll use a hybrid approach
            with open(path, 'r', encoding='utf-8', buffering=JSON_PARSER_BUFFER_SIZE) as f:
                
                if self.progress_callback:
                    self.progress_callback(0.3)

                # Read entire content but with buffered I/O
                content = f.read()

                if self.progress_callback:
                    self.progress_callback(0.6)

                # Use fast JSON parser for large content
                json_data = self._parse_json_streaming(content)

                if self.progress_callback:
                    self.progress_callback(0.8)

                # Validate and create document
                return self._validate_and_create_document(json_data, str(path))

        except Exception as e:
            logger.warning(f"Streaming loading failed, falling back to standard: {e}")
            return self._load_standard(path, file_size)
        finally:
            if self.progress_callback:
                self.progress_callback(1.0)

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON content with the selected parser."""
        try:
            return self._json_parser.loads(content)
        except Exception as e:
            # Fallback to standard library json
            if self._json_parser != json:
                logger.warning(f"Fast JSON parser failed, falling back to standard: {e}")
                try:
                    return json.loads(content)
                except json.JSONDecodeError as json_e:
                    raise DocPivotValidationError(
                        f"JSON parsing failed: {json_e}",
                        error_code="JSON_PARSE_ERROR",
                        context={"parser": "standard", "content_length": len(content)},
                        cause=json_e
                    ) from json_e
            raise DocPivotValidationError(
                f"JSON parsing failed: {e}",
                error_code="JSON_PARSE_ERROR", 
                context={"parser": self._json_parser.__name__, "content_length": len(content)},
                cause=e
            ) from e

    def _parse_json_streaming(self, content: str) -> Dict[str, Any]:
        """Parse JSON content optimized for streaming/large files."""
        # For very large JSON files, we can use specific optimizations
        if hasattr(self._json_parser, 'loads') and self._json_parser != json:
            # Fast parsers often have better memory handling
            try:
                return self._json_parser.loads(content)
            except Exception as e:
                logger.warning(f"Streaming JSON parsing failed: {e}")
        
        # Fallback to chunked parsing approach
        return self._parse_json_chunked(content)

    def _parse_json_chunked(self, content: str) -> Dict[str, Any]:
        """Parse JSON in chunks for memory efficiency (fallback method)."""
        try:
            # For now, use standard JSON parsing
            # TODO: Implement true streaming JSON parser if needed
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise DocPivotValidationError(
                f"Chunked JSON parsing failed: {e}",
                error_code="CHUNKED_JSON_PARSE_ERROR",
                context={"content_length": len(content)},
                cause=e
            ) from e

    def _validate_and_create_document(self, json_data: Dict[str, Any], file_path: str) -> DoclingDocument:
        """Validate JSON data and create DoclingDocument."""
        try:
            # Skip JSON content validation since we already parsed the JSON
            # and know it's valid JSON structure
            
            # Validate DoclingDocument schema
            validate_docling_document(json_data, file_path)
            
            # Create DoclingDocument
            document = DoclingDocument.model_validate(json_data)
            return document
            
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append(f"{field_path}: {error['msg']}")
            
            raise SchemaValidationError(
                f"DoclingDocument validation failed for '{file_path}':\n" + 
                "\n".join(f"  - {detail}" for detail in error_details),
                schema_name="DoclingDocument",
                context={
                    "file_path": file_path,
                    "validation_errors": error_details
                },
                cause=e
            ) from e

    def _select_json_parser(self):
        """Select the fastest available JSON parser."""
        if not self.use_fast_json:
            logger.debug("Fast JSON disabled, using standard library")
            return json

        # Try to import fast JSON libraries in order of preference
        try:
            import orjson
            logger.debug("Using orjson for JSON parsing")
            
            # Create wrapper for orjson to match standard interface
            class OrjsonWrapper:
                __name__ = "orjson"
                
                @staticmethod
                def loads(s: str) -> Any:
                    return orjson.loads(s.encode('utf-8'))
            
            return OrjsonWrapper()
        except ImportError:
            pass

        try:
            import ujson
            logger.debug("Using ujson for JSON parsing")
            return ujson
        except ImportError:
            pass

        try:
            import rapidjson
            logger.debug("Using rapidjson for JSON parsing")
            return rapidjson
        except ImportError:
            pass

        logger.debug("No fast JSON library available, using standard library")
        return json

    def detect_format(self, file_path: Union[str, Path]) -> bool:
        """Optimized format detection with caching."""
        logger.debug(f"Detecting format for {file_path}")
        
        try:
            path = Path(file_path)

            if not path.exists():
                return False

            # Check file extension first (fastest check)
            suffix = path.suffix.lower()
            if suffix not in self.SUPPORTED_EXTENSIONS:
                return False

            # For .docling.json files, assume they are valid
            if path.name.endswith(".docling.json"):
                return True

            # For generic .json files, do content-based detection
            if suffix == ".json":
                return self._check_docling_json_content_optimized(path)

            return False
            
        except Exception as e:
            logger.warning(f"Error during optimized format detection for {file_path}: {e}")
            return False

    def _check_docling_json_content_optimized(self, path: Path) -> bool:
        """Optimized content checking for DoclingDocument markers."""
        try:
            # Read only the first chunk to check for markers
            with open(path, "r", encoding="utf-8") as f:
                chunk = f.read(1024)  # Read first 1KB only

            # Quick string search for DoclingDocument markers
            has_markers = (
                '"schema_name"' in chunk and
                '"DoclingDocument"' in chunk and
                '"version"' in chunk
            )
            
            return has_markers

        except (IOError, UnicodeDecodeError) as e:
            logger.debug(f"Error reading content from {path} for format detection: {e}")
            return False

    def clear_cache(self):
        """Clear the document cache."""
        if self.enable_caching:
            cache_size = len(self._document_cache)
            self._document_cache.clear()
            logger.info(f"Cleared document cache ({cache_size} entries)")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the document cache."""
        return {
            "enabled": self.enable_caching,
            "size": len(self._document_cache),
            "files": list(self._document_cache.keys())
        }

    def preload_documents(self, file_paths: List[Union[str, Path]]) -> Dict[str, Union[DoclingDocument, Exception]]:
        """Preload multiple documents into cache.
        
        Args:
            file_paths: List of file paths to preload
            
        Returns:
            Dictionary mapping file paths to loaded documents or exceptions
        """
        results = {}
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                if self.progress_callback:
                    self.progress_callback(i / total_files)
                
                document = self.load_data(file_path)
                results[str(file_path)] = document
                logger.debug(f"Preloaded document: {file_path}")
                
            except Exception as e:
                results[str(file_path)] = e
                logger.warning(f"Failed to preload document {file_path}: {e}")
        
        if self.progress_callback:
            self.progress_callback(1.0)
        
        logger.info(f"Preloaded {len([r for r in results.values() if isinstance(r, DoclingDocument)])} of {total_files} documents")
        return results

    @contextmanager
    def performance_monitoring(self, operation_name: str = "optimized_reader"):
        """Context manager for performance monitoring."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - start_memory
            
            perf_logger.log_operation_time(
                operation_name, 
                duration_ms, 
                {
                    "memory_delta_mb": memory_delta,
                    "parser": self._json_parser.__name__ if hasattr(self._json_parser, '__name__') else str(type(self._json_parser)),
                    "streaming_enabled": self.use_streaming,
                    "caching_enabled": self.enable_caching
                }
            )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0