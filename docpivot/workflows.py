"""High-level workflow functions for DocPivot end-to-end processing."""

from pathlib import Path
from typing import Optional, Union, Any
from docling_core.types import DoclingDocument
from docling_core.transforms.serializer.base import SerializationResult

from docpivot.io.readers.readerfactory import ReaderFactory
from docpivot.io.serializers.serializerprovider import SerializerProvider


def load_document(file_path: Union[str, Path], **kwargs) -> DoclingDocument:
    """Auto-detect format and load document into DoclingDocument.
    
    Uses ReaderFactory for format detection and reader selection.
    
    Args:
        file_path: Path to the document file
        **kwargs: Additional arguments passed to the reader
        
    Returns:
        DoclingDocument: Loaded document
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnsupportedFormatError: If format is not supported
        ValueError: If file content is invalid
    """
    factory = ReaderFactory()
    reader = factory.get_reader(file_path, **kwargs)
    return reader.load_data(file_path)


def load_and_serialize(
    input_path: Union[str, Path], 
    output_format: str, 
    **kwargs
) -> SerializationResult:
    """Complete workflow: load document and serialize to target format in one call.
    
    Combines ReaderFactory + SerializerProvider for end-to-end processing.
    
    Args:
        input_path: Path to the input document file
        output_format: Target serialization format (markdown, html, lexical, doctags)
        **kwargs: Additional arguments passed to serializer
        
    Returns:
        SerializationResult: Serialized output
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        UnsupportedFormatError: If input or output format is not supported
        ValueError: If file content or serializer parameters are invalid
    """
    # Load document using auto-detection
    doc = load_document(input_path)
    
    # Get serializer and serialize
    provider = SerializerProvider()
    serializer = provider.get_serializer(output_format, doc=doc, **kwargs)
    return serializer.serialize()


def convert_document(
    input_path: Union[str, Path],
    output_format: str,
    output_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> Optional[str]:
    """Complete conversion with optional file output.
    
    If output_path provided, writes to file and returns path.
    If output_path is None, returns serialized content as string.
    
    Args:
        input_path: Path to the input document file
        output_format: Target serialization format
        output_path: Optional path to write output file
        **kwargs: Additional arguments passed to serializer
        
    Returns:
        Optional[str]: Output file path if written to file, None otherwise
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        UnsupportedFormatError: If input or output format is not supported
        ValueError: If file content or serializer parameters are invalid
        IOError: If unable to write output file
    """
    # Load and serialize
    result = load_and_serialize(input_path, output_format, **kwargs)
    
    if output_path is not None:
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.text, encoding='utf-8')
        return str(output_path)
    
    return result.text