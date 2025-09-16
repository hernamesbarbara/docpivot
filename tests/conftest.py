"""Shared pytest fixtures for DocPivot tests."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from docling_core.types import DoclingDocument


@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def sample_docling_json_path(test_data_dir):
    """Return path to sample Docling JSON file."""
    json_files = list((test_data_dir / "json").glob("*.docling.json"))
    if json_files:
        return json_files[0]
    return None


@pytest.fixture
def sample_lexical_json_path(test_data_dir):
    """Return path to sample Lexical JSON file."""
    json_files = list((test_data_dir / "json").glob("*.lexical.json"))
    if json_files:
        return json_files[0]
    return None


@pytest.fixture
def sample_pdf_path(test_data_dir):
    """Return path to sample PDF file."""
    pdf_files = list((test_data_dir / "pdf").glob("*.pdf"))
    if pdf_files:
        return pdf_files[0]
    return None


@pytest.fixture
def mock_docling_document():
    """Create a mock DoclingDocument for testing."""
    doc = Mock(spec=DoclingDocument)
    doc.name = "test_document"
    doc.body = Mock()
    doc.body.items = [
        Mock(type="paragraph", text="Test paragraph"),
        Mock(type="heading", text="Test heading"),
        Mock(type="list", items=["item1", "item2"])
    ]
    doc.metadata = {"source": "test", "version": "1.0"}
    return doc


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_lexical_content():
    """Return sample Lexical JSON content."""
    return {
        "root": {
            "children": [
                {
                    "type": "paragraph",
                    "children": [
                        {
                            "type": "text",
                            "text": "Sample paragraph text"
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def sample_docling_content():
    """Return sample Docling content structure."""
    return {
        "name": "sample_document",
        "body": {
            "items": [
                {
                    "type": "paragraph",
                    "text": "Sample paragraph"
                },
                {
                    "type": "heading",
                    "text": "Sample heading",
                    "level": 1
                }
            ]
        },
        "metadata": {
            "source": "test"
        }
    }
