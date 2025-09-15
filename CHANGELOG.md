# Changelog

## [2.0.0] - 2024-09-15

### 🎉 Major Refactoring - Simplified API

Complete overhaul based on CloakPivot learnings to create a simpler, cleaner codebase.

### Added
- **New `DocPivotEngine` class** - Primary API for document conversion
  - One-line conversion: `engine.convert_to_lexical(doc)`
  - Direct PDF support: `engine.convert_pdf(pdf_path)`
  - File conversion: `engine.convert_file(input_path, output_path)`
- **`DocPivotEngineBuilder`** - Fluent builder pattern for configuration
  - `DocPivotEngine.builder().with_pretty_print().build()`
  - Performance and debug modes
- **Smart defaults module** (`defaults.py`)
  - `get_default_lexical_config()` - Handles 90% of use cases
  - `get_performance_config()` - Optimized for speed
  - `get_debug_config()` - Maximum information for debugging
  - `get_minimal_config()`, `get_full_config()`, `get_web_config()`
- **Clean test suite** - Single focused test file with 13 tests

### Removed (30%+ code reduction)
- ❌ `performance/` module - Removed monitoring, benchmarks, profilers
- ❌ `plugins.py` - Removed plugin system
- ❌ `optimized_lexical_serializer.py` - Removed redundant optimizer
- ❌ `workflows.py` - Removed complex workflow functions
- ❌ `extensibility.py` - Removed over-engineered extensibility
- ❌ 28 old test files - Replaced with single clean test suite
- ❌ `PerformanceLogger` - Simplified to basic Python logging

### Changed
- Simplified `logging_config.py` to basic Python logging (~75% smaller)
- Updated `__init__.py` exports to focus on new API
- Made `docling` package optional (for PDF conversion only)
- Removed all deprecation warnings (no backward compatibility needed)

### Technical Improvements
- No monkey-patching of external classes
- Lazy initialization for better performance
- Optional dependencies handled gracefully
- Cleaner error messages
- Consistent API design

## [1.0.0] - Previous Version

Initial implementation with extensive features including performance monitoring, plugin system, and complex workflow functions.