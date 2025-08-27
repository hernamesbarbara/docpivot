"""Comprehensive tests for the extensibility module."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from docling_core.transforms.serializer.common import BaseDocSerializer, SerializationResult
from docling_core.types import DoclingDocument

from docpivot.extensibility import (
    ExtensibilityManager,
    get_extensibility_manager,
    register_format,
    load_plugin,
    discover_formats,
    list_supported_formats,
    validate_implementation,
)
from docpivot.io.readers.basereader import BaseReader
from docpivot.io.plugins import FormatPlugin, PluginLoadError


class TestReader(BaseReader):
    """Test reader for extensibility testing."""
    
    def detect_format(self, file_path):
        return str(file_path).endswith('.test')
    
    def load_data(self, file_path):
        return Mock(spec=DoclingDocument)


class TestSerializer(BaseDocSerializer):
    """Test serializer for extensibility testing."""
    
    def __init__(self, doc=None, **kwargs):
        """Initialize with optional doc parameter."""
        if doc is not None:
            super().__init__(doc, **kwargs)
    
    def serialize(self, **kwargs):
        return SerializationResult(text="test output")


class TestPlugin(FormatPlugin):
    """Test plugin for extensibility testing."""
    
    @property
    def name(self):
        return "test-plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    def get_readers(self):
        return {"test": TestReader}
    
    def get_serializers(self):
        return {"test": TestSerializer}


class TestExtensibilityManager(unittest.TestCase):
    """Test the ExtensibilityManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.manager = ExtensibilityManager()
    
    def test_initialization(self):
        """Test ExtensibilityManager initialization."""
        manager = ExtensibilityManager()
        self.assertIsNotNone(manager._format_registry)
        self.assertIsNotNone(manager._plugin_manager)
        self.assertIsNotNone(manager._validator)
    
    def test_register_reader_with_validation(self):
        """Test registering a reader with validation."""
        with patch.object(self.manager._validator, 'validate_reader') as mock_validate:
            mock_result = Mock()
            mock_result.is_valid = True
            mock_validate.return_value = mock_result
            
            self.manager.register_reader("test", TestReader, validate=True)
            
            # Verify reader registration was called
            mock_validate.assert_called_once_with(TestReader)
    
    def test_register_reader_without_validation(self):
        """Test registering a reader without validation."""
        self.manager.register_reader("test2", TestReader, validate=False)
        
        # Verify reader was registered
        formats = self.manager.discover_formats()
        self.assertIn("test2", formats)
    
    def test_register_reader_validation_failure(self):
        """Test registering a reader with validation failure."""
        # Create an invalid reader class
        class InvalidReader:
            pass
        
        with patch.object(self.manager._validator, 'validate_reader') as mock_validate:
            mock_result = Mock()
            mock_result.is_valid = False
            mock_result.__str__ = Mock(return_value="Validation failed")
            mock_validate.return_value = mock_result
            
            with self.assertRaises(ValueError) as ctx:
                self.manager.register_reader("invalid", InvalidReader, validate=True)
            
            self.assertIn("Reader validation failed", str(ctx.exception))
    
    def test_register_serializer_with_validation(self):
        """Test registering a serializer with validation."""
        with patch.object(self.manager._validator, 'validate_serializer') as mock_validate:
            mock_result = Mock()
            mock_result.is_valid = True
            mock_validate.return_value = mock_result
            
            self.manager.register_serializer("test", TestSerializer, validate=True)
            
            # Verify serializer validation was called
            mock_validate.assert_called_once_with(TestSerializer)
    
    def test_register_serializer_without_validation(self):
        """Test registering a serializer without validation."""
        self.manager.register_serializer("test2", TestSerializer, validate=False)
        
        # Verify serializer was registered
        formats = self.manager.discover_formats()
        self.assertIn("test2", formats)
    
    def test_register_serializer_validation_failure(self):
        """Test registering a serializer with validation failure."""
        # Create an invalid serializer class
        class InvalidSerializer:
            pass
        
        with patch.object(self.manager._validator, 'validate_serializer') as mock_validate:
            mock_result = Mock()
            mock_result.is_valid = False
            mock_result.__str__ = Mock(return_value="Validation failed")
            mock_validate.return_value = mock_result
            
            with self.assertRaises(ValueError) as ctx:
                self.manager.register_serializer("invalid", InvalidSerializer, validate=True)
            
            self.assertIn("Serializer validation failed", str(ctx.exception))
    
    def test_register_format_with_both(self):
        """Test registering a format with both reader and serializer."""
        with patch.object(self.manager._validator, 'validate_reader') as mock_val_reader:
            with patch.object(self.manager._validator, 'validate_serializer') as mock_val_serializer:
                mock_result = Mock()
                mock_result.is_valid = True
                mock_val_reader.return_value = mock_result
                mock_val_serializer.return_value = mock_result
                
                self.manager.register_format("test", TestReader, TestSerializer, validate=True)
                
                # Verify both validations were called
                mock_val_reader.assert_called_once_with(TestReader)
                mock_val_serializer.assert_called_once_with(TestSerializer)
    
    def test_register_format_with_reader_only(self):
        """Test registering a format with only a reader."""
        self.manager.register_format("test3", reader_class=TestReader, validate=False)
        
        # Verify reader was registered
        formats = self.manager.discover_formats()
        self.assertIn("test3", formats)
    
    def test_register_format_with_serializer_only(self):
        """Test registering a format with only a serializer."""
        self.manager.register_format("test4", serializer_class=TestSerializer, validate=False)
        
        # Verify serializer was registered
        formats = self.manager.discover_formats()
        self.assertIn("test4", formats)
    
    def test_load_plugin_instance(self):
        """Test loading a plugin instance."""
        # Clear any existing plugins first
        self.manager._plugin_manager.clear_plugins()
        
        plugin = TestPlugin()
        self.manager.load_plugin(plugin)
        
        # Verify plugin was loaded
        plugins = self.manager.list_plugins()
        self.assertIn("test-plugin", plugins)
    
    def test_load_plugin_class(self):
        """Test loading a plugin class."""
        self.manager.load_plugin(TestPlugin)
        
        # Verify plugin was loaded
        plugins = self.manager.list_plugins()
        self.assertIn("test-plugin", plugins)
    
    def test_load_plugin_module(self):
        """Test loading a plugin from module name."""
        with patch.object(self.manager._plugin_manager, 'load_plugin_from_module') as mock_load:
            self.manager.load_plugin("test.module")
            mock_load.assert_called_once_with("test.module")
    
    def test_load_plugin_file(self):
        """Test loading a plugin from file path."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            with patch.object(self.manager._plugin_manager, 'load_plugin_from_file') as mock_load:
                self.manager.load_plugin(temp_path)
                mock_load.assert_called_once_with(temp_path)
        finally:
            temp_path.unlink()
    
    def test_load_plugin_file_string_path(self):
        """Test loading a plugin from string file path."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_path = f.name
        
        try:
            # Check if path exists to determine which method to call
            self.assertTrue(Path(temp_path).exists())
            
            with patch.object(self.manager._plugin_manager, 'load_plugin_from_file') as mock_load:
                self.manager.load_plugin(temp_path)
                mock_load.assert_called_once_with(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_load_plugin_invalid_type(self):
        """Test loading plugin with invalid type."""
        with self.assertRaises(ValueError) as ctx:
            self.manager.load_plugin(123)
        
        self.assertIn("Invalid plugin type", str(ctx.exception))
    
    def test_load_plugins_from_directory(self):
        """Test loading plugins from directory."""
        with patch.object(self.manager._plugin_manager, 'load_plugins_from_directory') as mock_load:
            mock_load.return_value = ["plugin1", "plugin2"]
            
            result = self.manager.load_plugins_from_directory("/test/dir")
            
            self.assertEqual(result, ["plugin1", "plugin2"])
            mock_load.assert_called_once_with("/test/dir")
    
    def test_unload_plugin(self):
        """Test unloading a plugin."""
        with patch.object(self.manager._plugin_manager, 'unregister_plugin') as mock_unregister:
            mock_unregister.return_value = True
            
            result = self.manager.unload_plugin("test-plugin")
            
            self.assertTrue(result)
            mock_unregister.assert_called_once_with("test-plugin")
    
    def test_list_plugins(self):
        """Test listing plugins."""
        with patch.object(self.manager._plugin_manager, 'list_plugins') as mock_list:
            mock_list.return_value = ["plugin1", "plugin2"]
            
            result = self.manager.list_plugins()
            
            self.assertEqual(result, ["plugin1", "plugin2"])
    
    def test_get_plugin_info(self):
        """Test getting plugin info."""
        with patch.object(self.manager._plugin_manager, 'get_plugin_metadata') as mock_get:
            mock_get.return_value = {"name": "test", "version": "1.0"}
            
            result = self.manager.get_plugin_info("test")
            
            self.assertEqual(result, {"name": "test", "version": "1.0"})
    
    def test_discover_formats(self):
        """Test discovering formats."""
        with patch.object(self.manager._format_registry, 'discover_formats') as mock_discover:
            mock_discover.return_value = {"format1": {}, "format2": {}}
            
            result = self.manager.discover_formats()
            
            self.assertEqual(result, {"format1": {}, "format2": {}})
    
    def test_list_readable_formats(self):
        """Test listing readable formats."""
        with patch.object(self.manager._format_registry, 'list_readable_formats') as mock_list:
            mock_list.return_value = ["format1", "format2"]
            
            result = self.manager.list_readable_formats()
            
            self.assertEqual(result, ["format1", "format2"])
    
    def test_list_writable_formats(self):
        """Test listing writable formats."""
        with patch.object(self.manager._format_registry, 'list_writable_formats') as mock_list:
            mock_list.return_value = ["format1", "format2"]
            
            result = self.manager.list_writable_formats()
            
            self.assertEqual(result, ["format1", "format2"])
    
    def test_is_format_supported(self):
        """Test checking if format is supported."""
        with patch.object(self.manager._format_registry, 'is_format_supported') as mock_check:
            mock_check.return_value = True
            
            result = self.manager.is_format_supported("test")
            
            self.assertTrue(result)
    
    def test_can_read_format(self):
        """Test checking if format can be read."""
        with patch.object(self.manager._format_registry, 'can_read_format') as mock_check:
            mock_check.return_value = True
            
            result = self.manager.can_read_format("test")
            
            self.assertTrue(result)
    
    def test_can_write_format(self):
        """Test checking if format can be written."""
        with patch.object(self.manager._format_registry, 'can_write_format') as mock_check:
            mock_check.return_value = True
            
            result = self.manager.can_write_format("test")
            
            self.assertTrue(result)
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        with patch.object(self.manager._format_registry, 'get_supported_extensions') as mock_get:
            mock_get.return_value = [".txt", ".doc"]
            
            result = self.manager.get_supported_extensions()
            
            self.assertEqual(result, [".txt", ".doc"])
    
    def test_get_reader_for_file(self):
        """Test getting reader for file."""
        with patch.object(self.manager._format_registry, 'get_reader_for_file') as mock_get:
            mock_reader = Mock()
            mock_get.return_value = mock_reader
            
            result = self.manager.get_reader_for_file("/test/file.txt")
            
            self.assertEqual(result, mock_reader)
    
    def test_get_serializer_success(self):
        """Test getting serializer successfully."""
        from docpivot.io.serializers.serializerprovider import SerializerProvider
        
        with patch.object(SerializerProvider, 'get_serializer') as mock_get:
            mock_serializer = Mock()
            mock_get.return_value = mock_serializer
            
            doc = Mock(spec=DoclingDocument)
            result = self.manager.get_serializer("test", doc)
            
            self.assertEqual(result, mock_serializer)
    
    def test_get_serializer_not_found(self):
        """Test getting serializer when not found."""
        from docpivot.io.serializers.serializerprovider import SerializerProvider
        
        with patch.object(SerializerProvider, 'get_serializer') as mock_get:
            mock_get.side_effect = ValueError("Not found")
            
            doc = Mock(spec=DoclingDocument)
            result = self.manager.get_serializer("test", doc)
            
            self.assertIsNone(result)
    
    def test_validate_reader(self):
        """Test validating reader."""
        with patch.object(self.manager._validator, 'validate_reader') as mock_validate:
            mock_result = Mock()
            mock_result.is_valid = True
            mock_result.issues = []
            mock_result.tested_features = ["feature1", "feature2"]
            mock_validate.return_value = mock_result
            
            result = self.manager.validate_reader(TestReader)
            
            self.assertEqual(result["is_valid"], True)
            self.assertEqual(result["issues"], [])
            self.assertEqual(result["tested_features"], ["feature1", "feature2"])
    
    def test_validate_serializer(self):
        """Test validating serializer."""
        with patch.object(self.manager._validator, 'validate_serializer') as mock_validate:
            mock_result = Mock()
            mock_result.is_valid = True
            mock_result.issues = []
            mock_result.tested_features = ["feature1", "feature2"]
            mock_validate.return_value = mock_result
            
            result = self.manager.validate_serializer(TestSerializer)
            
            self.assertEqual(result["is_valid"], True)
            self.assertEqual(result["issues"], [])
            self.assertEqual(result["tested_features"], ["feature1", "feature2"])
    
    def test_validate_format_pair(self):
        """Test validating format pair."""
        with patch.object(self.manager._validator, 'validate_format_pair') as mock_validate:
            mock_validate.return_value = {"result": "success"}
            
            result = self.manager.validate_format_pair(TestReader, TestSerializer)
            
            self.assertEqual(result, {"result": "success"})
    
    def test_get_format_info_found(self):
        """Test getting format info when found."""
        with patch.object(self.manager._format_registry, 'get_format_info') as mock_get:
            mock_info = Mock()
            mock_info.get_capabilities.return_value = {"capability": "value"}
            mock_get.return_value = mock_info
            
            result = self.manager.get_format_info("test")
            
            self.assertEqual(result, {"capability": "value"})
    
    def test_get_format_info_not_found(self):
        """Test getting format info when not found."""
        with patch.object(self.manager._format_registry, 'get_format_info') as mock_get:
            mock_get.return_value = None
            
            result = self.manager.get_format_info("test")
            
            self.assertIsNone(result)
    
    def test_unregister_format(self):
        """Test unregistering format."""
        with patch.object(self.manager._format_registry, 'unregister_format') as mock_unregister:
            mock_unregister.return_value = True
            
            result = self.manager.unregister_format("test")
            
            self.assertTrue(result)
    
    def test_clear_registry(self):
        """Test clearing registry."""
        with patch.object(self.manager._format_registry, 'clear_registry') as mock_clear:
            self.manager.clear_registry()
            
            mock_clear.assert_called_once()
    
    def test_reset_to_defaults(self):
        """Test resetting to defaults."""
        with patch.object(self.manager._format_registry, 'clear_registry') as mock_clear:
            with patch.object(self.manager._plugin_manager, 'clear_plugins') as mock_clear_plugins:
                with patch.object(self.manager._format_registry, '_register_builtin_formats') as mock_register:
                    self.manager.reset_to_defaults()
                    
                    mock_clear.assert_called_once()
                    mock_clear_plugins.assert_called_once()
                    mock_register.assert_called_once()


class TestGlobalFunctions(unittest.TestCase):
    """Test global functions in extensibility module."""
    
    def test_get_extensibility_manager_singleton(self):
        """Test that get_extensibility_manager returns singleton."""
        import docpivot.extensibility
        
        # Reset global manager
        docpivot.extensibility._global_extensibility_manager = None
        
        manager1 = get_extensibility_manager()
        manager2 = get_extensibility_manager()
        
        self.assertIs(manager1, manager2)
    
    def test_register_format_global(self):
        """Test global register_format function."""
        with patch('docpivot.extensibility.get_extensibility_manager') as mock_get:
            mock_manager = Mock()
            mock_get.return_value = mock_manager
            
            register_format("test", TestReader, TestSerializer, validate=False)
            
            mock_manager.register_format.assert_called_once_with(
                "test", TestReader, TestSerializer, False
            )
    
    def test_load_plugin_global(self):
        """Test global load_plugin function."""
        with patch('docpivot.extensibility.get_extensibility_manager') as mock_get:
            mock_manager = Mock()
            mock_get.return_value = mock_manager
            
            plugin = TestPlugin()
            load_plugin(plugin)
            
            mock_manager.load_plugin.assert_called_once_with(plugin)
    
    def test_discover_formats_global(self):
        """Test global discover_formats function."""
        with patch('docpivot.extensibility.get_extensibility_manager') as mock_get:
            mock_manager = Mock()
            mock_manager.discover_formats.return_value = {"format": {}}
            mock_get.return_value = mock_manager
            
            result = discover_formats()
            
            self.assertEqual(result, {"format": {}})
    
    def test_list_supported_formats_global(self):
        """Test global list_supported_formats function."""
        with patch('docpivot.extensibility.get_extensibility_manager') as mock_get:
            mock_manager = Mock()
            mock_manager.list_readable_formats.return_value = ["read1", "read2"]
            mock_manager.list_writable_formats.return_value = ["write1", "write2"]
            mock_get.return_value = mock_manager
            
            result = list_supported_formats()
            
            self.assertEqual(result, {
                "readable": ["read1", "read2"],
                "writable": ["write1", "write2"]
            })
    
    def test_validate_implementation_reader_only(self):
        """Test global validate_implementation with reader only."""
        with patch('docpivot.extensibility.get_extensibility_manager') as mock_get:
            mock_manager = Mock()
            mock_manager.validate_reader.return_value = {"valid": True}
            mock_get.return_value = mock_manager
            
            result = validate_implementation(reader_class=TestReader)
            
            self.assertEqual(result, {"reader": {"valid": True}})
            mock_manager.validate_reader.assert_called_once_with(TestReader)
    
    def test_validate_implementation_serializer_only(self):
        """Test global validate_implementation with serializer only."""
        with patch('docpivot.extensibility.get_extensibility_manager') as mock_get:
            mock_manager = Mock()
            mock_manager.validate_serializer.return_value = {"valid": True}
            mock_get.return_value = mock_manager
            
            result = validate_implementation(serializer_class=TestSerializer)
            
            self.assertEqual(result, {"serializer": {"valid": True}})
            mock_manager.validate_serializer.assert_called_once_with(TestSerializer)
    
    def test_validate_implementation_both(self):
        """Test global validate_implementation with both reader and serializer."""
        with patch('docpivot.extensibility.get_extensibility_manager') as mock_get:
            mock_manager = Mock()
            mock_manager.validate_reader.return_value = {"valid": True}
            mock_manager.validate_serializer.return_value = {"valid": True}
            mock_manager.validate_format_pair.return_value = {"compatible": True}
            mock_get.return_value = mock_manager
            
            result = validate_implementation(reader_class=TestReader, serializer_class=TestSerializer)
            
            self.assertEqual(result, {
                "reader": {"valid": True},
                "serializer": {"valid": True},
                "compatibility": {"compatible": True}
            })
            mock_manager.validate_reader.assert_called_once_with(TestReader)
            mock_manager.validate_serializer.assert_called_once_with(TestSerializer)
            mock_manager.validate_format_pair.assert_called_once_with(TestReader, TestSerializer)
    
    def test_validate_implementation_empty(self):
        """Test global validate_implementation with no arguments."""
        with patch('docpivot.extensibility.get_extensibility_manager') as mock_get:
            mock_manager = Mock()
            mock_get.return_value = mock_manager
            
            result = validate_implementation()
            
            self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()