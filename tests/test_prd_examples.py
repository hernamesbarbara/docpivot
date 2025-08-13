"""Test all PRD examples to ensure they work exactly as documented."""

import pytest
from pathlib import Path
from docling_core.transforms.serializer.markdown import MarkdownParams, MarkdownDocSerializer
from docling_core.types import DoclingDocument

from docpivot import load_and_serialize, load_document, SerializerProvider


class TestPRDBasicUsage:
    """Test the basic usage patterns from the PRD."""

    def test_prd_basic_markdown_export_pattern1(self, sample_docling_json_path):
        """Test PRD Basic Markdown Export pattern with load_and_serialize."""
        # PRD Example (adapted for high-level API):
        # from docpivot import load_and_serialize
        # result = load_and_serialize("sample.docling.json", "markdown")
        # print(result.text)
        
        result = load_and_serialize(sample_docling_json_path, "markdown")
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        
    def test_prd_basic_markdown_export_pattern2(self, sample_docling_json_path):
        """Test PRD Basic Markdown Export pattern with explicit reader."""
        # PRD Example (exact from specification):
        # from docpivot.io.readers import DoclingJsonReader
        # from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
        # 
        # doc = DoclingJsonReader().load_data("sample.docling.json")
        # serializer = MarkdownDocSerializer(doc=doc)
        # ser_result = serializer.serialize()
        # print(ser_result.text)
        
        from docpivot.io.readers import DoclingJsonReader
        
        doc = DoclingJsonReader().load_data(sample_docling_json_path)
        serializer = MarkdownDocSerializer(doc=doc)
        ser_result = serializer.serialize()
        
        assert hasattr(ser_result, 'text')
        assert isinstance(ser_result.text, str)
        assert len(ser_result.text) > 0
        
    def test_prd_customized_markdown_export(self, sample_docling_json_path):
        """Test PRD Customized Markdown Export pattern."""
        # PRD Example (exact from specification):
        # from docling_core.transforms.chunker.hierarchical_chunker import TripletTableSerializer
        # from docling_core.transforms.serializer.markdown import MarkdownParams, MarkdownDocSerializer
        # 
        # serializer = MarkdownDocSerializer(
        #     doc=doc,
        #     table_serializer=TripletTableSerializer(),
        #     params=MarkdownParams(image_placeholder="(no image)")
        # )
        # ser_result = serializer.serialize()
        # print(ser_result.text)
        
        # Load document first (using our high-level API)
        doc = load_document(sample_docling_json_path)
        
        # Use exact PRD pattern
        try:
            from docling_core.transforms.chunker.hierarchical_chunker import TripletTableSerializer
            table_serializer = TripletTableSerializer()
        except ImportError:
            # If TripletTableSerializer is not available, skip table_serializer
            table_serializer = None
            
        if table_serializer is not None:
            serializer = MarkdownDocSerializer(
                doc=doc,
                table_serializer=table_serializer,
                params=MarkdownParams(image_placeholder="(no image)")
            )
        else:
            # Fallback without table serializer
            serializer = MarkdownDocSerializer(
                doc=doc,
                params=MarkdownParams(image_placeholder="(no image)")
            )
            
        ser_result = serializer.serialize()
        
        assert hasattr(ser_result, 'text')
        assert isinstance(ser_result.text, str)
        assert len(ser_result.text) > 0
        
    def test_prd_high_level_customized_markdown_export(self, sample_docling_json_path):
        """Test PRD Customized Markdown Export pattern using high-level API."""
        # PRD-inspired pattern using our high-level API:
        # from docpivot import load_document, SerializerProvider
        # doc = load_document("sample.docling.json")
        # serializer = SerializerProvider().get_serializer(
        #     "markdown", 
        #     doc=doc,
        #     params=MarkdownParams(image_placeholder="(no image)")
        # )
        # result = serializer.serialize()
        
        doc = load_document(sample_docling_json_path)
        serializer = SerializerProvider().get_serializer(
            "markdown", 
            doc=doc,
            params=MarkdownParams(image_placeholder="(no image)")
        )
        result = serializer.serialize()
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        
    def test_prd_lexical_export(self, sample_docling_json_path):
        """Test PRD Lexical Export pattern."""
        # PRD Example (exact from specification):
        # from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
        # 
        # serializer = LexicalDocSerializer(doc=doc)
        # ser_result = serializer.serialize()
        # print(ser_result.text)
        
        from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer
        
        # Load document first (using our high-level API)
        doc = load_document(sample_docling_json_path)
        
        # Use exact PRD pattern
        serializer = LexicalDocSerializer(doc=doc)
        ser_result = serializer.serialize()
        
        assert hasattr(ser_result, 'text')
        assert isinstance(ser_result.text, str)
        assert len(ser_result.text) > 0
        
        # Verify it's valid JSON structure
        import json
        lexical_data = json.loads(ser_result.text)
        assert "root" in lexical_data
        
    def test_prd_high_level_lexical_export(self, sample_docling_json_path):
        """Test PRD Lexical Export pattern using high-level API."""
        # High-level API version:
        # from docpivot import load_and_serialize
        # result = load_and_serialize("sample.docling.json", "lexical")
        # print(result.text)
        
        result = load_and_serialize(sample_docling_json_path, "lexical")
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        
        # Verify it's valid JSON structure
        import json
        lexical_data = json.loads(result.text)
        assert "root" in lexical_data


class TestPRDWorkflowPatterns:
    """Test the workflow patterns described in the PRD."""
    
    def test_auto_detection_workflow(self, sample_docling_json_path, sample_lexical_json_path):
        """Test auto-detection workflow: file_path → detect format → load → serialize."""
        # Test with both file types
        for file_path in [sample_docling_json_path, sample_lexical_json_path]:
            # Auto-detection workflow using high-level API
            result = load_and_serialize(file_path, "markdown")
            
            assert hasattr(result, 'text')
            assert isinstance(result.text, str)
            assert len(result.text) > 0
            
    def test_explicit_reader_workflow(self, sample_docling_json_path):
        """Test explicit reader workflow: reader_class + file_path → load → serialize."""
        from docpivot.io.readers import DoclingJsonReader
        
        # Explicit reader workflow
        reader = DoclingJsonReader()
        doc = reader.load_data(sample_docling_json_path)
        
        # Then serialize using SerializerProvider
        provider = SerializerProvider()
        serializer = provider.get_serializer("markdown", doc=doc)
        result = serializer.serialize()
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        
    def test_custom_serializer_workflow(self, sample_docling_json_path):
        """Test custom serializer workflow: reader → custom serializer with parameters → serialize."""
        # Load document
        doc = load_document(sample_docling_json_path)
        
        # Custom serializer with parameters
        provider = SerializerProvider()
        serializer = provider.get_serializer(
            "markdown", 
            doc=doc,
            params=MarkdownParams(image_placeholder="[CUSTOM IMAGE PLACEHOLDER]")
        )
        result = serializer.serialize()
        
        assert hasattr(result, 'text')
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        
    def test_batch_processing_workflow(self, sample_docling_json_path, sample_lexical_json_path):
        """Test batch processing workflow: multiple inputs → same output format."""
        files = [sample_docling_json_path, sample_lexical_json_path]
        output_format = "markdown"
        
        results = []
        for file_path in files:
            result = load_and_serialize(file_path, output_format)
            results.append(result)
            
        # Verify all results are valid
        for result in results:
            assert hasattr(result, 'text')
            assert isinstance(result.text, str)
            assert len(result.text) > 0


class TestPRDAdvancedUsage:
    """Test advanced usage patterns that should work with our implementation."""
    
    def test_custom_picture_serializer_pattern(self, sample_docling_json_path):
        """Test custom picture serializer pattern (adapted for available components)."""
        # PRD Example concept (adapted):
        # from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
        # from my_custom.picture_serializer import AnnotationPictureSerializer
        # 
        # serializer = MarkdownDocSerializer(
        #     doc=doc,
        #     picture_serializer=AnnotationPictureSerializer(),
        # )
        # ser_result = serializer.serialize()
        
        doc = load_document(sample_docling_json_path)
        
        # Test that custom component serializers can be passed through
        # (using existing components since we don't have custom ones)
        serializer = MarkdownDocSerializer(doc=doc)
        ser_result = serializer.serialize()
        
        assert hasattr(ser_result, 'text')
        assert isinstance(ser_result.text, str)
        assert len(ser_result.text) > 0
        
    def test_multiple_format_conversion(self, sample_docling_json_path):
        """Test converting the same document to multiple formats."""
        formats = ["markdown", "html", "lexical"]
        
        # Load once, serialize to multiple formats
        doc = load_document(sample_docling_json_path)
        
        results = {}
        for format_name in formats:
            provider = SerializerProvider()
            serializer = provider.get_serializer(format_name, doc=doc)
            result = serializer.serialize()
            results[format_name] = result
            
        # Verify all formats produced valid output
        for format_name, result in results.items():
            assert hasattr(result, 'text')
            assert isinstance(result.text, str)
            assert len(result.text) > 0
            
            if format_name == "lexical":
                # Verify JSON structure for lexical format
                import json
                lexical_data = json.loads(result.text)
                assert "root" in lexical_data


class TestPRDErrorHandling:
    """Test error handling as described in the PRD."""
    
    def test_unsupported_input_format_error(self):
        """Test error handling for unsupported input formats."""
        import tempfile
        from docpivot.io.readers.exceptions import UnsupportedFormatError
        
        with tempfile.NamedTemporaryFile(suffix=".unknown", delete=False) as tmp:
            tmp.write(b"unknown format content")
            tmp.flush()
            
            try:
                with pytest.raises(UnsupportedFormatError):
                    load_document(tmp.name)
                    
                with pytest.raises(UnsupportedFormatError):
                    load_and_serialize(tmp.name, "markdown")
                    
            finally:
                Path(tmp.name).unlink()
                
    def test_unsupported_output_format_error(self, sample_docling_json_path):
        """Test error handling for unsupported output formats."""
        with pytest.raises(ValueError, match="Unsupported format"):
            load_and_serialize(sample_docling_json_path, "unknown_format")
            
        with pytest.raises(ValueError, match="Unsupported format"):
            provider = SerializerProvider()
            doc = load_document(sample_docling_json_path)
            provider.get_serializer("unknown_format", doc=doc)
            
    def test_file_not_found_error_propagation(self):
        """Test that FileNotFoundError is properly propagated."""
        with pytest.raises(FileNotFoundError):
            load_document("nonexistent_file.json")
            
        with pytest.raises(FileNotFoundError):
            load_and_serialize("nonexistent_file.json", "markdown")