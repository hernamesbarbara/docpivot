"""Example format plugin combining YAML serializer and XML reader.

This module demonstrates how to create a format plugin that provides
both readers and serializers for DocPivot's extensibility system.
"""

from typing import Dict, Type

from docling_core.transforms.serializer.common import BaseDocSerializer

from docpivot.io.readers.basereader import BaseReader
from docpivot.io.plugins import FormatPlugin

# Import our example implementations
from .yaml_serializer import YAMLDocSerializer
from .xml_reader import XMLDocReader


class ExampleFormatPlugin(FormatPlugin):
    """Example format plugin providing XML reading and YAML serialization.
    
    This plugin demonstrates how to bundle multiple format capabilities
    into a single plugin that can be easily loaded and registered.
    """
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return "example-formats"
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return "Example plugin providing XML reading and YAML serialization capabilities"
    
    @property
    def author(self) -> str:
        """Plugin author."""
        return "DocPivot Team"
    
    @property
    def homepage(self) -> str:
        """Plugin homepage."""
        return "https://github.com/your-username/docpivot"
    
    def get_readers(self) -> Dict[str, Type[BaseReader]]:
        """Get reader classes provided by this plugin."""
        return {
            "xml": XMLDocReader,
        }
    
    def get_serializers(self) -> Dict[str, Type[BaseDocSerializer]]:
        """Get serializer classes provided by this plugin."""
        return {
            "yaml": YAMLDocSerializer,
        }
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        # Perform any setup needed for the plugin
        # For example, you might check for required dependencies
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML serialization. "
                "Install it with: pip install PyYAML"
            )
        
        try:
            import xml.etree.ElementTree as ET
        except ImportError:
            # This should be available in standard library
            raise ImportError("XML parsing support is not available")
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        # Perform any cleanup if needed
        pass


# Create plugin instance for easy loading
plugin = ExampleFormatPlugin()


# Alternative: Define plugin as class for dynamic loading
# plugin = ExampleFormatPlugin