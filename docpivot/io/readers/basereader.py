"""Base reader abstract class for DocPivot document readers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from docling_core.types import DoclingDocument


class BaseReader(ABC):
    """Abstract base class for all document readers in DocPivot.

    Provides the foundation for document readers following Docling's patterns.
    Subclasses must implement load_data to handle specific file formats.
    """

    @abstractmethod
    def load_data(self, file_path: str, **kwargs: Any) -> DoclingDocument:
        """Load document from file_path into DoclingDocument.

        Args:
            file_path: Path to the document file to load
            **kwargs: Additional format-specific parameters

        Returns:
            DoclingDocument: The loaded document as a DoclingDocument

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file format is not supported or invalid
            IOError: If there are issues reading the file
        """
        pass

    def detect_format(self, file_path: str) -> bool:
        """Detect if this reader can handle the given file format.

        Default implementation checks file extensions. Subclasses can override
        for content-based detection or more sophisticated format detection.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if this reader can handle the file format, False
                otherwise
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            return False

        # Default implementation always returns False
        # Subclasses should override with specific format detection logic
        return False

    def _validate_file_exists(self, file_path: str) -> Path:
        """Validate that the specified file exists and is readable.

        Args:
            file_path: Path to the file to validate

        Returns:
            Path: Validated Path object

        Raises:
            FileNotFoundError: If the file does not exist
            IsADirectoryError: If the path is a directory, not a file
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

        return path

    def _get_format_error_message(self, file_path: str) -> str:
        """Generate a clear error message for unsupported file formats.

        Args:
            file_path: Path to the unsupported file

        Returns:
            str: Formatted error message with guidance
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        return (
            f"Unsupported file format: {extension or 'unknown'} "
            f"for file '{file_path}'. "
            f"This reader does not support this format. "
            f"Please use the appropriate reader for your file format or "
            f"implement a custom reader by subclassing BaseReader."
        )
