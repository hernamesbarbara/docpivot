"""High-level workflow functions for end-to-end document processing."""

import logging
import time
from pathlib import Path
from typing import Any, Optional, Union

from docling_core.transforms.serializer.base import SerializationResult
from docling_core.types import DoclingDocument

from docpivot.io.readers import ReaderFactory
from docpivot.io.serializers import SerializerProvider
from docpivot.io.readers.exceptions import (
    DocPivotError,
    ValidationError,
    TransformationError,
    ConfigurationError,
    FileAccessError,
    UnsupportedFormatError,
)
from docpivot.logging_config import (
    get_logger,
    PerformanceLogger,
    log_exception_with_context,
)

logger = get_logger(__name__)
perf_logger = PerformanceLogger(logger)


def load_document(file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
    """Auto-detect format and load document into DoclingDocument.

    This function provides a simple interface for loading any supported document
    format by automatically detecting the format and selecting the appropriate
    reader. It includes comprehensive error handling and recovery mechanisms.

    Args:
        file_path: Path to the document file to load
        **kwargs: Additional parameters to pass to the reader

    Returns:
        DoclingDocument: The loaded document

    Raises:
        FileAccessError: If the file cannot be accessed or read
        UnsupportedFormatError: If no reader can handle the file format
        ValidationError: If the file format is invalid or corrupted
        TransformationError: If document loading fails

    Example:
        >>> doc = load_document("sample.docling.json")
        >>> print(f"Loaded document: {doc.name}")
    """
    start_time = time.time()
    file_path_str = str(file_path)
    logger.info(f"Loading document from {file_path_str}")

    try:
        # Create reader factory with error handling
        try:
            factory = ReaderFactory()
            logger.debug("ReaderFactory created successfully")
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create ReaderFactory: {e}. "
                f"DocPivot configuration may be corrupted.",
                context={"original_error": str(e)},
                cause=e,
            ) from e

        # Get appropriate reader with error handling
        try:
            reader = factory.get_reader(file_path, **kwargs)
            logger.debug(f"Selected reader: {type(reader).__name__}")
        except UnsupportedFormatError as e:
            # Log recovery suggestions for unsupported formats
            logger.error(f"No reader found for {file_path_str}")
            logger.error("Recovery suggestions:")
            logger.error("- Check that the file extension matches the content format")
            logger.error("- Verify the file is not corrupted")
            logger.error(
                "- Try converting the file to a supported format (.docling.json or .lexical.json)"
            )
            logger.error("- Check DocPivot documentation for supported formats")
            raise
        except FileNotFoundError as e:
            # Convert FileNotFoundError to FileAccessError for consistent API
            raise FileAccessError(
                f"File not found: {file_path_str}. "
                f"Check that the file exists and the path is correct.",
                file_path=file_path_str,
                operation="load_document",
                context={
                    "original_error": str(e),
                    "recovery_suggestions": [
                        "Verify the file path is correct",
                        "Check that the file exists",
                        "Ensure you have read permissions for the file",
                    ],
                },
                cause=e,
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Failed to get reader for '{file_path_str}': {e}. "
                f"File format detection may have failed.",
                context={
                    "file_path": file_path_str,
                    "kwargs": kwargs,
                    "original_error": str(e),
                },
                cause=e,
            ) from e

        # Load document data with comprehensive error handling
        try:
            document = reader.load_data(file_path, **kwargs)

            # Log successful completion with performance metrics
            duration = (time.time() - start_time) * 1000
            perf_logger.log_file_processing(file_path_str, "load_document", duration)
            logger.info(f"Successfully loaded document from {file_path_str}")

            return document

        except (
            FileAccessError,
            ValidationError,
            UnsupportedFormatError,
            TransformationError,
        ) as e:
            # Re-raise custom exceptions with additional context
            logger.error(f"Failed to load document from {file_path_str}: {e}")
            # Add workflow context to existing exception
            if hasattr(e, "context") and isinstance(e.context, dict):
                e.context.update(
                    {
                        "workflow_operation": "load_document",
                        "reader_type": type(reader).__name__,
                    }
                )
            raise
        except Exception as e:
            # Handle unexpected errors with comprehensive context
            context = {
                "file_path": file_path_str,
                "operation": "load_document",
                "reader_type": type(reader).__name__,
                "kwargs": kwargs,
            }
            log_exception_with_context(logger, e, "document loading workflow", context)

            raise TransformationError(
                f"Unexpected error loading document from '{file_path_str}': {e}. "
                f"The document processing workflow encountered an unexpected issue.",
                transformation_type="document_loading",
                recovery_suggestions=[
                    "Verify the file is not corrupted",
                    "Check available disk space and memory",
                    "Try restarting the application",
                    "Check DocPivot logs for detailed error information",
                ],
                context=context,
                cause=e,
            ) from e

    except (
        ConfigurationError,
        FileAccessError,
        UnsupportedFormatError,
        ValidationError,
        TransformationError,
    ):
        # Re-raise our custom exceptions without wrapping
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"Document loading workflow failed for {file_path_str} after {duration:.2f}ms"
        )
        raise
    except Exception as e:
        # Handle any remaining unexpected errors
        duration = (time.time() - start_time) * 1000
        context = {
            "file_path": file_path_str,
            "operation": "load_document",
            "duration_ms": str(duration),
            "kwargs": str(kwargs),
        }
        log_exception_with_context(logger, e, "document loading workflow", context)

        raise DocPivotError(
            f"Critical error in document loading workflow for '{file_path_str}': {e}. "
            f"Please report this issue to the DocPivot maintainers.",
            error_code="WORKFLOW_CRITICAL_ERROR",
            context=context,
            cause=e,
        ) from e


def load_and_serialize(
    input_path: Union[str, Path], output_format: str, **kwargs: Any
) -> SerializationResult:
    """Load document and serialize to target format in one call.

    This function combines document loading and serialization into a single
    operation with comprehensive error handling, automatically detecting the
    input format and using the appropriate serializer for the output format.

    Args:
        input_path: Path to the input document file
        output_format: Target output format (e.g., "markdown", "html", "lexical")
        **kwargs: Additional parameters to pass to the serializer

    Returns:
        SerializationResult: The serialized document with .text property

    Raises:
        FileAccessError: If the input file cannot be accessed
        UnsupportedFormatError: If input format is not supported
        ConfigurationError: If output format is not supported or parameters are invalid
        TransformationError: If serialization fails

    Example:
        >>> result = load_and_serialize("sample.docling.json", "lexical")
        >>> print(result.text)
    """
    start_time = time.time()
    input_path_str = str(input_path)
    logger.info(
        f"Loading and serializing document from {input_path_str} to {output_format}"
    )

    try:
        # Validate output format parameter
        if not isinstance(output_format, str) or not output_format.strip():
            raise ConfigurationError(
                f"Invalid output format: '{output_format}'. Must be a non-empty string.",
                invalid_parameters=["output_format"],
                context={"provided_output_format": output_format},
            )

        # Load the document using automatic format detection
        doc = load_document(input_path)
        logger.debug(f"Document loaded successfully from {input_path_str}")

        # Get the appropriate serializer with error handling
        try:
            provider = SerializerProvider()
            logger.debug("SerializerProvider created successfully")
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create SerializerProvider: {e}. "
                f"DocPivot serializer configuration may be corrupted.",
                context={"original_error": str(e)},
                cause=e,
            ) from e

        try:
            serializer = provider.get_serializer(output_format, doc=doc, **kwargs)
            logger.debug(f"Selected serializer: {type(serializer).__name__}")
        except Exception as e:
            # Check if this is an unsupported format error
            if "not supported" in str(e).lower() or "unknown" in str(e).lower():
                raise ConfigurationError(
                    f"Unsupported output format: '{output_format}'. "
                    f"Please check available serializers and try again. Error: {e}",
                    invalid_parameters=["output_format"],
                    context={
                        "requested_format": output_format,
                        "kwargs": kwargs,
                        "original_error": str(e),
                    },
                    cause=e,
                ) from e
            else:
                raise ConfigurationError(
                    f"Failed to get serializer for format '{output_format}': {e}",
                    context={
                        "output_format": output_format,
                        "kwargs": kwargs,
                        "original_error": str(e),
                    },
                    cause=e,
                ) from e

        # Perform serialization with error handling
        try:
            result = serializer.serialize()

            # Log successful completion with performance metrics
            duration = (time.time() - start_time) * 1000
            perf_logger.log_operation_time(
                "load_and_serialize",
                duration,
                {
                    "input_file": input_path_str,
                    "output_format": output_format,
                    "output_size_chars": (
                        len(result.text) if hasattr(result, "text") else 0
                    ),
                },
            )
            logger.info(
                f"Successfully loaded and serialized {input_path_str} to {output_format}"
            )

            return result

        except (ValidationError, TransformationError, ConfigurationError) as e:
            # Re-raise custom exceptions with additional context
            logger.error(
                f"Serialization failed for {input_path_str} to {output_format}: {e}"
            )
            if hasattr(e, "context") and isinstance(e.context, dict):
                e.context.update(
                    {
                        "workflow_operation": "load_and_serialize",
                        "serializer_type": type(serializer).__name__,
                        "output_format": output_format,
                    }
                )
            raise
        except Exception as e:
            # Handle unexpected serialization errors
            context = {
                "input_path": input_path_str,
                "output_format": output_format,
                "serializer_type": type(serializer).__name__,
                "kwargs": kwargs,
            }
            log_exception_with_context(
                logger, e, "document serialization workflow", context
            )

            raise TransformationError(
                f"Unexpected error during serialization to '{output_format}': {e}. "
                f"The serialization workflow encountered an unexpected issue.",
                transformation_type="document_serialization",
                recovery_suggestions=[
                    "Verify the document structure is compatible with the target format",
                    "Try with different serializer parameters",
                    "Check available memory and disk space",
                    "Check DocPivot logs for detailed error information",
                ],
                context=context,
                cause=e,
            ) from e

    except (
        ConfigurationError,
        FileAccessError,
        UnsupportedFormatError,
        ValidationError,
        TransformationError,
    ):
        # Re-raise our custom exceptions without wrapping
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"Load and serialize workflow failed for {input_path_str} -> {output_format} after {duration:.2f}ms"
        )
        raise
    except Exception as e:
        # Handle any remaining unexpected errors
        duration = (time.time() - start_time) * 1000
        context = {
            "input_path": input_path_str,
            "output_format": output_format,
            "operation": "load_and_serialize",
            "duration_ms": str(duration),
            "kwargs": str(kwargs),
        }
        log_exception_with_context(logger, e, "load and serialize workflow", context)

        raise DocPivotError(
            f"Critical error in load and serialize workflow for '{input_path_str}' -> '{output_format}': {e}. "
            f"Please report this issue to the DocPivot maintainers.",
            error_code="WORKFLOW_CRITICAL_ERROR",
            context=context,
            cause=e,
        ) from e


def convert_document(
    input_path: Union[str, Path],
    output_format: str,
    output_path: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> Optional[str]:
    """Complete conversion with optional file output.

    This function performs a complete document conversion, optionally writing
    the result to a file. It combines loading, serialization, and file I/O
    into a single operation.

    Args:
        input_path: Path to the input document file
        output_format: Target output format (e.g., "markdown", "html", "lexical")
        output_path: Optional path to write output file. If None, returns content as string
        **kwargs: Additional parameters to pass to the serializer

    Returns:
        Optional[str]: If output_path is None, returns serialized content as string.
                      If output_path is provided, writes to file and returns the output path.

    Raises:
        FileNotFoundError: If the input file does not exist
        UnsupportedFormatError: If input format is not supported
        ValueError: If output format is not supported or parameters are invalid
        IOError: If there are issues writing the output file

    Examples:
        >>> # Convert and return content as string
        >>> content = convert_document("sample.docling.json", "markdown")
        >>> print(content)

        >>> # Convert and write to file
        >>> output_file = convert_document(
        ...     "sample.docling.json",
        ...     "markdown",
        ...     "output.md"
        ... )
        >>> print(f"Converted document written to: {output_file}")
    """
    # Load and serialize the document
    result = load_and_serialize(input_path, output_format, **kwargs)

    # Handle output
    if output_path is None:
        return result.text

    # Write to file
    output_file = Path(output_path)
    try:
        # Create parent directories if they don't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.text, encoding="utf-8")
        return str(output_file)
    except IOError as e:
        raise IOError(f"Failed to write output file {output_path}: {e}") from e
