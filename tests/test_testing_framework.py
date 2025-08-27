"""Comprehensive tests for the testing framework module."""

import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Optional, Type
from unittest.mock import Mock, patch, MagicMock

from docling_core.transforms.serializer.common import BaseDocSerializer, SerializationResult
from docling_core.types import DoclingDocument
from docling_core.types.doc import DocumentOrigin, NodeItem, TextItem

from docpivot.io.readers.basereader import BaseReader
from docpivot.io.readers.custom_reader_base import CustomReaderBase
from docpivot.io.testing import CustomFormatTestBase, FormatTestSuite


class TestCustomReaderImpl(CustomReaderBase):
    """Test implementation of CustomReaderBase for testing."""
    
    @property
    def supported_extensions(self):
        return [".test", ".tst"]
    
    @property
    def format_name(self):
        return "TestFormat"
    
    def can_handle(self, file_path):
        path = Path(file_path)
        return path.suffix in self.supported_extensions
    
    def load_data(self, file_path):
        """Implement required load_data method from BaseReader."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return self.read_document(file_path)
    
    def detect_format(self, file_path):
        """Implement required detect_format method from BaseReader."""
        return self.can_handle(file_path)
    
    def read_document(self, file_path):
        from docling_core.types.doc import PictureDataType, PictureItem, RefItem
        
        # Create RefItem for self_ref
        ref_item = RefItem(
            cref="#/main-text/0",
            **{"$ref": "#/main-text/0"}
        )
        
        return DoclingDocument(
            name="test_doc",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="a" * 64,
                filename=str(file_path),
            ),
            furniture=[],
            body=NodeItem(
                self_ref=ref_item,
                label="root",
                orig="#/main-text/0",
                children=[
                    TextItem(
                        text="Test content from reader",
                        self_ref=ref_item,
                        label="text",
                        orig="#/main-text/0"
                    )
                ]
            )
        )
    
    def get_metadata(self, file_path):
        return {
            "filename": str(file_path),
            "format_name": self.format_name,
            "custom_field": "test_value"
        }


class TestSerializerImpl(BaseDocSerializer):
    """Test implementation of BaseDocSerializer for testing."""
    
    def serialize(self, **kwargs) -> SerializationResult:
        result = SerializationResult(text="Serialized output: " + self.doc.name)
        return result


class ConcreteTestCase(CustomFormatTestBase):
    """Concrete test case implementation for testing the base class."""
    
    def get_reader_class(self) -> Optional[Type[BaseReader]]:
        return TestCustomReaderImpl
    
    def get_serializer_class(self) -> Optional[Type[BaseDocSerializer]]:
        return TestSerializerImpl
    
    def get_test_documents(self):
        return [
            self._create_simple_document(),
            self._create_structured_document(),
            self._create_empty_document(),
        ]
    
    def get_test_files(self):
        # Create temporary test files
        test_files = []
        temp_dir = Path(tempfile.mkdtemp())
        
        test_file = temp_dir / "test.test"
        test_file.write_text("test content")
        test_files.append(str(test_file))
        
        test_file2 = temp_dir / "test2.tst"
        test_file2.write_text("another test")
        test_files.append(str(test_file2))
        
        return test_files


class TestCustomFormatTestBase(unittest.TestCase):
    """Test the CustomFormatTestBase class directly."""
    
    def test_concrete_implementation_runs(self):
        """Test that concrete implementation of CustomFormatTestBase works."""
        suite = unittest.TestSuite()
        test_case = ConcreteTestCase()
        
        # Add all test methods from ConcreteTestCase
        for method_name in dir(test_case):
            if method_name.startswith('test_'):
                suite.addTest(ConcreteTestCase(method_name))
        
        runner = unittest.TextTestRunner()
        result = runner.run(suite)
        
        # Check that tests ran
        self.assertGreater(result.testsRun, 0)
    
    def test_reader_interface_compliance(self):
        """Test reader interface compliance checking."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the reader interface compliance test
        test_case.test_reader_interface_compliance()
        
        test_case.tearDown()
    
    def test_serializer_interface_compliance(self):
        """Test serializer interface compliance checking."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the serializer interface compliance test
        test_case.test_serializer_interface_compliance()
        
        test_case.tearDown()
    
    def test_reader_instantiation(self):
        """Test reader instantiation test."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the reader instantiation test
        test_case.test_reader_instantiation()
        
        test_case.tearDown()
    
    def test_serializer_instantiation(self):
        """Test serializer instantiation test."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the serializer instantiation test
        test_case.test_serializer_instantiation()
        
        test_case.tearDown()
    
    def test_serializer_with_test_documents(self):
        """Test serializer with various test documents."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the serializer document test
        test_case.test_serializer_with_test_documents()
        
        test_case.tearDown()
    
    def test_reader_with_test_files(self):
        """Test reader with test files."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the reader file test
        test_case.test_reader_with_test_files()
        
        test_case.tearDown()
    
    def test_reader_format_detection(self):
        """Test reader format detection capabilities."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the format detection test
        test_case.test_reader_format_detection()
        
        test_case.tearDown()
    
    def test_parameter_handling(self):
        """Test parameter and component serializer support."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the parameter handling test
        test_case.test_parameter_handling()
        
        test_case.tearDown()
    
    def test_round_trip_compatibility(self):
        """Test round-trip compatibility between reader and serializer."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Mock the validator's test_round_trip method
        with patch.object(test_case.validator, 'test_round_trip') as mock_round_trip:
            mock_result = Mock()
            mock_result.success = True
            mock_result.error_message = None
            mock_round_trip.return_value = mock_result
            
            # Run the round trip test
            test_case.test_round_trip_compatibility()
        
        test_case.tearDown()
    
    def test_error_handling(self):
        """Test error handling for edge cases."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the error handling test
        test_case.test_error_handling()
        
        test_case.tearDown()
    
    def test_metadata_extraction(self):
        """Test metadata extraction capabilities."""
        test_case = ConcreteTestCase()
        test_case.setUp()
        
        # Run the metadata extraction test
        test_case.test_metadata_extraction()
        
        test_case.tearDown()
    
    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods must be implemented."""
        with self.assertRaises(TypeError):
            # Cannot instantiate abstract class
            CustomFormatTestBase()
    
    def test_skips_tests_when_no_reader_provided(self):
        """Test that tests are skipped when no reader is provided."""
        
        class NoReaderTestCase(CustomFormatTestBase):
            def get_reader_class(self):
                return None
            
            def get_serializer_class(self):
                return TestSerializerImpl
        
        test_case = NoReaderTestCase()
        test_case.setUp()
        
        # These should skip without error
        with self.assertRaises(unittest.SkipTest):
            test_case.test_reader_interface_compliance()
        
        with self.assertRaises(unittest.SkipTest):
            test_case.test_reader_instantiation()
        
        test_case.tearDown()
    
    def test_skips_tests_when_no_serializer_provided(self):
        """Test that tests are skipped when no serializer is provided."""
        
        class NoSerializerTestCase(CustomFormatTestBase):
            def get_reader_class(self):
                return TestCustomReaderImpl
            
            def get_serializer_class(self):
                return None
        
        test_case = NoSerializerTestCase()
        test_case.setUp()
        
        # These should skip without error
        with self.assertRaises(unittest.SkipTest):
            test_case.test_serializer_interface_compliance()
        
        with self.assertRaises(unittest.SkipTest):
            test_case.test_serializer_instantiation()
        
        test_case.tearDown()


class TestFormatTestSuite(unittest.TestCase):
    """Test the FormatTestSuite class."""
    
    def setUp(self):
        self.suite = FormatTestSuite()
    
    def test_initialization(self):
        """Test FormatTestSuite initialization."""
        self.assertIsNotNone(self.suite.validator)
    
    def test_run_comprehensive_tests_with_reader(self):
        """Test running comprehensive tests with reader only."""
        results = self.suite.run_comprehensive_tests(
            reader_class=TestCustomReaderImpl,
            serializer_class=None,
            test_files=None
        )
        
        self.assertIn("reader_tests", results)
        self.assertIn("serializer_tests", results)
        self.assertIn("round_trip_tests", results)
        self.assertIn("overall_success", results)
        
        self.assertIsNotNone(results["reader_tests"])
        self.assertIsNone(results["serializer_tests"])
        self.assertIsNone(results["round_trip_tests"])
    
    def test_run_comprehensive_tests_with_serializer(self):
        """Test running comprehensive tests with serializer only."""
        results = self.suite.run_comprehensive_tests(
            reader_class=None,
            serializer_class=TestSerializerImpl,
            test_files=None
        )
        
        self.assertIsNone(results["reader_tests"])
        self.assertIsNotNone(results["serializer_tests"])
        self.assertIsNone(results["round_trip_tests"])
    
    def test_run_comprehensive_tests_with_both(self):
        """Test running comprehensive tests with both reader and serializer."""
        results = self.suite.run_comprehensive_tests(
            reader_class=TestCustomReaderImpl,
            serializer_class=TestSerializerImpl,
            test_files=None
        )
        
        self.assertIsNotNone(results["reader_tests"])
        self.assertIsNotNone(results["serializer_tests"])
        self.assertIsNotNone(results["round_trip_tests"])
    
    def test_run_comprehensive_tests_with_test_files(self):
        """Test running comprehensive tests with test files."""
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.test"
        test_file.write_text("test content")
        
        results = self.suite.run_comprehensive_tests(
            reader_class=TestCustomReaderImpl,
            serializer_class=None,
            test_files=[str(test_file)]
        )
        
        self.assertIsNotNone(results["reader_tests"])
        self.assertGreater(len(results["reader_tests"]["file_tests"]), 0)
    
    def test_test_reader_success(self):
        """Test _test_reader method with successful reader."""
        results = self.suite._test_reader(TestCustomReaderImpl, None)
        
        self.assertIn("validation", results)
        self.assertIn("instantiation", results)
        self.assertIn("file_tests", results)
        self.assertIn("success", results)
        self.assertTrue(results["instantiation"])
    
    def test_test_reader_with_files(self):
        """Test _test_reader method with test files."""
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.test"
        test_file.write_text("test content")
        
        results = self.suite._test_reader(TestCustomReaderImpl, [str(test_file)])
        
        self.assertGreater(len(results["file_tests"]), 0)
        self.assertTrue(results["file_tests"][0]["success"])
    
    def test_test_reader_with_invalid_file(self):
        """Test _test_reader method with invalid file."""
        results = self.suite._test_reader(TestCustomReaderImpl, ["/nonexistent/file.test"])
        
        self.assertGreater(len(results["file_tests"]), 0)
        self.assertFalse(results["file_tests"][0]["success"])
        self.assertIn("error", results["file_tests"][0])
    
    def test_test_serializer_success(self):
        """Test _test_serializer method with successful serializer."""
        results = self.suite._test_serializer(TestSerializerImpl)
        
        self.assertIn("validation", results)
        self.assertIn("instantiation", results)
        self.assertIn("serialization_tests", results)
        self.assertIn("success", results)
        self.assertGreater(len(results["serialization_tests"]), 0)
    
    def test_test_round_trip_success(self):
        """Test _test_round_trip method."""
        with patch.object(self.suite.validator, 'test_round_trip') as mock_round_trip:
            mock_result = Mock()
            mock_result.success = True
            mock_result.error_message = None
            mock_round_trip.return_value = mock_result
            
            results = self.suite._test_round_trip(TestCustomReaderImpl, TestSerializerImpl)
            
            self.assertTrue(results["success"])
            self.assertIsNone(results["error"])
    
    def test_test_round_trip_failure(self):
        """Test _test_round_trip method with failure."""
        with patch.object(self.suite.validator, 'test_round_trip') as mock_round_trip:
            mock_result = Mock()
            mock_result.success = False
            mock_result.error_message = "Round trip failed"
            mock_round_trip.return_value = mock_result
            
            results = self.suite._test_round_trip(TestCustomReaderImpl, TestSerializerImpl)
            
            self.assertFalse(results["success"])
            self.assertEqual(results["error"], "Round trip failed")
    
    def test_test_round_trip_exception(self):
        """Test _test_round_trip method with exception."""
        with patch.object(self.suite.validator, 'test_round_trip') as mock_round_trip:
            mock_round_trip.side_effect = Exception("Test error")
            
            results = self.suite._test_round_trip(TestCustomReaderImpl, TestSerializerImpl)
            
            self.assertFalse(results["success"])
            self.assertEqual(results["error"], "Test error")
    
    def test_create_simple_document(self):
        """Test _create_simple_document method."""
        doc = self.suite._create_simple_document()
        
        self.assertIsInstance(doc, DoclingDocument)
        self.assertEqual(doc.name, "test")
        self.assertIsNotNone(doc.body)
        self.assertGreater(len(doc.body.children), 0)
    
    def test_create_empty_document(self):
        """Test _create_empty_document method."""
        doc = self.suite._create_empty_document()
        
        self.assertIsInstance(doc, DoclingDocument)
        self.assertEqual(doc.name, "empty")
        self.assertIsNotNone(doc.body)
    
    def test_generate_report_comprehensive(self):
        """Test generate_report method with comprehensive results."""
        results = {
            "overall_success": True,
            "reader_tests": {
                "success": True,
                "validation": Mock(is_valid=True, issues=[]),
                "instantiation": True,
                "file_tests": [
                    {"success": True, "file": "test1.txt"},
                    {"success": True, "file": "test2.txt"},
                ]
            },
            "serializer_tests": {
                "success": True,
                "validation": Mock(is_valid=True, issues=[]),
                "serialization_tests": [
                    {"success": True, "document": 0},
                    {"success": True, "document": 1},
                ]
            },
            "round_trip_tests": {
                "success": True,
                "error": None
            }
        }
        
        report = self.suite.generate_report(results)
        
        self.assertIn("Format Testing Report", report)
        self.assertIn("Overall Success: PASS", report)
        self.assertIn("Reader Tests: PASS", report)
        self.assertIn("Serializer Tests: PASS", report)
        self.assertIn("Round-trip Tests: PASS", report)
        self.assertIn("2/2 passed", report)  # File tests
    
    def test_generate_report_with_failures(self):
        """Test generate_report method with failures."""
        results = {
            "overall_success": False,
            "reader_tests": {
                "success": False,
                "validation": Mock(is_valid=False, issues=["issue1", "issue2"]),
                "instantiation": False,
                "file_tests": [
                    {"success": False, "file": "test1.txt", "error": "Error"}
                ]
            },
            "serializer_tests": {
                "success": False,
                "validation": Mock(is_valid=False, issues=["issue3"]),
                "serialization_tests": [
                    {"success": False, "document": 0, "error": "Error"}
                ]
            },
            "round_trip_tests": {
                "success": False,
                "error": "Round trip failed"
            }
        }
        
        report = self.suite.generate_report(results)
        
        self.assertIn("Overall Success: FAIL", report)
        self.assertIn("Reader Tests: FAIL", report)
        self.assertIn("Serializer Tests: FAIL", report)
        self.assertIn("Round-trip Tests: FAIL", report)
        self.assertIn("(2 issues)", report)  # Validation issues
        self.assertIn("Round trip failed", report)
    
    def test_generate_report_partial_results(self):
        """Test generate_report method with partial results."""
        results = {
            "overall_success": True,
            "reader_tests": None,
            "serializer_tests": {
                "success": True,
                "validation": None,
                "serialization_tests": []
            },
            "round_trip_tests": None
        }
        
        report = self.suite.generate_report(results)
        
        self.assertIn("Overall Success: PASS", report)
        self.assertIn("Serializer Tests: PASS", report)
        self.assertNotIn("Reader Tests:", report)
        self.assertNotIn("Round-trip Tests:", report)


class TestDocumentCreationMethods(unittest.TestCase):
    """Test document creation helper methods in CustomFormatTestBase."""
    
    def setUp(self):
        self.test_case = ConcreteTestCase()
        self.test_case.setUp()
    
    def tearDown(self):
        self.test_case.tearDown()
    
    def test_create_simple_document(self):
        """Test _create_simple_document helper method."""
        doc = self.test_case._create_simple_document()
        
        self.assertIsInstance(doc, DoclingDocument)
        self.assertEqual(doc.name, "test_document")
        self.assertIsNotNone(doc.origin)
        self.assertEqual(doc.origin.filename, "test.txt")
        self.assertIsNotNone(doc.body)
        self.assertGreater(len(doc.body.children), 0)
        self.assertIsInstance(doc.body.children[0], TextItem)
        self.assertEqual(doc.body.children[0].text, "This is a simple test document.")
    
    def test_create_structured_document(self):
        """Test _create_structured_document helper method."""
        doc = self.test_case._create_structured_document()
        
        self.assertIsInstance(doc, DoclingDocument)
        self.assertEqual(doc.name, "structured_document")
        self.assertEqual(doc.origin.filename, "structured.txt")
        self.assertIsNotNone(doc.body)
        self.assertGreater(len(doc.body.children), 0)
        
        # Check structure
        section1 = doc.body.children[0]
        self.assertIsInstance(section1, NodeItem)
        self.assertEqual(section1.label, "Section 1")
        self.assertGreater(len(section1.children), 0)
        
        # Check subsection
        subsection = section1.children[1]
        self.assertIsInstance(subsection, NodeItem)
        self.assertEqual(subsection.label, "Subsection 1.1")
    
    def test_create_empty_document(self):
        """Test _create_empty_document helper method."""
        doc = self.test_case._create_empty_document()
        
        self.assertIsInstance(doc, DoclingDocument)
        self.assertEqual(doc.name, "empty_document")
        self.assertEqual(doc.origin.filename, "empty.txt")
        self.assertIsNotNone(doc.body)
        # Empty document should have no children or empty children list
        self.assertTrue(
            doc.body.children is None or len(doc.body.children) == 0
        )
    
    def test_get_test_documents_default(self):
        """Test default get_test_documents implementation."""
        docs = self.test_case.get_test_documents()
        
        self.assertIsInstance(docs, list)
        self.assertEqual(len(docs), 3)
        
        # Check document types
        self.assertEqual(docs[0].name, "test_document")
        self.assertEqual(docs[1].name, "structured_document")
        self.assertEqual(docs[2].name, "empty_document")
    
    def test_get_test_files_override(self):
        """Test get_test_files can be overridden."""
        files = self.test_case.get_test_files()
        
        self.assertIsInstance(files, list)
        self.assertEqual(len(files), 2)
        
        # Check that files exist and have correct extensions
        for file_path in files:
            path = Path(file_path)
            self.assertTrue(path.exists())
            self.assertIn(path.suffix, [".test", ".tst"])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_reader_instantiation_failure(self):
        """Test handling of reader instantiation failure."""
        
        class FailingReader(BaseReader):
            def __init__(self):
                raise RuntimeError("Cannot instantiate")
            
            def detect_format(self, file_path):
                return True
            
            def load_data(self, file_path):
                pass
        
        class FailingReaderTestCase(CustomFormatTestBase):
            def get_reader_class(self):
                return FailingReader
            
            def get_serializer_class(self):
                return None
        
        test_case = FailingReaderTestCase()
        test_case.setUp()
        
        # Should fail the instantiation test
        with self.assertRaises(AssertionError):
            test_case.test_reader_instantiation()
        
        test_case.tearDown()
    
    def test_serializer_instantiation_failure(self):
        """Test handling of serializer instantiation failure."""
        
        class FailingSerializer(BaseDocSerializer):
            def __init__(self, doc=None):
                raise RuntimeError("Cannot instantiate")
            
            def serialize(self, **kwargs):
                pass
        
        class FailingSerializerTestCase(CustomFormatTestBase):
            def get_reader_class(self):
                return None
            
            def get_serializer_class(self):
                return FailingSerializer
        
        test_case = FailingSerializerTestCase()
        test_case.setUp()
        
        # Should fail the instantiation test
        with self.assertRaises(AssertionError):
            test_case.test_serializer_instantiation()
        
        test_case.tearDown()
    
    def test_non_custom_reader_format_detection(self):
        """Test format detection skip for non-CustomReaderBase readers."""
        
        class BasicReader(BaseReader):
            def detect_format(self, file_path):
                return True
            
            def load_data(self, file_path):
                return self._create_simple_document()
            
            def _create_simple_document(self):
                return DoclingDocument(
                    name="test",
                    origin=DocumentOrigin(
                        mimetype="text/plain",
                        binary_hash="a" * 64,
                        filename="test.txt",
                    ),
                    furniture=[],
                    body=NodeItem(children=[TextItem(text="Test")])
                )
        
        class BasicReaderTestCase(CustomFormatTestBase):
            def get_reader_class(self):
                return BasicReader
            
            def get_serializer_class(self):
                return None
        
        test_case = BasicReaderTestCase()
        test_case.setUp()
        
        # Should skip format detection test for non-CustomReaderBase
        with self.assertRaises(unittest.SkipTest):
            test_case.test_reader_format_detection()
        
        test_case.tearDown()
    
    def test_empty_test_files_list(self):
        """Test reader test with empty test files list."""
        
        class EmptyFilesTestCase(CustomFormatTestBase):
            def get_reader_class(self):
                return TestCustomReaderImpl
            
            def get_serializer_class(self):
                return None
            
            def get_test_files(self):
                return []
        
        test_case = EmptyFilesTestCase()
        test_case.setUp()
        
        # Should skip test when no test files provided
        with self.assertRaises(unittest.SkipTest):
            test_case.test_reader_with_test_files()
        
        test_case.tearDown()


if __name__ == "__main__":
    unittest.main()