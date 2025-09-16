"""ReaderFactory for automatic format detection and reader selection with extensibility support."""

from pathlib import Path

from .basereader import BaseReader
from .doclingjsonreader import DoclingJsonReader
from .exceptions import UnsupportedFormatError
from .lexicaljsonreader import LexicalJsonReader


class ReaderFactory:
    """Factory for automatically selecting the appropriate reader based on file format.

    This factory provides format detection capabilities and automatically selects
    the correct reader class based on file extensions and content signatures.
    It integrates with the extensibility system for extended format support.
    """

    def __init__(self, enable_registry_integration: bool = True):
        """Initialize the ReaderFactory with default readers.

        Args:
            enable_registry_integration: Whether to integrate with the format registry
        """
        self._readers: dict[str, type[BaseReader]] = {}
        self._registry_integration_enabled = enable_registry_integration
        self._register_default_readers()

    def _register_default_readers(self) -> None:
        """Register the default readers that come with DocPivot."""
        self.register_reader("docling", DoclingJsonReader)
        self.register_reader("lexical", LexicalJsonReader)

    def register_reader(self, format_name: str, reader_class: type[BaseReader]) -> None:
        """Register a reader class for a specific format.

        Args:
            format_name: Name of the format (e.g., "docling", "lexical")
            reader_class: Reader class that extends BaseReader

        Raises:
            ValueError: If reader_class does not extend BaseReader
        """
        if not issubclass(reader_class, BaseReader):
            raise ValueError(
                f"Reader class {reader_class.__name__} must extend BaseReader"
            )

        self._readers[format_name] = reader_class

    def get_reader(self, file_path: str | Path, **kwargs) -> BaseReader:
        """Automatically select and instantiate the appropriate reader for file.

        This method first checks local readers, then falls back to the
        global format registry for extended format support.

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

        # Try to detect format using local readers
        try:
            format_name = self.detect_format(file_path)
            reader_class = self._readers.get(format_name)
            if reader_class is not None:
                return reader_class(**kwargs)
        except UnsupportedFormatError:
            pass

        # Try format registry
        if self._registry_integration_enabled:
            try:
                from docpivot.io.format_registry import get_format_registry

                registry = get_format_registry()
                reader = registry.get_reader_for_file(file_path)
                if reader is not None:
                    return reader
            except ImportError:
                pass

        # No reader found
        raise UnsupportedFormatError(str(file_path))

    def detect_format(self, file_path: str | Path) -> str:
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

    def get_supported_formats(self) -> list[str]:
        """Get a list of supported format names.

        This includes both local readers and formats from the registry.

        Returns:
            List[str]: List of supported format names
        """
        formats = list(self._readers.keys())

        # Add formats from registry
        if self._registry_integration_enabled:
            try:
                from docpivot.io.format_registry import get_format_registry

                registry = get_format_registry()
                registry_formats = registry.list_readable_formats()

                # Merge and deduplicate
                all_formats = set(formats + registry_formats)
                return sorted(list(all_formats))
            except ImportError:
                pass

        return sorted(formats)

    def is_supported_format(self, file_path: str | Path) -> bool:
        """Check if the given file format is supported by any registered reader.

        This checks both local readers and the format registry.

        Args:
            file_path: Path to check for format compatibility

        Returns:
            bool: True if the format is supported, False otherwise
        """
        # Check local readers first
        try:
            self.detect_format(file_path)
            return True
        except UnsupportedFormatError:
            pass

        # Check format registry
        if self._registry_integration_enabled:
            try:
                from docpivot.io.format_registry import get_format_registry

                registry = get_format_registry()
                reader = registry.get_reader_for_file(file_path)
                return reader is not None
            except ImportError:
                pass

        return False

    def discover_formats(self) -> dict[str, dict[str, any]]:
        """Discover all available reading formats and their capabilities.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping format names to capabilities
        """
        formats = {}

        # Add local formats
        for format_name, reader_class in self._readers.items():
            formats[format_name] = {
                "name": format_name,
                "source": "builtin",
                "reader_class": reader_class.__name__,
            }

        # Add formats from registry
        if self._registry_integration_enabled:
            try:
                from docpivot.io.format_registry import get_format_registry

                registry = get_format_registry()
                registry_formats = registry.discover_formats()

                for format_name, capabilities in registry_formats.items():
                    if capabilities.get("can_read", False):
                        formats[format_name] = {
                            **capabilities,
                            "source": "registry",
                        }
            except ImportError:
                pass

        return formats

    def enable_registry_integration(self, enabled: bool = True) -> None:
        """Enable or disable integration with the format registry.

        Args:
            enabled: Whether to enable registry integration
        """
        self._registry_integration_enabled = enabled
