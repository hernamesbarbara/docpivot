"""Plugin architecture for format extensions.

This module provides a plugin system that allows users to create modular
format extensions for DocPivot. Plugins can provide readers, serializers,
or both for new file formats.
"""

import importlib
import importlib.util
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from docling_core.transforms.serializer.common import BaseDocSerializer

from .readers.basereader import BaseReader
from .format_registry import FormatRegistry, get_format_registry


class FormatPlugin(ABC):
    """Base class for format plugins.
    
    Format plugins provide one or more readers and/or serializers for
    file formats. This allows for modular extension of DocPivot's capabilities.
    
    Example usage:
        class MyFormatPlugin(FormatPlugin):
            @property
            def name(self) -> str:
                return "my-format-plugin"
            
            @property
            def version(self) -> str:
                return "1.0.0"
            
            def get_readers(self) -> Dict[str, Type[BaseReader]]:
                return {"myformat": MyFormatReader}
            
            def get_serializers(self) -> Dict[str, Type[BaseDocSerializer]]:
                return {"myformat": MyFormatSerializer}
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name.
        
        Returns:
            str: Unique name for this plugin
        """
        raise NotImplementedError("Plugin must define name")
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version.
        
        Returns:
            str: Version string for this plugin
        """
        raise NotImplementedError("Plugin must define version")
    
    @property
    def description(self) -> Optional[str]:
        """Optional plugin description.
        
        Returns:
            Optional[str]: Description of what this plugin provides
        """
        return None
    
    @property
    def author(self) -> Optional[str]:
        """Optional plugin author.
        
        Returns:
            Optional[str]: Plugin author information
        """
        return None
    
    @property
    def homepage(self) -> Optional[str]:
        """Optional plugin homepage.
        
        Returns:
            Optional[str]: Plugin homepage URL
        """
        return None
    
    def get_readers(self) -> Dict[str, Type[BaseReader]]:
        """Get reader classes provided by this plugin.
        
        Returns:
            Dict[str, Type[BaseReader]]: Dictionary mapping format names to reader classes
        """
        return {}
    
    def get_serializers(self) -> Dict[str, Type[BaseDocSerializer]]:
        """Get serializer classes provided by this plugin.
        
        Returns:
            Dict[str, Type[BaseDocSerializer]]: Dictionary mapping format names to serializer classes
        """
        return {}
    
    def initialize(self) -> None:
        """Initialize the plugin.
        
        This method is called after the plugin is loaded but before
        its readers and serializers are registered. Override to perform
        any necessary setup.
        """
        pass
    
    def cleanup(self) -> None:
        """Cleanup plugin resources.
        
        This method is called when the plugin is being unloaded.
        Override to perform any necessary cleanup.
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata.
        
        Returns:
            Dict[str, Any]: Dictionary of plugin metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "readers": list(self.get_readers().keys()),
            "serializers": list(self.get_serializers().keys()),
        }
    
    def __str__(self) -> str:
        """String representation of the plugin."""
        return f"{self.name} v{self.version}"
    
    def __repr__(self) -> str:
        """Detailed representation of the plugin."""
        return f"FormatPlugin(name='{self.name}', version='{self.version}')"


class PluginLoadError(Exception):
    """Exception raised when plugin loading fails."""
    
    def __init__(self, plugin_path: str, message: str, original_error: Optional[Exception] = None):
        """Initialize plugin load error.
        
        Args:
            plugin_path: Path to the plugin that failed to load
            message: Error message
            original_error: Original exception that caused the failure
        """
        self.plugin_path = plugin_path
        self.original_error = original_error
        super().__init__(message)


class PluginManager:
    """Manager for format plugins.
    
    This class handles loading, registering, and managing format plugins
    for DocPivot. It supports loading plugins from directories, modules,
    and individual plugin classes.
    """
    
    def __init__(self, registry: Optional[FormatRegistry] = None):
        """Initialize the plugin manager.
        
        Args:
            registry: Format registry to use for registration. If None, uses global registry.
        """
        self.registry = registry or get_format_registry()
        self._plugins: Dict[str, FormatPlugin] = {}
        self._loaded_modules: Dict[str, Any] = {}
    
    def register_plugin(self, plugin: FormatPlugin) -> None:
        """Register a format plugin.
        
        Args:
            plugin: Plugin instance to register
            
        Raises:
            ValueError: If plugin name is already registered
            TypeError: If plugin is not a FormatPlugin instance
        """
        if not isinstance(plugin, FormatPlugin):
            raise TypeError(f"Plugin must be a FormatPlugin instance, got {type(plugin)}")
        
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")
        
        # Initialize the plugin
        try:
            plugin.initialize()
        except Exception as e:
            raise PluginLoadError(
                plugin.name,
                f"Failed to initialize plugin '{plugin.name}': {e}",
                e
            )
        
        # Register readers
        for format_name, reader_class in plugin.get_readers().items():
            try:
                self.registry.register_reader(format_name, reader_class)
            except Exception as e:
                raise PluginLoadError(
                    plugin.name,
                    f"Failed to register reader for format '{format_name}': {e}",
                    e
                )
        
        # Register serializers
        for format_name, serializer_class in plugin.get_serializers().items():
            try:
                self.registry.register_serializer(format_name, serializer_class)
            except Exception as e:
                raise PluginLoadError(
                    plugin.name,
                    f"Failed to register serializer for format '{format_name}': {e}",
                    e
                )
        
        # Store the plugin
        self._plugins[plugin.name] = plugin
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin.
        
        Args:
            plugin_name: Name of the plugin to unregister
            
        Returns:
            bool: True if plugin was unregistered, False if not found
        """
        if plugin_name not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_name]
        
        # Cleanup plugin
        try:
            plugin.cleanup()
        except Exception:
            # Ignore cleanup errors
            pass
        
        # Note: We don't unregister formats from the registry as other
        # plugins or code might depend on them. This is by design.
        
        del self._plugins[plugin_name]
        return True
    
    def load_plugin_from_class(self, plugin_class: Type[FormatPlugin]) -> None:
        """Load a plugin from a class.
        
        Args:
            plugin_class: Plugin class to instantiate and register
            
        Raises:
            PluginLoadError: If plugin loading fails
        """
        if not issubclass(plugin_class, FormatPlugin):
            raise PluginLoadError(
                str(plugin_class),
                f"Plugin class must extend FormatPlugin, got {plugin_class.__name__}"
            )
        
        try:
            plugin = plugin_class()
            self.register_plugin(plugin)
        except Exception as e:
            raise PluginLoadError(
                str(plugin_class),
                f"Failed to instantiate plugin class {plugin_class.__name__}: {e}",
                e
            )
    
    def load_plugin_from_module(self, module_name: str) -> None:
        """Load plugins from a Python module.
        
        The module should define a variable called 'plugin' that contains
        either a FormatPlugin instance or a FormatPlugin class.
        
        Args:
            module_name: Name of the module to import
            
        Raises:
            PluginLoadError: If plugin loading fails
        """
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            raise PluginLoadError(
                module_name,
                f"Failed to import module '{module_name}': {e}",
                e
            )
        
        self._loaded_modules[module_name] = module
        
        # Look for plugin attribute
        if not hasattr(module, 'plugin'):
            raise PluginLoadError(
                module_name,
                f"Module '{module_name}' does not define a 'plugin' attribute"
            )
        
        plugin_attr = getattr(module, 'plugin')
        
        # Handle both plugin instances and classes
        if isinstance(plugin_attr, FormatPlugin):
            self.register_plugin(plugin_attr)
        elif isinstance(plugin_attr, type) and issubclass(plugin_attr, FormatPlugin):
            self.load_plugin_from_class(plugin_attr)
        else:
            raise PluginLoadError(
                module_name,
                f"Module '{module_name}' plugin attribute must be a FormatPlugin "
                f"instance or class, got {type(plugin_attr)}"
            )
    
    def load_plugin_from_file(self, file_path: Union[str, Path]) -> None:
        """Load a plugin from a Python file.
        
        Args:
            file_path: Path to the Python file containing the plugin
            
        Raises:
            PluginLoadError: If plugin loading fails
        """
        path = Path(file_path)
        
        if not path.exists():
            raise PluginLoadError(
                str(file_path),
                f"Plugin file not found: {file_path}"
            )
        
        if not path.suffix == '.py':
            raise PluginLoadError(
                str(file_path),
                f"Plugin file must be a Python file (.py), got: {path.suffix}"
            )
        
        module_name = f"docpivot_plugin_{path.stem}_{id(path)}"
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise PluginLoadError(
                    str(file_path),
                    f"Failed to create module spec for {file_path}"
                )
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
        except Exception as e:
            raise PluginLoadError(
                str(file_path),
                f"Failed to load plugin from file '{file_path}': {e}",
                e
            )
        
        self._loaded_modules[str(file_path)] = module
        
        # Look for plugin attribute
        if not hasattr(module, 'plugin'):
            raise PluginLoadError(
                str(file_path),
                f"Plugin file '{file_path}' does not define a 'plugin' attribute"
            )
        
        plugin_attr = getattr(module, 'plugin')
        
        # Handle both plugin instances and classes
        if isinstance(plugin_attr, FormatPlugin):
            self.register_plugin(plugin_attr)
        elif isinstance(plugin_attr, type) and issubclass(plugin_attr, FormatPlugin):
            self.load_plugin_from_class(plugin_attr)
        else:
            raise PluginLoadError(
                str(file_path),
                f"Plugin file '{file_path}' plugin attribute must be a FormatPlugin "
                f"instance or class, got {type(plugin_attr)}"
            )
    
    def load_plugins_from_directory(self, directory: Union[str, Path]) -> List[str]:
        """Load all plugins from a directory.
        
        This method searches for Python files in the directory and attempts
        to load plugins from each file.
        
        Args:
            directory: Directory to search for plugin files
            
        Returns:
            List[str]: List of successfully loaded plugin names
            
        Raises:
            FileNotFoundError: If directory does not exist
        """
        path = Path(directory)
        
        if not path.exists():
            raise FileNotFoundError(f"Plugin directory not found: {directory}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        loaded_plugins = []
        
        for plugin_file in path.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue  # Skip __init__.py and other special files
            
            try:
                self.load_plugin_from_file(plugin_file)
                # Get the last registered plugin (assuming it was from this file)
                if self._plugins:
                    latest_plugin = list(self._plugins.values())[-1]
                    loaded_plugins.append(latest_plugin.name)
            except PluginLoadError:
                # Continue loading other plugins even if one fails
                continue
        
        return loaded_plugins
    
    def get_plugin(self, plugin_name: str) -> Optional[FormatPlugin]:
        """Get a registered plugin by name.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Optional[FormatPlugin]: Plugin instance or None if not found
        """
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names.
        
        Returns:
            List[str]: List of plugin names
        """
        return list(self._plugins.keys())
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Optional[Dict[str, Any]]: Plugin metadata or None if not found
        """
        plugin = self._plugins.get(plugin_name)
        return plugin.get_metadata() if plugin else None
    
    def discover_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Discover all registered plugins and their capabilities.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping plugin names to metadata
        """
        return {
            name: plugin.get_metadata()
            for name, plugin in self._plugins.items()
        }
    
    def clear_plugins(self) -> None:
        """Unregister all plugins.
        
        Warning: This will unregister all plugins. Use with caution.
        """
        plugin_names = list(self._plugins.keys())
        for plugin_name in plugin_names:
            self.unregister_plugin(plugin_name)


# Global plugin manager instance
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance.
    
    Returns:
        PluginManager: Global plugin manager instance
    """
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager