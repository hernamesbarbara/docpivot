"""Tests for the simplified DocPivot API."""

from unittest.mock import Mock, patch

from docling_core.types import DoclingDocument

from docpivot import (
    ConversionResult,
    DocPivotEngine,
    get_debug_config,
    get_default_lexical_config,
    get_performance_config,
)


def create_mock_document():
    """Create a mock DoclingDocument for testing."""
    doc = Mock(spec=DoclingDocument)
    doc.name = "test_document"
    doc.body = Mock()
    doc.body.items = [Mock(), Mock(), Mock()]
    return doc


class TestDocPivotEngine:
    """Test the main DocPivotEngine class."""

    def test_initialization_defaults(self):
        """Test engine initializes with smart defaults."""
        engine = DocPivotEngine()
        assert engine.default_format == "lexical"
        assert engine.lexical_config["pretty"] is False
        assert engine.lexical_config["handle_tables"] is True

    def test_initialization_custom_config(self):
        """Test engine with custom configuration."""
        config = {"pretty": True, "indent": 4}
        engine = DocPivotEngine(lexical_config=config)
        assert engine.lexical_config["pretty"] is True
        assert engine.lexical_config["indent"] == 4

    def test_convert_to_lexical_mock(self):
        """Test conversion to Lexical format with mocked serializer."""
        engine = DocPivotEngine()
        doc = create_mock_document()

        with patch("docpivot.engine.LexicalDocSerializer") as mock_serializer:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.text = '{"type": "doc", "content": []}'
            mock_instance.serialize.return_value = mock_result
            mock_serializer.return_value = mock_instance

            result = engine.convert_to_lexical(doc)

            assert isinstance(result, ConversionResult)
            assert result.format == "lexical"
            assert result.content == '{"type": "doc", "content": []}'
            assert result.metadata["document_name"] == "test_document"

    def test_convert_file(self, tmp_path):
        """Test file conversion."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        engine = DocPivotEngine()
        with patch.object(engine._reader_factory, "get_reader") as mock_get_reader:
            mock_reader = Mock()
            mock_doc = create_mock_document()
            mock_reader.read.return_value = mock_doc
            mock_get_reader.return_value = mock_reader

            with patch.object(engine, "convert_to_lexical") as mock_convert:
                mock_convert.return_value = ConversionResult(
                    content='{"converted": true}', format="lexical", metadata={}
                )

                result = engine.convert_file(test_file)
                assert result.format == "lexical"
                assert result.content == '{"converted": true}'

    def test_convert_file_with_output(self, tmp_path):
        """Test file conversion with output path."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        input_file.write_text('{"test": "data"}')

        engine = DocPivotEngine()
        with patch.object(engine._reader_factory, "get_reader") as mock_get_reader:
            mock_reader = Mock()
            mock_doc = create_mock_document()
            mock_reader.read.return_value = mock_doc
            mock_get_reader.return_value = mock_reader

            with patch.object(engine, "convert_to_lexical") as mock_convert:
                mock_convert.return_value = ConversionResult(
                    content='{"converted": true}', format="lexical", metadata={}
                )

                result = engine.convert_file(input_file, output_path=output_file)
                assert output_file.exists()
                assert output_file.read_text() == '{"converted": true}'
                assert result.metadata["output_path"] == str(output_file)


class TestDocPivotEngineBuilder:
    """Test the builder pattern."""

    def test_builder_basic(self):
        """Test basic builder usage."""
        engine = DocPivotEngine.builder().build()
        assert isinstance(engine, DocPivotEngine)

    def test_builder_with_pretty_print(self):
        """Test builder with pretty printing."""
        engine = DocPivotEngine.builder().with_pretty_print(indent=4).build()

        assert engine.lexical_config["pretty"] is True
        assert engine.lexical_config["indent"] == 4

    def test_builder_performance_mode(self):
        """Test performance mode configuration."""
        engine = DocPivotEngine.builder().with_performance_mode().build()

        assert engine.lexical_config["pretty"] is False
        assert engine.lexical_config["include_metadata"] is False

    def test_builder_debug_mode(self):
        """Test debug mode configuration."""
        engine = DocPivotEngine.builder().with_debug_mode().build()

        assert engine.lexical_config["pretty"] is True
        assert engine.lexical_config["include_metadata"] is True

    def test_builder_chain(self):
        """Test fluent interface chaining."""
        engine = (
            DocPivotEngine.builder()
            .with_images(include=True)
            .with_metadata(include=False)
            .with_default_format("lexical")
            .build()
        )

        assert engine.lexical_config["handle_images"] is True
        assert engine.lexical_config["include_metadata"] is False
        assert engine.default_format == "lexical"


class TestDefaults:
    """Test default configurations."""

    def test_default_lexical_config(self):
        """Test default Lexical configuration."""
        config = get_default_lexical_config()
        assert config["pretty"] is False
        assert config["handle_tables"] is True
        assert config["handle_lists"] is True

    def test_performance_config(self):
        """Test performance configuration."""
        config = get_performance_config()
        assert config["pretty"] is False
        assert config["include_metadata"] is False

    def test_debug_config(self):
        """Test debug configuration."""
        config = get_debug_config()
        assert config["pretty"] is True
        assert config["indent"] == 4
        assert config["include_metadata"] is True
