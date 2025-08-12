# DocPivot Product Requirements Document (PRD)

## Overview

**DocPivot** is a lightweight Python package that extends the functionality of [Docling](https://docling.io/) by enabling seamless conversion of rich-text documents to and from a variety of file formats not natively supported by Docling. It serves as a bridge for formats such as Lexical JSON, alternative Markdown dialects, and other JSON variants, while leveraging Docling’s powerful `DoclingDocument` model and APIs.

### Purpose

DocPivot simplifies the process of loading, transforming, and serializing rich-text documents across diverse formats. It adopts Docling’s design patterns, abstractions, and naming conventions to ensure consistency and ease of integration, providing a mini-SDK for developers to handle both Docling-supported and non-supported formats.

### Scope

- **Input Formats**: Extend Docling’s input capabilities to include additional JSON dialects (e.g., Lexical JSON) and other text-based formats.
- **Output Formats**: Support serialization to additional formats like Lexical JSON, beyond Docling’s native Markdown, HTML, JSON, Text, and DocTags.
- **Core Functionality**: Read documents into `DoclingDocument`, transform them, and serialize to target formats using the same instantiation/configuration patterns as Docling.
- **Design Principle**: Reuse Docling’s abstractions (`BaseDocSerializer`, `BaseReader`) to avoid redundant implementations.

## Background

### Docling Capabilities

Docling parses and converts documents into a unified `DoclingDocument` model with:

- **Supported Input Formats**: PDF, DOCX, XLSX, PPTX, Markdown, AsciiDoc, HTML, XHTML, CSV, PNG, JPG, TIFF, BMP, WEBP.
- **Supported Output Formats**: HTML, Markdown, JSON (Docling-specific), Text, DocTags.
- **Serialization**: Serializer classes are instantiated with the `DoclingDocument` and optional parameters or component serializers.
- **Limitations**: No native support for formats like Lexical JSON.

### DocPivot’s Role

DocPivot extends Docling by:
- Adding support for reading non-native formats (e.g., Lexical JSON).
- Providing serializers for additional output formats.
- Maintaining Docling’s class hierarchy, API style, and instantiation patterns for seamless integration.

## Requirements

### Functional Requirements

1. **Readers**:
   - Implement `DoclingJsonReader` to load `.docling.json` into `DoclingDocument`.
   - Implement `LexicalJsonReader` to convert Lexical JSON into `DoclingDocument`.
   - Provide a `BaseReader` class for extensibility, allowing custom readers for other formats.
   - Detect formats by file extension or content signature.

2. **Serializers**:
   - Follow Docling’s serializer usage pattern:
     - Instantiate with `doc=DoclingDocument`, plus optional component serializers or parameter objects.
     - Call `.serialize()` to return a `SerializationResult` with `.text` and optional `.spans`.
   - Reuse Docling’s built-in serializers where possible (`MarkdownDocSerializer`, `DocTagsDocSerializer`, `HTMLDocSerializer`, `TextDocSerializer`).
   - Implement `LexicalDocSerializer` for serializing `DoclingDocument` to Lexical JSON.
   - Support user-configurable parameters (e.g., `MarkdownParams`, `HTMLParams`) and pluggable component serializers (e.g., custom picture/table serializers).

3. **Serializer Provider**:
   - Implement `SerializerProvider` to return an instantiated serializer given a format string.
   - Allow registration of new serializers, following Docling’s instantiation style.

4. **Core API**:
   - Provide Docling-inspired methods for:
     - `load_data` (via a reader)
     - `serialize` (via a serializer instantiated with `doc=...`)
   - Maintain API parity with `DocumentConverter` → `serializer.serialize()` flow.

5. **Extensibility**:
   - Allow custom serializers with the same constructor signature (`doc`, optional params, optional component serializers).
   - Allow custom readers by subclassing `BaseReader`.

### Non-Functional Requirements

- **Performance**: Serialization should remain as efficient as Docling’s base serializers.
- **Compatibility**: Full compatibility with Docling’s `docling-core`.
- **Maintainability**: Match Docling’s naming conventions, instantiation patterns, and module structure.
- **Usability**: Include examples for both simple and customized serialization flows.
- **Error Handling**: Raise clear errors for unsupported formats.

## Design Patterns

DocPivot mirrors Docling’s patterns:

- **Reader Pattern**: `BaseReader` for format-specific loaders.
- **Serializer Pattern**: `BaseDocSerializer` subclasses for output formats.
- **Configuration Pattern**: Pass optional parameter objects and component serializers at instantiation.
- **Factory Pattern**: `SerializerProvider` returns fully-configured serializer instances.

## API Specification

### Key Classes and Methods

**Readers**
- `BaseReader.load_data(file_path: str, **kwargs) -> DoclingDocument`
- `DoclingJsonReader(BaseReader)`
- `LexicalJsonReader(BaseReader)`

**Serializers**
- `BaseDocSerializer.serialize(doc, **kwargs) -> SerializationResult`
- `LexicalDocSerializer(BaseDocSerializer)`
- Built-in serializers reused from Docling: `MarkdownDocSerializer`, `DocTagsDocSerializer`, `HTMLDocSerializer`, `TextDocSerializer`.

**SerializerProvider**
- `get_serializer(format: str, **kwargs) -> BaseDocSerializer`
- `register_serializer(format: str, serializer_cls: type[BaseDocSerializer])`

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

## Example Usage

### Basic Markdown Export
```python
from docpivot.io.readers import DoclingJsonReader
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer

doc = DoclingJsonReader().load_data("sample.docling.json")

serializer = MarkdownDocSerializer(doc=doc)
ser_result = serializer.serialize()
print(ser_result.text)
```

### Customized Markdown Export
```python
from docling_core.transforms.chunker.hierarchical_chunker import TripletTableSerializer
from docling_core.transforms.serializer.markdown import MarkdownParams, MarkdownDocSerializer

serializer = MarkdownDocSerializer(
    doc=doc,
    table_serializer=TripletTableSerializer(),
    params=MarkdownParams(image_placeholder="(no image)")
)
ser_result = serializer.serialize()
print(ser_result.text)
```

### Lexical Export
```python
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer

serializer = LexicalDocSerializer(doc=doc)
ser_result = serializer.serialize()
print(ser_result.text)
```

### Custom Picture Serializer
```python
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from my_custom.picture_serializer import AnnotationPictureSerializer

serializer = MarkdownDocSerializer(
    doc=doc,
    picture_serializer=AnnotationPictureSerializer(),
)
ser_result = serializer.serialize()
print(ser_result.text)
```

---

## Status

| Capability                              | Module / Class                         | Status         |
|-----------------------------------------|----------------------------------------|----------------|
| Read *.docling.json* → `DoclingDocument`| `DoclingJsonReader`                    | ✅ Stable       |
| Read *.lexical.json* → `DoclingDocument`| `LexicalJsonReader`                    | 🚧 In Progress  |
| Serialize to Markdown                   | `MarkdownDocSerializer` (Docling)      | ✅ Stable       |
| Serialize to DocTags                    | `DocTagsDocSerializer` (Docling)       | ✅ Stable       |
| Serialize to HTML                       | `HTMLDocSerializer` (Docling)          | ✅ Stable       |
| Serialize to Text                       | `TextDocSerializer` (Docling)          | ✅ Stable       |
| Serialize to Lexical JSON               | `LexicalDocSerializer`                 | ⚠️ Prototype   |

## Next Steps

- Implement `LexicalJsonReader`.
- Implement `LexicalDocSerializer`.
- Integrate Docling-style parameter/configuration patterns in all DocPivot serializers.
- Add automatic format detection.
- Document advanced customization patterns for component serializers.
