"""Example demonstrating end-to-end workflows matching PRD usage patterns."""

from docpivot import load_and_serialize, load_document, SerializerProvider
from docling_core.transforms.serializer.markdown import MarkdownParams


def demonstrate_high_level_api():
    """Demonstrate the high-level API functions."""
    
    print("=== High-Level API Examples ===\n")
    
    # Example 1: Simple load and serialize (PRD pattern)
    print("1. Basic Markdown Export")
    print("   Code: result = load_and_serialize('sample.docling.json', 'markdown')")
    
    try:
        result = load_and_serialize("data/json/2025-07-03-Test-PDF-Styles.docling.json", "markdown")
        print(f"   Output: {len(result.text)} characters")
        print(f"   Preview: {result.text[:100]}...\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 2: Customized export with parameters (PRD pattern)  
    print("2. Customized Markdown Export")
    print("   Code: load_document() + SerializerProvider().get_serializer()")
    
    try:
        doc = load_document("data/json/2025-07-03-Test-PDF-Styles.docling.json")
        serializer = SerializerProvider().get_serializer(
            "markdown", 
            doc=doc,
            params=MarkdownParams(image_placeholder="(no image)")
        )
        result = serializer.serialize()
        print(f"   Output: {len(result.text)} characters")
        print(f"   Preview: {result.text[:100]}...\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 3: Lexical export (PRD pattern)
    print("3. Lexical JSON Export")
    print("   Code: load_and_serialize('sample.docling.json', 'lexical')")
    
    try:
        result = load_and_serialize("data/json/2025-07-03-Test-PDF-Styles.docling.json", "lexical")
        print(f"   Output: {len(result.text)} characters")
        # Verify it's valid JSON
        import json
        lexical_data = json.loads(result.text)
        print(f"   Lexical structure: root node with {len(lexical_data.get('root', {}).get('children', []))} children\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 4: Multiple format conversion
    print("4. Multiple Format Conversion")
    print("   Code: Converting same document to multiple formats")
    
    formats = ["markdown", "html", "lexical"]
    try:
        for format_name in formats:
            result = load_and_serialize("data/json/2025-07-03-Test-PDF-Styles.docling.json", format_name)
            print(f"   {format_name.upper()}: {len(result.text)} characters")
        print()
    except Exception as e:
        print(f"   Error: {e}\n")


def demonstrate_format_detection():
    """Demonstrate automatic format detection across different input formats."""
    
    print("=== Format Detection Examples ===\n")
    
    files = [
        ("Docling JSON", "data/json/2025-07-03-Test-PDF-Styles.docling.json"),
        ("Lexical JSON", "data/json/2025-07-03-Test-PDF-Styles.lexical.json"),
    ]
    
    for file_type, file_path in files:
        print(f"Processing {file_type}: {file_path}")
        
        try:
            # Auto-detection workflow
            doc = load_document(file_path)
            print(f"   Loaded: {doc.name}")
            print(f"   Text items: {len(doc.texts)}")
            print(f"   Tables: {len(doc.tables)}")
            
            # Convert to markdown
            result = load_and_serialize(file_path, "markdown")
            print(f"   Markdown output: {len(result.text)} characters")
            print()
            
        except Exception as e:
            print(f"   Error: {e}\n")


def demonstrate_error_handling():
    """Demonstrate error handling capabilities."""
    
    print("=== Error Handling Examples ===\n")
    
    # Test unsupported input format
    print("1. Unsupported Input Format")
    try:
        result = load_and_serialize("README.md", "markdown")
        print("   Unexpected success!")
    except Exception as e:
        print(f"   Expected error: {type(e).__name__}: {e}\n")
    
    # Test unsupported output format
    print("2. Unsupported Output Format")
    try:
        result = load_and_serialize("data/json/2025-07-03-Test-PDF-Styles.docling.json", "unknown_format")
        print("   Unexpected success!")
    except Exception as e:
        print(f"   Expected error: {type(e).__name__}: {e}\n")
    
    # Test file not found
    print("3. File Not Found")
    try:
        result = load_and_serialize("nonexistent_file.json", "markdown")
        print("   Unexpected success!")
    except Exception as e:
        print(f"   Expected error: {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    print("DocPivot End-to-End Workflows Example")
    print("=====================================\n")
    
    demonstrate_high_level_api()
    demonstrate_format_detection()
    demonstrate_error_handling()
    
    print("Example completed successfully!")