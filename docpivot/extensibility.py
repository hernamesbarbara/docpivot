"""Runtime format registration and discovery utilities.

This module provides convenient APIs for runtime format registration,
discovery, and management in DocPivot's extensibility system.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.types import DoclingDocument

from .io.readers.basereader import BaseReader
from .io.format_registry import get_format_registry, FormatRegistry
from .io.plugins import get_plugin_manager, PluginManager, FormatPlugin
from .io.validation import FormatValidator
from .io.serializers.serializerprovider import SerializerProvider
from .io.readers.readerfactory import ReaderFactory


class ExtensibilityManager:
    """Central manager for DocPivot's extensibility features.
    
    This class provides a high-level API for managing custom formats,
    plugins, and extensibility features in DocPivot.
    """
    
    def __init__(self):
        """Initialize the extensibility manager."""
        self._format_registry = get_format_registry()
        self._plugin_manager = get_plugin_manager()
        self._validator = FormatValidator()
    
    # Format Registration Methods
    
    def register_reader(
        self, 
        format_name: str, 
        reader_class: Type[BaseReader],
        validate: bool = True
    ) -> None:
        """Register a custom reader for a format.
        
        Args:
            format_name: Name of the format
            reader_class: Reader class that extends BaseReader
            validate: Whether to validate the reader implementation
            
        Raises:
            ValueError: If validation fails
        """
        if validate:
            result = self._validator.validate_reader(reader_class)
            if not result.is_valid:
                raise ValueError(f"Reader validation failed: {result}")
        
        self._format_registry.register_reader(format_name, reader_class)
    
    def register_serializer(
        self,
        format_name: str,
        serializer_class: Type[BaseDocSerializer],
        validate: bool = True
    ) -> None:
        """Register a custom serializer for a format.
        
        Args:
            format_name: Name of the format
            serializer_class: Serializer class that extends BaseDocSerializer
            validate: Whether to validate the serializer implementation
            
        Raises:
            ValueError: If validation fails
        """
        if validate:
            result = self._validator.validate_serializer(serializer_class)
            if not result.is_valid:
                raise ValueError(f"Serializer validation failed: {result}")
        
        self._format_registry.register_serializer(format_name, serializer_class)
        
        # Also register with SerializerProvider for backward compatibility
        SerializerProvider.register_serializer(format_name, serializer_class)
    
    def register_format(
        self,
        format_name: str,
        reader_class: Optional[Type[BaseReader]] = None,
        serializer_class: Optional[Type[BaseDocSerializer]] = None,
        validate: bool = True
    ) -> None:
        """Register both reader and serializer for a format.
        
        Args:
            format_name: Name of the format
            reader_class: Optional reader class
            serializer_class: Optional serializer class
            validate: Whether to validate implementations
        """
        if reader_class:
            self.register_reader(format_name, reader_class, validate)
        
        if serializer_class:
            self.register_serializer(format_name, serializer_class, validate)
    
    # Plugin Management Methods
    
    def load_plugin(self, plugin: Union[FormatPlugin, Type[FormatPlugin], str, Path]) -> None:
        """Load a format plugin.
        
        Args:
            plugin: Plugin instance, class, module name, or file path
            
        Raises:
            PluginLoadError: If plugin loading fails
        """
        if isinstance(plugin, FormatPlugin):
            self._plugin_manager.register_plugin(plugin)
        elif isinstance(plugin, type) and issubclass(plugin, FormatPlugin):
            self._plugin_manager.load_plugin_from_class(plugin)
        elif isinstance(plugin, str):
            self._plugin_manager.load_plugin_from_module(plugin)
        elif isinstance(plugin, Path) or (isinstance(plugin, str) and Path(plugin).exists()):
            self._plugin_manager.load_plugin_from_file(plugin)
        else:
            raise ValueError(f"Invalid plugin type: {type(plugin)}")
    
    def load_plugins_from_directory(self, directory: Union[str, Path]) -> List[str]:
        """Load all plugins from a directory.
        
        Args:
            directory: Directory containing plugin files
            
        Returns:
            List[str]: Names of successfully loaded plugins
        """
        return self._plugin_manager.load_plugins_from_directory(directory)
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            bool: True if plugin was unloaded, False if not found
        """
        return self._plugin_manager.unregister_plugin(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugins.
        
        Returns:
            List[str]: List of plugin names
        """
        return self._plugin_manager.list_plugins()
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Optional[Dict[str, Any]]: Plugin metadata or None if not found
        """
        return self._plugin_manager.get_plugin_metadata(plugin_name)
    
    # Format Discovery Methods
    
    def discover_formats(self) -> Dict[str, Dict[str, Any]]:
        """Discover all available formats and their capabilities.
        
        Returns:
            Dict[str, Dict[str, Any]]: Format information
        """
        return self._format_registry.discover_formats()
    
    def list_readable_formats(self) -> List[str]:
        """List formats that can be read.
        
        Returns:
            List[str]: List of readable format names
        """
        return self._format_registry.list_readable_formats()
    
    def list_writable_formats(self) -> List[str]:
        """List formats that can be written.
        
        Returns:
            List[str]: List of writable format names
        """
        return self._format_registry.list_writable_formats()
    
    def is_format_supported(self, format_name: str) -> bool:
        """Check if a format is supported.
        
        Args:
            format_name: Name of the format to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return self._format_registry.is_format_supported(format_name)
    
    def can_read_format(self, format_name: str) -> bool:
        """Check if a format can be read.
        
        Args:
            format_name: Name of the format to check
            
        Returns:
            bool: True if format can be read, False otherwise
        """
        return self._format_registry.can_read_format(format_name)
    
    def can_write_format(self, format_name: str) -> bool:
        """Check if a format can be written.
        
        Args:
            format_name: Name of the format to check
            
        Returns:
            bool: True if format can be written, False otherwise
        """
        return self._format_registry.can_write_format(format_name)
    
    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions.
        
        Returns:
            List[str]: List of supported file extensions
        """
        return self._format_registry.get_supported_extensions()
    
    # Reader and Serializer Factory Methods
    
    def get_reader_for_file(self, file_path: Union[str, Path]) -> Optional[BaseReader]:
        """Get appropriate reader for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[BaseReader]: Reader instance or None if not supported
        """
        return self._format_registry.get_reader_for_file(file_path)
    
    def get_serializer(
        self, 
        format_name: str, 
        doc: DoclingDocument, 
        **kwargs: Any
    ) -> Optional[BaseDocSerializer]:
        """Get serializer for a format.
        
        Args:
            format_name: Name of the format
            doc: Document to serialize
            **kwargs: Additional parameters
            
        Returns:
            Optional[BaseDocSerializer]: Serializer instance or None if not supported
        """
        try:
            return SerializerProvider.get_serializer(format_name, doc, **kwargs)
        except ValueError:
            return None
    
    # Validation Methods
    
    def validate_reader(self, reader_class: Type[BaseReader]) -> Dict[str, Any]:
        """Validate a reader implementation.
        
        Args:
            reader_class: Reader class to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        result = self._validator.validate_reader(reader_class)
        return {
            "is_valid": result.is_valid,
            "issues": [str(issue) for issue in result.issues],
            "tested_features": result.tested_features
        }
    
    def validate_serializer(self, serializer_class: Type[BaseDocSerializer]) -> Dict[str, Any]:
        """Validate a serializer implementation.
        
        Args:
            serializer_class: Serializer class to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        result = self._validator.validate_serializer(serializer_class)
        return {
            "is_valid": result.is_valid,
            "issues": [str(issue) for issue in result.issues],
            "tested_features": result.tested_features
        }
    
    def validate_format_pair(
        self,
        reader_class: Type[BaseReader],
        serializer_class: Type[BaseDocSerializer],
        test_file: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Validate reader/serializer compatibility.
        
        Args:
            reader_class: Reader class to test
            serializer_class: Serializer class to test
            test_file: Optional test file for round-trip testing
            
        Returns:
            Dict[str, Any]: Validation results
        """
        return self._validator.validate_format_pair(reader_class, serializer_class, test_file)
    
    # Utility Methods
    
    def get_format_info(self, format_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a format.
        
        Args:
            format_name: Name of the format
            
        Returns:
            Optional[Dict[str, Any]]: Format information or None if not found
        """
        format_info = self._format_registry.get_format_info(format_name)
        if format_info:
            return format_info.get_capabilities()
        return None
    
    def unregister_format(self, format_name: str) -> bool:
        """Unregister a format.
        
        Args:
            format_name: Name of the format to unregister
            
        Returns:
            bool: True if format was unregistered, False if not found
        """
        return self._format_registry.unregister_format(format_name)
    
    def clear_registry(self) -> None:
        """Clear all registered formats.
        
        Warning: This will remove all registered formats including built-ins.
        Use with caution.
        """
        self._format_registry.clear_registry()
    
    def reset_to_defaults(self) -> None:
        """Reset registry to default state.
        
        This clears all custom formats and plugins, keeping only built-ins.
        """
        self.clear_registry()
        self._plugin_manager.clear_plugins()
        
        # Re-register built-ins
        self._format_registry._register_builtin_formats()


# Global extensibility manager instance
_global_extensibility_manager: Optional[ExtensibilityManager] = None


def get_extensibility_manager() -> ExtensibilityManager:
    """Get the global extensibility manager instance.
    
    Returns:
        ExtensibilityManager: Global extensibility manager
    """
    global _global_extensibility_manager
    if _global_extensibility_manager is None:
        _global_extensibility_manager = ExtensibilityManager()
    return _global_extensibility_manager


# Convenience functions for common operations

def register_format(
    format_name: str,
    reader_class: Optional[Type[BaseReader]] = None,
    serializer_class: Optional[Type[BaseDocSerializer]] = None,
    validate: bool = True
) -> None:
    """Register a format with optional reader and/or serializer.
    
    Args:
        format_name: Name of the format
        reader_class: Optional reader class
        serializer_class: Optional serializer class
        validate: Whether to validate implementations
    """
    manager = get_extensibility_manager()
    manager.register_format(format_name, reader_class, serializer_class, validate)


def load_plugin(plugin: Union[FormatPlugin, Type[FormatPlugin], str, Path]) -> None:
    """Load a format plugin.
    
    Args:
        plugin: Plugin instance, class, module name, or file path
    """
    manager = get_extensibility_manager()
    manager.load_plugin(plugin)


def discover_formats() -> Dict[str, Dict[str, Any]]:
    """Discover all available formats.
    
    Returns:
        Dict[str, Dict[str, Any]]: Format information
    """
    manager = get_extensibility_manager()
    return manager.discover_formats()


def list_supported_formats() -> Dict[str, List[str]]:
    """List all supported formats by capability.
    
    Returns:
        Dict[str, List[str]]: Dictionary with 'readable' and 'writable' format lists
    """
    manager = get_extensibility_manager()
    return {
        "readable": manager.list_readable_formats(),
        "writable": manager.list_writable_formats(),
    }


def validate_implementation(
    reader_class: Optional[Type[BaseReader]] = None,
    serializer_class: Optional[Type[BaseDocSerializer]] = None
) -> Dict[str, Any]:
    """Validate custom format implementations.
    
    Args:
        reader_class: Optional reader class to validate
        serializer_class: Optional serializer class to validate
        
    Returns:
        Dict[str, Any]: Validation results
    """
    manager = get_extensibility_manager()
    results = {}
    
    if reader_class:
        results["reader"] = manager.validate_reader(reader_class)
    
    if serializer_class:
        results["serializer"] = manager.validate_serializer(serializer_class)
    
    if reader_class and serializer_class:
        results["compatibility"] = manager.validate_format_pair(reader_class, serializer_class)
    
    return results