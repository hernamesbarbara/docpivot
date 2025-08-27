"""Comprehensive validation framework for DocPivot.

This module provides validation utilities for documents, schemas, and parameters
throughout DocPivot operations. It includes validators for DoclingDocument structure,
Lexical JSON format, and general data validation patterns.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set, Tuple

from docling_core.types import DoclingDocument
from pydantic import ValidationError as PydanticValidationError

from docpivot.io.readers.exceptions import (
    ValidationError,
    SchemaValidationError,
    ConfigurationError,
    FileAccessError,
)

logger = logging.getLogger(__name__)


class DocumentValidator:
    """Validator for DoclingDocument structure and content."""

    # Required top-level DoclingDocument fields
    REQUIRED_DOCLING_FIELDS = {
        "schema_name",
        "version",
        "name",
        "origin",
        "furniture",
        "body",
        "groups",
        "texts",
        "pictures",
        "tables",
        "key_value_items",
        "pages",
    }

    # Expected schema name for DoclingDocument
    EXPECTED_SCHEMA_NAME = "DoclingDocument"

    # Supported DoclingDocument versions
    SUPPORTED_VERSIONS = {"1.4.0", "1.3.0", "1.2.0"}

    def validate_docling_document(
        self,
        doc_data: Union[Dict[str, Any], DoclingDocument],
        file_path: Optional[str] = None,
    ) -> None:
        """Validate DoclingDocument structure and required fields.

        Args:
            doc_data: Document data to validate (dict or DoclingDocument)
            file_path: Optional file path for error context

        Raises:
            ValidationError: If document structure is invalid
            SchemaValidationError: If schema validation fails
        """
        logger.debug(
            f"Validating DoclingDocument structure{f' for {file_path}' if file_path else ''}"
        )

        # Handle DoclingDocument objects
        if isinstance(doc_data, DoclingDocument):
            try:
                # DoclingDocument is already validated by Pydantic
                doc_dict = doc_data.model_dump()
            except Exception as e:
                raise ValidationError(
                    f"Failed to serialize DoclingDocument{f' from {file_path}' if file_path else ''}: {e}",
                    error_code="DOCUMENT_SERIALIZATION_ERROR",
                    context={"file_path": file_path, "original_error": str(e)},
                    cause=e,
                ) from e
        elif isinstance(doc_data, dict):
            doc_dict = doc_data
        else:
            raise ValidationError(
                f"Invalid DoclingDocument type{f' in {file_path}' if file_path else ''}: "
                f"Expected dict or DoclingDocument, got {type(doc_data).__name__}",
                error_code="INVALID_DOCUMENT_TYPE",
                context={
                    "file_path": file_path,
                    "actual_type": type(doc_data).__name__,
                },
            )

        # Validate schema structure
        self._validate_docling_schema(doc_dict, file_path)

        # Validate content structure
        self._validate_docling_content(doc_dict, file_path)

        logger.debug("DoclingDocument validation completed successfully")

    def _validate_docling_schema(
        self, doc_dict: Dict[str, Any], file_path: Optional[str]
    ) -> None:
        """Validate DoclingDocument schema fields.

        Args:
            doc_dict: Document dictionary to validate
            file_path: Optional file path for error context

        Raises:
            SchemaValidationError: If schema validation fails
        """
        # Check required fields
        missing_fields = self.REQUIRED_DOCLING_FIELDS - set(doc_dict.keys())
        if missing_fields:
            raise SchemaValidationError(
                f"DoclingDocument missing required fields{f' in {file_path}' if file_path else ''}: "
                f"{', '.join(sorted(missing_fields))}. "
                f"Required fields: {', '.join(sorted(self.REQUIRED_DOCLING_FIELDS))}",
                schema_name="DoclingDocument",
                missing_fields=list(missing_fields),
                context={"file_path": file_path},
            )

        # Validate schema name
        schema_name = doc_dict.get("schema_name")
        if schema_name != self.EXPECTED_SCHEMA_NAME:
            raise SchemaValidationError(
                f"Invalid DoclingDocument schema name{f' in {file_path}' if file_path else ''}: "
                f"Expected '{self.EXPECTED_SCHEMA_NAME}', got '{schema_name}'",
                schema_name=schema_name,
                expected_schema=self.EXPECTED_SCHEMA_NAME,
                actual_schema=schema_name,
                context={"file_path": file_path},
            )

        # Validate version
        version = doc_dict.get("version")
        if version not in self.SUPPORTED_VERSIONS:
            logger.warning(
                f"DoclingDocument version '{version}' is not in supported versions "
                f"{self.SUPPORTED_VERSIONS}. Processing may fail."
            )

    def _validate_docling_content(
        self, doc_dict: Dict[str, Any], file_path: Optional[str]
    ) -> None:
        """Validate DoclingDocument content structure.

        Args:
            doc_dict: Document dictionary to validate
            file_path: Optional file path for error context

        Raises:
            ValidationError: If content structure is invalid
        """
        # Validate origin field (can be dict or None)
        origin = doc_dict.get("origin")
        if origin is not None and not isinstance(origin, dict):
            raise ValidationError(
                f"DoclingDocument 'origin' field must be a dictionary or None{f' in {file_path}' if file_path else ''}",
                field_errors={"origin": ["Must be a dictionary or None"]},
                context={"file_path": file_path},
            )

        # Validate essential content fields
        for field_name in ["furniture", "body"]:
            field_value = doc_dict.get(field_name)
            if not isinstance(field_value, dict):
                raise ValidationError(
                    f"DoclingDocument '{field_name}' field must be a dictionary{f' in {file_path}' if file_path else ''}",
                    field_errors={field_name: ["Must be a dictionary"]},
                    context={"file_path": file_path},
                )

        # Validate array fields
        for field_name in ["groups", "texts", "pictures", "tables", "key_value_items"]:
            field_value = doc_dict.get(field_name)
            if not isinstance(field_value, list):
                raise ValidationError(
                    f"DoclingDocument '{field_name}' field must be a list{f' in {file_path}' if file_path else ''}",
                    field_errors={field_name: ["Must be a list"]},
                    context={"file_path": file_path},
                )


class LexicalValidator:
    """Validator for Lexical JSON format and structure."""

    # Required root-level Lexical fields
    REQUIRED_ROOT_FIELDS = {"root"}

    # Required fields in the root node
    REQUIRED_ROOT_NODE_FIELDS = {"children", "type"}

    # Valid Lexical node types
    VALID_NODE_TYPES = {
        "root",
        "text",
        "heading",
        "paragraph",
        "table",
        "tablerow",
        "tablecell",
        "list",
        "listitem",
        "link",
        "image",
    }

    # Valid list types
    VALID_LIST_TYPES = {"ordered", "unordered"}

    def validate_lexical_json(
        self, json_data: Dict[str, Any], file_path: Optional[str] = None
    ) -> None:
        """Validate Lexical JSON structure and content.

        Args:
            json_data: Lexical JSON data to validate
            file_path: Optional file path for error context

        Raises:
            ValidationError: If Lexical JSON structure is invalid
            SchemaValidationError: If schema validation fails
        """
        logger.debug(
            f"Validating Lexical JSON structure{f' for {file_path}' if file_path else ''}"
        )

        if not isinstance(json_data, dict):
            raise ValidationError(
                f"Invalid Lexical JSON format{f' in {file_path}' if file_path else ''}: "
                f"Expected JSON object, got {type(json_data).__name__}",
                error_code="INVALID_LEXICAL_FORMAT",
                context={
                    "file_path": file_path,
                    "actual_type": type(json_data).__name__,
                },
            )

        # Validate required root fields
        missing_fields = self.REQUIRED_ROOT_FIELDS - set(json_data.keys())
        if missing_fields:
            raise SchemaValidationError(
                f"Lexical JSON missing required fields{f' in {file_path}' if file_path else ''}: "
                f"{', '.join(sorted(missing_fields))}",
                schema_name="LexicalJSON",
                missing_fields=list(missing_fields),
                context={"file_path": file_path},
            )

        # Validate root node structure
        self._validate_lexical_root_node(json_data["root"], file_path)

        # Validate node hierarchy
        self._validate_lexical_nodes(json_data["root"].get("children", []), file_path)

        logger.debug("Lexical JSON validation completed successfully")

    def _validate_lexical_root_node(
        self, root_node: Any, file_path: Optional[str]
    ) -> None:
        """Validate Lexical root node structure.

        Args:
            root_node: Root node to validate
            file_path: Optional file path for error context

        Raises:
            ValidationError: If root node structure is invalid
        """
        if not isinstance(root_node, dict):
            raise ValidationError(
                f"Lexical JSON 'root' must be an object{f' in {file_path}' if file_path else ''}",
                field_errors={"root": ["Must be an object"]},
                context={"file_path": file_path},
            )

        # Check required root node fields
        missing_fields = self.REQUIRED_ROOT_NODE_FIELDS - set(root_node.keys())
        if missing_fields:
            raise ValidationError(
                f"Lexical JSON root node missing required fields{f' in {file_path}' if file_path else ''}: "
                f"{', '.join(sorted(missing_fields))}",
                field_errors={
                    "root": [f"Missing fields: {', '.join(sorted(missing_fields))}"]
                },
                context={"file_path": file_path},
            )

    def _validate_lexical_nodes(
        self, nodes: List[Any], file_path: Optional[str]
    ) -> None:
        """Validate Lexical node hierarchy.

        Args:
            nodes: List of nodes to validate
            file_path: Optional file path for error context

        Raises:
            ValidationError: If node structure is invalid
        """
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValidationError(
                    f"Lexical node {i} must be an object{f' in {file_path}' if file_path else ''}",
                    field_errors={f"node_{i}": ["Must be an object"]},
                    context={"file_path": file_path, "node_index": i},
                )

            # Validate node type
            node_type = node.get("type")
            if node_type not in self.VALID_NODE_TYPES:
                logger.warning(
                    f"Unknown Lexical node type '{node_type}' at node {i}"
                    f"{f' in {file_path}' if file_path else ''}. Processing may be incomplete."
                )

            # Recursively validate child nodes
            children = node.get("children")
            if children is not None:
                if not isinstance(children, list):
                    raise ValidationError(
                        f"Lexical node {i} 'children' must be a list{f' in {file_path}' if file_path else ''}",
                        field_errors={f"node_{i}.children": ["Must be a list"]},
                        context={"file_path": file_path, "node_index": i},
                    )
                self._validate_lexical_nodes(children, file_path)


class ParameterValidator:
    """Validator for parameters and configuration options."""

    def validate_serializer_params(
        self,
        params: Dict[str, Any],
        serializer_type: str,
        allowed_params: Optional[Set[str]] = None,
    ) -> None:
        """Validate serializer parameters.

        Args:
            params: Parameters to validate
            serializer_type: Type of serializer being configured
            allowed_params: Set of allowed parameter names (if None, all accepted)

        Raises:
            ConfigurationError: If parameters are invalid
        """
        logger.debug(f"Validating {serializer_type} serializer parameters")

        if not isinstance(params, dict):
            raise ConfigurationError(
                f"Serializer parameters must be a dictionary, got {type(params).__name__}",
                error_code="INVALID_PARAMETER_TYPE",
                context={
                    "serializer_type": serializer_type,
                    "actual_type": type(params).__name__,
                },
            )

        if allowed_params is not None:
            invalid_params = set(params.keys()) - allowed_params
            if invalid_params:
                raise ConfigurationError(
                    f"Invalid parameters for {serializer_type} serializer: "
                    f"{', '.join(sorted(invalid_params))}. "
                    f"Allowed parameters: {', '.join(sorted(allowed_params))}",
                    invalid_parameters=list(invalid_params),
                    valid_options={"allowed_parameters": list(allowed_params)},
                    context={"serializer_type": serializer_type},
                )

        logger.debug(f"{serializer_type} serializer parameters validation completed")

    def validate_file_path(
        self,
        file_path: Union[str, Path],
        must_exist: bool = True,
        must_be_file: bool = True,
        allowed_extensions: Optional[Set[str]] = None,
    ) -> Path:
        """Validate file path and return as Path object.

        Args:
            file_path: File path to validate
            must_exist: Whether the file must exist
            must_be_file: Whether the path must point to a file (not directory)
            allowed_extensions: Set of allowed file extensions (with dots)

        Returns:
            Path: Validated file path as Path object

        Raises:
            FileAccessError: If file validation fails
        """
        logger.debug(f"Validating file path: {file_path}")

        try:
            path = Path(file_path)
        except Exception as e:
            raise FileAccessError(
                f"Invalid file path: {file_path}",
                str(file_path),
                "validate_path",
                context={"original_error": str(e)},
                cause=e,
            ) from e

        if must_exist and not path.exists():
            raise FileAccessError(
                f"File not found: {file_path}", str(file_path), "check_existence"
            )

        if must_exist and must_be_file and path.is_dir():
            raise FileAccessError(
                f"Path is a directory, not a file: {file_path}",
                str(file_path),
                "check_file_type",
            )

        if allowed_extensions is not None:
            file_extension = path.suffix.lower()
            if file_extension not in allowed_extensions:
                raise FileAccessError(
                    f"Unsupported file extension: {file_extension} for file {file_path}. "
                    f"Allowed extensions: {', '.join(sorted(allowed_extensions))}",
                    str(file_path),
                    "check_extension",
                    context={
                        "detected_extension": file_extension,
                        "allowed_extensions": list(allowed_extensions),
                    },
                )

        logger.debug(f"File path validation completed: {path}")
        return path


class JsonValidator:
    """Validator for JSON content and structure."""

    def validate_json_content(
        self, content: str, file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate and parse JSON content.

        Args:
            content: JSON content string to validate
            file_path: Optional file path for error context

        Returns:
            Dict[str, Any]: Parsed JSON data

        Raises:
            ValidationError: If JSON is invalid
        """
        logger.debug(
            f"Validating JSON content{f' from {file_path}' if file_path else ''}"
        )

        if not isinstance(content, str):
            raise ValidationError(
                f"JSON content must be a string{f' from {file_path}' if file_path else ''}, "
                f"got {type(content).__name__}",
                error_code="INVALID_JSON_CONTENT_TYPE",
                context={"file_path": file_path, "actual_type": type(content).__name__},
            )

        if not content.strip():
            raise ValidationError(
                f"JSON content cannot be empty{f' from {file_path}' if file_path else ''}",
                error_code="EMPTY_JSON_CONTENT",
                context={"file_path": file_path},
            )

        try:
            json_data = json.loads(content)
            logger.debug(
                f"JSON content validation completed{f' for {file_path}' if file_path else ''}"
            )
            return json_data
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON format{f' in {file_path}' if file_path else ''} "
                f"at line {e.lineno}, column {e.colno}: {e.msg}. "
                f"Please check file format and syntax.",
                error_code="JSON_DECODE_ERROR",
                context={
                    "file_path": file_path,
                    "line_number": e.lineno,
                    "column_number": e.colno,
                    "json_error": e.msg,
                },
                cause=e,
            ) from e


# Global validator instances for convenience
document_validator = DocumentValidator()
lexical_validator = LexicalValidator()
parameter_validator = ParameterValidator()
json_validator = JsonValidator()


# Convenience functions for common validation operations
def validate_docling_document(
    doc_data: Union[Dict[str, Any], DoclingDocument], file_path: Optional[str] = None
) -> None:
    """Validate DoclingDocument structure.

    Args:
        doc_data: Document data to validate
        file_path: Optional file path for error context

    Raises:
        ValidationError: If validation fails
    """
    document_validator.validate_docling_document(doc_data, file_path)


def validate_lexical_json(
    json_data: Dict[str, Any], file_path: Optional[str] = None
) -> None:
    """Validate Lexical JSON structure.

    Args:
        json_data: Lexical JSON data to validate
        file_path: Optional file path for error context

    Raises:
        ValidationError: If validation fails
    """
    lexical_validator.validate_lexical_json(json_data, file_path)


def validate_file_path(
    file_path: Union[str, Path],
    must_exist: bool = True,
    must_be_file: bool = True,
    allowed_extensions: Optional[Set[str]] = None,
) -> Path:
    """Validate file path.

    Args:
        file_path: File path to validate
        must_exist: Whether the file must exist
        must_be_file: Whether the path must point to a file
        allowed_extensions: Set of allowed file extensions

    Returns:
        Path: Validated file path as Path object

    Raises:
        FileAccessError: If validation fails
    """
    return parameter_validator.validate_file_path(
        file_path, must_exist, must_be_file, allowed_extensions
    )


def validate_json_content(
    content: str, file_path: Optional[str] = None
) -> Dict[str, Any]:
    """Validate and parse JSON content.

    Args:
        content: JSON content string to validate
        file_path: Optional file path for error context

    Returns:
        Dict[str, Any]: Parsed JSON data

    Raises:
        ValidationError: If validation fails
    """
    return json_validator.validate_json_content(content, file_path)
