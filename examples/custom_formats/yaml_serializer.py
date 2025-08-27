"""Example YAML serializer implementation.

This module demonstrates how to create a custom serializer that outputs
DoclingDocument content to YAML format using DocPivot's extensibility patterns.
"""

import yaml
from typing import Any, Dict, Optional

from docling_core.types import DoclingDocument
from docling_core.transforms.serializer.base import SerializationResult

from docpivot.io.serializers.custom_serializer_base import (
    CustomSerializerBase, 
    CustomSerializerParams
)


class YAMLSerializerParams(CustomSerializerParams):
    """Parameters for YAML serialization."""
    
    def __init__(
        self,
        indent: int = 2,
        include_metadata: bool = True,
        include_furniture: bool = False,
        preserve_structure: bool = True,
    ):
        """Initialize YAML serializer parameters.
        
        Args:
            indent: Number of spaces for YAML indentation
            include_metadata: Whether to include document metadata
            include_furniture: Whether to include furniture elements
            preserve_structure: Whether to preserve document structure hierarchy
        """
        super().__init__()
        self.indent = indent
        self.include_metadata = include_metadata
        self.include_furniture = include_furniture
        self.preserve_structure = preserve_structure


class YAMLDocSerializer(CustomSerializerBase):
    """Serialize DoclingDocument to YAML format.
    
    This serializer demonstrates the extensibility patterns by converting
    a DoclingDocument into a structured YAML representation that preserves
    the document hierarchy and content.
    
    Example usage:
        doc = # ... DoclingDocument instance
        params = YAMLSerializerParams(indent=4, include_metadata=True)
        serializer = YAMLDocSerializer(doc=doc, params=params)
        result = serializer.serialize()
        print(result.text)
    """
    
    def __init__(
        self,
        doc: DoclingDocument,
        params: Optional[YAMLSerializerParams] = None,
        component_serializers: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        """Initialize the YAML serializer.
        
        Args:
            doc: The DoclingDocument to serialize
            params: YAML-specific parameters
            component_serializers: Optional component serializers
            **kwargs: Additional configuration
        """
        # Use YAMLSerializerParams if not provided
        if params is None:
            params = YAMLSerializerParams()
        
        super().__init__(
            doc=doc,
            params=params,
            component_serializers=component_serializers,
            **kwargs
        )
    
    @property
    def output_format(self) -> str:
        """Output format identifier."""
        return "yaml"
    
    @property
    def file_extension(self) -> str:
        """Default file extension for YAML files."""
        return ".yaml"
    
    @property
    def format_description(self) -> Optional[str]:
        """Description of the YAML format."""
        return "YAML (YAML Ain't Markup Language) structured document format"
    
    @property
    def mimetype(self) -> str:
        """MIME type for YAML content."""
        return "application/x-yaml"
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Capabilities supported by this serializer."""
        return {
            "text_content": True,
            "document_structure": True,
            "metadata": True,
            "images": False,  # YAML doesn't handle binary data well
            "tables": True,
            "formatting": False,  # YAML is primarily for structure
        }
    
    def serialize(self) -> SerializationResult:
        """Convert DoclingDocument to YAML format.
        
        Returns:
            SerializationResult: The YAML serialized content
        """
        # Create the main document structure
        yaml_doc = {}
        
        # Add metadata if requested
        if self.params.include_metadata:
            yaml_doc["metadata"] = self._serialize_metadata()
        
        # Add document content
        if self.params.preserve_structure:
            yaml_doc["content"] = self._serialize_structured_content()
        else:
            yaml_doc["content"] = self._serialize_text_content()
        
        # Add furniture if requested
        if self.params.include_furniture and hasattr(self.doc, 'furniture'):
            yaml_doc["furniture"] = self._serialize_furniture()
        
        # Convert to YAML string
        try:
            yaml_text = yaml.dump(
                yaml_doc,
                default_flow_style=False,
                indent=self.params.indent,
                allow_unicode=True,
                sort_keys=False
            )
        except Exception as e:
            # Fallback to simple text representation
            yaml_text = yaml.dump(
                {"content": {"text": self._serialize_text_content()}},
                default_flow_style=False,
                indent=self.params.indent
            )
        
        return SerializationResult(text=yaml_text)
    
    def _serialize_metadata(self) -> Dict[str, Any]:
        """Serialize document metadata to YAML structure.
        
        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        metadata = {}
        
        if hasattr(self.doc, 'name') and self.doc.name:
            metadata["name"] = self.doc.name
        
        if hasattr(self.doc, 'origin') and self.doc.origin:
            origin_data = {}
            if hasattr(self.doc.origin, 'filename') and self.doc.origin.filename:
                origin_data["filename"] = self.doc.origin.filename
            if hasattr(self.doc.origin, 'mimetype') and self.doc.origin.mimetype:
                origin_data["mimetype"] = self.doc.origin.mimetype
            if origin_data:
                metadata["origin"] = origin_data
        
        # Add serializer information
        metadata["serializer"] = {
            "format": self.output_format,
            "version": self.version,
            "timestamp": self._get_timestamp()
        }
        
        return metadata
    
    def _serialize_structured_content(self) -> Dict[str, Any]:
        """Serialize document content with structure preservation.
        
        Returns:
            Dict[str, Any]: Structured content dictionary
        """
        content = {}
        
        # Serialize body content
        if hasattr(self.doc, 'body') and self.doc.body:
            content["body"] = self._item_to_yaml_dict(self.doc.body)
        
        return content
    
    def _serialize_furniture(self) -> list:
        """Serialize furniture elements.
        
        Returns:
            list: List of furniture elements
        """
        furniture_list = []
        
        if hasattr(self.doc, 'furniture'):
            for item in self.doc.furniture:
                furniture_list.append(self._item_to_yaml_dict(item))
        
        return furniture_list
    
    def _item_to_yaml_dict(self, item) -> Dict[str, Any]:
        """Convert a document item to YAML-friendly dictionary.
        
        Args:
            item: Document item to convert
            
        Returns:
            Dict[str, Any]: YAML-friendly representation
        """
        result = {}
        
        # Add item type if available
        if hasattr(item, '__class__'):
            result["type"] = item.__class__.__name__
        
        # Add text content
        if hasattr(item, 'text') and item.text:
            result["text"] = item.text
        
        # Add label
        if hasattr(item, 'label') and item.label:
            result["label"] = item.label
        
        # Add properties
        if hasattr(item, 'properties') and item.properties:
            result["properties"] = dict(item.properties)
        
        # Add bounding box if available
        if hasattr(item, 'bbox') and item.bbox:
            result["bbox"] = {
                "x": item.bbox.l,
                "y": item.bbox.t,
                "width": item.bbox.r - item.bbox.l,
                "height": item.bbox.b - item.bbox.t
            }
        
        # Add children recursively
        if hasattr(item, 'children') and item.children:
            result["children"] = [
                self._item_to_yaml_dict(child) for child in item.children
            ]
        
        return result
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata.
        
        Returns:
            str: ISO formatted timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def validate_document(self, doc: DoclingDocument) -> None:
        """Validate that the document can be serialized to YAML.
        
        Args:
            doc: Document to validate
            
        Raises:
            ValueError: If document contains unsupported elements
        """
        super().validate_document(doc)
        
        # YAML-specific validations could go here
        # For example, checking for binary data that can't be represented in YAML
        pass