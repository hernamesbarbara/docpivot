"""ReaderFactory for automatic format detection and reader selection."""

from pathlib import Path
from typing import Dict, List, Type, Union

from .basereader import BaseReader
from .doclingjsonreader import DoclingJsonReader
from .lexicaljsonreader import LexicalJsonReader
from .exceptions import UnsupportedFormatError


class ReaderFactory:
    """Factory class for automatically selecting the appropriate reader based on file format.
    
    This factory provides format detection capabilities and automatically selects
    the correct reader class based on file extensions and content signatures.
    """
    
    def __init__(self):
        """Initialize the ReaderFactory with default readers."""
        self._readers: Dict[str, Type[BaseReader]] = {}
        self._register_default_readers()
    
    def _register_default_readers(self) -> None:
        """Register the default readers that come with DocPivot."""
        self.register_reader("docling", DoclingJsonReader)
        self.register_reader("lexical", LexicalJsonReader)
    
    def register_reader(self, format_name: str, reader_class: Type[BaseReader]) -> None:
        """Register a reader class for a specific format.
        
        Args:
            format_name: Name of the format (e.g., "docling", "lexical")
            reader_class: Reader class that extends BaseReader
            
        Raises:
            ValueError: If reader_class does not extend BaseReader
        """
        if not issubclass(reader_class, BaseReader):
            raise ValueError(f"Reader class {reader_class.__name__} must extend BaseReader")
        
        self._readers[format_name] = reader_class
    
    def get_reader(self, file_path: Union[str, Path], **kwargs) -> BaseReader:
        """Automatically select and instantiate the appropriate reader for the given file.
        
        Args:
            file_path: Path to the file to read
            **kwargs: Additional parameters to pass to the reader constructor
            
        Returns:
            BaseReader: Instantiated reader for the detected format
            
        Raises:
            FileNotFoundError: If the file does not exist
            UnsupportedFormatError: If no reader can handle the file format
        """
        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try to detect format
        format_name = self.detect_format(file_path)
        
        # Get and instantiate the appropriate reader
        reader_class = self._readers.get(format_name)
        if reader_class is None:
            raise UnsupportedFormatError(str(file_path))
        
        return reader_class(**kwargs)
    
    def detect_format(self, file_path: Union[str, Path]) -> str:
        """Detect the file format and return the format name.
        
        Uses both file extension and content-based detection to determine
        the appropriate format.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            str: Format name ("docling", "lexical", etc.)
            
        Raises:
            UnsupportedFormatError: If no reader can handle the file format
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            raise UnsupportedFormatError(str(file_path))
        
        # Try each registered reader's detect_format method
        for format_name, reader_class in self._readers.items():
            try:
                # Create a temporary instance to test format detection
                temp_reader = reader_class()
                if temp_reader.detect_format(file_path):
                    return format_name
            except Exception:
                # If a reader fails during detection, skip it
                continue
        
        # If no reader can handle the format, raise an error
        raise UnsupportedFormatError(str(file_path))
    
    def get_supported_formats(self) -> List[str]:
        """Get a list of supported format names.
        
        Returns:
            List[str]: List of supported format names
        """
        return list(self._readers.keys())
    
    def is_supported_format(self, file_path: Union[str, Path]) -> bool:
        """Check if the given file format is supported by any registered reader.
        
        Args:
            file_path: Path to check for format compatibility
            
        Returns:
            bool: True if the format is supported, False otherwise
        """
        try:
            self.detect_format(file_path)
            return True
        except UnsupportedFormatError:
            return False