"""Demonstration of advanced LexicalDocSerializer features."""

from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.serializers.lexicaldocserializer import (
    LexicalDocSerializer,
    LexicalParams
)


def demo_basic_usage():
    """Demonstrate basic serialization without parameters."""
    print("=== Basic LexicalDocSerializer Usage ===")

    reader = DoclingJsonReader()
    doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

    serializer = LexicalDocSerializer(doc=doc)
    result = serializer.serialize()

    print(f"Generated JSON length: {len(result.text)} characters")
    print("First 200 characters:")
    print(result.text[:200])
    print()


def demo_configuration_options():
    """Demonstrate LexicalParams configuration options."""
    print("=== Advanced Configuration Options ===")

    reader = DoclingJsonReader()
    doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

    # Configure with custom parameters
    custom_params = LexicalParams(
        include_metadata=True,
        preserve_formatting=True,
        indent_json=False,  # Compact JSON
        version=2,
        custom_root_attributes={
            "theme": "light",
            "editable": True
        }
    )

    serializer = LexicalDocSerializer(doc=doc, params=custom_params)
    result = serializer.serialize()

    print(f"Compact JSON (no indentation): {len(result.text)} characters")
    print("Sample of compact output:")
    print(result.text[:150])
    print()

    # Show with indentation for comparison
    indented_params = LexicalParams(
        include_metadata=True,
        indent_json=True,
        custom_root_attributes={"theme": "dark"}
    )

    indented_serializer = LexicalDocSerializer(doc=doc, params=indented_params)
    indented_result = indented_serializer.serialize()

    print(f"Indented JSON: {len(indented_result.text)} characters")
    print("Sample of indented output:")
    print(indented_result.text[:300])
    print()


def demo_custom_serializers():
    """Demonstrate custom component serializers."""
    print("=== Custom Component Serializers ===")

    class CustomImageSerializer:
        """Custom image serializer that adds watermarks."""

        def serialize(self, image_item, params=None):
            return {
                "type": "watermarked_image",
                "src": f"watermark_{getattr(image_item, 'path', 'unknown.jpg')}",
                "altText": getattr(image_item, 'caption', 'Watermarked image'),
                "watermark": "© 2025 DocPivot",
                "version": params.version if params else 1
            }

    reader = DoclingJsonReader()
    doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

    custom_image_serializer = CustomImageSerializer()
    params = LexicalParams(version=3)

    serializer = LexicalDocSerializer(
        doc=doc,
        params=params,
        image_serializer=custom_image_serializer
    )

    result = serializer.serialize()
    print("Serialization with custom image serializer completed")
    print(f"Result length: {len(result.text)} characters")

    # Check if any watermarked images were processed
    if "watermarked_image" in result.text:
        print("✓ Custom image serializer was used")
    else:
        print("ℹ No images found in this document to apply custom serializer")

    print()


def demo_formatting_detection():
    """Demonstrate text formatting detection capabilities."""
    print("=== Text Formatting Detection ===")

    reader = DoclingJsonReader()
    doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

    # Enable formatting detection
    formatting_params = LexicalParams(
        preserve_formatting=True,
        indent_json=True
    )

    serializer = LexicalDocSerializer(doc=doc, params=formatting_params)
    result = serializer.serialize()

    # Look for formatted text in the output
    import json
    lexical_data = json.loads(result.text)

    def find_formatted_text(node, path="root"):
        """Recursively find text nodes with formatting."""
        formatted_nodes = []

        if isinstance(node, dict):
            if node.get("type") == "text" and node.get("format", 0) != 0:
                formatted_nodes.append({
                    "path": path,
                    "text": node.get("text", ""),
                    "format": node.get("format", 0)
                })

            for key, child in node.items():
                if key == "children" and isinstance(child, list):
                    for i, item in enumerate(child):
                        formatted_nodes.extend(find_formatted_text(item, f"{path}.{key}[{i}]"))
                elif isinstance(child, (dict, list)):
                    formatted_nodes.extend(find_formatted_text(child, f"{path}.{key}"))
        elif isinstance(node, list):
            for i, item in enumerate(node):
                formatted_nodes.extend(find_formatted_text(item, f"{path}[{i}]"))

        return formatted_nodes

    formatted_text = find_formatted_text(lexical_data)

    if formatted_text:
        print(f"Found {len(formatted_text)} formatted text nodes:")
        for node in formatted_text[:3]:  # Show first 3
            print(f"  - '{node['text'][:50]}...' (format: {node['format']})")
    else:
        print("No formatted text detected (this is normal for the sample document)")

    print()


if __name__ == "__main__":
    print("Advanced LexicalDocSerializer Features Demo\n")

    try:
        demo_basic_usage()
        demo_configuration_options()
        demo_custom_serializers()
        demo_formatting_detection()

        print("=== Demo Complete ===")
        print("The LexicalDocSerializer now supports:")
        print("✓ Advanced configuration parameters (LexicalParams)")
        print("✓ Custom root attributes")
        print("✓ Document metadata inclusion")
        print("✓ Text formatting detection and preservation")
        print("✓ Component serializer support for images and tables")
        print("✓ Link node creation capabilities")
        print("✓ JSON output formatting control")
        print("✓ Version consistency across all nodes")

    except Exception as e:
        print(f"Demo encountered an error: {e}")
        print("Make sure you're running this from the project root directory.")
