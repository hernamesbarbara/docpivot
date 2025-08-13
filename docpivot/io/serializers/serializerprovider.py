"""Serializer provider following Docling's factory pattern."""

from typing import Any, Dict, Type, Optional, Union

from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from docling_core.transforms.serializer.doctags import DocTagsDocSerializer
from docling_core.transforms.serializer.html import HTMLDocSerializer
from docling_core.types import DoclingDocument


class SerializerProvider:
    """Factory for creating serializer instances following Docling patterns."""
    
    _serializers: Dict[str, Type[BaseDocSerializer]] = {
        "markdown": MarkdownDocSerializer,
        "md": MarkdownDocSerializer,
        "doctags": DocTagsDocSerializer,
        "html": HTMLDocSerializer,
    }
    
    @classmethod
    def get_serializer(
        cls,
        format_name: str,
        doc: DoclingDocument,
        **kwargs: Any
    ) -> BaseDocSerializer:
        """Get a serializer instance for the specified format.
        
        Args:
            format_name: The output format name (e.g., "markdown", "html").
            doc: The DoclingDocument to serialize.
            **kwargs: Additional parameters to pass to the serializer constructor.
            
        Returns:
            BaseDocSerializer: Configured serializer instance.
            
        Raises:
            ValueError: If the format is not supported.
        """
        format_key = format_name.lower().strip()
        
        if format_key not in cls._serializers:
            raise ValueError(
                f"Unsupported format '{format_name}'. "
                f"Supported formats: {', '.join(cls._serializers.keys())}"
            )
        
        serializer_cls = cls._serializers[format_key]
        return serializer_cls(doc=doc, **kwargs)  # type: ignore[call-arg]
    
    @classmethod
    def register_serializer(
        cls,
        format_name: str,
        serializer_cls: Type[BaseDocSerializer]
    ) -> None:
        """Register a new serializer for a format.
        
        Args:
            format_name: The format name to register.
            serializer_cls: The serializer class to use for this format.
            
        Raises:
            TypeError: If serializer_cls is not a BaseDocSerializer subclass.
        """
        if not issubclass(serializer_cls, BaseDocSerializer):
            raise TypeError(
                f"Serializer class must be a subclass of BaseDocSerializer, "
                f"got {serializer_cls.__name__}"
            )
        
        format_key = format_name.lower().strip()
        cls._serializers[format_key] = serializer_cls
    
    @classmethod
    def list_formats(cls) -> list[str]:
        """List all supported format names.
        
        Returns:
            list[str]: List of supported format names.
        """
        return list(cls._serializers.keys())
    
    @classmethod
    def is_format_supported(cls, format_name: str) -> bool:
        """Check if a format is supported.
        
        Args:
            format_name: The format name to check.
            
        Returns:
            bool: True if supported, False otherwise.
        """
        format_key = format_name.lower().strip()
        return format_key in cls._serializers