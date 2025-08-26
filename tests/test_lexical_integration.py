"""Integration tests for advanced LexicalDocSerializer features working together."""

import json
from unittest.mock import MagicMock

import pytest
from docling_core.types import DoclingDocument
from docling_core.types.doc.document import (
    TextItem, 
    SectionHeaderItem,
    PictureItem,
    TableItem,
)

from docpivot.io.serializers.lexicaldocserializer import (
    LexicalDocSerializer,
    LexicalParams,
    ImageSerializer,
)


class TestLexicalIntegration:
    """Integration tests for advanced LexicalDocSerializer features."""

    def test_complete_document_serialization(self) -> None:
        """Test serialization of a complete document with all advanced features."""
        # Create a mock DoclingDocument with various elements
        doc = MagicMock(spec=DoclingDocument)
        doc.name = "Advanced Test Document"
        doc.version = "2.1.0"
        
        # Mock origin
        origin = MagicMock()
        origin.mimetype = "application/pdf"
        origin.filename = "advanced_test.pdf"
        origin.binary_hash = 987654321
        origin.uri = "file://advanced_test.pdf"
        doc.origin = origin
        
        # Create body with various text items
        body = MagicMock()
        
        # Mock text items with formatting and links
        text1 = MagicMock(spec=SectionHeaderItem)
        text1.label = "section_header"
        text1.text = "IMPORTANT HEADING"  # Should be detected as bold
        text1.level = 1
        
        text2 = MagicMock(spec=TextItem)
        text2.label = "text"
        text2.text = "Visit https://example.com for more details about our services."
        
        text3 = MagicMock(spec=TextItem)
        text3.label = "text"
        text3.text = "In legal documents, italics are primarily used for emphasis and citations."
        
        doc.texts = [text1, text2, text3]
        
        # Mock pictures
        picture1 = MagicMock(spec=PictureItem)
        picture1.image_path = "logo.png"
        picture1.alt_text = "Company logo"
        picture1.width = 200
        picture1.height = 100
        
        doc.pictures = [picture1]
        
        # Mock body children with references
        ref1 = MagicMock()
        ref1.cref = "doc/texts/0"
        ref2 = MagicMock()
        ref2.cref = "doc/texts/1"
        ref3 = MagicMock()
        ref3.cref = "doc/texts/2"
        ref4 = MagicMock()
        ref4.cref = "doc/pictures/0"
        
        body.children = [ref1, ref2, ref3, ref4]
        doc.body = body
        
        # Mock empty collections
        doc.tables = []
        doc.groups = []
        
        # Set up advanced parameters
        params = LexicalParams(
            include_metadata=True,
            preserve_formatting=True,
            indent_json=True,
            version=2,
            custom_root_attributes={
                "theme": "professional",
                "editable": True
            }
        )
        
        # Create custom image serializer
        class TestImageSerializer:
            def serialize(self, item, params=None):
                return {
                    "type": "enhanced_image",
                    "src": f"enhanced_{getattr(item, 'image_path', '')}",
                    "altText": getattr(item, 'alt_text', ''),
                    "width": getattr(item, 'width', None),
                    "height": getattr(item, 'height', None),
                    "version": params.version if params else 1,
                    "enhancement": "applied"
                }
        
        # Serialize with all advanced features
        serializer = LexicalDocSerializer(
            doc=doc,
            params=params,
            image_serializer=TestImageSerializer()
        )
        
        result = serializer.serialize()
        lexical_data = json.loads(result.text)
        
        # Verify root structure
        root = lexical_data["root"]
        assert root["version"] == 2
        assert root["theme"] == "professional"
        assert root["editable"] is True
        
        # Verify metadata inclusion
        assert "metadata" in lexical_data
        metadata = lexical_data["metadata"]
        assert metadata["document_name"] == "Advanced Test Document"
        assert metadata["version"] == "2.1.0"
        assert metadata["origin"]["filename"] == "advanced_test.pdf"
        
        # Verify content structure
        children = root["children"]
        assert len(children) == 4  # heading, 2 paragraphs, image
        
        # Check heading with formatting
        heading = children[0]
        assert heading["type"] == "heading"
        assert heading["tag"] == "h1"
        heading_text = heading["children"][0]
        assert "IMPORTANT HEADING" in heading_text["text"]
        assert heading_text["format"] == 1  # Bold formatting
        
        # Check paragraph with link
        paragraph_with_link = children[1]
        assert paragraph_with_link["type"] == "paragraph"
        para_children = paragraph_with_link["children"]
        
        # Should have text before, link, and text after
        link_found = False
        for child in para_children:
            if child.get("type") == "link":
                assert child["url"] == "https://example.com"
                link_found = True
        assert link_found, "Link should be detected and created"
        
        # Check paragraph with italic formatting
        italic_paragraph = children[2]
        assert italic_paragraph["type"] == "paragraph"
        italic_text = italic_paragraph["children"][0]
        assert italic_text["format"] == 2  # Italic formatting
        assert "italics are primarily used" in italic_text["text"]
        
        # Check enhanced image
        image = children[3]
        assert image["type"] == "enhanced_image"
        assert image["src"] == "enhanced_logo.png"
        assert image["altText"] == "Company logo"
        assert image["width"] == 200
        assert image["height"] == 100
        assert image["enhancement"] == "applied"
        assert image["version"] == 2

    def test_mixed_content_serialization(self) -> None:
        """Test serialization of mixed content types with advanced features."""
        doc = MagicMock(spec=DoclingDocument)
        doc.name = "Mixed Content Document"
        
        # Create text with multiple URLs and formatting
        text_with_links = MagicMock(spec=TextItem)
        text_with_links.label = "text"
        text_with_links.text = "Check https://docs.example.com and www.support.example.org for help."
        
        doc.texts = [text_with_links]
        doc.pictures = []
        doc.tables = []
        doc.groups = []
        
        # Mock body
        body = MagicMock()
        ref1 = MagicMock()
        ref1.cref = "doc/texts/0"
        body.children = [ref1]
        doc.body = body
        
        params = LexicalParams(preserve_formatting=True)
        serializer = LexicalDocSerializer(doc=doc, params=params)
        result = serializer.serialize()
        
        lexical_data = json.loads(result.text)
        paragraph = lexical_data["root"]["children"][0]
        
        # Should have multiple children: text, link, text, link, text
        children = paragraph["children"]
        assert len(children) == 5
        
        # Verify link nodes
        links = [child for child in children if child.get("type") == "link"]
        assert len(links) == 2
        assert links[0]["url"] == "https://docs.example.com"
        assert links[1]["url"] == "https://www.support.example.org"

    def test_configuration_override(self) -> None:
        """Test that configuration parameters properly override defaults."""
        doc = MagicMock(spec=DoclingDocument)
        doc.name = "Config Test"
        doc.body = MagicMock()
        doc.body.children = []
        
        # Test with formatting disabled
        params_no_formatting = LexicalParams(
            preserve_formatting=False,
            include_metadata=False,
            indent_json=False
        )
        
        serializer = LexicalDocSerializer(doc=doc, params=params_no_formatting)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)
        
        # Should not have metadata
        assert "metadata" not in lexical_data
        
        # JSON should be compact (no indentation)
        assert "\n" not in result.text
        
        # Verify formatting would be disabled (test with mock text item)
        mock_text = "THIS IS ALL UPPERCASE"
        format_types = serializer._detect_text_formatting(mock_text)
        assert format_types == []  # Formatting disabled

    def test_error_resilience(self) -> None:
        """Test that advanced features handle errors gracefully."""
        doc = MagicMock(spec=DoclingDocument)
        doc.name = "Error Test"
        
        # Create malformed text item
        malformed_text = MagicMock(spec=TextItem)
        del malformed_text.text  # Remove required attribute
        malformed_text.label = "text"
        
        doc.texts = [malformed_text]
        doc.pictures = []
        doc.tables = []
        doc.groups = []
        
        # Mock body with reference to malformed text
        body = MagicMock()
        ref1 = MagicMock()
        ref1.cref = "doc/texts/0"
        body.children = [ref1]
        doc.body = body
        
        # Should handle errors gracefully
        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()
        
        # Should still produce valid JSON
        lexical_data = json.loads(result.text)
        assert "root" in lexical_data
        
        # Should have handled the malformed text gracefully
        children = lexical_data["root"]["children"]
        if children:  # If any children were created despite error
            assert all(child.get("type") in ["heading", "paragraph"] for child in children)