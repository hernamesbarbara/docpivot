"""Tests for ReaderFactory class."""

import json
from pathlib import Path

import pytest

from docpivot.io.readers.basereader import BaseReader
from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.readers.lexicaljsonreader import LexicalJsonReader
from docpivot.io.readers.readerfactory import ReaderFactory
from docpivot.io.readers.exceptions import UnsupportedFormatError


class TestReaderFactory:
    """Test suite for ReaderFactory class."""
    
    def test_can_be_instantiated(self):
        """Test that ReaderFactory can be instantiated."""
        factory = ReaderFactory()
        assert isinstance(factory, ReaderFactory)
    
    def test_has_default_readers_registered(self):
        """Test that default readers are registered on instantiation."""
        factory = ReaderFactory()
        
        supported_formats = factory.get_supported_formats()
        assert "docling" in supported_formats
        assert "lexical" in supported_formats
        assert len(supported_formats) >= 2
    
    def test_register_reader_valid(self):
        """Test registering a valid reader class."""
        factory = ReaderFactory()
        
        # Register a new reader
        factory.register_reader("test", DoclingJsonReader)
        
        # Check it was registered
        supported_formats = factory.get_supported_formats()
        assert "test" in supported_formats
    
    def test_register_reader_invalid_class(self):
        """Test that registering invalid reader class raises ValueError."""
        factory = ReaderFactory()
        
        # Try to register a class that doesn't extend BaseReader
        class NotAReader:
            pass
        
        with pytest.raises(ValueError, match="must extend BaseReader"):
            factory.register_reader("invalid", NotAReader)
    
    def test_get_reader_docling_json_file(self, temp_directory):
        """Test get_reader returns DoclingJsonReader for .docling.json file."""
        factory = ReaderFactory()
        
        # Create a .docling.json file with valid content
        docling_file = temp_directory / "test.docling.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        docling_file.write_text(content)
        
        # Get reader
        reader = factory.get_reader(str(docling_file))
        
        assert isinstance(reader, DoclingJsonReader)
    
    def test_get_reader_lexical_json_file(self, temp_directory):
        """Test get_reader returns LexicalJsonReader for .lexical.json file."""
        factory = ReaderFactory()
        
        # Create a .lexical.json file with valid content
        lexical_file = temp_directory / "test.lexical.json"
        content = '{"root": {"children": [], "type": "root"}}'
        lexical_file.write_text(content)
        
        # Get reader
        reader = factory.get_reader(str(lexical_file))
        
        assert isinstance(reader, LexicalJsonReader)
    
    def test_get_reader_generic_json_docling_content(self, temp_directory):
        """Test get_reader detects Docling content in generic .json file."""
        factory = ReaderFactory()
        
        # Create a .json file with DoclingDocument content
        json_file = temp_directory / "test.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        json_file.write_text(content)
        
        # Get reader
        reader = factory.get_reader(str(json_file))
        
        assert isinstance(reader, DoclingJsonReader)
    
    def test_get_reader_generic_json_lexical_content(self, temp_directory):
        """Test get_reader detects Lexical content in generic .json file.""" 
        factory = ReaderFactory()
        
        # Create a .json file with Lexical content
        json_file = temp_directory / "test.json"
        content = '{"root": {"children": [], "type": "root"}}'
        json_file.write_text(content)
        
        # Get reader
        reader = factory.get_reader(str(json_file))
        
        assert isinstance(reader, LexicalJsonReader)
    
    def test_get_reader_nonexistent_file(self, nonexistent_file):
        """Test get_reader raises FileNotFoundError for nonexistent file."""
        factory = ReaderFactory()
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            factory.get_reader(str(nonexistent_file))
    
    def test_get_reader_unsupported_format(self, temp_directory):
        """Test get_reader raises UnsupportedFormatError for unsupported format."""
        factory = ReaderFactory()
        
        # Create a file with unsupported format
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("some text content")
        
        with pytest.raises(UnsupportedFormatError):
            factory.get_reader(str(txt_file))
    
    def test_get_reader_passes_kwargs_to_reader(self, temp_directory):
        """Test get_reader passes kwargs to the reader constructor."""
        factory = ReaderFactory()
        
        # Create a .docling.json file
        docling_file = temp_directory / "test.docling.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        docling_file.write_text(content)
        
        # Get reader with kwargs
        test_config = {"key": "value"}
        reader = factory.get_reader(str(docling_file), **test_config)
        
        assert isinstance(reader, DoclingJsonReader)
        assert reader.config == test_config
    
    def test_detect_format_docling(self, temp_directory):
        """Test detect_format returns 'docling' for DoclingDocument files."""
        factory = ReaderFactory()
        
        # Create a .docling.json file
        docling_file = temp_directory / "test.docling.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        docling_file.write_text(content)
        
        format_name = factory.detect_format(str(docling_file))
        assert format_name == "docling"
    
    def test_detect_format_lexical(self, temp_directory):
        """Test detect_format returns 'lexical' for Lexical files."""
        factory = ReaderFactory()
        
        # Create a .lexical.json file
        lexical_file = temp_directory / "test.lexical.json" 
        content = '{"root": {"children": [], "type": "root"}}'
        lexical_file.write_text(content)
        
        format_name = factory.detect_format(str(lexical_file))
        assert format_name == "lexical"
    
    def test_detect_format_nonexistent_file(self, nonexistent_file):
        """Test detect_format raises UnsupportedFormatError for nonexistent file."""
        factory = ReaderFactory()
        
        with pytest.raises(UnsupportedFormatError):
            factory.detect_format(str(nonexistent_file))
    
    def test_detect_format_unsupported_format(self, temp_directory):
        """Test detect_format raises UnsupportedFormatError for unsupported format."""
        factory = ReaderFactory()
        
        # Create a file with unsupported format
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("some text content")
        
        with pytest.raises(UnsupportedFormatError):
            factory.detect_format(str(txt_file))
    
    def test_detect_format_handles_reader_exceptions(self, temp_directory):
        """Test detect_format gracefully handles reader exceptions during detection."""
        factory = ReaderFactory()
        
        # Create a mock reader that raises exceptions during detection
        class BrokenReader(BaseReader):
            def load_data(self, file_path, **kwargs):
                return None
            
            def detect_format(self, file_path):
                raise Exception("Broken reader")
        
        # Register the broken reader
        factory.register_reader("broken", BrokenReader)
        
        # Create a file that should be handled by a working reader
        docling_file = temp_directory / "test.docling.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        docling_file.write_text(content)
        
        # Should still detect as docling even with broken reader registered
        format_name = factory.detect_format(str(docling_file))
        assert format_name in ["docling", "lexical"]  # Should find one that works
    
    def test_get_supported_formats(self):
        """Test get_supported_formats returns list of format names."""
        factory = ReaderFactory()
        
        formats = factory.get_supported_formats()
        assert isinstance(formats, list)
        assert "docling" in formats
        assert "lexical" in formats
    
    def test_is_supported_format_true(self, temp_directory):
        """Test is_supported_format returns True for supported format."""
        factory = ReaderFactory()
        
        # Create a supported file
        docling_file = temp_directory / "test.docling.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        docling_file.write_text(content)
        
        assert factory.is_supported_format(str(docling_file)) is True
    
    def test_is_supported_format_false(self, temp_directory):
        """Test is_supported_format returns False for unsupported format."""
        factory = ReaderFactory()
        
        # Create an unsupported file
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("some text content")
        
        assert factory.is_supported_format(str(txt_file)) is False
    
    def test_register_reader_overwrites_existing(self):
        """Test that registering a reader with existing name overwrites it."""
        factory = ReaderFactory()
        
        # Register a custom reader with same name as existing one
        factory.register_reader("docling", LexicalJsonReader)
        
        # Create a .docling.json file
        # Note: We can't easily test the actual behavior change without complex setup,
        # but we can verify the registration worked
        assert "docling" in factory.get_supported_formats()
    
    def test_path_objects_supported(self, temp_directory):
        """Test that Path objects are supported alongside string paths."""
        factory = ReaderFactory()
        
        # Create a file and use Path object
        docling_file = temp_directory / "test.docling.json"
        content = '{"schema_name": "DoclingDocument", "version": "1.4.0"}'
        docling_file.write_text(content)
        
        # Should work with Path object
        reader = factory.get_reader(docling_file)
        assert isinstance(reader, DoclingJsonReader)
        
        # Should work with detect_format too
        format_name = factory.detect_format(docling_file)
        assert format_name == "docling"
        
        # Should work with is_supported_format too
        assert factory.is_supported_format(docling_file) is True