# TODO

## ✅ Completed (v2.0.0 Refactoring)

- [x] Remove over-engineered code (performance/, plugins, optimized serializer)
- [x] Simplify existing modules (logging, validation, extensibility)
- [x] Create DocPivotEngine core class in engine.py
- [x] Create DocPivotEngineBuilder with fluent API
- [x] Create smart defaults module
- [x] Update package exports in __init__.py
- [x] Remove old test files and create clean test suite
- [x] Remove deprecation warnings from code
- [x] Remove workflows.py entirely
- [x] Remove extensibility.py entirely
- [x] Document changes in CHANGELOG.md
- [x] Create implementation completed report

## 🚀 Future Enhancements (Optional)

### High Priority
- [ ] Add Markdown output format to DocPivotEngine
- [ ] Add HTML output format to DocPivotEngine
- [ ] Create CLI tool using DocPivotEngine
  ```bash
  docpivot convert input.pdf --format lexical --output output.json
  ```

### Medium Priority
- [ ] Add streaming support for large documents
- [ ] Implement batch processing method
  ```python
  engine.convert_batch(files, output_dir)
  ```
- [ ] Add progress callbacks for long operations
- [ ] Create more comprehensive documentation

### Low Priority
- [ ] Add async API methods
- [ ] Implement caching layer for repeated conversions
- [ ] Add support for more input formats
- [ ] Create web service wrapper
- [ ] Add performance benchmarks for new API

## 📝 Documentation TODOs

- [ ] Create README with new API examples
- [ ] Add docstrings to all public methods
- [ ] Create migration guide from v1 to v2
- [ ] Add type hints throughout
- [ ] Create Jupyter notebook examples

## 🧪 Testing TODOs

- [ ] Add integration tests with real documents
- [ ] Test with large PDF files
- [ ] Add property-based tests
- [ ] Test error handling edge cases
- [ ] Add performance regression tests

## 🐛 Known Issues

None currently reported.

## 💡 Ideas for v3.0.0

- Complete async/await support
- Plugin system (if actually needed)
- GraphQL API
- Cloud storage integration (S3, GCS)
- Document comparison features
- Semantic search within documents

---

*Last Updated: September 15, 2024*