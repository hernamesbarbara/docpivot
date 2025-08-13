"""DocPivot: Extend Docling with additional format support.

A lightweight Python package that extends Docling functionality by enabling
seamless conversion of rich-text documents to and from formats not natively
supported by Docling, such as Lexical JSON and other JSON variants.
"""

from docpivot.io.readers.basereader import BaseReader

__version__ = "0.1.0"
__all__ = ["BaseReader"]
