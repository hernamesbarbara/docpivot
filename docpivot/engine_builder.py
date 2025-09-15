"""Builder pattern for DocPivotEngine configuration."""

from typing import Optional, Dict, Any
from docpivot.engine import DocPivotEngine


class DocPivotEngineBuilder:
    """Fluent builder for DocPivotEngine with advanced configuration."""

    def __init__(self):
        """Initialize the builder with default values."""
        self._lexical_config = {}
        self._default_format = "lexical"
        self._custom_serializers = {}
        self._custom_readers = {}

    def with_lexical_config(self, config: Dict[str, Any]) -> 'DocPivotEngineBuilder':
        """Set Lexical serialization configuration.

        Args:
            config: Dictionary of Lexical configuration options

        Returns:
            Self for method chaining
        """
        self._lexical_config.update(config)
        return self

    def with_pretty_print(self, indent: int = 2) -> 'DocPivotEngineBuilder':
        """Enable pretty printing with specified indentation.

        Args:
            indent: Number of spaces for indentation (default: 2)

        Returns:
            Self for method chaining
        """
        self._lexical_config["pretty"] = True
        self._lexical_config["indent"] = indent
        return self

    def with_default_format(self, format: str) -> 'DocPivotEngineBuilder':
        """Set the default output format.

        Args:
            format: Default format name (e.g., "lexical")

        Returns:
            Self for method chaining
        """
        self._default_format = format
        return self

    def with_custom_serializer(self, format: str, serializer) -> 'DocPivotEngineBuilder':
        """Register a custom serializer for a format.

        Args:
            format: Format name
            serializer: Serializer instance or class

        Returns:
            Self for method chaining

        Note:
            This is for future extensibility. Currently not implemented.
        """
        self._custom_serializers[format] = serializer
        return self

    def with_custom_reader(self, extension: str, reader) -> 'DocPivotEngineBuilder':
        """Register a custom reader for a file extension.

        Args:
            extension: File extension (e.g., ".custom")
            reader: Reader instance or class

        Returns:
            Self for method chaining

        Note:
            This is for future extensibility. Currently not implemented.
        """
        self._custom_readers[extension] = reader
        return self

    def with_images(self, include: bool = True) -> 'DocPivotEngineBuilder':
        """Configure whether to include images in the output.

        Args:
            include: Whether to include images (default: True)

        Returns:
            Self for method chaining
        """
        self._lexical_config["handle_images"] = include
        return self

    def with_metadata(self, include: bool = True) -> 'DocPivotEngineBuilder':
        """Configure whether to include metadata in the output.

        Args:
            include: Whether to include metadata (default: True)

        Returns:
            Self for method chaining
        """
        self._lexical_config["include_metadata"] = include
        return self

    def with_performance_mode(self) -> 'DocPivotEngineBuilder':
        """Configure for optimal performance (minimal output).

        Returns:
            Self for method chaining
        """
        self._lexical_config.update({
            "pretty": False,
            "include_metadata": False,
            "handle_images": False,
        })
        return self

    def with_debug_mode(self) -> 'DocPivotEngineBuilder':
        """Configure for debugging (maximum information).

        Returns:
            Self for method chaining
        """
        self._lexical_config.update({
            "pretty": True,
            "indent": 4,
            "include_metadata": True,
            "handle_images": True,
        })
        return self

    def build(self) -> DocPivotEngine:
        """Build the configured DocPivotEngine.

        Returns:
            Configured DocPivotEngine instance
        """
        engine = DocPivotEngine(
            lexical_config=self._lexical_config,
            default_format=self._default_format
        )

        # Future: Register custom serializers and readers if any
        # for format, serializer in self._custom_serializers.items():
        #     engine.register_serializer(format, serializer)
        # for extension, reader in self._custom_readers.items():
        #     engine.register_reader(extension, reader)

        return engine