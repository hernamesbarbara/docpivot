"""DoclingJsonReader for loading .docling.json files into DoclingDocument
objects."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Union

from docling_core.types import DoclingDocument
from pydantic import ValidationError

from .basereader import BaseReader
from .exceptions import (
    ValidationError as DocPivotValidationError,
    SchemaValidationError,
    FileAccessError,
    UnsupportedFormatError,
)
from docpivot.validation import validate_docling_document, validate_json_content
from docpivot.logging_config import (
    get_logger,
    PerformanceLogger,
    log_exception_with_context,
)

logger = get_logger(__name__)
perf_logger = PerformanceLogger(logger)


class DoclingJsonReader(BaseReader):
    """Reader for .docling.json files that loads them into DoclingDocument
    objects.

    This reader handles the native Docling JSON format produced by
    DocumentConverter
    and other Docling tools. It validates the schema and reconstructs the full
    DoclingDocument object.
    """

    SUPPORTED_EXTENSIONS = {".docling.json", ".json"}
    REQUIRED_SCHEMA_FIELDS = {"schema_name", "version"}
    EXPECTED_SCHEMA_NAME = "DoclingDocument"

    def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
        """Load document from .docling.json file into DoclingDocument.

        Args:
            file_path: Path to the .docling.json file to load
            **kwargs: Additional parameters (currently unused)

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
            # Validate file exists and is readable
            try:
                path = self._validate_file_exists(file_path)
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

            # Log file size for performance monitoring
            file_size = path.stat().st_size
            logger.debug(f"File size: {file_size} bytes")

            # Check format detection
            if not self.detect_format(file_path):
                raise UnsupportedFormatError(file_path_str)

            # Read file content with error handling
            try:
                json_content = path.read_text(encoding="utf-8")
                logger.debug(
                    f"Successfully read {len(json_content)} characters from {file_path_str}"
                )
            except UnicodeDecodeError as e:
                raise FileAccessError(
                    f"Unable to decode file '{file_path_str}' as UTF-8. "
                    f"Please ensure the file is properly encoded. Error: {e}",
                    file_path_str,
                    "read_text",
                    context={"encoding": "utf-8", "original_error": str(e)},
                    cause=e,
                ) from e
            except IOError as e:
                raise FileAccessError(
                    f"Error reading file '{file_path_str}': {e}. "
                    f"Please check file permissions and disk space.",
                    file_path_str,
                    "read_file",
                    permission_issue=("permission" in str(e).lower()),
                    context={"original_error": str(e)},
                    cause=e,
                ) from e

            # Parse and validate JSON content
            json_data = validate_json_content(json_content, file_path_str)

            # Validate DoclingDocument structure using comprehensive validator
            validate_docling_document(json_data, file_path_str)

            # Create DoclingDocument from validated JSON data
            try:
                document = DoclingDocument.model_validate(json_data)

                # Log successful completion with performance metrics
                duration = (time.time() - start_time) * 1000
                perf_logger.log_file_processing(
                    file_path_str, "load", duration, file_size
                )
                logger.info(f"Successfully loaded DoclingDocument from {file_path_str}")

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

        except (
            DocPivotValidationError,
            FileAccessError,
            SchemaValidationError,
            UnsupportedFormatError,
        ):
            # Re-raise our custom exceptions without wrapping
            duration = (time.time() - start_time) * 1000
            perf_logger.log_operation_time(
                "load_data_error", duration, {"file_path": file_path}
            )
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

    def detect_format(self, file_path: Union[str, Path]) -> bool:
        """Detect if this reader can handle the given file format.

        Checks for .docling.json extension and optionally validates the
        content structure for .json files.

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

            # Check file extension
            suffix = path.suffix.lower()
            if suffix not in self.SUPPORTED_EXTENSIONS:
                logger.debug(f"Unsupported extension {suffix} for {file_path}")
                return False

            # For .docling.json files, we assume they are valid
            if path.name.endswith(".docling.json"):
                logger.debug(f"Detected .docling.json format for {file_path}")
                return True

            # For generic .json files, check content structure
            if suffix == ".json":
                result = self._check_docling_json_content(path)
                logger.debug(
                    f"Content-based format detection for {file_path}: {result}"
                )
                return result

            return False

        except Exception as e:
            # Log error but don't raise - format detection should be non-destructive
            logger.warning(f"Error during format detection for {file_path}: {e}")
            return False

    def _check_docling_json_content(self, path: Path) -> bool:
        """Check if a .json file contains DoclingDocument content.

        Args:
            path: Path object to the JSON file

        Returns:
            bool: True if the file appears to contain DoclingDocument data
        """
        try:
            # Read and parse a small portion to check schema
            with path.open("r", encoding="utf-8") as f:
                # Read first chunk to check for schema markers
                chunk = f.read(512)

            # Quick check for DoclingDocument markers
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

    def _validate_docling_schema(
        self, json_data: Dict[str, Any], file_path: str
    ) -> None:
        """Validate that JSON data has expected DoclingDocument schema
        structure.

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

    def _get_format_error_message(self, file_path: Union[str, Path]) -> str:
        """Generate a descriptive error message for unsupported file format.

        Args:
            file_path: Path to the unsupported file

        Returns:
            str: Error message describing the issue and supported formats
        """
        return (
            f"Unsupported file format: '{file_path}'\n"
            f"Supported formats:\n"
            f"  - .docling.json files (Docling native format)\n"
            f"  - .json files with DoclingDocument content\n"
            f"\nTo add support for additional formats, extend BaseReader."
        )
