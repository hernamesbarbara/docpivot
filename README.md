# DocPivot

DocPivot is a lightweight Python package that extends the functionality of [Docling](https://docling.io/) by enabling seamless conversion of rich-text documents to and from a variety of file formats not natively supported by Docling. It serves as a bridge for formats such as Lexical JSON, alternative Markdown dialects, and other JSON variants, while leveraging Docling's powerful `DoclingDocument` model and APIs.

## Features

- 📄 **Extended Format Support**: Read Lexical JSON and Docling JSON into unified document model
- 🔄 **Multi-Format Export**: Serialize to Markdown, HTML, Lexical JSON, and more
- 🎛️ **Configurable Serialization**: Customize output with parameters and component serializers
- 🏗️ **Extensible Architecture**: Easy to add support for new formats
- 🚀 **Docling Compatible**: Built on Docling's proven abstractions and patterns

## Supported Formats

| Format | Input | Output | Status |
|--------|--------|--------|--------|
| Docling JSON | ✅ | ✅ | Stable |
| Lexical JSON | ✅ | ✅ | Stable |
| Markdown | ➖ | ✅ | Via Docling |
| HTML | ➖ | ✅ | Via Docling |
| Text | ➖ | ✅ | Via Docling |
| DocTags | ➖ | ✅ | Via Docling |

## Installation

### From PyPI (when available)
```bash
pip install docpivot
```

### Development Installation
```bash
git clone https://github.com/your-org/docpivot.git
cd docpivot
pip install -e .
```

### Dependencies
- Python 3.8+
- docling-core
- pydantic

## Quick Start

### Basic Document Loading and Conversion

```python
from docpivot import load_and_serialize

# Convert Docling JSON to Markdown
result = load_and_serialize("document.docling.json", "markdown")
print(result.text)

# Convert Lexical JSON to HTML
result = load_and_serialize("document.lexical.json", "html")
print(result.text)
```

### Advanced Usage with Custom Configuration

```python
from docpivot import load_document, SerializerProvider
from docling_core.transforms.serializer.markdown import MarkdownParams

# Load document
doc = load_document("document.docling.json")

# Configure serializer with custom parameters
serializer = SerializerProvider().get_serializer(
    "markdown",
    doc=doc,
    params=MarkdownParams(image_placeholder="[Image]")
)

result = serializer.serialize()
print(result.text)
```

### Lexical JSON Export

```python
from docpivot.io.readers import DoclingJsonReader
from docpivot.io.serializers import LexicalDocSerializer

# Load document
reader = DoclingJsonReader()
doc = reader.load_data("document.docling.json")

# Serialize to Lexical JSON
serializer = LexicalDocSerializer(doc=doc)
result = serializer.serialize()
print(result.text)  # Valid Lexical JSON
```

## Core Components

### Readers
- `DoclingJsonReader`: Load Docling JSON files into DoclingDocument
- `LexicalJsonReader`: Convert Lexical JSON to DoclingDocument
- `BaseReader`: Base class for implementing custom readers

### Serializers
- `LexicalDocSerializer`: Export DoclingDocument to Lexical JSON
- Built-in Docling serializers: `MarkdownDocSerializer`, `HTMLDocSerializer`, `TextDocSerializer`

### Utilities
- `ReaderFactory`: Automatic format detection and reader selection
- `SerializerProvider`: Get configured serializers by format name
- High-level API functions: `load_document()`, `load_and_serialize()`

## Examples

The `examples/` directory contains comprehensive usage patterns:

- [`basic_usage/`](examples/basic_usage/): Simple conversion workflows
- [`advanced_usage/`](examples/advanced_usage/): Custom serializers and batch processing
- [`integration_examples/`](examples/integration_examples/): Custom readers and testing patterns

### Running Examples

```bash
# Basic examples
cd examples
python basic_usage/basic_markdown_export.py
python basic_usage/lexical_export.py

# Advanced examples  
python advanced_usage/custom_serializers.py
python advanced_usage/batch_processing.py
```

## API Reference

### High-Level API

```python
from docpivot import load_document, load_and_serialize

# Load any supported document format
doc = load_document(file_path)

# One-step load and convert
result = load_and_serialize(input_file, output_format)
```

### Reader API

```python
from docpivot.io.readers import DoclingJsonReader, LexicalJsonReader

reader = DoclingJsonReader()
doc = reader.load_data("document.docling.json")
```

### Serializer API

```python
from docpivot.io.serializers import LexicalDocSerializer
from docpivot.io.serializers.lexicaldocserializer import LexicalParams

# Basic usage
serializer = LexicalDocSerializer(doc=doc)
result = serializer.serialize()

# With configuration
params = LexicalParams(indent_json=True, include_metadata=True)
serializer = LexicalDocSerializer(doc=doc, params=params)
result = serializer.serialize()
```

## Extending DocPivot

### Custom Readers

```python
from docpivot.io.readers import BaseReader
from docling_core.types import DoclingDocument

class MyFormatReader(BaseReader):
    def can_read(self, file_path: str) -> bool:
        return file_path.endswith('.myformat')
    
    def load_data(self, file_path: str) -> DoclingDocument:
        # Implementation here
        pass
```

### Custom Serializers

```python
from docpivot.io.serializers import BaseDocSerializer

class MyFormatSerializer(BaseDocSerializer):
    def serialize(self) -> SerializationResult:
        # Implementation here
        pass
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install -e .[test]

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=docpivot --cov-report=html
```

## Performance

DocPivot is designed for efficiency:

- Streaming JSON processing for large documents
- Minimal memory overhead during conversion
- Configurable output formatting to optimize for size vs readability

For performance optimization tips, see [`examples/advanced_usage/performance_optimization.py`](examples/advanced_usage/performance_optimization.py).

## Contributing

We welcome contributions! Please see:

- [Contributing Guidelines](CONTRIBUTING.md)
- [Development Setup](docs/development.md)
- [Architecture Overview](docs/architecture.md)

### Development Setup

```bash
git clone https://github.com/your-org/docpivot.git
cd docpivot
pip install -e .[dev]
pre-commit install
```

## Troubleshooting

### Common Issues

**Q: "UnsupportedFormatError" when loading files**
A: Ensure your file has the correct extension (`.docling.json` or `.lexical.json`) or use the ReaderFactory for automatic detection.

**Q: Lexical JSON output is not valid**
A: Check that your input document has valid structure. Enable `indent_json=True` in LexicalParams for debugging.

**Q: Performance issues with large documents**
A: Use streaming mode and disable unnecessary features like metadata inclusion.

For more troubleshooting tips, see [docs/troubleshooting.md](docs/troubleshooting.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the excellent [Docling](https://docling.io/) framework
- Inspired by Docling's clean API design and extensible architecture
- Thanks to the Docling team for creating a solid foundation

## Related Projects

- [Docling](https://docling.io/) - The core document processing framework
- [docling-core](https://github.com/DS4SD/docling-core) - Core document models and transforms