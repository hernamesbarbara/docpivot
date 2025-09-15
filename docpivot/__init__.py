"""DocPivot - Simple document format conversion for Docling."""

__version__ = "2.0.1"

# Core engine (primary interface)
from docpivot.engine import DocPivotEngine, ConversionResult
from docpivot.engine_builder import DocPivotEngineBuilder
from docpivot.defaults import (
    get_default_lexical_config,
    get_performance_config,
    get_debug_config,
    get_minimal_config,
    get_full_config,
    get_web_config,
    merge_configs,
)

# Specific implementations for advanced users
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.readers.lexicaljsonreader import LexicalJsonReader
from docpivot.io.readers.basereader import BaseReader

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