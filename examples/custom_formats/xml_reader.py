"""Example XML reader implementation.

This module demonstrates how to create a custom reader that can parse
XML documents into DoclingDocument format using DocPivot's extensibility patterns.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, List, Union, Optional, Dict

from docling_core.types import (
    DoclingDocument,
    DocumentOrigin,
    NodeItem,
    TextItem,
    GroupItem,
)

from docpivot.io.readers.custom_reader_base import CustomReaderBase


class XMLDocReader(CustomReaderBase):
    """Read XML documents into DoclingDocument format.
    
    This reader demonstrates the extensibility patterns by parsing XML files
    and converting them into the DoclingDocument structure. It handles basic
    XML elements, attributes, and text content.
    
    Example usage:
        reader = XMLDocReader()
        doc = reader.load_data("document.xml")
    """
    
    @property
    def supported_extensions(self) -> List[str]:
        """File extensions this reader supports."""
        return ['.xml', '.xhtml']
    
    @property
    def format_name(self) -> str:
        """Human-readable format name."""
        return "XML Documents"
    
    @property
    def format_description(self) -> Optional[str]:
        """Detailed description of the XML format."""
        return "Extensible Markup Language (XML) document reader with basic structure parsing"
    
    @property
    def version(self) -> str:
        """Version of this reader implementation."""
        return "1.0.0"
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Capabilities supported by this reader."""
        return {
            "text_extraction": True,
            "metadata_extraction": True,
            "structure_preservation": True,
            "embedded_images": False,  # Could be extended to handle image references
            "embedded_tables": True,   # Can handle table-like XML structures
        }
    
    def can_handle(self, file_path: Union[str, Path]) -> bool:
        """Check if this reader can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if this reader can handle the file
        """
        path = Path(file_path)
        
        # Check file extension
        if path.suffix.lower() in self.supported_extensions:
            return True
        
        # Check content for XML signature
        try:
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('<?xml'):
                    return True
                # Also check for XML-like content without declaration
                if first_line.startswith('<') and '>' in first_line:
                    return True
        except Exception:
            return False
        
        return False
    
    def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
        """Load and parse an XML document.
        
        Args:
            file_path: Path to the XML file to load
            **kwargs: Additional parameters (preserve_attributes, namespace_aware, etc.)
            
        Returns:
            DoclingDocument: The loaded and parsed document
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file format is not supported or parsing fails
        """
        path = self._validate_file_exists(file_path)
        self.validate_file_format(path)
        
        # Parse configuration from kwargs
        preserve_attributes = kwargs.get('preserve_attributes', True)
        namespace_aware = kwargs.get('namespace_aware', False)
        
        try:
            # Parse XML content
            if namespace_aware:
                # Use iterparse for namespace-aware parsing
                tree = self._parse_xml_namespace_aware(path)
            else:
                tree = ET.parse(path)
            
            root = tree.getroot()
            
            # Create DoclingDocument
            doc = DoclingDocument(
                name=path.stem,
                origin=DocumentOrigin(
                    mimetype="application/xml",
                    binary_hash="",  # Could compute hash if needed
                    filename=path.name,
                ),
                furniture=[],  # XML doesn't typically have furniture
                body=self._convert_xml_to_node_item(root, preserve_attributes)
            )
            
            return doc
            
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML file {path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading XML file {path}: {e}")
    
    def _parse_xml_namespace_aware(self, file_path: Path) -> ET.ElementTree:
        """Parse XML with namespace awareness.
        
        Args:
            file_path: Path to the XML file
            
        Returns:
            ET.ElementTree: Parsed XML tree
        """
        # For this example, we'll use the standard parser
        # In a real implementation, you might use lxml or other namespace-aware parsers
        return ET.parse(file_path)
    
    def _convert_xml_to_node_item(self, element: ET.Element, preserve_attributes: bool = True) -> NodeItem:
        """Convert XML element to NodeItem recursively.
        
        Args:
            element: XML element to convert
            preserve_attributes: Whether to preserve element attributes
            
        Returns:
            NodeItem: Converted node item
        """
        # Create the base node item
        node_item = NodeItem()
        
        # Set label to element tag (remove namespace prefix for readability)
        tag_name = element.tag
        if '}' in tag_name:
            tag_name = tag_name.split('}')[-1]
        node_item.label = tag_name
        
        # Handle element text content
        if element.text and element.text.strip():
            text_item = TextItem(text=element.text.strip())
            node_item.children = [text_item]
        
        # Handle attributes
        if preserve_attributes and element.attrib:
            # Store attributes as properties or in a special way
            # For this example, we'll add them as text items
            attr_items = []
            for attr_name, attr_value in element.attrib.items():
                attr_text = f"@{attr_name}: {attr_value}"
                attr_items.append(TextItem(text=attr_text))
            
            if attr_items:
                if node_item.children:
                    node_item.children.extend(attr_items)
                else:
                    node_item.children = attr_items
        
        # Handle child elements
        child_items = []
        for child_element in element:
            child_node = self._convert_xml_to_node_item(child_element, preserve_attributes)
            child_items.append(child_node)
            
            # Handle tail text (text after the element)
            if child_element.tail and child_element.tail.strip():
                tail_text = TextItem(text=child_element.tail.strip())
                child_items.append(tail_text)
        
        # Add child items
        if child_items:
            if node_item.children:
                node_item.children.extend(child_items)
            else:
                node_item.children = child_items
        
        return node_item
    
    def get_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract metadata from XML file without full parsing.
        
        Args:
            file_path: Path to the XML file
            
        Returns:
            Dict[str, Any]: Dictionary of metadata properties
        """
        metadata = super().get_metadata(file_path)
        
        try:
            path = Path(file_path)
            
            # Quick parsing to get root element info
            for event, elem in ET.iterparse(path, events=['start']):
                # Get root element information
                root_tag = elem.tag
                if '}' in root_tag:
                    root_tag = root_tag.split('}')[-1]
                
                metadata.update({
                    "root_element": root_tag,
                    "namespace": elem.tag.split('}')[0][1:] if '}' in elem.tag else None,
                    "attributes": dict(elem.attrib) if elem.attrib else {},
                })
                
                # We only need the root element for metadata
                break
                
        except Exception:
            # If parsing fails, return basic metadata
            pass
        
        return metadata
    
    def _detect_xml_type(self, file_path: Path) -> Optional[str]:
        """Detect specific XML document type.
        
        Args:
            file_path: Path to the XML file
            
        Returns:
            Optional[str]: Detected XML document type
        """
        try:
            # Quick check of root element and DOCTYPE
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1000 characters
                
                if '<!DOCTYPE html' in content.lower():
                    return "XHTML"
                elif 'xmlns:xsi' in content:
                    return "XML Schema Instance"
                elif '<rss' in content.lower():
                    return "RSS Feed"
                elif '<feed' in content.lower() and 'xmlns="http://www.w3.org/2005/Atom"' in content:
                    return "Atom Feed"
                else:
                    return "Generic XML"
                    
        except Exception:
            return None
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the XML reader.
        
        Args:
            **kwargs: Configuration parameters
        """
        super().__init__(**kwargs)
        
        # Set default configuration
        self.config.setdefault('preserve_attributes', True)
        self.config.setdefault('namespace_aware', False)
        self.config.setdefault('handle_namespaces', True)