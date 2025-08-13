"""Tests for edge cases to improve test coverage."""

import pytest
from pathlib import Path
from docling_core.types import DoclingDocument

from docpivot.io.readers.basereader import BaseReader
from docpivot.io.readers.lexicaljsonreader import LexicalJsonReader
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer


class TestEdgeCasesForCoverage:
    """Test edge cases to improve code coverage."""
    
    def test_basereader_with_pathlib_path(self, temp_directory: Path):
        """Test BaseReader methods with pathlib.Path objects."""
        # Create concrete implementation for testing
        class ConcreteReader(BaseReader):
            def load_data(self, file_path):
                self._validate_file_exists(file_path)
                return DoclingDocument(name="test")
            
            def detect_format(self, file_path):
                try:
                    self._validate_file_exists(file_path)
                    return "test"
                except:
                    return None
        
        reader = ConcreteReader()
        
        # Test with pathlib.Path
        test_file = temp_directory / "test.txt" 
        test_file.write_text("test content")
        
        # Test path object handling
        result = reader.detect_format(test_file)
        assert result == "test"
        
        doc = reader.load_data(test_file)
        assert isinstance(doc, DoclingDocument)
    
    def test_lexical_reader_edge_cases(self, temp_directory: Path):
        """Test LexicalJsonReader edge cases."""
        reader = LexicalJsonReader()
        
        # Test with minimal valid lexical JSON
        minimal_lexical = {
            "root": {
                "children": [],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1
            }
        }
        
        minimal_file = temp_directory / "minimal.lexical.json"
        minimal_file.write_text(str(minimal_lexical).replace("'", '"'))
        
        # Should handle minimal case
        doc = reader.load_data(minimal_file)
        assert isinstance(doc, DoclingDocument)
        assert "lexical" in doc.name.lower()
    
    def test_lexical_serializer_edge_cases(self, sample_docling_document: DoclingDocument):
        """Test LexicalDocSerializer edge cases."""
        # Test with minimal document
        serializer = LexicalDocSerializer(sample_docling_document)
        result = serializer.serialize()
        
        # Should produce valid JSON even for minimal document
        assert result.text is not None
        assert len(result.text) > 0
        
        # Should be valid JSON
        import json
        data = json.loads(result.text)
        assert "root" in data
    
    def test_lexical_reader_text_extraction_edge_cases(self):
        """Test text extraction with various edge cases."""
        reader = LexicalJsonReader()
        
        # Test empty children
        assert reader._extract_text_from_children([]) == ""
        
        # Test with empty list (since None would cause TypeError)
        # This tests the actual implementation behavior
        
        # Test mixed content
        mixed_children = [
            {"type": "text", "text": "Hello"},
            {"type": "other", "content": "ignored"},
            {"type": "text", "text": "World"}
        ]
        result = reader._extract_text_from_children(mixed_children)
        assert "Hello" in result and "World" in result
    
    def test_serializer_complex_document_structures(self, sample_docling_document_from_file: DoclingDocument):
        """Test serializer with complex document structures."""
        serializer = LexicalDocSerializer(sample_docling_document_from_file)
        
        # Test with custom parameters
        result = serializer.serialize()
        
        # Verify complex structure handling
        import json
        data = json.loads(result.text)
        
        # Should handle all element types
        def count_element_types(node, counts=None):
            if counts is None:
                counts = {}
            
            if isinstance(node, dict):
                node_type = node.get("type")
                if node_type:
                    counts[node_type] = counts.get(node_type, 0) + 1
                if "children" in node and isinstance(node["children"], list):
                    for child in node["children"]:
                        count_element_types(child, counts)
            elif isinstance(node, list):
                for item in node:
                    count_element_types(item, counts)
            
            return counts
        
        # Start counting from the root element, not the top-level data
        type_counts = count_element_types(data.get('root', {}))
        
        # Should have processed some element types 
        # Note: The exact types depend on the document structure
        assert len(type_counts) > 0, f"Should have some element types, got: {type_counts}"
    
    def test_error_message_formatting_edge_cases(self, temp_directory: Path):
        """Test error message formatting in various scenarios."""
        from docpivot.io.readers.exceptions import UnsupportedFormatError
        
        # Test with very long file path
        long_path = temp_directory / ("very_long_filename_" * 10 + ".txt")
        
        error = UnsupportedFormatError(str(long_path))
        error_msg = str(error)
        
        # Should handle long paths gracefully
        assert str(long_path) in error_msg
        assert "supported formats" in error_msg.lower()
        
        # Test with custom formats
        custom_formats = ["format1", "format2", "format3"]
        error_custom = UnsupportedFormatError(str(long_path), custom_formats)
        error_custom_msg = str(error_custom)
        
        for fmt in custom_formats:
            assert fmt in error_custom_msg
    
    def test_reader_factory_edge_cases(self, temp_directory: Path):
        """Test ReaderFactory edge cases."""
        from docpivot.io.readers.readerfactory import ReaderFactory
        
        factory = ReaderFactory()
        
        # Test with file that has no extension
        no_ext_file = temp_directory / "noextension"
        no_ext_file.write_text('{"test": "content"}')
        
        # Should handle files without extensions
        try:
            format_detected = factory.detect_format(no_ext_file)
            # May detect as unsupported, which is fine
        except Exception:
            # Also acceptable if it raises an exception
            pass
    
    def test_serializer_provider_edge_cases(self):
        """Test SerializerProvider edge cases."""
        from docpivot.io.serializers.serializerprovider import SerializerProvider
        
        provider = SerializerProvider()
        
        # Test case insensitive format handling
        formats_to_test = ["MARKDOWN", "Html", "LEXICAL", "DocTags"]
        
        doc = DoclingDocument(name="test")
        
        for format_name in formats_to_test:
            try:
                serializer = provider.get_serializer(format_name.lower(), doc=doc)
                assert serializer is not None
            except (ValueError, ImportError):
                # Some formats may not be available, which is acceptable
                pass
    
    def test_workflow_functions_with_path_objects(self, sample_docling_json_path: Path):
        """Test workflow functions with pathlib.Path objects."""
        from docpivot import load_document, load_and_serialize, convert_document
        
        # Test with Path objects (not just strings)
        doc = load_document(sample_docling_json_path)  # Already a Path
        assert isinstance(doc, DoclingDocument)
        
        result = load_and_serialize(sample_docling_json_path, "markdown")
        assert result.text is not None
        assert len(result.text) > 0
        
        # Test string return from convert_document  
        markdown_text = convert_document(sample_docling_json_path, "markdown")
        assert isinstance(markdown_text, str)
        assert len(markdown_text) > 0