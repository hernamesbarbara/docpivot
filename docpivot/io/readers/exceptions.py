"""Exceptions for document readers and DocPivot operations.

This module provides a comprehensive exception hierarchy for error handling
throughout DocPivot, enabling clear error reporting and programmatic
error handling.
"""

from typing import Any, Dict, List, Optional, Union


class DocPivotError(Exception):
    """Base exception for all DocPivot operations.

    This exception provides structured error context and serves as the base
    for all other DocPivot exceptions. It includes optional context data
    for programmatic error handling.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """Initialize DocPivotError.

        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            context: Optional context data for error details
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause

    def __str__(self) -> str:
        """Return string representation of the error."""
        return self.message

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value by key.

        Args:
            key: Context key to retrieve
            default: Default value if key not found

        Returns:
            Context value or default
        """
        return self.context.get(key, default)


class ValidationError(DocPivotError):
    """Raised when data validation fails.

    This exception provides detailed information about validation failures,
    including specific field errors and validation rules that were violated.
    """

    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, List[str]]] = None,
        validation_rules: Optional[List[str]] = None,
        **kwargs: Any
    ):
        """Initialize ValidationError.

        Args:
            message: Human-readable error message
            field_errors: Dictionary mapping field names to error lists
            validation_rules: List of validation rules that were violated
            **kwargs: Additional arguments passed to DocPivotError
        """
        super().__init__(message, **kwargs)
        self.field_errors = field_errors or {}
        self.validation_rules = validation_rules or []

    def add_field_error(self, field_name: str, error_message: str) -> None:
        """Add a field-specific error.

        Args:
            field_name: Name of the field with error
            error_message: Error message for this field
        """
        if field_name not in self.field_errors:
            self.field_errors[field_name] = []
        self.field_errors[field_name].append(error_message)

    def has_field_errors(self) -> bool:
        """Check if there are field-specific errors.

        Returns:
            True if field errors exist, False otherwise
        """
        return bool(self.field_errors)


class TransformationError(DocPivotError):
    """Raised when document transformation fails.

    This exception provides information about transformation failures
    and includes recovery suggestions when available.
    """

    def __init__(
        self,
        message: str,
        transformation_type: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        **kwargs: Any
    ):
        """Initialize TransformationError.

        Args:
            message: Human-readable error message
            transformation_type: Type of transformation that failed
            recovery_suggestions: List of recovery suggestions
            **kwargs: Additional arguments passed to DocPivotError
        """
        super().__init__(message, **kwargs)
        self.transformation_type = transformation_type
        self.recovery_suggestions = recovery_suggestions or []


class ConfigurationError(DocPivotError):
    """Raised when invalid configuration or parameters are provided.

    This exception handles configuration validation failures and
    provides guidance on correct parameter usage.
    """

    def __init__(
        self,
        message: str,
        invalid_parameters: Optional[List[str]] = None,
        valid_options: Optional[Dict[str, List[str]]] = None,
        **kwargs: Any
    ):
        """Initialize ConfigurationError.

        Args:
            message: Human-readable error message
            invalid_parameters: List of invalid parameter names
            valid_options: Dictionary mapping parameter names to valid options
            **kwargs: Additional arguments passed to DocPivotError
        """
        super().__init__(message, **kwargs)
        self.invalid_parameters = invalid_parameters or []
        self.valid_options = valid_options or {}


class UnsupportedFormatError(DocPivotError, ValueError):
    """Raised when an unsupported file format is encountered.

    This exception provides clear error messages to guide users toward
    supported formats and implementation options. It maintains backward
    compatibility by inheriting from ValueError.
    """

    def __init__(
        self,
        file_path: str,
        supported_formats: Optional[List[str]] = None,
        detected_format: Optional[str] = None,
        **kwargs: Any
    ):
        """Initialize UnsupportedFormatError.

        Args:
            file_path: Path to the file with unsupported format
            supported_formats: List of supported format descriptions
            detected_format: The format that was detected (if any)
            **kwargs: Additional arguments passed to DocPivotError
        """
        if supported_formats is None:
            supported_formats = [
                ".docling.json files (Docling native format)",
                ".lexical.json files (Lexical JSON format)",
                ".json files with DoclingDocument or Lexical content",
            ]

        message_parts = [f"Unsupported file format: '{file_path}'"]
        
        if detected_format:
            message_parts.append(f"Detected format: {detected_format}")
            
        message_parts.append("Supported formats:")
        message_parts.extend(f"  - {fmt}" for fmt in supported_formats)
        message_parts.append("\nTo add support for additional formats, extend BaseReader.")

        message = "\n".join(message_parts)

        # Set context for programmatic access
        context = {
            "file_path": file_path,
            "supported_formats": supported_formats,
            "detected_format": detected_format
        }

        kwargs_copy = kwargs.copy()
        kwargs_copy.update({
            "error_code": "UNSUPPORTED_FORMAT",
            "context": context
        })
        super().__init__(message, **kwargs_copy)
        
        # Maintain backward compatibility
        self.file_path = file_path
        self.supported_formats = supported_formats


class FileAccessError(DocPivotError):
    """Raised when file access operations fail.

    This exception handles various file system errors and provides
    specific guidance based on the type of access failure.
    """

    def __init__(
        self,
        message: str,
        file_path: str,
        operation: str,
        permission_issue: bool = False,
        **kwargs: Any
    ):
        """Initialize FileAccessError.

        Args:
            message: Human-readable error message
            file_path: Path to the file that caused the error
            operation: Operation that was attempted (read, write, etc.)
            permission_issue: Whether this is a permission-related error
            **kwargs: Additional arguments passed to DocPivotError
        """
        # Start with default context
        context = {
            "file_path": file_path,
            "operation": operation,
            "permission_issue": permission_issue
        }
        
        # Merge with any additional context passed in kwargs
        if "context" in kwargs:
            context.update(kwargs["context"])

        kwargs_copy = kwargs.copy()
        kwargs_copy.update({
            "error_code": "FILE_ACCESS_ERROR",
            "context": context
        })
        super().__init__(message, **kwargs_copy)
        self.file_path = file_path
        self.operation = operation
        self.permission_issue = permission_issue


class SchemaValidationError(ValidationError):
    """Raised when document schema validation fails.

    This exception provides detailed information about schema validation
    failures, including missing fields, invalid types, and schema mismatches.
    """

    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        expected_schema: Optional[str] = None,
        actual_schema: Optional[str] = None,
        missing_fields: Optional[List[str]] = None,
        **kwargs: Any
    ):
        """Initialize SchemaValidationError.

        Args:
            message: Human-readable error message
            schema_name: Name of the schema being validated
            expected_schema: Expected schema identifier
            actual_schema: Actual schema found (if any)
            missing_fields: List of missing required fields
            **kwargs: Additional arguments passed to ValidationError
        """
        context = {
            "schema_name": schema_name,
            "expected_schema": expected_schema,
            "actual_schema": actual_schema,
            "missing_fields": missing_fields or []
        }

        kwargs_copy = kwargs.copy()
        kwargs_copy.update({
            "error_code": "SCHEMA_VALIDATION_ERROR",
            "context": context
        })
        super().__init__(message, **kwargs_copy)
        self.schema_name = schema_name
        self.expected_schema = expected_schema
        self.actual_schema = actual_schema
        self.missing_fields = missing_fields or []


# Backward compatibility is achieved by making UnsupportedFormatError inherit from ValueError
# This allows existing code that catches ValueError to continue working
