# DOCPIVOT_000008: End-to-End Workflows and Integration

Refer to ./specification/index.md

## Objective

Create high-level API functions that combine readers and serializers into complete workflows, matching the usage patterns shown in the PRD examples.

## Requirements

- Implement high-level convenience functions for common workflows
- Support reader → serializer pipelines with automatic format detection
- Create API that matches PRD example usage patterns
- Enable both simple and customized serialization flows
- Provide clear error handling for the complete pipeline

## Implementation Details

### High-Level API Functions
```python
def load_and_serialize(input_path: str, output_format: str, **kwargs) -> SerializationResult:
    """Load document and serialize to target format in one call"""
    pass

def convert_document(input_path: str, output_format: str, output_path: str = None, **kwargs):
    """Complete conversion with optional file output"""
    pass
```

### Workflow Patterns
1. **Auto-detection workflow**: file_path → detect format → load → serialize
2. **Explicit reader workflow**: reader_class + file_path → load → serialize  
3. **Custom serializer workflow**: reader → custom serializer with parameters → serialize
4. **Batch processing workflow**: multiple inputs → same output format

### Integration Points
- Use ReaderFactory for automatic reader selection
- Use SerializerProvider for serializer instantiation  
- Support all serializer parameters and component customization
- Handle file I/O for complete file-to-file conversion

### Example Usage Implementation
Must support all PRD examples:

```python
# Basic Markdown Export (PRD example)
from docpivot import load_and_serialize
result = load_and_serialize("sample.docling.json", "markdown")
print(result.text)

# Customized Markdown Export (PRD example)  
from docpivot import load_document, SerializerProvider
doc = load_document("sample.docling.json")
serializer = SerializerProvider().get_serializer(
    "markdown", 
    doc=doc,
    params=MarkdownParams(image_placeholder="(no image)")
)
result = serializer.serialize()
```

### Error Handling Strategy
- Propagate reader errors (file not found, format detection)
- Propagate serializer errors (unsupported format, invalid parameters)  
- Add workflow-specific errors (incompatible reader/serializer combinations)
- Provide helpful error messages with suggested solutions

### Performance Considerations
- Minimize file I/O operations
- Support streaming for large documents
- Cache reader/serializer instances where appropriate
- Provide progress callbacks for batch operations

### Testing Strategy
- Test all PRD example usage patterns
- Test error propagation through complete pipeline
- Test with sample data files end-to-end
- Test performance with large documents
- Test batch processing scenarios

### Acceptance Criteria

- [ ] High-level API functions implemented  
- [ ] All PRD example usage patterns work correctly
- [ ] Auto-detection + serialization workflow functional
- [ ] Custom serializer parameter passing works
- [ ] Error handling covers complete pipeline
- [ ] File-to-file conversion supports all formats
- [ ] Performance acceptable for typical document sizes
- [ ] Full test coverage of workflow scenarios
- [ ] API documentation matches PRD examples

## Notes

This is the user-facing API that makes DocPivot easy to use. The implementation should feel natural to users familiar with Docling while adding the extended format support seamlessly.