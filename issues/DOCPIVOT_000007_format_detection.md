# DOCPIVOT_000007: Format Detection and Reader Selection

Refer to ./specification/index.md

## Objective

Implement robust format detection to automatically select the appropriate reader based on file extensions and content signatures.

## Requirements

- Detect .docling.json files for DoclingJsonReader
- Detect .lexical.json files for LexicalJsonReader  
- Add content-based detection for ambiguous cases
- Provide clear error messages for unsupported formats
- Create reader factory with automatic selection
- Handle edge cases and malformed files gracefully

## Implementation Details

### Format Detection Strategy
```python
class ReaderFactory:
    def get_reader(self, file_path: str) -> BaseReader:
        """Automatically select reader based on file format"""
        pass
    
    def detect_format(self, file_path: str) -> str:
        """Detect file format from extension and content"""
        pass
```

### Detection Rules
- **Extension-based**: `.docling.json` → DoclingJsonReader
- **Extension-based**: `.lexical.json` → LexicalJsonReader  
- **Content-based**: Check JSON structure for ambiguous `.json` files
  - Look for `schema_name: "DoclingDocument"` for Docling format
  - Look for `root.children` structure for Lexical format
- **Fallback**: Clear error message for unknown formats

### Content Signature Detection
For generic `.json` files:
```python
def _detect_json_content(self, file_path: str) -> str:
    # Load JSON and check structure
    # Return "docling" or "lexical" or raise error
```

### Error Handling
- FileNotFoundError for missing files
- JSONDecodeError for malformed JSON  
- UnsupportedFormatError for unknown formats
- Clear error messages guiding users to supported formats

### Integration with Existing Readers
- Update BaseReader with format detection capability
- Add ReaderFactory as main entry point
- Maintain backward compatibility with direct reader instantiation

### Testing Strategy
- Test extension-based detection with sample files
- Test content-based detection with renamed files
- Test error cases (missing files, malformed JSON, unknown formats)
- Test integration with existing readers
- Test with edge cases (empty files, invalid JSON, mixed content)

### Acceptance Criteria

- [ ] ReaderFactory class implemented
- [ ] get_reader() automatically selects correct reader
- [ ] detect_format() works with file extensions
- [ ] Content-based detection works for generic .json files
- [ ] Clear error messages for unsupported formats
- [ ] Graceful handling of malformed files
- [ ] Integration with DoclingJsonReader and LexicalJsonReader
- [ ] Full test coverage including edge cases
- [ ] Documentation for supported formats and detection rules

## Notes

This creates a user-friendly interface where users don't need to know the specific reader class - they can just provide a file path and get the appropriate reader automatically.

## Proposed Solution

Based on analysis of the existing codebase, I will implement the format detection and reader selection system as follows:

### 1. LexicalJsonReader Implementation
- Create `LexicalJsonReader` class that extends `BaseReader`
- Implement format detection for `.lexical.json` files and content-based detection for generic `.json` files
- Convert Lexical JSON structure (with `root.children` hierarchy) to `DoclingDocument`
- Handle nested Lexical nodes (paragraphs, headings, lists, tables) and convert them to corresponding Docling elements

### 2. ReaderFactory Implementation  
- Create `ReaderFactory` class with `get_reader()` and `detect_format()` methods
- Implement automatic reader selection based on file extensions and content signatures
- Support format detection rules:
  - `.docling.json` → `DoclingJsonReader`
  - `.lexical.json` → `LexicalJsonReader`  
  - Generic `.json` files → content-based detection by checking JSON structure

### 3. Exception Handling
- Add `UnsupportedFormatError` exception class for clear error reporting
- Provide helpful error messages that guide users to supported formats
- Handle malformed files and edge cases gracefully

### 4. Integration Strategy
- Follow existing patterns from `DoclingJsonReader` for consistency
- Maintain backward compatibility with direct reader instantiation
- Use same testing patterns and error handling approaches
- Add comprehensive test coverage including edge cases

### 5. Implementation Steps
1. Create `LexicalJsonReader` with format detection capability
2. Implement `ReaderFactory` with automatic reader selection
3. Add `UnsupportedFormatError` exception class  
4. Write comprehensive tests for all components
5. Update module exports and documentation

This approach maintains consistency with existing code patterns while providing the robust format detection capabilities required by the issue.

## Implementation Completed ✅

### What Was Implemented

1. **LexicalJsonReader** (`lexicaljsonreader.py`)
   - Extends BaseReader with comprehensive format detection
   - Supports `.lexical.json` files and content-based detection for generic `.json` files
   - Converts Lexical JSON hierarchical structure to DoclingDocument referenced elements
   - Handles paragraphs, headings, lists, and tables with proper DoclingDocument schema compliance
   - Includes robust error handling for malformed files and edge cases

2. **ReaderFactory** (`readerfactory.py`)
   - Automatic reader selection based on file extensions and content signatures
   - `get_reader()` method for automatic reader instantiation
   - `detect_format()` method for format identification
   - Extensible design allowing registration of custom readers
   - Built-in support for "docling" and "lexical" formats

3. **UnsupportedFormatError** (`exceptions.py`)
   - Custom exception class extending ValueError
   - Clear error messages guiding users to supported formats
   - Configurable supported formats list for context-specific errors

### Format Detection Rules Implemented

- **Extension-based detection:**
  - `.docling.json` → DoclingJsonReader
  - `.lexical.json` → LexicalJsonReader
  
- **Content-based detection for generic `.json` files:**
  - Looks for `schema_name: "DoclingDocument"` for Docling format
  - Looks for `root.children` structure for Lexical format
  
- **Error handling:** Clear error messages for unknown formats

### Test Coverage

- **51 comprehensive tests** covering all new components
- Edge cases: malformed files, missing files, invalid JSON, schema validation
- Integration tests: ReaderFactory with both reader types
- Real data testing: Successfully processes actual Lexical JSON files

### Usage Examples

Created `examples/format_detection_example.py` demonstrating:
- Automatic format detection and reader selection
- Error handling for unsupported formats
- Direct reader usage patterns
- Integration with existing codebase

### Integration

- Updated module exports in `__init__.py`
- Maintains backward compatibility with existing code
- Follows established patterns from DoclingJsonReader
- Full integration with Docling's DoclingDocument model

### Verification

- All new tests passing (51/51)
- Successfully processes real Lexical JSON files from `data/` directory  
- ReaderFactory correctly identifies and instantiates appropriate readers
- Error handling provides helpful user guidance

The format detection system is now fully operational and ready for production use.