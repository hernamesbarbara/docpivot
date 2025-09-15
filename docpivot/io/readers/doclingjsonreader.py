"""DoclingJsonReader for loading .docling.json files into DoclingDocument
objects."""

import json
import time
import mmap
from pathlib import Path
from typing import Any, Dict, Union, Optional, Callable

from docling_core.types import DoclingDocument
from pydantic import ValidationError

from .basereader import BaseReader
from .exceptions import (
    ValidationError as DocPivotValidationError,
    SchemaValidationError,
    FileAccessError,
    UnsupportedFormatError,
)
from docpivot.validation import validate_docling_document
from docpivot.logging_config import (
    get_logger,
    log_exception_with_context,
)

logger = get_logger(__name__)

# Performance constants
DEFAULT_CHUNK_SIZE = 8192
DEFAULT_STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_LARGE_FILE_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100MB
JSON_PARSER_BUFFER_SIZE = 1024 * 1024  # 1MB


class DoclingJsonReader(BaseReader):
    """Reader for .docling.json files that loads them into DoclingDocument
    objects.

    This reader handles the native Docling JSON format produced by
    DocumentConverter and other Docling tools. It validates the schema and
    reconstructs the full DoclingDocument object.

    Features:
    - Fast JSON library selection (orjson, ujson, rapidjson fallbacks)
    - Automatic loading strategy selection based on file size
    - Memory-efficient file reading with mmap for large files
    - Progress callbacks for long-running operations
    - Fast JSON library selection (orjson, ujson, rapidjson fallbacks)
    """

    SUPPORTED_EXTENSIONS = {".docling.json", ".json"}
    REQUIRED_SCHEMA_FIELDS = {"schema_name", "version"}
    EXPECTED_SCHEMA_NAME = "DoclingDocument"

    def __init__(
        self,
        use_streaming: Optional[bool] = None,
        use_fast_json: bool = True,
        enable_caching: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
        streaming_threshold_bytes: int = DEFAULT_STREAMING_THRESHOLD_BYTES,
        large_file_threshold_bytes: int = DEFAULT_LARGE_FILE_THRESHOLD_BYTES,
        **kwargs: Any,
    ) -> None:
        """Initialize DoclingJsonReader.

        Args:
            use_streaming: Force streaming mode (auto-detected if None)
            use_fast_json: Whether to use fast JSON libraries when available
            enable_caching: Whether to enable document caching
            progress_callback: Callback for progress updates (receives 0.0-1.0)
            streaming_threshold_bytes: File size threshold for streaming mode
            large_file_threshold_bytes: File size threshold for memory mapping
            **kwargs: Additional configuration parameters
        """
        super().__init__(**kwargs)

        self.use_streaming = use_streaming
        self.use_fast_json = use_fast_json
        self.enable_caching = enable_caching
        self.progress_callback = progress_callback
        self.streaming_threshold_bytes = streaming_threshold_bytes
        self.large_file_threshold_bytes = large_file_threshold_bytes

        # Document cache - key by (absolute_path, size, mtime)
        self._document_cache: Dict[tuple, DoclingDocument] = {}

        # JSON parser selection
        self._json_parser = self._select_json_parser()

        logger.debug(
            f"DoclingJsonReader initialized with parser: "
            f"{getattr(self._json_parser, '__name__', type(self._json_parser).__name__)}"
        )

    def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
        """Load document from .docling.json file.

        Args:
            file_path: Path to the .docling.json file to load
            **kwargs: Additional parameters for loading

        Returns:
            DoclingDocument: The loaded document as a DoclingDocument object

        Raises:
            FileAccessError: If the file cannot be accessed or read
            ValidationError: If the file format is invalid or corrupted
            SchemaValidationError: If the DoclingDocument schema is invalid
        """
        start_time = time.time()
        file_path_str = str(file_path)
        logger.info(f"Loading DoclingDocument from {file_path_str}")

        try:
            # Check cache first if enabled
            if self.enable_caching:
                try:
                    path = self._validate_file_exists(file_path)
                    cache_key = self._get_cache_key(path)
                    if cache_key in self._document_cache:
                        logger.debug(f"Returning cached document for {file_path_str}")
                        cached_doc = self._document_cache[cache_key]
                        duration = (time.time() - start_time) * 1000
                        logger.debug(f"Cached load completed in {duration:.2f}ms")
                        return cached_doc
                except (FileNotFoundError, IsADirectoryError, OSError) as e:
                    # Continue with normal flow to handle error properly
                    logger.debug(f"Cache lookup failed for {file_path_str}: {e}")
                    pass

            # Validate file exists and get metadata
            try:
                path = self._validate_file_exists(file_path)
                file_size = path.stat().st_size
                logger.debug(f"File size: {file_size} bytes")
            except FileNotFoundError as e:
                raise FileAccessError(
                    f"File not found: {file_path_str}",
                    file_path_str,
                    "check_existence",
                    context={"original_error": str(e)},
                    cause=e,
                ) from e
            except IsADirectoryError as e:
                raise FileAccessError(
                    f"Path is a directory, not a file: {file_path_str}",
                    file_path_str,
                    "check_file_type",
                    context={"original_error": str(e)},
                    cause=e,
                ) from e

            # Check format detection
            if not self.detect_format(file_path):
                raise UnsupportedFormatError(file_path_str)

            # Choose loading strategy based on file size and configuration
            loading_strategy = self._choose_loading_strategy(file_size)
            logger.debug(f"Using {loading_strategy} loading strategy for {file_size} byte file")

            # Load document using selected strategy
            if loading_strategy == "streaming":
                document = self._load_streaming(path, file_size)
            elif loading_strategy == "mmap":
                document = self._load_memory_mapped(path, file_size)
            else:  # standard
                document = self._load_standard(path, file_size)

            # Cache document if enabled
            if self.enable_caching:
                cache_key = self._get_cache_key(path)
                self._document_cache[cache_key] = document
                logger.debug(f"Cached document for {file_path_str}")

            # Log success metrics
            duration = (time.time() - start_time) * 1000
            logger.info(
                f"Successfully loaded DoclingDocument from {file_path_str} in {duration:.2f}ms"
            )
            return document

        except (
            DocPivotValidationError,
            FileAccessError,
            SchemaValidationError,
            UnsupportedFormatError,
        ):
            duration = (time.time() - start_time) * 1000
            # Log error timing
            logger.error(
                f"Failed to load DoclingDocument from {file_path} after {duration:.2f}ms"
            )
            raise
        except Exception as e:
            # Handle unexpected errors with comprehensive context
            duration = (time.time() - start_time) * 1000
            context = {
                "file_path": file_path,
                "operation": "load_data",
                "duration_ms": duration,
            }
            log_exception_with_context(logger, e, "DoclingDocument loading", context)

            raise DocPivotValidationError(
                f"Unexpected error loading DoclingDocument from '{file_path}': {e}. "
                f"Please check the file format and try again.",
                error_code="UNEXPECTED_LOAD_ERROR",
                context=context,
                cause=e,
            ) from e

    def _choose_loading_strategy(self, file_size: int) -> str:
        """Choose the optimal loading strategy based on file size and configuration."""
        if self.use_streaming is True:
            return "streaming"
        elif self.use_streaming is False:
            return "standard" if file_size < self.large_file_threshold_bytes else "mmap"
        else:  # Auto-detect based on file size
            if file_size > self.streaming_threshold_bytes:
                return "streaming"
            elif file_size > self.large_file_threshold_bytes:
                return "mmap"
            else:
                return "standard"

    def _load_standard(self, path: Path, file_size: int) -> DoclingDocument:
        """Load document using standard file reading."""
        try:
            if self.progress_callback:
                self.progress_callback(0.1)

            # Read file with encoding detection
            try:
                content = path.read_text(encoding="utf-8")
                logger.debug(
                    f"Successfully read {len(content)} characters from {path}"
                )
            except UnicodeDecodeError as e:
                raise FileAccessError(
                    f"Unable to decode file '{path}' as UTF-8. "
                    f"Please ensure the file is properly encoded. Error: {e}",
                    str(path),
                    "read_text",
                    context={"encoding": "utf-8", "original_error": str(e)},
                    cause=e,
                ) from e
            except IOError as e:
                raise FileAccessError(
                    f"Error reading file '{path}': {e}. "
                    f"Please check file permissions and disk space.",
                    str(path),
                    "read_file",
                    permission_issue=("permission" in str(e).lower()),
                    context={"original_error": str(e)},
                    cause=e,
                ) from e

            if self.progress_callback:
                self.progress_callback(0.3)

            # Parse JSON with selected parser
            json_data = self._parse_json(content)

            if self.progress_callback:
                self.progress_callback(0.6)

            if self.progress_callback:
                self.progress_callback(0.8)

            # Validate and create document
            return self._validate_and_create_document(json_data, str(path))

        except (FileAccessError, DocPivotValidationError):
            raise
        except Exception as e:
            raise FileAccessError(
                f"Error in standard loading: {e}",
                str(path),
                "standard_load",
                context={"file_size": file_size, "error": str(e)},
                cause=e,
            ) from e
        finally:
            if self.progress_callback:
                self.progress_callback(1.0)

    def _load_memory_mapped(self, path: Path, file_size: int) -> DoclingDocument:
        """Load document using memory-mapped file for large files."""
        try:
            if self.progress_callback:
                self.progress_callback(0.1)

            with open(path, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:

                    if self.progress_callback:
                        self.progress_callback(0.3)

                    # Read content from memory-mapped file
                    try:
                        content = mmapped_file.read().decode("utf-8")
                        logger.debug(
                            f"Successfully read {len(content)} characters from memory-mapped {path}"
                        )
                    except UnicodeDecodeError as e:
                        raise FileAccessError(
                            f"Unable to decode memory-mapped file '{path}' as UTF-8: {e}",
                            str(path),
                            "mmap_decode",
                            context={"encoding": "utf-8", "original_error": str(e)},
                            cause=e,
                        ) from e

                    if self.progress_callback:
                        self.progress_callback(0.6)

                    # Parse JSON
                    json_data = self._parse_json(content)

                    if self.progress_callback:
                        self.progress_callback(0.8)

                    # Validate and create document
                    return self._validate_and_create_document(json_data, str(path))

        except (FileAccessError, DocPivotValidationError):
            raise
        except Exception as e:
            # Fallback to standard loading if memory mapping fails
            logger.warning(
                f"Memory-mapped loading failed, falling back to standard: {e}"
            )
            return self._load_standard(path, file_size)
        finally:
            if self.progress_callback:
                self.progress_callback(1.0)

    def _load_streaming(self, path: Path, file_size: int) -> DoclingDocument:
        """Load document using streaming/buffered approach for very large files."""
        try:
            if self.progress_callback:
                self.progress_callback(0.1)

            # Use buffered I/O for large files
            with open(
                path, "r", encoding="utf-8", buffering=JSON_PARSER_BUFFER_SIZE
            ) as f:

                if self.progress_callback:
                    self.progress_callback(0.3)

                # Read entire content with buffered I/O
                try:
                    content = f.read()
                    logger.debug(
                        f"Successfully read {len(content)} characters with streaming from {path}"
                    )
                except UnicodeDecodeError as e:
                    raise FileAccessError(
                        f"Unable to decode streaming file '{path}' as UTF-8: {e}",
                        str(path),
                        "streaming_decode",
                        context={"encoding": "utf-8", "original_error": str(e)},
                        cause=e,
                    ) from e
                except IOError as e:
                    raise FileAccessError(
                        f"Error reading streaming file '{path}': {e}",
                        str(path),
                        "streaming_read",
                        permission_issue=("permission" in str(e).lower()),
                        context={"original_error": str(e)},
                        cause=e,
                    ) from e

                if self.progress_callback:
                    self.progress_callback(0.6)

                # Use fast JSON parser for large content
                json_data = self._parse_json_buffered(content)

                if self.progress_callback:
                    self.progress_callback(0.8)

                # Validate and create document
                return self._validate_and_create_document(json_data, str(path))

        except (FileAccessError, DocPivotValidationError):
            raise
        except Exception as e:
            logger.warning(f"Streaming loading failed, falling back to standard: {e}")
            return self._load_standard(path, file_size)
        finally:
            if self.progress_callback:
                self.progress_callback(1.0)

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON content with the selected parser."""
        parser_name = getattr(self._json_parser, '__name__', type(self._json_parser).__name__)

        try:
            return self._json_parser.loads(content)
        except Exception as e:
            # Fallback to standard library json if using fast parser
            if self._json_parser != json:
                logger.warning(
                    f"Fast JSON parser ({parser_name}) failed, falling back to standard: {e}"
                )
                try:
                    return json.loads(content)
                except json.JSONDecodeError as json_e:
                    raise DocPivotValidationError(
                        f"Invalid JSON format: {json_e}",
                        error_code="JSON_PARSE_ERROR",
                        context={
                            "parser": "standard_fallback",
                            "primary_parser": parser_name,
                            "content_length": len(content),
                            "primary_parser_error": str(e)
                        },
                        cause=json_e,
                    ) from json_e

            # Already using standard json parser
            raise DocPivotValidationError(
                f"Invalid JSON format: {e}",
                error_code="JSON_PARSE_ERROR",
                context={
                    "parser": parser_name,
                    "content_length": len(content),
                },
                cause=e,
            ) from e

    def _parse_json_buffered(self, content: str) -> Dict[str, Any]:
        """Parse JSON content optimized for streaming/large files."""
        # For very large JSON files, use the selected fast parser if available
        if hasattr(self._json_parser, "loads") and self._json_parser != json:
            try:
                return self._json_parser.loads(content)
            except Exception as e:
                logger.warning(f"Buffered JSON parsing failed with fast parser: {e}")

        # Fallback to standard parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise DocPivotValidationError(
                f"Invalid JSON format: {e}",
                error_code="BUFFERED_JSON_PARSE_ERROR",
                context={"content_length": len(content)},
                cause=e,
            ) from e

    def _validate_and_create_document(
        self, json_data: Dict[str, Any], file_path: str
    ) -> DoclingDocument:
        """Validate JSON data and create DoclingDocument."""
        try:
            # Extract version for logging and potential downstream handling (if json_data is a dict)
            version = "unknown"
            if isinstance(json_data, dict):
                version = json_data.get("version", "unknown")
                logger.debug(f"Processing DoclingDocument version {version} from {file_path}")
            
            # Validate DoclingDocument schema
            validate_docling_document(json_data, file_path)

            # Create DoclingDocument
            document = DoclingDocument.model_validate(json_data)
            
            # Log version-specific handling info
            if version == "1.7.0":
                logger.info(
                    f"Loaded DoclingDocument v1.7.0 from {file_path}. "
                    "Note: This version uses segment-local charspans (each segment starts at 0)."
                )
            
            return document

        except ValidationError as e:
            # Convert Pydantic validation error to our custom error
            error_details = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append(f"{field_path}: {error['msg']}")

            raise SchemaValidationError(
                f"DoclingDocument validation failed for '{file_path}':\n"
                + "\n".join(f"  - {detail}" for detail in error_details)
                + "\n\nPlease check the document structure and required fields.",
                schema_name="DoclingDocument",
                context={
                    "file_path": file_path,
                    "validation_errors": error_details,
                    "original_error": str(e),
                },
                cause=e,
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
                    return orjson.loads(s.encode("utf-8"))

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
            import rapidjson  # type: ignore

            logger.debug("Using rapidjson for JSON parsing")
            return rapidjson
        except ImportError:
            pass

        logger.debug("No fast JSON library available, using standard library")
        return json

    def _get_cache_key(self, path: Path) -> tuple:
        """Generate cache key based on file path, size, and modification time.

        Raises:
            OSError: If file stat information cannot be accessed due to permissions
        """
        try:
            stat = path.stat()
            return (str(path.absolute()), stat.st_size, stat.st_mtime)
        except OSError:
            # Re-raise OSError to be handled by caller
            raise

    def clear_cache(self) -> None:
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
            "files": [cache_key[0] for cache_key in self._document_cache.keys()],
        }

    def detect_format(self, file_path: Union[str, Path]) -> bool:
        """Detect if this reader can handle the given file format.

        Checks for .docling.json extension and optionally validates the
        content structure for .json files using optimized content checking.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if this reader can handle the file format, False otherwise
        """
        logger.debug(f"Detecting format for {file_path}")

        try:
            path = Path(file_path)

            # Check if file exists
            if not path.exists():
                logger.debug(f"File does not exist: {file_path}")
                return False

            # Check file extension first (fastest check)
            suffix = path.suffix.lower()
            if suffix not in self.SUPPORTED_EXTENSIONS:
                logger.debug(f"Unsupported extension {suffix} for {file_path}")
                return False

            # For .docling.json files, assume they are valid
            if path.name.endswith(".docling.json"):
                logger.debug(f"Detected .docling.json format for {file_path}")
                return True

            # For generic .json files, do optimized content-based detection
            if suffix == ".json":
                result = self._check_docling_json_content_optimized(path)
                logger.debug(
                    f"Content-based format detection for {file_path}: {result}"
                )
                return result

            return False

        except Exception as e:
            # Log error but don't raise - format detection should be non-destructive
            logger.warning(f"Error during format detection for {file_path}: {e}")
            return False

    def _check_docling_json_content_optimized(self, path: Path) -> bool:
        """Optimized content checking for DoclingDocument markers.

        Args:
            path: Path object to the JSON file

        Returns:
            bool: True if the file appears to contain DoclingDocument data
        """
        try:
            # Read only the first chunk to check for markers (optimized)
            with open(path, "r", encoding="utf-8") as f:
                chunk = f.read(1024)  # Read first 1KB only

            # Quick string search for DoclingDocument markers
            has_markers = (
                '"schema_name"' in chunk
                and '"DoclingDocument"' in chunk
                and '"version"' in chunk
            )
            logger.debug(
                f"DoclingDocument content markers found in {path}: {has_markers}"
            )
            return has_markers

        except (IOError, UnicodeDecodeError) as e:
            logger.debug(f"Error reading content from {path} for format detection: {e}")
            return False

    def _check_docling_json_content(self, path: Path) -> bool:
        """Backward compatibility method - delegates to optimized version."""
        return self._check_docling_json_content_optimized(path)

    def _validate_docling_schema(
        self, json_data: Dict[str, Any], file_path: str
    ) -> None:
        """Validate that JSON data has expected DoclingDocument schema structure.

        This method is kept for backward compatibility with existing tests.

        Args:
            json_data: Parsed JSON data dictionary
            file_path: Path to the file being validated (for error messages)

        Raises:
            ValueError: If the schema is invalid or missing required fields
        """
        if not isinstance(json_data, dict):
            raise ValueError(
                f"Invalid DoclingDocument format in '{file_path}': "
                f"Expected JSON object, got {type(json_data).__name__}"
            )

        # Check for required schema fields
        missing_fields = self.REQUIRED_SCHEMA_FIELDS - set(json_data.keys())
        if missing_fields:
            raise ValueError(
                f"Invalid DoclingDocument schema in '{file_path}': "
                f"Missing required fields: {', '.join(sorted(missing_fields))}"
            )

        # Validate schema name
        schema_name = json_data.get("schema_name")
        if schema_name != self.EXPECTED_SCHEMA_NAME:
            raise ValueError(
                f"Invalid DoclingDocument schema in '{file_path}': "
                f"Expected schema_name '{self.EXPECTED_SCHEMA_NAME}', "
                f"got '{schema_name}'"
            )
