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

## Proposed Solution ✅ COMPLETED

Successfully implemented DoclingJsonReader with the following features:

### Core Implementation
- **File**: `docpivot/io/readers/doclingjsonreader.py`
- **Class**: `DoclingJsonReader` extending `BaseReader`
- **Dependencies**: Uses `DoclingDocument.model_validate()` from docling-core
- **Format Detection**: Supports both `.docling.json` and generic `.json` files with DoclingDocument content

### Key Features
1. **Format Detection**:
   - Automatic detection of `.docling.json` files
   - Content-based detection for generic `.json` files
   - Validates DoclingDocument schema markers in file content

2. **Loading Process**:
   - Reads and parses JSON content
   - Validates DoclingDocument schema structure
   - Uses Pydantic model validation for robust parsing
   - Creates properly structured DoclingDocument objects

3. **Error Handling**:
   - File existence validation
   - JSON syntax validation
   - Schema validation (checks for required fields)
   - Pydantic ValidationError handling
   - Clear error messages with guidance

4. **Testing**:
   - **File**: `tests/test_doclingjsonreader.py`
   - **Coverage**: 98% line coverage
   - **Tests**: 25 comprehensive test cases covering:
     - Format detection (various file types and extensions)
     - Successful loading of valid documents
     - Error handling for all failure modes
     - Edge cases (unreadable files, malformed JSON, etc.)

### Validation with Sample Data
Successfully tested with `/data/json/2025-07-03-Test-PDF-Styles.docling.json`:
- ✅ Document loaded: "2025-07-03-Test-PDF-Styles"
- ✅ Schema: DoclingDocument v1.4.0  
- ✅ Content: 20 texts, 2 groups, 2 pages
- ✅ All structural elements properly preserved

### Usage Example
```python
from docpivot.io.readers import DoclingJsonReader

reader = DoclingJsonReader()
doc = reader.load_data("sample.docling.json")
print(f"Loaded: {doc.name}")
```

All acceptance criteria have been met:
- [x] DoclingJsonReader class implemented extending BaseReader
- [x] Successfully loads sample .docling.json file
- [x] Returns valid DoclingDocument object
- [x] Handles file not found errors gracefully
- [x] Handles malformed JSON gracefully  
- [x] Validates DoclingDocument schema
- [x] Full test coverage with sample data
- [x] Follows Docling naming and error handling patterns