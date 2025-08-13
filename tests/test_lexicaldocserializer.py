"""Tests for LexicalDocSerializer class."""

import json
from docling_core.transforms.serializer.base import SerializationResult

from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
from docpivot.io.serializers.serializerprovider import SerializerProvider


class TestLexicalDocSerializer:
    """Test suite for LexicalDocSerializer class."""

    def test_can_be_instantiated(self) -> None:
        """Test that LexicalDocSerializer can be instantiated."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        assert isinstance(serializer, LexicalDocSerializer)
        assert serializer.doc == doc

    def test_serialize_returns_serialization_result(self) -> None:
        """Test that serialize returns a SerializationResult."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()

        assert isinstance(result, SerializationResult)
        assert hasattr(result, "text")
        assert isinstance(result.text, str)
        assert len(result.text) > 0

    def test_serialize_produces_valid_json(self) -> None:
        """Test that serialize produces valid JSON."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()

        # Should be valid JSON
        lexical_data = json.loads(result.text)
        assert isinstance(lexical_data, dict)
        assert "root" in lexical_data

    def test_lexical_json_structure(self) -> None:
        """Test that the output has correct Lexical JSON structure."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)

        # Check root structure
        assert "root" in lexical_data
        root = lexical_data["root"]

        assert root["type"] == "root"
        assert root["version"] == 1
        assert "children" in root
        assert isinstance(root["children"], list)
        assert root["direction"] == "ltr"

    def test_heading_transformation(self) -> None:
        """Test that headings are transformed correctly."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)

        # Find headings in the output
        headings = [
            child
            for child in lexical_data["root"]["children"]
            if child.get("type") == "heading"
        ]

        assert len(headings) > 0

        # Check first heading
        first_heading = headings[0]
        assert first_heading["type"] == "heading"
        assert first_heading["tag"] in ["h1", "h2", "h3", "h4", "h5", "h6"]
        assert first_heading["version"] == 1
        assert "children" in first_heading

        # Check heading text content
        text_child = first_heading["children"][0]
        assert text_child["type"] == "text"
        assert "text" in text_child
        assert isinstance(text_child["text"], str)

    def test_paragraph_transformation(self) -> None:
        """Test that paragraphs are transformed correctly."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)

        # Find paragraphs in the output
        paragraphs = [
            child
            for child in lexical_data["root"]["children"]
            if child.get("type") == "paragraph"
        ]

        assert len(paragraphs) > 0

        # Check first paragraph
        first_paragraph = paragraphs[0]
        assert first_paragraph["type"] == "paragraph"
        assert first_paragraph["version"] == 1
        assert "children" in first_paragraph

        # Check paragraph text content
        text_child = first_paragraph["children"][0]
        assert text_child["type"] == "text"
        assert "text" in text_child
        assert isinstance(text_child["text"], str)

    def test_list_transformation(self) -> None:
        """Test that lists are transformed correctly."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)

        # Find lists in the output
        lists = [
            child
            for child in lexical_data["root"]["children"]
            if child.get("type") == "list"
        ]

        assert len(lists) >= 2  # We expect at least 2 lists

        # Check list structure
        for list_node in lists:
            assert list_node["type"] == "list"
            assert list_node["listType"] in ["ordered", "unordered"]
            assert list_node["tag"] in ["ol", "ul"]
            assert list_node["version"] == 1
            assert "children" in list_node
            assert isinstance(list_node["children"], list)

            # Check list items
            for item in list_node["children"]:
                assert item["type"] == "listitem"
                assert "children" in item
                text_child = item["children"][0]
                assert text_child["type"] == "text"
                assert "text" in text_child

    def test_ordered_vs_unordered_lists(self) -> None:
        """Test that ordered and unordered lists are detected correctly."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)

        # Find lists in the output
        lists = [
            child
            for child in lexical_data["root"]["children"]
            if child.get("type") == "list"
        ]

        # Should have both ordered and unordered lists
        list_types = {list_node["listType"] for list_node in lists}
        assert "ordered" in list_types
        assert "unordered" in list_types

        # Check that tags match list types
        for list_node in lists:
            if list_node["listType"] == "ordered":
                assert list_node["tag"] == "ol"
            else:
                assert list_node["tag"] == "ul"

    def test_table_transformation(self) -> None:
        """Test that tables are transformed correctly."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)

        # Find tables in the output
        tables = [
            child
            for child in lexical_data["root"]["children"]
            if child.get("type") == "table"
        ]

        assert len(tables) >= 2  # We expect at least 2 tables

        # Check table structure
        for table_node in tables:
            assert table_node["type"] == "table"
            assert table_node["version"] == 1
            assert "rows" in table_node
            assert "columns" in table_node
            assert isinstance(table_node["rows"], int)
            assert isinstance(table_node["columns"], int)
            assert "children" in table_node

            # Check table rows
            for row in table_node["children"]:
                assert row["type"] == "tablerow"
                assert "children" in row

                # Check table cells
                for cell in row["children"]:
                    assert cell["type"] == "tablecell"
                    assert "children" in cell
                    text_child = cell["children"][0]
                    assert text_child["type"] == "text"
                    assert "text" in text_child

    def test_text_content_preservation(self) -> None:
        """Test that text content is preserved accurately."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)

        # Check that specific known text content is present
        all_text_content = []

        def extract_text_from_node(node):
            if isinstance(node, dict):
                if node.get("type") == "text" and "text" in node:
                    all_text_content.append(node["text"])
                if "children" in node and isinstance(node["children"], list):
                    for child in node["children"]:
                        extract_text_from_node(child)
            elif isinstance(node, list):
                for item in node:
                    extract_text_from_node(item)

        extract_text_from_node(lexical_data["root"]["children"])

        # Check for known content from the sample file
        all_text = " ".join(all_text_content)
        assert "This is the title" in all_text
        assert "Item Blue" in all_text  # From unordered list
        assert "This is item 1" in all_text  # From ordered list
        assert "Company" in all_text  # From table header

    def test_serializer_provider_integration(self) -> None:
        """Test integration with SerializerProvider."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        # Test that lexical format is supported
        assert SerializerProvider.is_format_supported("lexical")
        assert "lexical" in SerializerProvider.list_formats()

        # Test serializer creation via provider
        serializer = SerializerProvider.get_serializer("lexical", doc=doc)
        assert isinstance(serializer, LexicalDocSerializer)

        # Test serialization via provider
        result = serializer.serialize()
        assert isinstance(result, SerializationResult)

        # Validate JSON output
        lexical_data = json.loads(result.text)
        assert "root" in lexical_data

    def test_empty_document(self) -> None:
        """Test serialization of an empty-ish document."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        # Create a mock empty document structure
        doc.body.children = []  # Remove all body children

        serializer = LexicalDocSerializer(doc=doc)
        result = serializer.serialize()

        lexical_data = json.loads(result.text)
        assert "root" in lexical_data
        assert lexical_data["root"]["children"] == []

    def test_serializer_with_kwargs(self) -> None:
        """Test that serializer handles additional kwargs."""
        reader = DoclingJsonReader()
        doc = reader.load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

        # Should not raise exception with extra kwargs
        serializer = LexicalDocSerializer(doc=doc, extra_param="test")
        result = serializer.serialize()

        assert isinstance(result, SerializationResult)
        lexical_data = json.loads(result.text)
        assert "root" in lexical_data
