#!/usr/bin/env python3
"""Lexical JSON Export Example - PRD Pattern Implementation

This example demonstrates DocPivot's Lexical JSON serialization capability,
converting Docling documents to Lexical JSON format.
"""

import json
from docpivot.io.readers import DoclingJsonReader
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer


def main():
    """Demonstrate Lexical JSON export workflow."""
    print("=== Lexical JSON Export (PRD Example) ===\n")
    
    # PRD Example Implementation:
    # from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
    #
    # serializer = LexicalDocSerializer(doc=doc)
    # ser_result = serializer.serialize()
    # print(ser_result.text)
    
    try:
        # Load document
        print("1. Loading Docling JSON document...")
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")
        print(f"   ✓ Loaded document: {doc.name}")
        print(f"   ✓ Text items: {len(doc.texts)}")
        print(f"   ✓ Tables: {len(doc.tables)}")
        print(f"   ✓ Pictures: {len(doc.pictures)}")
        
        # Serialize to Lexical JSON
        print("\n2. Converting to Lexical JSON...")
        serializer = LexicalDocSerializer(doc=doc)
        ser_result = serializer.serialize()
        print(f"   ✓ Generated {len(ser_result.text)} characters of Lexical JSON")
        
        # Validate JSON structure
        print("\n3. Validating JSON structure...")
        try:
            lexical_data = json.loads(ser_result.text)
            print("   ✓ Valid JSON structure")
            
            # Analyze Lexical structure
            root = lexical_data.get("root", {})
            children = root.get("children", [])
            print(f"   ✓ Root node with {len(children)} children")
            
            # Count different node types
            node_types = {}
            def count_nodes(node):
                if isinstance(node, dict):
                    node_type = node.get("type", "unknown")
                    node_types[node_type] = node_types.get(node_type, 0) + 1
                    
                    # Recursively count children
                    children = node.get("children", [])
                    for child in children:
                        count_nodes(child)
                elif isinstance(node, list):
                    for item in node:
                        count_nodes(item)
            
            count_nodes(lexical_data)
            
            print("   ✓ Node type distribution:")
            for node_type, count in sorted(node_types.items()):
                print(f"     - {node_type}: {count}")
            
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON validation failed: {e}")
            return
        
        # Display structure preview
        print("\n4. Lexical JSON Structure Preview:")
        print("-" * 50)
        
        # Pretty print a portion of the JSON for inspection
        try:
            formatted_json = json.dumps(lexical_data, indent=2, ensure_ascii=False)
            lines = formatted_json.split('\n')
            
            # Show first 25 lines
            for i, line in enumerate(lines[:25]):
                print(f"{i+1:2d}: {line}")
            
            if len(lines) > 25:
                print(f"    ... ({len(lines) - 25} more lines)")
            
        except Exception as e:
            print(f"   Error formatting JSON preview: {e}")
            # Fallback to raw text preview
            lines = ser_result.text.split('\n')
            for i, line in enumerate(lines[:10]):
                print(f"{i+1:2d}: {line[:100]}")
        
        print("-" * 50)
        
        # Save to file
        output_file = "output_lexical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ser_result.text)
        print(f"\n5. Saved to: {output_file}")
        
        # Save formatted version for easier reading
        formatted_file = "output_lexical_formatted.json"
        with open(formatted_file, 'w', encoding='utf-8') as f:
            json.dump(lexical_data, f, indent=2, ensure_ascii=False)
        print(f"   Saved formatted version to: {formatted_file}")
        
        print("\n✅ Lexical JSON export completed successfully!")
        print("\nLexical JSON features demonstrated:")
        print("  ✓ DoclingDocument to Lexical JSON conversion")
        print("  ✓ Valid JSON structure generation")
        print("  ✓ Hierarchical node structure preservation")
        print("  ✓ Multiple node types (text, paragraph, heading, etc.)")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Input file not found - {e}")
        print("   Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()