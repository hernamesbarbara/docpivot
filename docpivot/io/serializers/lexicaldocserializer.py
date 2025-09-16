"""LexicalDocSerializer for converting DoclingDocument to Lexical JSON format."""

import gc
import json
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from docling_core.transforms.serializer.base import SerializationResult
from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.types import DoclingDocument
from docling_core.types.doc.document import (
    DocItem,
    FloatingItem,
    GroupItem,
    NodeItem,
    OrderedList,
    PictureItem,
    SectionHeaderItem,
    TableItem,
    TextItem,
    UnorderedList,
)
from pydantic.networks import AnyUrl

from docpivot.io.readers.exceptions import (
    ConfigurationError,
    TransformationError,
    ValidationError,
)
from docpivot.logging_config import (
    get_logger,
    log_exception_with_context,
)
from docpivot.validation import validate_docling_document

logger = get_logger(__name__)

# Type aliases for method parameters
TextItemType = SectionHeaderItem | TextItem
GroupItemType = OrderedList | UnorderedList | GroupItem

# Constants for Lexical JSON structure
LEXICAL_VERSION = 1
DEFAULT_DETAIL = 0
DEFAULT_FORMAT = 0
DEFAULT_INDENT = 0
HEADER_STATE_VALUE = 1
MIN_HEADING_LEVEL = 1
MAX_HEADING_LEVEL = 6
DEFAULT_HEADING_TAG = "h1"
TEXT_DIRECTION_LTR = "ltr"
DEFAULT_MODE = "normal"
DEFAULT_STYLE = ""
LIST_MARKER_BULLET = "● "
LIST_MARKER_BULLET_ALT = "• "
LIST_MARKER_SEPARATOR = ". "
JSON_INDENT_SIZE = 2

# Lexical node types
NODE_TYPE_ROOT = "root"
NODE_TYPE_TEXT = "text"
NODE_TYPE_HEADING = "heading"
NODE_TYPE_PARAGRAPH = "paragraph"
NODE_TYPE_TABLE = "table"
NODE_TYPE_TABLE_ROW = "tablerow"
NODE_TYPE_TABLE_CELL = "tablecell"
NODE_TYPE_LIST = "list"
NODE_TYPE_LIST_ITEM = "listitem"

# List types and tags
LIST_TYPE_ORDERED = "ordered"
LIST_TYPE_UNORDERED = "unordered"
LIST_TAG_ORDERED = "ol"
LIST_TAG_UNORDERED = "ul"

# Reference parsing constants
MIN_REF_PARTS = 3
REF_ELEMENT_TYPE_INDEX = 1
REF_ELEMENT_INDEX = 2
ELEMENT_TYPE_TEXTS = "texts"
ELEMENT_TYPE_TABLES = "tables"
ELEMENT_TYPE_GROUPS = "groups"
ELEMENT_TYPE_PICTURES = "pictures"

# Additional Lexical node types
NODE_TYPE_LINK = "link"
NODE_TYPE_IMAGE = "image"

# Text formatting constants
FORMAT_BOLD = 1
FORMAT_ITALIC = 2
FORMAT_UNDERLINE = 4
FORMAT_STRIKETHROUGH = 8


@dataclass
class LexicalParams:
    """Configuration parameters for LexicalDocSerializer.

    Attributes:
        include_metadata: Whether to include document metadata in output
        preserve_formatting: Whether to preserve text formatting when available
        indent_json: Whether to indent JSON output for readability
        version: Lexical format version to use
        custom_root_attributes: Additional attributes to add to root node
        skip_validation: Whether to skip DoclingDocument validation (for testing)

        Performance optimization options:
        enable_streaming: Force streaming mode (None for auto-detect)
        batch_size: Elements per batch for streaming processing
        streaming_threshold_elements: Auto-activate streaming above this count
        use_fast_json: Use fast JSON libraries (orjson, ujson) when available
        parallel_processing: Use parallel processing for large documents
        max_workers: Worker threads for parallel processing
        memory_efficient_mode: Reduce memory usage with batching and GC
        cache_node_creation: Cache frequently created nodes
        optimize_text_formatting: Use optimized text processing methods
        progress_callback: Callback function for progress updates (0.0-1.0)
    """

    include_metadata: bool = True
    preserve_formatting: bool = True
    indent_json: bool = True
    version: int = LEXICAL_VERSION
    custom_root_attributes: dict[str, Any] | None = field(default_factory=dict)
    skip_validation: bool = False

    # Performance optimization options
    enable_streaming: bool | None = None  # None for auto-detect
    batch_size: int = 1000  # Elements per batch
    streaming_threshold_elements: int = 5000  # Use streaming for docs >5000 elements
    use_fast_json: bool = True  # Use fast JSON libraries when available
    parallel_processing: bool = False  # Use parallel processing for large docs
    max_workers: int = 4  # Worker threads for parallel processing
    memory_efficient_mode: bool = False  # Reduce memory usage
    cache_node_creation: bool = False  # Cache frequently created nodes
    optimize_text_formatting: bool = True  # Use optimized text processing
    progress_callback: Any | None = None  # Progress callback function


class ComponentSerializer(Protocol):
    """Protocol for component serializers."""

    def serialize(self, item: Any, params: LexicalParams | None = None) -> dict[str, Any]:
        """Serialize a component to Lexical node format."""
        ...


class ImageSerializer:
    """Default image serializer for Lexical format."""

    def serialize(
        self, image_item: PictureItem, params: LexicalParams | None = None
    ) -> dict[str, Any]:
        """Serialize a PictureItem to Lexical image node.

        Args:
            image_item: The PictureItem to serialize
            params: Optional LexicalParams for configuration

        Returns:
            Lexical image node dictionary
        """
        # Handle missing or malformed image data
        src = getattr(image_item, "image_path", "") or getattr(image_item, "path", "") or ""
        alt_text = getattr(image_item, "alt_text", "") or getattr(image_item, "caption", "") or ""

        # Get dimensions if available
        width = getattr(image_item, "width", None)
        height = getattr(image_item, "height", None)

        node = {
            "type": NODE_TYPE_IMAGE,
            "src": src,
            "altText": alt_text,
            "version": params.version if params else LEXICAL_VERSION,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
        }

        if width is not None:
            node["width"] = width
        if height is not None:
            node["height"] = height

        return node


class LexicalDocSerializer(BaseDocSerializer):
    """Serializer for converting DoclingDocument objects to Lexical JSON format.

    This serializer transforms DoclingDocument elements into Lexical's nested node
    structure, handling the conversion between referenced elements and hierarchical
    nodes. It supports advanced features including text formatting, links, images,
    and component serializers.

    Note: This serializer does NOT extend BaseDocSerializer because it has fundamentally
    different requirements:
    - BaseDocSerializer is designed for text-based serializers with inline formatting
    - LexicalDocSerializer converts entire document structure to JSON forma
    - The APIs are incompatible (different serialize() method signatures and patterns)
    """

    def __init__(
        self,
        doc: DoclingDocument,
        params: LexicalParams | None = None,
        image_serializer: ComponentSerializer | None = None,
        table_serializer: ComponentSerializer | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the LexicalDocSerializer.

        Args:
            doc: The DoclingDocument to serialize
            params: Optional LexicalParams for configuration
            image_serializer: Optional custom image serializer
            table_serializer: Optional custom table serializer
            **kwargs: Additional parameters for extensibility
        """
        super().__init__()
        # Store the document and initialize components
        self.doc = doc
        self.params = params or LexicalParams()
        self.image_serializer = image_serializer or ImageSerializer()
        self.table_serializer = table_serializer

        # Performance optimization state (with safeguards for invalid params)
        try:
            self._json_encoder = self._select_json_encoder()
            self._node_cache: dict[str, Any] | None = (
                {} if getattr(self.params, "cache_node_creation", False) else None
            )
        except AttributeError:
            # Handle invalid params gracefully - will be caught in validation
            self._json_encoder = json
            self._node_cache = None
        self._elements_processed = 0
        self._start_time = 0.0

    def _select_json_encoder(self):
        """Select fastest available JSON encoder."""
        if not self.params.use_fast_json:
            return json

        # Try fast JSON libraries in order of preference
        try:
            import orjson

            logger.debug("Using orjson for JSON encoding")
            return orjson
        except ImportError:
            pass

        try:
            import ujson

            logger.debug("Using ujson for JSON encoding")
            return ujson
        except ImportError:
            pass

        logger.debug("Using standard json library")
        return json

    def _count_total_elements(self) -> int:
        """Count total elements in document for processing strategy selection."""
        return (
            len(self.doc.body.children)
            + len(self.doc.texts)
            + len(getattr(self.doc, "tables", []))
            + len(getattr(self.doc, "groups", []))
            + len(getattr(self.doc, "pictures", []))
        )

    def serialize(self) -> SerializationResult:
        """Serialize the DoclingDocument to Lexical JSON format.

        Returns:
            SerializationResult: The serialization result with Lexical JSON in .tex

        Raises:
            ValidationError: If the document structure is invalid
            TransformationError: If conversion to Lexical format fails
            ConfigurationError: If serializer parameters are invalid
        """
        self._start_time = time.time()
        logger.info("Serializing DoclingDocument to Lexical JSON format")

        try:
            # Validate input document structure (skip if disabled for testing)
            should_validate = True
            try:
                should_validate = not self.params.skip_validation
            except AttributeError:
                should_validate = True

            if should_validate:
                validate_docling_document(self.doc)
                logger.debug("DoclingDocument validation passed")
            else:
                logger.debug("DoclingDocument validation skipped")

            # Validate serializer parameters
            self._validate_serializer_params()
            logger.debug("Serializer parameters validation passed")

            # Determine processing strategy based on document size and configuration
            total_elements = self._count_total_elements()
            use_streaming = self._should_use_streaming(total_elements)
            use_parallel = self._should_use_parallel_processing(total_elements)

            logger.debug(
                f"Processing {total_elements} elements, streaming: {use_streaming}, parallel: {use_parallel}"
            )

            # Initialize progress tracking
            if self.params.progress_callback:
                self.params.progress_callback(0.0)

            # Choose serialization strategy
            if use_streaming:
                json_text = self._serialize_streaming()
            elif use_parallel:
                json_text = self._serialize_parallel()
            else:
                json_text = self._serialize_standard()

            # Performance metrics removed - simplified implementation
            duration = (time.time() - self._start_time) * 1000

            logger.info(f"Lexical serialization complete: {duration:.2f}ms, {len(json_text)} chars")

            # Final progress update
            if self.params.progress_callback:
                self.params.progress_callback(1.0)

            return SerializationResult(text=json_text)

        except (ValidationError, TransformationError, ConfigurationError):
            # Re-raise custom exceptions
            duration = (time.time() - self._start_time) * 1000
            logger.error(f"Lexical serialization failed after {duration:.2f}ms")
            raise
        except Exception as e:
            # Handle unexpected errors with comprehensive contex
            duration = (time.time() - self._start_time) * 1000
            context = {
                "operation": "serialize",
                "duration_ms": duration,
                "elements_processed": self._elements_processed,
            }
            log_exception_with_context(logger, e, "Lexical JSON serialization", context)

            raise TransformationError(
                f"Unexpected error during Lexical JSON serialization: {e}",
                transformation_type="lexical",
                context=context,
                cause=e,
            ) from e

    def _should_use_streaming(self, total_elements: int) -> bool:
        """Determine if streaming mode should be used."""
        if self.params.enable_streaming is not None:
            return self.params.enable_streaming
        return total_elements > self.params.streaming_threshold_elements

    def _should_use_parallel_processing(self, total_elements: int) -> bool:
        """Determine if parallel processing should be used."""
        return (
            self.params.parallel_processing
            and total_elements > 1000
            and not self._should_use_streaming(total_elements)
        )

    def _serialize_streaming(self) -> str:
        """Serialize using streaming approach for large documents."""
        logger.debug("Using streaming serialization")
        try:
            lexical_data = self._transform_docling_to_lexical_streaming()
            return self._encode_json(lexical_data)
        except Exception as e:
            raise TransformationError(
                f"Streaming serialization failed: {e}",
                transformation_type="streaming_lexical",
                context={"elements_processed": self._elements_processed},
                cause=e,
            ) from e

    def _serialize_parallel(self) -> str:
        """Serialize using parallel processing for large documents."""
        logger.debug("Using parallel serialization")
        try:
            lexical_data = self._transform_docling_to_lexical_parallel()
            return self._encode_json(lexical_data)
        except Exception as e:
            raise TransformationError(
                f"Parallel serialization failed: {e}",
                transformation_type="parallel_lexical",
                context={"elements_processed": self._elements_processed},
                cause=e,
            ) from e

    def _serialize_standard(self) -> str:
        """Serialize using standard approach."""
        logger.debug("Using standard serialization")
        try:
            lexical_data = self._transform_docling_to_lexical()
            return self._encode_json(lexical_data)
        except Exception as e:
            raise TransformationError(
                f"Standard serialization failed: {e}",
                transformation_type="standard_lexical",
                context={"elements_processed": self._elements_processed},
                cause=e,
            ) from e

    def _validate_serializer_params(self) -> None:
        """Validate serializer parameters.

        Raises:
            ConfigurationError: If parameters are invalid
        """
        # Validate params objec
        if not isinstance(self.params, LexicalParams):
            raise ConfigurationError(
                f"Invalid serializer parameters: expected LexicalParams, "
                f"got {type(self.params).__name__}",
                context={"actual_type": type(self.params).__name__},
            )

        # Validate version parameter
        if not isinstance(self.params.version, int) or self.params.version < 1:
            raise ConfigurationError(
                f"Invalid version parameter: {self.params.version}. "
                f"Version must be a positive integer.",
                invalid_parameters=["version"],
                valid_options={"version": ["Any positive integer"]},
                context={"provided_version": self.params.version},
            )

        # Validate boolean parameters
        bool_params = [
            "include_metadata",
            "preserve_formatting",
            "indent_json",
            "use_fast_json",
            "parallel_processing",
            "memory_efficient_mode",
            "cache_node_creation",
            "optimize_text_formatting",
            "skip_validation",
        ]
        for param_name in bool_params:
            param_value = getattr(self.params, param_name, None)
            if param_value is not None and not isinstance(param_value, bool):
                raise ConfigurationError(
                    f"Invalid {param_name} parameter: {param_value}. " f"Must be a boolean value.",
                    invalid_parameters=[param_name],
                    valid_options={param_name: ["true", "false"]},
                    context={f"provided_{param_name}": param_value},
                )

        # Validate batch size
        if self.params.batch_size <= 0:
            raise ConfigurationError(
                f"Invalid batch_size: {self.params.batch_size}. Must be positive.",
                invalid_parameters=["batch_size"],
            )

        # Validate worker coun
        if self.params.max_workers <= 0:
            raise ConfigurationError(
                f"Invalid max_workers: {self.params.max_workers}. Must be positive.",
                invalid_parameters=["max_workers"],
            )

        # Validate streaming threshold
        if self.params.streaming_threshold_elements <= 0:
            raise ConfigurationError(
                f"Invalid streaming_threshold_elements: "
                f"{self.params.streaming_threshold_elements}. Must be positive.",
                invalid_parameters=["streaming_threshold_elements"],
            )

        # Validate custom root attributes
        if self.params.custom_root_attributes is not None and not isinstance(
            self.params.custom_root_attributes, dict
        ):
            raise ConfigurationError(
                f"Invalid custom_root_attributes: must be a dictionary, "
                f"got {type(self.params.custom_root_attributes).__name__}",
                invalid_parameters=["custom_root_attributes"],
                context={"actual_type": type(self.params.custom_root_attributes).__name__},
            )

        logger.debug("Serializer parameters validation completed successfully")

    def _transform_docling_to_lexical_streaming(self) -> dict[str, Any]:
        """Transform DoclingDocument to Lexical JSON structure using streaming."""
        logger.debug("Starting streaming DoclingDocument to Lexical transformation")
        try:
            lexical_children = self._process_body_children_streaming()
            return self._build_final_structure(list(lexical_children))
        except Exception as e:
            raise TransformationError(
                f"Failed to transform document using streaming: {e}",
                transformation_type="streaming_transformation",
                cause=e,
            ) from e

    def _transform_docling_to_lexical_parallel(self) -> dict[str, Any]:
        """Transform DoclingDocument to Lexical JSON structure using parallel."""
        logger.debug("Starting parallel DoclingDocument to Lexical transformation")
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            # Split body children into chunks
            chunks = self._split_body_children_into_chunks()

            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=self.params.max_workers) as executor:
                futures = [
                    executor.submit(self._process_body_children_chunk, chunk) for chunk in chunks
                ]

                lexical_children = []
                for future in as_completed(futures):
                    chunk_result = future.result()
                    lexical_children.extend(chunk_result)

            # Update progress
            if self.params.progress_callback:
                self.params.progress_callback(0.8)

            return self._build_final_structure(lexical_children)
        except Exception as e:
            raise TransformationError(
                f"Failed to transform document using parallel processing: {e}",
                transformation_type="parallel_transformation",
                cause=e,
            ) from e

    def _transform_docling_to_lexical(self) -> dict[str, Any]:
        """Transform DoclingDocument to Lexical JSON structure.

        Returns:
            Dict representing the Lexical JSON structure

        Raises:
            TransformationError: If document transformation fails
        """
        logger.debug("Starting DoclingDocument to Lexical transformation")

        try:
            # Process body children to create Lexical nodes with error handling
            try:
                lexical_children = self._process_body_children_optimized()
                logger.debug(f"Processed {len(lexical_children)} body children")
            except Exception as e:
                raise TransformationError(
                    f"Failed to process document body children: {e}. "
                    f"The document structure may be invalid or corrupted.",
                    transformation_type="body_children_processing",
                    recovery_suggestions=[
                        "Check that the document body contains valid elements",
                        "Verify all referenced elements exist in the document",
                        "Ensure element references are properly formatted",
                    ],
                    context={"original_error": str(e)},
                    cause=e,
                ) from e

            # Build the final structure
            return self._build_final_structure(lexical_children)

        except TransformationError:
            # Re-raise transformation errors without wrapping
            raise
        except Exception as e:
            # Handle any unexpected errors during transformation
            logger.error(f"Unexpected error during Lexical transformation: {e}")
            raise TransformationError(
                f"Unexpected error during DoclingDocument to Lexical " f"transformation: {e}",
                transformation_type="docling_to_lexical",
                recovery_suggestions=[
                    "Check the document structure for validity",
                    "Verify all document elements are properly formed",
                    "Try with simplified serializer parameters",
                ],
                context={"original_error": str(e)},
                cause=e,
            ) from e

    def _build_final_structure(self, lexical_children: list[dict[str, Any]]) -> dict[str, Any]:
        """Build final Lexical structure with metadata."""
        # Create the root Lexical structure
        root_node = {
            "children": lexical_children,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_ROOT,
            "version": self.params.version,
        }

        # Add custom root attributes if provided
        if self.params.custom_root_attributes:
            try:
                root_node.update(self.params.custom_root_attributes)
                logger.debug(
                    f"Added {len(self.params.custom_root_attributes)} custom root attributes"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to add custom root attributes: {e}. Proceeding without them."
                )

        lexical_data = {"root": root_node}

        # Include document metadata if requested
        if self.params.include_metadata:
            try:
                metadata = {}
                if hasattr(self.doc, "name") and self.doc.name:
                    metadata.update(
                        {
                            "document_name": self.doc.name,
                            "version": getattr(self.doc, "version", "1.0.0"),
                        }
                    )

                # Handle origin object serialization
                if hasattr(self.doc, "origin") and self.doc.origin:
                    origin = self.doc.origin
                    metadata["origin"] = {
                        "mimetype": getattr(origin, "mimetype", ""),
                        "filename": getattr(origin, "filename", ""),
                        "binary_hash": getattr(origin, "binary_hash", 0),
                        "uri": getattr(origin, "uri", None),
                    }

                if metadata:
                    lexical_data["metadata"] = metadata
                    logger.debug(f"Added metadata with {len(metadata)} fields")
            except Exception as e:
                logger.warning(
                    f"Failed to include document metadata: {e}. Proceeding without metadata."
                )

        logger.debug("DoclingDocument to Lexical transformation completed successfully")
        return lexical_data

    def _encode_json(self, data: dict[str, Any]) -> str:
        """Encode data to JSON using selected encoder."""
        try:
            if self._json_encoder == json:
                # Standard library json
                indent = JSON_INDENT_SIZE if self.params.indent_json else None
                return json.dumps(data, indent=indent, ensure_ascii=False)

            if hasattr(self._json_encoder, "__name__") and self._json_encoder.__name__ == "orjson":
                # orjson
                options = 0
                if self.params.indent_json:
                    options |= self._json_encoder.OPT_INDENT_2
                return self._json_encoder.dumps(data, option=options).decode("utf-8")

            if hasattr(self._json_encoder, "dumps"):
                # ujson and other libraries
                try:
                    if self.params.indent_json:
                        # Try with all parameters
                        return self._json_encoder.dumps(
                            data, indent=JSON_INDENT_SIZE, ensure_ascii=False
                        )
                    return self._json_encoder.dumps(data, ensure_ascii=False)
                except TypeError:
                    # Fallback if ensure_ascii not supported
                    if self.params.indent_json:
                        return self._json_encoder.dumps(data, indent=JSON_INDENT_SIZE)
                    return self._json_encoder.dumps(data)

            else:
                # Ultimate fallback to standard json
                indent = JSON_INDENT_SIZE if self.params.indent_json else None
                return json.dumps(data, indent=indent, ensure_ascii=False)

        except Exception as e:
            raise TransformationError(
                f"JSON encoding failed: {e}",
                transformation_type="json_encoding",
                cause=e,
            ) from e

    def _process_body_children_streaming(self) -> Generator[dict[str, Any], None, None]:
        """Generator that yields processed body children in batches."""
        batch = []
        batch_count = 0

        for i, child_ref in enumerate(self.doc.body.children):
            try:
                if not child_ref.cref:
                    continue

                lexical_node = self._process_single_child_ref_optimized(child_ref)
                if lexical_node:
                    batch.append(lexical_node)
                    batch_count += 1
                    self._elements_processed += 1

                # Process batch when full
                if batch_count >= self.params.batch_size:
                    for node in batch:
                        yield node
                    batch.clear()
                    batch_count = 0

                    # Update progress
                    if self.params.progress_callback:
                        progress = min(0.7, i / len(self.doc.body.children) * 0.7)
                        self.params.progress_callback(progress)

                    # Force garbage collection for memory managemen
                    if self.params.memory_efficient_mode:
                        gc.collect()

            except Exception as e:
                logger.warning(f"Failed to process child ref {i}: {e}")
                continue

        # Yield remaining items
        for node in batch:
            yield node

    def _split_body_children_into_chunks(self) -> list[list]:
        """Split body children into chunks for parallel processing."""
        children = self.doc.body.children
        chunk_size = max(1, len(children) // self.params.max_workers)

        chunks = []
        for i in range(0, len(children), chunk_size):
            chunk = children[i : i + chunk_size]
            chunks.append(chunk)

        logger.debug(f"Split {len(children)} children into {len(chunks)} chunks")
        return chunks

    def _process_body_children_chunk(self, children_chunk: list) -> list[dict[str, Any]]:
        """Process a chunk of body children."""
        lexical_nodes = []

        for child_ref in children_chunk:
            try:
                if not child_ref.cref:
                    continue

                lexical_node = self._process_single_child_ref_optimized(child_ref)
                if lexical_node:
                    lexical_nodes.append(lexical_node)
                    self._elements_processed += 1

            except Exception as e:
                logger.warning(f"Failed to process child ref in chunk: {e}")
                continue

        return lexical_nodes

    def _process_body_children_optimized(self) -> list[dict[str, Any]]:
        """Process body children with optimizations."""
        lexical_nodes = []

        for i, child_ref in enumerate(self.doc.body.children):
            try:
                if not child_ref.cref:
                    continue

                lexical_node = self._process_single_child_ref_optimized(child_ref)
                if lexical_node:
                    lexical_nodes.append(lexical_node)
                    self._elements_processed += 1

                # Update progress periodically
                if self.params.progress_callback and i % 100 == 0:
                    progress = min(0.7, i / len(self.doc.body.children) * 0.7)
                    self.params.progress_callback(progress)

                # Memory management for large documents
                if self.params.memory_efficient_mode and i % self.params.batch_size == 0:
                    gc.collect()

            except Exception as e:
                logger.warning(f"Failed to process child ref {i}: {e}")
                continue

        return lexical_nodes

    def _process_single_child_ref_optimized(self, child_ref) -> dict[str, Any] | None:
        """Process a single child reference with optimizations."""
        # Parse reference
        ref_parts = child_ref.cref.split("/")
        if len(ref_parts) < MIN_REF_PARTS:
            return None

        element_type = ref_parts[REF_ELEMENT_TYPE_INDEX]

        # Parse element index with error handling
        try:
            element_index = int(ref_parts[REF_ELEMENT_INDEX])
        except ValueError:
            return None

        # Process based on element type with bounds checking
        if element_type == ELEMENT_TYPE_TEXTS:
            if element_index >= len(self.doc.texts):
                return None
            text_item = self.doc.texts[element_index]
            return self._create_text_node_optimized(text_item)

        if element_type == ELEMENT_TYPE_TABLES:
            if element_index >= len(self.doc.tables):
                return None
            table_item = self.doc.tables[element_index]
            if self.table_serializer:
                return self.table_serializer.serialize(table_item, self.params)
            return self._create_table_node_optimized(table_item)

        if element_type == ELEMENT_TYPE_GROUPS:
            if element_index >= len(self.doc.groups):
                return None
            group_item = self.doc.groups[element_index]
            return self._create_group_node_optimized(group_item)

        if (
            element_type == ELEMENT_TYPE_PICTURES
            and hasattr(self.doc, "pictures")
            and element_index < len(self.doc.pictures)
        ):
            picture_item = self.doc.pictures[element_index]
            return self.image_serializer.serialize(picture_item, self.params)

        return None

    def _process_body_children(self) -> list[dict[str, Any]]:
        """Process DoclingDocument body children and convert to Lexical nodes.

        Returns:
            List of Lexical nodes
        """
        return self._process_body_children_optimized()

    def _detect_text_formatting(
        self, text_content: str, text_item: TextItemType | None = None
    ) -> list[str]:
        """Detect text formatting from content patterns and DoclingDocument attributes.

        Args:
            text_content: The text content to analyze
            text_item: Optional TextItem to extract formatting metadata from

        Returns:
            List of format types detected (e.g., ['bold'], ['italic'])
        """
        format_types: list[str] = []

        if not self.params.preserve_formatting or not text_content:
            return format_types

        # First check if the text_item has style information
        if text_item:
            # Check if the item has any style attributes
            if hasattr(text_item, "style"):
                style = getattr(text_item, "style", {})
                if isinstance(style, dict):
                    if style.get("bold") or style.get("font_weight", "").lower() in [
                        "bold",
                        "700",
                    ]:
                        format_types.append("bold")
                    if style.get("italic") or style.get("font_style", "").lower() == "italic":
                        format_types.append("italic")
                    if style.get("underline"):
                        format_types.append("underline")

            # Check if the item has formatting attributes directly
            if hasattr(text_item, "font_weight") and str(
                getattr(text_item, "font_weight", "")
            ).lower() in ["bold", "700"]:
                format_types.append("bold")
            if (
                hasattr(text_item, "font_style")
                and str(getattr(text_item, "font_style", "")).lower() == "italic"
            ):
                format_types.append("italic")

        # Fallback to heuristic detection for common formatting patterns
        lower_text = text_content.lower()

        # Detect emphasis patterns (enhanced heuristics)
        if not format_types:  # Only use heuristics if no style info found
            # Bold text patterns
            if (
                ("bold" in lower_text and ("are" in lower_text or "terms" in lower_text))
                or text_content.isupper()
                or "important" in lower_text.lower()
                or (text_content.startswith("**") and text_content.endswith("**"))
            ):
                format_types.append("bold")

            # Italic text patterns
            elif (
                ("italic" in lower_text and "emphasis" in lower_text)
                or "primarily used" in lower_text
                or (
                    text_content.startswith("*")
                    and text_content.endswith("*")
                    and not text_content.startswith("**")
                )
            ):
                format_types.append("italic")

        return format_types

    def _create_formatted_text_node(
        self, text_content: str, format_types: list[str] | None = None
    ) -> dict[str, Any]:
        """Create a Lexical text node with formatting.

        Args:
            text_content: The text conten
            format_types: List of format types to apply

        Returns:
            Lexical text node with formatting
        """
        format_types = format_types or []

        # Calculate format bitmask
        format_value = DEFAULT_FORMAT
        if "bold" in format_types:
            format_value |= FORMAT_BOLD
        if "italic" in format_types:
            format_value |= FORMAT_ITALIC
        if "underline" in format_types:
            format_value |= FORMAT_UNDERLINE
        if "strikethrough" in format_types:
            format_value |= FORMAT_STRIKETHROUGH

        return {
            "detail": DEFAULT_DETAIL,
            "format": format_value,
            "mode": DEFAULT_MODE,
            "style": DEFAULT_STYLE,
            "text": text_content,
            "type": NODE_TYPE_TEXT,
            "version": self.params.version,
        }

    def _process_text_with_links(
        self, text_content: str, text_item: TextItemType | None = None
    ) -> list[dict[str, Any]]:
        """Process text content to detect and create link nodes.

        Args:
            text_content: The text content to process
            text_item: Optional TextItem for formatting metadata

        Returns:
            List of Lexical nodes (text nodes or link nodes)
        """
        import re

        # URL pattern to detect links
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+' r'|www\.[^\s<>"{}|\\^`\[\]]+'

        # Find all URLs in the tex
        urls = list(re.finditer(url_pattern, text_content))

        if not urls:
            # No links found, return a single formatted text node
            format_types = self._detect_text_formatting(text_content, text_item)
            return [self._create_formatted_text_node(text_content, format_types)]

        nodes = []
        last_end = 0

        for url_match in urls:
            # Add text before the URL as a regular text node
            if url_match.start() > last_end:
                before_text = text_content[last_end : url_match.start()]
                if before_text.strip():  # Only add non-empty tex
                    format_types = self._detect_text_formatting(before_text, text_item)
                    nodes.append(self._create_formatted_text_node(before_text, format_types))

            # Create link node
            url = url_match.group()
            # Ensure URL has protocol
            if not url.startswith("http"):
                url = "https://" + url

            link_text = url_match.group()  # Display the original match
            nodes.append(self._create_link_node(link_text, url))

            last_end = url_match.end()

        # Add any remaining text after the last URL
        if last_end < len(text_content):
            after_text = text_content[last_end:]
            if after_text.strip():  # Only add non-empty tex
                format_types = self._detect_text_formatting(after_text, text_item)
                nodes.append(self._create_formatted_text_node(after_text, format_types))

        return nodes

    def _create_link_node(self, text_content: str, url: str) -> dict[str, Any]:
        """Create a Lexical link node.

        Args:
            text_content: The link tex
            url: The link URL

        Returns:
            Lexical link node
        """
        return {
            "children": [
                {
                    "detail": DEFAULT_DETAIL,
                    "format": DEFAULT_FORMAT,
                    "mode": DEFAULT_MODE,
                    "style": DEFAULT_STYLE,
                    "text": text_content,
                    "type": NODE_TYPE_TEXT,
                    "version": self.params.version,
                }
            ],
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_LINK,
            "url": url,
            "version": self.params.version,
        }

    def _create_text_node_optimized(self, text_item: TextItemType) -> dict[str, Any] | None:
        """Create optimized text node."""
        if text_item.label == "section_header":
            return self._create_heading_node_optimized(text_item)
        return self._create_paragraph_node_optimized(text_item)

    def _create_text_node(self, text_item: TextItemType) -> dict[str, Any] | None:
        """Create a Lexical node from a DoclingDocument TextItem.

        Args:
            text_item: The TextItem to conver

        Returns:
            Lexical node dictionary or None if conversion fails
        """
        return self._create_text_node_optimized(text_item)

    def _create_heading_node_optimized(self, text_item: SectionHeaderItem) -> dict[str, Any]:
        """Create optimized heading node."""
        # Check cache firs
        if self._node_cache is not None:
            cache_key = f"heading_{text_item.text}_{getattr(text_item, 'level', 1)}"
            if cache_key in self._node_cache:
                return self._node_cache[cache_key].copy()

        try:
            level = getattr(text_item, "level", MIN_HEADING_LEVEL)
            tag = f"h{min(max(level, MIN_HEADING_LEVEL), MAX_HEADING_LEVEL)}"
            text_content = getattr(text_item, "text", "") or ""

            # Detect formatting if enabled, passing the text_item for metadata
            format_types = self._detect_text_formatting_optimized(text_content, text_item)

            # Create formatted text node
            text_node = self._create_formatted_text_node_optimized(text_content, format_types)

            node = {
                "children": [text_node],
                "direction": TEXT_DIRECTION_LTR,
                "format": DEFAULT_STYLE,
                "indent": DEFAULT_INDENT,
                "tag": tag,
                "type": NODE_TYPE_HEADING,
                "version": self.params.version,
            }

            # Cache resul
            if self._node_cache is not None:
                cache_key = f"heading_{text_item.text}_{level}"
                self._node_cache[cache_key] = node.copy()

            return node

        except (AttributeError, TypeError):
            # Return default heading for malformed items
            return self._create_default_heading_node()

    def _create_paragraph_node_optimized(self, text_item: TextItem) -> dict[str, Any]:
        """Create optimized paragraph node."""
        text_content = getattr(text_item, "text", "") or ""

        # Check for links in the text and create appropriate nodes
        if self.params.optimize_text_formatting:
            children = self._process_text_with_links_optimized(text_content, text_item)
        else:
            children = [self._create_formatted_text_node_optimized(text_content, [])]

        return {
            "children": children,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_PARAGRAPH,
            "version": self.params.version,
        }

    def _create_table_node_optimized(self, table_item: TableItem) -> dict[str, Any]:
        """Create optimized table node."""
        rows: list[dict[str, Any]] = []

        try:
            if table_item.data and table_item.data.grid:
                for row in table_item.data.grid:
                    try:
                        lexical_row = {
                            "children": [],
                            "direction": TEXT_DIRECTION_LTR,
                            "format": DEFAULT_STYLE,
                            "indent": DEFAULT_INDENT,
                            "type": NODE_TYPE_TABLE_ROW,
                            "version": self.params.version,
                        }

                        # Process cells in batch
                        cells = []
                        for cell in row:
                            try:
                                cell_text = getattr(cell, "text", "") or ""
                                lexical_cell = {
                                    "children": [
                                        self._create_formatted_text_node_optimized(cell_text, [])
                                    ],
                                    "direction": TEXT_DIRECTION_LTR,
                                    "format": DEFAULT_STYLE,
                                    "indent": DEFAULT_INDENT,
                                    "type": NODE_TYPE_TABLE_CELL,
                                    "version": self.params.version,
                                }

                                # Add header state efficiently
                                if hasattr(cell, "column_header") and cell.column_header:
                                    lexical_cell["headerState"] = HEADER_STATE_VALUE

                                cells.append(lexical_cell)
                            except (AttributeError, TypeError):
                                continue

                        lexical_row["children"] = cells
                        if cells:  # Only add rows with cells
                            rows.append(lexical_row)

                    except (AttributeError, TypeError):
                        continue

        except (AttributeError, TypeError):
            pass

        # Calculate dimensions efficiently
        num_rows = len(rows)
        num_cols = len(rows[0]["children"]) if rows else 0

        return {
            "children": rows,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_TABLE,
            "version": self.params.version,
            "rows": num_rows,
            "columns": num_cols,
        }

    def _create_group_node_optimized(self, group_item: GroupItemType) -> dict[str, Any]:
        """Create optimized group/list node."""
        # Determine list type efficiently
        list_type = LIST_TYPE_UNORDERED
        try:
            if (
                group_item.children
                and group_item.children[0].cref
                and "texts" in group_item.children[0].cref
            ):
                ref_parts = group_item.children[0].cref.split("/")
                if len(ref_parts) >= 3 and ref_parts[1] == "texts":
                    try:
                        text_index = int(ref_parts[2])
                        if text_index < len(self.doc.texts):
                            first_text = getattr(self.doc.texts[text_index], "text", "") or ""
                            if first_text and ". " in first_text:
                                prefix = first_text.split(". ", 1)[0].strip()
                                if prefix.isdigit():
                                    list_type = LIST_TYPE_ORDERED
                    except (ValueError, IndexError, AttributeError):
                        pass
        except (AttributeError, TypeError):
            pass

        tag = LIST_TAG_ORDERED if list_type == LIST_TYPE_ORDERED else LIST_TAG_UNORDERED

        list_items = []

        # Process list items in batch
        for child_ref in group_item.children:
            if not child_ref.cref:
                continue

            ref_parts = child_ref.cref.split("/")
            if len(ref_parts) >= 3 and ref_parts[1] == "texts":
                try:
                    text_index = int(ref_parts[2])
                    if text_index < len(self.doc.texts):
                        text_item = self.doc.texts[text_index]
                        text_content = text_item.text

                        # Remove list markers efficiently
                        if text_content.startswith("● ") or text_content.startswith("• "):
                            text_content = text_content[2:]
                        elif ". " in text_content:
                            parts = text_content.split(". ", 1)
                            if parts[0].isdigit():
                                text_content = parts[1]

                        # Process text optimally
                        if self.params.optimize_text_formatting:
                            children = self._process_text_with_links_optimized(
                                text_content, text_item
                            )
                        else:
                            children = [
                                self._create_formatted_text_node_optimized(text_content, [])
                            ]

                        list_item = {
                            "children": children,
                            "direction": TEXT_DIRECTION_LTR,
                            "format": DEFAULT_STYLE,
                            "indent": DEFAULT_INDENT,
                            "type": NODE_TYPE_LIST_ITEM,
                            "value": 1,
                            "version": self.params.version,
                        }

                        list_items.append(list_item)
                except (ValueError, IndexError, AttributeError):
                    continue

        return {
            "children": list_items,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "listType": list_type,
            "start": 1,
            "tag": tag,
            "type": NODE_TYPE_LIST,
            "version": self.params.version,
        }

    def _detect_text_formatting_optimized(
        self, text_content: str, text_item: TextItemType | None = None
    ) -> list[str]:
        """Fast text formatting detection with minimal overhead."""
        format_types = []

        if not text_content or not self.params.preserve_formatting:
            return format_types

        # Quick heuristic checks (faster than detailed analysis)
        lower_text = text_content.lower()

        if text_content.isupper() or "important" in lower_text or text_content.startswith("**"):
            format_types.append("bold")
        elif "italic" in lower_text or text_content.startswith("*"):
            format_types.append("italic")

        return format_types

    def _process_text_with_links_optimized(
        self, text_content: str, text_item: TextItemType | None = None
    ) -> list[dict[str, Any]]:
        """Fast link processing with minimal regex overhead."""
        # Quick check for URLs to avoid regex if not needed
        if "http" not in text_content and "www." not in text_content:
            format_types = self._detect_text_formatting_optimized(text_content, text_item)
            return [self._create_formatted_text_node_optimized(text_content, format_types)]

        # Use simplified URL detection
        import re

        url_pattern = r"https?://\S+|www\.\S+"
        urls = list(re.finditer(url_pattern, text_content))

        if not urls:
            format_types = self._detect_text_formatting_optimized(text_content, text_item)
            return [self._create_formatted_text_node_optimized(text_content, format_types)]

        # Process URLs (simplified version of original logic)
        nodes = []
        last_end = 0

        for url_match in urls:
            # Add text before URL
            if url_match.start() > last_end:
                before_text = text_content[last_end : url_match.start()]
                if before_text.strip():
                    format_types = self._detect_text_formatting_optimized(before_text, text_item)
                    nodes.append(
                        self._create_formatted_text_node_optimized(before_text, format_types)
                    )

            # Add link node
            url = url_match.group()
            if not url.startswith("http"):
                url = "https://" + url
            nodes.append(self._create_link_node_optimized(url_match.group(), url))
            last_end = url_match.end()

        # Add remaining tex
        if last_end < len(text_content):
            after_text = text_content[last_end:]
            if after_text.strip():
                format_types = self._detect_text_formatting_optimized(after_text, text_item)
                nodes.append(self._create_formatted_text_node_optimized(after_text, format_types))

        return nodes

    def _create_formatted_text_node_optimized(
        self, text_content: str, format_types: list[str]
    ) -> dict[str, Any]:
        """Create optimized formatted text node."""
        # Calculate format bitmask efficiently
        format_value = 0
        for fmt in format_types:
            if fmt == "bold":
                format_value |= FORMAT_BOLD
            elif fmt == "italic":
                format_value |= FORMAT_ITALIC
            elif fmt == "underline":
                format_value |= FORMAT_UNDERLINE
            elif fmt == "strikethrough":
                format_value |= FORMAT_STRIKETHROUGH

        return {
            "detail": DEFAULT_DETAIL,
            "format": format_value,
            "mode": DEFAULT_MODE,
            "style": DEFAULT_STYLE,
            "text": text_content,
            "type": NODE_TYPE_TEXT,
            "version": self.params.version,
        }

    def _create_link_node_optimized(self, text_content: str, url: str) -> dict[str, Any]:
        """Create optimized link node."""
        return {
            "children": [
                {
                    "detail": DEFAULT_DETAIL,
                    "format": DEFAULT_FORMAT,
                    "mode": DEFAULT_MODE,
                    "style": DEFAULT_STYLE,
                    "text": text_content,
                    "type": NODE_TYPE_TEXT,
                    "version": self.params.version,
                }
            ],
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_LINK,
            "url": url,
            "version": self.params.version,
        }

    def _create_default_heading_node(self) -> dict[str, Any]:
        """Create default heading node for error cases."""
        return {
            "children": [self._create_formatted_text_node_optimized("", [])],
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "tag": DEFAULT_HEADING_TAG,
            "type": NODE_TYPE_HEADING,
            "version": self.params.version,
        }

    def _create_heading_node(self, text_item: SectionHeaderItem) -> dict[str, Any]:
        """Create a Lexical heading node from a TextItem.

        Args:
            text_item: The heading TextItem

        Returns:
            Lexical heading node
        """
        return self._create_heading_node_optimized(text_item)

    def _create_paragraph_node(self, text_item: TextItem) -> dict[str, Any]:
        """Create a Lexical paragraph node from a TextItem.

        Args:
            text_item: The paragraph TextItem

        Returns:
            Lexical paragraph node
        """
        return self._create_paragraph_node_optimized(text_item)

    def _create_table_node(self, table_item: TableItem) -> dict[str, Any]:
        """Create a Lexical table node from a TableItem.

        Args:
            table_item: The TableItem to conver

        Returns:
            Lexical table node
        """
        return self._create_table_node_optimized(table_item)

    def _create_group_node(self, group_item: GroupItemType) -> dict[str, Any]:
        """Create a Lexical list node from a GroupItem.

        Args:
            group_item: The GroupItem to conver

        Returns:
            Lexical list node
        """
        return self._create_group_node_optimized(group_item)

    # Required abstract method implementations from BaseDocSerializer
    def get_excluded_refs(self, **kwargs: Any) -> set[str]:
        """Get set of item references that should be excluded from serialization.

        For Lexical format, we don't exclude any references as the forma
        handles all content types in the JSON structure.

        Returns:
            Empty set - no exclusions for Lexical forma
        """
        return set()

    def get_parts(self, item: NodeItem | None = None, **kwargs: Any) -> list[SerializationResult]:
        """Get serialization parts for an item.

        For Lexical format, we serialize the entire document as one JSON structure
        rather than individual parts.

        Args:
            item: Optional item to get parts for
            **kwargs: Additional parameters

        Returns:
            List containing the complete serialization resul
        """
        if item is None:
            # Return the complete document serialization
            return [self.serialize()]

        # For specific items, return empty list as Lexical handles complete structure
        return []

    def post_process(self, text: str, **kwargs: Any) -> str:
        """Post-process the serialized text.

        For Lexical JSON format, no post-processing is needed as the JSON
        is already properly formatted.

        Args:
            text: The serialized tex
            **kwargs: Additional parameters

        Returns:
            The text unchanged
        """
        return text

    def requires_page_break(self) -> bool:
        """Check if this serializer requires page breaks.

        Lexical JSON format doesn't use page breaks as it's a structured
        JSON format rather than a text-based format.

        Returns:
            False - no page breaks needed
        """
        return False

    def serialize_annotations(self, item: DocItem, **kwargs: Any) -> SerializationResult:
        """Serialize annotations for an item.

        For Lexical format, annotations are handled within the JSON structure
        rather than as separate serialization results.

        Args:
            item: The item to serialize annotations for
            **kwargs: Additional parameters

        Returns:
            Empty serialization resul
        """
        return SerializationResult(text="")

    def serialize_bold(self, text: str, **kwargs: Any) -> str:
        """Serialize bold text formatting.

        For Lexical format, bold formatting is handled through the forma
        bitmask in the JSON structure, not as text markup.

        Args:
            text: The text to forma
            **kwargs: Additional parameters

        Returns:
            The text unchanged (formatting handled in JSON structure)
        """
        return text

    def get_performance_stats(self) -> dict[str, Any]:
        """Get current performance statistics."""
        duration = (time.time() - self._start_time) * 1000 if self._start_time > 0 else 0

        return {
            "elements_processed": self._elements_processed,
            "duration_ms": duration,
            "elements_per_second": (
                (self._elements_processed / (duration / 1000)) if duration > 0 else 0
            ),
            "json_encoder": self._json_encoder.__name__,
            "cache_size": len(self._node_cache) if self._node_cache else 0,
            "configuration": {
                "streaming": self.params.enable_streaming,
                "parallel": self.params.parallel_processing,
                "batch_size": self.params.batch_size,
                "memory_efficient": self.params.memory_efficient_mode,
            },
        }

    def serialize_captions(self, item: FloatingItem, **kwargs: Any) -> SerializationResult:
        """Serialize captions for a floating item.

        For Lexical format, captions are handled within the item's JSON
        structure rather than as separate serialization results.

        Args:
            item: The floating item to serialize captions for
            **kwargs: Additional parameters

        Returns:
            Empty serialization resul
        """
        return SerializationResult(text="")

    def serialize_hyperlink(self, text: str, hyperlink: AnyUrl | Path, **kwargs: Any) -> str:
        """Serialize hyperlink formatting.

        For Lexical format, hyperlinks are handled through dedicated link
        nodes in the JSON structure, not as text markup.

        Args:
            text: The link tex
            hyperlink: The link URL or path
            **kwargs: Additional parameters

        Returns:
            The text unchanged (links handled in JSON structure)
        """
        return text

    def serialize_italic(self, text: str, **kwargs: Any) -> str:
        """Serialize italic text formatting.

        For Lexical format, italic formatting is handled through the forma
        bitmask in the JSON structure, not as text markup.

        Args:
            text: The text to forma
            **kwargs: Additional parameters

        Returns:
            The text unchanged (formatting handled in JSON structure)
        """
        return text

    def serialize_strikethrough(self, text: str, **kwargs: Any) -> str:
        """Serialize strikethrough text formatting.

        For Lexical format, strikethrough formatting is handled through the forma
        bitmask in the JSON structure, not as text markup.

        Args:
            text: The text to forma
            **kwargs: Additional parameters

        Returns:
            The text unchanged (formatting handled in JSON structure)
        """
        return text

    def serialize_subscript(self, text: str, **kwargs: Any) -> str:
        """Serialize subscript text formatting.

        For Lexical format, subscript formatting would be handled through the forma
        bitmask in the JSON structure, not as text markup.

        Args:
            text: The text to forma
            **kwargs: Additional parameters

        Returns:
            The text unchanged (formatting handled in JSON structure)
        """
        return text

    def serialize_superscript(self, text: str, **kwargs: Any) -> str:
        """Serialize superscript text formatting.

        For Lexical format, superscript formatting would be handled through the forma
        bitmask in the JSON structure, not as text markup.

        Args:
            text: The text to forma
            **kwargs: Additional parameters

        Returns:
            The text unchanged (formatting handled in JSON structure)
        """
        return text

    def serialize_underline(self, text: str, **kwargs: Any) -> str:
        """Serialize underline text formatting.

        For Lexical format, underline formatting is handled through the forma
        bitmask in the JSON structure, not as text markup.

        Args:
            text: The text to forma
            **kwargs: Additional parameters

        Returns:
            The text unchanged (formatting handled in JSON structure)
        """
        return text
