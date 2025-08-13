# DOCPIVOT_000003: Implement DoclingJsonReader

Refer to ./docs/prd.md

## Objective

Implement DoclingJsonReader to load .docling.json files into DoclingDocument objects, providing the simpler of the two readers as a foundation.

## Requirements

- Extend BaseReader to handle .docling.json format
- Load JSON and reconstruct DoclingDocument
- Handle DoclingDocument schema validation
- Provide comprehensive error handling for malformed files
- Test with existing sample data

## Implementation Details

### Core Functionality
- Read .docling.json files
- Parse JSON content
- Validate DoclingDocument schema
- Reconstruct full DoclingDocument object
- Handle file I/O errors gracefully

### Schema Handling
Based on sample data analysis:
- schema_name: "DoclingDocument"
- version: "1.4.0"
- Structured content with body, furniture, texts, etc.

### Testing Strategy
- Use `/data/json/2025-07-03-Test-PDF-Styles.docling.json` for testing
- Validate that loaded document matches expected structure
- Test error cases (missing files, malformed JSON, invalid schema)

### Acceptance Criteria

- [ ] DoclingJsonReader class implemented extending BaseReader
- [ ] Successfully loads sample .docling.json file
- [ ] Returns valid DoclingDocument object
- [ ] Handles file not found errors gracefully
- [ ] Handles malformed JSON gracefully
- [ ] Validates DoclingDocument schema
- [ ] Full test coverage with sample data
- [ ] Follows Docling naming and error handling patterns

## Notes

This is the simpler reader implementation and should be completed first to validate the BaseReader design and establish patterns for LexicalJsonReader.