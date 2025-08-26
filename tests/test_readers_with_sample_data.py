"""Comprehensive tests for readers using real sample data files."""

import pytest
from pathlib import Path
from docling_core.types import DoclingDocument

from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.readers.lexicaljsonreader import LexicalJsonReader
from docpivot.io.readers.readerfactory import ReaderFactory
from docpivot.io.readers.exceptions import SchemaValidationError


class TestDoclingJsonReaderWithSampleData:
    """Test DoclingJsonReader with real sample data."""
    
    def test_load_sample_docling_json(self, sample_docling_json_path: Path):
        """Test loading sample docling JSON file."""
        reader = DoclingJsonReader()
        document = reader.load_data(sample_docling_json_path)
        
        # Verify basic document structure
        assert isinstance(document, DoclingDocument)
        assert document.name == "2025-07-03-Test-PDF-Styles"
        assert document.origin is not None
        assert document.origin.filename == "2025-07-03-Test-PDF-Styles.pdf"
        assert document.origin.mimetype == "application/pdf"
    
    def test_docling_document_structure(self, sample_docling_document_from_file: DoclingDocument):
        """Validate loaded document structure and content."""
        document = sample_docling_document_from_file
        
        # Check schema information
        assert document.name == "2025-07-03-Test-PDF-Styles"
        
        # Check body structure
        assert document.body is not None
        assert len(document.body.children) > 0
        
        # Check texts are present
        assert document.texts is not None
        assert len(document.texts) > 0
        
        # Verify some text content exists
        first_text = document.texts[0]
        assert hasattr(first_text, 'text')
        assert len(first_text.text) > 0
    
    def test_document_content_quality(self, sample_docling_document_from_file: DoclingDocument):
        """Test that document content is meaningful and well-structured."""
        document = sample_docling_document_from_file
        
        # Check that we have meaningful text content
        text_elements = [text for text in document.texts if text.text.strip()]
        assert len(text_elements) > 0
        
        # Find title-like content
        title_texts = [text for text in document.texts if "title" in text.text.lower()]
        assert len(title_texts) > 0, "Should contain title text"
        
        # Find paragraph content
        paragraph_texts = [text for text in document.texts if len(text.text) > 50]
        assert len(paragraph_texts) > 0, "Should contain substantial paragraph text"
    
    def test_error_handling_with_invalid_sample(self, temp_directory: Path):
        """Test error handling with corrupted sample file."""
        # Create corrupted JSON file
        invalid_file = temp_directory / "invalid.docling.json"
        invalid_file.write_text('{"invalid": "json", "missing": "schema"}')
        
        reader = DoclingJsonReader()
        with pytest.raises(SchemaValidationError):
            reader.load_data(invalid_file)


class TestLexicalJsonReaderWithSampleData:
    """Test LexicalJsonReader with real sample data."""
    
    def test_load_sample_lexical_json(self, sample_lexical_json_path: Path):
        """Test loading sample lexical JSON file."""
        reader = LexicalJsonReader()
        document = reader.load_data(sample_lexical_json_path)
        
        # Verify basic document structure
        assert isinstance(document, DoclingDocument)
        assert "lexical" in document.name.lower()
        assert len(document.name) > 10  # Should have meaningful name
    
    def test_lexical_to_docling_mapping(self, sample_lexical_document_from_file: DoclingDocument):
        """Validate transformation from Lexical to DoclingDocument."""
        document = sample_lexical_document_from_file
        
        # Check that transformation occurred
        assert document.body is not None
        assert len(document.body.children) > 0
        
        # Check that we have text elements
        assert document.texts is not None
        assert len(document.texts) > 0
        
        # Verify content mapping
        all_text = " ".join([text.text for text in document.texts if text.text])
        assert "title" in all_text.lower()
        assert "subtitle" in all_text.lower()
    
    def test_lexical_content_preservation(self, sample_lexical_document_from_file: DoclingDocument):
        """Test that important content is preserved during transformation."""
        document = sample_lexical_document_from_file
        
        # Extract all text content
        all_text = " ".join([text.text for text in document.texts if text.text.strip()])
        
        # Check for expected content from lexical sample
        assert "This is the title" in all_text
        assert "subtitle" in all_text
        assert "Lorem Ipsum" in all_text or "Lorem ipsum" in all_text
        
        # Check we have reasonable amount of text
        assert len(all_text) > 100, "Should have substantial text content"
    
    def test_lexical_structure_mapping(self, sample_lexical_document_from_file: DoclingDocument):
        """Test that Lexical structure maps correctly to Docling structure."""
        document = sample_lexical_document_from_file
        
        # Check we have different types of text elements
        section_headers = []
        text_elements = []
        
        for text in document.texts:
            if text.label and "section_header" in str(text.label).lower():
                section_headers.append(text)
            elif text.label and "text" in str(text.label).lower():
                text_elements.append(text)
        
        # We should have some structure differentiation
        assert len(section_headers) > 0 or len(text_elements) > 0


class TestReaderFactoryWithSampleData:
    """Test ReaderFactory with real sample data."""
    
    def test_auto_detect_docling_format(self, sample_docling_json_path: Path):
        """Test automatic detection of docling format."""
        factory = ReaderFactory()
        reader = factory.get_reader(sample_docling_json_path)
        
        assert isinstance(reader, DoclingJsonReader)
        
        # Test that it can load the document
        document = reader.load_data(sample_docling_json_path)
        assert isinstance(document, DoclingDocument)
    
    def test_auto_detect_lexical_format(self, sample_lexical_json_path: Path):
        """Test automatic detection of lexical format.""" 
        factory = ReaderFactory()
        reader = factory.get_reader(sample_lexical_json_path)
        
        assert isinstance(reader, LexicalJsonReader)
        
        # Test that it can load the document
        document = reader.load_data(sample_lexical_json_path)
        assert isinstance(document, DoclingDocument)
    
    def test_format_detection_accuracy(self, sample_docling_json_path: Path, sample_lexical_json_path: Path):
        """Test that format detection is accurate for both formats."""
        factory = ReaderFactory()
        
        # Test docling detection
        docling_format = factory.detect_format(sample_docling_json_path)
        assert docling_format == "docling"
        
        # Test lexical detection
        lexical_format = factory.detect_format(sample_lexical_json_path)
        assert lexical_format == "lexical"
    
    def test_end_to_end_loading(self, sample_docling_json_path: Path, sample_lexical_json_path: Path):
        """Test complete end-to-end loading process."""
        factory = ReaderFactory()
        
        # Load docling document
        docling_reader = factory.get_reader(sample_docling_json_path)
        docling_doc = docling_reader.load_data(sample_docling_json_path)
        assert isinstance(docling_doc, DoclingDocument)
        assert len(docling_doc.texts) > 0
        
        # Load lexical document
        lexical_reader = factory.get_reader(sample_lexical_json_path)
        lexical_doc = lexical_reader.load_data(sample_lexical_json_path)
        assert isinstance(lexical_doc, DoclingDocument)
        assert len(lexical_doc.texts) > 0


class TestReaderPerformanceWithSampleData:
    """Test reader performance with real sample data."""
    
    def test_docling_reader_performance(self, sample_docling_json_path: Path):
        """Test DoclingJsonReader performance with sample file."""
        import time
        
        reader = DoclingJsonReader()
        
        # Time multiple loads
        start_time = time.time()
        for _ in range(10):
            document = reader.load_data(sample_docling_json_path)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        # Should load reasonably quickly (less than 100ms per load)
        assert avg_time < 0.1, f"Average load time too slow: {avg_time:.3f}s"
    
    def test_lexical_reader_performance(self, sample_lexical_json_path: Path):
        """Test LexicalJsonReader performance with sample file."""
        import time
        
        reader = LexicalJsonReader()
        
        # Time multiple loads
        start_time = time.time()
        for _ in range(10):
            document = reader.load_data(sample_lexical_json_path)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        # Should load reasonably quickly (less than 200ms per load due to transformation)
        assert avg_time < 0.2, f"Average load time too slow: {avg_time:.3f}s"
    
    def test_factory_performance(self, sample_docling_json_path: Path, sample_lexical_json_path: Path):
        """Test ReaderFactory performance with sample files."""
        import time
        
        factory = ReaderFactory()
        
        # Time format detection
        start_time = time.time()
        for _ in range(20):
            factory.detect_format(sample_docling_json_path)
            factory.detect_format(sample_lexical_json_path)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 40
        # Format detection should be fast (less than 10ms)
        assert avg_time < 0.01, f"Average detection time too slow: {avg_time:.4f}s"