# DocPivot Testing Documentation

## Testing Philosophy

DocPivot follows a **pragmatic Test-Driven Development (TDD)** approach optimized for a single-developer project. We prioritize:

1. **TDD for new features** - Write tests first when adding functionality
2. **90%+ coverage target** - Focus on code paths that matter
3. **Fast test execution** - Full suite runs in <120 seconds
4. **Simplicity over complexity** - Maintainable tests that catch real bugs

## TDD Workflow

### 1. Write Test First
```python
# tests/test_engine.py
def test_new_feature():
    """Test that new feature works as expected."""
    engine = DocPivotEngine()
    result = engine.new_feature()  # This doesn't exist yet
    assert result == expected_value
```

### 2. Run Failing Test
```bash
# Run specific test and stop on first failure
pytest tests/test_engine.py::test_new_feature -xvs
```

### 3. Implement Minimal Code
Write just enough code to make the test pass.

### 4. Verify Test Passes
```bash
# Run again to confirm
pytest tests/test_engine.py::test_new_feature -xvs
```

### 5. Refactor with Confidence
Clean up implementation knowing tests will catch regressions.

### 6. Check Coverage
```bash
# Quick coverage check
pytest --cov=docpivot --cov-report=term:skip-covered -q
```

## Test Structure (Simplified for v2.0)

After the v2.0 refactor that removed 30% of the codebase, tests are organized into three focused files:

### Core Test Files

```
tests/
├── test_docpivot_engine.py      # Core engine tests (unit + integration)
├── test_integration.py           # End-to-end with real files (if needed)
└── test_performance.py           # Performance benchmarks (optional)
```

### Current Test Suite
- **test_docpivot_engine.py** - 13 tests covering all major DocPivotEngine functionality
  - Engine initialization with defaults
  - Custom configuration
  - File conversion
  - PDF conversion (when docling available)
  - Builder pattern tests
  - Configuration presets

### Legacy Tests (to be cleaned up)
The `tests_old/` directory contains 28 test files from v1.0 that need review and potential removal.

## Running Tests

### Quick Test Run (<10 seconds)
```bash
# Run core tests only
pytest tests/test_docpivot_engine.py -q

# Run with minimal output
pytest tests/ -q
```

### Full Test Run with Coverage
```bash
# Run all tests with coverage report
pytest tests/ --cov=docpivot --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=docpivot --cov-report=html
open htmlcov/index.html  # View in browser
```

### Performance Testing
```bash
# Run with timing information
pytest tests/ --durations=10

# Run only performance-related tests
pytest tests/ -k "performance" -v
```

### Fast Test Execution
Use the Makefile for all test operations:

```bash
# Run tests with coverage (full report)
make test

# Run tests quickly without coverage
make test-fast

# Generate HTML coverage report
make coverage

# Run all checks (format, lint, type, test)
make all

# Quick pre-commit check
make check
```

The Makefile ensures consistent test execution and includes timing information.

## Pragmatic Testing Strategy

### What to Test
✅ **DO Test:**
- Public API methods (`convert_to_lexical`, `convert_file`, `convert_pdf`)
- Format conversions with real sample files
- Configuration and builder patterns
- Error handling for common user mistakes
- Round-trip conversions (document → lexical → document)

❌ **DON'T Test:**
- Internal helper methods (unless complex)
- Defensive code paths that never execute
- External library behavior (trust docling, pydantic)
- Getters/setters without logic
- Academic edge cases with no real-world relevance

### Test Types Priority

1. **Integration Tests** (High Value)
   - Test complete workflows with real files
   - Catch most bugs with least effort
   - Example: PDF → Lexical JSON conversion

2. **Unit Tests** (Medium Value)
   - Test complex business logic
   - Test error conditions
   - Example: Configuration merging, format detection

3. **Performance Tests** (Low Value)
   - Only for critical paths
   - Use reasonable tolerances
   - Example: Large document processing

### Using Doctest for Documentation
Combine documentation with testing:

```python
def convert_to_lexical(self, document: DoclingDocument) -> ConversionResult:
    """Convert a DoclingDocument to Lexical format.

    >>> engine = DocPivotEngine()
    >>> result = engine.convert_to_lexical(doc)
    >>> assert result.format == "lexical"
    """
```

Run doctests:
```bash
pytest --doctest-modules docpivot/
```

## Coverage Guidelines

### Current Status
- **Target**: 90% coverage
- **Focus**: Test code paths that users will actually hit
- **Ignore**: Defensive programming, unreachable code

### Coverage Commands
```bash
# Quick coverage check
pytest --cov=docpivot --cov-report=term:skip-covered

# Detailed missing lines
pytest --cov=docpivot --cov-report=term-missing

# Coverage with specific file
pytest --cov=docpivot.engine tests/test_docpivot_engine.py
```

### Excluding Code from Coverage
Mark code that doesn't need testing:

```python
if TYPE_CHECKING:  # pragma: no cover
    import SomeType

def defensive_check():  # pragma: no cover
    """This should never happen in practice."""
    raise RuntimeError("Unreachable")
```

## Test Data

### Sample Files Location
```
data/
├── pdf/
│   └── email.pdf                    # Sample PDF for testing
├── json/
│   ├── sample.docling.json         # Docling format sample
│   └── sample.lexical.json         # Lexical format sample
```

### Creating Test Fixtures
```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_pdf():
    """Return path to sample PDF."""
    return Path("data/pdf/email.pdf")

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install -e ".[dev]"
    - run: make all  # Single CI entry point
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running pre-commit checks..."
make check || exit 1
```

## Test Maintenance

### When to Add Tests
- **Always** when adding new features (TDD)
- When fixing bugs (regression tests)
- When refactoring complex code

### When to Remove Tests
- Test is redundant with other tests
- Feature being tested was removed
- Test is brittle and provides no value
- Test takes >5 seconds for marginal benefit

### Test Review Checklist
- [ ] Test name clearly describes what is being tested
- [ ] Test has single responsibility
- [ ] Test runs quickly (<1s for unit, <5s for integration)
- [ ] Test failure message is helpful for debugging
- [ ] Test doesn't depend on test execution order

## Performance Benchmarks

### Targets
- Unit tests: <100ms each
- Integration tests: <5s each
- Full test suite: <120s total
- Coverage report generation: <10s

### Monitoring Test Performance
```bash
# Find slow tests
pytest --durations=10

# Profile specific test
python -m cProfile -s time -m pytest tests/test_docpivot_engine.py::test_name
```

## Troubleshooting

### Common Issues

**Tests pass locally but fail in CI:**
- Check for hardcoded paths
- Verify sample files are committed
- Check Python version differences

**Coverage unexpectedly drops:**
- New code added without tests
- Tests were deleted but code wasn't
- Conditional imports not being tested

**Tests become slow over time:**
- Too many integration tests
- Not using fixtures efficiently
- Testing external dependencies

## Summary

The DocPivot test suite is designed to be:
- **Fast** - Run frequently without friction
- **Focused** - Test what matters, ignore what doesn't
- **Maintainable** - Easy to understand and modify

Remember: The goal is to catch real bugs and enable confident refactoring, not to achieve 100% coverage or test every theoretical edge case.

For a single-developer project, pragmatic testing that runs quickly and catches actual problems is more valuable than comprehensive testing that slows down development.