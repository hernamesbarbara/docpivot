# DOCPIVOT_000004: Implement LexicalJsonReader

Refer to ./docs/prd.md

## Objective

Implement LexicalJsonReader to convert Lexical JSON format into DoclingDocument objects, handling the complex transformation between Lexical's node-based structure and Docling's document model.

## Requirements

- Extend BaseReader to handle .lexical.json format
- Transform Lexical node structure to DoclingDocument format
- Map Lexical node types (heading, paragraph, text) to Docling elements
- Handle nested structures and formatting
- Provide comprehensive error handling

## Implementation Details

### Lexical Format Analysis
Based on sample data:
```json
{
  "root": {
    "children": [
      {
        "tag": "h1",
        "type": "heading",
        "children": [{"type": "text", "text": "..."}]
      },
      {
        "type": "paragraph", 
        "children": [{"type": "text", "text": "..."}]
      }
    ]
  }
}
```

### Transformation Logic
- Map Lexical "heading" nodes to Docling heading elements
- Map Lexical "paragraph" nodes to Docling text elements  
- Handle nested text formatting and styles
- Preserve document structure and hierarchy
- Generate appropriate Docling document metadata

### Key Challenges
- Different data models: Lexical uses nested nodes, Docling uses referenced elements
- Text formatting preservation
- Document structure mapping
- Metadata generation for DoclingDocument

### Testing Strategy
- Use `/data/json/2025-07-03-Test-PDF-Styles.lexical.json` for testing
- Validate transformation produces valid DoclingDocument
- Test various Lexical node types and structures
- Compare output with expected Docling format

### Acceptance Criteria

- [ ] LexicalJsonReader class implemented extending BaseReader
- [ ] Successfully transforms sample .lexical.json file
- [ ] Returns valid DoclingDocument object
- [ ] Preserves text content and basic formatting
- [ ] Maps document structure correctly (headings, paragraphs)
- [ ] Handles malformed Lexical JSON gracefully
- [ ] Full test coverage with sample data
- [ ] Transformation logic is well-documented

## Notes

This is the most complex reader implementation due to the significant differences between Lexical and Docling data models. The transformation logic will be critical for the project's success.