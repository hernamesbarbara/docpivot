# DOCPIVOT_000006: LexicalDocSerializer Core Implementation

Refer to ./specification/index.md

## Objective

Implement LexicalDocSerializer to convert DoclingDocument objects to Lexical JSON format, following Docling's serializer patterns and API design.

## Requirements

- Extend BaseDocSerializer from docling-core
- Transform DoclingDocument elements to Lexical JSON node structure
- Support basic text elements (headings, paragraphs, text runs)
- Follow Docling's constructor and serialize() method patterns
- Return SerializationResult with .text containing JSON string

## Implementation Details

### Core Transformation Logic
- Map DoclingDocument text elements to Lexical paragraph nodes
- Map DoclingDocument headings to Lexical heading nodes with appropriate tag (h1-h6)
- Handle text formatting and basic styles
- Generate valid Lexical JSON structure with root node

### Lexical JSON Structure
```json
{
  "root": {
    "children": [
      {
        "type": "heading",
        "tag": "h1", 
        "children": [{"type": "text", "text": "..."}]
      },
      {
        "type": "paragraph",
        "children": [{"type": "text", "text": "..."}]
      }
    ],
    "direction": null,
    "format": "",
    "indent": 0,
    "type": "root",
    "version": 1
  }
}
```

### API Design
```python
class LexicalDocSerializer(BaseDocSerializer):
    def __init__(self, doc: DoclingDocument, **kwargs):
        # Follow Docling constructor pattern
        
    def serialize(self) -> SerializationResult:
        # Return SerializationResult with JSON string in .text
```

### Element Mapping Strategy
- DoclingDocument.texts → Lexical paragraph nodes
- DoclingDocument.headings → Lexical heading nodes  
- Preserve text content and basic formatting
- Handle document structure and hierarchy
- Generate appropriate Lexical metadata

### Testing Strategy
- Use DoclingJsonReader to load sample data for transformation
- Test basic text and heading conversion
- Validate JSON structure against Lexical format
- Test with various DoclingDocument structures
- Compare output with existing .lexical.json sample

### Acceptance Criteria

- [ ] LexicalDocSerializer class extending BaseDocSerializer
- [ ] Constructor follows Docling patterns (doc parameter, optional configs)
- [ ] serialize() returns SerializationResult with valid JSON
- [ ] Basic text elements (paragraphs, headings) convert correctly
- [ ] Generated JSON matches Lexical format specification
- [ ] Text content preserved accurately
- [ ] Document structure maintained
- [ ] Registered with SerializerProvider as "lexical" format
- [ ] Full test coverage with sample data

## Notes

This is the core value-add for DocPivot - enabling Lexical JSON output. The implementation must handle the fundamental differences between Docling's element-based model and Lexical's node-based structure.