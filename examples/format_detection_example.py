"""Example demonstrating format detection and automatic reader selection."""

from docpivot.io.readers import ReaderFactory, LexicalJsonReader, DoclingJsonReader
from docpivot.io.readers.exceptions import UnsupportedFormatError


def demonstrate_format_detection():
    """Demonstrate automatic format detection and reader selection."""

    # Create a reader factory
    factory = ReaderFactory()

    # Demonstrate supported formats
    print("Supported formats:", factory.get_supported_formats())

    # Example 1: Automatic reader selection for Lexical JSON
    lexical_file = "data/json/2025-07-03-Test-PDF-Styles.lexical.json"

    try:
        print(f"\n1. Testing automatic detection for: {lexical_file}")

        # Detect format first
        format_name = factory.detect_format(lexical_file)
        print(f"   Detected format: {format_name}")

        # Get appropriate reader
        reader = factory.get_reader(lexical_file)
        print(f"   Reader type: {type(reader).__name__}")

        # Load document
        doc = reader.load_data(lexical_file)
        print(f"   Document loaded: {doc.name}")
        print(f"   Text items: {len(doc.texts)}")
        print(f"   Groups: {len(doc.groups)}")
        print(f"   Tables: {len(doc.tables)}")

    except (FileNotFoundError, UnsupportedFormatError) as e:
        print(f"   Error: {e}")

    # Example 2: Automatic reader selection for Docling JSON
    docling_file = "data/json/2025-07-03-Test-PDF-Styles.docling.json"

    try:
        print(f"\n2. Testing automatic detection for: {docling_file}")

        # Detect format and get reader in one step
        reader = factory.get_reader(docling_file)
        print(f"   Reader type: {type(reader).__name__}")

        # Load document
        doc = reader.load_data(docling_file)
        print(f"   Document loaded: {doc.name}")
        print(f"   Text items: {len(doc.texts)}")
        print(f"   Groups: {len(doc.groups)}")
        print(f"   Tables: {len(doc.tables)}")

    except (FileNotFoundError, UnsupportedFormatError) as e:
        print(f"   Error: {e}")

    # Example 3: Handling unsupported formats
    unsupported_file = "README.md"

    try:
        print(f"\n3. Testing unsupported format: {unsupported_file}")

        if factory.is_supported_format(unsupported_file):
            reader = factory.get_reader(unsupported_file)
            print(f"   Reader type: {type(reader).__name__}")
        else:
            print("   Format not supported")

    except UnsupportedFormatError as e:
        print(f"   Expected error: {type(e).__name__}")

    # Example 4: Direct reader usage
    print("\n4. Testing direct reader usage")

    try:
        # Use LexicalJsonReader directly
        lexical_reader = LexicalJsonReader()
        if lexical_reader.detect_format(lexical_file):
            doc = lexical_reader.load_data(lexical_file)
            print(f"   Direct Lexical reader: {doc.name}")

        # Use DoclingJsonReader directly
        docling_reader = DoclingJsonReader()
        if docling_reader.detect_format(docling_file):
            doc = docling_reader.load_data(docling_file)
            print(f"   Direct Docling reader: {doc.name}")

    except (FileNotFoundError, UnsupportedFormatError) as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    demonstrate_format_detection()
