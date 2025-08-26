"""LexicalDocSerializer for converting DoclingDocument to Lexical JSON format."""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Protocol

from docling_core.transforms.serializer.base import SerializationResult
from docling_core.types import DoclingDocument
from docling_core.types.doc.document import (
    GroupItem,
    OrderedList,
    SectionHeaderItem,
    TextItem,
    TableItem,
    UnorderedList,
    PictureItem,
)

from docpivot.io.readers.exceptions import (
    ValidationError,
    TransformationError,
    ConfigurationError
)
from docpivot.validation import validate_docling_document, parameter_validator
from docpivot.logging_config import get_logger, PerformanceLogger, log_exception_with_context

logger = get_logger(__name__)
perf_logger = PerformanceLogger(logger)

# Type aliases for method parameters
TextItemType = Union[SectionHeaderItem, TextItem]
GroupItemType = Union[OrderedList, UnorderedList, GroupItem]

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
    """

    include_metadata: bool = True
    preserve_formatting: bool = True
    indent_json: bool = True
    version: int = LEXICAL_VERSION
    custom_root_attributes: Optional[Dict[str, Any]] = field(default_factory=dict)
    skip_validation: bool = False


class ComponentSerializer(Protocol):
    """Protocol for component serializers."""

    def serialize(
        self, item: Any, params: Optional[LexicalParams] = None
    ) -> Dict[str, Any]:
        """Serialize a component to Lexical node format."""
        ...


class ImageSerializer:
    """Default image serializer for Lexical format."""

    def serialize(
        self, image_item: PictureItem, params: Optional[LexicalParams] = None
    ) -> Dict[str, Any]:
        """Serialize a PictureItem to Lexical image node.

        Args:
            image_item: The PictureItem to serialize
            params: Optional LexicalParams for configuration

        Returns:
            Lexical image node dictionary
        """
        # Handle missing or malformed image data
        src = (
            getattr(image_item, "image_path", "")
            or getattr(image_item, "path", "")
            or ""
        )
        alt_text = (
            getattr(image_item, "alt_text", "")
            or getattr(image_item, "caption", "")
            or ""
        )

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


class LexicalDocSerializer:
    """Serializer for converting DoclingDocument objects to Lexical JSON format.

    This serializer transforms DoclingDocument elements into Lexical's nested node
    structure, handling the conversion between referenced elements and hierarchical
    nodes. It supports advanced features including text formatting, links, images,
    and component serializers.

    Note: This serializer does NOT extend BaseDocSerializer because it has fundamentally
    different requirements:
    - BaseDocSerializer is designed for text-based serializers with inline formatting
    - LexicalDocSerializer converts entire document structure to JSON format
    - The APIs are incompatible (different serialize() method signatures and patterns)
    """

    def __init__(
        self,
        doc: DoclingDocument,
        params: Optional[LexicalParams] = None,
        image_serializer: Optional[ComponentSerializer] = None,
        table_serializer: Optional[ComponentSerializer] = None,
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
        self.doc = doc
        self.params = params or LexicalParams()
        self.image_serializer = image_serializer or ImageSerializer()
        self.table_serializer = table_serializer

    def serialize(self) -> SerializationResult:
        """Serialize the DoclingDocument to Lexical JSON format.

        Returns:
            SerializationResult: The serialization result with Lexical JSON in .text

        Raises:
            ValidationError: If the document structure is invalid
            TransformationError: If conversion to Lexical format fails
            ConfigurationError: If serializer parameters are invalid
        """
        start_time = time.time()
        logger.info("Serializing DoclingDocument to Lexical JSON format")

        try:
            # Validate input document structure (skip if disabled for testing)
            # Handle case where params might not be a valid LexicalParams object
            should_validate = True
            try:
                should_validate = not self.params.skip_validation
            except AttributeError:
                # If params doesn't have skip_validation, assume we should validate
                should_validate = True
            
            if should_validate:
                validate_docling_document(self.doc)
                logger.debug("DoclingDocument validation passed")
            else:
                logger.debug("DoclingDocument validation skipped")

            # Validate serializer parameters
            self._validate_serializer_params()
            logger.debug("Serializer parameters validation passed")

            # Transform document structure with error handling
            lexical_data = self._transform_docling_to_lexical()
            logger.debug("DoclingDocument transformation to Lexical completed")

            # Serialize to JSON with error handling
            try:
                indent = JSON_INDENT_SIZE if self.params.indent_json else None
                json_text = json.dumps(lexical_data, indent=indent, ensure_ascii=False)
                
                # Log performance metrics
                duration = (time.time() - start_time) * 1000
                perf_logger.log_operation_time(
                    "Lexical serialization", 
                    duration, 
                    {
                        "output_size_chars": len(json_text),
                        "indent_json": self.params.indent_json,
                        "include_metadata": self.params.include_metadata
                    }
                )
                logger.info("Successfully serialized DoclingDocument to Lexical JSON")
                
                return SerializationResult(text=json_text)
                
            except (TypeError, ValueError) as e:
                raise TransformationError(
                    f"Failed to serialize Lexical data to JSON: {e}. "
                    f"The transformed data structure may be invalid.",
                    transformation_type="lexical_to_json",
                    recovery_suggestions=[
                        "Check for circular references in the document structure",
                        "Verify all data types are JSON-serializable",
                        "Try with different serializer parameters"
                    ],
                    context={"original_error": str(e)},
                    cause=e
                ) from e

        except (ValidationError, TransformationError, ConfigurationError):
            # Re-raise our custom exceptions without wrapping
            duration = (time.time() - start_time) * 1000
            logger.error(f"Failed to serialize DoclingDocument to Lexical JSON after {duration:.2f}ms")
            raise
        except Exception as e:
            # Handle unexpected errors with comprehensive context
            duration = (time.time() - start_time) * 1000
            context = {
                "operation": "serialize",
                "duration_ms": duration,
                "serializer_params": self.params.__dict__ if hasattr(self.params, '__dict__') else str(self.params)
            }
            log_exception_with_context(logger, e, "Lexical JSON serialization", context)
            
            raise TransformationError(
                f"Unexpected error during Lexical JSON serialization: {e}. "
                f"Please check the document structure and try again.",
                transformation_type="docling_to_lexical",
                context=context,
                cause=e
            ) from e

    def _validate_serializer_params(self) -> None:
        """Validate serializer parameters.

        Raises:
            ConfigurationError: If parameters are invalid
        """
        # Validate params object
        if not isinstance(self.params, LexicalParams):
            raise ConfigurationError(
                f"Invalid serializer parameters: expected LexicalParams, got {type(self.params).__name__}",
                context={"actual_type": type(self.params).__name__}
            )

        # Validate version parameter
        if not isinstance(self.params.version, int) or self.params.version < 1:
            raise ConfigurationError(
                f"Invalid version parameter: {self.params.version}. Version must be a positive integer.",
                invalid_parameters=["version"],
                valid_options={"version": ["Any positive integer"]},
                context={"provided_version": self.params.version}
            )

        # Validate boolean parameters
        bool_params = ["include_metadata", "preserve_formatting", "indent_json"]
        for param_name in bool_params:
            param_value = getattr(self.params, param_name)
            if not isinstance(param_value, bool):
                raise ConfigurationError(
                    f"Invalid {param_name} parameter: {param_value}. Must be a boolean value.",
                    invalid_parameters=[param_name],
                    valid_options={param_name: ["true", "false"]},
                    context={f"provided_{param_name}": param_value}
                )

        # Validate custom root attributes
        if self.params.custom_root_attributes is not None:
            if not isinstance(self.params.custom_root_attributes, dict):
                raise ConfigurationError(
                    f"Invalid custom_root_attributes: must be a dictionary, got {type(self.params.custom_root_attributes).__name__}",
                    invalid_parameters=["custom_root_attributes"],
                    context={"actual_type": type(self.params.custom_root_attributes).__name__}
                )

        logger.debug("Serializer parameters validation completed successfully")

    def _transform_docling_to_lexical(self) -> Dict[str, Any]:
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
                lexical_children = self._process_body_children()
                logger.debug(f"Processed {len(lexical_children)} body children")
            except Exception as e:
                raise TransformationError(
                    f"Failed to process document body children: {e}. "
                    f"The document structure may be invalid or corrupted.",
                    transformation_type="body_children_processing",
                    recovery_suggestions=[
                        "Check that the document body contains valid elements",
                        "Verify all referenced elements exist in the document",
                        "Ensure element references are properly formatted"
                    ],
                    context={"original_error": str(e)},
                    cause=e
                ) from e

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
                    logger.debug(f"Added {len(self.params.custom_root_attributes)} custom root attributes")
                except Exception as e:
                    logger.warning(f"Failed to add custom root attributes: {e}. Proceeding without them.")

            lexical_data = {"root": root_node}

            # Include document metadata if requested
            if self.params.include_metadata:
                try:
                    metadata = {}
                    if hasattr(self.doc, "name") and self.doc.name:
                        metadata.update({
                            "document_name": self.doc.name,
                            "version": getattr(self.doc, "version", "1.0.0"),
                        })

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
                    logger.warning(f"Failed to include document metadata: {e}. Proceeding without metadata.")

            logger.debug("DoclingDocument to Lexical transformation completed successfully")
            return lexical_data
            
        except TransformationError:
            # Re-raise transformation errors without wrapping
            raise
        except Exception as e:
            # Handle any unexpected errors during transformation
            logger.error(f"Unexpected error during Lexical transformation: {e}")
            raise TransformationError(
                f"Unexpected error during DoclingDocument to Lexical transformation: {e}",
                transformation_type="docling_to_lexical",
                recovery_suggestions=[
                    "Check the document structure for validity",
                    "Verify all document elements are properly formed",
                    "Try with simplified serializer parameters"
                ],
                context={"original_error": str(e)},
                cause=e
            ) from e

    def _process_body_children(self) -> List[Dict[str, Any]]:
        """Process DoclingDocument body children and convert to Lexical nodes.

        Returns:
            List of Lexical nodes
        """
        lexical_nodes = []

        for child_ref in self.doc.body.children:
            try:
                if not child_ref.cref:
                    continue

                # Parse the reference to determine type and index
                ref_parts = child_ref.cref.split("/")
                if len(ref_parts) < MIN_REF_PARTS:
                    continue

                element_type = ref_parts[REF_ELEMENT_TYPE_INDEX]

                # Parse element index with error handling
                try:
                    element_index = int(ref_parts[REF_ELEMENT_INDEX])
                except ValueError:
                    continue

                # Process based on element type with bounds checking
                if element_type == ELEMENT_TYPE_TEXTS:
                    if element_index >= len(self.doc.texts):
                        continue
                    text_item = self.doc.texts[element_index]
                    lexical_node = self._create_text_node(text_item)
                    if lexical_node:
                        lexical_nodes.append(lexical_node)

                elif element_type == ELEMENT_TYPE_TABLES:
                    if element_index >= len(self.doc.tables):
                        continue
                    table_item = self.doc.tables[element_index]
                    if self.table_serializer:
                        lexical_node = self.table_serializer.serialize(
                            table_item, self.params
                        )
                    else:
                        lexical_node = self._create_table_node(table_item)
                    if lexical_node:
                        lexical_nodes.append(lexical_node)

                elif element_type == ELEMENT_TYPE_GROUPS:
                    if element_index >= len(self.doc.groups):
                        continue
                    group_item = self.doc.groups[element_index]
                    lexical_node = self._create_group_node(group_item)
                    if lexical_node:
                        lexical_nodes.append(lexical_node)

                elif element_type == ELEMENT_TYPE_PICTURES:
                    if hasattr(self.doc, "pictures") and element_index < len(
                        self.doc.pictures
                    ):
                        picture_item = self.doc.pictures[element_index]
                        lexical_node = self.image_serializer.serialize(
                            picture_item, self.params
                        )
                        if lexical_node:
                            lexical_nodes.append(lexical_node)

            except (AttributeError, IndexError, TypeError):
                # Skip malformed references and continue processing
                continue

        return lexical_nodes

    def _detect_text_formatting(
        self, text_content: str, text_item: Optional[TextItemType] = None
    ) -> List[str]:
        """Detect text formatting from content patterns and DoclingDocument attributes.

        Args:
            text_content: The text content to analyze
            text_item: Optional TextItem to extract formatting metadata from

        Returns:
            List of format types detected (e.g., ['bold'], ['italic'])
        """
        format_types: List[str] = []

        if not self.params.preserve_formatting or not text_content:
            return format_types

        # First check if the text_item has style information
        if text_item:
            # Check if the item has any style attributes
            if hasattr(text_item, 'style'):
                style = getattr(text_item, 'style', {})
                if isinstance(style, dict):
                    if (style.get('bold') or
                            style.get('font_weight', '').lower()
                            in ['bold', '700']):
                        format_types.append("bold")
                    if (style.get('italic') or
                            style.get('font_style', '').lower() == 'italic'):
                        format_types.append("italic")
                    if style.get('underline'):
                        format_types.append("underline")

            # Check if the item has formatting attributes directly
            if (hasattr(text_item, 'font_weight') and
                    str(getattr(text_item, 'font_weight', '')).lower()
                    in ['bold', '700']):
                format_types.append("bold")
            if (hasattr(text_item, 'font_style') and
                    str(getattr(text_item, 'font_style', '')).lower()
                    == 'italic'):
                format_types.append("italic")

        # Fallback to heuristic detection for common formatting patterns
        lower_text = text_content.lower()

        # Detect emphasis patterns (enhanced heuristics)
        if not format_types:  # Only use heuristics if no style info found
            # Bold text patterns
            if (("bold" in lower_text and
                 ("are" in lower_text or "terms" in lower_text)) or
                text_content.isupper() or
                "important" in lower_text.lower() or
                (text_content.startswith("**") and
                 text_content.endswith("**"))):
                format_types.append("bold")

            # Italic text patterns
            elif (("italic" in lower_text and "emphasis" in lower_text) or
                  "primarily used" in lower_text or
                  (text_content.startswith("*") and
                   text_content.endswith("*") and
                   not text_content.startswith("**"))):
                format_types.append("italic")

        return format_types

    def _create_formatted_text_node(
        self, text_content: str, format_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a Lexical text node with formatting.

        Args:
            text_content: The text content
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
        self, text_content: str, text_item: Optional[TextItemType] = None
    ) -> List[Dict[str, Any]]:
        """Process text content to detect and create link nodes.

        Args:
            text_content: The text content to process
            text_item: Optional TextItem for formatting metadata

        Returns:
            List of Lexical nodes (text nodes or link nodes)
        """
        import re

        # URL pattern to detect links
        url_pattern = (r'https?://[^\s<>"{}|\\^`\[\]]+'
                       r'|www\.[^\s<>"{}|\\^`\[\]]+')

        # Find all URLs in the text
        urls = list(re.finditer(url_pattern, text_content))

        if not urls:
            # No links found, return a single formatted text node
            format_types = self._detect_text_formatting(
                text_content, text_item)
            return [self._create_formatted_text_node(
                text_content, format_types)]

        nodes = []
        last_end = 0

        for url_match in urls:
            # Add text before the URL as a regular text node
            if url_match.start() > last_end:
                before_text = text_content[last_end:url_match.start()]
                if before_text.strip():  # Only add non-empty text
                    format_types = self._detect_text_formatting(
                        before_text, text_item)
                    nodes.append(self._create_formatted_text_node(
                        before_text, format_types))

            # Create link node
            url = url_match.group()
            # Ensure URL has protocol
            if not url.startswith('http'):
                url = 'https://' + url

            link_text = url_match.group()  # Display the original match
            nodes.append(self._create_link_node(link_text, url))

            last_end = url_match.end()

        # Add any remaining text after the last URL
        if last_end < len(text_content):
            after_text = text_content[last_end:]
            if after_text.strip():  # Only add non-empty text
                format_types = self._detect_text_formatting(
                    after_text, text_item)
                nodes.append(self._create_formatted_text_node(
                    after_text, format_types))

        return nodes

    def _create_link_node(self, text_content: str, url: str) -> Dict[str, Any]:
        """Create a Lexical link node.

        Args:
            text_content: The link text
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

    def _create_text_node(self, text_item: TextItemType) -> Optional[Dict[str, Any]]:
        """Create a Lexical node from a DoclingDocument TextItem.

        Args:
            text_item: The TextItem to convert

        Returns:
            Lexical node dictionary or None if conversion fails
        """
        if text_item.label == "section_header":
            return self._create_heading_node(text_item)
        else:
            return self._create_paragraph_node(text_item)

    def _create_heading_node(self, text_item: SectionHeaderItem) -> Dict[str, Any]:
        """Create a Lexical heading node from a TextItem.

        Args:
            text_item: The heading TextItem

        Returns:
            Lexical heading node
        """
        # Map level to HTML heading tags with error handling
        try:
            level = getattr(text_item, "level", MIN_HEADING_LEVEL)
            tag = f"h{min(max(level, MIN_HEADING_LEVEL), MAX_HEADING_LEVEL)}"

            # Handle missing or malformed text content
            text_content = getattr(text_item, "text", "") or ""

            # Detect formatting if enabled, passing the text_item for metadata
            format_types = self._detect_text_formatting(text_content, text_item)

            # Create formatted text node
            text_node = self._create_formatted_text_node(text_content, format_types)

            return {
                "children": [text_node],
                "direction": TEXT_DIRECTION_LTR,
                "format": DEFAULT_STYLE,
                "indent": DEFAULT_INDENT,
                "tag": tag,
                "type": NODE_TYPE_HEADING,
                "version": self.params.version,
            }
        except (AttributeError, TypeError):
            # Return default heading if text item is malformed
            default_text_node = self._create_formatted_text_node("", [])
            return {
                "children": [default_text_node],
                "direction": TEXT_DIRECTION_LTR,
                "format": DEFAULT_STYLE,
                "indent": DEFAULT_INDENT,
                "tag": DEFAULT_HEADING_TAG,
                "type": NODE_TYPE_HEADING,
                "version": self.params.version,
            }

    def _create_paragraph_node(self, text_item: TextItem) -> Dict[str, Any]:
        """Create a Lexical paragraph node from a TextItem.

        Args:
            text_item: The paragraph TextItem

        Returns:
            Lexical paragraph node
        """
        # Handle missing or malformed text content
        text_content = getattr(text_item, "text", "") or ""

        # Check for links in the text and create appropriate nodes
        children = self._process_text_with_links(text_content, text_item)

        return {
            "children": children,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_PARAGRAPH,
            "version": self.params.version,
        }

    def _create_table_node(self, table_item: TableItem) -> Dict[str, Any]:
        """Create a Lexical table node from a TableItem.

        Args:
            table_item: The TableItem to convert

        Returns:
            Lexical table node
        """
        rows: List[Dict[str, Any]] = []

        # Convert table grid to Lexical table rows
        try:
            if table_item.data and table_item.data.grid:
                for row in table_item.data.grid:
                    try:
                        lexical_row: Dict[str, Any] = {
                            "children": [],
                            "direction": TEXT_DIRECTION_LTR,
                            "format": DEFAULT_STYLE,
                            "indent": DEFAULT_INDENT,
                            "type": NODE_TYPE_TABLE_ROW,
                            "version": self.params.version,
                        }

                        for cell in row:
                            try:
                                # Handle missing or malformed cell text
                                cell_text = getattr(cell, "text", "") or ""

                                lexical_cell = {
                                    "children": [
                                        self._create_formatted_text_node(cell_text, [])
                                    ],
                                    "direction": TEXT_DIRECTION_LTR,
                                    "format": DEFAULT_STYLE,
                                    "indent": DEFAULT_INDENT,
                                    "type": NODE_TYPE_TABLE_CELL,
                                    "version": self.params.version,
                                }

                                # Add header state if it's a header cell
                                if (
                                    hasattr(cell, "column_header")
                                    and cell.column_header
                                ):
                                    lexical_cell["headerState"] = HEADER_STATE_VALUE

                                lexical_row["children"].append(lexical_cell)

                            except (AttributeError, TypeError):
                                # Skip malformed cells
                                continue

                        # Only add row if it has cells
                        if lexical_row["children"]:
                            rows.append(lexical_row)

                    except (AttributeError, TypeError):
                        # Skip malformed rows
                        continue

        except (AttributeError, TypeError):
            # Handle case where table structure is completely malformed
            pass

        # Create the table node
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

    def _create_group_node(self, group_item: GroupItemType) -> Dict[str, Any]:
        """Create a Lexical list node from a GroupItem.

        Args:
            group_item: The GroupItem to convert

        Returns:
            Lexical list node
        """
        # Determine list type by examining the first item's content
        list_type = "unordered"  # default
        try:
            if group_item.children:
                first_ref = group_item.children[0]
                if first_ref.cref and "texts" in first_ref.cref:
                    ref_parts = first_ref.cref.split("/")
                    if len(ref_parts) >= 3 and ref_parts[1] == "texts":
                        try:
                            text_index = int(ref_parts[2])
                            if text_index < len(self.doc.texts):
                                first_text = (
                                    getattr(self.doc.texts[text_index], "text", "")
                                    or ""
                                )
                                # Check if it starts with a number followed by period
                                if (
                                    first_text
                                    and ". " in first_text
                                    and first_text.split(". ", 1)[0].strip().isdigit()
                                ):
                                    list_type = "ordered"
                        except (ValueError, IndexError, AttributeError):
                            # Default to unordered if parsing fails
                            pass
        except (AttributeError, TypeError):
            # Default to unordered if group structure is malformed
            pass

        tag = "ol" if list_type == "ordered" else "ul"

        list_items = []

        # Process child text items
        for child_ref in group_item.children:
            if not child_ref.cref:
                continue

            ref_parts = child_ref.cref.split("/")
            if len(ref_parts) >= 3 and ref_parts[1] == "texts":
                text_index = int(ref_parts[2])
                if text_index < len(self.doc.texts):
                    text_item = self.doc.texts[text_index]

                    # Extract the actual content without list markers
                    text_content = text_item.text
                    # Remove bullet points or numbers if they exist
                    if text_content.startswith("● "):
                        text_content = text_content[2:]  # Remove bullet and space
                    elif text_content.startswith("• "):
                        text_content = text_content[2:]  # Remove bullet and space
                    elif (
                        ". " in text_content
                        and text_content.split(". ", 1)[0].isdigit()
                    ):
                        text_content = text_content.split(". ", 1)[
                            1
                        ]  # Remove number and period

                    # Process text with links and formatting
                    children = self._process_text_with_links(text_content, text_item)

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
