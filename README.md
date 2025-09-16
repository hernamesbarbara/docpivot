# DocPivot

**Version 2.0.0** - Simplified document conversion API for [Docling](https://github.com/DS4SD/docling)

DocPivot provides a clean, one-line API for converting documents between formats, with special focus on Lexical Editor JSON format. Built on top of Docling's powerful document processing capabilities.

## ✨ What's New in v2.0

- **Simplified API**: One-line document conversion with `DocPivotEngine`
- **30% less code**: Removed over-engineered features for a cleaner codebase
- **Builder pattern**: Fluent configuration API for advanced use cases
- **Smart defaults**: Works out of the box for 90% of use cases

## 🚀 Quick Start

```python
from docpivot import DocPivotEngine

# Create engine with defaults
engine = DocPivotEngine()

# Convert any DoclingDocument to Lexical JSON
result = engine.convert_to_lexical(doc)
print(result.content)  # Lexical Editor JSON

# Convert files directly
result = engine.convert_file("document.docling.json")

# Convert PDF (requires docling package)
result = engine.convert_pdf("document.pdf")
```

## 📦 Installation

```bash
# Basic installation
pip install docpivot

# Development installation (includes all tools)
git clone https://github.com/hernamesbarbara/docpivot.git
cd docpivot
make install  # or: pip install -e ".[dev]"
```

## 🔧 Advanced Configuration

### Using the Builder Pattern

```python
from docpivot import DocPivotEngine

# Configure with builder
engine = (DocPivotEngine.builder()
    .with_pretty_print(indent=2)
    .with_images(include=True)
    .with_metadata(include=True)
    .build())

# Use preset configurations
from docpivot import get_performance_config

engine = DocPivotEngine(lexical_config=get_performance_config())
```

### Available Presets

- `get_default_lexical_config()` - Balanced defaults
- `get_performance_config()` - Optimized for speed
- `get_debug_config()` - Maximum information for debugging
- `get_minimal_config()` - Smallest output size
- `get_web_config()` - Optimized for web applications

## 📄 Supported Formats

| Format | Input | Output | Notes |
|--------|--------|--------|-------|
| Docling JSON | ✅ | ✅ | Native Docling format |
| Lexical JSON | ✅ | ✅ | Lexical Editor format |
| PDF | ✅ | ➖ | Via Docling (input only) |
| Markdown | ➖ | ✅ | Via native Docling |
| HTML | ➖ | ✅ | Via native Docling |

## 🛠️ Development

DocPivot uses a simplified development setup with all configuration centralized in `pyproject.toml` and commands in `Makefile`.

```bash
# Setup development environment
make dev

# Run all checks (CI entry point)
make all

# Quick pre-commit check
make check

# Run tests with coverage
make test

# Format code
make format

# Type checking
make type

# Clean all artifacts
make clean

# See all commands
make help
```

### Project Structure

```
docpivot/
├── engine.py           # Core DocPivotEngine class
├── engine_builder.py   # Fluent builder pattern
├── defaults.py         # Smart configuration presets
└── io/                # Readers and serializers
    ├── readers/       # Format readers
    └── serializers/   # Format serializers
```

### Configuration Philosophy

All project configuration follows a **single-source-of-truth** approach:

- **`pyproject.toml`** - All tool configurations and metadata
  - Project metadata (PEP 621)
  - Dependencies (runtime + single `dev` group)
  - Tool configs: Black, Ruff (with isort), MyPy, pytest, Coverage
- **`Makefile`** - Single command hub for all operations
- **No duplicate configs** - Everything in pyproject.toml
- **Gradual typing** - Strict for new code, lenient for legacy

Tools automatically read their config from `pyproject.toml`:
```bash
black docpivot/          # Reads [tool.black]
ruff check docpivot/     # Reads [tool.ruff]
mypy docpivot/           # Reads [tool.mypy]
pytest tests/            # Reads [tool.pytest.ini_options]
```

## 📚 Examples

See the `examples/` directory for complete examples:

- `basic_usage.py` - Simple conversion patterns
- `advanced_usage.py` - Batch processing and pipelines
- `builder_pattern.py` - Configuration with builder API
- `pdf_conversion.py` - PDF to multiple formats

## 🧪 Testing

DocPivot follows a pragmatic TDD approach:

```bash
# Run tests
make test         # With coverage
make test-fast    # Quick, no coverage

# Coverage report
make coverage     # Generate and open HTML report
```

See [TESTING.md](TESTING.md) for testing philosophy and guidelines.

## 📝 License

Apache 2.0 - See LICENSE file for details.

## 🤝 Contributing

This is primarily a single-developer project. If you find bugs or have suggestions, please open an issue.

## 🔗 Related Projects

- [Docling](https://github.com/DS4SD/docling) - Document conversion framework
- [Lexical](https://lexical.dev) - Extensible text editor framework

---

**Note**: DocPivot v2.0 represents a major simplification from v1.0. If you need the older, more complex API, use version 1.0.0.