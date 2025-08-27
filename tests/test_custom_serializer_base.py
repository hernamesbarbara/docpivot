"""Comprehensive tests for custom serializer base module."""

import unittest
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock, patch
from docling_core.types import DoclingDocument
from docling_core.transforms.serializer.base import SerializationResult

from docpivot.io.serializers.custom_serializer_base import (
    CustomSerializerParams,
    CustomSerializerBase,
)


class TestCustomSerializerParams(unittest.TestCase):
    """Test CustomSerializerParams class."""

    def test_init(self):
        """Test CustomSerializerParams initialization."""
        params = CustomSerializerParams()
        # Should initialize without errors
        self.assertIsNotNone(params)


class TestCustomSerializerBase(unittest.TestCase):
    """Test CustomSerializerBase class using mocking."""

    def setUp(self):
        """Set up test fixtures."""
        self.doc = Mock(spec=DoclingDocument)
        self.doc.body = Mock()
        self.doc.body.text = "Test text"
        self.doc.body.children = []
        self.doc.name = "test_doc"
        self.doc.origin = {"source": "test"}
        self.doc.furniture = []

    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_init_with_defaults(self, mock_super_init):
        """Test initialization with default parameters."""
        mock_super_init.return_value = None
        
        # Create a concrete implementation for testing
        class TestSerializer(CustomSerializerBase):
            @property
            def output_format(self): return "test"
            @property
            def file_extension(self): return ".test"
            def serialize(self): return SerializationResult(text="test")
        
        serializer = TestSerializer(doc=self.doc)
        
        self.assertEqual(serializer.doc, self.doc)
        self.assertIsInstance(serializer.params, CustomSerializerParams)
        self.assertEqual(serializer.component_serializers, {})
        self.assertEqual(serializer.config, {})
        mock_super_init.assert_called_once()

    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_init_with_custom_params(self, mock_super_init):
        """Test initialization with custom parameters."""
        mock_super_init.return_value = None
        
        class TestParams(CustomSerializerParams):
            def __init__(self, indent=2):
                super().__init__()
                self.indent = indent
        
        class TestSerializer(CustomSerializerBase):
            @property
            def output_format(self): return "test"
            @property
            def file_extension(self): return ".test"
            def serialize(self): return SerializationResult(text="test")
        
        params = TestParams(indent=4)
        component_serializers = {"table": Mock()}
        kwargs = {"option1": "value1"}
        
        serializer = TestSerializer(
            doc=self.doc,
            params=params,
            component_serializers=component_serializers,
            **kwargs
        )
        
        self.assertEqual(serializer.params.indent, 4)
        self.assertEqual(serializer.component_serializers, component_serializers)
        self.assertEqual(serializer.config, kwargs)

    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_validate_configuration_empty_format(self, mock_super_init):
        """Test _validate_configuration with empty output format."""
        mock_super_init.return_value = None
        
        class InvalidSerializer(CustomSerializerBase):
            @property
            def output_format(self): return ""
            @property
            def file_extension(self): return ".test"
            def serialize(self): return SerializationResult(text="test")
        
        with self.assertRaises(ValueError) as ctx:
            InvalidSerializer(doc=self.doc)
        
        self.assertIn("must define output_format", str(ctx.exception))

    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_validate_configuration_invalid_extension(self, mock_super_init):
        """Test _validate_configuration with invalid file extension."""
        mock_super_init.return_value = None
        
        class BadExtensionSerializer(CustomSerializerBase):
            @property
            def output_format(self): return "test"
            @property
            def file_extension(self): return "test"  # Missing leading dot
            def serialize(self): return SerializationResult(text="test")
        
        with self.assertRaises(ValueError) as ctx:
            BadExtensionSerializer(doc=self.doc)
        
        self.assertIn("File extension must start with '.'", str(ctx.exception))

    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_validate_configuration_missing_extension(self, mock_super_init):
        """Test _validate_configuration with missing file extension."""
        mock_super_init.return_value = None
        
        class NoExtensionSerializer(CustomSerializerBase):
            @property
            def output_format(self): return "test"
            @property
            def file_extension(self): return ""
            def serialize(self): return SerializationResult(text="test")
        
        with self.assertRaises(ValueError) as ctx:
            NoExtensionSerializer(doc=self.doc)
        
        self.assertIn("must define file_extension", str(ctx.exception))

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_properties(self, mock_init):
        """Test property methods."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        serializer.doc = self.doc
        serializer.params = CustomSerializerParams()
        serializer.component_serializers = {}
        serializer.config = {}
        
        # Test default properties
        self.assertIsNone(serializer.format_description)
        self.assertEqual(serializer.version, "1.0.0")
        self.assertEqual(serializer.mimetype, "text/plain")
        
        expected_capabilities = {
            "text_content": True,
            "document_structure": True,
            "metadata": False,
            "images": False,
            "tables": False,
            "formatting": False,
        }
        self.assertEqual(serializer.capabilities, expected_capabilities)

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_get_supported_features(self, mock_init):
        """Test get_supported_features method."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        serializer.doc = self.doc
        serializer.capabilities = {"test": True}
        
        features = serializer.get_supported_features()
        self.assertEqual(features, {"test": True})
        
        # Ensure it returns a copy
        features["test"] = False
        self.assertTrue(serializer.capabilities["test"])

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_validate_document(self, mock_init):
        """Test validate_document method."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        
        # Valid document should not raise
        serializer.validate_document(self.doc)
        
        # None should raise
        with self.assertRaises(ValueError) as ctx:
            serializer.validate_document(None)
        self.assertIn("Document cannot be None", str(ctx.exception))

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_get_metadata(self, mock_init):
        """Test get_metadata method."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        serializer.output_format = "test"
        serializer.file_extension = ".test"
        serializer.version = "1.0.0"
        serializer.capabilities = {"test": True}
        serializer.mimetype = "text/plain"
        
        metadata = serializer.get_metadata()
        
        self.assertEqual(metadata["output_format"], "test")
        self.assertEqual(metadata["file_extension"], ".test")
        self.assertEqual(metadata["version"], "1.0.0")
        self.assertEqual(metadata["capabilities"], {"test": True})
        self.assertEqual(metadata["mimetype"], "text/plain")

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_serialize_text_content_with_body(self, mock_init):
        """Test _serialize_text_content with document body."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        
        # Create nested structure
        child1 = Mock()
        child1.text = "Child 1"
        child1.children = []
        
        grandchild = Mock()
        grandchild.text = "Grandchild"
        grandchild.children = []
        
        child2 = Mock()
        child2.text = "Child 2"
        child2.children = [grandchild]
        
        self.doc.body.text = "Root"
        self.doc.body.children = [child1, child2]
        serializer.doc = self.doc
        
        text = serializer._serialize_text_content()
        
        self.assertEqual(text, "Root\nChild 1\nChild 2\nGrandchild")

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_serialize_text_content_no_body(self, mock_init):
        """Test _serialize_text_content with no body."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        self.doc.body = None
        serializer.doc = self.doc
        
        text = serializer._serialize_text_content()
        self.assertEqual(text, "")

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_serialize_text_content_no_body_attribute(self, mock_init):
        """Test _serialize_text_content when doc has no body attribute."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        doc = Mock(spec=DoclingDocument)
        del doc.body
        serializer.doc = doc
        
        text = serializer._serialize_text_content()
        self.assertEqual(text, "")

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_serialize_with_structure(self, mock_init):
        """Test _serialize_with_structure method."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        
        body_item = Mock()
        body_item.text = "Body text"
        body_item.label = "paragraph"
        body_item.children = []
        
        furniture_item = Mock()
        furniture_item.text = "Header"
        furniture_item.label = "header"
        furniture_item.children = []
        
        self.doc.body = body_item
        self.doc.furniture = [furniture_item]
        serializer.doc = self.doc
        
        result = serializer._serialize_with_structure()
        
        self.assertIn("metadata", result)
        self.assertIn("content", result)
        self.assertEqual(result["metadata"]["name"], "test_doc")
        self.assertIn("body", result["content"])
        self.assertIn("furniture", result["content"])

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_item_to_dict(self, mock_init):
        """Test _item_to_dict method."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        
        # Test with all attributes
        item = Mock()
        item.text = "Item text"
        item.label = "paragraph"
        child = Mock()
        child.text = "Child"
        child.label = "span"
        child.children = []
        item.children = [child]
        
        result = serializer._item_to_dict(item)
        
        self.assertEqual(result["text"], "Item text")
        self.assertEqual(result["label"], "paragraph")
        self.assertEqual(len(result["children"]), 1)
        
        # Test with minimal attributes
        minimal_item = Mock()
        result = serializer._item_to_dict(minimal_item)
        self.assertEqual(result, {})
        
        # Test with empty values
        empty_item = Mock()
        empty_item.text = ""
        empty_item.label = None
        empty_item.children = []
        result = serializer._item_to_dict(empty_item)
        self.assertEqual(result, {})

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_apply_component_serializers(self, mock_init):
        """Test _apply_component_serializers method."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        
        content = "Original content"
        result = serializer._apply_component_serializers(content)
        
        # Base implementation should return content unchanged
        self.assertEqual(result, content)

    @patch.object(CustomSerializerBase, '__init__', return_value=None)
    def test_str_and_repr(self, mock_init):
        """Test __str__ and __repr__ methods."""
        serializer = CustomSerializerBase.__new__(CustomSerializerBase)
        serializer.__class__.__name__ = "TestSerializer"
        serializer.output_format = "test"
        serializer.version = "1.0.0"
        serializer.file_extension = ".test"
        
        str_repr = str(serializer)
        self.assertEqual(str_repr, "TestSerializer(test v1.0.0)")
        
        repr_str = repr(serializer)
        expected = "TestSerializer(output_format='test', version='1.0.0', extension='.test')"
        self.assertEqual(repr_str, expected)

    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        # Create instance without calling __init__
        base = CustomSerializerBase.__new__(CustomSerializerBase)
        base.doc = self.doc
        
        # Test output_format
        with self.assertRaises(NotImplementedError) as ctx:
            _ = base.output_format
        self.assertIn("Subclasses must define output_format", str(ctx.exception))
        
        # Test file_extension
        with self.assertRaises(NotImplementedError) as ctx:
            _ = base.file_extension
        self.assertIn("Subclasses must define file_extension", str(ctx.exception))
        
        # Test serialize
        with self.assertRaises(NotImplementedError) as ctx:
            base.serialize()
        self.assertIn("Subclasses must implement serialize method", str(ctx.exception))

    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_subclass_customization(self, mock_super_init):
        """Test that subclasses can customize properties."""
        mock_super_init.return_value = None
        
        class CustomSerializer(CustomSerializerBase):
            @property
            def output_format(self): return "custom"
            @property
            def file_extension(self): return ".custom"
            @property
            def format_description(self): return "Custom format"
            @property
            def version(self): return "2.0.0"
            @property
            def mimetype(self): return "application/custom"
            @property
            def capabilities(self):
                return {"all": True}
            
            def serialize(self): return SerializationResult(text="custom")
            
            def validate_document(self, doc):
                super().validate_document(doc)
                if not hasattr(doc, 'custom_field'):
                    raise ValueError("Missing custom_field")
            
            def _apply_component_serializers(self, content):
                return content.upper()
        
        serializer = CustomSerializer(doc=self.doc)
        
        self.assertEqual(serializer.output_format, "custom")
        self.assertEqual(serializer.file_extension, ".custom")
        self.assertEqual(serializer.format_description, "Custom format")
        self.assertEqual(serializer.version, "2.0.0")
        self.assertEqual(serializer.mimetype, "application/custom")
        self.assertEqual(serializer.capabilities, {"all": True})
        
        # Test custom validation
        with self.assertRaises(ValueError) as ctx:
            serializer.validate_document(self.doc)
        self.assertIn("Missing custom_field", str(ctx.exception))
        
        # Test custom component serializer
        result = serializer._apply_component_serializers("test")
        self.assertEqual(result, "TEST")


if __name__ == "__main__":
    unittest.main()