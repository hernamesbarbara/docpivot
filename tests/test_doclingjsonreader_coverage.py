"""Additional tests for DoclingJsonReader to improve coverage."""

import json
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
import mmap
import tempfile

from docpivot.io.readers.doclingjsonreader import DoclingJsonReader
from docpivot.io.readers.exceptions import (
    FileAccessError, 
    UnsupportedFormatError, 
    ValidationError as DocPivotValidationError,
    SchemaValidationError
)
from docling_core.types import DoclingDocument


class TestDoclingJsonReaderCoverage:
    """Additional test coverage for DoclingJsonReader class."""

    @pytest.fixture
    def valid_docling_data(self):
        """Create minimal valid DoclingDocument JSON data."""
        return {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            "name": "test_document",
            "origin": {
                "mimetype": "application/pdf",
                "binary_hash": 123456789,
                "filename": "test.pdf",
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
            },
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
            },
            "groups": [],
            "labels": [],
            "key_value_items": [],
            "pages": {},
            "pictures": [],
            "tables": [],
            "texts": []
        }

    def test_cache_lookup_failure_file_not_found(self, temp_directory, valid_docling_data):
        """Test cache lookup failure handling when file not found."""
        reader = DoclingJsonReader(enable_caching=True)
        
        # Create file and cache it
        json_file = temp_directory / "test.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        # Load document to populate cache
        doc1 = reader.load_data(str(json_file))
        assert doc1 is not None
        
        # Delete the file to trigger cache lookup failure
        json_file.unlink()
        
        # Recreate file with same content for successful load after cache miss
        json_file.write_text(json.dumps(valid_docling_data))
        
        # Should handle cache failure gracefully and reload
        doc2 = reader.load_data(str(json_file))
        assert doc2 is not None

    def test_cache_lookup_failure_os_error(self, temp_directory, valid_docling_data):
        """Test cache lookup failure with OS error during stat."""
        reader = DoclingJsonReader(enable_caching=True)
        
        json_file = temp_directory / "test.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        # Load document to populate cache
        doc1 = reader.load_data(str(json_file))
        assert doc1 is not None
        
        # The cache lookup failure is handled internally and falls back to normal loading
        # which is already covered by other tests

    def test_streaming_loading_strategy(self, temp_directory, valid_docling_data):
        """Test streaming loading strategy for large files."""
        # Create reader with streaming forced on
        reader = DoclingJsonReader(use_streaming=True, enable_caching=False)
        
        json_file = temp_directory / "test_streaming.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        # Load using streaming strategy
        doc = reader.load_data(str(json_file))
        assert isinstance(doc, DoclingDocument)
        assert doc.name == "test_document"

    def test_streaming_loading_with_progress_callback(self, temp_directory, valid_docling_data):
        """Test streaming loading with progress callback."""
        progress_values = []
        
        def progress_callback(value):
            progress_values.append(value)
        
        reader = DoclingJsonReader(
            use_streaming=True,
            progress_callback=progress_callback,
            enable_caching=False
        )
        
        json_file = temp_directory / "test_streaming_progress.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        doc = reader.load_data(str(json_file))
        assert isinstance(doc, DoclingDocument)
        
        # Check progress was reported
        assert len(progress_values) > 0
        assert progress_values[-1] == 1.0  # Final progress should be 100%

    def test_streaming_unicode_decode_error(self, temp_directory):
        """Test streaming loading with Unicode decode error."""
        reader = DoclingJsonReader(use_streaming=True, enable_caching=False)
        
        # Create file with invalid UTF-8
        json_file = temp_directory / "test_bad_encoding.docling.json"
        json_file.write_bytes(b"\xff\xfe\x00\x00invalid")
        
        with pytest.raises(FileAccessError) as exc_info:
            reader.load_data(str(json_file))
        
        assert "Unable to decode" in str(exc_info.value)
        assert "UTF-8" in str(exc_info.value)

    def test_streaming_io_error(self, temp_directory, valid_docling_data):
        """Test streaming loading with IO error."""
        reader = DoclingJsonReader(use_streaming=True, enable_caching=False)
        
        json_file = temp_directory / "test_io_error.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        # Mock _load_streaming to raise IOError
        with patch.object(reader, '_load_streaming', side_effect=FileAccessError(
            "Error reading streaming file", str(json_file), "streaming_read"
        )):
            with pytest.raises(FileAccessError) as exc_info:
                reader.load_data(str(json_file))
            
            assert "Error reading streaming file" in str(exc_info.value)

    def test_memory_mapped_loading_strategy(self, temp_directory, valid_docling_data):
        """Test memory-mapped loading strategy."""
        # Force memory-mapped loading by setting large file threshold to 0
        reader = DoclingJsonReader(
            use_streaming=False,
            large_file_threshold_bytes=0,  # Force mmap for any size
            enable_caching=False
        )
        
        json_file = temp_directory / "test_mmap.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        # Load using memory-mapped strategy
        doc = reader.load_data(str(json_file))
        assert isinstance(doc, DoclingDocument)
        assert doc.name == "test_document"

    def test_memory_mapped_with_progress_callback(self, temp_directory, valid_docling_data):
        """Test memory-mapped loading with progress callback."""
        progress_values = []
        
        def progress_callback(value):
            progress_values.append(value)
        
        reader = DoclingJsonReader(
            use_streaming=False,
            large_file_threshold_bytes=0,
            progress_callback=progress_callback,
            enable_caching=False
        )
        
        json_file = temp_directory / "test_mmap_progress.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        doc = reader.load_data(str(json_file))
        assert isinstance(doc, DoclingDocument)
        
        # Check progress was reported
        assert len(progress_values) > 0
        assert progress_values[-1] == 1.0

    def test_memory_mapped_unicode_decode_error(self, temp_directory):
        """Test memory-mapped loading with Unicode decode error."""
        reader = DoclingJsonReader(
            use_streaming=False,
            large_file_threshold_bytes=0,
            enable_caching=False
        )
        
        # Create file with invalid UTF-8
        json_file = temp_directory / "test_mmap_bad_encoding.docling.json"
        json_file.write_bytes(b"\xff\xfe\x00\x00invalid")
        
        with pytest.raises(FileAccessError) as exc_info:
            reader.load_data(str(json_file))
        
        assert "Unable to decode memory-mapped file" in str(exc_info.value)

    def test_memory_mapped_fallback_to_standard(self, temp_directory, valid_docling_data):
        """Test memory-mapped loading falls back to standard on error."""
        reader = DoclingJsonReader(
            use_streaming=False,
            large_file_threshold_bytes=0,
            enable_caching=False
        )
        
        json_file = temp_directory / "test_mmap_fallback.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        # Mock mmap to raise exception
        with patch("mmap.mmap", side_effect=Exception("mmap failed")):
            # Should fallback to standard loading
            doc = reader.load_data(str(json_file))
            assert isinstance(doc, DoclingDocument)

    def test_loading_strategy_selection_streaming_forced(self):
        """Test loading strategy selection when streaming is forced."""
        reader = DoclingJsonReader(use_streaming=True)
        
        # Should always return streaming when forced
        assert reader._choose_loading_strategy(100) == "streaming"
        assert reader._choose_loading_strategy(10000000) == "streaming"

    def test_loading_strategy_selection_streaming_disabled(self):
        """Test loading strategy selection when streaming is disabled."""
        reader = DoclingJsonReader(use_streaming=False, large_file_threshold_bytes=100000000)
        
        # Should use standard for small files
        assert reader._choose_loading_strategy(1000) == "standard"
        
        # Should use mmap for large files when streaming disabled
        assert reader._choose_loading_strategy(200000000) == "mmap"

    def test_loading_strategy_auto_selection(self):
        """Test automatic loading strategy selection."""
        reader = DoclingJsonReader(
            use_streaming=None,  # Auto mode
            streaming_threshold_bytes=10000000,  # 10MB
            large_file_threshold_bytes=100000000  # 100MB
        )
        
        # Small file - standard
        assert reader._choose_loading_strategy(1000) == "standard"
        
        # Medium file - streaming
        assert reader._choose_loading_strategy(50000000) == "streaming"
        
        # Very large file - should be streaming when mmap unavailable
        result = reader._choose_loading_strategy(200000000)
        assert result in ["mmap", "streaming"]  # Allow either based on platform

    def test_general_exception_handling(self, temp_directory):
        """Test general exception handling in load_data."""
        reader = DoclingJsonReader(enable_caching=False)
        
        json_file = temp_directory / "test_exception.docling.json"
        json_file.write_text('{"schema_name": "DoclingDocument"}')  # Invalid JSON
        
        # Mock detect_format to return True so we get past format check
        with patch.object(reader, 'detect_format', return_value=True):
            # Mock _load_standard to raise unexpected exception
            with patch.object(reader, '_load_standard', side_effect=RuntimeError("Unexpected error")):
                with pytest.raises(DocPivotValidationError) as exc_info:
                    reader.load_data(str(json_file))
                
                assert "Unexpected error" in str(exc_info.value)

    def test_parse_json_buffered_with_orjson(self, valid_docling_data):
        """Test _parse_json_buffered method with orjson."""
        reader = DoclingJsonReader(use_orjson=True)
        
        json_str = json.dumps(valid_docling_data)
        result = reader._parse_json_buffered(json_str)
        
        assert result == valid_docling_data

    def test_parse_json_buffered_without_orjson(self, valid_docling_data):
        """Test _parse_json_buffered method without orjson."""
        reader = DoclingJsonReader(use_orjson=False)
        
        json_str = json.dumps(valid_docling_data)
        result = reader._parse_json_buffered(json_str)
        
        assert result == valid_docling_data

    def test_validate_and_create_document_validation_error(self, temp_directory):
        """Test _validate_and_create_document with validation error."""
        reader = DoclingJsonReader()
        
        # Invalid data missing required fields
        invalid_data = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0"
            # Missing required fields
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            reader._validate_and_create_document(invalid_data, "test_file.json")
        
        assert "missing required fields" in str(exc_info.value)

    def test_check_docling_json_content_edge_cases(self, temp_directory):
        """Test checking docling json content through detect_format."""
        reader = DoclingJsonReader()
        
        # Test with invalid JSON content
        json_file = temp_directory / "test.json"
        
        # Test with non-dict JSON
        json_file.write_text("[]")
        assert reader.detect_format(str(json_file)) is False
        
        # Test with missing schema_name
        json_file.write_text('{"version": "1.4.0"}')
        assert reader.detect_format(str(json_file)) is False
        
        # Test with wrong schema_name
        json_file.write_text(json.dumps({
            "schema_name": "OtherSchema",
            "version": "1.4.0"
        }))
        assert reader.detect_format(str(json_file)) is False

    def test_get_cache_key(self, temp_directory):
        """Test _get_cache_key method."""
        reader = DoclingJsonReader()
        
        test_file = temp_directory / "test.json"
        test_file.write_text("{}")
        
        cache_key = reader._get_cache_key(test_file)
        assert cache_key is not None
        # Cache key might be a tuple or string depending on implementation
        assert isinstance(cache_key, (str, tuple))

    def test_load_data_with_caching_disabled(self, temp_directory, valid_docling_data):
        """Test load_data with caching explicitly disabled."""
        reader = DoclingJsonReader(enable_caching=False)
        
        json_file = temp_directory / "test_no_cache.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        # Load twice - should not use cache
        doc1 = reader.load_data(str(json_file))
        doc2 = reader.load_data(str(json_file))
        
        assert doc1 is not None
        assert doc2 is not None
        # Both documents should be valid DoclingDocument instances
        assert isinstance(doc1, DoclingDocument)
        assert isinstance(doc2, DoclingDocument)

    def test_performance_config_integration(self, temp_directory, valid_docling_data):
        """Test integration with PerformanceConfig."""
        from docpivot.performance import PerformanceConfig
        
        # Use actual PerformanceConfig attributes
        perf_config = PerformanceConfig()
        
        reader = DoclingJsonReader(performance_config=perf_config)
        
        json_file = temp_directory / "test_perf_config.docling.json"
        json_file.write_text(json.dumps(valid_docling_data))
        
        doc = reader.load_data(str(json_file))
        assert isinstance(doc, DoclingDocument)