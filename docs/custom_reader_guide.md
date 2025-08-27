# Custom Reader Development Guide

This guide provides step-by-step instructions for creating custom readers in DocPivot.

## Overview

Custom readers convert files from your format into `DoclingDocument` objects. They handle format detection, file parsing, and document structure creation.

## Step 1: Set Up Your Reader Class

Start with the `CustomReaderBase` template:

```python
from pathlib import Path
from typing import Any, Dict, List, Union, Optional
from docling_core.types import DoclingDocument
from docpivot.io.readers.custom_reader_base import CustomReaderBase

class MyFormatReader(CustomReaderBase):
    pass  # We'll implement this step by step
```

## Step 2: Define Format Properties

Implement the required properties:

```python
@property
def supported_extensions(self) -> List[str]:
    """File extensions this reader supports."""
    return ['.myformat', '.mf']

@property
def format_name(self) -> str:
    """Human-readable format name."""
    return "My Custom Format"

@property
def format_description(self) -> Optional[str]:
    """Detailed description."""
    return "A custom format for demonstration purposes"

@property
def version(self) -> str:
    """Reader version."""
    return "1.0.0"

@property
def capabilities(self) -> Dict[str, bool]:
    """Reader capabilities."""
    return {
        "text_extraction": True,
        "metadata_extraction": True,
        "structure_preservation": True,
        "embedded_images": False,
        "embedded_tables": False,
    }
```

## Step 3: Implement Format Detection

The `can_handle` method determines if your reader can process a file:

```python
def can_handle(self, file_path: Union[str, Path]) -> bool:
    """Check if this reader can handle the given file."""
    path = Path(file_path)
    
    # Check file extension
    if path.suffix.lower() in self.supported_extensions:
        return True
    
    # Check file content signature
    try:
        with open(path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line.startswith('MYFORMAT:'):
                return True
    except Exception:
        return False
    
    return False
```

## Step 4: Implement File Loading

The `load_data` method is the core of your reader:

```python
def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
    """Load and parse a file."""
    path = self._validate_file_exists(file_path)
    self.validate_file_format(path)
    
    try:
        # Read file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse content (implement your parsing logic)
        parsed_data = self._parse_content(content)
        
        # Create DoclingDocument
        doc = DoclingDocument(
            name=path.stem,
            origin=DocumentOrigin(
                mimetype="application/x-myformat",
                binary_hash="",  # Compute if needed
                filename=path.name,
            ),
            furniture=[],
            body=self._create_document_structure(parsed_data)
        )
        
        return doc
        
    except Exception as e:
        raise ValueError(f"Failed to parse {path}: {e}")
```

## Step 5: Implement Parsing Logic

Add methods to parse your specific format:

```python
def _parse_content(self, content: str) -> Dict[str, Any]:
    """Parse content into structured data."""
    lines = content.strip().split('\n')
    
    # Example parsing logic for a simple format
    parsed = {
        'title': '',
        'sections': []
    }
    
    current_section = None
    
    for line in lines:
        if line.startswith('TITLE:'):
            parsed['title'] = line[6:].strip()
        elif line.startswith('SECTION:'):
            if current_section:
                parsed['sections'].append(current_section)
            current_section = {
                'name': line[8:].strip(),
                'content': []
            }
        elif line.strip() and current_section:
            current_section['content'].append(line.strip())
    
    if current_section:
        parsed['sections'].append(current_section)
    
    return parsed

def _create_document_structure(self, parsed_data: Dict[str, Any]) -> NodeItem:
    """Create document structure from parsed data."""
    from docling_core.types import NodeItem, TextItem
    
    root = NodeItem()
    children = []
    
    # Add title if present
    if parsed_data.get('title'):
        title_node = NodeItem(
            label="title",
            children=[TextItem(text=parsed_data['title'])]
        )
        children.append(title_node)
    
    # Add sections
    for section in parsed_data.get('sections', []):
        section_node = NodeItem(
            label="section",
            children=[TextItem(text=section['name'])]
        )
        
        # Add section content
        for content_line in section['content']:
            section_node.children.append(TextItem(text=content_line))
        
        children.append(section_node)
    
    root.children = children
    return root
```

## Step 6: Add Metadata Support

Implement metadata extraction:

```python
def get_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
    """Extract metadata without full parsing."""
    metadata = super().get_metadata(file_path)
    
    try:
        path = Path(file_path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(500)  # Read first 500 chars
        
        # Extract quick metadata
        lines = content.split('\n')
        for line in lines:
            if line.startswith('TITLE:'):
                metadata['title'] = line[6:].strip()
                break
        
        metadata['sections_count'] = content.count('SECTION:')
        
    except Exception:
        pass  # Return basic metadata on error
    
    return metadata
```

## Step 7: Add Configuration Support

Support configuration options:

```python
def __init__(self, **kwargs: Any) -> None:
    """Initialize with configuration."""
    super().__init__(**kwargs)
    
    # Set configuration defaults
    self.config.setdefault('encoding', 'utf-8')
    self.config.setdefault('strict_parsing', False)
    self.config.setdefault('ignore_comments', True)

def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
    """Load with configuration support."""
    # Merge instance config with method kwargs
    config = {**self.config, **kwargs}
    
    path = self._validate_file_exists(file_path)
    self.validate_file_format(path)
    
    try:
        encoding = config.get('encoding', 'utf-8')
        with open(path, 'r', encoding=encoding) as f:
            content = f.read()
        
        # Use config in parsing
        parsed_data = self._parse_content(content, config)
        # ... rest of implementation
```

## Step 8: Error Handling

Add robust error handling:

```python
def _parse_content(self, content: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Parse with error handling."""
    config = config or {}
    
    try:
        lines = content.strip().split('\n')
        parsed = {'title': '', 'sections': []}
        
        for line_num, line in enumerate(lines, 1):
            try:
                if line.startswith('TITLE:'):
                    parsed['title'] = line[6:].strip()
                elif line.startswith('SECTION:'):
                    # ... parsing logic
                    pass
            except Exception as e:
                if config.get('strict_parsing', False):
                    raise ValueError(f"Parse error at line {line_num}: {e}")
                # In non-strict mode, skip problematic lines
                continue
        
        return parsed
        
    except Exception as e:
        if config.get('strict_parsing', False):
            raise ValueError(f"Failed to parse content: {e}")
        
        # Fallback: return minimal structure
        return {'title': 'Parse Error', 'sections': []}
```

## Step 9: Testing Your Reader

Create tests using the testing framework:

```python
from docpivot.io.testing import CustomFormatTestBase
from docpivot.io.readers.basereader import BaseReader
from typing import Type, Optional, List
import tempfile
from pathlib import Path

class TestMyFormatReader(CustomFormatTestBase):
    def get_reader_class(self) -> Type[BaseReader]:
        return MyFormatReader
    
    def get_serializer_class(self) -> Optional[Type]:
        return None  # No serializer for this test
    
    def get_test_files(self) -> List[str]:
        # Create test files
        test_files = []
        
        # Create sample file
        test_content = """TITLE: Sample Document
SECTION: Introduction
This is the introduction section.
It has multiple lines.

SECTION: Body
This is the body section.
"""
        
        test_file = Path(tempfile.mktemp(suffix='.myformat'))
        test_file.write_text(test_content)
        test_files.append(str(test_file))
        
        return test_files

# Run the tests
if __name__ == '__main__':
    import unittest
    unittest.main()
```

## Step 10: Registration and Usage

Register your reader:

```python
from docpivot.io.format_registry import get_format_registry

# Register the reader
registry = get_format_registry()
registry.register_reader("myformat", MyFormatReader)

# Use the reader
reader = MyFormatReader()
doc = reader.load_data("sample.myformat")
```

## Advanced Features

### Content Validation

Add format-specific validation:

```python
def validate_file_format(self, file_path: Union[str, Path]) -> None:
    """Validate file format."""
    super().validate_file_format(file_path)
    
    # Custom validation
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        if not first_line.startswith('MYFORMAT:') and not first_line.startswith('TITLE:'):
            raise ValueError("File does not appear to be in My Format")
```

### Binary Format Support

For binary formats, adjust your approach:

```python
def can_handle(self, file_path: Union[str, Path]) -> bool:
    """Handle binary format detection."""
    path = Path(file_path)
    
    if path.suffix.lower() in self.supported_extensions:
        try:
            # Check binary signature
            with open(path, 'rb') as f:
                header = f.read(8)
                if header.startswith(b'MYBIN'):
                    return True
        except Exception:
            pass
    
    return False

def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
    """Load binary format."""
    path = self._validate_file_exists(file_path)
    
    with open(path, 'rb') as f:
        binary_data = f.read()
    
    # Parse binary data
    parsed_data = self._parse_binary_content(binary_data)
    # ... create DoclingDocument
```

### Streaming Support

For large files, consider streaming:

```python
def load_data(self, file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
    """Load with streaming support."""
    path = self._validate_file_exists(file_path)
    
    sections = []
    current_section = None
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Process line by line to avoid loading entire file
            if line.startswith('SECTION:'):
                if current_section:
                    sections.append(current_section)
                current_section = {'name': line[8:].strip(), 'content': []}
            elif current_section and line.strip():
                current_section['content'].append(line.strip())
    
    # Build document from streamed data
    return self._create_document_from_sections(sections)
```

## Best Practices

1. **Error Handling**: Provide clear, actionable error messages
2. **Performance**: Use streaming for large files
3. **Validation**: Validate inputs and file formats
4. **Configuration**: Support optional parameters
5. **Testing**: Use the comprehensive testing framework
6. **Documentation**: Include docstrings and examples
7. **Standards**: Follow Docling patterns and conventions

## Common Patterns

### Configuration Pattern
```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.config.setdefault('default_encoding', 'utf-8')
```

### Metadata Pattern
```python
def get_metadata(self, file_path):
    metadata = super().get_metadata(file_path)
    metadata.update(self._extract_format_specific_metadata(file_path))
    return metadata
```

### Error Recovery Pattern
```python
try:
    return self._parse_strict(content)
except ParseError:
    if self.config.get('allow_fallback', True):
        return self._parse_lenient(content)
    raise
```

This guide provides a complete foundation for creating custom readers. Refer to the `examples/custom_formats/xml_reader.py` for a working implementation example.