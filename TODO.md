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

## More Cleanup and Project Organization

### Evaluate Files & Folders for Removal
- [ ] .coverage
- [ ] .benchmarks/
- [ ] htmlcov/

### Ensure README Up-to-Date
- [ ] Look at README.md, pyproject.toml, PROJECT_CONFIG.md, and CHANGELOG.md
- [ ] Figure out if README is up-to-date for all recent improvements
- [ ] If PROJECT_CONFIG.md contains anything useful, update the README with the useful bits and remove the PROJECT_CONFIG.md file from the repo to ensure README is single source of truth

### Validate examples/
- [ ] Look at each script in examples/ and make sure they are working

### Testing & Tests
- [ ] Read TESTING.md and confirm that it outlines a testing methodology that includes: TDD, 90% coverage targets, very lightweight and not overkill for a simple project that is only going to be used by me personally and not a lot of developers
- [ ] Ensure Makefile is used as the entry point for running tests and linting and that this is documented properly in TESTING.md
- [ ] Create a test suite in the tests/ directory following your finalized TESTING.md methodology. Remember you have data/pdf/ and data/json/ for real-world data to use for testing. Remember you have examples/ which should all be working and can help you craft realistic useful tests. 
- [ ] Ensure entire test suite takes no longer than 120 seconds to complete
- [ ] Ensure ruff linting is working

### Cloakpivot Companion TODOs
- [ ] Look at the cloakpivot repo
- [ ] Create a plan just like this one such that I can perform the same set of updates you just completed in this TODO.md file in that repo as well. The goal is to make it easy to maintain both docpivot and cloakpivot using the same build and test tooling and the same project organizational structure

### Change summary
- [ ] Overwrite this section each time you complete a meaningful chunk of work. Commit all meaningful chunks of work to the local feature branch we are on. Update the "Next Up" with a propmt that will help you get started on whatever is next. 
