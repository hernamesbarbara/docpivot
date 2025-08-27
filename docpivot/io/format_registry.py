"""Central registry for readers and serializers with discovery capabilities.

This module provides a centralized system for registering, discovering, and
managing custom readers and serializers in DocPivot.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.types import DoclingDocument

from .readers.basereader import BaseReader
from .readers.custom_reader_base import CustomReaderBase
from .serializers.custom_serializer_base import CustomSerializerBase


class FormatInfo:
    """Information about a registered format."""

    def __init__(
        self,
        format_name: str,
        reader_class: Optional[Type[BaseReader]] = None,
        serializer_class: Optional[Type[BaseDocSerializer]] = None,
    ):
        """Initialize format information.

        Args:
            format_name: Name of the format
            reader_class: Reader class for this format
            serializer_class: Serializer class for this format
        """
        self.format_name = format_name
        self.reader_class = reader_class
        self.serializer_class = serializer_class

    @property
    def has_reader(self) -> bool:
        """Check if this format has a reader."""
        return self.reader_class is not None

    @property
    def has_serializer(self) -> bool:
        """Check if this format has a serializer."""
        return self.serializer_class is not None

    def get_capabilities(self) -> Dict[str, Any]:
        """Get combined capabilities from reader and serializer.

        Returns:
            Dict[str, Any]: Combined capabilities information
        """
        capabilities = {
            "format_name": self.format_name,
            "can_read": self.has_reader,
            "can_write": self.has_serializer,
        }

        if self.has_reader and hasattr(self.reader_class, "__new__"):
            try:
                temp_reader = self.reader_class()
                if isinstance(temp_reader, CustomReaderBase):
                    capabilities.update(
                        {
                            "supported_extensions": temp_reader.supported_extensions,
                            "reader_capabilities": temp_reader.capabilities,
                            "reader_version": temp_reader.version,
                        }
                    )
            except Exception:
                pass

        if self.has_serializer and hasattr(self.serializer_class, "__new__"):
            try:
                # Create with empty doc for capability inspection
                from docling_core.types import DocumentOrigin, NodeItem

                empty_doc = DoclingDocument(
                    name="",
                    origin=DocumentOrigin(mimetype="", binary_hash="", filename=""),
                    furniture=[],
                    body=NodeItem(),
                )
                temp_serializer = self.serializer_class(doc=empty_doc)
                if isinstance(temp_serializer, CustomSerializerBase):
                    capabilities.update(
                        {
                            "file_extension": temp_serializer.file_extension,
                            "serializer_capabilities": temp_serializer.capabilities,
                            "serializer_version": temp_serializer.version,
                            "mimetype": temp_serializer.mimetype,
                        }
                    )
            except Exception:
                pass

        return capabilities


class FormatRegistry:
    """Central registry for readers and serializers.

    This class provides a centralized system for managing format support
    in DocPivot, including registration, discovery, and capability inspection.
    """

    def __init__(self):
        """Initialize the format registry."""
        self._formats: Dict[str, FormatInfo] = {}
        self._register_builtin_formats()

    def _register_builtin_formats(self) -> None:
        """Register built-in formats that come with DocPivot."""
        try:
            from .readers.doclingjsonreader import DoclingJsonReader
            from .readers.lexicaljsonreader import LexicalJsonReader
            from .serializers.lexicaldocserializer import LexicalDocSerializer

            # Register built-in readers
            self.register_reader("docling", DoclingJsonReader)
            self.register_reader("lexical", LexicalJsonReader)

            # Register built-in serializers
            self.register_serializer("lexical", LexicalDocSerializer)

            # Register Docling core serializers
            from docling_core.transforms.serializer.markdown import (
                MarkdownDocSerializer,
            )
            from docling_core.transforms.serializer.doctags import DocTagsDocSerializer
            from docling_core.transforms.serializer.html import HTMLDocSerializer

            self.register_serializer("markdown", MarkdownDocSerializer)
            self.register_serializer("md", MarkdownDocSerializer)
            self.register_serializer("doctags", DocTagsDocSerializer)
            self.register_serializer("html", HTMLDocSerializer)

        except ImportError:
            # Some formats may not be available - that's okay
            pass

    def register_reader(self, format_name: str, reader_class: Type[BaseReader]) -> None:
        """Register a reader class for a format.

        Args:
            format_name: Name of the format
            reader_class: Reader class that extends BaseReader

        Raises:
            TypeError: If reader_class is not a BaseReader subclass
            ValueError: If format_name is empty
        """
        if not format_name or not format_name.strip():
            raise ValueError("Format name cannot be empty")

        if not issubclass(reader_class, BaseReader):
            raise TypeError(
                f"Reader class {reader_class.__name__} must extend BaseReader"
            )

        format_key = format_name.lower().strip()

        if format_key in self._formats:
            self._formats[format_key].reader_class = reader_class
        else:
            self._formats[format_key] = FormatInfo(
                format_name=format_name, reader_class=reader_class
            )

    def register_serializer(
        self, format_name: str, serializer_class: Type[BaseDocSerializer]
    ) -> None:
        """Register a serializer class for a format.

        Args:
            format_name: Name of the format
            serializer_class: Serializer class that extends BaseDocSerializer

        Raises:
            TypeError: If serializer_class is not a BaseDocSerializer subclass
            ValueError: If format_name is empty
        """
        if not format_name or not format_name.strip():
            raise ValueError("Format name cannot be empty")

        if not issubclass(serializer_class, BaseDocSerializer):
            raise TypeError(
                f"Serializer class {serializer_class.__name__} must extend BaseDocSerializer"
            )

        format_key = format_name.lower().strip()

        if format_key in self._formats:
            self._formats[format_key].serializer_class = serializer_class
        else:
            self._formats[format_key] = FormatInfo(
                format_name=format_name, serializer_class=serializer_class
            )

    def register_format(
        self,
        format_name: str,
        reader_class: Optional[Type[BaseReader]] = None,
        serializer_class: Optional[Type[BaseDocSerializer]] = None,
    ) -> None:
        """Register both reader and serializer for a format.

        Args:
            format_name: Name of the format
            reader_class: Optional reader class
            serializer_class: Optional serializer class

        Raises:
            ValueError: If neither reader nor serializer is provided
        """
        if not reader_class and not serializer_class:
            raise ValueError("Must provide at least a reader or serializer class")

        if reader_class:
            self.register_reader(format_name, reader_class)

        if serializer_class:
            self.register_serializer(format_name, serializer_class)

    def get_reader_for_format(self, format_name: str) -> Optional[Type[BaseReader]]:
        """Get reader class for a format.

        Args:
            format_name: Name of the format

        Returns:
            Optional[Type[BaseReader]]: Reader class or None if not registered
        """
        format_key = format_name.lower().strip()
        format_info = self._formats.get(format_key)
        return format_info.reader_class if format_info else None

    def get_serializer_for_format(
        self, format_name: str
    ) -> Optional[Type[BaseDocSerializer]]:
        """Get serializer class for a format.

        Args:
            format_name: Name of the format

        Returns:
            Optional[Type[BaseDocSerializer]]: Serializer class or None if not registered
        """
        format_key = format_name.lower().strip()
        format_info = self._formats.get(format_key)
        return format_info.serializer_class if format_info else None

    def get_reader_for_file(self, file_path: Union[str, Path]) -> Optional[BaseReader]:
        """Get appropriate reader instance for a file.

        This method tries to find the best reader for the given file by
        testing each registered reader's format detection capabilities.

        Args:
            file_path: Path to the file

        Returns:
            Optional[BaseReader]: Reader instance or None if no suitable reader found
        """
        path = Path(file_path)

        if not path.exists():
            return None

        # Try each registered reader
        for format_info in self._formats.values():
            if not format_info.has_reader:
                continue

            try:
                reader = format_info.reader_class()
                if reader.can_handle(file_path):
                    return reader
            except Exception:
                # If reader instantiation or detection fails, skip it
                continue

        return None

    def discover_formats(self) -> Dict[str, Dict[str, Any]]:
        """Discover all available formats and their capabilities.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping format names to capabilities
        """
        result = {}

        for format_key, format_info in self._formats.items():
            result[format_key] = format_info.get_capabilities()

        return result

    def list_formats(self) -> List[str]:
        """List all registered format names.

        Returns:
            List[str]: List of format names
        """
        return list(self._formats.keys())

    def list_readable_formats(self) -> List[str]:
        """List formats that can be read (have readers).

        Returns:
            List[str]: List of readable format names
        """
        return [
            format_key
            for format_key, format_info in self._formats.items()
            if format_info.has_reader
        ]

    def list_writable_formats(self) -> List[str]:
        """List formats that can be written (have serializers).

        Returns:
            List[str]: List of writable format names
        """
        return [
            format_key
            for format_key, format_info in self._formats.items()
            if format_info.has_serializer
        ]

    def is_format_supported(self, format_name: str) -> bool:
        """Check if a format is supported (registered).

        Args:
            format_name: Name of the format to check

        Returns:
            bool: True if supported, False otherwise
        """
        format_key = format_name.lower().strip()
        return format_key in self._formats

    def can_read_format(self, format_name: str) -> bool:
        """Check if a format can be read.

        Args:
            format_name: Name of the format to check

        Returns:
            bool: True if format has a reader, False otherwise
        """
        format_key = format_name.lower().strip()
        format_info = self._formats.get(format_key)
        return format_info.has_reader if format_info else False

    def can_write_format(self, format_name: str) -> bool:
        """Check if a format can be written.

        Args:
            format_name: Name of the format to check

        Returns:
            bool: True if format has a serializer, False otherwise
        """
        format_key = format_name.lower().strip()
        format_info = self._formats.get(format_key)
        return format_info.has_serializer if format_info else False

    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions from registered readers.

        Returns:
            List[str]: List of supported file extensions
        """
        extensions = set()

        for format_info in self._formats.values():
            if not format_info.has_reader:
                continue

            try:
                reader = format_info.reader_class()
                if isinstance(reader, CustomReaderBase):
                    extensions.update(reader.supported_extensions)
            except Exception:
                continue

        return sorted(list(extensions))

    def unregister_format(self, format_name: str) -> bool:
        """Unregister a format.

        Args:
            format_name: Name of the format to unregister

        Returns:
            bool: True if format was unregistered, False if not found
        """
        format_key = format_name.lower().strip()
        if format_key in self._formats:
            del self._formats[format_key]
            return True
        return False

    def clear_registry(self) -> None:
        """Clear all registered formats.

        Warning: This will remove all registered formats including built-ins.
        Use with caution.
        """
        self._formats.clear()

    def get_format_info(self, format_name: str) -> Optional[FormatInfo]:
        """Get detailed information about a format.

        Args:
            format_name: Name of the format

        Returns:
            Optional[FormatInfo]: Format information or None if not found
        """
        format_key = format_name.lower().strip()
        return self._formats.get(format_key)


# Global registry instance
_global_registry: Optional[FormatRegistry] = None


def get_format_registry() -> FormatRegistry:
    """Get the global format registry instance.

    Returns:
        FormatRegistry: Global registry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = FormatRegistry()
    return _global_registry
