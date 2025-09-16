"""Tests for core DocPivot functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from docpivot import ConversionResult, DocPivotEngine


class TestDocPivotEngineCore:
    """Test core engine functionality."""

    def test_engine_initialization_default(self):
        """Test engine initializes with defaults."""
        engine = DocPivotEngine()

        assert engine.default_format == "lexical"
        assert isinstance(engine.lexical_config, dict)

    def test_engine_initialization_custom_config(self):
        """Test engine with custom configuration."""
        custom_config = {
            "pretty": True,
            "indent": 3,
            "custom_option": "test"
        }
        engine = DocPivotEngine(
            default_format="json",
            lexical_config=custom_config
        )

        assert engine.default_format == "json"
        assert engine.lexical_config["pretty"] is True
        assert engine.lexical_config["indent"] == 3
        assert engine.lexical_config["custom_option"] == "test"

    def test_engine_has_required_attributes(self):
        """Test engine has required attributes."""
        engine = DocPivotEngine()
        assert hasattr(engine, 'lexical_config')
        assert hasattr(engine, 'default_format')
        assert hasattr(engine, 'convert_to_lexical')
        assert hasattr(engine, 'convert_file')
        assert hasattr(engine, 'convert_pdf')

    @patch('docpivot.engine.LexicalDocSerializer')
    def test_convert_to_lexical_success(self, mock_serializer_class, mock_docling_document):
        """Test successful conversion to Lexical format."""
        # Setup mock serializer
        mock_serializer = Mock()
        mock_result = Mock()
        mock_result.text = '{"root": {"children": []}}'
        mock_serializer.serialize.return_value = mock_result
        mock_serializer_class.return_value = mock_serializer

        engine = DocPivotEngine()
        result = engine.convert_to_lexical(mock_docling_document)

        assert isinstance(result, ConversionResult)
        assert result.format == "lexical"
        assert result.content == '{"root": {"children": []}}'
        assert result.metadata["document_name"] == "test_document"
        assert "conversion_time" in result.metadata

        # Verify serializer was called correctly
        mock_serializer_class.assert_called_once()
        mock_serializer.serialize.assert_called_once_with(mock_docling_document)

    @patch('docpivot.engine.LexicalDocSerializer')
    def test_convert_to_lexical_with_custom_config(self, mock_serializer_class, mock_docling_document):
        """Test conversion with custom configuration."""
        mock_serializer = Mock()
        mock_result = Mock()
        mock_result.text = '{"formatted": true}'
        mock_serializer.serialize.return_value = mock_result
        mock_serializer_class.return_value = mock_serializer

        custom_config = {"pretty": True, "indent": 4}
        engine = DocPivotEngine(lexical_config=custom_config)
        result = engine.convert_to_lexical(mock_docling_document)

        # Verify config was passed to serializer
        mock_serializer_class.assert_called_once_with(
            pretty=True,
            indent=4,
            handle_tables=True,  # From defaults
            handle_lists=True,   # From defaults
            handle_images=True,  # From defaults
            include_metadata=True  # From defaults
        )

    def test_convert_file_not_found(self):
        """Test handling of non-existent file."""
        engine = DocPivotEngine()
        non_existent = Path("/path/that/does/not/exist.json")

        with pytest.raises(FileNotFoundError):
            engine.convert_file(non_existent)

    @patch('docpivot.engine.ReaderFactory')
    def test_convert_file_success(self, mock_factory_class, tmp_path, mock_docling_document):
        """Test successful file conversion."""
        # Create test file
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        # Setup mocks
        mock_factory = Mock()
        mock_reader = Mock()
        mock_reader.read.return_value = mock_docling_document
        mock_factory.get_reader.return_value = mock_reader
        mock_factory_class.return_value = mock_factory

        engine = DocPivotEngine()

        with patch.object(engine, 'convert_to_lexical') as mock_convert:
            mock_convert.return_value = ConversionResult(
                content='{"converted": true}',
                format="lexical",
                metadata={}
            )

            result = engine.convert_file(test_file)

            assert result.format == "lexical"
            assert result.content == '{"converted": true}'
            mock_reader.read.assert_called_once_with(test_file)
            mock_convert.assert_called_once_with(mock_docling_document)

    @patch('docpivot.engine.ReaderFactory')
    def test_convert_file_with_output_path(self, mock_factory_class, tmp_path, mock_docling_document):
        """Test file conversion with output path."""
        # Setup files
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        input_file.write_text('{"test": "data"}')

        # Setup mocks
        mock_factory = Mock()
        mock_reader = Mock()
        mock_reader.read.return_value = mock_docling_document
        mock_factory.get_reader.return_value = mock_reader
        mock_factory_class.return_value = mock_factory

        engine = DocPivotEngine()

        with patch.object(engine, 'convert_to_lexical') as mock_convert:
            mock_convert.return_value = ConversionResult(
                content='{"converted": true}',
                format="lexical",
                metadata={}
            )

            result = engine.convert_file(input_file, output_path=output_file)

            # Check file was written
            assert output_file.exists()
            assert output_file.read_text() == '{"converted": true}'
            assert result.metadata["output_path"] == str(output_file)

    def test_convert_pdf_without_docling(self):
        """Test PDF conversion raises error when docling not available."""
        engine = DocPivotEngine()

        with patch('docpivot.engine.HAS_DOCLING', False):
            with pytest.raises(ImportError, match="docling"):
                engine.convert_pdf("dummy.pdf")

    @patch('docpivot.engine.HAS_DOCLING', True)
    @patch('docpivot.engine.DocumentConverter')
    def test_convert_pdf_success(self, mock_converter_class, tmp_path):
        """Test successful PDF conversion."""
        # Create test PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"PDF content")

        # Setup mock converter
        mock_converter = Mock()
        mock_result = Mock()
        mock_doc = Mock()
        mock_doc.document = Mock()
        mock_result.documents = [mock_doc]
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter

        engine = DocPivotEngine()

        with patch.object(engine, 'convert_to_lexical') as mock_convert:
            mock_convert.return_value = ConversionResult(
                content='{"from_pdf": true}',
                format="lexical",
                metadata={"source": "pdf"}
            )

            result = engine.convert_pdf(pdf_file)

            assert result.format == "lexical"
            assert result.content == '{"from_pdf": true}'
            assert result.metadata["source_type"] == "pdf"
            assert result.metadata["pdf_path"] == str(pdf_file)

            mock_converter.convert.assert_called_once()
            mock_convert.assert_called_once_with(mock_doc.document)


class TestConversionResult:
    """Test ConversionResult class."""

    def test_conversion_result_creation(self):
        """Test creating ConversionResult."""
        result = ConversionResult(
            content='{"test": true}',
            format="lexical",
            metadata={"key": "value"}
        )

        assert result.content == '{"test": true}'
        assert result.format == "lexical"
        assert result.metadata["key"] == "value"

    def test_conversion_result_metadata_update(self):
        """Test updating ConversionResult metadata."""
        result = ConversionResult(
            content="content",
            format="format",
            metadata={"initial": "value"}
        )

        result.metadata["new_key"] = "new_value"
        assert result.metadata["initial"] == "value"
        assert result.metadata["new_key"] == "new_value"


class TestErrorHandling:
    """Test error handling in DocPivot."""

    def test_convert_file_invalid_path_type(self):
        """Test handling invalid path type."""
        engine = DocPivotEngine()

        with pytest.raises(TypeError):
            engine.convert_file(123)  # Not a path

    @patch('docpivot.engine.ReaderFactory')
    def test_convert_file_reader_error(self, mock_factory_class, tmp_path):
        """Test handling reader errors."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        mock_factory = Mock()
        mock_factory.get_reader.side_effect = ValueError("Unsupported format")
        mock_factory_class.return_value = mock_factory

        engine = DocPivotEngine()

        with pytest.raises(ValueError, match="Unsupported format"):
            engine.convert_file(test_file)

    @patch('docpivot.engine.LexicalDocSerializer')
    def test_convert_to_lexical_serializer_error(self, mock_serializer_class, mock_docling_document):
        """Test handling serializer errors."""
        mock_serializer = Mock()
        mock_serializer.serialize.side_effect = RuntimeError("Serialization failed")
        mock_serializer_class.return_value = mock_serializer

        engine = DocPivotEngine()

        with pytest.raises(RuntimeError, match="Serialization failed"):
            engine.convert_to_lexical(mock_docling_document)
