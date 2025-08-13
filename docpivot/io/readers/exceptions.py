"""Exceptions for document readers."""


class UnsupportedFormatError(ValueError):
    """Raised when an unsupported file format is encountered.
    
    This exception provides clear error messages to guide users toward
    supported formats and implementation options.
    """
    
    def __init__(self, file_path: str, supported_formats: list[str] = None):
        """Initialize UnsupportedFormatError.
        
        Args:
            file_path: Path to the file with unsupported format
            supported_formats: List of supported format descriptions
        """
        if supported_formats is None:
            supported_formats = [
                ".docling.json files (Docling native format)",
                ".lexical.json files (Lexical JSON format)", 
                ".json files with DoclingDocument or Lexical content"
            ]
            
        message = (
            f"Unsupported file format: '{file_path}'\n"
            f"Supported formats:\n" + 
            "\n".join(f"  - {fmt}" for fmt in supported_formats) +
            "\n\nTo add support for additional formats, extend BaseReader."
        )
        super().__init__(message)
        self.file_path = file_path
        self.supported_formats = supported_formats