"""Comprehensive tests for the plugin system."""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Type
from unittest.mock import Mock, patch, MagicMock

from docling_core.transforms.serializer.common import BaseDocSerializer, SerializationResult
from docling_core.types import DoclingDocument

from docpivot.io.plugins import FormatPlugin, PluginManager, PluginLoadError, get_plugin_manager
from docpivot.io.readers.basereader import BaseReader
from docpivot.io.format_registry import FormatRegistry


class TestReaderPlugin(BaseReader):
    """Test reader for plugin testing."""
    
    def detect_format(self, file_path):
        return str(file_path).endswith('.test')
    
    def load_data(self, file_path):
        return Mock(spec=DoclingDocument)


class TestSerializerPlugin(BaseDocSerializer):
    """Test serializer for plugin testing."""
    
    def serialize(self, **kwargs):
        return SerializationResult(text="test output")


class TestFormatPlugin(FormatPlugin):
    """Test implementation of FormatPlugin."""
    
    @property
    def name(self):
        return "test-plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    @property
    def description(self):
        return "Test plugin for unit testing"
    
    @property
    def author(self):
        return "Test Author"
    
    @property
    def homepage(self):
        return "https://example.com/test-plugin"
    
    def get_readers(self):
        return {"test": TestReaderPlugin}
    
    def get_serializers(self):
        return {"test": TestSerializerPlugin}


class TestFormatPluginBase(unittest.TestCase):
    """Test the FormatPlugin base class."""
    
    def test_abstract_plugin_cannot_be_instantiated(self):
        """Test that abstract FormatPlugin cannot be instantiated."""
        with self.assertRaises(TypeError):
            FormatPlugin()
    
    def test_plugin_with_required_properties(self):
        """Test plugin with required properties implemented."""
        plugin = TestFormatPlugin()
        
        self.assertEqual(plugin.name, "test-plugin")
        self.assertEqual(plugin.version, "1.0.0")
        self.assertEqual(plugin.description, "Test plugin for unit testing")
        self.assertEqual(plugin.author, "Test Author")
        self.assertEqual(plugin.homepage, "https://example.com/test-plugin")
    
    def test_plugin_string_representations(self):
        """Test __str__ and __repr__ methods."""
        plugin = TestFormatPlugin()
        
        self.assertEqual(str(plugin), "test-plugin v1.0.0")
        self.assertEqual(repr(plugin), "FormatPlugin(name='test-plugin', version='1.0.0')")
    
    def test_plugin_get_metadata(self):
        """Test get_metadata method."""
        plugin = TestFormatPlugin()
        metadata = plugin.get_metadata()
        
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata["name"], "test-plugin")
        self.assertEqual(metadata["version"], "1.0.0")
        self.assertEqual(metadata["description"], "Test plugin for unit testing")
        self.assertEqual(metadata["author"], "Test Author")
        self.assertEqual(metadata["homepage"], "https://example.com/test-plugin")
        self.assertEqual(metadata["readers"], ["test"])
        self.assertEqual(metadata["serializers"], ["test"])
    
    def test_plugin_initialize_and_cleanup(self):
        """Test initialize and cleanup methods."""
        plugin = TestFormatPlugin()
        
        # These should not raise
        plugin.initialize()
        plugin.cleanup()
    
    def test_minimal_plugin_implementation(self):
        """Test minimal plugin implementation with only required properties."""
        
        class MinimalPlugin(FormatPlugin):
            @property
            def name(self):
                return "minimal"
            
            @property
            def version(self):
                return "0.1.0"
        
        plugin = MinimalPlugin()
        
        self.assertEqual(plugin.name, "minimal")
        self.assertEqual(plugin.version, "0.1.0")
        self.assertIsNone(plugin.description)
        self.assertIsNone(plugin.author)
        self.assertIsNone(plugin.homepage)
        self.assertEqual(plugin.get_readers(), {})
        self.assertEqual(plugin.get_serializers(), {})
    
    def test_plugin_with_custom_initialization(self):
        """Test plugin with custom initialization logic."""
        
        class InitPlugin(FormatPlugin):
            @property
            def name(self):
                return "init-plugin"
            
            @property
            def version(self):
                return "1.0.0"
            
            def initialize(self):
                self.initialized = True
            
            def cleanup(self):
                self.cleaned = True
        
        plugin = InitPlugin()
        
        self.assertFalse(hasattr(plugin, 'initialized'))
        plugin.initialize()
        self.assertTrue(plugin.initialized)
        
        self.assertFalse(hasattr(plugin, 'cleaned'))
        plugin.cleanup()
        self.assertTrue(plugin.cleaned)


class TestPluginLoadError(unittest.TestCase):
    """Test the PluginLoadError exception."""
    
    def test_plugin_load_error_basic(self):
        """Test basic PluginLoadError creation."""
        error = PluginLoadError("test/path.py", "Test error message")
        
        self.assertEqual(error.plugin_path, "test/path.py")
        self.assertEqual(str(error), "Test error message")
        self.assertIsNone(error.original_error)
    
    def test_plugin_load_error_with_original(self):
        """Test PluginLoadError with original exception."""
        original = ValueError("Original error")
        error = PluginLoadError("test/path.py", "Wrapped error", original)
        
        self.assertEqual(error.plugin_path, "test/path.py")
        self.assertEqual(str(error), "Wrapped error")
        self.assertIs(error.original_error, original)


class TestPluginManager(unittest.TestCase):
    """Test the PluginManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.registry = FormatRegistry()
        self.manager = PluginManager(registry=self.registry)
    
    def test_initialization(self):
        """Test PluginManager initialization."""
        self.assertIs(self.manager.registry, self.registry)
        self.assertEqual(self.manager._plugins, {})
        self.assertEqual(self.manager._loaded_modules, {})
    
    def test_initialization_with_default_registry(self):
        """Test PluginManager initialization with default registry."""
        manager = PluginManager()
        self.assertIsNotNone(manager.registry)
    
    def test_register_plugin_success(self):
        """Test successful plugin registration."""
        plugin = TestFormatPlugin()
        self.manager.register_plugin(plugin)
        
        self.assertIn("test-plugin", self.manager._plugins)
        self.assertIs(self.manager._plugins["test-plugin"], plugin)
    
    def test_register_plugin_invalid_type(self):
        """Test registering invalid plugin type."""
        with self.assertRaises(TypeError) as ctx:
            self.manager.register_plugin("not a plugin")
        
        self.assertIn("Plugin must be a FormatPlugin instance", str(ctx.exception))
    
    def test_register_plugin_duplicate_name(self):
        """Test registering duplicate plugin name."""
        plugin1 = TestFormatPlugin()
        plugin2 = TestFormatPlugin()
        
        self.manager.register_plugin(plugin1)
        
        with self.assertRaises(ValueError) as ctx:
            self.manager.register_plugin(plugin2)
        
        self.assertIn("Plugin 'test-plugin' is already registered", str(ctx.exception))
    
    def test_register_plugin_initialization_error(self):
        """Test plugin registration with initialization error."""
        
        class FailingPlugin(FormatPlugin):
            @property
            def name(self):
                return "failing"
            
            @property
            def version(self):
                return "1.0.0"
            
            def initialize(self):
                raise RuntimeError("Initialization failed")
        
        plugin = FailingPlugin()
        
        with self.assertRaises(PluginLoadError) as ctx:
            self.manager.register_plugin(plugin)
        
        self.assertIn("Failed to initialize plugin", str(ctx.exception))
        self.assertEqual(ctx.exception.plugin_path, "failing")
    
    def test_unregister_plugin_success(self):
        """Test successful plugin unregistration."""
        plugin = TestFormatPlugin()
        self.manager.register_plugin(plugin)
        
        result = self.manager.unregister_plugin("test-plugin")
        
        self.assertTrue(result)
        self.assertNotIn("test-plugin", self.manager._plugins)
    
    def test_unregister_plugin_not_found(self):
        """Test unregistering non-existent plugin."""
        result = self.manager.unregister_plugin("non-existent")
        self.assertFalse(result)
    
    def test_unregister_plugin_with_cleanup_error(self):
        """Test unregistering plugin with cleanup error."""
        
        class CleanupErrorPlugin(FormatPlugin):
            @property
            def name(self):
                return "cleanup-error"
            
            @property
            def version(self):
                return "1.0.0"
            
            def cleanup(self):
                raise RuntimeError("Cleanup failed")
        
        plugin = CleanupErrorPlugin()
        self.manager.register_plugin(plugin)
        
        # Should succeed despite cleanup error
        result = self.manager.unregister_plugin("cleanup-error")
        self.assertTrue(result)
        self.assertNotIn("cleanup-error", self.manager._plugins)
    
    def test_load_plugin_from_class(self):
        """Test loading plugin from class."""
        self.manager.load_plugin_from_class(TestFormatPlugin)
        
        self.assertIn("test-plugin", self.manager._plugins)
        plugin = self.manager._plugins["test-plugin"]
        self.assertIsInstance(plugin, TestFormatPlugin)
    
    def test_load_plugin_from_class_invalid(self):
        """Test loading plugin from invalid class."""
        
        class NotAPlugin:
            pass
        
        with self.assertRaises(PluginLoadError) as ctx:
            self.manager.load_plugin_from_class(NotAPlugin)
        
        self.assertIn("Plugin class must extend FormatPlugin", str(ctx.exception))
    
    def test_load_plugin_from_class_instantiation_error(self):
        """Test loading plugin from class that fails to instantiate."""
        
        class FailingConstructorPlugin(FormatPlugin):
            def __init__(self):
                raise RuntimeError("Cannot instantiate")
            
            @property
            def name(self):
                return "failing"
            
            @property
            def version(self):
                return "1.0.0"
        
        with self.assertRaises(PluginLoadError) as ctx:
            self.manager.load_plugin_from_class(FailingConstructorPlugin)
        
        self.assertIn("Failed to instantiate plugin class", str(ctx.exception))
    
    def test_get_plugin(self):
        """Test getting a plugin by name."""
        plugin = TestFormatPlugin()
        self.manager.register_plugin(plugin)
        
        retrieved = self.manager.get_plugin("test-plugin")
        self.assertIs(retrieved, plugin)
        
        not_found = self.manager.get_plugin("non-existent")
        self.assertIsNone(not_found)
    
    def test_list_plugins(self):
        """Test listing all plugin names."""
        plugin1 = TestFormatPlugin()
        
        class AnotherPlugin(FormatPlugin):
            @property
            def name(self):
                return "another"
            
            @property
            def version(self):
                return "1.0.0"
        
        plugin2 = AnotherPlugin()
        
        self.manager.register_plugin(plugin1)
        self.manager.register_plugin(plugin2)
        
        plugins = self.manager.list_plugins()
        self.assertEqual(set(plugins), {"test-plugin", "another"})
    
    def test_get_plugin_metadata(self):
        """Test getting plugin metadata."""
        plugin = TestFormatPlugin()
        self.manager.register_plugin(plugin)
        
        metadata = self.manager.get_plugin_metadata("test-plugin")
        
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata["name"], "test-plugin")
        self.assertEqual(metadata["version"], "1.0.0")
        
        not_found = self.manager.get_plugin_metadata("non-existent")
        self.assertIsNone(not_found)
    
    def test_discover_plugins(self):
        """Test discovering all plugins."""
        plugin1 = TestFormatPlugin()
        
        class SimplePlugin(FormatPlugin):
            @property
            def name(self):
                return "simple"
            
            @property
            def version(self):
                return "0.1.0"
        
        plugin2 = SimplePlugin()
        
        self.manager.register_plugin(plugin1)
        self.manager.register_plugin(plugin2)
        
        discovery = self.manager.discover_plugins()
        
        self.assertIsInstance(discovery, dict)
        self.assertIn("test-plugin", discovery)
        self.assertIn("simple", discovery)
        self.assertEqual(discovery["test-plugin"]["version"], "1.0.0")
        self.assertEqual(discovery["simple"]["version"], "0.1.0")
    
    def test_clear_plugins(self):
        """Test clearing all plugins."""
        plugin1 = TestFormatPlugin()
        
        class SimplePlugin(FormatPlugin):
            @property
            def name(self):
                return "simple"
            
            @property
            def version(self):
                return "0.1.0"
        
        plugin2 = SimplePlugin()
        
        self.manager.register_plugin(plugin1)
        self.manager.register_plugin(plugin2)
        
        self.assertEqual(len(self.manager._plugins), 2)
        
        self.manager.clear_plugins()
        
        self.assertEqual(len(self.manager._plugins), 0)
    
    def test_load_plugin_from_module(self):
        """Test loading plugin from module."""
        # Create a mock module
        mock_module = MagicMock()
        mock_module.plugin = TestFormatPlugin()
        
        with patch('importlib.import_module', return_value=mock_module):
            self.manager.load_plugin_from_module("test.module")
        
        self.assertIn("test-plugin", self.manager._plugins)
        self.assertIn("test.module", self.manager._loaded_modules)
    
    def test_load_plugin_from_module_class(self):
        """Test loading plugin from module with class."""
        # Create a mock module
        mock_module = MagicMock()
        mock_module.plugin = TestFormatPlugin  # Class, not instance
        
        with patch('importlib.import_module', return_value=mock_module):
            self.manager.load_plugin_from_module("test.module")
        
        self.assertIn("test-plugin", self.manager._plugins)
        self.assertIsInstance(self.manager._plugins["test-plugin"], TestFormatPlugin)
    
    def test_load_plugin_from_module_import_error(self):
        """Test loading plugin from module with import error."""
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            with self.assertRaises(PluginLoadError) as ctx:
                self.manager.load_plugin_from_module("test.module")
            
            self.assertIn("Failed to import module", str(ctx.exception))
    
    def test_load_plugin_from_module_no_plugin_attr(self):
        """Test loading plugin from module without plugin attribute."""
        mock_module = MagicMock(spec=[])  # No attributes
        
        with patch('importlib.import_module', return_value=mock_module):
            with self.assertRaises(PluginLoadError) as ctx:
                self.manager.load_plugin_from_module("test.module")
            
            self.assertIn("does not define a 'plugin' attribute", str(ctx.exception))
    
    def test_load_plugin_from_module_invalid_plugin_attr(self):
        """Test loading plugin from module with invalid plugin attribute."""
        mock_module = MagicMock()
        mock_module.plugin = "not a plugin"  # Invalid type
        
        with patch('importlib.import_module', return_value=mock_module):
            with self.assertRaises(PluginLoadError) as ctx:
                self.manager.load_plugin_from_module("test.module")
            
            self.assertIn("plugin attribute must be a FormatPlugin", str(ctx.exception))
    
    def test_load_plugin_from_file(self):
        """Test loading plugin from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from docpivot.io.plugins import FormatPlugin

class FilePlugin(FormatPlugin):
    @property
    def name(self):
        return "file-plugin"
    
    @property
    def version(self):
        return "1.0.0"

plugin = FilePlugin()
""")
            temp_path = f.name
        
        try:
            self.manager.load_plugin_from_file(temp_path)
            
            self.assertIn("file-plugin", self.manager._plugins)
            self.assertIn(temp_path, self.manager._loaded_modules)
        finally:
            Path(temp_path).unlink()
    
    def test_load_plugin_from_file_not_found(self):
        """Test loading plugin from non-existent file."""
        with self.assertRaises(PluginLoadError) as ctx:
            self.manager.load_plugin_from_file("/non/existent/file.py")
        
        self.assertIn("Plugin file not found", str(ctx.exception))
    
    def test_load_plugin_from_file_wrong_extension(self):
        """Test loading plugin from file with wrong extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            with self.assertRaises(PluginLoadError) as ctx:
                self.manager.load_plugin_from_file(temp_path)
            
            self.assertIn("Plugin file must be a Python file", str(ctx.exception))
        finally:
            Path(temp_path).unlink()
    
    def test_load_plugin_from_file_no_plugin_attr(self):
        """Test loading plugin from file without plugin attribute."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# No plugin defined\n")
            temp_path = f.name
        
        try:
            with self.assertRaises(PluginLoadError) as ctx:
                self.manager.load_plugin_from_file(temp_path)
            
            self.assertIn("does not define a 'plugin' attribute", str(ctx.exception))
        finally:
            Path(temp_path).unlink()
    
    def test_load_plugin_from_file_invalid_plugin_attr(self):
        """Test loading plugin from file with invalid plugin attribute."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("plugin = 'not a plugin'\n")
            temp_path = f.name
        
        try:
            with self.assertRaises(PluginLoadError) as ctx:
                self.manager.load_plugin_from_file(temp_path)
            
            self.assertIn("plugin attribute must be a FormatPlugin", str(ctx.exception))
        finally:
            Path(temp_path).unlink()
    
    def test_load_plugin_from_file_with_class(self):
        """Test loading plugin from file with plugin class."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from docpivot.io.plugins import FormatPlugin

class FilePlugin(FormatPlugin):
    @property
    def name(self):
        return "file-class-plugin"
    
    @property
    def version(self):
        return "1.0.0"

plugin = FilePlugin  # Class, not instance
""")
            temp_path = f.name
        
        try:
            self.manager.load_plugin_from_file(temp_path)
            
            self.assertIn("file-class-plugin", self.manager._plugins)
            plugin = self.manager._plugins["file-class-plugin"]
            self.assertIsInstance(plugin, FormatPlugin)
        finally:
            Path(temp_path).unlink()
    
    def test_load_plugins_from_directory(self):
        """Test loading plugins from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create plugin files
            plugin1_path = Path(temp_dir) / "plugin1.py"
            plugin1_path.write_text("""
from docpivot.io.plugins import FormatPlugin

class Plugin1(FormatPlugin):
    @property
    def name(self):
        return "plugin1"
    
    @property
    def version(self):
        return "1.0.0"

plugin = Plugin1()
""")
            
            plugin2_path = Path(temp_dir) / "plugin2.py"
            plugin2_path.write_text("""
from docpivot.io.plugins import FormatPlugin

class Plugin2(FormatPlugin):
    @property
    def name(self):
        return "plugin2"
    
    @property
    def version(self):
        return "2.0.0"

plugin = Plugin2()
""")
            
            # Create file to be skipped
            init_path = Path(temp_dir) / "__init__.py"
            init_path.write_text("")
            
            # Create invalid plugin file (should be skipped)
            invalid_path = Path(temp_dir) / "invalid.py"
            invalid_path.write_text("# No plugin here")
            
            loaded = self.manager.load_plugins_from_directory(temp_dir)
            
            # Should load valid plugins and skip invalid ones
            self.assertIn("plugin1", loaded)
            self.assertIn("plugin2", loaded)
            self.assertEqual(len(loaded), 2)
            
            self.assertIn("plugin1", self.manager._plugins)
            self.assertIn("plugin2", self.manager._plugins)
    
    def test_load_plugins_from_directory_not_found(self):
        """Test loading plugins from non-existent directory."""
        with self.assertRaises(FileNotFoundError) as ctx:
            self.manager.load_plugins_from_directory("/non/existent/directory")
        
        self.assertIn("Plugin directory not found", str(ctx.exception))
    
    def test_load_plugins_from_directory_not_a_dir(self):
        """Test loading plugins from a file instead of directory."""
        with tempfile.NamedTemporaryFile() as f:
            with self.assertRaises(ValueError) as ctx:
                self.manager.load_plugins_from_directory(f.name)
            
            self.assertIn("Path is not a directory", str(ctx.exception))


class TestPluginIntegration(unittest.TestCase):
    """Test plugin integration with format registry."""
    
    def setUp(self):
        """Set up test environment."""
        self.registry = FormatRegistry()
        self.manager = PluginManager(registry=self.registry)
    
    def test_plugin_registers_readers_and_serializers(self):
        """Test that plugin correctly registers readers and serializers."""
        plugin = TestFormatPlugin()
        self.manager.register_plugin(plugin)
        
        # Check that reader was registered
        reader_class = self.registry.get_reader_for_format("test")
        self.assertIs(reader_class, TestReaderPlugin)
        
        # Check that serializer was registered
        serializer_class = self.registry.get_serializer_for_format("test")
        self.assertIs(serializer_class, TestSerializerPlugin)
    
    def test_plugin_with_reader_registration_error(self):
        """Test plugin with reader registration error."""
        
        class BadReaderPlugin(FormatPlugin):
            @property
            def name(self):
                return "bad-reader"
            
            @property
            def version(self):
                return "1.0.0"
            
            def get_readers(self):
                return {"test": "not a reader class"}  # Invalid reader
        
        plugin = BadReaderPlugin()
        
        with self.assertRaises(PluginLoadError) as ctx:
            self.manager.register_plugin(plugin)
        
        self.assertIn("Failed to register reader", str(ctx.exception))
    
    def test_plugin_with_serializer_registration_error(self):
        """Test plugin with serializer registration error."""
        
        class BadSerializerPlugin(FormatPlugin):
            @property
            def name(self):
                return "bad-serializer"
            
            @property
            def version(self):
                return "1.0.0"
            
            def get_serializers(self):
                return {"test": "not a serializer class"}  # Invalid serializer
        
        plugin = BadSerializerPlugin()
        
        with self.assertRaises(PluginLoadError) as ctx:
            self.manager.register_plugin(plugin)
        
        self.assertIn("Failed to register serializer", str(ctx.exception))


class TestGlobalPluginManager(unittest.TestCase):
    """Test global plugin manager functionality."""
    
    def tearDown(self):
        """Clean up global state."""
        # Reset global plugin manager
        import docpivot.io.plugins
        docpivot.io.plugins._global_plugin_manager = None
    
    def test_get_plugin_manager_singleton(self):
        """Test that get_plugin_manager returns singleton."""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()
        
        self.assertIs(manager1, manager2)
    
    def test_get_plugin_manager_creates_instance(self):
        """Test that get_plugin_manager creates instance when needed."""
        import docpivot.io.plugins
        
        # Ensure no existing instance
        docpivot.io.plugins._global_plugin_manager = None
        
        manager = get_plugin_manager()
        
        self.assertIsNotNone(manager)
        self.assertIsInstance(manager, PluginManager)
        self.assertIs(docpivot.io.plugins._global_plugin_manager, manager)


if __name__ == "__main__":
    unittest.main()