# Changelog

## [2.0.1] - 2024-09-15

### 🔧 Project Configuration Improvements

Simplified project configuration and tooling setup for better maintainability.

### Changed
- **Consolidated configuration in `pyproject.toml`**
  - Moved all mypy configuration from `mypy.ini` to `[tool.mypy]`
  - Single `dev` dependency group (removed redundant test/lint/all groups)
  - Removed standalone isort config (using ruff's integrated isort)
  - Explicit mypy `files = ["docpivot", "tests"]` instead of path configs
- **Makefile as single command hub**
  - `make all` - Single CI/CD entry point
  - `make check` - Quick pre-commit validation
  - Removed `run_tests.sh` (redundant with Makefile)
- **Improved examples**
  - Reduced from 17 scattered examples to 4 focused ones
  - Added `pdf_conversion.py` demonstrating PDF → multiple formats
  - All examples now showcase v2.0 simplified API
- **Documentation updates**
  - Updated README.md to highlight v2.0 simplified API
  - Added PROJECT_CONFIG.md documenting configuration philosophy
  - Updated TESTING.md with TDD workflow and pragmatic testing approach

### Fixed
- Fixed `duration` variable bug in `lexicaldocserializer.py`
- Fixed safe attribute access for `document.body.items` in `engine.py`
- Removed references to deleted modules in mypy config

### Removed
- `mypy.ini` (moved to pyproject.toml)
- `run_tests.sh` (use Makefile instead)
- 13 outdated example files
- Redundant dependency groups (test/lint/all)
- Standalone isort configuration

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