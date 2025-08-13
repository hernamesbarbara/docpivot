"""LexicalDocSerializer for converting DoclingDocument to Lexical JSON format."""

import json
from typing import Any, Dict, List, Optional, Union

from docling_core.transforms.serializer.base import SerializationResult
from docling_core.types import DoclingDocument
from docling_core.types.doc.document import (
    GroupItem,
    OrderedList,
    SectionHeaderItem,
    TextItem,
    TableItem,
    UnorderedList,
)

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


class LexicalDocSerializer:
    """Serializer for converting DoclingDocument objects to Lexical JSON format.

    This serializer transforms DoclingDocument elements into Lexical's nested node
    structure, handling the conversion between referenced elements and hierarchical
    nodes.

    Note: This serializer does NOT extend BaseDocSerializer because it has fundamentally
    different requirements:
    - BaseDocSerializer is designed for text-based serializers with inline formatting
    - LexicalDocSerializer converts entire document structure to JSON format
    - The APIs are incompatible (different serialize() method signatures and patterns)
    """

    def __init__(self, doc: DoclingDocument, **kwargs: Any) -> None:
        """Initialize the LexicalDocSerializer.

        Args:
            doc: The DoclingDocument to serialize
            **kwargs: Additional parameters (currently unused)
        """
        self.doc = doc

    def serialize(self) -> SerializationResult:
        """Serialize the DoclingDocument to Lexical JSON format.

        Returns:
            SerializationResult: The serialization result with Lexical JSON in .text
        """
        lexical_data = self._transform_docling_to_lexical()
        json_text = json.dumps(
            lexical_data, indent=JSON_INDENT_SIZE, ensure_ascii=False
        )

        return SerializationResult(text=json_text)

    def _transform_docling_to_lexical(self) -> Dict[str, Any]:
        """Transform DoclingDocument to Lexical JSON structure.

        Returns:
            Dict representing the Lexical JSON structure
        """
        # Process body children to create Lexical nodes
        lexical_children = self._process_body_children()

        # Create the root Lexical structure
        lexical_data = {
            "root": {
                "children": lexical_children,
                "direction": TEXT_DIRECTION_LTR,
                "format": DEFAULT_STYLE,
                "indent": DEFAULT_INDENT,
                "type": NODE_TYPE_ROOT,
                "version": LEXICAL_VERSION,
            }
        }

        return lexical_data

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

            except (AttributeError, IndexError, TypeError):
                # Skip malformed references and continue processing
                continue

        return lexical_nodes

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

            return {
                "children": [
                    {
                        "detail": DEFAULT_DETAIL,
                        "format": DEFAULT_FORMAT,
                        "mode": DEFAULT_MODE,
                        "style": DEFAULT_STYLE,
                        "text": text_content,
                        "type": NODE_TYPE_TEXT,
                        "version": LEXICAL_VERSION,
                    }
                ],
                "direction": TEXT_DIRECTION_LTR,
                "format": DEFAULT_STYLE,
                "indent": DEFAULT_INDENT,
                "tag": tag,
                "type": NODE_TYPE_HEADING,
                "version": LEXICAL_VERSION,
            }
        except (AttributeError, TypeError):
            # Return default heading if text item is malformed
            return {
                "children": [
                    {
                        "detail": DEFAULT_DETAIL,
                        "format": DEFAULT_FORMAT,
                        "mode": DEFAULT_MODE,
                        "style": DEFAULT_STYLE,
                        "text": "",
                        "type": NODE_TYPE_TEXT,
                        "version": LEXICAL_VERSION,
                    }
                ],
                "direction": TEXT_DIRECTION_LTR,
                "format": DEFAULT_STYLE,
                "indent": DEFAULT_INDENT,
                "tag": DEFAULT_HEADING_TAG,
                "type": NODE_TYPE_HEADING,
                "version": LEXICAL_VERSION,
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

        return {
            "children": [
                {
                    "detail": DEFAULT_DETAIL,
                    "format": DEFAULT_FORMAT,
                    "mode": DEFAULT_MODE,
                    "style": DEFAULT_STYLE,
                    "text": text_content,
                    "type": NODE_TYPE_TEXT,
                    "version": LEXICAL_VERSION,
                }
            ],
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_PARAGRAPH,
            "version": LEXICAL_VERSION,
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
                            "direction": "ltr",
                            "format": "",
                            "indent": 0,
                            "type": "tablerow",
                            "version": 1,
                        }

                        for cell in row:
                            try:
                                # Handle missing or malformed cell text
                                cell_text = getattr(cell, "text", "") or ""

                                lexical_cell = {
                                    "children": [
                                        {
                                            "detail": 0,
                                            "format": 0,
                                            "mode": "normal",
                                            "style": "",
                                            "text": cell_text,
                                            "type": "text",
                                            "version": 1,
                                        }
                                    ],
                                    "direction": "ltr",
                                    "format": "",
                                    "indent": 0,
                                    "type": "tablecell",
                                    "version": 1,
                                }

                                # Add header state if it's a header cell
                                if (
                                    hasattr(cell, "column_header")
                                    and cell.column_header
                                ):
                                    lexical_cell["headerState"] = 1

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
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "type": "table",
            "version": 1,
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

                    list_item = {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": text_content,
                                "type": "text",
                                "version": 1,
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "listitem",
                        "value": 1,
                        "version": 1,
                    }

                    list_items.append(list_item)

        return {
            "children": list_items,
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "listType": list_type,
            "start": 1,
            "tag": tag,
            "type": "list",
            "version": 1,
        }
