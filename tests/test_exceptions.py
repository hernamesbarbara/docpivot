"""Tests for reader exceptions and error handling."""


from docpivot.io.readers.exceptions import (
    DocPivotError,
    ValidationError,
    TransformationError,
    ConfigurationError,
    UnsupportedFormatError,
    FileAccessError,
    SchemaValidationError
)


class TestDocPivotError:
    """Test suite for DocPivotError base exception."""

    def test_can_be_instantiated_with_basic_parameters(self):
        """Test that DocPivotError can be instantiated with basic parameters."""
        error = DocPivotError("Test message")
        
        assert isinstance(error, DocPivotError)
        assert str(error) == "Test message"
        assert error.error_code is None
        assert error.context == {}
        assert error.cause is None

    def test_can_be_instantiated_with_all_parameters(self):
        """Test DocPivotError with all parameters."""
        context = {"key": "value"}
        cause = ValueError("Original error")
        error = DocPivotError(
            "Test message",
            error_code="TEST_ERROR",
            context=context,
            cause=cause
        )
        
        assert error.message == "Test message"
        assert error.error_code == "TEST_ERROR"
        assert error.context == context
        assert error.cause is cause

    def test_get_context_method(self):
        """Test get_context method functionality."""
        error = DocPivotError("Test", context={"key1": "value1"})
        
        assert error.get_context("key1") == "value1"
        assert error.get_context("missing_key", "default") == "default"
        assert error.get_context("missing_key") is None


class TestValidationError:
    """Test suite for ValidationError exception."""

    def test_basic_validation_error(self):
        """Test basic ValidationError functionality."""
        error = ValidationError("Validation failed")
        
        assert isinstance(error, ValidationError)
        assert isinstance(error, DocPivotError)
        assert not error.has_field_errors()
        assert error.field_errors == {}
        assert error.validation_rules == []

    def test_validation_error_with_field_errors(self):
        """Test ValidationError with field errors."""
        field_errors = {"field1": ["Error 1"], "field2": ["Error 2"]}
        error = ValidationError("Validation failed", field_errors=field_errors)
        
        assert error.has_field_errors()
        assert error.field_errors == field_errors

    def test_add_field_error_method(self):
        """Test add_field_error method."""
        error = ValidationError("Validation failed")
        
        error.add_field_error("test_field", "Test error")
        assert error.has_field_errors()
        assert "test_field" in error.field_errors
        assert "Test error" in error.field_errors["test_field"]


class TestTransformationError:
    """Test suite for TransformationError exception."""

    def test_basic_transformation_error(self):
        """Test basic TransformationError functionality."""
        error = TransformationError("Transformation failed")
        
        assert isinstance(error, TransformationError)
        assert isinstance(error, DocPivotError)
        assert error.transformation_type is None
        assert error.recovery_suggestions == []

    def test_transformation_error_with_details(self):
        """Test TransformationError with details."""
        suggestions = ["Try option A", "Try option B"]
        error = TransformationError(
            "Transformation failed",
            transformation_type="test_transform",
            recovery_suggestions=suggestions
        )
        
        assert error.transformation_type == "test_transform"
        assert error.recovery_suggestions == suggestions


class TestConfigurationError:
    """Test suite for ConfigurationError exception."""

    def test_basic_configuration_error(self):
        """Test basic ConfigurationError functionality."""
        error = ConfigurationError("Configuration invalid")
        
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, DocPivotError)
        assert error.invalid_parameters == []
        assert error.valid_options == {}

    def test_configuration_error_with_details(self):
        """Test ConfigurationError with details."""
        invalid_params = ["param1", "param2"]
        valid_options = {"param1": ["option1", "option2"]}
        error = ConfigurationError(
            "Configuration invalid",
            invalid_parameters=invalid_params,
            valid_options=valid_options
        )
        
        assert error.invalid_parameters == invalid_params
        assert error.valid_options == valid_options


class TestFileAccessError:
    """Test suite for FileAccessError exception."""

    def test_basic_file_access_error(self):
        """Test basic FileAccessError functionality."""
        error = FileAccessError("File access failed", "/test/path", "read")
        
        assert isinstance(error, FileAccessError)
        assert isinstance(error, DocPivotError)
        assert error.file_path == "/test/path"
        assert error.operation == "read"
        assert error.permission_issue is False

    def test_file_access_error_with_permission_issue(self):
        """Test FileAccessError with permission issue."""
        error = FileAccessError(
            "Permission denied",
            "/test/path",
            "write",
            permission_issue=True
        )
        
        assert error.permission_issue is True


class TestSchemaValidationError:
    """Test suite for SchemaValidationError exception."""

    def test_basic_schema_validation_error(self):
        """Test basic SchemaValidationError functionality."""
        error = SchemaValidationError("Schema validation failed")
        
        assert isinstance(error, SchemaValidationError)
        assert isinstance(error, ValidationError)
        assert error.schema_name is None
        assert error.missing_fields == []

    def test_schema_validation_error_with_details(self):
        """Test SchemaValidationError with details."""
        missing_fields = ["field1", "field2"]
        error = SchemaValidationError(
            "Schema validation failed",
            schema_name="TestSchema",
            expected_schema="v1.0",
            actual_schema="v0.9",
            missing_fields=missing_fields
        )
        
        assert error.schema_name == "TestSchema"
        assert error.expected_schema == "v1.0"
        assert error.actual_schema == "v0.9"
        assert error.missing_fields == missing_fields


class TestUnsupportedFormatError:
    """Test suite for UnsupportedFormatError exception."""

    def test_can_be_instantiated_with_file_path(self):
        """Test that UnsupportedFormatError can be instantiated with just file path."""
        error = UnsupportedFormatError("test.unknown")

        assert isinstance(error, UnsupportedFormatError)
        assert isinstance(error, DocPivotError)
        assert isinstance(error, ValueError)  # Backward compatibility
        assert error.file_path == "test.unknown"

    def test_has_default_supported_formats(self):
        """Test that default supported formats are included in error."""
        error = UnsupportedFormatError("test.unknown")

        expected_formats = [
            ".docling.json files (Docling native format)",
            ".lexical.json files (Lexical JSON format)",
            ".json files with DoclingDocument or Lexical content",
        ]

        assert error.supported_formats == expected_formats

    def test_can_be_instantiated_with_custom_supported_formats(self):
        """Test UnsupportedFormatError with custom supported formats list."""
        custom_formats = [".txt files", ".md files"]
        error = UnsupportedFormatError("test.unknown", custom_formats)

        assert error.supported_formats == custom_formats
        assert error.file_path == "test.unknown"

    def test_error_message_includes_file_path(self):
        """Test that error message includes the file path."""
        error = UnsupportedFormatError("test.unknown")
        message = str(error)

        assert "test.unknown" in message
        assert "Unsupported file format" in message

    def test_error_message_includes_supported_formats(self):
        """Test that error message lists supported formats."""
        error = UnsupportedFormatError("test.unknown")
        message = str(error)

        assert ".docling.json files" in message
        assert ".lexical.json files" in message
        assert "Supported formats:" in message

    def test_error_message_includes_extension_hint(self):
        """Test that error message includes hint about extending BaseReader."""
        error = UnsupportedFormatError("test.unknown")
        message = str(error)

        assert "extend BaseReader" in message

    def test_custom_supported_formats_in_message(self):
        """Test that custom supported formats appear in error message."""
        custom_formats = [".txt files", ".custom files"]
        error = UnsupportedFormatError("test.unknown", custom_formats)
        message = str(error)

        assert ".txt files" in message
        assert ".custom files" in message
        assert ".docling.json files" not in message  # Default formats should not appear

    def test_detected_format_in_context(self):
        """Test that detected format is included in context."""
        error = UnsupportedFormatError(
            "test.unknown",
            detected_format="unknown_format"
        )
        
        assert error.get_context("detected_format") == "unknown_format"
        assert error.error_code == "UNSUPPORTED_FORMAT"

    def test_backward_compatibility_with_valueerror(self):
        """Test that UnsupportedFormatError is still caught as ValueError."""
        error = UnsupportedFormatError("test.unknown")
        
        # Should be catchable as ValueError for backward compatibility
        try:
            raise error
        except ValueError as e:
            assert isinstance(e, UnsupportedFormatError)
            assert isinstance(e, DocPivotError)
        except Exception:
            assert False, "Should be catchable as ValueError"
