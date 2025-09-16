"""DocPivot - Simple document format conversion for Docling."""

__version__ = "2.0.1"

# Core engine (primary interface)
from docpivot.defaults import (
    get_debug_config,
    get_default_lexical_config,
    get_full_config,
    get_minimal_config,
    get_performance_config,
    get_web_config,
    merge_configs,
)
from docpivot.engine import ConversionResult, DocPivotEngine
from docpivot.engine_builder import DocPivotEngineBuilder
from docpivot.io.readers.basereader import BaseReader
from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.readers.lexicaljsonreader import LexicalJsonReader

# Specific implementations for advanced users
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer

__all__ = [
    # New simplified API (primary)
    "DocPivotEngine",
    "ConversionResult",
    "DocPivotEngineBuilder",

    # Configuration helpers
    "get_default_lexical_config",
    "get_performance_config",
    "get_debug_config",
    "get_minimal_config",
    "get_full_config",
    "get_web_config",
    "merge_configs",

    # Low-level components (advanced users)
    "LexicalDocSerializer",
    "DoclingJsonReader",
    "LexicalJsonReader",
    "BaseReader",
]
