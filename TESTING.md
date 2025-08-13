# DocPivot Testing Documentation

## Overview

DocPivot has a comprehensive test suite designed to ensure reliability and correctness of all functionality. The test suite achieves **93% code coverage** with 187 tests covering all major components.

## Test Structure

### Core Test Files

#### Unit Tests
- `test_basereader.py` - Base reader interface and common functionality
- `test_doclingjsonreader.py` - DoclingJsonReader implementation
- `test_lexicaljsonreader.py` - LexicalJsonReader implementation  
- `test_lexicaldocserializer.py` - LexicalDocSerializer implementation
- `test_readerfactory.py` - Format detection and reader factory
- `test_serializerprovider.py` - Serializer provider and integration
- `test_exceptions.py` - Error handling and custom exceptions

#### Integration Tests
- `test_readers_with_sample_data.py` - Reader testing with real sample files
- `test_serializers_with_sample_data.py` - Serializer testing with realistic documents
- `test_workflows_comprehensive.py` - End-to-end workflow testing
- `test_edge_cases_coverage.py` - Edge cases and coverage improvements

### Sample Data

The test suite uses real sample files located in `/data/`:
- `2025-07-03-Test-PDF-Styles.docling.json` - Sample Docling document
- `2025-07-03-Test-PDF-Styles.lexical.json` - Sample Lexical document  
- `2025-07-03-Test-PDF-Styles.pdf` - Original PDF for reference

## Test Categories

### 1. Reader Tests (45 tests)
Tests all document readers with both synthetic and real data:
- **Format Detection**: Automatic format detection for JSON files
- **Document Loading**: Loading and parsing various document formats
- **Error Handling**: File not found, malformed JSON, invalid schemas
- **Performance**: Load time benchmarks with sample data
- **Content Validation**: Ensuring loaded content matches expected structure

### 2. Serializer Tests (58 tests)  
Tests all serializers with realistic documents:
- **Format Output**: Correct serialization to target formats (markdown, HTML, lexical, doctags)
- **Content Preservation**: Text and structure preservation through transformations
- **Round-trip Conversions**: lexical → docling → lexical consistency
- **Custom Parameters**: Serializer parameter passing and customization
- **Quality Validation**: Output format compliance and structure validation

### 3. Workflow Tests (27 tests)
Tests high-level API functions:
- **Load Document**: Auto-detection and document loading
- **Load and Serialize**: Complete workflow in single function call
- **Convert Document**: File-to-file and file-to-string conversion
- **Error Propagation**: Error handling through complete pipeline
- **Performance**: End-to-end workflow timing benchmarks
- **Format Combinations**: All input format → output format combinations

### 4. Factory and Provider Tests (57 tests)
Tests factory and provider patterns:
- **Reader Factory**: Format detection, reader selection, registration
- **Serializer Provider**: Format-specific serializer instantiation
- **Integration**: Factory + Provider coordination
- **Error Handling**: Unsupported format handling and clear error messages

## Test Features

### Real Data Testing
All integration tests use actual sample files rather than synthetic data:
- Tests realistic document structures and content
- Validates transformations preserve meaningful content
- Ensures output quality meets real-world standards

### Performance Benchmarks
Performance tests establish baseline metrics:
- Reader loading times: < 200ms per document
- End-to-end workflows: < 500ms complete pipeline
- Format detection: < 10ms per file
- Memory usage monitoring for large documents

### Error Condition Coverage
Comprehensive error testing:
- File system errors (missing files, permissions)
- Format errors (malformed JSON, wrong schemas)
- API errors (invalid parameters, unsupported formats)
- Network/IO errors in various scenarios

### Quality Validation
Automated output quality checks:
- Markdown structure validation (headings, paragraphs, lists)
- HTML tag structure and compliance
- Lexical JSON schema validation
- Content preservation verification

## Running Tests

### Basic Test Execution
```bash
# Run all tests
python -m pytest tests/

# Run with verbose output  
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/test_workflows_comprehensive.py -v
```

### Coverage Reporting
```bash
# Generate coverage report
python -m pytest tests/ --cov=docpivot --cov-report=term-missing

# Generate HTML coverage report
python -m pytest tests/ --cov=docpivot --cov-report=html
# View at htmlcov/index.html
```

### Performance Testing
```bash
# Run only performance tests
python -m pytest tests/ -k "performance" -v

# Run with timing information
python -m pytest tests/ --durations=10
```

## Test Fixtures

The test suite uses pytest fixtures for consistent test data:

### File Fixtures
- `test_data_dir`: Path to sample data directory
- `sample_docling_json_path`: Path to Docling sample file
- `sample_lexical_json_path`: Path to Lexical sample file
- `temp_directory`: Temporary directory for test outputs
- `nonexistent_file`: Path to non-existent file for error testing

### Document Fixtures  
- `sample_docling_document`: Minimal DoclingDocument for unit testing
- `sample_docling_document_from_file`: Real document loaded from sample file
- `sample_lexical_document_from_file`: Real document from Lexical sample

## Coverage Analysis

Current coverage: **93%** (515 statements, 34 missing)

### High Coverage Modules (95%+)
- `workflows.py`: 100% - All workflow functions covered
- `exceptions.py`: 100% - All exception handling paths tested  
- `doclingjsonreader.py`: 98% - Comprehensive reader testing
- `serializerprovider.py`: 98% - Provider patterns well tested
- `lexicaljsonreader.py`: 97% - Complex transformation logic covered

### Lower Coverage Areas
- `lexicaldocserializer.py`: 86% - Complex serialization logic, some edge cases uncovered
- `basereader.py`: 92% - Abstract base class, some paths unreachable
- `readerfactory.py`: 93% - Factory pattern, some error paths uncovered

Missing coverage primarily consists of:
- Error handling paths in complex transformation logic
- Edge cases in format detection for unusual files
- Some defensive programming paths that are difficult to trigger

## Test Development Guidelines

### Writing New Tests
1. **Use Real Data**: Prefer sample files over synthetic data when possible
2. **Test Error Conditions**: Include negative test cases for each feature
3. **Performance Awareness**: Add timing assertions for performance-critical code
4. **Quality Validation**: Verify output quality, not just successful execution

### Test Organization
1. **Group Related Tests**: Use test classes to group related functionality
2. **Clear Test Names**: Test names should describe the specific scenario being tested
3. **Comprehensive Docstrings**: Each test should document what it validates
4. **Fixture Usage**: Leverage fixtures to reduce code duplication

### CI/CD Integration
Tests are designed to run reliably in CI environments:
- No external dependencies required
- Deterministic test execution
- Clear failure messages with actionable information
- Performance tests with reasonable tolerances

## Conclusion

The DocPivot test suite provides comprehensive coverage of all functionality with a focus on real-world usage scenarios. The combination of unit tests, integration tests, and performance benchmarks ensures the library works correctly and efficiently with actual document data.

The 93% coverage metric represents thorough testing of all main code paths, with remaining uncovered lines consisting primarily of edge case error handling that is difficult to trigger in normal usage.