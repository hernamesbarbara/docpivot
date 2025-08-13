"""Tests for BaseReader abstract class."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from docling_core.types import DoclingDocument

from docpivot.io.readers.basereader import BaseReader


class ConcreteReader(BaseReader):
    """Concrete implementation of BaseReader for testing."""
    
    def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
        """Test implementation that creates a mock DoclingDocument."""
        self._validate_file_exists(file_path)
        
        # Create a mock DoclingDocument for testing
        doc = Mock(spec=DoclingDocument)
        doc.name = Path(file_path).name
        return doc
    
    def detect_format(self, file_path: str) -> bool:
        """Test implementation that detects .txt files."""
        path = Path(file_path)
        return path.exists() and path.suffix.lower() == ".txt"


class TestBaseReader:
    """Test suite for BaseReader abstract class."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseReader cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseReader()
    
    def test_concrete_implementation_can_be_instantiated(self):
        """Test that concrete subclass can be instantiated."""
        reader = ConcreteReader()
        assert isinstance(reader, BaseReader)
    
    def test_load_data_with_valid_file(self, temp_file):
        """Test load_data with a valid existing file."""
        reader = ConcreteReader()
        doc = reader.load_data(str(temp_file))
        
        assert doc is not None
        assert doc.name == temp_file.name
    
    def test_load_data_with_nonexistent_file(self, nonexistent_file):
        """Test load_data raises FileNotFoundError for nonexistent file."""
        reader = ConcreteReader()
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            reader.load_data(str(nonexistent_file))
    
    def test_load_data_with_directory(self, temp_directory):
        """Test load_data raises IsADirectoryError for directory path."""
        reader = ConcreteReader()
        
        with pytest.raises(IsADirectoryError, match="Path is a directory"):
            reader.load_data(str(temp_directory))
    
    def test_detect_format_default_implementation(self, temp_file):
        """Test default detect_format implementation returns False."""
        # Create a reader that uses default detect_format implementation
        class DefaultFormatReader(BaseReader):
            def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
                return Mock(spec=DoclingDocument)
            # Uses default detect_format implementation
        
        reader = DefaultFormatReader()
        
        # Default implementation should return False
        assert reader.detect_format(str(temp_file)) is False
    
    def test_detect_format_with_nonexistent_file(self, nonexistent_file):
        """Test detect_format returns False for nonexistent file."""
        # Create a reader that uses default detect_format implementation  
        class DefaultFormatReader(BaseReader):
            def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
                return Mock(spec=DoclingDocument)
            # Uses default detect_format implementation
        
        reader = DefaultFormatReader()
        
        assert reader.detect_format(str(nonexistent_file)) is False
    
    def test_detect_format_concrete_implementation(self, temp_file):
        """Test concrete detect_format implementation."""
        reader = ConcreteReader()
        
        # Should return True for .txt files
        assert reader.detect_format(str(temp_file)) is True
    
    def test_detect_format_wrong_extension(self, temp_directory):
        """Test detect_format returns False for unsupported extension."""
        reader = ConcreteReader()
        
        # Create a file with wrong extension
        wrong_file = temp_directory / "test.pdf"
        wrong_file.write_text("test")
        
        assert reader.detect_format(str(wrong_file)) is False
    
    def test_validate_file_exists_valid_file(self, temp_file):
        """Test _validate_file_exists with valid file."""
        reader = ConcreteReader()
        
        validated_path = reader._validate_file_exists(str(temp_file))
        assert isinstance(validated_path, Path)
        assert validated_path == temp_file
    
    def test_validate_file_exists_nonexistent_file(self, nonexistent_file):
        """Test _validate_file_exists raises FileNotFoundError."""
        reader = ConcreteReader()
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            reader._validate_file_exists(str(nonexistent_file))
    
    def test_validate_file_exists_directory(self, temp_directory):
        """Test _validate_file_exists raises IsADirectoryError for directory."""
        reader = ConcreteReader()
        
        with pytest.raises(IsADirectoryError, match="Path is a directory"):
            reader._validate_file_exists(str(temp_directory))
    
    def test_get_format_error_message_with_extension(self, temp_directory):
        """Test _get_format_error_message for file with extension."""
        reader = ConcreteReader()
        test_file = temp_directory / "test.pdf"
        
        error_msg = reader._get_format_error_message(str(test_file))
        
        assert "Unsupported file format: .pdf" in error_msg
        assert "test.pdf" in error_msg
        assert "subclassing BaseReader" in error_msg
    
    def test_get_format_error_message_without_extension(self, temp_directory):
        """Test _get_format_error_message for file without extension."""
        reader = ConcreteReader()
        test_file = temp_directory / "testfile"
        
        error_msg = reader._get_format_error_message(str(test_file))
        
        assert "Unsupported file format: unknown" in error_msg
        assert "testfile" in error_msg
        assert "subclassing BaseReader" in error_msg
    
    def test_load_data_abstract_method_signature(self):
        """Test that abstract load_data method has correct signature."""
        # This verifies the method signature is properly defined
        assert hasattr(BaseReader, 'load_data')
        assert BaseReader.load_data.__annotations__.get('return') == DoclingDocument
    
    def test_helper_methods_are_protected(self):
        """Test that helper methods use protected naming convention."""
        reader = ConcreteReader()
        
        # Verify helper methods exist and are protected (start with _)
        assert hasattr(reader, '_validate_file_exists')
        assert hasattr(reader, '_get_format_error_message')
        
        # These should be callable
        assert callable(getattr(reader, '_validate_file_exists'))
        assert callable(getattr(reader, '_get_format_error_message'))