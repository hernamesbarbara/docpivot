"""High-level workflow functions for end-to-end document processing."""

from pathlib import Path
from typing import Any, Optional, Union

from docling_core.transforms.serializer.base import SerializationResult
from docling_core.types import DoclingDocument

from docpivot.io.readers import ReaderFactory
from docpivot.io.serializers import SerializerProvider


def load_document(file_path: Union[str, Path], **kwargs: Any) -> DoclingDocument:
    """Auto-detect format and load document into DoclingDocument.
    
    This function provides a simple interface for loading any supported document
    format by automatically detecting the format and selecting the appropriate
    reader.
    
    Args:
        file_path: Path to the document file to load
        **kwargs: Additional parameters to pass to the reader
        
    Returns:
        DoclingDocument: The loaded document
        
    Raises:
        FileNotFoundError: If the file does not exist
        UnsupportedFormatError: If no reader can handle the file format
        ValueError: If the file format is invalid or corrupted
        
    Example:
        >>> doc = load_document("sample.docling.json")
        >>> print(f"Loaded document: {doc.name}")
    """
    factory = ReaderFactory()
    reader = factory.get_reader(file_path, **kwargs)
    return reader.load_data(file_path, **kwargs)


def load_and_serialize(
    input_path: Union[str, Path], 
    output_format: str, 
    **kwargs: Any
) -> SerializationResult:
    """Load document and serialize to target format in one call.
    
    This function combines document loading and serialization into a single
    operation, automatically detecting the input format and using the
    appropriate serializer for the output format.
    
    Args:
        input_path: Path to the input document file
        output_format: Target output format (e.g., "markdown", "html", "lexical")
        **kwargs: Additional parameters to pass to the serializer
        
    Returns:
        SerializationResult: The serialized document with .text property
        
    Raises:
        FileNotFoundError: If the input file does not exist
        UnsupportedFormatError: If input format is not supported
        ValueError: If output format is not supported or parameters are invalid
        
    Example:
        >>> result = load_and_serialize("sample.docling.json", "markdown")
        >>> print(result.text)
    """
    # Load the document using automatic format detection
    doc = load_document(input_path)
    
    # Get the appropriate serializer and serialize
    provider = SerializerProvider()
    serializer = provider.get_serializer(output_format, doc=doc, **kwargs)
    return serializer.serialize()


def convert_document(
    input_path: Union[str, Path],
    output_format: str,
    output_path: Optional[Union[str, Path]] = None,
    **kwargs: Any
) -> Optional[str]:
    """Complete conversion with optional file output.
    
    This function performs a complete document conversion, optionally writing
    the result to a file. It combines loading, serialization, and file I/O
    into a single operation.
    
    Args:
        input_path: Path to the input document file
        output_format: Target output format (e.g., "markdown", "html", "lexical")
        output_path: Optional path to write output file. If None, returns content as string
        **kwargs: Additional parameters to pass to the serializer
        
    Returns:
        Optional[str]: If output_path is None, returns serialized content as string.
                      If output_path is provided, writes to file and returns the output path.
        
    Raises:
        FileNotFoundError: If the input file does not exist
        UnsupportedFormatError: If input format is not supported
        ValueError: If output format is not supported or parameters are invalid
        IOError: If there are issues writing the output file
        
    Examples:
        >>> # Convert and return content as string
        >>> content = convert_document("sample.docling.json", "markdown")
        >>> print(content)
        
        >>> # Convert and write to file
        >>> output_file = convert_document(
        ...     "sample.docling.json", 
        ...     "markdown", 
        ...     "output.md"
        ... )
        >>> print(f"Converted document written to: {output_file}")
    """
    # Load and serialize the document
    result = load_and_serialize(input_path, output_format, **kwargs)
    
    # Handle output
    if output_path is None:
        return result.text
    
    # Write to file
    output_file = Path(output_path)
    try:
        output_file.write_text(result.text, encoding="utf-8")
        return str(output_file)
    except IOError as e:
        raise IOError(f"Failed to write output file {output_path}: {e}") from e
