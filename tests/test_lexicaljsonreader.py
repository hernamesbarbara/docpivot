"""Tests for LexicalJsonReader class."""

import json

import pytest
from docling_core.types import DoclingDocument

from docpivot.io.readers.lexicaljsonreader import LexicalJsonReader
from docpivot.io.readers.exceptions import UnsupportedFormatError


class TestLexicalJsonReader:
    """Test suite for LexicalJsonReader class."""

    def test_can_be_instantiated(self):
        """Test that LexicalJsonReader can be instantiated."""
        reader = LexicalJsonReader()
        assert isinstance(reader, LexicalJsonReader)

    def test_inherits_from_basereader(self):
        """Test that LexicalJsonReader inherits from BaseReader."""
        from docpivot.io.readers.basereader import BaseReader

        reader = LexicalJsonReader()
        assert isinstance(reader, BaseReader)

    def test_detect_format_lexical_json_extension(self, temp_directory):
        """Test detect_format returns True for .lexical.json files."""
        reader = LexicalJsonReader()

        # Create a .lexical.json file
        lexical_file = temp_directory / "test.lexical.json"
        lexical_file.write_text('{"test": "content"}')

        assert reader.detect_format(str(lexical_file)) is True

    def test_detect_format_generic_json_with_lexical_content(self, temp_directory):
        """Test detect_format returns True for .json files with Lexical content."""
        reader = LexicalJsonReader()

        # Create a .json file with Lexical markers
        json_file = temp_directory / "test.json"
        content = '{"root": {"children": [], "type": "root"}}'
        json_file.write_text(content)

        assert reader.detect_format(str(json_file)) is True

    def test_detect_format_generic_json_without_lexical_content(self, temp_directory):
        """Test detect_format returns False for .json files without Lexical content."""
        reader = LexicalJsonReader()

        # Create a .json file without Lexical markers
        json_file = temp_directory / "test.json"
        json_file.write_text('{"other": "content"}')

        assert reader.detect_format(str(json_file)) is False

    def test_detect_format_unsupported_extension(self, temp_directory):
        """Test detect_format returns False for unsupported extensions."""
        reader = LexicalJsonReader()

        # Create a file with unsupported extension
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("content")

        assert reader.detect_format(str(txt_file)) is False

    def test_detect_format_nonexistent_file(self, nonexistent_file):
        """Test detect_format returns False for nonexistent files."""
        reader = LexicalJsonReader()
        assert reader.detect_format(str(nonexistent_file)) is False

    def test_detect_format_unreadable_json_file(self, temp_directory):
        """Test detect_format handles unreadable files gracefully."""
        reader = LexicalJsonReader()

        # Create a file with binary content that's not valid UTF-8
        json_file = temp_directory / "test.json"
        json_file.write_bytes(b"\xff\xfe\x00\x00invalid")

        assert reader.detect_format(str(json_file)) is False

    @pytest.fixture
    def valid_lexical_json_content(self):
        """Create valid Lexical JSON content for testing."""
        return {
            "root": {
                "children": [
                    {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": "This is a heading",
                                "type": "text",
                                "version": 1,
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "tag": "h1",
                        "type": "heading",
                        "version": 1,
                    },
                    {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": "This is a paragraph.",
                                "type": "text",
                                "version": 1,
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "paragraph",
                        "version": 1,
                    },
                ],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1,
            }
        }

    def test_load_data_valid_lexical_json(
        self, temp_directory, valid_lexical_json_content
    ):
        """Test load_data successfully loads valid .lexical.json file."""
        reader = LexicalJsonReader()

        # Create a valid .lexical.json file
        lexical_file = temp_directory / "test.lexical.json"
        lexical_file.write_text(json.dumps(valid_lexical_json_content))

        # Load the document
        doc = reader.load_data(str(lexical_file))

        # Verify it's a DoclingDocument
        assert isinstance(doc, DoclingDocument)
        assert doc.name == "test.lexical"
        assert doc.origin.filename == "test.lexical.json"

        # Verify content was converted correctly
        assert len(doc.texts) == 2  # heading + paragraph
        assert doc.texts[0].label == "section_header"
        assert doc.texts[0].text == "This is a heading"
        assert doc.texts[1].label == "text"
        assert doc.texts[1].text == "This is a paragraph."

    def test_load_data_valid_generic_json(
        self, temp_directory, valid_lexical_json_content
    ):
        """Test load_data successfully loads valid .json file with Lexical content."""
        reader = LexicalJsonReader()

        # Create a valid .json file with Lexical content
        json_file = temp_directory / "test.json"
        json_file.write_text(json.dumps(valid_lexical_json_content))

        # Load the document
        doc = reader.load_data(str(json_file))

        # Verify it's a DoclingDocument
        assert isinstance(doc, DoclingDocument)
        assert doc.name == "test"

    def test_load_data_nonexistent_file(self, nonexistent_file):
        """Test load_data raises FileNotFoundError for nonexistent file."""
        reader = LexicalJsonReader()

        with pytest.raises(FileNotFoundError, match="File not found"):
            reader.load_data(str(nonexistent_file))

    def test_load_data_unsupported_format(self, temp_directory):
        """Test load_data raises UnsupportedFormatError for unsupported format."""
        reader = LexicalJsonReader()

        # Create a file with unsupported extension
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("content")

        with pytest.raises(UnsupportedFormatError):
            reader.load_data(str(txt_file))

    def test_load_data_invalid_json_syntax(self, temp_directory):
        """Test load_data raises ValueError for invalid JSON syntax."""
        reader = LexicalJsonReader()

        # Create a .lexical.json file with invalid JSON
        lexical_file = temp_directory / "invalid.lexical.json"
        lexical_file.write_text('{"invalid": json}')  # Missing quotes around json

        with pytest.raises(ValueError, match="Invalid JSON format"):
            reader.load_data(str(lexical_file))

    def test_load_data_missing_root_field(self, temp_directory):
        """Test load_data raises ValueError for missing root field."""
        reader = LexicalJsonReader()

        # Create a .lexical.json file without root
        lexical_file = temp_directory / "no_root.lexical.json"
        content = {"other": "content"}
        lexical_file.write_text(json.dumps(content))

        with pytest.raises(ValueError, match="Missing required fields: root"):
            reader.load_data(str(lexical_file))

    def test_load_data_invalid_root_structure(self, temp_directory):
        """Test load_data raises ValueError for invalid root structure."""
        reader = LexicalJsonReader()

        # Create a .lexical.json file with root as array instead of object
        lexical_file = temp_directory / "invalid_root.lexical.json"
        content = {"root": []}
        lexical_file.write_text(json.dumps(content))

        with pytest.raises(ValueError, match="'root' must be an object"):
            reader.load_data(str(lexical_file))

    def test_load_data_missing_root_children(self, temp_directory):
        """Test load_data raises ValueError for missing root children."""
        reader = LexicalJsonReader()

        # Create a .lexical.json file without children in root
        lexical_file = temp_directory / "no_children.lexical.json"
        content = {"root": {"type": "root"}}
        lexical_file.write_text(json.dumps(content))

        with pytest.raises(ValueError, match="root missing required fields: children"):
            reader.load_data(str(lexical_file))

    def test_load_data_non_object_json(self, temp_directory):
        """Test load_data raises ValueError for non-object JSON."""
        reader = LexicalJsonReader()

        # Create a .lexical.json file with array instead of object
        lexical_file = temp_directory / "array.lexical.json"
        lexical_file.write_text('["not", "an", "object"]')

        with pytest.raises(ValueError, match="Expected JSON object, got list"):
            reader.load_data(str(lexical_file))

    def test_load_data_with_list_content(self, temp_directory):
        """Test load_data correctly processes list content."""
        reader = LexicalJsonReader()

        lexical_content = {
            "root": {
                "children": [
                    {
                        "children": [
                            {
                                "children": [
                                    {
                                        "detail": 0,
                                        "format": 0,
                                        "mode": "normal",
                                        "style": "",
                                        "text": "First item",
                                        "type": "text",
                                        "version": 1,
                                    }
                                ],
                                "direction": "ltr",
                                "format": "",
                                "indent": 0,
                                "type": "listitem",
                                "value": 1,
                                "version": 1,
                            },
                            {
                                "children": [
                                    {
                                        "detail": 0,
                                        "format": 0,
                                        "mode": "normal",
                                        "style": "",
                                        "text": "Second item",
                                        "type": "text",
                                        "version": 1,
                                    }
                                ],
                                "direction": "ltr",
                                "format": "",
                                "indent": 0,
                                "type": "listitem",
                                "value": 2,
                                "version": 1,
                            },
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "listType": "unordered",
                        "start": 1,
                        "tag": "ul",
                        "type": "list",
                        "version": 1,
                    }
                ],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1,
            }
        }

        # Create a .lexical.json file with list content
        lexical_file = temp_directory / "list.lexical.json"
        lexical_file.write_text(json.dumps(lexical_content))

        # Load the document
        doc = reader.load_data(str(lexical_file))

        # Verify list was converted
        assert len(doc.groups) == 1
        assert len(doc.texts) == 2  # Two list items as text items
        assert "● First item" in doc.texts[0].text
        assert "● Second item" in doc.texts[1].text

    def test_class_constants(self):
        """Test that class constants are properly defined."""
        reader = LexicalJsonReader()

        assert reader.SUPPORTED_EXTENSIONS == {".lexical.json", ".json"}
        assert reader.REQUIRED_ROOT_FIELDS == {"root"}
        assert reader.REQUIRED_ROOT_CHILD_FIELDS == {"children", "type"}

    def test_check_lexical_json_content_valid(self, temp_directory):
        """Test _check_lexical_json_content identifies valid Lexical JSON."""
        reader = LexicalJsonReader()

        # Create a file with Lexical markers
        json_file = temp_directory / "valid.json"
        content = '{"root": {"children": [], "type": "root"}}'
        json_file.write_text(content)

        assert reader._check_lexical_json_content(json_file) is True

    def test_check_lexical_json_content_invalid(self, temp_directory):
        """Test _check_lexical_json_content rejects non-Lexical JSON."""
        reader = LexicalJsonReader()

        # Create a file without Lexical markers
        json_file = temp_directory / "invalid.json"
        json_file.write_text('{"other": "content"}')

        assert reader._check_lexical_json_content(json_file) is False

    def test_extract_text_from_children(self):
        """Test _extract_text_from_children method."""
        reader = LexicalJsonReader()

        children = [
            {"type": "text", "text": "Hello "},
            {"type": "text", "text": "World"},
            {"type": "other", "text": "ignored"},
        ]

        result = reader._extract_text_from_children(children)
        assert result == "Hello World"

    def test_extract_text_from_children_empty(self):
        """Test _extract_text_from_children with empty list."""
        reader = LexicalJsonReader()

        result = reader._extract_text_from_children([])
        assert result == ""
