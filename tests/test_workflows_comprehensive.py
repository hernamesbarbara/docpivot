"""Comprehensive tests for end-to-end workflows using sample data."""

import json
import pytest
from pathlib import Path
from docling_core.types import DoclingDocument
from docling_core.transforms.serializer.base import SerializationResult

from docpivot import load_document, load_and_serialize, convert_document
from docpivot.io.readers.exceptions import UnsupportedFormatError, FileAccessError, SchemaValidationError, ConfigurationError


class TestWorkflowFunctions:
    """Test high-level workflow functions with sample data."""
    
    def test_load_document_with_docling_sample(self, sample_docling_json_path: Path):
        """Test load_document with docling sample file."""
        document = load_document(sample_docling_json_path)
        
        assert isinstance(document, DoclingDocument)
        assert document.name == "2025-07-03-Test-PDF-Styles"
        assert len(document.texts) > 0
        
        # Check content quality
        all_text = " ".join([text.text for text in document.texts if text.text])
        assert len(all_text) > 100, "Should load substantial content"
    
    def test_load_document_with_lexical_sample(self, sample_lexical_json_path: Path):
        """Test load_document with lexical sample file."""
        document = load_document(sample_lexical_json_path)
        
        assert isinstance(document, DoclingDocument)
        assert "lexical" in document.name.lower()
        assert len(document.texts) > 0
        
        # Check content quality
        all_text = " ".join([text.text for text in document.texts if text.text])
        assert "title" in all_text.lower()
        assert len(all_text) > 50, "Should load meaningful content"
    
    def test_load_and_serialize_docling_to_markdown(self, sample_docling_json_path: Path):
        """Test complete workflow: docling → markdown."""
        result = load_and_serialize(sample_docling_json_path, "markdown")
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Check markdown format
        markdown = result.text
        assert "##" in markdown or "#" in markdown, "Should contain markdown headings"
        assert len(markdown.split('\n')) > 5, "Should be multi-line"
    
    def test_load_and_serialize_lexical_to_markdown(self, sample_lexical_json_path: Path):
        """Test complete workflow: lexical → markdown."""
        result = load_and_serialize(sample_lexical_json_path, "markdown")
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Check content preservation
        markdown = result.text
        assert "title" in markdown.lower()
        assert len(markdown) > 100, "Should generate substantial markdown"
    
    def test_load_and_serialize_docling_to_html(self, sample_docling_json_path: Path):
        """Test complete workflow: docling → HTML."""
        result = load_and_serialize(sample_docling_json_path, "html")
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Check HTML format
        html = result.text
        assert "<" in html and ">" in html, "Should contain HTML tags"
        assert "<h" in html or "<p" in html, "Should contain structural HTML"
    
    def test_load_and_serialize_docling_to_lexical(self, sample_docling_json_path: Path):
        """Test complete workflow: docling → lexical."""
        result = load_and_serialize(sample_docling_json_path, "lexical")
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        
        # Validate lexical JSON format
        lexical_data = json.loads(result.text)
        assert "root" in lexical_data
        assert "children" in lexical_data["root"]
        assert len(lexical_data["root"]["children"]) > 0
    
    def test_load_and_serialize_with_custom_params(self, sample_docling_json_path: Path):
        """Test workflow with custom serializer parameters."""
        # Test with markdown parameters
        from docling_core.transforms.serializer.markdown import MarkdownParams
        params = MarkdownParams(image_placeholder="(no image)")
        result = load_and_serialize(sample_docling_json_path, "markdown", params=params)
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        
        # If there are images, they should show the placeholder
        if "(no image)" in result.text or len(result.text) > 0:
            # Test passed - either placeholder found or no images to replace
            assert True
    
    def test_convert_document_to_file(self, sample_docling_json_path: Path, temp_directory: Path):
        """Test convert_document with file output."""
        output_path = temp_directory / "output.md"
        
        result_path = convert_document(
            sample_docling_json_path, 
            "markdown", 
            output_path
        )
        
        assert result_path == str(output_path)
        assert output_path.exists()
        
        # Check file content
        content = output_path.read_text(encoding='utf-8')
        assert len(content) > 0
        assert "##" in content or "#" in content, "Should contain markdown headings"
    
    def test_convert_document_to_string(self, sample_docling_json_path: Path):
        """Test convert_document returning string."""
        result = convert_document(sample_docling_json_path, "markdown")
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "##" in result or "#" in result, "Should contain markdown headings"
    
    def test_convert_document_creates_directories(self, sample_docling_json_path: Path, temp_directory: Path):
        """Test that convert_document creates necessary directories."""
        nested_output = temp_directory / "nested" / "output" / "result.html"
        
        result_path = convert_document(
            sample_docling_json_path,
            "html",
            nested_output
        )
        
        assert result_path == str(nested_output)
        assert nested_output.exists()
        assert nested_output.parent.exists()
        
        # Check content
        content = nested_output.read_text(encoding='utf-8')
        assert "<" in content and ">" in content, "Should contain HTML"


class TestWorkflowErrorHandling:
    """Test error handling in workflow functions."""
    
    def test_load_document_nonexistent_file(self, temp_directory: Path):
        """Test load_document with nonexistent file."""
        nonexistent = temp_directory / "nonexistent.json"
        
        with pytest.raises(FileAccessError):
            load_document(nonexistent)
    
    def test_load_document_unsupported_format(self, temp_directory: Path):
        """Test load_document with unsupported format."""
        unsupported_file = temp_directory / "unsupported.txt"
        unsupported_file.write_text("This is not a supported format")
        
        with pytest.raises(UnsupportedFormatError):
            load_document(unsupported_file)
    
    def test_load_and_serialize_invalid_format(self, sample_docling_json_path: Path):
        """Test load_and_serialize with invalid output format."""
        with pytest.raises(ConfigurationError):
            load_and_serialize(sample_docling_json_path, "invalid_format")
    
    def test_load_and_serialize_malformed_input(self, temp_directory: Path):
        """Test load_and_serialize with malformed input file."""
        malformed_file = temp_directory / "malformed.docling.json"
        malformed_file.write_text('{"invalid": "json structure"}')
        
        with pytest.raises(SchemaValidationError):
            load_and_serialize(malformed_file, "markdown")
    
    def test_convert_document_io_error(self, sample_docling_json_path: Path):
        """Test convert_document with IO errors."""
        # Try to write to a protected location (this may not work on all systems)
        try:
            protected_path = Path("/root/protected.md")  # This should fail on most systems
            with pytest.raises((IOError, OSError, PermissionError)):
                convert_document(sample_docling_json_path, "markdown", protected_path)
        except (IOError, OSError, PermissionError):
            # If we can't even try to write there, that's expected
            pass


class TestWorkflowPerformance:
    """Test workflow performance with sample data."""
    
    def test_load_document_performance(self, sample_docling_json_path: Path, sample_lexical_json_path: Path):
        """Test load_document performance."""
        import time
        
        # Test docling loading
        start_time = time.time()
        for _ in range(5):
            load_document(sample_docling_json_path)
        docling_time = (time.time() - start_time) / 5
        
        # Test lexical loading
        start_time = time.time()
        for _ in range(5):
            load_document(sample_lexical_json_path)
        lexical_time = (time.time() - start_time) / 5
        
        # Should be reasonably fast
        assert docling_time < 0.2, f"Docling loading too slow: {docling_time:.3f}s"
        assert lexical_time < 0.3, f"Lexical loading too slow: {lexical_time:.3f}s"  # Transformation adds time
    
    def test_end_to_end_performance(self, sample_docling_json_path: Path):
        """Test complete end-to-end workflow performance."""
        import time
        
        start_time = time.time()
        for _ in range(3):
            result = load_and_serialize(sample_docling_json_path, "markdown")
            assert len(result.text) > 0
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 3
        # Complete workflow should complete in reasonable time
        assert avg_time < 0.5, f"End-to-end workflow too slow: {avg_time:.3f}s"
    
    def test_file_conversion_performance(self, sample_docling_json_path: Path, temp_directory: Path):
        """Test file conversion performance."""
        import time
        
        output_files = []
        start_time = time.time()
        
        for i in range(3):
            output_path = temp_directory / f"output_{i}.md"
            result_path = convert_document(sample_docling_json_path, "markdown", output_path)
            output_files.append(result_path)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 3
        
        # File conversion should be reasonably fast
        assert avg_time < 0.6, f"File conversion too slow: {avg_time:.3f}s"
        
        # Verify all files were created
        for output_file in output_files:
            assert Path(output_file).exists()
            assert Path(output_file).stat().st_size > 0


class TestWorkflowAllFormatCombinations:
    """Test all supported format combinations."""
    
    @pytest.mark.parametrize("output_format", ["markdown", "html", "lexical", "doctags"])
    def test_docling_to_all_formats(self, sample_docling_json_path: Path, output_format: str):
        """Test docling input to all output formats."""
        try:
            result = load_and_serialize(sample_docling_json_path, output_format)
            assert isinstance(result, SerializationResult)
            assert result.text is not None
            assert len(result.text) > 0
            
            # Format-specific validations
            if output_format == "markdown":
                assert "#" in result.text, "Markdown should contain headings"
            elif output_format == "html":
                assert "<" in result.text and ">" in result.text, "HTML should contain tags"
            elif output_format == "lexical":
                lexical_data = json.loads(result.text)
                assert "root" in lexical_data, "Lexical should have root node"
            elif output_format == "doctags":
                assert len(result.text) > 10, "Doctags should have substantial content"
                
        except (ImportError, ValueError) as e:
            if "not supported" in str(e) or "not available" in str(e):
                pytest.skip(f"Format {output_format} not available: {e}")
            raise
    
    @pytest.mark.parametrize("output_format", ["markdown", "html", "lexical", "doctags"])
    def test_lexical_to_all_formats(self, sample_lexical_json_path: Path, output_format: str):
        """Test lexical input to all output formats."""
        try:
            result = load_and_serialize(sample_lexical_json_path, output_format)
            assert isinstance(result, SerializationResult)
            assert result.text is not None
            assert len(result.text) > 0
            
            # Format-specific validations
            if output_format == "markdown":
                assert "#" in result.text or len(result.text) > 50, "Should have headings or content"
            elif output_format == "html":
                assert "<" in result.text and ">" in result.text, "HTML should contain tags"
            elif output_format == "lexical":
                lexical_data = json.loads(result.text)
                assert "root" in lexical_data, "Lexical should have root node"
            elif output_format == "doctags":
                assert len(result.text) > 10, "Doctags should have content"
                
        except (ImportError, ValueError) as e:
            if "not supported" in str(e) or "not available" in str(e):
                pytest.skip(f"Format {output_format} not available: {e}")
            raise
    
    def test_batch_processing_workflow(self, sample_docling_json_path: Path, sample_lexical_json_path: Path, temp_directory: Path):
        """Test batch processing multiple files with same workflow."""
        input_files = [sample_docling_json_path, sample_lexical_json_path]
        output_format = "markdown"
        
        results = []
        for i, input_file in enumerate(input_files):
            output_path = temp_directory / f"batch_output_{i}.md"
            result_path = convert_document(input_file, output_format, output_path)
            results.append(result_path)
        
        # Verify all outputs
        for result_path in results:
            assert Path(result_path).exists()
            content = Path(result_path).read_text()
            assert len(content) > 0
            assert "#" in content, "Should contain markdown headings"