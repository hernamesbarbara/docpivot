"""DocPivot - Lightweight Python package extending Docling.

Provides additional format readers and serializers with high-level workflow functions.
"""

__version__ = "0.1.0"

# Core classes for advanced usage
from docpivot.io.readers.basereader import BaseReader
from docpivot.io.serializers.serializerprovider import SerializerProvider
from docpivot.workflows import load_document, load_and_serialize, convert_document

__all__ = [
    # High-level API functions (primary interface)
    "load_document", 
    "load_and_serialize", 
    "convert_document",
    # Core classes for advanced usage
    "BaseReader", 
    "SerializerProvider"
]
