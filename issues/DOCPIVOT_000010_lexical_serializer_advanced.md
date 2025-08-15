# DOCPIVOT_000010: Advanced Lexical Serializer Features

Refer to ./specification/index.md

## Objective

Enhance LexicalDocSerializer with advanced features including formatting preservation, nested structures, and configuration options to match Docling's serializer sophistication.

## Requirements

- Support complex text formatting (bold, italic, links)
- Handle nested document structures (lists, tables, sections)  
- Add configuration parameters for output customization
- Support component serializers for specialized elements
- Implement advanced Lexical JSON features (marks, attributes)

## Implementation Details

### Advanced Text Formatting
```python
# Support Lexical text marks for formatting
{
  "type": "text",
  "text": "bold text",
  "format": ["bold"]
}

{
  "type": "text", 
  "text": "italic text",
  "format": ["italic"]
}
```

### Nested Structure Support
- **Lists**: Convert DoclingDocument list elements to Lexical list nodes
- **Tables**: Handle table structures with rows/columns
- **Links**: Preserve hyperlinks with proper Lexical link nodes
- **Images**: Convert image elements to Lexical image nodes

### Configuration Parameters
```python
class LexicalParams:
    include_metadata: bool = True
    preserve_formatting: bool = True
    indent_json: bool = False
    version: int = 1

class LexicalDocSerializer(BaseDocSerializer):
    def __init__(self, doc: DoclingDocument, params: LexicalParams = None, **kwargs):
        # Support parameter configuration like other Docling serializers
```

### Component Serializer Support
```python
# Support custom serializers for specific elements
class CustomImageSerializer:
    def serialize_image(self, image_element) -> dict:
        # Custom Lexical image node generation
        
serializer = LexicalDocSerializer(
    doc=doc,
    image_serializer=CustomImageSerializer()
)
```

### Lexical JSON Advanced Features
- **Direction**: Support text direction (LTR/RTL)
- **Indentation**: Handle nested content indentation
- **Attributes**: Support custom element attributes
- **Versions**: Handle different Lexical format versions

### Element Mapping Enhancements
- **DoclingDocument.images** → Lexical image nodes
- **DoclingDocument.tables** → Lexical table structures
- **DoclingDocument.lists** → Lexical list nodes  
- **Text formatting** → Lexical text marks
- **Links and references** → Lexical link nodes

### Testing Strategy
- Test complex documents with multiple formatting types
- Test nested structures (lists within lists, etc.)
- Test configuration parameter effects
- Test component serializer customization
- Compare with Docling serializer patterns for consistency

### Performance Optimization
- Efficient handling of large documents
- Minimize JSON generation overhead  
- Optimize nested structure processing
- Memory-efficient text formatting handling

### Acceptance Criteria

- [ ] Advanced text formatting (bold, italic, links) supported
- [ ] Nested structures (lists, tables) convert correctly
- [ ] LexicalParams configuration class implemented
- [ ] Component serializer support functional
- [ ] Complex sample documents serialize correctly
- [ ] Output matches advanced Lexical JSON specification
- [ ] Performance acceptable for large, complex documents
- [ ] API consistency with Docling serializer patterns
- [ ] Full test coverage for advanced features

## Notes

This elevates LexicalDocSerializer from basic functionality to production-ready with full feature parity with Docling's built-in serializers. The implementation should handle real-world document complexity.

## Proposed Solution

After analyzing the existing codebase and requirements, I will enhance the LexicalDocSerializer with the following approach:

### 1. Configuration Parameters (LexicalParams class)
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class LexicalParams:
    """Configuration parameters for LexicalDocSerializer"""
    include_metadata: bool = True
    preserve_formatting: bool = True
    indent_json: bool = True
    version: int = 1
    custom_root_attributes: Optional[dict] = None
```

### 2. Advanced Text Formatting Support
- Implement text format detection from DoclingDocument text styles/attributes
- Support Lexical format marks: ["bold"], ["italic"], ["underline"], ["strikethrough"]
- Parse and convert inline formatting from source documents

### 3. Enhanced Node Creation
- Extend existing _create_text_node methods to handle text formatting
- Add support for link nodes with href attributes
- Implement image node generation from DoclingDocument images
- Support nested structures within text blocks

### 4. Component Serializer Architecture
- Add constructor parameters for custom serializers (image_serializer, table_serializer, etc.)
- Create abstract interfaces for component serializers
- Allow pluggable serializers following Docling patterns

### 5. Advanced Lexical Features
- Support for text direction (LTR/RTL)
- Custom element attributes
- Version management
- Indentation controls
- Root-level metadata

### 6. Implementation Steps
1. Create LexicalParams dataclass
2. Enhance constructor to accept params and component serializers
3. Extend text processing for advanced formatting
4. Add link and image node support
5. Implement component serializer delegation
6. Add comprehensive testing

This approach maintains backward compatibility while significantly enhancing functionality to match Docling's serializer sophistication.