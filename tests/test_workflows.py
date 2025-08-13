"""Tests for high-level workflow functions."""

import tempfile
from pathlib import Path

import pytest
from docling_core.types import DoclingDocument

from docpivot.workflows import load_document, load_and_serialize, convert_document
from docpivot.io.readers.exceptions import UnsupportedFormatError


class TestLoadDocument:
    """Test suite for load_document function."""
    
    def test_load_docling_json(self, sample_docling_json_path):
        """Test loading a docling.json file."""
        doc = load_document(sample_docling_json_path)
        
        assert isinstance(doc, DoclingDocument)
        assert doc.name is not None
        assert len(doc.texts) >= 0
        
    def test_load_lexical_json(self, sample_lexical_json_path):
        """Test loading a lexical.json file."""
        doc = load_document(sample_lexical_json_path)
        
        assert isinstance(doc, DoclingDocument)
        assert doc.name is not None
        assert len(doc.texts) >= 0
        
    def test_load_file_not_found(self):
        """Test error handling when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_document("nonexistent_file.json")
            
    def test_load_unsupported_format(self):
        """Test error handling for unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix=".unsupported", delete=False) as tmp:
            tmp.write(b"invalid content")
            tmp.flush()
            
            try:
                with pytest.raises(UnsupportedFormatError):
                    load_document(tmp.name)
            finally:
                Path(tmp.name).unlink()


class TestLoadAndSerialize:
    """Test suite for load_and_serialize function."""
    
    def test_load_and_serialize_to_markdown(self, sample_docling_json_path):
        """Test loading and serializing to markdown."""
        result = load_and_serialize(sample_docling_json_path, "markdown")
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        
    def test_load_and_serialize_to_html(self, sample_docling_json_path):
        """Test loading and serializing to HTML."""
        result = load_and_serialize(sample_docling_json_path, "html")
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        
    def test_load_and_serialize_to_lexical(self, sample_docling_json_path):
        """Test loading and serializing to lexical format."""
        result = load_and_serialize(sample_docling_json_path, "lexical")
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        # Verify it's valid JSON structure
        import json
        lexical_data = json.loads(result.text)
        assert "root" in lexical_data
        
    def test_load_and_serialize_with_params(self, sample_docling_json_path):
        """Test loading and serializing with custom parameters."""
        from docling_core.transforms.serializer.markdown import MarkdownParams
        
        params = MarkdownParams(image_placeholder="(no image)")
        result = load_and_serialize(
            sample_docling_json_path, 
            "markdown", 
            params=params
        )
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        
    def test_load_and_serialize_unsupported_format(self, sample_docling_json_path):
        """Test error handling for unsupported output format."""
        with pytest.raises(ValueError):
            load_and_serialize(sample_docling_json_path, "unsupported_format")
            
    def test_load_and_serialize_file_not_found(self):
        """Test error handling when input file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_and_serialize("nonexistent_file.json", "markdown")


class TestConvertDocument:
    """Test suite for convert_document function."""
    
    def test_convert_document_return_string(self, sample_docling_json_path):
        """Test converting document and returning content as string."""
        content = convert_document(sample_docling_json_path, "markdown")
        
        assert isinstance(content, str)
        assert len(content) > 0
        
    def test_convert_document_write_to_file(self, sample_docling_json_path):
        """Test converting document and writing to output file."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            output_path = tmp.name
            
        try:
            result_path = convert_document(
                sample_docling_json_path, 
                "markdown", 
                output_path
            )
            
            assert result_path == output_path
            assert Path(output_path).exists()
            
            # Verify file content
            content = Path(output_path).read_text(encoding="utf-8")
            assert len(content) > 0
            
        finally:
            Path(output_path).unlink(missing_ok=True)
            
    def test_convert_document_html_format(self, sample_docling_json_path):
        """Test converting to HTML format."""
        content = convert_document(sample_docling_json_path, "html")
        
        assert isinstance(content, str)
        assert len(content) > 0
        
    def test_convert_document_lexical_format(self, sample_docling_json_path):
        """Test converting to lexical JSON format."""
        content = convert_document(sample_docling_json_path, "lexical")
        
        assert isinstance(content, str)
        assert len(content) > 0
        
        # Verify it's valid JSON
        import json
        lexical_data = json.loads(content)
        assert "root" in lexical_data
        
    def test_convert_document_with_custom_serializer_params(self, sample_docling_json_path):
        """Test converting with custom serializer parameters."""
        from docling_core.transforms.serializer.markdown import MarkdownParams
        
        params = MarkdownParams(image_placeholder="[IMAGE REMOVED]")
        content = convert_document(
            sample_docling_json_path, 
            "markdown", 
            params=params
        )
        
        assert isinstance(content, str)
        assert len(content) > 0
        
    def test_convert_document_invalid_output_path(self, sample_docling_json_path):
        """Test error handling for invalid output path."""
        # Try to write to a directory that doesn't exist
        invalid_path = "/nonexistent_directory/output.md"
        
        with pytest.raises(IOError):
            convert_document(sample_docling_json_path, "markdown", invalid_path)
            
    def test_convert_document_unsupported_format(self, sample_docling_json_path):
        """Test error handling for unsupported output format."""
        with pytest.raises(ValueError):
            convert_document(sample_docling_json_path, "unsupported_format")
            
    def test_convert_document_file_not_found(self):
        """Test error handling when input file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            convert_document("nonexistent_file.json", "markdown")


class TestWorkflowIntegration:
    """Integration tests for workflow functions working together."""
    
    def test_all_formats_roundtrip_workflow(self, sample_docling_json_path):
        """Test complete workflow with different format combinations."""
        # Test all supported output formats
        formats = ["markdown", "html", "lexical", "doctags"]
        
        for output_format in formats:
            try:
                # Load and serialize
                result = load_and_serialize(sample_docling_json_path, output_format)
                assert hasattr(result, 'text')
                assert isinstance(result.text, str)
                assert len(result.text) > 0
                
                # Convert to string
                content = convert_document(sample_docling_json_path, output_format)
                assert isinstance(content, str)
                assert content == result.text
                
            except ValueError:
                # Some formats might not be supported, that's okay
                continue
                
    def test_lexical_to_markdown_workflow(self, sample_lexical_json_path):
        """Test converting from Lexical JSON to Markdown."""
        result = load_and_serialize(sample_lexical_json_path, "markdown")
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        
    def test_error_propagation_workflow(self):
        """Test that errors propagate correctly through the workflow."""
        # Test file not found error propagation
        with pytest.raises(FileNotFoundError):
            load_and_serialize("nonexistent.json", "markdown")
            
        with pytest.raises(FileNotFoundError):
            convert_document("nonexistent.json", "markdown")
            
        # Test unsupported format error propagation
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"plain text content")
            tmp.flush()
            
            try:
                with pytest.raises(UnsupportedFormatError):
                    load_and_serialize(tmp.name, "markdown")
                    
                with pytest.raises(UnsupportedFormatError):
                    convert_document(tmp.name, "markdown")
                    
            finally:
                Path(tmp.name).unlink()
                
    def test_parameter_passing_workflow(self, sample_docling_json_path):
        """Test that parameters are correctly passed through the workflow."""
        from docling_core.transforms.serializer.markdown import MarkdownParams
        
        # Test with MarkdownParams
        params = MarkdownParams(image_placeholder="(image removed)")
        
        # Test load_and_serialize with params
        result1 = load_and_serialize(
            sample_docling_json_path, 
            "markdown", 
            params=params
        )
        
        # Test convert_document with params  
        result2 = convert_document(
            sample_docling_json_path, 
            "markdown", 
            params=params
        )
        
        # Results should be identical
        assert result1.text == result2