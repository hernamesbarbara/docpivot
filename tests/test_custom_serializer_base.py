"""Comprehensive tests for custom serializer base module."""

import unittest
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, MagicMock, patch
from docling_core.types import DoclingDocument
from docling_core.transforms.serializer.base import SerializationResult

from docpivot.io.serializers.custom_serializer_base import (
    CustomSerializerParams,
    CustomSerializerBase,
)


class BaseTestSerializerMixin:
    """Mixin providing required BaseDocSerializer methods."""
    
    # Implement all abstract methods from BaseDocSerializer
    def serialize_annotations(self, annotations) -> str:
        return ""
    
    def serialize_bold(self, text: str) -> str:
        return text
    
    def serialize_captions(self, captions) -> str:
        return ""
    
    def serialize_hyperlink(self, text: str, url: str) -> str:
        return text
    
    def serialize_italic(self, text: str) -> str:
        return text
    
    def serialize_strikethrough(self, text: str) -> str:
        return text
    
    def serialize_subscript(self, text: str) -> str:
        return text
    
    def serialize_superscript(self, text: str) -> str:
        return text
    
    def serialize_underline(self, text: str) -> str:
        return text
    
    def get_excluded_refs(self) -> List[str]:
        return []
    
    def get_parts(self) -> List[str]:
        return []
    
    def post_process(self, text: str) -> str:
        return text
    
    def requires_page_break(self, item) -> bool:
        return False


class ConcreteTestSerializer(BaseTestSerializerMixin, CustomSerializerBase):
    """Concrete implementation for testing purposes."""
    
    @property
    def output_format(self) -> str:
        return getattr(self, '_output_format', 'test')
    
    @property
    def file_extension(self) -> str:
        return getattr(self, '_file_extension', '.test')
    
    def serialize(self) -> SerializationResult:
        return SerializationResult(text="test")


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

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        # Create a concrete implementation for testing
        class TestSerializer(BaseTestSerializerMixin, CustomSerializerBase):
            @property
            def output_format(self): return "test"
            @property
            def file_extension(self): return ".test"
            def serialize(self): return SerializationResult(text="test")
            
            def __init__(self, doc, **kwargs):
                # Bypass BaseDocSerializer.__init__ but still run CustomSerializerBase logic
                self.doc = doc  # Store doc directly
                # Now call CustomSerializerBase logic (without calling super)
                self.params = kwargs.get('params', None) or CustomSerializerParams()
                self.component_serializers = kwargs.get('component_serializers', None) or {}
                self.config = kwargs
                self._validate_configuration()
        
        serializer = TestSerializer(doc=self.doc)
        
        self.assertEqual(serializer.doc, self.doc)
        self.assertIsInstance(serializer.params, CustomSerializerParams)
        self.assertEqual(serializer.component_serializers, {})
        self.assertEqual(serializer.config, {})

    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_init_with_custom_params(self, mock_super_init):
        """Test initialization with custom parameters."""
        mock_super_init.return_value = None
        
        class TestParams(CustomSerializerParams):
            def __init__(self, indent=2):
                super().__init__()
                self.indent = indent
        
        class TestSerializer(BaseTestSerializerMixin, CustomSerializerBase):
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
        
        class InvalidSerializer(BaseTestSerializerMixin, CustomSerializerBase):
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
        
        class BadExtensionSerializer(BaseTestSerializerMixin, CustomSerializerBase):
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
        
        class NoExtensionSerializer(BaseTestSerializerMixin, CustomSerializerBase):
            @property
            def output_format(self): return "test"
            @property
            def file_extension(self): return ""
            def serialize(self): return SerializationResult(text="test")
        
        with self.assertRaises(ValueError) as ctx:
            NoExtensionSerializer(doc=self.doc)
        
        self.assertIn("must define file_extension", str(ctx.exception))

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_properties(self, mock_init):
        """Test property methods."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
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

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_get_supported_features(self, mock_init):
        """Test get_supported_features method."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        serializer.doc = self.doc
        
        features = serializer.get_supported_features()
        # Check it returns the default capabilities
        expected = {
            "text_content": True,
            "document_structure": True,
            "metadata": False,
            "images": False,
            "tables": False,
            "formatting": False,
        }
        self.assertEqual(features, expected)
        
        # Ensure it returns a copy
        features["test"] = True
        self.assertNotIn("test", serializer.get_supported_features())

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_validate_document(self, mock_init):
        """Test validate_document method."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        
        # Valid document should not raise
        serializer.validate_document(self.doc)
        
        # None should raise
        with self.assertRaises(ValueError) as ctx:
            serializer.validate_document(None)
        self.assertIn("Document cannot be None", str(ctx.exception))

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_get_metadata(self, mock_init):
        """Test get_metadata method."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        # Use private attributes that properties can read
        serializer._output_format = "test"
        serializer._file_extension = ".test"
        
        metadata = serializer.get_metadata()
        
        self.assertEqual(metadata["output_format"], "test")
        self.assertEqual(metadata["file_extension"], ".test")
        self.assertEqual(metadata["version"], "1.0.0")
        self.assertIn("text_content", metadata["capabilities"])
        self.assertEqual(metadata["mimetype"], "text/plain")

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_serialize_text_content_with_body(self, mock_init):
        """Test _serialize_text_content with document body."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        
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

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_serialize_text_content_no_body(self, mock_init):
        """Test _serialize_text_content with no body."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        self.doc.body = None
        serializer.doc = self.doc
        
        text = serializer._serialize_text_content()
        self.assertEqual(text, "")

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_serialize_text_content_no_body_attribute(self, mock_init):
        """Test _serialize_text_content when doc has no body attribute."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        doc = Mock(spec=DoclingDocument)
        del doc.body
        serializer.doc = doc
        
        text = serializer._serialize_text_content()
        self.assertEqual(text, "")

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_serialize_with_structure(self, mock_init):
        """Test _serialize_with_structure method."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        
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

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_item_to_dict(self, mock_init):
        """Test _item_to_dict method."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        
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
        minimal_item = Mock(spec=[])  # Spec with empty list means no attributes
        result = serializer._item_to_dict(minimal_item)
        self.assertEqual(result, {})
        
        # Test with empty values
        empty_item = Mock()
        empty_item.text = ""
        empty_item.label = None
        empty_item.children = []
        result = serializer._item_to_dict(empty_item)
        self.assertEqual(result, {})

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_apply_component_serializers(self, mock_init):
        """Test _apply_component_serializers method."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        
        content = "Original content"
        result = serializer._apply_component_serializers(content)
        
        # Base implementation should return content unchanged
        self.assertEqual(result, content)

    @patch.object(ConcreteTestSerializer, '__init__', return_value=None)
    def test_str_and_repr(self, mock_init):
        """Test __str__ and __repr__ methods."""
        serializer = ConcreteTestSerializer.__new__(ConcreteTestSerializer)
        # Use private attributes that properties can read
        serializer._output_format = "test"
        serializer._file_extension = ".test"
        
        str_repr = str(serializer)
        self.assertEqual(str_repr, "ConcreteTestSerializer(test v1.0.0)")
        
        repr_str = repr(serializer)
        expected = "ConcreteTestSerializer(output_format='test', version='1.0.0', extension='.test')"
        self.assertEqual(repr_str, expected)

    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        # Test that CustomSerializerBase correctly defines abstract methods
        # We can't instantiate it directly due to abstract methods
        with self.assertRaises(TypeError) as ctx:
            CustomSerializerBase(doc=self.doc)
        
        # Error message should mention the abstract methods
        self.assertIn("Can't instantiate abstract class", str(ctx.exception))
        
        # Now test that abstract methods raise NotImplementedError when not overridden properly
        class BadSerializer(ConcreteTestSerializer):
            # Override properties to raise NotImplementedError (simulating abstract behavior)
            @property
            def output_format(self):
                raise NotImplementedError("Subclasses must define output_format")
            
            @property
            def file_extension(self):
                raise NotImplementedError("Subclasses must define file_extension")
            
            def serialize(self):
                raise NotImplementedError("Subclasses must implement serialize method")
        
        with patch.object(BadSerializer, '__init__', return_value=None):
            base = BadSerializer.__new__(BadSerializer)
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
        
        class CustomSerializer(BaseTestSerializerMixin, CustomSerializerBase):
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
    
    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_property_defaults(self, mock_super_init):
        """Test default property values."""
        mock_super_init.return_value = None
        
        serializer = ConcreteTestSerializer(doc=self.doc)
        
        # Test optional properties that return default values
        self.assertIsNone(serializer.format_description)
        self.assertEqual(serializer.version, "1.0.0")
        self.assertEqual(serializer.mimetype, "text/plain")
        
        # Test capabilities
        expected_capabilities = {
            "text_content": True,
            "document_structure": True,
            "metadata": False,
            "images": False,
            "tables": False,
            "formatting": False,
        }
        self.assertEqual(serializer.capabilities, expected_capabilities)
    
    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_serialize_text_content_with_nested_children(self, mock_super_init):
        """Test _serialize_text_content with deeply nested structure."""
        mock_super_init.return_value = None
        
        serializer = ConcreteTestSerializer(doc=self.doc)
        serializer.doc = self.doc  # Ensure doc is set
        
        # Create a more complex nested structure
        grandchild1 = Mock()
        grandchild1.text = "Grandchild 1"
        grandchild1.children = []
        
        grandchild2 = Mock()
        grandchild2.text = "Grandchild 2"
        grandchild2.children = []
        
        child1 = Mock()
        child1.text = "Child 1"
        child1.children = [grandchild1]
        
        child2 = Mock()
        child2.text = "Child 2"
        child2.children = [grandchild2]
        
        self.doc.body.text = "Root"
        self.doc.body.children = [child1, child2]
        
        text = serializer._serialize_text_content()
        expected = "Root\nChild 1\nGrandchild 1\nChild 2\nGrandchild 2"
        self.assertEqual(text, expected)
    
    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_serialize_with_structure_no_furniture(self, mock_super_init):
        """Test _serialize_with_structure without furniture."""
        mock_super_init.return_value = None
        
        serializer = ConcreteTestSerializer(doc=self.doc)
        serializer.doc = self.doc  # Ensure doc is set
        
        # Remove furniture attribute
        del self.doc.furniture
        
        body_item = Mock()
        body_item.text = "Body text"
        body_item.label = "paragraph"
        body_item.children = []
        
        self.doc.body = body_item
        
        result = serializer._serialize_with_structure()
        
        self.assertIn("metadata", result)
        self.assertIn("content", result)
        self.assertIn("body", result["content"])
        self.assertNotIn("furniture", result["content"])
    
    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_item_to_dict_with_none_values(self, mock_super_init):
        """Test _item_to_dict with None text and label."""
        mock_super_init.return_value = None
        
        serializer = ConcreteTestSerializer(doc=self.doc)
        
        item = Mock()
        item.text = None
        item.label = None
        item.children = []
        
        result = serializer._item_to_dict(item)
        self.assertEqual(result, {})
    
    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_custom_params_subclass(self, mock_super_init):
        """Test using a custom params subclass."""
        mock_super_init.return_value = None
        
        class MyParams(CustomSerializerParams):
            def __init__(self, indent=2, include_metadata=True):
                super().__init__()
                self.indent = indent
                self.include_metadata = include_metadata
        
        params = MyParams(indent=4, include_metadata=False)
        serializer = ConcreteTestSerializer(doc=self.doc, params=params)
        
        self.assertIsInstance(serializer.params, MyParams)
        self.assertEqual(serializer.params.indent, 4)
        self.assertEqual(serializer.params.include_metadata, False)
    
    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_component_serializers_usage(self, mock_super_init):
        """Test component serializers parameter."""
        mock_super_init.return_value = None
        
        table_serializer = Mock()
        image_serializer = Mock()
        
        component_serializers = {
            "table": table_serializer,
            "image": image_serializer,
        }
        
        serializer = ConcreteTestSerializer(
            doc=self.doc,
            component_serializers=component_serializers
        )
        
        self.assertEqual(serializer.component_serializers["table"], table_serializer)
        self.assertEqual(serializer.component_serializers["image"], image_serializer)
    
    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_validate_document_with_custom_doc(self, mock_super_init):
        """Test validate_document with various document types."""
        mock_super_init.return_value = None
        
        serializer = ConcreteTestSerializer(doc=self.doc)
        
        # Test with valid document
        valid_doc = Mock(spec=DoclingDocument)
        serializer.validate_document(valid_doc)  # Should not raise
        
        # Test with None - should raise
        with self.assertRaises(ValueError) as ctx:
            serializer.validate_document(None)
        self.assertIn("Document cannot be None", str(ctx.exception))
    
    @patch('docpivot.io.serializers.custom_serializer_base.BaseDocSerializer.__init__')
    def test_serialize_text_content_with_items_without_text(self, mock_super_init):
        """Test _serialize_text_content when items don't have text attribute."""
        mock_super_init.return_value = None
        
        serializer = ConcreteTestSerializer(doc=self.doc)
        serializer.doc = self.doc  # Ensure doc is set
        
        # Create items without text attribute
        child1 = Mock(spec=["children"])
        child1.children = []
        
        child2 = Mock()
        child2.text = "Has text"
        child2.children = []
        
        self.doc.body.text = "Root"
        self.doc.body.children = [child1, child2]
        
        text = serializer._serialize_text_content()
        self.assertEqual(text, "Root\nHas text")


if __name__ == "__main__":
    unittest.main()