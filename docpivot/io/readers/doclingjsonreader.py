"""DoclingJsonReader for loading .docling.json files into DoclingDocument objects."""

import json
from pathlib import Path
from typing import Any, Dict

from docling_core.types import DoclingDocument
from pydantic import ValidationError

from .basereader import BaseReader


class DoclingJsonReader(BaseReader):
    """Reader for .docling.json files that loads them into DoclingDocument objects.
    
    This reader handles the native Docling JSON format produced by DocumentConverter
    and other Docling tools. It validates the schema and reconstructs the full
    DoclingDocument object.
    """
    
    SUPPORTED_EXTENSIONS = {".docling.json", ".json"}
    REQUIRED_SCHEMA_FIELDS = {"schema_name", "version"}
    EXPECTED_SCHEMA_NAME = "DoclingDocument"
    
    def load_data(self, file_path: str, **kwargs) -> DoclingDocument:
        """Load document from .docling.json file into DoclingDocument.
        
        Args:
            file_path: Path to the .docling.json file to load
            **kwargs: Additional parameters (currently unused)
            
        Returns:
            DoclingDocument: The loaded document as a DoclingDocument object
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file format is not supported or JSON is invalid
            IOError: If there are issues reading the file
        """
        # Validate file exists and is readable
        path = self._validate_file_exists(file_path)
        
        # Check format detection
        if not self.detect_format(file_path):
            raise ValueError(self._get_format_error_message(file_path))
        
        try:
            # Read and parse JSON file
            json_content = path.read_text(encoding='utf-8')
            
            # Parse JSON content
            try:
                json_data = json.loads(json_content)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON format in file '{file_path}': {e}"
                ) from e
            
            # Validate DoclingDocument schema
            self._validate_docling_schema(json_data, file_path)
            
            # Create DoclingDocument from JSON data
            try:
                return DoclingDocument.model_validate(json_data)
            except ValidationError as e:
                raise ValueError(
                    f"Invalid DoclingDocument schema in file '{file_path}': {e}"
                ) from e
                
        except IOError as e:
            raise IOError(
                f"Error reading file '{file_path}': {e}"
            ) from e
    
    def detect_format(self, file_path: str) -> bool:
        """Detect if this reader can handle the given file format.
        
        Checks for .docling.json extension and optionally validates the content
        structure for .json files.
        
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
        
        # For .docling.json files, we assume they are valid
        if path.name.endswith('.docling.json'):
            return True
            
        # For generic .json files, check content structure
        if suffix == '.json':
            return self._check_docling_json_content(path)
            
        return False
    
    def _check_docling_json_content(self, path: Path) -> bool:
        """Check if a .json file contains DoclingDocument content.
        
        Args:
            path: Path object to the JSON file
            
        Returns:
            bool: True if the file appears to contain DoclingDocument data
        """
        try:
            # Read and parse a small portion to check schema
            with path.open('r', encoding='utf-8') as f:
                # Read first chunk to check for schema markers
                chunk = f.read(512)
                
            # Quick check for DoclingDocument markers
            return (
                '"schema_name"' in chunk and 
                '"DoclingDocument"' in chunk and
                '"version"' in chunk
            )
            
        except (IOError, UnicodeDecodeError):
            return False
    
    def _validate_docling_schema(self, json_data: Dict[str, Any], file_path: str) -> None:
        """Validate that JSON data has expected DoclingDocument schema structure.
        
        Args:
            json_data: Parsed JSON data dictionary
            file_path: Path to the file being validated (for error messages)
            
        Raises:
            ValueError: If the schema is invalid or missing required fields
        """
        if not isinstance(json_data, dict):
            raise ValueError(
                f"Invalid DoclingDocument format in '{file_path}': "
                f"Expected JSON object, got {type(json_data).__name__}"
            )
        
        # Check for required schema fields
        missing_fields = self.REQUIRED_SCHEMA_FIELDS - set(json_data.keys())
        if missing_fields:
            raise ValueError(
                f"Invalid DoclingDocument schema in '{file_path}': "
                f"Missing required fields: {', '.join(sorted(missing_fields))}"
            )
        
        # Validate schema name
        schema_name = json_data.get("schema_name")
        if schema_name != self.EXPECTED_SCHEMA_NAME:
            raise ValueError(
                f"Invalid DoclingDocument schema in '{file_path}': "
                f"Expected schema_name '{self.EXPECTED_SCHEMA_NAME}', "
                f"got '{schema_name}'"
            )