"""Base reader class following Docling patterns."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

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
    def load_data(self, file_path: str | Path, **kwargs: Any) -> DoclingDocument:
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
    def is_supported_format(cls, file_path: str | Path) -> bool:
        """Check if the given file format is supported by this reader.

        Args:
            file_path: Path to check for format compatibility.

        Returns:
            bool: True if the format is supported, False otherwise.
        """
        return False

    def detect_format(self, file_path: str | Path) -> bool:
        """Detect if this reader can handle the given file format.

        Default implementation returns False. Subclasses should override
        this method to implement format detection logic.

        Args:
            file_path: Path to the file to check.

        Returns:
            bool: True if this reader can handle the file format, False otherwise.
        """
        return False

    def _validate_file_exists(self, file_path: str | Path) -> Path:
        """Validate that the file exists and return as Path object.

        Args:
            file_path: File path to validate.

        Returns:
            Path: Validated file path.

        Raises:
            FileNotFoundError: If the file does not exist.
            IsADirectoryError: If the path points to a directory.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if path.is_dir():
            raise IsADirectoryError(f"Path is a directory: {file_path}")
        return path

    def _get_format_error_message(self, file_path: str | Path) -> str:
        """Generate a descriptive error message for unsupported file format.

        Args:
            file_path: Path to the unsupported file.

        Returns:
            str: Error message describing the issue and how to add support.
        """
        path = Path(file_path)
        extension = path.suffix.lower() if path.suffix else "unknown"

        return (
            f"Unsupported file format: {extension} ({path.name})\n"
            f"This file format is not supported by this reader.\n"
            f"Consider subclassing BaseReader to add support for this format."
        )
