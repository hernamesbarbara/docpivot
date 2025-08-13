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