"""LexicalJsonReader for loading Lexical JSON files into DoclingDocument objects."""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from docling_core.types import DoclingDocument
from pydantic import ValidationError

from .basereader import BaseReader
from .exceptions import UnsupportedFormatError


class LexicalJsonReader(BaseReader):
    """Reader for Lexical JSON files that loads them into DoclingDocument objects.

    This reader handles Lexical JSON format with hierarchical node structure
    and converts it to Docling's referenced element model.
    """

    SUPPORTED_EXTENSIONS = {".lexical.json", ".json"}
    REQUIRED_ROOT_FIELDS = {"root"}
    REQUIRED_ROOT_CHILD_FIELDS = {"children", "type"}

    def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
        """Load document from Lexical JSON file into DoclingDocument.

        Args:
            file_path: Path to the Lexical JSON file to load
            **kwargs: Additional parameters (currently unused)

        Returns:
            DoclingDocument: The loaded document as a DoclingDocument object

        Raises:
            FileNotFoundError: If the file does not exist
            UnsupportedFormatError: If the file format is not supported
            ValueError: If the JSON is invalid or malformed
            IOError: If there are issues reading the file
        """
        # Validate file exists and is readable
        path = self._validate_file_exists(file_path)

        # Check format detection
        if not self.detect_format(file_path):
            raise UnsupportedFormatError(str(file_path))

        try:
            # Read and parse JSON file
            json_content = path.read_text(encoding="utf-8")

            # Parse JSON content
            try:
                json_data = json.loads(json_content)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON format in file '{file_path}': {e}"
                ) from e

            # Validate Lexical schema
            self._validate_lexical_schema(json_data, str(file_path))

            # Convert Lexical JSON to DoclingDocument
            return self._convert_lexical_to_docling(json_data, str(file_path))

        except IOError as e:
            raise IOError(f"Error reading file '{file_path}': {e}") from e

    def detect_format(self, file_path: Union[str, Path]) -> bool:
        """Detect if this reader can handle the given file format.

        Checks for .lexical.json extension and optionally validates the
        content structure for .json files.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if this reader can handle the file format, False otherwise
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            return False

        # Check file extension
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            return False

        # For .lexical.json files, we assume they are valid
        if path.name.endswith(".lexical.json"):
            return True

        # For generic .json files, check content structure
        if suffix == ".json":
            return self._check_lexical_json_content(path)

        return False

    def _check_lexical_json_content(self, path: Path) -> bool:
        """Check if a .json file contains Lexical JSON content.

        Args:
            path: Path object to the JSON file

        Returns:
            bool: True if the file appears to contain Lexical data
        """
        try:
            # Read and parse a small portion to check schema
            with path.open("r", encoding="utf-8") as f:
                # Read first chunk to check for Lexical markers
                chunk = f.read(512)

            # Quick check for Lexical JSON markers
            return '"root"' in chunk and '"children"' in chunk and '"type"' in chunk

        except (IOError, UnicodeDecodeError):
            return False

    def _validate_lexical_schema(
        self, json_data: Dict[str, Any], file_path: str
    ) -> None:
        """Validate that JSON data has expected Lexical schema structure.

        Args:
            json_data: Parsed JSON data dictionary
            file_path: Path to the file being validated (for error messages)

        Raises:
            ValueError: If the schema is invalid or missing required fields
        """
        if not isinstance(json_data, dict):
            raise ValueError(
                f"Invalid Lexical JSON format in '{file_path}': "
                f"Expected JSON object, got {type(json_data).__name__}"
            )

        # Check for required root fields
        missing_fields = self.REQUIRED_ROOT_FIELDS - set(json_data.keys())
        if missing_fields:
            raise ValueError(
                f"Invalid Lexical JSON schema in '{file_path}': "
                f"Missing required fields: {', '.join(sorted(missing_fields))}"
            )

        # Validate root structure
        root = json_data.get("root")
        if not isinstance(root, dict):
            raise ValueError(
                f"Invalid Lexical JSON schema in '{file_path}': "
                f"'root' must be an object, got {type(root).__name__}"
            )

        # Check required root child fields
        missing_root_fields = self.REQUIRED_ROOT_CHILD_FIELDS - set(root.keys())
        if missing_root_fields:
            raise ValueError(
                f"Invalid Lexical JSON schema in '{file_path}': "
                f"root missing required fields: "
                f"{', '.join(sorted(missing_root_fields))}"
            )

    def _convert_lexical_to_docling(
        self, lexical_data: Dict[str, Any], file_path: str
    ) -> DoclingDocument:
        """Convert Lexical JSON data to DoclingDocument.

        Args:
            lexical_data: Parsed Lexical JSON data
            file_path: Source file path for metadata

        Returns:
            DoclingDocument: Converted document
        """
        # Initialize document structure
        doc_data = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            "name": Path(file_path).stem,
            "origin": {
                "mimetype": "application/json",
                "binary_hash": abs(hash(str(lexical_data))),
                "filename": Path(file_path).name,
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified",
            },
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified",
            },
            "groups": [],
            "texts": [],
            "pictures": [],
            "tables": [],
            "key_value_items": [],
            "pages": {},
        }

        # Process Lexical nodes into Docling elements
        root_children = lexical_data["root"].get("children", [])
        self._process_lexical_nodes(root_children, doc_data)

        # Create and return DoclingDocument
        try:
            return DoclingDocument.model_validate(doc_data)
        except ValidationError as e:
            raise ValueError(
                f"Failed to create DoclingDocument from '{file_path}': {e}"
            ) from e

    def _process_lexical_nodes(
        self, nodes: List[Dict[str, Any]], doc_data: Dict[str, Any]
    ) -> None:
        """Process Lexical nodes and convert to Docling elements.

        Args:
            nodes: List of Lexical nodes to process
            doc_data: Document data structure being built
        """
        for node in nodes:
            node_type = node.get("type", "")

            if node_type == "heading":
                self._process_heading_node(node, doc_data)
            elif node_type == "paragraph":
                self._process_paragraph_node(node, doc_data)
            elif node_type == "list":
                self._process_list_node(node, doc_data)
            elif node_type == "table":
                self._process_table_node(node, doc_data)

    def _process_heading_node(
        self, node: Dict[str, Any], doc_data: Dict[str, Any]
    ) -> None:
        """Process a Lexical heading node into Docling SectionHeaderItem.

        Args:
            node: Lexical heading node
            doc_data: Document data structure being built
        """
        # Extract text content from children
        text_content = self._extract_text_from_children(node.get("children", []))

        # Determine heading level from tag
        tag = node.get("tag", "h1")
        level = int(tag[1]) if tag.startswith("h") and tag[1:].isdigit() else 1

        # Create SectionHeaderItem
        text_index = len(doc_data["texts"])
        text_item = {
            "self_ref": f"#/texts/{text_index}",
            "parent": {"$ref": "#/body"},
            "children": [],
            "content_layer": "body",
            "label": "section_header",
            "level": level,
            "text": text_content,
            "orig": text_content,
            "prov": [],
        }

        # Add to texts array and reference in body
        doc_data["texts"].append(text_item)

        doc_data["body"]["children"].append({"$ref": f"#/texts/{text_index}"})

    def _process_paragraph_node(
        self, node: Dict[str, Any], doc_data: Dict[str, Any]
    ) -> None:
        """Process a Lexical paragraph node into Docling TextItem.

        Args:
            node: Lexical paragraph node
            doc_data: Document data structure being built
        """
        # Extract text content from children
        text_content = self._extract_text_from_children(node.get("children", []))

        # Create TextItem
        text_index = len(doc_data["texts"])
        text_item = {
            "self_ref": f"#/texts/{text_index}",
            "parent": {"$ref": "#/body"},
            "children": [],
            "content_layer": "body",
            "label": "text",
            "text": text_content,
            "orig": text_content,
            "prov": [],
        }

        # Add to texts array and reference in body
        doc_data["texts"].append(text_item)

        doc_data["body"]["children"].append({"$ref": f"#/texts/{text_index}"})

    def _process_list_node(
        self, node: Dict[str, Any], doc_data: Dict[str, Any]
    ) -> None:
        """Process a Lexical list node into Docling GroupItem.

        Args:
            node: Lexical list node
            doc_data: Document data structure being built
        """
        list_type = node.get("listType", "unordered")
        list_items = node.get("children", [])

        # Create text items for each list item
        group_children = []
        for item in list_items:
            if item.get("type") == "listitem":
                text_content = self._extract_text_from_children(
                    item.get("children", [])
                )

                # Add list marker based on type
                if list_type == "ordered":
                    marker_text = f"{len(group_children) + 1}. {text_content}"
                else:
                    marker_text = f"● {text_content}"

                # Create TextItem
                text_index = len(doc_data["texts"])
                text_item = {
                    "self_ref": f"#/texts/{text_index}",
                    "parent": {"$ref": f"#/groups/{len(doc_data['groups'])}"},
                    "children": [],
                    "content_layer": "body",
                    "label": "text",
                    "text": marker_text,
                    "orig": marker_text,
                    "prov": [],
                }

                # Add to texts array
                doc_data["texts"].append(text_item)

                group_children.append({"$ref": f"#/texts/{text_index}"})

        # Create GroupItem
        if group_children:
            group_index = len(doc_data["groups"])
            group_item = {
                "self_ref": f"#/groups/{group_index}",
                "parent": {"$ref": "#/body"},
                "children": group_children,
                "content_layer": "body",
                "name": f"list_{group_index}",
                "label": "list",
            }

            # Add to groups array and reference in body
            doc_data["groups"].append(group_item)

            doc_data["body"]["children"].append({"$ref": f"#/groups/{group_index}"})

    def _process_table_node(
        self, node: Dict[str, Any], doc_data: Dict[str, Any]
    ) -> None:
        """Process a Lexical table node into Docling TableItem.

        Args:
            node: Lexical table node
            doc_data: Document data structure being built
        """
        rows = node.get("children", [])

        # Convert table rows to grid format
        grid_data = []
        for row in rows:
            if row.get("type") == "tablerow":
                grid_row = []
                for cell in row.get("children", []):
                    if cell.get("type") == "tablecell":
                        cell_text = self._extract_text_from_children(
                            cell.get("children", [])
                        )
                        is_header = cell.get("headerState", 0) == 1

                        grid_cell = {
                            "text": cell_text,
                            "column_header": is_header,
                            "prov": [],
                        }
                        grid_row.append(grid_cell)

                if grid_row:
                    grid_data.append(grid_row)

        # Create TableItem
        if grid_data:
            table_index = len(doc_data["tables"])
            table_item = {
                "self_ref": f"#/tables/{table_index}",
                "parent": {"$ref": "#/body"},
                "children": [],
                "content_layer": "body",
                "data": {"grid": grid_data},
                "label": "table",
                "prov": [],
            }

            # Add to tables array and reference in body
            doc_data["tables"].append(table_item)

            doc_data["body"]["children"].append({"$ref": f"#/tables/{table_index}"})

    def _extract_text_from_children(self, children: List[Dict[str, Any]]) -> str:
        """Extract text content from Lexical node children.

        Args:
            children: List of child nodes

        Returns:
            str: Combined text content
        """
        text_parts = []
        for child in children:
            if child.get("type") == "text":
                text_parts.append(child.get("text", ""))
        return "".join(text_parts)
