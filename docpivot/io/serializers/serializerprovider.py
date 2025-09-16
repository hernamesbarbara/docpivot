"""Serializer provider following Docling's factory pattern with extensibility support."""

# Forward reference for LexicalDocSerializer to avoid circular imports
from typing import TYPE_CHECKING, Any, Union

from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.transforms.serializer.doctags import DocTagsDocSerializer
from docling_core.transforms.serializer.html import HTMLDocSerializer
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from docling_core.types import DoclingDocument

if TYPE_CHECKING:
    from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer

# Type alias for any serializer (docling-core or our custom ones)
AnySerializer = Union[BaseDocSerializer, "LexicalDocSerializer"]


class SerializerProvider:
    """Factory for creating serializer instances following Docling patterns with extensibility support."""

    _serializers: dict[str, type[BaseDocSerializer]] = {
        "markdown": MarkdownDocSerializer,
        "md": MarkdownDocSerializer,
        "doctags": DocTagsDocSerializer,
        "html": HTMLDocSerializer,
    }

    # Integration with format registry
    _registry_integration_enabled = True

    @classmethod
    def _get_lexical_serializer(cls) -> type["LexicalDocSerializer"]:
        """Import LexicalDocSerializer to avoid circular imports."""
        from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer

        return LexicalDocSerializer

    @classmethod
    def get_serializer(cls, format_name: str, doc: DoclingDocument, **kwargs: Any) -> AnySerializer:
        """Get a serializer instance for the specified format.

        This method first checks the local registry, then falls back to the
        global format registry for extended format support.

        Args:
            format_name: The output format name (e.g., "markdown", "html").
            doc: The DoclingDocument to serialize.
            **kwargs: Additional parameters to pass to the serializer constructor.

        Returns:
            AnySerializer: Configured serializer instance
                (BaseDocSerializer or LexicalDocSerializer).

        Raises:
            ValueError: If the format is not supported.
        """
        format_key = format_name.lower().strip()

        # Check built-in formats first
        if format_key == "lexical":
            serializer_cls: Any = cls._get_lexical_serializer()
            return serializer_cls(doc=doc, **kwargs)  # type: ignore[call-arg]
        if format_key in cls._serializers:
            serializer_cls = cls._serializers[format_key]
            return serializer_cls(doc=doc, **kwargs)  # type: ignore[call-arg]

        # Check format registry for extended formats
        if cls._registry_integration_enabled:
            try:
                from docpivot.io.format_registry import get_format_registry

                registry = get_format_registry()

                serializer_cls = registry.get_serializer_for_format(format_name)
                if serializer_cls is not None:
                    return serializer_cls(doc=doc, **kwargs)  # type: ignore[call-arg]
            except ImportError:
                # Format registry not available
                pass

        # Format not found anywhere
        supported_formats = cls.list_formats()
        raise ValueError(
            f"Unsupported format '{format_name}'. "
            f"Supported formats: {', '.join(supported_formats)}"
        )

    @classmethod
    def register_serializer(cls, format_name: str, serializer_cls: type[BaseDocSerializer]) -> None:
        """Register a new serializer for a format.

        Args:
            format_name: The format name to register.
            serializer_cls: The serializer class to use for this format.

        Raises:
            TypeError: If serializer_cls is not a BaseDocSerializer subclass.
        """
        if not issubclass(serializer_cls, BaseDocSerializer):
            raise TypeError(
                f"Serializer class must be a subclass of BaseDocSerializer, "
                f"got {serializer_cls.__name__}"
            )

        format_key = format_name.lower().strip()
        cls._serializers[format_key] = serializer_cls

    @classmethod
    def list_formats(cls) -> list[str]:
        """List all supported format names.

        This includes both built-in formats and formats from the registry.

        Returns:
            list[str]: List of supported format names.
        """
        formats = list(cls._serializers.keys()) + ["lexical"]

        # Add formats from registry
        if cls._registry_integration_enabled:
            try:
                from docpivot.io.format_registry import get_format_registry

                registry = get_format_registry()
                registry_formats = registry.list_writable_formats()

                # Merge and deduplicate
                all_formats = set(formats + registry_formats)
                return sorted(all_formats)
            except ImportError:
                pass

        return sorted(formats)

    @classmethod
    def is_format_supported(cls, format_name: str) -> bool:
        """Check if a format is supported.

        This checks both built-in formats and formats in the registry.

        Args:
            format_name: The format name to check.

        Returns:
            bool: True if supported, False otherwise.
        """
        format_key = format_name.lower().strip()

        # Check built-in formats
        if format_key in cls._serializers or format_key == "lexical":
            return True

        # Check format registry
        if cls._registry_integration_enabled:
            try:
                from docpivot.io.format_registry import get_format_registry

                registry = get_format_registry()
                return registry.can_write_format(format_name)
            except ImportError:
                pass

        return False

    @classmethod
    def discover_formats(cls) -> dict[str, dict[str, Any]]:
        """Discover all available serialization formats and their capabilities.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping format names to capabilities
        """
        formats = {}

        # Add built-in formats
        for format_name in cls._serializers:
            formats[format_name] = {
                "name": format_name,
                "source": "builtin",
                "serializer_class": cls._serializers[format_name].__name__,
            }

        # Add lexical format
        formats["lexical"] = {
            "name": "lexical",
            "source": "builtin",
            "serializer_class": "LexicalDocSerializer",
        }

        # Add formats from registry
        if cls._registry_integration_enabled:
            try:
                from docpivot.io.format_registry import get_format_registry

                registry = get_format_registry()
                registry_formats = registry.discover_formats()

                for format_name, capabilities in registry_formats.items():
                    if capabilities.get("can_write", False):
                        formats[format_name] = {
                            **capabilities,
                            "source": "registry",
                        }
            except ImportError:
                pass

        return formats

    @classmethod
    def enable_registry_integration(cls, enabled: bool = True) -> None:
        """Enable or disable integration with the format registry.

        Args:
            enabled: Whether to enable registry integration
        """
        cls._registry_integration_enabled = enabled
