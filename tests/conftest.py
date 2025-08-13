"""Test configuration and fixtures for docpivot tests."""

import pytest
from pathlib import Path

from docling_core.types import DoclingDocument


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Fixture providing path to test data directory."""
    return Path(__file__).parent.parent / "data"


@pytest.fixture(scope="session")
def sample_docling_json_path(test_data_dir: Path) -> Path:
    """Fixture providing path to sample docling JSON file."""
    return test_data_dir / "json" / "2025-07-03-Test-PDF-Styles.docling.json"


@pytest.fixture(scope="session")
def sample_lexical_json_path(test_data_dir: Path) -> Path:
    """Fixture providing path to sample lexical JSON file."""
    return test_data_dir / "json" / "2025-07-03-Test-PDF-Styles.lexical.json"


@pytest.fixture
def sample_docling_document() -> DoclingDocument:
    """Fixture providing a minimal DoclingDocument for testing."""
    # Create a minimal document structure for testing
    doc = DoclingDocument(name="test_document")
    return doc


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Fixture providing a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def nonexistent_file(tmp_path: Path) -> Path:
    """Fixture providing path to a nonexistent file for testing."""
    return tmp_path / "nonexistent.json"


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    """Fixture providing a temporary file for testing."""
    temp_file = tmp_path / "test.txt"
    temp_file.write_text("test content")
    return temp_file
