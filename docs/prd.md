# DocPivot Product Requirements Document (PRD)

## Overview

**DocPivot** is a lightweight Python package that extends the functionality of [Docling](https://docling.io/) by enabling seamless conversion of rich-text documents to and from a variety of file formats not natively supported by Docling. It serves as a bridge for formats such as Lexical JSON, alternative Markdown dialects, and other JSON variants, while leveraging Docling’s powerful `DoclingDocument` model and APIs.

### Purpose

DocPivot simplifies the process of loading, transforming, and serializing rich-text documents across diverse formats. It adopts Docling’s design patterns, abstractions, and naming conventions to ensure consistency and ease of integration, providing a mini-SDK for developers to handle both Docling-supported and non-supported formats.

### Scope

- **Input Formats**: Extend Docling’s input capabilities to include additional JSON dialects (e.g., Lexical JSON) and other text-based formats.
- **Output Formats**: Support serialization to additional formats like Lexical JSON, beyond Docling’s native Markdown, HTML, JSON, Text, and DocTags.
- **Core Functionality**: Read documents into `DoclingDocument`, transform them, and serialize to target formats.
- **Design Principle**: Reuse Docling’s abstractions (e.g., `BaseDocSerializer`, `BaseReader`) to avoid redundant implementations.

## Background

### Docling Capabilities

Docling is a powerful tool for parsing and converting documents into a unified `DoclingDocument` model. Its key features include:

- **Supported Input Formats**: PDF, DOCX, XLSX, PPTX, Markdown, AsciiDoc, HTML, XHTML, CSV, PNG, JPG, TIFF, BMP, WEBP.
- **Supported Output Formats**: HTML, Markdown, JSON (Docling-specific), Text, DocTags.
- **Serialization**: Uses a hierarchy of serializers (`BaseDocSerializer`, `BaseTextSerializer`, etc.) to convert `DoclingDocument` into textual representations.
- **Limitations**: Limited to specific dialects of Markdown and JSON, lacking support for formats like Lexical JSON used in React’s Lexical editor.

### DocPivot’s Role

DocPivot extends Docling by:
- Adding support for reading non-native formats (e.g., Lexical JSON).
- Providing serializers for additional output formats.
- Maintaining Docling’s class hierarchy and API patterns for seamless integration.

## Requirements

### Functional Requirements

1. **Readers**:
   - Implement `DoclingJsonReader` to load Docling JSON files into `DoclingDocument`.
   - Implement `LexicalJsonReader` to convert Lexical JSON into `DoclingDocument`.
   - Provide a `BaseReader` class for extensibility, allowing custom readers for other formats.
   - Intelligently detect input file formats based on file extension or content analysis.

2. **Serializers**:
   - Reuse Docling’s `MarkdownDocSerializer` and `DocTagsDocSerializer` for native formats.
   - Implement `LexicalDocSerializer` for serializing `DoclingDocument` to Lexical JSON.
   - Support extensible serializers via a `BaseDocSerializer` subclass for custom formats (e.g., HTML, alternative Markdown dialects).

3. **Serializer Provider**:
   - Implement a `SerializerProvider` to instantiate the appropriate serializer based on the requested format (e.g., "markdown", "lexical", "doctags").
   - Allow registration of custom serializers for future extensibility.

4. **Core API**:
   - Provide a simple, Docling-inspired API for loading, transforming, and serializing documents.
   - Ensure compatibility with Docling’s `DocumentConverter` and `DoclingDocument` models.

5. **Extensibility**:
   - Allow developers to add custom readers and serializers by subclassing `BaseReader` and `BaseDocSerializer`.
   - Support dynamic registration of new formats in the `SerializerProvider`.

### Non-Functional Requirements

- **Performance**: Conversion and serialization should be efficient, leveraging Docling’s optimized pipeline.
- **Compatibility**: Fully compatible with Docling’s latest version and its `docling-core` library.
- **Maintainability**: Follow Docling’s naming conventions, class hierarchies, and design patterns to ensure consistency.
- **Usability**: Provide clear documentation and example usage for developers.
- **Error Handling**: Gracefully handle unsupported formats with meaningful error messages.

## Design Patterns

DocPivot will adopt Docling’s design patterns to ensure consistency:

- **Reader Pattern**: Use `BaseReader` as an abstract base class for format-specific readers (e.g., `DoclingJsonReader`, `LexicalJsonReader`).
- **Serializer Pattern**: Use `BaseDocSerializer` for format-specific serializers, with a `serialize()` method returning a `SerializationResult` (text and optional spans).
- **Factory Pattern**: Implement `SerializerProvider` as a factory to return the appropriate serializer based on the requested format.
- **Extensibility**: Support custom readers and serializers via subclassing and registration.

## API Specification

### Key Classes and Methods

1. **Readers**:
   - `BaseReader`:
     - Abstract method: `load_data(file_path: str, **kwargs) -> DoclingDocument`
   - `DoclingJsonReader(BaseReader)`:
     - Loads Docling JSON into `DoclingDocument`.
   - `LexicalJsonReader(BaseReader)`:
     - Converts Lexical JSON to `DoclingDocument`.

2. **Serializers**:
   - `BaseDocSerializer`:
     - Abstract method: `serialize(doc: DoclingDocument, **kwargs) -> SerializationResult`
   - `LexicalDocSerializer(BaseDocSerializer)`:
     - Serializes `DoclingDocument` to Lexical JSON.
   - Reuse Docling’s `MarkdownDocSerializer` and `DocTagsDocSerializer`.

3. **SerializerProvider**:
   - Method: `get_serializer(format: str) -> BaseDocSerializer`
   - Method: `register_serializer(format: str, serializer: BaseDocSerializer)`

### Example Usage

```python
from pathlib import Path
from docpivot.io.readers import DoclingJsonReader, LexicalJsonReader
from docpivot.io.serializers import SerializerProvider

# Load a Docling JSON file
docling_reader = DoclingJsonReader()
doc = docling_reader.load_data("data/2025-07-03-Test-PDF-Styles.docling.json")

# Serialize to Markdown
provider = SerializerProvider()
md_serializer = provider.get_serializer("markdown")
markdown_out = md_serializer.serialize(doc).text
Path("output.md").write_text(markdown_out, encoding="utf-8")

# Load a Lexical JSON file
try:
    lexical_reader = LexicalJsonReader()
    doc = lexical_reader.load_data("data/sample.lexical.json")
except NotImplementedError as e:
    print(f"Error: {e}")

# Serialize to Lexical JSON
lexical_serializer = provider.get_serializer("lexical")
lexical_out = lexical_serializer.serialize(doc).text
Path("output.lexical.json").write_text(lexical_out, encoding="utf-8")
```

### Extending DocPivot

#### Custom Reader
```python
from docpivot.io.readers.basereader import BaseReader
from docling_core.types.doc.document import DoclingDocument

class CustomReader(BaseReader):
    def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
        raw_data = ...  # Read custom format
        return DoclingDocument.model_validate(raw_data)
```

#### Custom Serializer
```python
from docling_core.transforms.serializer.base import BaseDocSerializer, SerializationResult

class CustomSerializer(BaseDocSerializer):
    def serialize(self, doc: DoclingDocument, **kwargs) -> SerializationResult:
        text = ...  # Convert to custom format
        return SerializationResult(text=text, spans=[])

# Register custom serializer
provider = SerializerProvider()
provider.register_serializer("custom", CustomSerializer)
```

## Implementation Notes

- **Dependencies**: Rely on `docling-core` for `DoclingDocument`, `BaseDocSerializer`, `BaseReader`, and other core abstractions.
- **File Structure**:
  ```
  docpivot/
  ├── io/
  │   ├── readers/
  │   │   ├── basereader.py
  │   │   ├── doclingjsonreader.py
  │   │   ├── lexicaljsonreader.py
  │   ├── serializers/
  │   │   ├── serializerprovider.py
  │   │   ├── lexicaldocserializer.py
  ├── __init__.py
  ├── example.py
  ```
- **Format Detection**: Implement logic to detect input formats based on file extensions (e.g., `.docling.json`, `.lexical.json`) or content signatures.
- **Error Handling**: Raise `NotImplementedError` for unsupported formats, with clear messages guiding users to extend functionality.

## Status

| Capability                              | Module / Class                         | Status         |
|-----------------------------------------|----------------------------------------|----------------|
| Read *.docling.json* → `DoclingDocument`| `DoclingJsonReader`                    | ✅ Stable       |
| Read *.lexical.json* → `DoclingDocument`| `LexicalJsonReader`                    | 🚧 In Progress  |
| Serialize to Markdown                   | `MarkdownDocSerializer` (Docling)      | ✅ Stable       |
| Serialize to DocTags                   | `DocTagsDocSerializer` (Docling)       | ✅ Stable       |
| Serialize to Lexical JSON               | `LexicalDocSerializer`                 | ⚠️ Prototype   |

## Next Steps

- Implement `LexicalJsonReader` to parse Lexical JSON into `DoclingDocument`.
- Develop `LexicalDocSerializer` for valid Lexical JSON output compatible with the Lexical editor.
- Add format detection logic for automatic input format identification.
- Provide comprehensive documentation and examples in a `README.md`.