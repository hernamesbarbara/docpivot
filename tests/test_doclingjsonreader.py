"""Tests for DoclingJsonReader class."""

import json

import pytest
from docling_core.types import DoclingDocument

from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.readers.exceptions import FileAccessError, UnsupportedFormatError, ValidationError, SchemaValidationError


class TestDoclingJsonReader:
    """Test suite for DoclingJsonReader class."""

    def test_can_be_instantiated(self):
        """Test that DoclingJsonReader can be instantiated."""
        reader = DoclingJsonReader()
        assert isinstance(reader, DoclingJsonReader)

    def test_inherits_from_basereader(self):
        """Test that DoclingJsonReader inherits from BaseReader."""
        from docpivot.io.readers.basereader import BaseReader

        reader = DoclingJsonReader()
        assert isinstance(reader, BaseReader)

    def test_detect_format_docling_json_extension(self, temp_directory):
        """Test detect_format returns True for .docling.json files."""
        reader = DoclingJsonReader()

        # Create a .docling.json file
        docling_file = temp_directory / "test.docling.json"
        docling_file.write_text('{"test": "content"}')

        assert reader.detect_format(str(docling_file)) is True

    def test_detect_format_generic_json_with_docling_content(self, temp_directory):
        """Test detect_format returns True for .json files with DoclingDocument
        content."""
        reader = DoclingJsonReader()

        # Create a .json file with DoclingDocument markers
        json_file = temp_directory / "test.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        json_file.write_text(content)

        assert reader.detect_format(str(json_file)) is True

    def test_detect_format_generic_json_without_docling_content(self, temp_directory):
        """Test detect_format returns False for .json files without
        DoclingDocument content."""
        reader = DoclingJsonReader()

        # Create a .json file without DoclingDocument markers
        json_file = temp_directory / "test.json"
        json_file.write_text('{"other": "content"}')

        assert reader.detect_format(str(json_file)) is False

    def test_detect_format_unsupported_extension(self, temp_directory):
        """Test detect_format returns False for unsupported extensions."""
        reader = DoclingJsonReader()

        # Create a file with unsupported extension
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("content")

        assert reader.detect_format(str(txt_file)) is False

    def test_detect_format_nonexistent_file(self, nonexistent_file):
        """Test detect_format returns False for nonexistent files."""
        reader = DoclingJsonReader()
        assert reader.detect_format(str(nonexistent_file)) is False

    def test_detect_format_unreadable_json_file(self, temp_directory):
        """Test detect_format handles unreadable files gracefully."""
        reader = DoclingJsonReader()

        # Create a file with binary content that's not valid UTF-8
        json_file = temp_directory / "test.json"
        json_file.write_bytes(b"\xff\xfe\x00\x00invalid")

        assert reader.detect_format(str(json_file)) is False

    @pytest.fixture
    def valid_docling_json_content(self):
        """Create valid DoclingDocument JSON content for testing."""
        return {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            "name": "test_document",
            "origin": {
                "mimetype": "application/pdf",
                "binary_hash": 123456789,
                "filename": "test.pdf",
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified",
            },
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified",
            },
            "groups": [],
            "texts": [],
            "pictures": [],
            "tables": [],
            "key_value_items": [],
            "pages": {},
        }

    def test_load_data_valid_docling_json(
        self, temp_directory, valid_docling_json_content
    ):
        """Test load_data successfully loads valid .docling.json file."""
        reader = DoclingJsonReader()

        # Create a valid .docling.json file
        docling_file = temp_directory / "test.docling.json"
        docling_file.write_text(json.dumps(valid_docling_json_content))

        # Load the document
        doc = reader.load_data(str(docling_file))

        # Verify it's a DoclingDocument
        assert isinstance(doc, DoclingDocument)
        assert doc.name == "test_document"
        assert doc.origin.filename == "test.pdf"

    def test_load_data_valid_generic_json(
        self, temp_directory, valid_docling_json_content
    ):
        """Test load_data successfully loads valid .json file with DoclingDocument
        content."""
        reader = DoclingJsonReader()

        # Create a valid .json file with DoclingDocument content
        json_file = temp_directory / "test.json"
        json_file.write_text(json.dumps(valid_docling_json_content))

        # Load the document
        doc = reader.load_data(str(json_file))

        # Verify it's a DoclingDocument
        assert isinstance(doc, DoclingDocument)
        assert doc.name == "test_document"

    def test_load_data_nonexistent_file(self, nonexistent_file):
        """Test load_data raises FileAccessError for nonexistent file."""
        reader = DoclingJsonReader()

        with pytest.raises(FileAccessError, match="File not found"):
            reader.load_data(str(nonexistent_file))

    def test_load_data_directory_path(self, temp_directory):
        """Test load_data raises FileAccessError for directory path."""
        reader = DoclingJsonReader()

        with pytest.raises(FileAccessError, match="Path is a directory"):
            reader.load_data(str(temp_directory))

    def test_load_data_unsupported_format(self, temp_directory):
        """Test load_data raises UnsupportedFormatError for unsupported file format."""
        reader = DoclingJsonReader()

        # Create a file with unsupported extension
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("content")

        with pytest.raises(UnsupportedFormatError):
            reader.load_data(str(txt_file))

    def test_load_data_invalid_json_syntax(self, temp_directory):
        """Test load_data raises ValidationError for invalid JSON syntax."""
        reader = DoclingJsonReader()

        # Create a .docling.json file with invalid JSON
        docling_file = temp_directory / "invalid.docling.json"
        docling_file.write_text('{"invalid": json}')  # Missing quotes around json

        with pytest.raises(ValidationError, match="Invalid JSON format"):
            reader.load_data(str(docling_file))

    def test_load_data_missing_schema_name(self, temp_directory):
        """Test load_data raises SchemaValidationError for missing schema_name."""
        reader = DoclingJsonReader()

        # Create a .docling.json file without schema_name
        docling_file = temp_directory / "no_schema.docling.json"
        content = {"version": "1.4.0", "name": "test"}
        docling_file.write_text(json.dumps(content))

        with pytest.raises(SchemaValidationError, match="missing required fields"):
            reader.load_data(str(docling_file))

    def test_load_data_missing_version(self, temp_directory):
        """Test load_data raises SchemaValidationError for missing version."""
        reader = DoclingJsonReader()

        # Create a .docling.json file without version
        docling_file = temp_directory / "no_version.docling.json"
        content = {"schema_name": "DoclingDocument", "name": "test"}
        docling_file.write_text(json.dumps(content))

        with pytest.raises(SchemaValidationError, match="missing required fields"):
            reader.load_data(str(docling_file))

    def test_load_data_wrong_schema_name(self, temp_directory):
        """Test load_data raises SchemaValidationError for wrong schema_name."""
        reader = DoclingJsonReader()

        # Create a .docling.json file with wrong schema_name
        docling_file = temp_directory / "wrong_schema.docling.json"
        content = {"schema_name": "WrongSchema", "version": "1.4.0"}
        docling_file.write_text(json.dumps(content))

        with pytest.raises(SchemaValidationError, match="missing required fields"):
            reader.load_data(str(docling_file))

    def test_load_data_non_object_json(self, temp_directory):
        """Test load_data raises ValidationError for non-object JSON."""
        reader = DoclingJsonReader()

        # Create a .docling.json file with array instead of object
        docling_file = temp_directory / "array.docling.json"
        docling_file.write_text('["not", "an", "object"]')

        with pytest.raises(ValidationError, match="Expected dict or DoclingDocument"):
            reader.load_data(str(docling_file))

    def test_load_data_pydantic_validation_error(self, temp_directory):
        """Test load_data handles Pydantic validation errors."""
        reader = DoclingJsonReader()

        # Create a .docling.json file with valid schema but invalid DoclingDocument
        # structure
        docling_file = temp_directory / "invalid_doc.docling.json"
        content = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            # Missing required fields for DoclingDocument
        }
        docling_file.write_text(json.dumps(content))

        with pytest.raises(SchemaValidationError, match="missing required fields"):
            reader.load_data(str(docling_file))

    def test_load_data_io_error(self, temp_directory):
        """Test load_data handles IO errors gracefully."""
        reader = DoclingJsonReader()

        # Create a file and then remove read permissions
        docling_file = temp_directory / "no_read.docling.json"
        docling_file.write_text('{"test": "content"}')
        docling_file.chmod(0o000)  # Remove all permissions

        try:
            with pytest.raises(FileAccessError, match="Error reading file"):
                reader.load_data(str(docling_file))
        finally:
            # Restore permissions for cleanup
            docling_file.chmod(0o644)

    def test_class_constants(self):
        """Test that class constants are properly defined."""
        reader = DoclingJsonReader()

        assert reader.SUPPORTED_EXTENSIONS == {".docling.json", ".json"}
        assert reader.REQUIRED_SCHEMA_FIELDS == {"schema_name", "version"}
        assert reader.EXPECTED_SCHEMA_NAME == "DoclingDocument"

    def test_check_docling_json_content_valid(self, temp_directory):
        """Test _check_docling_json_content identifies valid DoclingDocument JSON."""
        reader = DoclingJsonReader()

        # Create a file with DoclingDocument markers
        json_file = temp_directory / "valid.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        json_file.write_text(content)

        assert reader._check_docling_json_content(json_file) is True

    def test_check_docling_json_content_invalid(self, temp_directory):
        """Test _check_docling_json_content rejects non-DoclingDocument JSON."""
        reader = DoclingJsonReader()

        # Create a file without DoclingDocument markers
        json_file = temp_directory / "invalid.json"
        json_file.write_text('{"other": "content"}')

        assert reader._check_docling_json_content(json_file) is False

    def test_validate_docling_schema_valid(self, valid_docling_json_content):
        """Test _validate_docling_schema passes for valid schema."""
        reader = DoclingJsonReader()

        # Should not raise any exception
        reader._validate_docling_schema(valid_docling_json_content, "test.json")

    def test_validate_docling_schema_missing_fields(self):
        """Test _validate_docling_schema raises for missing required fields."""
        reader = DoclingJsonReader()

        invalid_data = {"version": "1.4.0"}  # Missing schema_name

        with pytest.raises(ValueError, match="Missing required fields: schema_name"):
            reader._validate_docling_schema(invalid_data, "test.json")
