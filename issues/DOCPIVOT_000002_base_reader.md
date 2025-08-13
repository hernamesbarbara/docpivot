# DOCPIVOT_000002: Implement BaseReader Abstract Class

Refer to ./docs/prd.md

## Objective

Create the BaseReader abstract class that provides the foundation for all document readers in DocPivot, following Docling's patterns.

## Requirements

- Implement BaseReader as abstract base class
- Define load_data method signature matching PRD specification
- Add format detection capabilities
- Provide extensibility patterns for custom readers
- Add comprehensive error handling

## Implementation Details

### BaseReader Specification
```python
class BaseReader(ABC):
    @abstractmethod
    def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
        """Load document from file_path into DoclingDocument"""
        pass
    
    def detect_format(self, file_path: str) -> bool:
        """Detect if this reader can handle the given file"""
        pass
```

### Format Detection
- Check file extensions (.docling.json, .lexical.json)
- Optional content-based detection for ambiguous cases
- Return clear error messages for unsupported formats

### Dependencies
- docling-core for DoclingDocument
- ABC from abc module
- pathlib for file handling

### Acceptance Criteria

- [ ] BaseReader class defined with proper abstractions
- [ ] load_data method signature matches PRD
- [ ] Format detection works for known extensions
- [ ] Clear error messages for unsupported formats
- [ ] Full test coverage for base functionality
- [ ] Documentation follows Docling patterns

## Notes

This class provides the template that DoclingJsonReader and LexicalJsonReader will implement. The design must be extensible for future reader implementations.