"""Comprehensive tests for OptimizedDoclingJsonReader."""

import unittest
import json
import tempfile
import mmap
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import time
import io

from docling_core.types import DoclingDocument
from pydantic import ValidationError

from docpivot.io.readers.optimized_docling_reader import OptimizedDoclingJsonReader
from docpivot.io.readers.doclingjsonreader import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_STREAMING_THRESHOLD_BYTES as STREAMING_THRESHOLD_BYTES,
    DEFAULT_LARGE_FILE_THRESHOLD_BYTES as LARGE_FILE_THRESHOLD_BYTES,
)
from docpivot.io.readers.exceptions import (
    ValidationError as DocPivotValidationError,
    SchemaValidationError,
    FileAccessError,
    UnsupportedFormatError,
)
from docpivot.performance import PerformanceConfig


class TestOptimizedDoclingJsonReader(unittest.TestCase):
    """Test OptimizedDoclingJsonReader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = OptimizedDoclingJsonReader()
        
        # Valid docling document data with all required fields
        self.valid_docling_data = {
            "schema_name": "DoclingDocument",
            "version": "1.0.0",
            "name": "test.pdf",
            "origin": {
                "mimetype": "application/pdf",
                "binary_hash": 123456,
                "filename": "test.pdf"
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": []
            },
            "body": {
                "self_ref": "#/body",
                "children": []
            },
            "groups": [],
            "key_value_items": [],
            "pages": {},
            "pictures": [],
            "tables": [],
            "texts": []
        }
        
    def test_initialization_default(self):
        """Test reader initialization with default parameters."""
        reader = OptimizedDoclingJsonReader()
        self.assertIsNotNone(reader.performance_config)
        self.assertIsNone(reader.use_streaming)
        self.assertTrue(reader.use_fast_json)
        self.assertFalse(reader.enable_caching)
        self.assertIsNone(reader.progress_callback)
        self.assertEqual(len(reader._document_cache), 0)
        
    def test_initialization_with_config(self):
        """Test reader initialization with custom config."""
        perf_config = PerformanceConfig()
        progress_cb = Mock()
        
        reader = OptimizedDoclingJsonReader(
            performance_config=perf_config,
            use_streaming=True,
            use_fast_json=False,
            enable_caching=True,
            progress_callback=progress_cb
        )
        
        self.assertEqual(reader.performance_config, perf_config)
        self.assertTrue(reader.use_streaming)
        self.assertFalse(reader.use_fast_json)
        self.assertTrue(reader.enable_caching)
        self.assertEqual(reader.progress_callback, progress_cb)
        
    def test_supported_extensions(self):
        """Test supported file extensions."""
        self.assertIn(".docling.json", OptimizedDoclingJsonReader.SUPPORTED_EXTENSIONS)
        self.assertIn(".json", OptimizedDoclingJsonReader.SUPPORTED_EXTENSIONS)
        
    def test_detect_format_valid_docling_json(self):
        """Test format detection for valid .docling.json file."""
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = tmp.name
            
        try:
            result = self.reader.detect_format(tmp_path)
            self.assertTrue(result)
        finally:
            Path(tmp_path).unlink()
            
    def test_detect_format_invalid_extension(self):
        """Test format detection for invalid extension."""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as tmp:
            tmp.write("test")
            tmp_path = tmp.name
            
        try:
            result = self.reader.detect_format(tmp_path)
            self.assertFalse(result)
        finally:
            Path(tmp_path).unlink()
            
    def test_detect_format_nonexistent_file(self):
        """Test format detection for nonexistent file."""
        result = self.reader.detect_format("/nonexistent/file.docling.json")
        self.assertFalse(result)
        
    def test_load_data_standard_mode(self):
        """Test loading data in standard mode (small file)."""
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = tmp.name
            
        try:
            doc = self.reader.load_data(tmp_path)
            self.assertIsInstance(doc, DoclingDocument)
            self.assertEqual(doc.name, "test.pdf")
        finally:
            Path(tmp_path).unlink()
            
    def test_load_data_with_caching(self):
        """Test loading data with caching enabled."""
        reader = OptimizedDoclingJsonReader(enable_caching=True)
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = tmp.name
            
        try:
            # First load
            doc1 = reader.load_data(tmp_path)
            # Check if any cache key contains the tmp_path
            cache_keys = [key[0] if isinstance(key, tuple) else key for key in reader._document_cache.keys()]
            self.assertIn(tmp_path, cache_keys)
            
            # Second load should use cache
            doc2 = reader.load_data(tmp_path)
            self.assertIs(doc1, doc2)
        finally:
            Path(tmp_path).unlink()
            
    def test_load_data_with_progress_callback(self):
        """Test loading with progress callback."""
        progress_values = []
        
        def progress_callback(value):
            progress_values.append(value)
            
        reader = OptimizedDoclingJsonReader(progress_callback=progress_callback)
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = tmp.name
            
        try:
            reader.load_data(tmp_path)
            # Should have progress updates
            self.assertTrue(len(progress_values) > 0)
            # Final progress should be 1.0
            self.assertEqual(progress_values[-1], 1.0)
        finally:
            Path(tmp_path).unlink()
            
    def test_load_data_file_not_found(self):
        """Test loading nonexistent file."""
        with self.assertRaises(FileAccessError) as ctx:
            self.reader.load_data("/nonexistent/file.docling.json")
        self.assertIn("File not found", str(ctx.exception))
        
    def test_load_data_is_directory(self):
        """Test loading a directory instead of file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileAccessError) as ctx:
                self.reader.load_data(tmpdir)
            self.assertIn("Path is a directory", str(ctx.exception))
            
    def test_load_data_file_access_error(self):
        """Test handling file access errors."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_dir', return_value=False):
                with patch('pathlib.Path.stat', side_effect=PermissionError("Permission denied")):
                    with self.assertRaises(DocPivotValidationError) as ctx:
                        self.reader.load_data("/some/file.docling.json")
                    self.assertIn("Unexpected error loading DoclingDocument", str(ctx.exception))
                    
    def test_load_data_unsupported_format(self):
        """Test loading unsupported format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as tmp:
            tmp.write("test")
            tmp_path = tmp.name
            
        try:
            with self.assertRaises(UnsupportedFormatError):
                self.reader.load_data(tmp_path)
        finally:
            Path(tmp_path).unlink()
            
    def test_load_data_invalid_json(self):
        """Test loading invalid JSON."""
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            tmp.write("invalid json{")
            tmp_path = tmp.name
            
        try:
            with self.assertRaises(DocPivotValidationError) as ctx:
                self.reader.load_data(tmp_path)
            self.assertIn("Invalid JSON format", str(ctx.exception))
        finally:
            Path(tmp_path).unlink()
            
    def test_load_data_missing_schema_fields(self):
        """Test loading JSON missing required schema fields."""
        invalid_data = {"name": "test.pdf"}  # Missing schema_name and version
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(invalid_data, tmp)
            tmp_path = tmp.name
            
        try:
            with self.assertRaises(SchemaValidationError) as ctx:
                self.reader.load_data(tmp_path)
            self.assertIn("missing required fields", str(ctx.exception))
        finally:
            Path(tmp_path).unlink()
            
    def test_load_data_wrong_schema_name(self):
        """Test loading JSON with wrong schema name."""
        invalid_data = {
            "schema_name": "WrongSchema",
            "version": "1.0.0",
            "name": "test.pdf"
        }
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(invalid_data, tmp)
            tmp_path = tmp.name
            
        try:
            with self.assertRaises(SchemaValidationError) as ctx:
                self.reader.load_data(tmp_path)
            self.assertIn("missing required fields", str(ctx.exception))
        finally:
            Path(tmp_path).unlink()
            
    @patch('docpivot.io.readers.optimized_docling_reader.STREAMING_THRESHOLD_BYTES', 100)
    def test_load_streaming_mode(self):
        """Test loading in streaming mode for large files."""
        # Create a large enough data to trigger streaming
        large_data = self.valid_docling_data.copy()
        large_data["large_field"] = "x" * 200  # Make it larger than threshold
        
        reader = OptimizedDoclingJsonReader(use_streaming=None)
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(large_data, tmp)
            tmp_path = tmp.name
            
        try:
            # Test that streaming mode works for large files
            doc = reader.load_data(tmp_path)
            self.assertIsInstance(doc, DoclingDocument)
            self.assertEqual(doc.name, "test.pdf")
        finally:
            Path(tmp_path).unlink()
            
    def test_force_streaming_mode(self):
        """Test forcing streaming mode."""
        reader = OptimizedDoclingJsonReader(use_streaming=True)
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = tmp.name
            
        try:
            with patch.object(reader, '_load_streaming', return_value=DoclingDocument(name="test")) as mock_streaming:
                doc = reader.load_data(tmp_path)
                mock_streaming.assert_called_once()
        finally:
            Path(tmp_path).unlink()
            
    @patch('docpivot.io.readers.optimized_docling_reader.LARGE_FILE_THRESHOLD_BYTES', 100)
    def test_load_memory_mapped_mode(self):
        """Test loading in memory-mapped mode for very large files."""
        # Create a very large data
        large_data = self.valid_docling_data.copy()
        large_data["large_field"] = "x" * 200
        
        reader = OptimizedDoclingJsonReader(use_streaming=False)
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(large_data, tmp)
            tmp_path = tmp.name
            
        try:
            # Test that memory mapped mode works for large files
            doc = reader.load_data(tmp_path)
            self.assertIsInstance(doc, DoclingDocument)
            self.assertEqual(doc.name, "test.pdf")
        finally:
            Path(tmp_path).unlink()
            
    def test_json_parser_selection_orjson(self):
        """Test JSON parser selection with orjson available."""
        with patch.dict('sys.modules', {'orjson': MagicMock()}):
            reader = OptimizedDoclingJsonReader(use_fast_json=True)
            # Should select orjson
            self.assertIsNotNone(reader._json_parser)
            
    def test_json_parser_selection_ujson(self):
        """Test JSON parser selection with ujson available."""
        mock_ujson = MagicMock()
        mock_ujson.__name__ = "ujson"
        
        with patch.dict('sys.modules', {'orjson': None}):
            with patch.dict('sys.modules', {'ujson': mock_ujson}):
                reader = OptimizedDoclingJsonReader(use_fast_json=True)
                # Should select ujson  
                self.assertIsNotNone(reader._json_parser)
                self.assertEqual(reader._json_parser.__name__, "ujson")
                
    def test_json_parser_selection_standard(self):
        """Test JSON parser selection fallback to standard."""
        reader = OptimizedDoclingJsonReader(use_fast_json=False)
        # Should use standard json
        import json as std_json
        self.assertEqual(reader._json_parser, std_json)
        
    def test_load_standard_with_progress(self):
        """Test _load_standard method with progress callback."""
        progress_values = []
        reader = OptimizedDoclingJsonReader(progress_callback=lambda x: progress_values.append(x))
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = Path(tmp.name)
            
        try:
            doc = reader._load_standard(tmp_path, tmp_path.stat().st_size)
            self.assertIsInstance(doc, DoclingDocument)
            # Check progress was called
            self.assertIn(0.1, progress_values)
            self.assertIn(1.0, progress_values)
        finally:
            tmp_path.unlink()
            
    def test_load_standard_error_handling(self):
        """Test _load_standard error handling."""
        reader = OptimizedDoclingJsonReader()
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            tmp.write("invalid json")
            tmp_path = Path(tmp.name)
            
        try:
            with self.assertRaises(DocPivotValidationError) as ctx:
                reader._load_standard(tmp_path, tmp_path.stat().st_size)
            self.assertIn("Invalid JSON format", str(ctx.exception))
        finally:
            tmp_path.unlink()
            
    def test_load_memory_mapped_success(self):
        """Test successful memory-mapped loading."""
        reader = OptimizedDoclingJsonReader()
        
        # Create a file large enough to memory map
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = Path(tmp.name)
            
        try:
            doc = reader._load_memory_mapped(tmp_path, tmp_path.stat().st_size)
            self.assertIsInstance(doc, DoclingDocument)
        finally:
            tmp_path.unlink()
            
    def test_load_memory_mapped_fallback(self):
        """Test memory-mapped loading fallback to standard."""
        reader = OptimizedDoclingJsonReader()
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = Path(tmp.name)
            
        try:
            # Mock mmap to fail
            with patch('mmap.mmap', side_effect=Exception("mmap failed")):
                with patch.object(reader, '_load_standard', return_value=DoclingDocument(name="test")) as mock_standard:
                    doc = reader._load_memory_mapped(tmp_path, tmp_path.stat().st_size)
                    mock_standard.assert_called_once()
                    self.assertIsInstance(doc, DoclingDocument)
        finally:
            tmp_path.unlink()
            
    def test_load_streaming_success(self):
        """Test successful streaming load."""
        reader = OptimizedDoclingJsonReader()
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = Path(tmp.name)
            
        try:
            doc = reader._load_streaming(tmp_path, tmp_path.stat().st_size)
            self.assertIsInstance(doc, DoclingDocument)
        finally:
            tmp_path.unlink()
            
    def test_load_streaming_error(self):
        """Test streaming load error handling - falls back to standard load."""
        reader = OptimizedDoclingJsonReader()
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            tmp.write("invalid json")
            tmp_path = Path(tmp.name)
            
        try:
            # Since streaming falls back to standard on error, check for standard error
            with self.assertRaises(DocPivotValidationError) as ctx:
                reader._load_streaming(tmp_path, tmp_path.stat().st_size)
            self.assertIn("Invalid JSON format", str(ctx.exception))
        finally:
            tmp_path.unlink()
            
    def test_parse_json_with_orjson(self):
        """Test JSON parsing with orjson."""
        mock_orjson = MagicMock()
        mock_orjson.loads.return_value = {"test": "data"}
        
        reader = OptimizedDoclingJsonReader(use_fast_json=True)
        reader._json_parser = mock_orjson
        
        result = reader._parse_json('{"test": "data"}')
        mock_orjson.loads.assert_called_once()
        self.assertEqual(result, {"test": "data"})
        
    def test_parse_json_standard(self):
        """Test JSON parsing with standard json."""
        reader = OptimizedDoclingJsonReader(use_fast_json=False)
        
        result = reader._parse_json('{"test": "data"}')
        self.assertEqual(result, {"test": "data"})
        
    def test_validate_and_create_document_success(self):
        """Test successful document validation and creation."""
        reader = OptimizedDoclingJsonReader()
        
        doc = reader._validate_and_create_document(self.valid_docling_data, "test.json")
        self.assertIsInstance(doc, DoclingDocument)
        self.assertEqual(doc.name, "test.pdf")
        
    def test_validate_and_create_document_missing_fields(self):
        """Test validation with missing required fields."""
        reader = OptimizedDoclingJsonReader()
        
        invalid_data = {"name": "test"}
        with self.assertRaises(SchemaValidationError):
            reader._validate_and_create_document(invalid_data, "test.json")
            
    def test_validate_and_create_document_wrong_schema(self):
        """Test validation with wrong schema name."""
        reader = OptimizedDoclingJsonReader()
        
        invalid_data = {
            "schema_name": "WrongSchema",
            "version": "1.0.0",
            "name": "test"
        }
        with self.assertRaises(SchemaValidationError):
            reader._validate_and_create_document(invalid_data, "test.json")
            
    def test_get_cache_info(self):
        """Test get_cache_info method."""
        reader = OptimizedDoclingJsonReader(enable_caching=True)
        
        # Add items to cache
        reader._document_cache["/path1.json"] = DoclingDocument(name="test1")
        reader._document_cache["/path2.json"] = DoclingDocument(name="test2")
        
        cache_info = reader.get_cache_info()
        self.assertIn("size", cache_info)
        self.assertEqual(cache_info["size"], 2)
        self.assertIn("enabled", cache_info)
        self.assertTrue(cache_info["enabled"])
        
    def test_cache_usage_from_cached(self):
        """Test that cached documents are returned from cache."""
        reader = OptimizedDoclingJsonReader(enable_caching=True)
        
        with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
            json.dump(self.valid_docling_data, tmp)
            tmp_path = tmp.name
            
        try:
            # First load - should cache
            doc1 = reader.load_data(tmp_path)
            # Check if any cache key contains the tmp_path
            cache_keys = [key[0] if isinstance(key, tuple) else key for key in reader._document_cache.keys()]
            self.assertIn(tmp_path, cache_keys)
            
            # Modify the file - cache should detect change and reload
            with open(tmp_path, 'w') as f:
                modified_data = self.valid_docling_data.copy()
                modified_data["name"] = "modified.pdf"
                json.dump(modified_data, f)
            
            # Second load should detect file change and load new version
            doc2 = reader.load_data(tmp_path)
            self.assertEqual(doc2.name, "modified.pdf")  # New name from modified file
            self.assertIsNot(doc1, doc2)  # Different object instance
        finally:
            Path(tmp_path).unlink()
        
    def test_clear_cache(self):
        """Test clear_cache method."""
        reader = OptimizedDoclingJsonReader(enable_caching=True)
        
        # Add items to cache
        reader._document_cache["/path1.json"] = DoclingDocument(name="test1")
        reader._document_cache["/path2.json"] = DoclingDocument(name="test2")
        
        self.assertEqual(len(reader._document_cache), 2)
        
        reader.clear_cache()
        self.assertEqual(len(reader._document_cache), 0)
        
    def test_exception_handling_in_load_data(self):
        """Test general exception handling in load_data."""
        reader = OptimizedDoclingJsonReader()
        
        # Mock Path to raise unexpected exception
        with patch('pathlib.Path', side_effect=RuntimeError("Unexpected error")):
            with self.assertRaises(DocPivotValidationError) as ctx:
                reader.load_data("test.json")
            self.assertIn("Unexpected error loading DoclingDocument", str(ctx.exception))
            
    def test_load_data_propagates_known_exceptions(self):
        """Test that known exceptions are propagated correctly."""
        reader = OptimizedDoclingJsonReader()
        
        # Test FileAccessError propagation
        with patch.object(reader, '_load_standard', side_effect=FileAccessError("Test error", "test.json", "test")):
            with tempfile.NamedTemporaryFile(suffix=".docling.json", mode="w", delete=False) as tmp:
                json.dump(self.valid_docling_data, tmp)
                tmp_path = tmp.name
                
            try:
                with self.assertRaises(FileAccessError):
                    reader.load_data(tmp_path)
            finally:
                Path(tmp_path).unlink()


if __name__ == "__main__":
    unittest.main()