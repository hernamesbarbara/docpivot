# DocPivot Project Configuration

## Overview

DocPivot uses a **simplified, single-source-of-truth** configuration approach:

1. **`pyproject.toml`** - All tool configurations and metadata
2. **`Makefile`** - Single command hub for all operations
3. **`.gitignore`** - Comprehensive ignore patterns (already set)

## Configuration Files

### pyproject.toml
Contains configurations for:
- **Project metadata** (PEP 621) - version 2.0.0
- **Dependencies** (runtime + single `dev` group)
- **Black** - Code formatting (100 char line length)
- **Ruff** - Fast linting with integrated isort rules
- **MyPy** - Type checking (gradual typing approach)
- **pytest** - Testing framework
- **Coverage** - Test coverage reporting

### Makefile
Single entry point for all commands:
- `make help` - Show all available commands
- `make all` - CI/CD entry point (format, lint, type, test)
- `make check` - Quick pre-commit check
- `make test` - Run tests with coverage
- `make clean` - Remove all artifacts

## Quick Start

```bash
# Setup development environment
make dev

# Run all checks (CI entry point)
make all

# Quick check before commit
make check

# Clean everything
make clean
```

## CI/CD

GitHub Actions simply runs:
```yaml
- run: make install
- run: make all
```

## Tool Commands

All tools read their config from `pyproject.toml`:

```bash
# These commands use pyproject.toml configs automatically:
black docpivot/          # Reads [tool.black]
ruff check docpivot/     # Reads [tool.ruff]
mypy docpivot/           # Reads [tool.mypy]
pytest tests/            # Reads [tool.pytest.ini_options]
```

## Philosophy

- **No duplicate configs** - Everything in pyproject.toml
- **No shell scripts in root** - Use Makefile targets
- **Single CI entry** - `make all` for everything
- **Gradual typing** - Strict for new code, lenient for legacy
- **Fast feedback** - `make check` for quick validation

## Simplified Configuration Decisions

Key simplifications made:
- **Single dev dependency group** - No more test/lint/all groups, just `dev`
- **No duplicate tool configs** - Removed standalone isort (using ruff's isort)
- **Explicit mypy files** - Using `files = ["docpivot", "tests"]` instead of paths
- **No redundant settings** - Removed defaults like `strict_optional = true`

## Files Removed

These files were removed as redundant:
- `mypy.ini` - Moved to `[tool.mypy]` in pyproject.toml
- `run_tests.sh` - Replaced by Makefile targets
- Standalone isort config - Using ruff's integrated isort rules

## Adding New Tools

When adding new tools:
1. Add config to `pyproject.toml` under `[tool.toolname]`
2. Add Makefile target if needed
3. Update `.gitignore` if tool creates cache files
4. Document in this file

This approach keeps the project root clean and configuration centralized.