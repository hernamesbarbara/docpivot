# DocPivot Makefile - Single Command Hub
# Run 'make help' to see all available commands

.PHONY: help install test lint type format clean all check coverage

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

help:  ## Show this help message
	@echo "$(BLUE)DocPivot Development Commands$(NC)"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

# ============================================================
# INSTALLATION
# ============================================================
install:  ## Install package in development mode with all dependencies
	pip install -e ".[dev]"

# ============================================================
# TESTING
# ============================================================
test:  ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	pytest tests/ \
		--cov=docpivot \
		--cov-report=term-missing:skip-covered \
		--cov-report=html \
		--tb=short \
		-v

test-fast:  ## Run tests quickly without coverage
	@echo "$(YELLOW)Running tests (fast mode)...$(NC)"
	pytest tests/ -q --tb=short

coverage:  ## Generate and open HTML coverage report
	pytest tests/ --cov=docpivot --cov-report=html --tb=short -q
	@echo "$(GREEN)Opening coverage report...$(NC)"
	@python -m webbrowser htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html in your browser"

# ============================================================
# CODE QUALITY
# ============================================================
lint:  ## Run ruff linter
	@echo "$(YELLOW)Running ruff linter...$(NC)"
	ruff check docpivot/ tests/ examples/

lint-fix:  ## Run ruff linter with automatic fixes
	@echo "$(YELLOW)Running ruff with fixes...$(NC)"
	ruff check --fix docpivot/ tests/ examples/

type:  ## Run mypy type checker
	@echo "$(YELLOW)Running mypy type checker...$(NC)"
	mypy docpivot/

format:  ## Format code with black
	@echo "$(YELLOW)Formatting code with black...$(NC)"
	black docpivot/ tests/ examples/

format-check:  ## Check if code needs formatting (CI mode)
	@echo "$(YELLOW)Checking code format...$(NC)"
	black --check docpivot/ tests/ examples/

# ============================================================
# CLEANUP
# ============================================================
clean:  ## Clean all generated files and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage .coverage.*
	rm -rf output/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	@echo "$(GREEN)✓ Cleaned$(NC)"

# ============================================================
# MAIN TARGETS
# ============================================================
check: format lint type test-fast  ## Quick check before commit (fast)
	@echo "$(GREEN)✓ All checks passed!$(NC)"

all: format lint type test  ## Full validation suite (CI entry point)
	@echo "$(GREEN)✓ Full validation complete!$(NC)"

# ============================================================
# DEVELOPMENT HELPERS
# ============================================================
dev: install  ## Setup development environment
	@echo "$(GREEN)✓ Development environment ready$(NC)"

docs:  ## Build documentation (if we add it later)
	@echo "$(YELLOW)Documentation not yet implemented$(NC)"

# ============================================================
# CI/CD TARGETS
# ============================================================
ci: all  ## Single entry point for CI/CD (alias for 'all')
	@echo "$(GREEN)✓ CI validation complete$(NC)"

pre-commit: check  ## Run pre-commit checks
	@echo "$(GREEN)✓ Ready to commit$(NC)"

# ============================================================
# UTILITY TARGETS
# ============================================================
.PHONY: version
version:  ## Show package version
	@python -c "import docpivot; print(f'DocPivot v{docpivot.__version__}')"

.PHONY: deps
deps:  ## Show installed dependencies
	pip list | grep -E "(docling|pydantic|pytest|mypy|black|ruff)"

.PHONY: stats
stats:  ## Show code statistics
	@echo "$(BLUE)Code Statistics:$(NC)"
	@echo "Lines of code:"
	@find docpivot -name "*.py" -type f | xargs wc -l | tail -1
	@echo "Number of Python files:"
	@find docpivot -name "*.py" -type f | wc -l
	@echo "Number of tests:"
	@grep -r "def test_" tests/ | wc -l