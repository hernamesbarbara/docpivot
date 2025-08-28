"""Testing framework for custom format implementations.

This module provides comprehensive testing utilities for validating
custom readers and serializers in DocPivot's extensibility system.
"""

import tempfile
import unittest
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.types import DoclingDocument
from docling_core.types.doc import DocumentOrigin, NodeItem, TextItem, GroupItem

from .readers.basereader import BaseReader
from .readers.custom_reader_base import CustomReaderBase
from .validation import FormatValidator


class CustomFormatTestBase(unittest.TestCase, ABC):
    """Base class for testing custom format implementations.

    This class provides a comprehensive test framework for custom readers
    and serializers. Subclass this to create tests for your custom formats.

    Example usage:
        class MyFormatTest(CustomFormatTestBase):
            def get_reader_class(self) -> Type[BaseReader]:
                return MyCustomReader

            def get_serializer_class(self) -> Type[BaseDocSerializer]:
                return MyCustomSerializer

            def get_test_documents(self) -> List[DoclingDocument]:
                return [self._create_simple_document()]
    """
    
    # Prevent test discovery of this abstract base class
    __test__ = False

    @abstractmethod
    def get_reader_class(self) -> Optional[Type[BaseReader]]:
        """Get the reader class to test.

        Returns:
            Optional[Type[BaseReader]]: Reader class or None if not testing reader
        """
        return None

    @abstractmethod
    def get_serializer_class(self) -> Optional[Type[BaseDocSerializer]]:
        """Get the serializer class to test.

        Returns:
            Optional[Type[BaseDocSerializer]]: Serializer class or None if not testing serializer
        """
        return None

    def get_test_documents(self) -> List[DoclingDocument]:
        """Get test documents for testing.

        Override this method to provide custom test documents.

        Returns:
            List[DoclingDocument]: List of test documents
        """
        return [
            self._create_simple_document(),
            self._create_structured_document(),
            self._create_empty_document(),
        ]

    def get_test_files(self) -> List[str]:
        """Get test file paths for reader testing.

        Override this method to provide custom test files.

        Returns:
            List[str]: List of test file paths
        """
        return []

    def setUp(self) -> None:
        """Set up test environment."""
        super().setUp()
        self.validator = FormatValidator()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self) -> None:
        """Clean up test environment."""
        super().tearDown()
        # Clean up temporary files
        import shutil

        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)

    def test_reader_interface_compliance(self) -> None:
        """Test that reader follows interface correctly."""
        reader_class = self.get_reader_class()
        if reader_class is None:
            self.skipTest("No reader class provided")

        result = self.validator.validate_reader(reader_class)

        # Print detailed results for debugging
        if not result.is_valid:
            print(f"\nReader validation failed:\n{result}")

        self.assertTrue(result.is_valid, f"Reader validation failed: {result}")

    def test_serializer_interface_compliance(self) -> None:
        """Test that serializer follows interface correctly."""
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            self.skipTest("No serializer class provided")

        result = self.validator.validate_serializer(serializer_class)

        # Print detailed results for debugging
        if not result.is_valid:
            print(f"\nSerializer validation failed:\n{result}")

        self.assertTrue(result.is_valid, f"Serializer validation failed: {result}")

    def test_reader_instantiation(self) -> None:
        """Test reader can be instantiated."""
        reader_class = self.get_reader_class()
        if reader_class is None:
            self.skipTest("No reader class provided")

        try:
            reader = reader_class()
            self.assertIsInstance(reader, BaseReader)
        except Exception as e:
            self.fail(f"Failed to instantiate reader: {e}")

    def test_serializer_instantiation(self) -> None:
        """Test serializer can be instantiated."""
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            self.skipTest("No serializer class provided")

        try:
            doc = self._create_simple_document()
            serializer = serializer_class(doc=doc)
            self.assertIsInstance(serializer, BaseDocSerializer)
        except Exception as e:
            self.fail(f"Failed to instantiate serializer: {e}")

    def test_serializer_with_test_documents(self) -> None:
        """Test serializer with various test documents."""
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            self.skipTest("No serializer class provided")

        test_docs = self.get_test_documents()

        for i, doc in enumerate(test_docs):
            with self.subTest(document=i):
                try:
                    serializer = serializer_class(doc=doc)
                    result = serializer.serialize()

                    # Basic checks
                    self.assertIsNotNone(result)
                    self.assertTrue(hasattr(result, "text"))
                    self.assertIsInstance(result.text, str)
                    self.assertGreater(len(result.text), 0)

                except Exception as e:
                    self.fail(f"Serialization failed for document {i}: {e}")

    def test_reader_with_test_files(self) -> None:
        """Test reader with test files."""
        reader_class = self.get_reader_class()
        if reader_class is None:
            self.skipTest("No reader class provided")

        test_files = self.get_test_files()
        if not test_files:
            self.skipTest("No test files provided")

        reader = reader_class()

        for i, file_path in enumerate(test_files):
            with self.subTest(file=i):
                try:
                    doc = reader.load_data(file_path)

                    # Basic checks
                    self.assertIsInstance(doc, DoclingDocument)
                    self.assertIsNotNone(doc.body)

                except Exception as e:
                    self.fail(f"Reading failed for file {file_path}: {e}")

    def test_reader_format_detection(self) -> None:
        """Test reader format detection capabilities."""
        reader_class = self.get_reader_class()
        if reader_class is None:
            self.skipTest("No reader class provided")

        if not issubclass(reader_class, CustomReaderBase):
            self.skipTest(
                "Reader is not CustomReaderBase, skipping format detection test"
            )

        reader = reader_class()

        # Test with supported extensions
        for ext in reader.supported_extensions:
            test_file = self.temp_path / f"test{ext}"
            test_file.write_text("test content")

            result = reader.can_handle(test_file)
            self.assertTrue(result, f"Reader should handle {ext} files")

        # Test with unsupported extension
        unsupported_file = self.temp_path / "test.unsupported"
        unsupported_file.write_text("test content")

        result = reader.can_handle(unsupported_file)
        self.assertFalse(result, "Reader should not handle unsupported files")

    def test_parameter_handling(self) -> None:
        """Test parameter and component serializer support."""
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            self.skipTest("No serializer class provided")

        doc = self._create_simple_document()

        # Test with parameters
        try:
            serializer = serializer_class(doc=doc, test_param="test_value")
            result = serializer.serialize()
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Failed to handle parameters: {e}")

        # Test with component serializers
        try:
            component_serializers = {"test_component": lambda x: str(x)}
            serializer = serializer_class(
                doc=doc, component_serializers=component_serializers
            )
            result = serializer.serialize()
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Failed to handle component serializers: {e}")

    def test_round_trip_compatibility(self) -> None:
        """Test round-trip compatibility between reader and serializer."""
        reader_class = self.get_reader_class()
        serializer_class = self.get_serializer_class()

        if reader_class is None or serializer_class is None:
            self.skipTest("Need both reader and serializer for round-trip test")

        doc = self._create_simple_document()

        try:
            reader = reader_class()
            serializer = serializer_class(doc=doc)

            result = self.validator.test_round_trip(reader, serializer)

            if not result.success:
                print(f"\nRound-trip test failed:\n{result}")

            self.assertTrue(
                result.success, f"Round-trip test failed: {result.error_message}"
            )

        except Exception as e:
            self.fail(f"Round-trip test failed: {e}")

    def test_error_handling(self) -> None:
        """Test error handling for edge cases."""
        # Test reader with non-existent file
        reader_class = self.get_reader_class()
        if reader_class is not None:
            reader = reader_class()

            with self.assertRaises((FileNotFoundError, ValueError)):
                reader.load_data("/non/existent/file.txt")

        # Test serializer with None document
        serializer_class = self.get_serializer_class()
        if serializer_class is not None:
            with self.assertRaises((TypeError, ValueError)):
                serializer_class(doc=None)

    def test_metadata_extraction(self) -> None:
        """Test metadata extraction capabilities."""
        reader_class = self.get_reader_class()
        if reader_class is None:
            self.skipTest("No reader class provided")

        if not issubclass(reader_class, CustomReaderBase):
            self.skipTest("Reader is not CustomReaderBase, skipping metadata test")

        reader = reader_class()

        # Create test file
        test_file = self.temp_path / f"test{reader.supported_extensions[0]}"
        test_file.write_text("test content")

        try:
            metadata = reader.get_metadata(test_file)

            # Basic metadata checks
            self.assertIsInstance(metadata, dict)
            self.assertIn("filename", metadata)
            self.assertIn("format_name", metadata)

        except Exception as e:
            self.fail(f"Metadata extraction failed: {e}")

    def _create_simple_document(self) -> DoclingDocument:
        """Create a simple test document.

        Returns:
            DoclingDocument: Simple test document
        """
        doc = DoclingDocument(
            name="test_document",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="a" * 64,  # Valid SHA256 hash
                filename="test.txt",
            ),
            body=GroupItem(self_ref="#/body"),
        )
        doc.add_text(label="text", text="Test document content")
        return doc

    def _create_structured_document(self) -> DoclingDocument:
        """Create a structured test document.

        Returns:
            DoclingDocument: Structured test document
        """
        doc = DoclingDocument(
            name="structured_document",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="b" * 64,  # Valid SHA256 hash
                filename="structured.txt",
            ),
            body=GroupItem(self_ref="#/body"),
        )
        # Create a structured document with nested groups
        section1 = doc.add_group(name="Section 1")
        doc.add_text(label="text", text="Content of section 1", parent=section1)
        
        subsection = doc.add_group(name="Subsection 1.1", parent=section1)
        doc.add_text(label="text", text="Content of subsection 1.1", parent=subsection)
        
        return doc

    def _create_empty_document(self) -> DoclingDocument:
        """Create an empty test document.

        Returns:
            DoclingDocument: Empty test document
        """
        return DoclingDocument(
            name="empty_document",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="c" * 64,  # Valid SHA256 hash
                filename="empty.txt",
            ),
            body=GroupItem(self_ref="#/body"),
        )


class FormatTestSuite:
    """Test suite runner for format implementations.

    This class provides utilities to run comprehensive tests on
    format implementations and generate detailed reports.
    """

    def __init__(self):
        """Initialize the test suite."""
        self.validator = FormatValidator()

    def run_comprehensive_tests(
        self,
        reader_class: Optional[Type[BaseReader]] = None,
        serializer_class: Optional[Type[BaseDocSerializer]] = None,
        test_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run comprehensive tests on format implementations.

        Args:
            reader_class: Reader class to test
            serializer_class: Serializer class to test
            test_files: Optional test files for reader testing

        Returns:
            Dict[str, Any]: Comprehensive test results
        """
        results = {
            "reader_tests": None,
            "serializer_tests": None,
            "round_trip_tests": None,
            "overall_success": True,
        }

        # Run reader tests
        if reader_class:
            results["reader_tests"] = self._test_reader(reader_class, test_files)
            if not results["reader_tests"]["success"]:
                results["overall_success"] = False

        # Run serializer tests
        if serializer_class:
            results["serializer_tests"] = self._test_serializer(serializer_class)
            if not results["serializer_tests"]["success"]:
                results["overall_success"] = False

        # Run round-trip tests
        if reader_class and serializer_class:
            results["round_trip_tests"] = self._test_round_trip(
                reader_class, serializer_class
            )
            if not results["round_trip_tests"]["success"]:
                results["overall_success"] = False

        return results

    def _test_reader(
        self, reader_class: Type[BaseReader], test_files: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Test a reader class.

        Args:
            reader_class: Reader class to test
            test_files: Optional test files

        Returns:
            Dict[str, Any]: Reader test results
        """
        results = {
            "validation": None,
            "instantiation": False,
            "file_tests": [],
            "success": True,
        }

        # Validation test
        results["validation"] = self.validator.validate_reader(reader_class)
        if not results["validation"].is_valid:
            results["success"] = False

        # Instantiation test
        try:
            reader = reader_class()
            results["instantiation"] = True
        except Exception as e:
            results["instantiation"] = False
            results["success"] = False
            results["instantiation_error"] = str(e)

        # File tests
        if test_files and results["instantiation"]:
            reader = reader_class()
            for file_path in test_files:
                file_result = {"file": file_path, "success": False}
                try:
                    doc = reader.load_data(file_path)
                    file_result["success"] = True
                    file_result["document_name"] = getattr(doc, "name", "")
                except Exception as e:
                    file_result["error"] = str(e)
                    results["success"] = False

                results["file_tests"].append(file_result)

        return results

    def _test_serializer(
        self, serializer_class: Type[BaseDocSerializer]
    ) -> Dict[str, Any]:
        """Test a serializer class.

        Args:
            serializer_class: Serializer class to test

        Returns:
            Dict[str, Any]: Serializer test results
        """
        results = {
            "validation": None,
            "instantiation": False,
            "serialization_tests": [],
            "success": True,
        }

        # Validation test
        results["validation"] = self.validator.validate_serializer(serializer_class)
        if not results["validation"].is_valid:
            results["success"] = False

        # Create test documents
        test_docs = [
            self._create_simple_document(),
            self._create_empty_document(),
        ]

        # Test each document
        for i, doc in enumerate(test_docs):
            test_result = {"document": i, "success": False}

            try:
                serializer = serializer_class(doc=doc)
                result = serializer.serialize()

                test_result["success"] = True
                test_result["output_length"] = len(result.text)

            except Exception as e:
                test_result["error"] = str(e)
                results["success"] = False

            results["serialization_tests"].append(test_result)

        return results

    def _test_round_trip(
        self, reader_class: Type[BaseReader], serializer_class: Type[BaseDocSerializer]
    ) -> Dict[str, Any]:
        """Test round-trip compatibility.

        Args:
            reader_class: Reader class
            serializer_class: Serializer class

        Returns:
            Dict[str, Any]: Round-trip test results
        """
        results = {
            "success": False,
            "error": None,
        }

        try:
            reader = reader_class()

            doc = self._create_simple_document()
            serializer = serializer_class(doc=doc)

            round_trip_result = self.validator.test_round_trip(reader, serializer)
            results["success"] = round_trip_result.success

            if not round_trip_result.success:
                results["error"] = round_trip_result.error_message

        except Exception as e:
            results["error"] = str(e)

        return results

    def _create_simple_document(self) -> DoclingDocument:
        """Create a simple test document."""
        doc = DoclingDocument(
            name="test",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="d" * 64,  # Valid SHA256 hash
                filename="test.txt",
            ),
            body=GroupItem(self_ref="#/body"),
        )
        doc.add_text(label="text", text="Test content")
        return doc

    def _create_empty_document(self) -> DoclingDocument:
        """Create an empty test document."""
        return DoclingDocument(
            name="empty",
            origin=DocumentOrigin(
                mimetype="text/plain", 
                binary_hash="e" * 64,  # Valid SHA256 hash
                filename="empty.txt"
            ),
            body=GroupItem(self_ref="#/body"),
        )

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable test report.

        Args:
            results: Test results from run_comprehensive_tests

        Returns:
            str: Formatted test report
        """
        report = "Format Testing Report\n"
        report += "=" * 50 + "\n\n"

        report += (
            f"Overall Success: {'PASS' if results['overall_success'] else 'FAIL'}\n\n"
        )

        # Reader tests
        if results["reader_tests"]:
            reader_results = results["reader_tests"]
            report += (
                f"Reader Tests: {'PASS' if reader_results['success'] else 'FAIL'}\n"
            )

            if reader_results["validation"]:
                validation = reader_results["validation"]
                report += f"  Validation: {'PASS' if validation.is_valid else 'FAIL'} ({len(validation.issues)} issues)\n"

            report += f"  Instantiation: {'PASS' if reader_results['instantiation'] else 'FAIL'}\n"

            if reader_results["file_tests"]:
                successful_files = sum(
                    1 for test in reader_results["file_tests"] if test["success"]
                )
                total_files = len(reader_results["file_tests"])
                report += f"  File Tests: {successful_files}/{total_files} passed\n"

            report += "\n"

        # Serializer tests
        if results["serializer_tests"]:
            serializer_results = results["serializer_tests"]
            report += f"Serializer Tests: {'PASS' if serializer_results['success'] else 'FAIL'}\n"

            if serializer_results["validation"]:
                validation = serializer_results["validation"]
                report += f"  Validation: {'PASS' if validation.is_valid else 'FAIL'} ({len(validation.issues)} issues)\n"

            if serializer_results["serialization_tests"]:
                successful_tests = sum(
                    1
                    for test in serializer_results["serialization_tests"]
                    if test["success"]
                )
                total_tests = len(serializer_results["serialization_tests"])
                report += (
                    f"  Serialization Tests: {successful_tests}/{total_tests} passed\n"
                )

            report += "\n"

        # Round-trip tests
        if results["round_trip_tests"]:
            round_trip = results["round_trip_tests"]
            report += (
                f"Round-trip Tests: {'PASS' if round_trip['success'] else 'FAIL'}\n"
            )
            if round_trip.get("error"):
                report += f"  Error: {round_trip['error']}\n"
            report += "\n"

        return report
