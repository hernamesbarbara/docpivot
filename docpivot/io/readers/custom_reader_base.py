"""Template base class for custom reader implementations.

This module provides a comprehensive template for creating custom readers
that extend DocPivot's functionality to support additional file formats.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Union, Optional

from docling_core.types import DoclingDocument

from .basereader import BaseReader


class CustomReaderBase(BaseReader):
    """Template base class for custom reader implementations.

    This class provides a comprehensive template and interface for creating
    custom readers that can handle new file formats. It includes metadata
    properties, validation helpers, and clear extension points.

    Example usage:
        class MyCustomReader(CustomReaderBase):
            @property
            def supported_extensions(self) -> List[str]:
                return ['.mycustom', '.mc']

            @property
            def format_name(self) -> str:
                return "My Custom Format"

            def can_handle(self, file_path: Union[str, Path]) -> bool:
                return Path(file_path).suffix.lower() in self.supported_extensions

            def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
                # Implementation here
                return self._create_empty_document()
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """File extensions this reader supports.

        Returns:
            List[str]: List of file extensions including the dot (e.g., ['.xml', '.xhtml'])
        """
        raise NotImplementedError("Subclasses must define supported_extensions")

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Human-readable format name.

        Returns:
            str: Descriptive name of the format (e.g., "XML Documents")
        """
        raise NotImplementedError("Subclasses must define format_name")

    @property
    def format_description(self) -> Optional[str]:
        """Optional detailed description of the format.

        Returns:
            Optional[str]: Detailed description of what this format handles
        """
        return None

    @property
    def version(self) -> str:
        """Version of this reader implementation.

        Returns:
            str: Version string (e.g., "1.0.0")
        """
        return "1.0.0"

    @property
    def capabilities(self) -> Dict[str, bool]:
        """Capabilities supported by this reader.

        Returns:
            Dict[str, bool]: Dictionary of capability flags
        """
        return {
            "text_extraction": True,
            "metadata_extraction": False,
            "structure_preservation": True,
            "embedded_images": False,
            "embedded_tables": False,
        }

    @abstractmethod
    def can_handle(self, file_path: Union[str, Path]) -> bool:
        """Check if this reader can handle the given file.

        This method should implement format detection logic, which may include:
        - File extension checking
        - Content signature verification
        - Header analysis

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if this reader can handle the file, False otherwise
        """
        raise NotImplementedError("Subclasses must implement can_handle method")

    def detect_format(self, file_path: Union[str, Path]) -> bool:
        """Detect if this reader can handle the given file format.

        Default implementation delegates to can_handle method.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if this reader can handle the file format, False otherwise
        """
        return self.can_handle(file_path)

    @classmethod
    def is_supported_format(cls, file_path: Union[str, Path]) -> bool:
        """Check if the given file format is supported by this reader class.

        This is a class method that can be called without instantiation.
        Default implementation checks file extension against supported_extensions.

        Args:
            file_path: Path to check for format compatibility

        Returns:
            bool: True if the format is supported, False otherwise
        """
        try:
            # Create temporary instance to access properties
            temp_instance = cls()
            extension = Path(file_path).suffix.lower()
            return extension in temp_instance.supported_extensions
        except Exception:
            return False

    def validate_file_format(self, file_path: Union[str, Path]) -> None:
        """Validate that the file format is compatible with this reader.

        Args:
            file_path: Path to the file to validate

        Raises:
            ValueError: If the file format is not supported
            FileNotFoundError: If the file does not exist
        """
        path = self._validate_file_exists(file_path)

        if not self.can_handle(path):
            extension = path.suffix.lower() if path.suffix else "unknown"
            raise ValueError(
                f"Unsupported file format for {self.format_name} reader: "
                f"{extension} ({path.name})\n"
                f"Supported extensions: {', '.join(self.supported_extensions)}"
            )

    def get_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract metadata from the file without full parsing.

        This is an optional method that readers can implement to provide
        quick metadata extraction without full document parsing.

        Args:
            file_path: Path to the file

        Returns:
            Dict[str, Any]: Dictionary of metadata properties
        """
        path = Path(file_path)
        return {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "format_name": self.format_name,
            "reader_version": self.version,
        }

    def _create_empty_document(self) -> DoclingDocument:
        """Create an empty DoclingDocument with basic structure.

        This helper method can be used by subclasses to create a base document
        that can then be populated with content.

        Returns:
            DoclingDocument: Empty document with basic structure
        """
        from docling_core.types import DoclingDocument
        from docling_core.types.doc import DocumentOrigin, NodeItem

        # Create basic document structure
        doc = DoclingDocument(
            name="",
            origin=DocumentOrigin(
                mimetype="application/octet-stream",
                binary_hash="",
                filename="",
            ),
            furniture=[],
            body=NodeItem(),
        )

        return doc

    def _validate_configuration(self) -> None:
        """Validate reader configuration and properties.

        This method is called during initialization to ensure the reader
        is properly configured. Subclasses can override to add custom validation.

        Raises:
            ValueError: If the configuration is invalid
        """
        if not self.supported_extensions:
            raise ValueError(
                f"{self.__class__.__name__} must define supported_extensions"
            )

        if not self.format_name:
            raise ValueError(f"{self.__class__.__name__} must define format_name")

        # Validate extensions format
        for ext in self.supported_extensions:
            if not ext.startswith("."):
                raise ValueError(f"Extensions must start with '.', got: {ext}")

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the custom reader with validation.

        Args:
            **kwargs: Configuration parameters specific to the reader implementation
        """
        super().__init__(**kwargs)
        self._validate_configuration()

    def __str__(self) -> str:
        """String representation of the reader."""
        return f"{self.__class__.__name__}({self.format_name} v{self.version})"

    def __repr__(self) -> str:
        """Detailed representation of the reader."""
        return (
            f"{self.__class__.__name__}("
            f"format_name='{self.format_name}', "
            f"version='{self.version}', "
            f"extensions={self.supported_extensions})"
        )
