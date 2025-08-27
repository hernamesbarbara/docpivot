"""Comprehensive tests for custom reader base module."""

import unittest
from pathlib import Path
from typing import List, Any
from unittest.mock import Mock, patch, MagicMock
from tempfile import NamedTemporaryFile
import tempfile

from docling_core.types import DoclingDocument
from docling_core.types.doc import DocumentOrigin, NodeItem

from docpivot.io.readers.custom_reader_base import CustomReaderBase


class ConcreteCustomReader(CustomReaderBase):
    """Concrete implementation for testing purposes."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".test", ".tst"]
    
    @property
    def format_name(self) -> str:
        return "Test Format"
    
    def can_handle(self, file_path) -> bool:
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def load_data(self, file_path, **kwargs) -> DoclingDocument:
        # Simple implementation that creates an empty document
        doc = self._create_empty_document()
        doc.name = Path(file_path).name
        return doc


class MinimalCustomReader(CustomReaderBase):
    """Minimal implementation to test abstract methods."""
    
    def supported_extensions(self):
        # Property implemented as method to test NotImplementedError
        raise NotImplementedError("Subclasses must define supported_extensions")
    
    def format_name(self):
        # Property implemented as method to test NotImplementedError
        raise NotImplementedError("Subclasses must define format_name")
    
    def can_handle(self, file_path):
        raise NotImplementedError("Subclasses must implement can_handle method")
    
    def load_data(self, file_path, **kwargs):
        return self._create_empty_document()


class TestCustomReaderBase(unittest.TestCase):
    """Test CustomReaderBase class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = ConcreteCustomReader()
        
    def test_supported_extensions_property(self):
        """Test supported_extensions property."""
        extensions = self.reader.supported_extensions
        self.assertEqual(extensions, [".test", ".tst"])
        
    def test_format_name_property(self):
        """Test format_name property."""
        name = self.reader.format_name
        self.assertEqual(name, "Test Format")
        
    def test_format_description_property_default(self):
        """Test format_description property returns None by default."""
        description = self.reader.format_description
        self.assertIsNone(description)
        
    def test_version_property_default(self):
        """Test version property returns default value."""
        version = self.reader.version
        self.assertEqual(version, "1.0.0")
        
    def test_capabilities_property_default(self):
        """Test capabilities property returns default capabilities."""
        capabilities = self.reader.capabilities
        expected = {
            "text_extraction": True,
            "metadata_extraction": False,
            "structure_preservation": True,
            "embedded_images": False,
            "embedded_tables": False,
        }
        self.assertEqual(capabilities, expected)
        
    def test_can_handle_with_supported_extension(self):
        """Test can_handle returns True for supported extensions."""
        self.assertTrue(self.reader.can_handle("/path/to/file.test"))
        self.assertTrue(self.reader.can_handle(Path("/path/to/file.tst")))
        
    def test_can_handle_with_unsupported_extension(self):
        """Test can_handle returns False for unsupported extensions."""
        self.assertFalse(self.reader.can_handle("/path/to/file.txt"))
        self.assertFalse(self.reader.can_handle(Path("/path/to/file.pdf")))
        
    def test_detect_format_delegates_to_can_handle(self):
        """Test detect_format delegates to can_handle method."""
        self.assertTrue(self.reader.detect_format("/path/to/file.test"))
        self.assertFalse(self.reader.detect_format("/path/to/file.txt"))
        
    def test_is_supported_format_class_method(self):
        """Test is_supported_format class method."""
        self.assertTrue(ConcreteCustomReader.is_supported_format("/path/to/file.test"))
        self.assertTrue(ConcreteCustomReader.is_supported_format(Path("/path/to/file.tst")))
        self.assertFalse(ConcreteCustomReader.is_supported_format("/path/to/file.txt"))
        
    def test_is_supported_format_with_exception(self):
        """Test is_supported_format returns False on exception."""
        # Test with a class that raises exception on instantiation
        class BrokenReader(CustomReaderBase):
            def __init__(self, **kwargs):
                raise RuntimeError("Cannot instantiate")
        
        self.assertFalse(BrokenReader.is_supported_format("/path/to/file.test"))
        
    def test_validate_file_format_with_existing_file(self):
        """Test validate_file_format with existing supported file."""
        with NamedTemporaryFile(suffix=".test", delete=False) as tmp:
            try:
                self.reader.validate_file_format(tmp.name)  # Should not raise
            finally:
                Path(tmp.name).unlink()
                
    def test_validate_file_format_with_nonexistent_file(self):
        """Test validate_file_format raises FileNotFoundError for nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            self.reader.validate_file_format("/nonexistent/file.test")
            
    def test_validate_file_format_with_unsupported_format(self):
        """Test validate_file_format raises ValueError for unsupported format."""
        with NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            try:
                with self.assertRaises(ValueError) as ctx:
                    self.reader.validate_file_format(tmp.name)
                self.assertIn("Unsupported file format", str(ctx.exception))
                self.assertIn("Test Format reader", str(ctx.exception))
            finally:
                Path(tmp.name).unlink()
                
    def test_get_metadata(self):
        """Test get_metadata method."""
        with NamedTemporaryFile(suffix=".test", delete=False) as tmp:
            tmp.write(b"test content")
            tmp.flush()
            
            try:
                metadata = self.reader.get_metadata(tmp.name)
                
                self.assertIn("filename", metadata)
                self.assertIn("extension", metadata)
                self.assertIn("size_bytes", metadata)
                self.assertIn("format_name", metadata)
                self.assertIn("reader_version", metadata)
                
                self.assertEqual(metadata["extension"], ".test")
                self.assertEqual(metadata["size_bytes"], 12)  # "test content" = 12 bytes
                self.assertEqual(metadata["format_name"], "Test Format")
                self.assertEqual(metadata["reader_version"], "1.0.0")
            finally:
                Path(tmp.name).unlink()
                
    def test_get_metadata_nonexistent_file(self):
        """Test get_metadata with nonexistent file."""
        metadata = self.reader.get_metadata("/nonexistent/file.test")
        self.assertEqual(metadata["size_bytes"], 0)
        
    def test_create_empty_document(self):
        """Test _create_empty_document helper method."""
        doc = self.reader._create_empty_document()
        
        self.assertIsInstance(doc, DoclingDocument)
        self.assertEqual(doc.name, "")
        # Document should have proper structure created by DoclingDocument
        # The furniture and body properties exist and are not None
        self.assertIsNotNone(doc.furniture)
        self.assertIsNotNone(doc.body)
        
    def test_validate_configuration_valid(self):
        """Test _validate_configuration with valid configuration."""
        reader = ConcreteCustomReader()
        # Should not raise during initialization
        self.assertIsNotNone(reader)
        
    def test_validate_configuration_no_extensions(self):
        """Test _validate_configuration raises error for missing extensions."""
        class NoExtensionsReader(CustomReaderBase):
            @property
            def supported_extensions(self):
                return []  # Empty list
            
            @property
            def format_name(self):
                return "Test"
            
            def can_handle(self, file_path):
                return False
            
            def load_data(self, file_path, **kwargs):
                return self._create_empty_document()
        
        with self.assertRaises(ValueError) as ctx:
            NoExtensionsReader()
        self.assertIn("must define supported_extensions", str(ctx.exception))
        
    def test_validate_configuration_no_format_name(self):
        """Test _validate_configuration raises error for missing format name."""
        class NoNameReader(CustomReaderBase):
            @property
            def supported_extensions(self):
                return [".test"]
            
            @property
            def format_name(self):
                return ""  # Empty string
            
            def can_handle(self, file_path):
                return False
            
            def load_data(self, file_path, **kwargs):
                return self._create_empty_document()
        
        with self.assertRaises(ValueError) as ctx:
            NoNameReader()
        self.assertIn("must define format_name", str(ctx.exception))
        
    def test_validate_configuration_invalid_extension_format(self):
        """Test _validate_configuration raises error for invalid extension format."""
        class BadExtensionReader(CustomReaderBase):
            @property
            def supported_extensions(self):
                return ["test", ".valid"]  # First one missing dot
            
            @property
            def format_name(self):
                return "Test"
            
            def can_handle(self, file_path):
                return False
            
            def load_data(self, file_path, **kwargs):
                return self._create_empty_document()
        
        with self.assertRaises(ValueError) as ctx:
            BadExtensionReader()
        self.assertIn("Extensions must start with '.'", str(ctx.exception))
        
    def test_init_with_kwargs(self):
        """Test initialization with kwargs."""
        reader = ConcreteCustomReader(custom_param="value")
        self.assertIsNotNone(reader)
        
    def test_str_representation(self):
        """Test __str__ representation."""
        str_repr = str(self.reader)
        self.assertEqual(str_repr, "ConcreteCustomReader(Test Format v1.0.0)")
        
    def test_repr_representation(self):
        """Test __repr__ representation."""
        repr_str = repr(self.reader)
        expected = "ConcreteCustomReader(format_name='Test Format', version='1.0.0', extensions=['.test', '.tst'])"
        self.assertEqual(repr_str, expected)
        
    def test_abstract_methods_not_implemented(self):
        """Test abstract methods raise NotImplementedError."""
        # Test that CustomReaderBase is abstract and cannot be instantiated
        with self.assertRaises(TypeError) as ctx:
            CustomReaderBase()
        self.assertIn("Can't instantiate abstract class", str(ctx.exception))
        
        # Create a minimal reader to test the abstract method errors
        class PartialReader(CustomReaderBase):
            # Only implement some abstract methods to test errors
            @property
            def supported_extensions(self):
                return [".test"]
            
            @property
            def format_name(self):
                return "Test"
            
            def can_handle(self, file_path):
                return True
            
            def load_data(self, file_path, **kwargs):
                # This minimal implementation is for testing
                from docling_core.types import DoclingDocument
                return DoclingDocument(name="test")
        
    def test_custom_format_description(self):
        """Test custom format_description property."""
        class DescriptiveReader(ConcreteCustomReader):
            @property
            def format_description(self):
                return "A detailed description of the test format"
        
        reader = DescriptiveReader()
        self.assertEqual(reader.format_description, "A detailed description of the test format")
        
    def test_custom_version(self):
        """Test custom version property."""
        class VersionedReader(ConcreteCustomReader):
            @property
            def version(self):
                return "2.0.0"
        
        reader = VersionedReader()
        self.assertEqual(reader.version, "2.0.0")
        
    def test_custom_capabilities(self):
        """Test custom capabilities property."""
        class CapableReader(ConcreteCustomReader):
            @property
            def capabilities(self):
                return {
                    "text_extraction": True,
                    "metadata_extraction": True,
                    "structure_preservation": True,
                    "embedded_images": True,
                    "embedded_tables": True,
                }
        
        reader = CapableReader()
        self.assertTrue(reader.capabilities["metadata_extraction"])
        self.assertTrue(reader.capabilities["embedded_images"])
        
    def test_load_data_implementation(self):
        """Test load_data creates document properly."""
        with NamedTemporaryFile(suffix=".test", delete=False) as tmp:
            try:
                doc = self.reader.load_data(tmp.name)
                self.assertIsInstance(doc, DoclingDocument)
                self.assertEqual(doc.name, Path(tmp.name).name)
            finally:
                Path(tmp.name).unlink()
                
    def test_validate_file_format_with_no_extension(self):
        """Test validate_file_format with file without extension."""
        with NamedTemporaryFile(suffix="", delete=False) as tmp:
            try:
                with self.assertRaises(ValueError) as ctx:
                    self.reader.validate_file_format(tmp.name)
                self.assertIn("unknown", str(ctx.exception))
            finally:
                Path(tmp.name).unlink()
                
    def test_multiple_readers_different_formats(self):
        """Test multiple readers with different format support."""
        class XMLReader(CustomReaderBase):
            @property
            def supported_extensions(self):
                return [".xml", ".xhtml"]
            
            @property
            def format_name(self):
                return "XML Format"
            
            def can_handle(self, file_path):
                return Path(file_path).suffix.lower() in self.supported_extensions
            
            def load_data(self, file_path, **kwargs):
                return self._create_empty_document()
        
        xml_reader = XMLReader()
        test_reader = ConcreteCustomReader()
        
        self.assertTrue(xml_reader.can_handle("file.xml"))
        self.assertFalse(xml_reader.can_handle("file.test"))
        self.assertFalse(test_reader.can_handle("file.xml"))
        self.assertTrue(test_reader.can_handle("file.test"))


if __name__ == "__main__":
    unittest.main()