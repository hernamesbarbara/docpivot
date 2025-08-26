# DOCPIVOT_000001: Project Setup and Foundation

Refer to ./docs/prd.md

## Objective

Set up the basic Python package structure for DocPivot according to the PRD specifications and establish the development environment.

## Requirements

- Create Python package structure matching PRD layout
- Set up pyproject.toml with dependencies including docling-core
- Create __init__.py files with proper exports
- Set up basic testing infrastructure
- Create .gitignore entries for Python development

## Implementation Details

### Directory Structure to Create
```
docpivot/
├── __init__.py
├── io/
│   ├── __init__.py
│   ├── readers/
│   │   ├── __init__.py
│   │   └── basereader.py
│   └── serializers/
│       ├── __init__.py
│       └── serializerprovider.py
├── tests/
│   ├── __init__.py
│   └── conftest.py
└── examples/
    └── __init__.py
```

### Dependencies
- docling-core (primary dependency)
- pytest (for testing)
- Standard library only for initial implementation

### Acceptance Criteria

- [ ] Directory structure matches PRD specification
- [ ] pyproject.toml configured with correct dependencies
- [ ] Basic imports work without errors
- [ ] pytest can discover and run (empty) test suite
- [ ] Project can be installed in development mode

## Notes

This establishes the foundation for all subsequent development. The structure must exactly match the PRD to ensure consistency with Docling patterns.

## Proposed Solution

Based on the PRD specification, I will implement the following steps:

1. **Create pyproject.toml** - Configure Python package with docling-core dependency and pytest for testing
2. **Create docpivot package structure** - Follow PRD layout with io/readers and io/serializers subdirectories  
3. **Implement __init__.py files** - Proper exports for clean imports
4. **Create BaseReader class** - Foundation for extensible document readers
5. **Create SerializerProvider class** - Factory pattern for serializer instantiation
6. **Set up test infrastructure** - pytest configuration and conftest.py
7. **Add .gitignore** - Python-specific ignores including __pycache__, .pytest_cache
8. **Validate installation** - Ensure dev mode install works
9. **Validate testing** - Ensure pytest can discover and run tests

This establishes the exact structure specified in the PRD while following Docling patterns for extensibility.

## Implementation Complete

All acceptance criteria have been met:

- ✅ Directory structure matches PRD specification exactly
- ✅ pyproject.toml configured with docling-core and pytest dependencies
- ✅ Basic imports work without errors (`from docpivot import BaseReader, SerializerProvider`)
- ✅ pytest can discover and run (empty) test suite
- ✅ Project can be installed in development mode (`pip install -e .`)

### Implemented Components

1. **pyproject.toml** - Complete package configuration with dependencies
2. **docpivot/** - Main package with proper `__init__.py` exports
3. **docpivot/io/readers/** - Reader module with `BaseReader` class
4. **docpivot/io/serializers/** - Serializer module with `SerializerProvider` class  
5. **tests/** - Test infrastructure with pytest fixtures
6. **examples/** - Examples directory ready for future content
7. **.gitignore** - Updated with Python and MCP-specific entries

### Validation Results

- Package installs successfully in development mode
- All imports work correctly
- SerializerProvider works with Docling's MarkdownDocSerializer, DocTagsDocSerializer, and HTMLDocSerializer
- pytest discovers tests correctly (0 tests found as expected)
- Foundation is ready for next development phase

Ready for DOCPIVOT_000002_base_reader implementation.