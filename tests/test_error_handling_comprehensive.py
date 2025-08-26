"""Comprehensive test suite for error handling and validation throughout DocPivot.

This test suite validates that all error conditions are properly handled
and that error messages are helpful and actionable.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from docling_core.types import DoclingDocument

from docpivot.io.readers.exceptions import (
    DocPivotError,
    ValidationError,
    TransformationError,
    ConfigurationError,
    FileAccessError,
    UnsupportedFormatError,
    SchemaValidationError
)
from docpivot.io.readers import DoclingJsonReader, LexicalJsonReader
from docpivot.io.serializers import LexicalDocSerializer, LexicalParams
from docpivot.validation import (
    validate_docling_document,
    validate_lexical_json,
    validate_file_path,
    validate_json_content
)
from docpivot.workflows import load_document, load_and_serialize


class TestExceptionHierarchy:
    """Test the custom exception hierarchy and error context handling."""

    def test_docpivot_error_base_functionality(self):
        """Test DocPivotError base functionality."""
        error = DocPivotError(
            "Test error message",
            error_code="TEST_ERROR",
            context={"key": "value"},
            cause=ValueError("original error")
        )

        assert str(error) == "Test error message"
        assert error.error_code == "TEST_ERROR"
        assert error.get_context("key") == "value"
        assert error.get_context("missing", "default") == "default"
        assert error.cause is not None
        assert isinstance(error.cause, ValueError)

    def test_validation_error_field_errors(self):
        """Test ValidationError field-specific error handling."""
        error = ValidationError(
            "Validation failed",
            field_errors={"field1": ["Error 1", "Error 2"]},
            validation_rules=["rule1", "rule2"]
        )

        assert error.has_field_errors()
        assert "field1" in error.field_errors
        assert len(error.field_errors["field1"]) == 2

        error.add_field_error("field2", "Error 3")
        assert "field2" in error.field_errors
        assert error.field_errors["field2"] == ["Error 3"]

    def test_transformation_error_recovery_suggestions(self):
        """Test TransformationError recovery suggestions."""
        error = TransformationError(
            "Transformation failed",
            transformation_type="test_transform",
            recovery_suggestions=["suggestion1", "suggestion2"]
        )

        assert error.transformation_type == "test_transform"
        assert len(error.recovery_suggestions) == 2
        assert "suggestion1" in error.recovery_suggestions

    def test_configuration_error_parameter_validation(self):
        """Test ConfigurationError parameter validation."""
        error = ConfigurationError(
            "Invalid configuration",
            invalid_parameters=["param1", "param2"],
            valid_options={"param1": ["option1", "option2"]}
        )

        assert len(error.invalid_parameters) == 2
        assert "param1" in error.invalid_parameters
        assert "param1" in error.valid_options
        assert "option1" in error.valid_options["param1"]

    def test_file_access_error_permission_detection(self):
        """Test FileAccessError permission issue detection."""
        error = FileAccessError(
            "File access failed",
            "/test/file.txt",
            "read",
            permission_issue=True
        )

        assert error.file_path == "/test/file.txt"
        assert error.operation == "read"
        assert error.permission_issue is True

    def test_schema_validation_error_schema_details(self):
        """Test SchemaValidationError schema details."""
        error = SchemaValidationError(
            "Schema validation failed",
            schema_name="TestSchema",
            expected_schema="v1.0",
            actual_schema="v0.9",
            missing_fields=["field1", "field2"]
        )

        assert error.schema_name == "TestSchema"
        assert error.expected_schema == "v1.0"
        assert error.actual_schema == "v0.9"
        assert len(error.missing_fields) == 2

    def test_unsupported_format_error_backward_compatibility(self):
        """Test UnsupportedFormatError backward compatibility with ValueError."""
        error = UnsupportedFormatError("test.unknown")
        
        # Should inherit from both DocPivotError and ValueError for backward compatibility
        assert isinstance(error, ValueError)
        assert isinstance(error, DocPivotError)
        assert error.file_path == "test.unknown"


class TestValidationFramework:
    """Test the comprehensive validation framework."""

    def test_validate_docling_document_valid(self):
        """Test validation of valid DoclingDocument."""
        valid_doc_data = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            "name": "test",
            "origin": {"mimetype": "application/json"},
            "furniture": {"children": []},
            "body": {"children": []},
            "groups": [],
            "texts": [],
            "pictures": [],
            "tables": [],
            "key_value_items": [],
            "pages": {}
        }

        # Should not raise any exception
        validate_docling_document(valid_doc_data, "test.json")

    def test_validate_docling_document_missing_fields(self):
        """Test validation fails for missing required fields."""
        invalid_doc_data = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0"
            # Missing required fields
        }

        with pytest.raises(SchemaValidationError) as exc_info:
            validate_docling_document(invalid_doc_data, "test.json")
        
        assert "missing required fields" in str(exc_info.value).lower()
        assert len(exc_info.value.missing_fields) > 0

    def test_validate_docling_document_wrong_schema_name(self):
        """Test validation fails for wrong schema name."""
        invalid_doc_data = {
            "schema_name": "WrongSchema",
            "version": "1.4.0",
            "name": "test",
            "origin": {"mimetype": "application/json"},
            "furniture": {"children": []},
            "body": {"children": []},
            "groups": [],
            "texts": [],
            "pictures": [],
            "tables": [],
            "key_value_items": [],
            "pages": {}
        }

        with pytest.raises(SchemaValidationError) as exc_info:
            validate_docling_document(invalid_doc_data, "test.json")
        
        assert exc_info.value.expected_schema == "DoclingDocument"
        assert exc_info.value.actual_schema == "WrongSchema"

    def test_validate_lexical_json_valid(self):
        """Test validation of valid Lexical JSON."""
        valid_lexical_data = {
            "root": {
                "children": [
                    {
                        "type": "paragraph",
                        "children": [
                            {"type": "text", "text": "Hello"}
                        ]
                    }
                ],
                "type": "root"
            }
        }

        # Should not raise any exception
        validate_lexical_json(valid_lexical_data, "test.lexical.json")

    def test_validate_lexical_json_missing_root(self):
        """Test validation fails for missing root field."""
        invalid_lexical_data = {
            "content": "some content"
            # Missing root field
        }

        with pytest.raises(SchemaValidationError) as exc_info:
            validate_lexical_json(invalid_lexical_data, "test.json")
        
        assert "root" in exc_info.value.missing_fields

    def test_validate_file_path_existing_file(self):
        """Test file path validation for existing files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
            tf.write('{"test": true}')
            temp_path = tf.name
        
        try:
            result = validate_file_path(temp_path)
            assert isinstance(result, Path)
            assert result.exists()
        finally:
            Path(temp_path).unlink()

    def test_validate_file_path_nonexistent_file(self):
        """Test file path validation fails for non-existent files."""
        nonexistent_path = "/path/that/does/not/exist.json"
        
        with pytest.raises(FileAccessError) as exc_info:
            validate_file_path(nonexistent_path)
        
        assert exc_info.value.operation == "check_existence"
        assert nonexistent_path in str(exc_info.value)

    def test_validate_file_path_directory_instead_of_file(self):
        """Test file path validation fails when path is directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileAccessError) as exc_info:
                validate_file_path(temp_dir, must_be_file=True)
            
            assert exc_info.value.operation == "check_file_type"
            assert "directory" in str(exc_info.value).lower()

    def test_validate_file_path_wrong_extension(self):
        """Test file path validation fails for wrong extension."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
            tf.write('test content')
            temp_path = tf.name
        
        try:
            allowed_extensions = {'.json', '.docling.json'}
            with pytest.raises(FileAccessError) as exc_info:
                validate_file_path(temp_path, allowed_extensions=allowed_extensions)
            
            assert exc_info.value.operation == "check_extension"
            assert ".txt" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_validate_json_content_valid(self):
        """Test JSON content validation with valid JSON."""
        valid_json = '{"test": true, "number": 42}'
        result = validate_json_content(valid_json, "test.json")
        
        assert isinstance(result, dict)
        assert result["test"] is True
        assert result["number"] == 42

    def test_validate_json_content_invalid(self):
        """Test JSON content validation fails with invalid JSON."""
        invalid_json = '{"test": true, "invalid": }'
        
        with pytest.raises(ValidationError) as exc_info:
            validate_json_content(invalid_json, "test.json")
        
        assert exc_info.value.error_code == "JSON_DECODE_ERROR"
        assert "line" in str(exc_info.value)
        assert "column" in str(exc_info.value)

    def test_validate_json_content_empty(self):
        """Test JSON content validation fails with empty content."""
        with pytest.raises(ValidationError) as exc_info:
            validate_json_content("", "test.json")
        
        assert exc_info.value.error_code == "EMPTY_JSON_CONTENT"


class TestReaderErrorHandling:
    """Test error handling in document readers."""

    def test_docling_reader_file_not_found(self):
        """Test DoclingJsonReader handles file not found."""
        reader = DoclingJsonReader()
        
        with pytest.raises(FileAccessError):
            reader.load_data("/nonexistent/file.docling.json")

    def test_docling_reader_invalid_json(self):
        """Test DoclingJsonReader handles invalid JSON."""
        reader = DoclingJsonReader()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as tf:
            tf.write('{"invalid": json}')  # Invalid JSON
            temp_path = tf.name
        
        try:
            with pytest.raises(ValidationError) as exc_info:
                reader.load_data(temp_path)
            
            assert "JSON" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_docling_reader_wrong_schema(self):
        """Test DoclingJsonReader handles wrong schema."""
        reader = DoclingJsonReader()
        
        wrong_schema_data = {
            "schema_name": "WrongSchema",  # Wrong schema name
            "version": "1.4.0"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as tf:
            json.dump(wrong_schema_data, tf)
            temp_path = tf.name
        
        try:
            with pytest.raises(SchemaValidationError):
                reader.load_data(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_lexical_reader_file_not_found(self):
        """Test LexicalJsonReader handles file not found."""
        reader = LexicalJsonReader()
        
        with pytest.raises(FileAccessError):
            reader.load_data("/nonexistent/file.lexical.json")

    def test_lexical_reader_invalid_structure(self):
        """Test LexicalJsonReader handles invalid Lexical structure."""
        reader = LexicalJsonReader()
        
        invalid_lexical_data = {
            "content": "some content"
            # Missing required root field
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lexical.json', delete=False) as tf:
            json.dump(invalid_lexical_data, tf)
            temp_path = tf.name
        
        try:
            with pytest.raises(SchemaValidationError):
                reader.load_data(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_reader_format_detection_error_handling(self):
        """Test that format detection handles errors gracefully."""
        reader = DoclingJsonReader()
        
        # Should return False for non-existent files, not raise exception
        assert not reader.detect_format("/nonexistent/file.json")


class TestSerializerErrorHandling:
    """Test error handling in document serializers."""

    def test_lexical_serializer_invalid_document(self):
        """Test LexicalDocSerializer handles invalid document."""
        # Create mock invalid document
        invalid_doc = Mock(spec=DoclingDocument)
        invalid_doc.model_dump.side_effect = Exception("Invalid document structure")
        
        params = LexicalParams()
        serializer = LexicalDocSerializer(invalid_doc, params)
        
        with pytest.raises(ValidationError):
            serializer.serialize()

    def test_lexical_serializer_invalid_params(self, sample_docling_document):
        """Test LexicalDocSerializer handles invalid parameters."""
        # Use sample document fixture
        doc = sample_docling_document
        
        # Invalid params (not LexicalParams object)
        invalid_params = "not_a_params_object"
        
        serializer = LexicalDocSerializer(doc, invalid_params)
        
        with pytest.raises(ConfigurationError) as exc_info:
            serializer.serialize()
        
        assert "LexicalParams" in str(exc_info.value)

    def test_lexical_serializer_transformation_error(self):
        """Test LexicalDocSerializer handles transformation errors."""
        # Create document with problematic structure
        doc = Mock(spec=DoclingDocument)
        doc.body = Mock()
        doc.body.children = None  # This should cause issues
        
        params = LexicalParams()
        serializer = LexicalDocSerializer(doc, params)
        
        # Mock the validation to pass but transformation to fail
        with patch('docpivot.validation.validate_docling_document'):
            with pytest.raises(TransformationError):
                serializer.serialize()


class TestWorkflowErrorHandling:
    """Test error handling in workflow functions."""

    def test_load_document_file_not_found(self):
        """Test load_document handles file not found."""
        with pytest.raises(FileAccessError):
            load_document("/nonexistent/file.json")

    def test_load_document_unsupported_format(self):
        """Test load_document handles unsupported format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.unsupported', delete=False) as tf:
            tf.write('some content')
            temp_path = tf.name
        
        try:
            with pytest.raises(UnsupportedFormatError) as exc_info:
                load_document(temp_path)
            
            # Check that recovery suggestions are added
            assert hasattr(exc_info.value, 'recovery_suggestions')
            if hasattr(exc_info.value, 'recovery_suggestions'):
                assert len(exc_info.value.recovery_suggestions) > 0
        finally:
            Path(temp_path).unlink()

    def test_load_and_serialize_invalid_output_format(self):
        """Test load_and_serialize handles invalid output format."""
        # Create valid input file
        valid_docling_data = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            "name": "test",
            "origin": {
                "mimetype": "application/json",
                "binary_hash": 123456789,
                "filename": "test.json"
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified"
            },
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified"
            },
            "groups": [],
            "texts": [],
            "pictures": [],
            "tables": [],
            "key_value_items": [],
            "pages": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as tf:
            json.dump(valid_docling_data, tf)
            temp_path = tf.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_and_serialize(temp_path, "")  # Empty output format
            
            assert "output_format" in exc_info.value.invalid_parameters
        finally:
            Path(temp_path).unlink()

    def test_load_and_serialize_unsupported_output_format(self):
        """Test load_and_serialize handles unsupported output format."""
        # Create valid input file
        valid_docling_data = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            "name": "test",
            "origin": {
                "mimetype": "application/json",
                "binary_hash": 123456789,
                "filename": "test.json"
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified"
            },
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified"
            },
            "groups": [],
            "texts": [],
            "pictures": [],
            "tables": [],
            "key_value_items": [],
            "pages": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as tf:
            json.dump(valid_docling_data, tf)
            temp_path = tf.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_and_serialize(temp_path, "unsupported_format")
            
            assert "unsupported format" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()


class TestErrorMessageQuality:
    """Test that error messages are helpful and actionable."""

    def test_error_messages_contain_context(self):
        """Test that error messages contain useful context information."""
        error = FileAccessError(
            "File not found",
            "/test/file.txt",
            "read",
            context={"additional_info": "test"}
        )
        
        assert error.file_path == "/test/file.txt"
        assert error.operation == "read"
        assert error.get_context("additional_info") == "test"

    def test_error_messages_are_actionable(self):
        """Test that error messages provide actionable guidance."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
            tf.write('not json')
            temp_path = tf.name
        
        try:
            reader = DoclingJsonReader()
            with pytest.raises(UnsupportedFormatError) as exc_info:
                reader.load_data(temp_path)
            
            error_msg = str(exc_info.value)
            # Should contain actionable guidance
            assert "supported formats" in error_msg.lower()
            assert "extend BaseReader" in error_msg
        finally:
            Path(temp_path).unlink()

    def test_validation_errors_provide_field_details(self):
        """Test that validation errors provide field-level details."""
        reader = DoclingJsonReader()
        
        invalid_docling_data = {
            "schema_name": "DoclingDocument",
            # Missing required fields
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as tf:
            json.dump(invalid_docling_data, tf)
            temp_path = tf.name
        
        try:
            with pytest.raises(SchemaValidationError) as exc_info:
                reader.load_data(temp_path)
            
            # Should have specific field information
            assert len(exc_info.value.missing_fields) > 0
            error_msg = str(exc_info.value)
            assert "missing required fields" in error_msg.lower()
        finally:
            Path(temp_path).unlink()

    def test_transformation_errors_provide_recovery_suggestions(self):
        """Test that transformation errors provide recovery suggestions."""
        error = TransformationError(
            "Transformation failed",
            transformation_type="test",
            recovery_suggestions=["Try option A", "Try option B"]
        )
        
        assert len(error.recovery_suggestions) == 2
        assert "Try option A" in error.recovery_suggestions
        assert error.transformation_type == "test"


class TestLoggingIntegration:
    """Test that error handling integrates properly with logging."""

    def test_logging_captures_error_context(self):
        """Test that logging captures error context information."""
        with patch('docpivot.io.readers.doclingjsonreader.logger') as mock_logger:
            reader = DoclingJsonReader()
            
            with pytest.raises(FileAccessError):
                reader.load_data("/nonexistent/file.json")
            
            # Should have logged the error attempt
            mock_logger.error.assert_called()

    def test_performance_logging_on_errors(self):
        """Test that performance is logged even when errors occur."""
        with patch('docpivot.io.readers.doclingjsonreader.perf_logger') as mock_perf_logger:
            reader = DoclingJsonReader()
            
            with pytest.raises(FileAccessError):
                reader.load_data("/nonexistent/file.json")
            
            # Should have logged timing information even on failure
            mock_perf_logger.log_operation_time.assert_called()


class TestErrorRecoveryMechanisms:
    """Test error recovery and graceful degradation."""

    def test_format_detection_recovery(self):
        """Test that format detection recovers from errors gracefully."""
        reader = DoclingJsonReader()
        
        # Should return False rather than raise exception for unreadable files
        result = reader.detect_format("/proc/version")  # System file that might not be readable
        assert isinstance(result, bool)  # Should return a boolean, not raise

    def test_partial_document_processing(self):
        """Test handling of partially valid documents."""
        # Create document with some valid and some invalid elements
        partial_valid_data = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            "name": "test",
            "origin": {
                "mimetype": "application/json",
                "binary_hash": 123456789,
                "filename": "test.json"
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified"
            },
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified"
            },
            "groups": [],
            "texts": [],
            "pictures": [],
            "tables": [],
            "key_value_items": [],
            "pages": {}
        }
        
        # Should process without error even if not all optional fields are present
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docling.json', delete=False) as tf:
            json.dump(partial_valid_data, tf)
            temp_path = tf.name
        
        try:
            reader = DoclingJsonReader()
            doc = reader.load_data(temp_path)
            assert isinstance(doc, DoclingDocument)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])