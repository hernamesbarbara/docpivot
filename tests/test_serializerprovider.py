"""Tests for SerializerProvider class."""

from pathlib import Path
from typing import Any, Dict

import pytest
from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.transforms.serializer.doctags import DocTagsDocSerializer, DocTagsParams
from docling_core.transforms.serializer.html import HTMLDocSerializer, HTMLParams
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer, MarkdownParams
from docling_core.types import DoclingDocument

from docpivot.io.serializers import SerializerProvider


class TestSerializerProvider:
    """Test suite for SerializerProvider class."""

    def test_get_serializer_markdown_format(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer returns MarkdownDocSerializer for markdown format."""
        serializer = SerializerProvider.get_serializer("markdown", sample_docling_document)
        
        assert isinstance(serializer, MarkdownDocSerializer)
        assert isinstance(serializer, BaseDocSerializer)

    def test_get_serializer_md_alias(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer returns MarkdownDocSerializer for md alias."""
        serializer = SerializerProvider.get_serializer("md", sample_docling_document)
        
        assert isinstance(serializer, MarkdownDocSerializer)

    def test_get_serializer_html_format(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer returns HTMLDocSerializer for html format."""
        serializer = SerializerProvider.get_serializer("html", sample_docling_document)
        
        assert isinstance(serializer, HTMLDocSerializer)
        assert isinstance(serializer, BaseDocSerializer)

    def test_get_serializer_doctags_format(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer returns DocTagsDocSerializer for doctags format."""
        serializer = SerializerProvider.get_serializer("doctags", sample_docling_document)
        
        assert isinstance(serializer, DocTagsDocSerializer)
        assert isinstance(serializer, BaseDocSerializer)

    def test_get_serializer_case_insensitive(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer handles case insensitive format names."""
        formats = ["MARKDOWN", "Html", "DocTags", "MD"]
        expected_types = [MarkdownDocSerializer, HTMLDocSerializer, DocTagsDocSerializer, MarkdownDocSerializer]
        
        for format_name, expected_type in zip(formats, expected_types):
            serializer = SerializerProvider.get_serializer(format_name, sample_docling_document)
            assert isinstance(serializer, expected_type)

    def test_get_serializer_strips_whitespace(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer strips whitespace from format names."""
        serializer = SerializerProvider.get_serializer("  markdown  ", sample_docling_document)
        assert isinstance(serializer, MarkdownDocSerializer)

    def test_get_serializer_unsupported_format(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer raises ValueError for unsupported format."""
        with pytest.raises(ValueError, match="Unsupported format 'unsupported'"):
            SerializerProvider.get_serializer("unsupported", sample_docling_document)

    def test_get_serializer_with_parameters(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer passes parameters to serializer constructor."""
        params = MarkdownParams(wrap_width=80, escape_html=False)
        
        serializer = SerializerProvider.get_serializer(
            "markdown", 
            sample_docling_document,
            params=params
        )
        
        assert isinstance(serializer, MarkdownDocSerializer)
        assert serializer.params.wrap_width == 80
        assert serializer.params.escape_html is False

    def test_get_serializer_html_with_parameters(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer with HTML parameters."""
        params = HTMLParams(prettify=True, html_lang="en-US")
        
        serializer = SerializerProvider.get_serializer(
            "html",
            sample_docling_document, 
            params=params
        )
        
        assert isinstance(serializer, HTMLDocSerializer)
        assert serializer.params.prettify is True
        assert serializer.params.html_lang == "en-US"

    def test_get_serializer_doctags_with_parameters(self, sample_docling_document: DoclingDocument) -> None:
        """Test get_serializer with DocTags parameters."""
        params = DocTagsParams(add_content=True, add_location=False)
        
        serializer = SerializerProvider.get_serializer(
            "doctags",
            sample_docling_document,
            params=params
        )
        
        assert isinstance(serializer, DocTagsDocSerializer)
        assert serializer.params.add_content is True
        assert serializer.params.add_location is False

    def test_register_serializer_custom_class(self, sample_docling_document: DoclingDocument) -> None:
        """Test register_serializer allows custom serializer registration."""
        # Use MarkdownDocSerializer as a custom serializer (it's a real working serializer)
        # Save original state
        original_serializers = SerializerProvider._serializers.copy()
        
        try:
            # Register MarkdownDocSerializer under a custom name
            SerializerProvider.register_serializer("custom", MarkdownDocSerializer)
            
            # Verify it was registered
            assert "custom" in SerializerProvider.list_formats()
            
            # Test getting the custom serializer
            serializer = SerializerProvider.get_serializer("custom", sample_docling_document)
            assert isinstance(serializer, MarkdownDocSerializer)
            assert isinstance(serializer, BaseDocSerializer)
            assert serializer.doc == sample_docling_document
        finally:
            # Clean up - restore original serializers
            SerializerProvider._serializers = original_serializers

    def test_register_serializer_invalid_class(self) -> None:
        """Test register_serializer raises TypeError for invalid serializer class."""
        class NotASerializer:
            pass
        
        with pytest.raises(TypeError, match="Serializer class must be a subclass of BaseDocSerializer"):
            SerializerProvider.register_serializer("invalid", NotASerializer)  # type: ignore[arg-type]

    def test_register_serializer_overrides_existing(self, sample_docling_document: DoclingDocument) -> None:
        """Test register_serializer can override existing format."""
        # Save original
        original_serializer_cls = SerializerProvider._serializers["markdown"]
        
        try:
            # Override markdown with HTML serializer (different type)
            SerializerProvider.register_serializer("markdown", HTMLDocSerializer)
            
            # Verify override worked
            serializer = SerializerProvider.get_serializer("markdown", sample_docling_document)
            assert isinstance(serializer, HTMLDocSerializer)
            assert not isinstance(serializer, MarkdownDocSerializer)
            assert serializer.doc == sample_docling_document
        finally:
            # Restore original
            SerializerProvider._serializers["markdown"] = original_serializer_cls

    def test_list_formats(self) -> None:
        """Test list_formats returns all supported formats."""
        # Save and restore the original state to avoid test pollution
        original_serializers = SerializerProvider._serializers.copy()
        
        try:
            # Reset to only built-in serializers
            SerializerProvider._serializers = {
                "markdown": MarkdownDocSerializer,
                "md": MarkdownDocSerializer,
                "doctags": DocTagsDocSerializer,
                "html": HTMLDocSerializer,
            }
            
            formats = SerializerProvider.list_formats()
            expected_formats = {"markdown", "md", "doctags", "html"}
            assert set(formats) == expected_formats
        finally:
            # Restore original state
            SerializerProvider._serializers = original_serializers

    def test_is_format_supported(self) -> None:
        """Test is_format_supported checks format availability."""
        # Test supported formats
        assert SerializerProvider.is_format_supported("markdown") is True
        assert SerializerProvider.is_format_supported("html") is True
        assert SerializerProvider.is_format_supported("doctags") is True
        assert SerializerProvider.is_format_supported("md") is True
        
        # Test case insensitive
        assert SerializerProvider.is_format_supported("MARKDOWN") is True
        assert SerializerProvider.is_format_supported("Html") is True
        
        # Test with whitespace
        assert SerializerProvider.is_format_supported("  markdown  ") is True
        
        # Test unsupported format
        assert SerializerProvider.is_format_supported("unsupported") is False
        assert SerializerProvider.is_format_supported("text") is False

    def test_builtin_serializers_registered(self) -> None:
        """Test that all expected built-in serializers are registered."""
        expected_serializers = {
            "markdown": MarkdownDocSerializer,
            "md": MarkdownDocSerializer,
            "doctags": DocTagsDocSerializer, 
            "html": HTMLDocSerializer,
        }
        
        for format_name, expected_class in expected_serializers.items():
            assert format_name in SerializerProvider._serializers
            assert SerializerProvider._serializers[format_name] == expected_class

    def test_serialization_produces_output(self, sample_docling_document: DoclingDocument) -> None:
        """Test that serializers actually produce output."""
        formats_to_test = ["markdown", "html", "doctags"]
        
        for format_name in formats_to_test:
            serializer = SerializerProvider.get_serializer(format_name, sample_docling_document)
            result = serializer.serialize()
            
            # Should have text output
            assert hasattr(result, 'text')
            assert isinstance(result.text, str)
            # For a minimal document, we might get empty text, but at least it shouldn't error

    def test_error_message_includes_supported_formats(self, sample_docling_document: DoclingDocument) -> None:
        """Test that error message for unsupported format lists available formats."""
        with pytest.raises(ValueError) as exc_info:
            SerializerProvider.get_serializer("unsupported", sample_docling_document)
        
        error_msg = str(exc_info.value)
        assert "Unsupported format 'unsupported'" in error_msg
        assert "Supported formats:" in error_msg
        
        # Should contain all the format names
        for format_name in ["markdown", "md", "html", "doctags"]:
            assert format_name in error_msg


class TestSerializerProviderIntegration:
    """Integration tests with real document loading."""

    def test_serializer_with_docling_json_reader_output(self, sample_docling_json_path: Path) -> None:
        """Test SerializerProvider with output from DoclingJsonReader."""
        from docpivot.io.readers import DoclingJsonReader
        
        # Load a real document
        reader = DoclingJsonReader()
        doc = reader.load_data(str(sample_docling_json_path))
        
        # Test serialization to different formats
        formats_to_test = ["markdown", "html", "doctags"]
        
        for format_name in formats_to_test:
            serializer = SerializerProvider.get_serializer(format_name, doc)
            result = serializer.serialize()
            
            assert isinstance(result.text, str)
            # For a real document, we should get some actual content
            assert len(result.text.strip()) > 0

    def test_markdown_serializer_with_custom_params(self, sample_docling_json_path: Path) -> None:
        """Test MarkdownDocSerializer with custom parameters on real document."""
        from docpivot.io.readers import DoclingJsonReader
        
        # Load document
        reader = DoclingJsonReader()
        doc = reader.load_data(str(sample_docling_json_path))
        
        # Create serializer with custom parameters
        params = MarkdownParams(
            wrap_width=60,
            escape_html=True,
            include_formatting=True
        )
        
        serializer = SerializerProvider.get_serializer("markdown", doc, params=params)
        result = serializer.serialize()
        
        assert isinstance(result.text, str)
        assert len(result.text.strip()) > 0

    def test_html_serializer_with_custom_params(self, sample_docling_json_path: Path) -> None:
        """Test HTMLDocSerializer with custom parameters on real document."""
        from docpivot.io.readers import DoclingJsonReader
        
        # Load document
        reader = DoclingJsonReader()
        doc = reader.load_data(str(sample_docling_json_path))
        
        # Create serializer with custom parameters
        params = HTMLParams(
            prettify=True,
            html_lang="en",
            css_styles="body { font-family: Arial; }"
        )
        
        serializer = SerializerProvider.get_serializer("html", doc, params=params)
        result = serializer.serialize()
        
        assert isinstance(result.text, str)
        assert len(result.text.strip()) > 0
        # Should contain HTML structure
        assert "<" in result.text and ">" in result.text