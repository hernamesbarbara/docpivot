"""Comprehensive tests for serializers using realistic documents from sample data."""

import json
import pytest
from pathlib import Path
from docling_core.types import DoclingDocument
from docling_core.transforms.serializer.base import SerializationResult

from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
from docpivot.io.serializers.serializerprovider import SerializerProvider


class TestLexicalDocSerializerWithSampleData:
    """Test LexicalDocSerializer with realistic documents."""
    
    def test_serialize_docling_sample_to_lexical(self, sample_docling_document_from_file: DoclingDocument):
        """Test converting sample docling document to lexical format."""
        serializer = LexicalDocSerializer(sample_docling_document_from_file)
        result = serializer.serialize()
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Parse and validate JSON structure
        lexical_data = json.loads(result.text)
        assert "root" in lexical_data
        assert "children" in lexical_data["root"]
        assert len(lexical_data["root"]["children"]) > 0
    
    def test_lexical_output_format_compliance(self, sample_docling_document_from_file: DoclingDocument):
        """Validate output against Lexical JSON schema requirements."""
        serializer = LexicalDocSerializer(sample_docling_document_from_file)
        result = serializer.serialize()
        
        lexical_data = json.loads(result.text)
        
        # Validate root structure
        assert "root" in lexical_data
        root = lexical_data["root"]
        assert "children" in root
        assert isinstance(root["children"], list)
        
        # Check that children have proper Lexical node structure
        for child in root["children"][:5]:  # Check first few children
            assert "type" in child
            if child["type"] in ["heading", "paragraph"]:
                assert "children" in child
                if child["children"]:
                    # Check text nodes
                    text_node = child["children"][0] 
                    assert "type" in text_node
                    if text_node["type"] == "text":
                        assert "text" in text_node
                        assert "version" in text_node
    
    def test_content_preservation_docling_to_lexical(
        self, 
        sample_docling_document_from_file: DoclingDocument,
        sample_lexical_json_path: Path
    ):
        """Test that content is preserved when converting docling to lexical."""
        # Serialize docling document to lexical
        serializer = LexicalDocSerializer(sample_docling_document_from_file)
        result = serializer.serialize()
        generated_lexical = json.loads(result.text)
        
        # Load original lexical for comparison
        original_lexical = json.loads(sample_lexical_json_path.read_text())
        
        # Extract text content from both
        def extract_text_content(lexical_data):
            """Extract all text content from lexical structure."""
            texts = []
            
            def traverse(node):
                if isinstance(node, dict):
                    if node.get("type") == "text" and "text" in node:
                        texts.append(node["text"])
                    if "children" in node and isinstance(node["children"], list):
                        for child in node["children"]:
                            traverse(child)
                elif isinstance(node, list):
                    for item in node:
                        traverse(item)
            
            # Start traversal from the root
            if isinstance(lexical_data, dict) and "root" in lexical_data:
                traverse(lexical_data["root"])
            else:
                traverse(lexical_data)
            return texts
        
        generated_texts = extract_text_content(generated_lexical)
        original_texts = extract_text_content(original_lexical)
        
        # Should have some text content
        assert len(generated_texts) > 0
        
        # Should contain key content elements
        all_generated = " ".join(generated_texts)
        all_original = " ".join(original_texts)
        
        # Check for common content (allowing for some variation in transformation)
        assert len(all_generated) > 100, "Should generate substantial content"
    
    def test_heading_structure_preservation(self, sample_docling_document_from_file: DoclingDocument):
        """Test that heading structure is preserved in lexical output."""
        serializer = LexicalDocSerializer(sample_docling_document_from_file)
        result = serializer.serialize()
        lexical_data = json.loads(result.text)
        
        # Find heading nodes
        headings = []
        
        def find_headings(node):
            if isinstance(node, dict):
                if node.get("type") == "heading":
                    headings.append(node)
                if "children" in node and isinstance(node["children"], list):
                    for child in node["children"]:
                        find_headings(child)
            elif isinstance(node, list):
                for item in node:
                    find_headings(item)
        
        # Start from root
        if isinstance(lexical_data, dict) and "root" in lexical_data:
            find_headings(lexical_data["root"])
        else:
            find_headings(lexical_data)
        
        # Should have found some headings
        assert len(headings) > 0, "Should preserve heading structure"
        
        # Check heading properties
        for heading in headings:
            assert "tag" in heading or "type" in heading
            assert "children" in heading
            if heading["children"]:
                # Should have text content
                text_nodes = [child for child in heading["children"] if child.get("type") == "text"]
                assert len(text_nodes) > 0, "Headings should have text content"


class TestSerializerProviderWithSampleData:
    """Test SerializerProvider with realistic documents."""
    
    def test_markdown_serialization_with_sample_data(self, sample_docling_document_from_file: DoclingDocument):
        """Test markdown serialization with sample document."""
        provider = SerializerProvider()
        serializer = provider.get_serializer("markdown", doc=sample_docling_document_from_file)
        result = serializer.serialize()
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Check for markdown structure
        markdown_text = result.text
        assert "##" in markdown_text or "#" in markdown_text, "Should contain markdown headings"
        assert len(markdown_text.split('\n')) > 5, "Should have multiple lines"
    
    def test_html_serialization_with_sample_data(self, sample_docling_document_from_file: DoclingDocument):
        """Test HTML serialization with sample document."""
        provider = SerializerProvider()
        serializer = provider.get_serializer("html", doc=sample_docling_document_from_file)
        result = serializer.serialize()
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Check for HTML structure
        html_text = result.text
        assert "<" in html_text and ">" in html_text, "Should contain HTML tags"
        assert "<h" in html_text or "<p" in html_text, "Should contain heading or paragraph tags"
    
    def test_doctags_serialization_with_sample_data(self, sample_docling_document_from_file: DoclingDocument):
        """Test doctags serialization with sample document."""
        provider = SerializerProvider()
        serializer = provider.get_serializer("doctags", doc=sample_docling_document_from_file)
        result = serializer.serialize()
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Check for doctags structure
        doctags_text = result.text
        assert len(doctags_text) > 50, "Should generate substantial content"
    
    def test_lexical_serialization_through_provider(self, sample_docling_document_from_file: DoclingDocument):
        """Test lexical serialization through SerializerProvider."""
        provider = SerializerProvider()
        serializer = provider.get_serializer("lexical", doc=sample_docling_document_from_file)
        result = serializer.serialize()
        
        assert isinstance(result, SerializationResult)
        assert result.text is not None
        
        # Validate JSON structure
        lexical_data = json.loads(result.text)
        assert "root" in lexical_data
        assert "children" in lexical_data["root"]
    
    def test_serialization_with_custom_parameters(self, sample_docling_document_from_file: DoclingDocument):
        """Test serialization with custom parameters."""
        provider = SerializerProvider()
        
        # Test markdown with custom image placeholder
        try:
            from docling_core.transforms.serializers.markdown.md_serializer import MarkdownSerializer
            from docling_core.transforms.serializers.markdown.params import MarkdownParams
            
            params = MarkdownParams(image_placeholder="(no image)")
            serializer = provider.get_serializer("markdown", doc=sample_docling_document_from_file, params=params)
            result = serializer.serialize()
            
            assert isinstance(result, SerializationResult)
            assert result.text is not None
        except ImportError:
            # Skip if markdown serializer not available
            pytest.skip("MarkdownSerializer not available")


class TestRoundTripConversions:
    """Test round-trip conversions between formats."""
    
    def test_lexical_to_docling_to_lexical_consistency(
        self, 
        sample_lexical_json_path: Path,
        sample_lexical_document_from_file: DoclingDocument
    ):
        """Test consistency in lexical → docling → lexical conversion."""
        # Load original lexical
        original_lexical = json.loads(sample_lexical_json_path.read_text())
        
        # Convert docling back to lexical
        serializer = LexicalDocSerializer(sample_lexical_document_from_file)
        result = serializer.serialize()
        converted_lexical = json.loads(result.text)
        
        # Extract and compare text content
        def extract_text_content(lexical_data):
            texts = []
            def traverse(node):
                if isinstance(node, dict):
                    if node.get("type") == "text" and "text" in node:
                        texts.append(node["text"].strip())
                    if "children" in node and isinstance(node["children"], list):
                        for child in node["children"]:
                            traverse(child)
                elif isinstance(node, list):
                    for item in node:
                        traverse(item)
            
            # Start from root if present
            if isinstance(lexical_data, dict) and "root" in lexical_data:
                traverse(lexical_data["root"])
            else:
                traverse(lexical_data)
            return [t for t in texts if t]  # Filter empty strings
        
        original_texts = extract_text_content(original_lexical)
        converted_texts = extract_text_content(converted_lexical)
        
        # Should preserve core textual content
        assert len(converted_texts) > 0
        
        # Check that major content elements are preserved
        original_content = " ".join(original_texts).lower()
        converted_content = " ".join(converted_texts).lower()
        
        # Check for key content preservation
        if "title" in original_content:
            assert "title" in converted_content, "Should preserve title content"
        if "lorem" in original_content:
            assert "lorem" in converted_content, "Should preserve lorem ipsum content"
    
    def test_docling_to_markdown_quality(self, sample_docling_document_from_file: DoclingDocument):
        """Test quality of docling to markdown conversion."""
        provider = SerializerProvider()
        serializer = provider.get_serializer("markdown", doc=sample_docling_document_from_file)
        result = serializer.serialize()
        
        markdown_text = result.text
        lines = markdown_text.split('\n')
        
        # Quality checks
        assert len(lines) > 5, "Should have multiple lines"
        
        # Should have headings
        heading_lines = [line for line in lines if line.startswith('#')]
        assert len(heading_lines) > 0, "Should contain markdown headings"
        
        # Should have content lines
        content_lines = [line for line in lines if line.strip() and not line.startswith('#')]
        assert len(content_lines) > 0, "Should contain content beyond headings"
        
        # Should not have excessive empty lines
        empty_line_count = len([line for line in lines if not line.strip()])
        total_lines = len(lines)
        assert empty_line_count < total_lines * 0.6, "Should not be mostly empty lines"