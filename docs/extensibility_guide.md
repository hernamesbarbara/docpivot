# DocPivot Extensibility Guide

This guide explains how to extend DocPivot with custom readers and serializers for new file formats.

## Overview

DocPivot provides a comprehensive extensibility system that allows you to:

- Create custom readers to support new input formats
- Create custom serializers to support new output formats
- Bundle formats into plugins for easy distribution
- Validate and test your implementations

## Quick Start

### Creating a Custom Serializer

```python
from docpivot.io.serializers.custom_serializer_base import CustomSerializerBase
from docling_core.transforms.serializer.base import SerializationResult

class MyFormatSerializer(CustomSerializerBase):
    @property
    def output_format(self) -> str:
        return "myformat"
    
    @property
    def file_extension(self) -> str:
        return ".myformat"
    
    def serialize(self) -> SerializationResult:
        # Convert document to your format
        content = self._serialize_text_content()
        return SerializationResult(text=content)
```

### Creating a Custom Reader

```python
from docpivot.io.readers.custom_reader_base import CustomReaderBase
from docling_core.types import DoclingDocument

class MyFormatReader(CustomReaderBase):
    @property
    def supported_extensions(self) -> List[str]:
        return ['.myformat']
    
    @property
    def format_name(self) -> str:
        return "My Format"
    
    def can_handle(self, file_path: Union[str, Path]) -> bool:
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def load_data(self, file_path: Union[str, Path], **kwargs) -> DoclingDocument:
        # Parse your format and create DoclingDocument
        return self._create_empty_document()  # Implement your parsing
```

### Registering Your Formats

```python
from docpivot.io.format_registry import get_format_registry

registry = get_format_registry()
registry.register_reader("myformat", MyFormatReader)
registry.register_serializer("myformat", MyFormatSerializer)
```

## Detailed Guides

### [Custom Reader Development](./custom_reader_guide.md)
Learn how to create readers for new input formats.

### [Custom Serializer Development](./custom_serializer_guide.md)
Learn how to create serializers for new output formats.

### [Plugin Development](./plugin_development_guide.md)
Learn how to package your formats as plugins.

### [Testing Your Formats](./testing_guide.md)
Learn how to test and validate your implementations.

## Architecture Overview

DocPivot's extensibility system consists of:

1. **Base Classes**: `CustomReaderBase` and `CustomSerializerBase` provide templates
2. **Format Registry**: Central registration and discovery system
3. **Plugin System**: Modular format packaging and loading
4. **Validation Framework**: Comprehensive testing and validation
5. **Integration Points**: Seamless integration with existing DocPivot APIs

## Best Practices

### Design Principles

- **Follow Docling Patterns**: Use the same instantiation and parameter patterns as Docling
- **Comprehensive Interface**: Implement all required methods and properties
- **Error Handling**: Provide clear error messages and handle edge cases gracefully
- **Documentation**: Include comprehensive docstrings and examples

### Implementation Guidelines

- Use type hints for all methods and properties
- Validate inputs and provide meaningful error messages
- Support optional parameters and component serializers
- Include metadata and capability information
- Test thoroughly with the provided testing framework

### Performance Considerations

- Minimize memory usage for large documents
- Use streaming where possible
- Cache expensive operations
- Consider concurrent processing for batch operations

## Examples

The `examples/custom_formats/` directory contains complete working examples:

- `yaml_serializer.py`: YAML output serializer
- `xml_reader.py`: XML input reader  
- `example_plugin.py`: Plugin combining both

## API Reference

### Core Classes

- [`CustomReaderBase`](../docpivot/io/readers/custom_reader_base.py): Base class for readers
- [`CustomSerializerBase`](../docpivot/io/serializers/custom_serializer_base.py): Base class for serializers
- [`FormatRegistry`](../docpivot/io/format_registry.py): Central format registry
- [`FormatPlugin`](../docpivot/io/plugins.py): Plugin base class
- [`FormatValidator`](../docpivot/io/validation.py): Validation framework

### Testing Framework

- [`CustomFormatTestBase`](../docpivot/io/testing.py): Base class for format tests
- [`FormatTestSuite`](../docpivot/io/testing.py): Comprehensive test runner

## Migration Guide

If you have existing custom formats, see the [Migration Guide](./migration_guide.md) for information on updating them to use the new extensibility system.

## Troubleshooting

Common issues and solutions:

### Validation Errors

- Ensure all required methods are implemented
- Check that properties return correct types
- Verify error handling for edge cases

### Registration Issues

- Check that classes extend the correct base classes
- Ensure format names are unique
- Verify plugin loading paths and imports

### Performance Issues

- Use profiling to identify bottlenecks
- Consider streaming for large documents
- Cache expensive operations

## Contributing

To contribute to DocPivot's extensibility system:

1. Follow the development guidelines
2. Add comprehensive tests
3. Update documentation
4. Submit pull requests with clear descriptions

## Support

For questions and support:

- Check the [FAQ](./faq.md)
- Review existing examples
- Run the validation framework on your implementations
- Open issues on the project repository