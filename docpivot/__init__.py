"""DocPivot - Lightweight Python package extending Docling.

Provides additional format readers and serializers with high-level workflow functions
and comprehensive extensibility system for custom formats.
"""

__version__ = "1.0.0"

# Core classes for advanced usage
from docpivot.io.readers.basereader import BaseReader
from docpivot.io.serializers.serializerprovider import SerializerProvider
from docpivot.workflows import load_document, load_and_serialize, convert_document

# Specific readers and serializers mentioned in PRD
from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.readers.lexicaljsonreader import LexicalJsonReader
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer

# Extensibility API
from docpivot.extensibility import (
    get_extensibility_manager,
    register_format,
    load_plugin,
    discover_formats,
    list_supported_formats,
    validate_implementation,
)

# Base classes for custom formats
from docpivot.io.readers.custom_reader_base import CustomReaderBase
from docpivot.io.serializers.custom_serializer_base import CustomSerializerBase
from docpivot.io.plugins import FormatPlugin

__all__ = [
    # High-level API functions (primary interface)
    "load_document",
    "load_and_serialize",
    "convert_document",
    # Core classes for advanced usage
    "BaseReader",
    "SerializerProvider",
    # Specific readers and serializers from PRD
    "DoclingJsonReader",
    "LexicalJsonReader",
    "LexicalDocSerializer",
    # Extensibility API (main interface for custom formats)
    "get_extensibility_manager",
    "register_format",
    "load_plugin",
    "discover_formats",
    "list_supported_formats",
    "validate_implementation",
    # Base classes for custom format development
    "CustomReaderBase",
    "CustomSerializerBase",
    "FormatPlugin",
]
