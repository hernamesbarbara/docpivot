"""Tests for advanced LexicalDocSerializer features."""

import json
from unittest.mock import MagicMock

from docling_core.types import DoclingDocument
from docling_core.types.doc.document import PictureItem, TableItem

from docpivot.io.serializers.lexicaldocserializer import (
    LexicalDocSerializer,
    LexicalParams,
    ImageSerializer,
)


class TestLexicalParams:
    """Test LexicalParams configuration class."""

    def test_default_parameters(self) -> None:
        """Test default parameter values."""
        params = LexicalParams()

        assert params.include_metadata is True
        assert params.preserve_formatting is True
        assert params.indent_json is True
        assert params.version == 1
        assert params.custom_root_attributes == {}

    def test_custom_parameters(self) -> None:
        """Test custom parameter configuration."""
        custom_attrs = {"custom_key": "custom_value"}
        params = LexicalParams(
            include_metadata=False,
            preserve_formatting=False,
            indent_json=False,
            version=2,
            custom_root_attributes=custom_attrs,
        )

        assert params.include_metadata is False
        assert params.preserve_formatting is False
        assert params.indent_json is False
        assert params.version == 2
        assert params.custom_root_attributes == custom_attrs


class TestAdvancedTextFormatting:
    """Test advanced text formatting features."""

    def test_detect_text_formatting_bold(self) -> None:
        """Test detection of bold text formatting."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        # Test bold text detection with uppercase text
        bold_text = "THIS TEXT IS ALL UPPERCASE"
        format_types = serializer._detect_text_formatting(bold_text)
        assert "bold" in format_types

        # Test with 'bold' and 'are' pattern
        bold_text2 = "Terms that are bold in this contract"
        format_types2 = serializer._detect_text_formatting(bold_text2)
        assert "bold" in format_types2

    def test_detect_text_formatting_italic(self) -> None:
        """Test detection of italic text formatting."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        # Test italic text detection
        italic_text = "In legal documents, italics are primarily used for emphasis"
        format_types = serializer._detect_text_formatting(italic_text)
        assert "italic" in format_types

    def test_detect_text_formatting_disabled(self) -> None:
        """Test formatting detection when disabled."""
        doc = MagicMock(spec=DoclingDocument)
        params = LexicalParams(preserve_formatting=False)
        serializer = LexicalDocSerializer(doc=doc, params=params)

        bold_text = "This text contains bold information"
        format_types = serializer._detect_text_formatting(bold_text)
        assert format_types == []

    def test_create_formatted_text_node_bold(self) -> None:
        """Test creation of bold formatted text node."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        text_node = serializer._create_formatted_text_node("Bold text", ["bold"])

        assert text_node["type"] == "text"
        assert text_node["text"] == "Bold text"
        assert text_node["format"] == 1  # FORMAT_BOLD bitmask
        assert text_node["version"] == 1

    def test_create_formatted_text_node_multiple_formats(self) -> None:
        """Test creation of text node with multiple formats."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        text_node = serializer._create_formatted_text_node(
            "Bold and italic text", ["bold", "italic"]
        )

        assert text_node["type"] == "text"
        assert text_node["text"] == "Bold and italic text"
        assert text_node["format"] == 3  # FORMAT_BOLD | FORMAT_ITALIC (1 | 2 = 3)
        assert text_node["version"] == 1


class TestLinkNodes:
    """Test Lexical link node creation."""

    def test_create_link_node(self) -> None:
        """Test creation of Lexical link node."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        link_node = serializer._create_link_node("Click here", "https://example.com")

        assert link_node["type"] == "link"
        assert link_node["url"] == "https://example.com"
        assert len(link_node["children"]) == 1
        assert link_node["children"][0]["text"] == "Click here"
        assert link_node["children"][0]["type"] == "text"
        assert link_node["version"] == 1

    def test_process_text_with_links_simple(self) -> None:
        """Test processing text with a simple URL."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        text = "Visit https://example.com for more info"
        nodes = serializer._process_text_with_links(text)

        assert len(nodes) == 3  # text before, link, text after
        assert nodes[0]["type"] == "text"
        assert nodes[0]["text"] == "Visit "
        assert nodes[1]["type"] == "link"
        assert nodes[1]["url"] == "https://example.com"
        assert nodes[2]["type"] == "text"
        assert nodes[2]["text"] == " for more info"

    def test_process_text_with_links_www(self) -> None:
        """Test processing text with www URL."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        text = "Check www.example.com"
        nodes = serializer._process_text_with_links(text)

        assert len(nodes) == 2  # text before, link
        assert nodes[1]["type"] == "link"
        assert nodes[1]["url"] == "https://www.example.com"  # Protocol added

    def test_process_text_without_links(self) -> None:
        """Test processing text without any links."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        text = "This is plain text without links"
        nodes = serializer._process_text_with_links(text)

        assert len(nodes) == 1
        assert nodes[0]["type"] == "text"
        assert nodes[0]["text"] == text

    def test_process_text_with_multiple_links(self) -> None:
        """Test processing text with multiple URLs."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        text = "Visit https://example.com and www.test.org"
        nodes = serializer._process_text_with_links(text)

        assert len(nodes) == 4  # text, link, text, link
        assert nodes[1]["type"] == "link"
        assert nodes[1]["url"] == "https://example.com"
        assert nodes[3]["type"] == "link"
        assert nodes[3]["url"] == "https://www.test.org"


class TestImageSerializer:
    """Test ImageSerializer for picture elements."""

    def test_image_serializer_basic(self) -> None:
        """Test basic image serialization."""
        picture_item = MagicMock(spec=PictureItem)
        picture_item.image_path = "test.jpg"
        picture_item.alt_text = "Test image"
        picture_item.width = 100
        picture_item.height = 200

        serializer = ImageSerializer()
        result = serializer.serialize(picture_item)

        assert result["type"] == "image"
        assert result["src"] == "test.jpg"
        assert result["altText"] == "Test image"
        assert result["width"] == 100
        assert result["height"] == 200

    def test_image_serializer_with_params(self) -> None:
        """Test image serialization with custom params."""
        picture_item = MagicMock(spec=PictureItem)
        picture_item.path = "custom.png"
        picture_item.caption = "Custom caption"

        params = LexicalParams(version=2)
        serializer = ImageSerializer()
        result = serializer.serialize(picture_item, params)

        assert result["type"] == "image"
        assert result["src"] == "custom.png"
        assert result["altText"] == "Custom caption"
        assert result["version"] == 2

    def test_image_serializer_fallback_attributes(self) -> None:
        """Test image serialization with fallback attribute handling."""
        picture_item = MagicMock(spec=PictureItem)
        # No image_path, should fall back to path
        picture_item.path = "fallback.gif"
        # No alt_text, should fall back to caption
        picture_item.caption = "Fallback caption"

        serializer = ImageSerializer()
        result = serializer.serialize(picture_item)

        assert result["src"] == "fallback.gif"
        assert result["altText"] == "Fallback caption"


class TestComponentSerializerSupport:
    """Test component serializer support."""

    def test_custom_image_serializer(self) -> None:
        """Test custom image serializer integration."""

        class CustomImageSerializer:
            def serialize(
                self, item: PictureItem, params: LexicalParams = None
            ) -> dict:
                return {
                    "type": "custom_image",
                    "src": "custom_" + getattr(item, "path", ""),
                    "version": params.version if params else 1,
                }

        doc = MagicMock(spec=DoclingDocument)
        doc.pictures = []

        custom_serializer = CustomImageSerializer()
        serializer = LexicalDocSerializer(doc=doc, image_serializer=custom_serializer)

        assert serializer.image_serializer == custom_serializer

    def test_custom_table_serializer(self) -> None:
        """Test custom table serializer integration."""

        class CustomTableSerializer:
            def serialize(self, item: TableItem, params: LexicalParams = None) -> dict:
                return {
                    "type": "custom_table",
                    "version": params.version if params else 1,
                }

        doc = MagicMock(spec=DoclingDocument)
        doc.tables = []

        custom_serializer = CustomTableSerializer()
        serializer = LexicalDocSerializer(doc=doc, table_serializer=custom_serializer)

        assert serializer.table_serializer == custom_serializer


class TestAdvancedLexicalFeatures:
    """Test advanced Lexical JSON features."""

    def test_custom_root_attributes(self, sample_docling_document) -> None:
        """Test custom root attributes in output."""
        doc = sample_docling_document

        custom_attrs = {"custom_attribute": "test_value", "theme": "dark"}
        params = LexicalParams(custom_root_attributes=custom_attrs)

        serializer = LexicalDocSerializer(doc=doc, params=params)
        result = serializer.serialize()

        lexical_data = json.loads(result.text)
        root_node = lexical_data["root"]

        assert root_node["custom_attribute"] == "test_value"
        assert root_node["theme"] == "dark"

    def test_metadata_inclusion(self, sample_docling_document) -> None:
        """Test document metadata inclusion."""
        doc = sample_docling_document
        
        # Create a simple object with the origin attributes
        class MockOrigin:
            def __init__(self):
                self.filename = "test.pdf"
                self.mimetype = "application/pdf"
                self.binary_hash = 12345
                self.uri = "file:///test.pdf"
                
        doc.origin = MockOrigin()
        
        params = LexicalParams(include_metadata=True)
        serializer = LexicalDocSerializer(doc=doc, params=params)
        result = serializer.serialize()

        lexical_data = json.loads(result.text)

        assert "metadata" in lexical_data
        metadata = lexical_data["metadata"]
        assert metadata["document_name"] == doc.name
        assert metadata["version"] == doc.version
        assert "origin" in metadata
        assert metadata["origin"]["filename"] == "test.pdf"
        assert metadata["origin"]["mimetype"] == "application/pdf"
        if doc.origin:
            assert "origin" in metadata
            assert metadata["origin"]["mimetype"] == doc.origin.mimetype

    def test_metadata_exclusion(self, sample_docling_document) -> None:
        """Test metadata exclusion when disabled."""
        doc = sample_docling_document

        params = LexicalParams(include_metadata=False)
        serializer = LexicalDocSerializer(doc=doc, params=params)
        result = serializer.serialize()

        lexical_data = json.loads(result.text)
        assert "metadata" not in lexical_data

    def test_json_indent_control(self, sample_docling_document) -> None:
        """Test JSON indentation control."""
        doc = sample_docling_document

        # Test with indentation
        params_with_indent = LexicalParams(indent_json=True)
        serializer_with_indent = LexicalDocSerializer(
            doc=doc, params=params_with_indent
        )
        result_with_indent = serializer_with_indent.serialize()

        # Test without indentation
        params_without_indent = LexicalParams(indent_json=False)
        serializer_without_indent = LexicalDocSerializer(
            doc=doc, params=params_without_indent
        )
        result_without_indent = serializer_without_indent.serialize()

        # Indented JSON should be longer (contains whitespace)
        assert len(result_with_indent.text) > len(result_without_indent.text)
        assert "\n" in result_with_indent.text
        assert "\n" not in result_without_indent.text

    def test_version_consistency(self, sample_docling_document) -> None:
        """Test version consistency across all nodes."""
        doc = sample_docling_document

        custom_version = 3
        params = LexicalParams(version=custom_version)
        serializer = LexicalDocSerializer(doc=doc, params=params)
        result = serializer.serialize()

        lexical_data = json.loads(result.text)
        root_node = lexical_data["root"]

        assert root_node["version"] == custom_version


class TestErrorHandling:
    """Test error handling in advanced features."""

    def test_malformed_picture_handling(self) -> None:
        """Test handling of malformed picture items."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        # Create malformed picture item
        picture_item = MagicMock(spec=PictureItem)
        del picture_item.image_path  # Remove expected attributes
        del picture_item.path
        del picture_item.alt_text
        del picture_item.caption

        result = serializer.image_serializer.serialize(picture_item)

        # Should handle gracefully with empty strings
        assert result["src"] == ""
        assert result["altText"] == ""
        assert result["type"] == "image"

    def test_none_params_handling(self) -> None:
        """Test handling of None params in component serializers."""
        doc = MagicMock(spec=DoclingDocument)
        serializer = LexicalDocSerializer(doc=doc)

        picture_item = MagicMock(spec=PictureItem)
        picture_item.path = "test.jpg"
        picture_item.caption = "Test"

        # Should work with None params
        result = serializer.image_serializer.serialize(picture_item, None)
        assert result["version"] == 1  # Default version
