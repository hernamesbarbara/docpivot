"""Template base class for custom serializer implementations.

This module provides a comprehensive template for creating custom serializers
that extend DocPivot's functionality to support additional output formats.
"""

from abc import abstractmethod
from typing import Any

from docling_core.transforms.serializer.base import SerializationResult
from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.types import DoclingDocument


class CustomSerializerParams:
    """Base class for custom serializer parameters.

    This class provides a pattern for parameter objects that can be passed
    to custom serializers. Subclasses should define specific parameters
    for their serialization format.

    Example usage:
        class MySerializerParams(CustomSerializerParams):
            def __init__(self, indent: int = 2, include_metadata: bool = True):
                super().__init__()
                self.indent = indent
                self.include_metadata = include_metadata
    """

    def __init__(self) -> None:
        """Initialize base parameters."""
        pass


class CustomSerializerBase(BaseDocSerializer):
    """Template base class for custom serializer implementations.

    This class provides a comprehensive template and interface for creating
    custom serializers that can output DoclingDocument to new formats.
    It follows Docling's parameter and component serializer patterns.

    Example usage:
        class MyCustomSerializer(CustomSerializerBase):
            @property
            def output_format(self) -> str:
                return "mycustom"

            @property
            def file_extension(self) -> str:
                return ".mycustom"

            def serialize(self) -> SerializationResult:
                # Implementation here
                content = self._convert_to_format()
                return SerializationResult(text=content)
    """

    def __init__(
        self,
        doc: DoclingDocument,
        params: CustomSerializerParams | None = None,
        component_serializers: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the custom serializer following Docling patterns.

        Args:
            doc: The DoclingDocument to serialize
            params: Optional parameters object for configuration
            component_serializers: Optional component serializers for specific elements
            **kwargs: Additional configuration parameters
        """
        super().__init__(doc=doc, **kwargs)
        self.params = params or CustomSerializerParams()
        self.component_serializers = component_serializers or {}
        self.config = kwargs
        self._validate_configuration()

    @property
    @abstractmethod
    def output_format(self) -> str:
        """Output format identifier.

        Returns:
            str: Format identifier (e.g., "yaml", "xml", "custom")
        """
        raise NotImplementedError("Subclasses must define output_format")

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Default file extension for output files.

        Returns:
            str: File extension including the dot (e.g., ".yaml", ".xml")
        """
        raise NotImplementedError("Subclasses must define file_extension")

    @property
    def format_description(self) -> str | None:
        """Optional detailed description of the output format.

        Returns:
            Optional[str]: Detailed description of the format
        """
        return None

    @property
    def version(self) -> str:
        """Version of this serializer implementation.

        Returns:
            str: Version string (e.g., "1.0.0")
        """
        return "1.0.0"

    @property
    def capabilities(self) -> dict[str, bool]:
        """Capabilities supported by this serializer.

        Returns:
            Dict[str, bool]: Dictionary of capability flags
        """
        return {
            "text_content": True,
            "document_structure": True,
            "metadata": False,
            "images": False,
            "tables": False,
            "formatting": False,
        }

    @property
    def mimetype(self) -> str:
        """MIME type for the output format.

        Returns:
            str: MIME type (e.g., "application/x-yaml", "text/xml")
        """
        return "text/plain"

    @abstractmethod
    def serialize(self) -> SerializationResult:
        """Convert DoclingDocument to target format.

        This is the main method that performs the serialization. It should
        process the DoclingDocument and return the serialized content.

        Returns:
            SerializationResult: The serialized content with metadata

        Raises:
            NotImplementedError: If not implemented by subclass
            ValueError: If serialization fails due to invalid content
        """
        raise NotImplementedError("Subclasses must implement serialize method")

    def get_supported_features(self) -> dict[str, bool]:
        """Get features supported by this serializer.

        Returns:
            Dict[str, bool]: Dictionary mapping feature names to support status
        """
        return self.capabilities.copy()

    def validate_document(self, doc: DoclingDocument) -> None:
        """Validate that the document can be serialized by this format.

        Args:
            doc: Document to validate

        Raises:
            ValueError: If the document cannot be serialized
        """
        if not doc:
            raise ValueError("Document cannot be None")

        # Subclasses can override to add format-specific validation

    def get_metadata(self) -> dict[str, Any]:
        """Get serializer metadata.

        Returns:
            Dict[str, Any]: Dictionary of serializer metadata
        """
        return {
            "output_format": self.output_format,
            "file_extension": self.file_extension,
            "version": self.version,
            "capabilities": self.capabilities,
            "mimetype": self.mimetype,
        }

    def _validate_configuration(self) -> None:
        """Validate serializer configuration and properties.

        This method is called during initialization to ensure the serializer
        is properly configured. Subclasses can override to add custom validation.

        Raises:
            ValueError: If the configuration is invalid
        """
        if not self.output_format:
            raise ValueError(f"{self.__class__.__name__} must define output_format")

        if not self.file_extension:
            raise ValueError(f"{self.__class__.__name__} must define file_extension")

        if not self.file_extension.startswith("."):
            raise ValueError(f"File extension must start with '.', got: {self.file_extension}")

    def _serialize_text_content(self) -> str:
        """Helper method to extract plain text content from document.

        This is a utility method that subclasses can use to extract
        the text content from the document for serialization.

        Returns:
            str: Plain text content of the document
        """
        if not hasattr(self.doc, "body") or not self.doc.body:
            return ""

        # Extract text from document body
        # This is a simple implementation - subclasses may need more sophisticated parsing
        text_parts = []

        def extract_text(item):
            if hasattr(item, "text") and item.text:
                text_parts.append(item.text)
            if hasattr(item, "children"):
                for child in item.children:
                    extract_text(child)

        extract_text(self.doc.body)
        return "\n".join(text_parts)

    def _serialize_with_structure(self) -> dict[str, Any]:
        """Helper method to serialize document with structure preservation.

        This method creates a structured representation of the document
        that preserves hierarchy and metadata. Subclasses can use this
        as a base for their format-specific serialization.

        Returns:
            Dict[str, Any]: Structured representation of the document
        """
        result = {
            "metadata": {
                "name": getattr(self.doc, "name", ""),
                "origin": getattr(self.doc, "origin", {}),
            },
            "content": {},
        }

        if hasattr(self.doc, "body") and self.doc.body:
            result["content"]["body"] = self._item_to_dict(self.doc.body)

        if hasattr(self.doc, "furniture"):
            result["content"]["furniture"] = [
                self._item_to_dict(item) for item in self.doc.furniture
            ]

        return result

    def _item_to_dict(self, item) -> dict[str, Any]:
        """Convert a document item to dictionary representation.

        Args:
            item: Document item to convert

        Returns:
            Dict[str, Any]: Dictionary representation of the item
        """
        result = {}

        if hasattr(item, "text") and item.text:
            result["text"] = item.text

        if hasattr(item, "label") and item.label:
            result["label"] = item.label

        if hasattr(item, "children") and item.children:
            result["children"] = [self._item_to_dict(child) for child in item.children]

        return result

    def _apply_component_serializers(self, content: str) -> str:
        """Apply component serializers to process specific elements.

        This method allows component serializers to process specific
        parts of the content (e.g., images, tables) before final serialization.

        Args:
            content: Content to process

        Returns:
            str: Processed content
        """
        # Base implementation - subclasses can override for format-specific processing
        return content

    def __str__(self) -> str:
        """String representation of the serializer."""
        return f"{self.__class__.__name__}({self.output_format} v{self.version})"

    def __repr__(self) -> str:
        """Detailed representation of the serializer."""
        return (
            f"{self.__class__.__name__}("
            f"output_format='{self.output_format}', "
            f"version='{self.version}', "
            f"extension='{self.file_extension}')"
        )
