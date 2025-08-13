"""Tests for reader exceptions."""


from docpivot.io.readers.exceptions import UnsupportedFormatError


class TestUnsupportedFormatError:
    """Test suite for UnsupportedFormatError exception."""

    def test_can_be_instantiated_with_file_path(self):
        """Test that UnsupportedFormatError can be instantiated with just file path."""
        error = UnsupportedFormatError("test.unknown")

        assert isinstance(error, UnsupportedFormatError)
        assert isinstance(error, ValueError)
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
