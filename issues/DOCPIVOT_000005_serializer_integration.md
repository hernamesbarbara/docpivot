# DOCPIVOT_000005: Serializer Integration and Provider Setup

Refer to ./specification/index.md

## Objective

Integrate docling-core serializers and create the SerializerProvider infrastructure to register and instantiate serializers following Docling patterns.

## Requirements

- Import and integrate existing docling-core serializers (MarkdownDocSerializer, DocTagsDocSerializer, HTMLDocSerializer, TextDocSerializer)
- Implement SerializerProvider class with registration and retrieval methods
- Support Docling's instantiation patterns with doc parameter and optional configurations
- Provide factory methods for serializer creation
- Add format string to serializer class mapping

## Implementation Details

### SerializerProvider Class
```python
class SerializerProvider:
    def get_serializer(self, format: str, **kwargs) -> BaseDocSerializer:
        """Get instantiated serializer for format"""
        pass
    
    def register_serializer(self, format: str, serializer_cls: type[BaseDocSerializer]):
        """Register new serializer class for format"""
        pass
```

### Built-in Format Support
- "markdown" → MarkdownDocSerializer
- "html" → HTMLDocSerializer  
- "text" → TextDocSerializer
- "doctags" → DocTagsDocSerializer

### Configuration Pattern
- Support parameter objects (MarkdownParams, HTMLParams, etc.)
- Support component serializers (picture_serializer, table_serializer)
- Match Docling's constructor signature: `doc=DoclingDocument`, optional params, optional components

### Testing Strategy
- Test all built-in serializer registrations
- Test SerializerProvider.get_serializer() with various formats
- Test parameter passing to serializers
- Test unknown format error handling
- Use DoclingJsonReader output for serializer testing

### Acceptance Criteria

- [ ] SerializerProvider class implemented
- [ ] All docling-core serializers registered by default  
- [ ] get_serializer() returns properly instantiated serializers
- [ ] register_serializer() allows custom serializer registration
- [ ] Parameter and component serializer support working
- [ ] Clear error messages for unknown formats
- [ ] Full test coverage with sample data
- [ ] API matches Docling instantiation patterns

## Notes

This establishes the serialization foundation that LexicalDocSerializer will plug into. The provider pattern enables extensibility while maintaining Docling compatibility.