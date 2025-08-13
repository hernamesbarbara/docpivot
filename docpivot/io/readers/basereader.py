"""Base reader class following Docling patterns."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union

from docling_core.types import DoclingDocument


class BaseReader(ABC):
    """Base class for document readers following Docling's reader pattern."""
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the reader with optional configuration parameters.
        
        Args:
            **kwargs: Configuration parameters specific to the reader implementation.
        """
        self.config = kwargs
    
    @abstractmethod
    def load_data(
        self, 
        file_path: Union[str, Path], 
        **kwargs: Any
    ) -> DoclingDocument:
        """Load and parse a document from the given file path.
        
        Args:
            file_path: Path to the document file to load.
            **kwargs: Additional parameters for loading.
            
        Returns:
            DoclingDocument: The loaded document.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is not supported.
            NotImplementedError: If the reader implementation is incomplete.
        """
        raise NotImplementedError("Subclasses must implement load_data method")
    
    @classmethod
    def is_supported_format(cls, file_path: Union[str, Path]) -> bool:
        """Check if the given file format is supported by this reader.
        
        Args:
            file_path: Path to check for format compatibility.
            
        Returns:
            bool: True if the format is supported, False otherwise.
        """
        return False
    
    def _validate_file_exists(self, file_path: Union[str, Path]) -> Path:
        """Validate that the file exists and return as Path object.
        
        Args:
            file_path: File path to validate.
            
        Returns:
            Path: Validated file path.
            
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return path