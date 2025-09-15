# DocPivot Implementation Plan - REVISED

**Date:** September 15, 2025
**Status:** READY FOR IMPLEMENTATION
**Priority:** HIGH
**Estimated Effort:** 2 days
**Strategy:** Apply CloakPivot learnings for simplification

## Executive Summary

Based on our successful CloakPivot implementation, this revised plan focuses on creating a simple `DocPivotEngine` API that provides one-line document conversion without monkey-patching DoclingDocument. We'll remove unnecessary complexity first, then build a clean, focused API.

## Key Lessons Applied from CloakPivot

1. **NO monkey-patching**: Don't modify external DoclingDocument class
2. **Simplify first**: Remove unnecessary code before adding features
3. **One-line API**: Focus on `engine.convert_to_lexical(doc)` pattern
4. **Smart defaults**: Cover 90% use cases out of the box
5. **Builder pattern**: Advanced configuration without complexity
6. **Minimize codebase**: Target 30%+ reduction in lines of code

## Phase 1: Cleanup and Simplification (Day 1 Morning)

### Task 0: Remove Over-Engineered Code
**Priority:** Do this FIRST
**Target:** Remove ~30% of codebase

```bash
# Remove excessive performance monitoring
rm -rf docpivot/performance/  # Memory profiler, benchmarks, edge cases

# Simplify error handling
# - Reduce custom exceptions from 6 to 2 (DocPivotError, ValidationError)
# - Remove excessive recovery mechanisms
# - Simplify logging configuration

# Remove plugin system if not essential
rm docpivot/io/plugins.py  # Unless actively used

# Remove optimized serializer if redundant
rm docpivot/io/serializers/optimized_lexical_serializer.py
```

### Task 0.1: Simplify Existing Code
- **workflows.py**: Reduce from complex error handling to simple try/catch
- **logging_config.py**: Replace with standard Python logging
- **extensibility.py**: Evaluate if needed; likely remove
- **validation.py**: Keep only essential validation

## Phase 2: Core DocPivotEngine Implementation (Day 1 Afternoon)

### Task 1: Create DocPivotEngine Core Class
**File:** `docpivot/engine.py` (new file ~200 lines)

```python
"""DocPivotEngine - Simple API for document format conversion."""

from typing import Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass

from docling_core.types import DoclingDocument
from docling.document_converter import DocumentConverter

from docpivot.defaults import get_default_lexical_config
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
from docpivot.io.readers.readerfactory import ReaderFactory


@dataclass
class ConversionResult:
    """Result of a document conversion."""
    content: str  # The converted content (JSON, etc.)
    format: str   # Output format used
    metadata: Dict[str, Any]  # Conversion metadata


class DocPivotEngine:
    """Simple API for document format conversion.

    Provides one-line conversion between document formats with
    smart defaults and minimal configuration.

    Examples:
        # Simple usage
        engine = DocPivotEngine()
        result = engine.convert_to_lexical(doc)

        # From file
        result = engine.convert_file("document.pdf", "lexical")

        # With custom config
        engine = DocPivotEngine(lexical_config={"pretty": True})
    """

    def __init__(self,
                 lexical_config: Optional[Dict[str, Any]] = None,
                 default_format: str = "lexical"):
        """Initialize with smart defaults."""
        self.lexical_config = lexical_config or get_default_lexical_config()
        self.default_format = default_format
        self._serializer = LexicalDocSerializer()
        self._reader_factory = ReaderFactory()
        self._converter = None  # Lazy init for DocumentConverter

    def convert_to_lexical(self,
                          document: DoclingDocument,
                          pretty: bool = False,
                          **kwargs) -> ConversionResult:
        """Convert DoclingDocument to Lexical JSON format.

        Args:
            document: The document to convert
            pretty: Pretty-print the output
            **kwargs: Additional serializer options

        Returns:
            ConversionResult with the JSON content
        """
        config = {**self.lexical_config, **kwargs}
        if pretty:
            config["pretty"] = True

        result = self._serializer.serialize(document, **config)

        return ConversionResult(
            content=result.text,
            format="lexical",
            metadata={
                "pretty": pretty,
                "document_name": document.name if hasattr(document, 'name') else None
            }
        )

    def convert_file(self,
                    input_path: Union[str, Path],
                    output_format: str = "lexical",
                    output_path: Optional[Union[str, Path]] = None,
                    **kwargs) -> ConversionResult:
        """Convert a file to the specified format.

        Args:
            input_path: Path to input file
            output_format: Target format (default: "lexical")
            output_path: Optional output file path
            **kwargs: Additional conversion options

        Returns:
            ConversionResult with the converted content
        """
        # Load document
        reader = self._reader_factory.get_reader(input_path)
        document = reader.read(input_path)

        # Convert based on format
        if output_format == "lexical":
            result = self.convert_to_lexical(document, **kwargs)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        # Write to file if requested
        if output_path:
            Path(output_path).write_text(result.content)
            result.metadata["output_path"] = str(output_path)

        return result

    def convert_pdf(self,
                   pdf_path: Union[str, Path],
                   output_format: str = "lexical",
                   **kwargs) -> ConversionResult:
        """Convert PDF to specified format using Docling.

        Args:
            pdf_path: Path to PDF file
            output_format: Target format (default: "lexical")
            **kwargs: Additional conversion options

        Returns:
            ConversionResult with the converted content
        """
        if self._converter is None:
            self._converter = DocumentConverter()

        # Convert PDF to DoclingDocument
        result = self._converter.convert(str(pdf_path))
        document = result.document

        # Convert to target format
        if output_format == "lexical":
            return self.convert_to_lexical(document, **kwargs)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    @classmethod
    def builder(cls) -> 'DocPivotEngineBuilder':
        """Get a builder for advanced configuration."""
        return DocPivotEngineBuilder()
```

### Task 2: Create Builder Pattern
**File:** `docpivot/engine_builder.py` (new file ~150 lines)

```python
"""Builder pattern for DocPivotEngine configuration."""

from typing import Optional, Dict, Any
from docpivot.engine import DocPivotEngine


class DocPivotEngineBuilder:
    """Fluent builder for DocPivotEngine with advanced configuration."""

    def __init__(self):
        self._lexical_config = {}
        self._default_format = "lexical"
        self._custom_serializers = {}
        self._custom_readers = {}

    def with_lexical_config(self, config: Dict[str, Any]) -> 'DocPivotEngineBuilder':
        """Set Lexical serialization configuration."""
        self._lexical_config.update(config)
        return self

    def with_pretty_print(self, indent: int = 2) -> 'DocPivotEngineBuilder':
        """Enable pretty printing with specified indentation."""
        self._lexical_config["pretty"] = True
        self._lexical_config["indent"] = indent
        return self

    def with_default_format(self, format: str) -> 'DocPivotEngineBuilder':
        """Set the default output format."""
        self._default_format = format
        return self

    def with_custom_serializer(self, format: str, serializer) -> 'DocPivotEngineBuilder':
        """Register a custom serializer for a format."""
        self._custom_serializers[format] = serializer
        return self

    def build(self) -> DocPivotEngine:
        """Build the configured DocPivotEngine."""
        engine = DocPivotEngine(
            lexical_config=self._lexical_config,
            default_format=self._default_format
        )

        # Register custom serializers if any
        for format, serializer in self._custom_serializers.items():
            # Future: engine.register_serializer(format, serializer)
            pass

        return engine
```

### Task 3: Create Smart Defaults
**File:** `docpivot/defaults.py` (new file ~100 lines)

```python
"""Smart defaults for DocPivot operations."""

from typing import Dict, Any


def get_default_lexical_config() -> Dict[str, Any]:
    """Get default configuration for Lexical JSON serialization.

    Returns configuration that handles 90% of use cases.
    """
    return {
        "pretty": False,  # Compact by default
        "indent": 2,      # If pretty=True
        "include_metadata": True,
        "preserve_formatting": True,
        "handle_tables": True,
        "handle_lists": True,
        "handle_images": False,  # Skip images by default for smaller output
    }


def get_performance_config() -> Dict[str, Any]:
    """Get configuration optimized for performance."""
    return {
        "pretty": False,
        "include_metadata": False,
        "streaming": True,  # If supported
        "batch_size": 100,
    }


def get_debug_config() -> Dict[str, Any]:
    """Get configuration for debugging/development."""
    return {
        "pretty": True,
        "indent": 4,
        "include_metadata": True,
        "include_debug_info": True,
        "validate_output": True,
    }
```

### Task 4: Simplify Main API
**File:** `docpivot/__init__.py` (modify existing)

```python
"""DocPivot - Simple document format conversion for Docling."""

__version__ = "2.0.0"

# Core engine (primary interface)
from docpivot.engine import DocPivotEngine, ConversionResult
from docpivot.engine_builder import DocPivotEngineBuilder
from docpivot.defaults import (
    get_default_lexical_config,
    get_performance_config,
    get_debug_config,
)

# Legacy workflow functions (deprecated but maintained)
from docpivot.workflows import load_document, convert_document

# Specific implementations for advanced users
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.readers.lexicaljsonreader import LexicalJsonReader

__all__ = [
    # New simplified API (recommended)
    "DocPivotEngine",
    "ConversionResult",
    "DocPivotEngineBuilder",
    "get_default_lexical_config",
    "get_performance_config",
    "get_debug_config",

    # Legacy API (maintained for compatibility)
    "load_document",
    "convert_document",

    # Low-level components
    "LexicalDocSerializer",
    "DoclingJsonReader",
    "LexicalJsonReader",
]
```

## Phase 3: Testing and Examples (Day 2)

### Task 5: Create Simple Examples
**File:** `examples/simple_conversion.py`

```python
"""Simple document conversion with DocPivot."""

from pathlib import Path
from docling.document_converter import DocumentConverter
from docpivot import DocPivotEngine

# Initialize engine with defaults
engine = DocPivotEngine()

# Convert PDF to Lexical JSON
result = engine.convert_pdf("document.pdf")
print(f"Converted to {result.format}")
print(result.content[:500])  # First 500 chars

# Convert with pretty printing
result = engine.convert_pdf("document.pdf", pretty=True)
Path("output.json").write_text(result.content)

# From existing DoclingDocument
converter = DocumentConverter()
doc = converter.convert("document.pdf").document
result = engine.convert_to_lexical(doc)
```

**File:** `examples/advanced_configuration.py`

```python
"""Advanced configuration with builder pattern."""

from docpivot import DocPivotEngine

# Configure with builder
engine = DocPivotEngine.builder() \
    .with_pretty_print(indent=4) \
    .with_lexical_config({"include_images": True}) \
    .with_default_format("lexical") \
    .build()

# Use configured engine
result = engine.convert_pdf("complex_document.pdf")
print(f"Processed with custom config: {result.metadata}")
```

### Task 6: Create Comprehensive Tests
**File:** `tests/test_engine.py`

```python
"""Test suite for DocPivotEngine."""

import pytest
from docpivot import DocPivotEngine
from tests.fixtures import create_test_document


def test_simple_conversion():
    """Test basic conversion functionality."""
    engine = DocPivotEngine()
    doc = create_test_document()

    result = engine.convert_to_lexical(doc)
    assert result.format == "lexical"
    assert result.content is not None
    assert '"type"' in result.content


def test_pretty_print():
    """Test pretty printing option."""
    engine = DocPivotEngine()
    doc = create_test_document()

    compact = engine.convert_to_lexical(doc, pretty=False)
    pretty = engine.convert_to_lexical(doc, pretty=True)

    # Pretty version should be longer due to formatting
    assert len(pretty.content) > len(compact.content)


def test_builder_pattern():
    """Test engine configuration via builder."""
    engine = DocPivotEngine.builder() \
        .with_pretty_print(indent=4) \
        .build()

    doc = create_test_document()
    result = engine.convert_to_lexical(doc)

    # Should have indentation
    assert '\n    ' in result.content  # 4-space indent


def test_file_conversion():
    """Test file-to-file conversion."""
    engine = DocPivotEngine()

    # Test with sample file
    result = engine.convert_file(
        "tests/samples/test.docling.json",
        output_format="lexical"
    )

    assert result.format == "lexical"
    assert result.content is not None
```

## Phase 4: Deprecation and Migration (Day 2 Afternoon)

### Task 7: Add Deprecation Warnings
**File:** `docpivot/deprecated.py` (new file)

```python
"""Deprecated APIs with migration guidance."""

import warnings
from typing import Any
from docpivot.engine import DocPivotEngine

# Global engine instance for backward compatibility
_default_engine = None


def load_and_serialize(file_path: str, format: str = "lexical", **kwargs) -> str:
    """Deprecated. Use DocPivotEngine instead.

    Migration:
        # Old way
        result = load_and_serialize("file.pdf", "lexical")

        # New way
        engine = DocPivotEngine()
        result = engine.convert_file("file.pdf", "lexical")
    """
    warnings.warn(
        "load_and_serialize is deprecated. Use DocPivotEngine.convert_file() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    global _default_engine
    if _default_engine is None:
        _default_engine = DocPivotEngine()

    result = _default_engine.convert_file(file_path, format, **kwargs)
    return result.content
```

## Success Metrics

### Code Reduction
- **Target:** 30%+ reduction in lines of code
- **Remove:** Performance monitoring, complex error handling, plugins
- **Simplify:** Logging, validation, extensibility

### API Simplicity
- ✅ One-line conversion: `engine.convert_to_lexical(doc)`
- ✅ Smart defaults cover 90% of use cases
- ✅ Builder pattern for advanced users
- ✅ No monkey-patching of external classes

### Compatibility
- ✅ Legacy functions still work with deprecation warnings
- ✅ Clear migration path documented
- ✅ All existing tests pass

## Implementation Checklist

### Day 1: Core Implementation
- [ ] Phase 1: Remove unnecessary code (2 hours)
- [ ] Task 1: Create DocPivotEngine (2 hours)
- [ ] Task 2: Implement builder pattern (1 hour)
- [ ] Task 3: Create defaults system (1 hour)
- [ ] Task 4: Update package exports (30 min)

### Day 2: Testing and Polish
- [ ] Task 5: Create examples (1 hour)
- [ ] Task 6: Write comprehensive tests (2 hours)
- [ ] Task 7: Add deprecation layer (1 hour)
- [ ] Documentation updates (1 hour)
- [ ] Final testing and cleanup (1 hour)

## Key Differences from Original Plan

1. **No monkey-patching**: We don't modify DoclingDocument
2. **Cleanup first**: Remove 30% of code before adding features
3. **Single engine class**: DocPivotEngine instead of registration system
4. **Simpler API**: `engine.convert_to_lexical()` instead of `doc.export_to_lexical_json()`
5. **Less abstraction**: Direct, clear code instead of wrappers and compatibility layers
6. **Performance focus**: Remove performance monitoring overhead
7. **Proven pattern**: Follows successful CloakEngine architecture

## Risk Mitigation

1. **Breaking changes**: Maintain legacy functions with deprecation warnings
2. **User adoption**: Provide clear examples and migration guide
3. **Testing**: Comprehensive test suite before any release
4. **Documentation**: Update all docs with new patterns

## Expected Outcome

After implementation:
- **Codebase**: ~30% smaller, much simpler
- **API**: Clean, intuitive, one-line usage
- **Performance**: Faster due to less overhead
- **Maintenance**: Easier to understand and extend
- **User Experience**: Similar to successful CloakEngine pattern

This approach applies all the hard-won lessons from CloakPivot to create a simpler, better DocPivot.