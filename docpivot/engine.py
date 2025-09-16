"""DocPivotEngine - Simple API for document format conversion."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from docling_core.types.doc.document import DoclingDocument

# Optional import for PDF conversion
if TYPE_CHECKING:
    from docling.document_converter import DocumentConverter

try:
    from docling.document_converter import DocumentConverter

    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False
    DocumentConverter = None  # type: ignore[misc, assignment]

from docpivot.io.readers.readerfactory import ReaderFactory
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer


@dataclass
class ConversionResult:
    """Result of a document conversion."""

    content: str  # The converted content (JSON, etc.)
    format: str  # Output format used
    metadata: dict[str, Any]  # Conversion metadata


class DocPivotEngine:
    """Simple API for document format conversion.

    Provides one-line conversion between document formats with
    smart defaults and minimal configuration.

    Examples:
        # Simple usage
        engine = DocPivotEngine()
        result = engine.convert_to_lexical(doc)

        # From file
        result = engine.convert_file("document.pdf", "lexical")

        # With custom config
        engine = DocPivotEngine(lexical_config={"pretty": True})
    """

    def __init__(
        self, lexical_config: dict[str, Any] | None = None, default_format: str = "lexical"
    ):
        """Initialize with smart defaults.

        Args:
            lexical_config: Optional configuration for Lexical serialization
            default_format: Default output format (default: "lexical")
        """
        self.lexical_config = lexical_config or self._get_default_lexical_config()
        self.default_format = default_format
        self._serializer: LexicalDocSerializer | None = None  # Lazy init
        self._reader_factory = ReaderFactory()
        self._converter: DocumentConverter | None = None  # Lazy init for DocumentConverter

    def _get_default_lexical_config(self) -> dict[str, Any]:
        """Get default configuration for Lexical JSON serialization."""
        return {
            "pretty": False,  # Compact by default
            "indent": 2,  # If pretty=True
            "include_metadata": True,
            "preserve_formatting": True,
            "handle_tables": True,
            "handle_lists": True,
            "handle_images": False,  # Skip images by default for smaller output
        }

    def convert_to_lexical(
        self, document: DoclingDocument, pretty: bool = False, **kwargs: Any
    ) -> ConversionResult:
        """Convert DoclingDocument to Lexical JSON format.

        Args:
            document: The document to convert
            pretty: Pretty-print the output
            **kwargs: Additional serializer options

        Returns:
            ConversionResult with the JSON content
        """
        # Lazy init serializer
        if self._serializer is None:
            self._serializer = LexicalDocSerializer(document)
        else:
            # Re-init with new document
            self._serializer = LexicalDocSerializer(document)

        # Merge configurations
        config = {**self.lexical_config, **kwargs}
        if pretty:
            config["pretty"] = True

        # Serialize
        result = self._serializer.serialize()

        # Safe element counting
        elements_count = 0
        try:
            if hasattr(document, "body") and hasattr(document.body, "items"):
                elements_count = len(document.body.items)
        except AttributeError:
            pass

        return ConversionResult(
            content=result.text,
            format="lexical",
            metadata={
                "pretty": pretty,
                "document_name": document.name if hasattr(document, "name") else None,
                "elements_count": elements_count,
            },
        )

    def convert_file(
        self,
        input_path: str | Path,
        output_format: str = "lexical",
        output_path: str | Path | None = None,
        **kwargs: Any,
    ) -> ConversionResult:
        """Convert a file to the specified format.

        Args:
            input_path: Path to input file
            output_format: Target format (default: "lexical")
            output_path: Optional output file path
            **kwargs: Additional conversion options

        Returns:
            ConversionResult with the converted content
        """
        # Load document
        reader = self._reader_factory.get_reader(input_path)
        document = reader.load_data(input_path)

        # Convert based on format
        if output_format == "lexical":
            result = self.convert_to_lexical(document, **kwargs)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        # Write to file if requested
        if output_path:
            Path(output_path).write_text(result.content)
            result.metadata["output_path"] = str(output_path)

        return result

    def convert_pdf(
        self, pdf_path: str | Path, output_format: str = "lexical", **kwargs: Any
    ) -> ConversionResult:
        """Convert PDF to specified format using Docling.

        Args:
            pdf_path: Path to PDF file
            output_format: Target format (default: "lexical")
            **kwargs: Additional conversion options

        Returns:
            ConversionResult with the converted content

        Raises:
            ImportError: If docling package is not installed
        """
        if not HAS_DOCLING:
            raise ImportError(
                "PDF conversion requires the 'docling' package. "
                "Install it with: pip install docling"
            )

        if self._converter is None:
            self._converter = DocumentConverter()

        # Convert PDF to DoclingDocument
        result = self._converter.convert(str(pdf_path))
        document = result.document

        # Convert to target format
        if output_format == "lexical":
            return self.convert_to_lexical(document, **kwargs)
        raise ValueError(f"Unsupported output format: {output_format}")

    @classmethod
    def builder(cls) -> Any:  # Returns DocPivotEngineBuilder
        """Get a builder for advanced configuration.

        Returns:
            DocPivotEngineBuilder instance for fluent configuration
        """
        # Import here to avoid circular dependency
        from .engine_builder import DocPivotEngineBuilder

        return DocPivotEngineBuilder()
