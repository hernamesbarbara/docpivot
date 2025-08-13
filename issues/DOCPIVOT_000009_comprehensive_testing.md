# DOCPIVOT_000009: Comprehensive Testing with Sample Data

Refer to ./specification/index.md

## Objective

Create comprehensive test suite covering all components using the provided sample data, ensuring reliability and correctness of all DocPivot functionality.

## Requirements

- Test all readers with sample data files
- Test all serializers with realistic DoclingDocument objects
- Test end-to-end workflows with actual file conversion
- Test error conditions and edge cases
- Validate output quality and format compliance
- Add performance benchmarks

## Implementation Details

### Test Data Organization
Use existing sample files:
- `/data/json/2025-07-03-Test-PDF-Styles.docling.json` - for DoclingJsonReader testing
- `/data/json/2025-07-03-Test-PDF-Styles.lexical.json` - for LexicalJsonReader testing and output validation
- `/data/pdf/2025-07-03-Test-PDF-Styles.pdf` - for reference and additional testing

### Reader Test Coverage
```python
class TestDoclingJsonReader:
    def test_load_sample_docling_json(self):
        # Test loading sample file
        
    def test_docling_document_structure(self):
        # Validate loaded document structure
        
    def test_error_handling(self):
        # Test malformed JSON, missing files

class TestLexicalJsonReader:  
    def test_load_sample_lexical_json(self):
        # Test loading sample file
        
    def test_lexical_to_docling_mapping(self):
        # Validate transformation correctness
```

### Serializer Test Coverage
```python
class TestLexicalDocSerializer:
    def test_docling_to_lexical_conversion(self):
        # Load docling.json, convert to lexical format
        
    def test_output_format_compliance(self):
        # Validate against Lexical JSON schema
        
    def test_round_trip_conversion(self):
        # lexical → docling → lexical consistency
```

### Integration Test Coverage
```python
class TestEndToEndWorkflows:
    def test_docling_to_markdown(self):
        # docling.json → MarkdownDocSerializer
        
    def test_lexical_to_markdown(self):
        # lexical.json → MarkdownDocSerializer
        
    def test_docling_to_lexical(self):
        # docling.json → LexicalDocSerializer
        
    def test_auto_format_detection(self):
        # Test ReaderFactory with sample files
```

### Quality Validation Tests
- Compare generated Lexical JSON with sample file structure
- Validate text content preservation through transformations
- Test formatting preservation (headings, paragraphs, styles)
- Validate JSON schema compliance for all outputs

### Performance Testing
```python
class TestPerformance:
    def test_reader_performance(self):
        # Benchmark reading large documents
        
    def test_serializer_performance(self):  
        # Benchmark serialization speed
        
    def test_memory_usage(self):
        # Monitor memory consumption
```

### Error Condition Testing
- File not found scenarios
- Malformed JSON input files
- Invalid DoclingDocument objects  
- Unsupported format requests
- Network/file system errors
- Large file handling

### Test Fixtures and Utilities
```python
@pytest.fixture
def sample_docling_document():
    # Load sample docling.json as DoclingDocument
    
@pytest.fixture  
def sample_lexical_document():
    # Load sample lexical.json as DoclingDocument

def assert_valid_lexical_json(json_str: str):
    # Validate Lexical JSON format compliance
```

### Acceptance Criteria

- [ ] All readers tested with sample data
- [ ] All serializers tested with realistic documents
- [ ] Round-trip conversion testing (where applicable)
- [ ] End-to-end workflow testing covers all format combinations
- [ ] Error conditions comprehensively tested
- [ ] Performance benchmarks established
- [ ] Output quality validation automated
- [ ] Test coverage > 95% for all components
- [ ] Tests run reliably in CI environment
- [ ] Clear test documentation and examples

## Notes

This comprehensive testing ensures DocPivot works correctly with real-world data and provides confidence for production use. The tests should serve as living documentation of expected behavior.