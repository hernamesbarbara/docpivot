"""LexicalJsonReader for loading Lexical JSON files into DoclingDocument objects."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Union

from docling_core.types import DoclingDocument
from pydantic import ValidationError

from .basereader import BaseReader
from .exceptions import (
    UnsupportedFormatError,
    ValidationError as DocPivotValidationError,
    TransformationError,
    FileAccessError
)
from docpivot.validation import validate_lexical_json, validate_json_content
from docpivot.logging_config import get_logger, PerformanceLogger, log_exception_with_context

logger = get_logger(__name__)
perf_logger = PerformanceLogger(logger)


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
            FileAccessError: If the file cannot be accessed or read
            ValidationError: If the JSON format is invalid
            UnsupportedFormatError: If the file format is not supported
            TransformationError: If conversion to DoclingDocument fails
        """
        start_time = time.time()
        file_path_str = str(file_path)
        logger.info(f"Loading Lexical JSON from {file_path_str}")

        try:
            # Validate file exists and is readable
            try:
                path = self._validate_file_exists(file_path)
            except FileNotFoundError as e:
                raise FileAccessError(
                    f"File not found: {file_path}",
                    file_path_str,
                    "check_existence",
                    context={"original_error": str(e)},
                    cause=e
                ) from e
            except IsADirectoryError as e:
                raise FileAccessError(
                    f"Path is a directory, not a file: {file_path}",
                    file_path_str,
                    "check_file_type",
                    context={"original_error": str(e)},
                    cause=e
                ) from e
            
            # Log file size for performance monitoring
            file_size = path.stat().st_size
            logger.debug(f"File size: {file_size} bytes")

            # Check format detection
            if not self.detect_format(file_path):
                raise UnsupportedFormatError(file_path_str)

            # Read file content with comprehensive error handling
            try:
                json_content = path.read_text(encoding="utf-8")
                logger.debug(f"Successfully read {len(json_content)} characters from {file_path_str}")
            except UnicodeDecodeError as e:
                raise FileAccessError(
                    f"Unable to decode file '{file_path_str}' as UTF-8. "
                    f"Please ensure the file is properly encoded. Error: {e}",
                    file_path_str,
                    "read_text",
                    context={"encoding": "utf-8", "original_error": str(e)},
                    cause=e
                ) from e
            except IOError as e:
                raise FileAccessError(
                    f"Error reading file '{file_path_str}': {e}. "
                    f"Please check file permissions and disk space.",
                    file_path_str,
                    "read_file",
                    permission_issue=("permission" in str(e).lower()),
                    context={"original_error": str(e)},
                    cause=e
                ) from e

            # Parse and validate JSON content
            json_data = validate_json_content(json_content, file_path_str)
            
            # Validate Lexical JSON structure using comprehensive validator
            validate_lexical_json(json_data, file_path_str)

            # Convert Lexical JSON to DoclingDocument with error recovery
            try:
                document = self._convert_lexical_to_docling(json_data, file_path_str)
                
                # Log successful completion with performance metrics
                duration = (time.time() - start_time) * 1000
                perf_logger.log_file_processing(file_path_str, "load", duration, file_size)
                logger.info(f"Successfully loaded Lexical JSON from {file_path_str}")
                
                return document
                
            except Exception as e:
                raise TransformationError(
                    f"Failed to convert Lexical JSON to DoclingDocument from '{file_path_str}': {e}. "
                    f"The file structure may be incompatible or corrupted.",
                    transformation_type="lexical_to_docling",
                    recovery_suggestions=[
                        "Verify the Lexical JSON structure is valid",
                        "Check that all required nodes and properties are present",
                        "Ensure node hierarchy is properly nested",
                        "Try validating the original Lexical JSON in a Lexical editor"
                    ],
                    context={
                        "file_path": file_path_str,
                        "original_error": str(e)
                    },
                    cause=e
                ) from e

        except (DocPivotValidationError, FileAccessError, UnsupportedFormatError, TransformationError):
            # Re-raise our custom exceptions without wrapping
            duration = (time.time() - start_time) * 1000
            logger.error(f"Failed to load Lexical JSON from {file_path_str} after {duration:.2f}ms")
            raise
        except Exception as e:
            # Handle unexpected errors with comprehensive context
            duration = (time.time() - start_time) * 1000
            context = {
                "file_path": file_path_str,
                "operation": "load_data",
                "duration_ms": duration
            }
            log_exception_with_context(logger, e, "Lexical JSON loading", context)
            
            raise DocPivotValidationError(
                f"Unexpected error loading Lexical JSON from '{file_path_str}': {e}. "
                f"Please check the file format and try again.",
                error_code="UNEXPECTED_LOAD_ERROR",
                context=context,
                cause=e
            ) from e

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
        group_children: List[Dict[str, str]] = []
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
