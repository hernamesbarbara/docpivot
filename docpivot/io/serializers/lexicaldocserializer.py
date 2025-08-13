"""LexicalDocSerializer for converting DoclingDocument to Lexical JSON format."""

import json
from typing import Any, Dict, List, Union, Optional

from docling_core.transforms.serializer.base import SerializationResult
from docling_core.types import DoclingDocument


class LexicalDocSerializer:
    """Serializer for converting DoclingDocument objects to Lexical JSON format.
    
    This serializer transforms DoclingDocument elements into Lexical's nested node
    structure, handling the conversion between referenced elements and hierarchical nodes.
    """

    def __init__(self, doc: DoclingDocument, **kwargs: Any) -> None:
        """Initialize the LexicalDocSerializer.
        
        Args:
            doc: The DoclingDocument to serialize
            **kwargs: Additional parameters (currently unused)
        """
        self.doc = doc

    def serialize(self) -> SerializationResult:
        """Serialize the DoclingDocument to Lexical JSON format.
        
        Returns:
            SerializationResult: The serialization result with Lexical JSON in .text
        """
        lexical_data = self._transform_docling_to_lexical()
        json_text = json.dumps(lexical_data, indent=2, ensure_ascii=False)
        
        return SerializationResult(text=json_text)

    def _transform_docling_to_lexical(self) -> Dict[str, Any]:
        """Transform DoclingDocument to Lexical JSON structure.
        
        Returns:
            Dict representing the Lexical JSON structure
        """
        # Process body children to create Lexical nodes
        lexical_children = self._process_body_children()
        
        # Create the root Lexical structure
        lexical_data = {
            "root": {
                "children": lexical_children,
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1
            }
        }
        
        return lexical_data

    def _process_body_children(self) -> List[Dict[str, Any]]:
        """Process DoclingDocument body children and convert to Lexical nodes.
        
        Returns:
            List of Lexical nodes
        """
        lexical_nodes = []
        
        for child_ref in self.doc.body.children:
            if not child_ref.cref:
                continue
                
            # Parse the reference to determine type and index
            ref_parts = child_ref.cref.split("/")
            if len(ref_parts) < 3:
                continue
                
            element_type = ref_parts[1]  # texts, tables, groups, etc.
            element_index = int(ref_parts[2])
            
            if element_type == "texts":
                text_item = self.doc.texts[element_index]
                lexical_node = self._create_text_node(text_item)
                if lexical_node:
                    lexical_nodes.append(lexical_node)
                    
            elif element_type == "tables":
                table_item = self.doc.tables[element_index]
                lexical_node = self._create_table_node(table_item)
                if lexical_node:
                    lexical_nodes.append(lexical_node)
                    
            elif element_type == "groups":
                group_item = self.doc.groups[element_index]
                lexical_node = self._create_group_node(group_item)
                if lexical_node:
                    lexical_nodes.append(lexical_node)
        
        return lexical_nodes

    def _create_text_node(self, text_item: Any) -> Optional[Dict[str, Any]]:
        """Create a Lexical node from a DoclingDocument TextItem.
        
        Args:
            text_item: The TextItem to convert
            
        Returns:
            Lexical node dictionary or None if conversion fails
        """
        if text_item.label == "section_header":
            return self._create_heading_node(text_item)
        else:
            return self._create_paragraph_node(text_item)

    def _create_heading_node(self, text_item: Any) -> Dict[str, Any]:
        """Create a Lexical heading node from a TextItem.
        
        Args:
            text_item: The heading TextItem
            
        Returns:
            Lexical heading node
        """
        # Map level to HTML heading tags
        level = getattr(text_item, 'level', 1)
        tag = f"h{min(max(level, 1), 6)}"  # Ensure h1-h6 range
        
        return {
            "children": [
                {
                    "detail": 0,
                    "format": 0,
                    "mode": "normal",
                    "style": "",
                    "text": text_item.text,
                    "type": "text",
                    "version": 1
                }
            ],
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "tag": tag,
            "type": "heading",
            "version": 1
        }

    def _create_paragraph_node(self, text_item: Any) -> Dict[str, Any]:
        """Create a Lexical paragraph node from a TextItem.
        
        Args:
            text_item: The paragraph TextItem
            
        Returns:
            Lexical paragraph node
        """
        return {
            "children": [
                {
                    "detail": 0,
                    "format": 0,
                    "mode": "normal",
                    "style": "",
                    "text": text_item.text,
                    "type": "text",
                    "version": 1
                }
            ],
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "type": "paragraph",
            "version": 1
        }

    def _create_table_node(self, table_item: Any) -> Dict[str, Any]:
        """Create a Lexical table node from a TableItem.
        
        Args:
            table_item: The TableItem to convert
            
        Returns:
            Lexical table node
        """
        rows = []
        
        # Convert table grid to Lexical table rows
        if table_item.data and table_item.data.grid:
            for row in table_item.data.grid:
                lexical_row = {
                    "children": [],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "tablerow",
                    "version": 1
                }
                
                for cell in row:
                    lexical_cell = {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": cell.text,
                                "type": "text",
                                "version": 1
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "tablecell",
                        "version": 1
                    }
                    
                    # Add header state if it's a header cell
                    if cell.column_header:
                        lexical_cell["headerState"] = 1
                        
                    lexical_row["children"].append(lexical_cell)
                
                rows.append(lexical_row)
        
        # Create the table node
        num_rows = len(rows)
        num_cols = len(rows[0]["children"]) if rows else 0
        
        return {
            "children": rows,
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "type": "table",
            "version": 1,
            "rows": num_rows,
            "columns": num_cols
        }

    def _create_group_node(self, group_item: Any) -> Dict[str, Any]:
        """Create a Lexical list node from a GroupItem.
        
        Args:
            group_item: The GroupItem to convert
            
        Returns:
            Lexical list node
        """
        # Determine list type by examining the first item's content
        list_type = "unordered"  # default
        if group_item.children:
            first_ref = group_item.children[0]
            if first_ref.cref and "texts" in first_ref.cref:
                ref_parts = first_ref.cref.split("/")
                if len(ref_parts) >= 3 and ref_parts[1] == "texts":
                    text_index = int(ref_parts[2])
                    if text_index < len(self.doc.texts):
                        first_text = self.doc.texts[text_index].text
                        # Check if it starts with a number followed by period
                        if first_text and ". " in first_text and first_text.split(". ", 1)[0].strip().isdigit():
                            list_type = "ordered"
        
        tag = "ol" if list_type == "ordered" else "ul"
        
        list_items = []
        
        # Process child text items
        for child_ref in group_item.children:
            if not child_ref.cref:
                continue
                
            ref_parts = child_ref.cref.split("/")
            if len(ref_parts) >= 3 and ref_parts[1] == "texts":
                text_index = int(ref_parts[2])
                if text_index < len(self.doc.texts):
                    text_item = self.doc.texts[text_index]
                    
                    # Extract the actual content without list markers
                    text_content = text_item.text
                    # Remove bullet points or numbers if they exist
                    if text_content.startswith("● "):
                        text_content = text_content[2:]  # Remove bullet and space
                    elif text_content.startswith("• "):
                        text_content = text_content[2:]  # Remove bullet and space
                    elif ". " in text_content and text_content.split(". ", 1)[0].isdigit():
                        text_content = text_content.split(". ", 1)[1]  # Remove number and period
                    
                    list_item = {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": text_content,
                                "type": "text",
                                "version": 1
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "listitem",
                        "value": 1,
                        "version": 1
                    }
                    
                    list_items.append(list_item)
        
        return {
            "children": list_items,
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "listType": list_type,
            "start": 1,
            "tag": tag,
            "type": "list",
            "version": 1
        }