"""Tests for the validation framework."""

import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import List, Dict, Any

from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.transforms.serializer.base import SerializationResult
from docling_core.types import DoclingDocument
from docling_core.types.doc import DocumentOrigin, NodeItem, TextItem, GroupItem, RefItem

from docpivot.io.validation import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    RoundTripTestResult,
    FormatValidator,
)
from docpivot.io.readers.basereader import BaseReader
from docpivot.io.readers.custom_reader_base import CustomReaderBase
from docpivot.io.serializers.custom_serializer_base import CustomSerializerBase


class ConcreteTestSerializer(BaseDocSerializer):
    """Concrete serializer implementation for testing."""
    
    def __init__(self, doc):
        self.doc = doc
    
    def serialize(self):
        """Implement serialize method."""
        return SerializationResult(text="serialized content")
    
    def get_parts(self, item) -> List:
        """Implement get_parts."""
        return []
    
    def get_excluded_refs(self) -> List[RefItem]:
        """Implement get_excluded_refs."""
        return []
    
    def serialize_captions(self, item, level: int, output: list) -> None:
        """Implement serialize_captions."""
        pass
    
    def serialize_annotations(self, item, output: list) -> None:
        """Implement serialize_annotations."""
        pass
    
    def serialize_bold(self, text: str, **kwargs) -> str:
        """Implement serialize_bold."""
        return text
    
    def serialize_italic(self, text: str, **kwargs) -> str:
        """Implement serialize_italic."""
        return text
    
    def serialize_underline(self, text: str, **kwargs) -> str:
        """Implement serialize_underline."""
        return text
    
    def serialize_strikethrough(self, text: str, **kwargs) -> str:
        """Implement serialize_strikethrough."""
        return text
    
    def serialize_subscript(self, text: str, **kwargs) -> str:
        """Implement serialize_subscript."""
        return text
    
    def serialize_superscript(self, text: str, **kwargs) -> str:
        """Implement serialize_superscript."""
        return text
    
    def serialize_hyperlink(self, text: str, **kwargs) -> str:
        """Implement serialize_hyperlink."""
        return text
    
    def requires_page_break(self, group_item: GroupItem, prev_group_item: GroupItem) -> bool:
        """Implement requires_page_break."""
        return False
    
    def post_process(self, output: list) -> str:
        """Implement post_process."""
        return "".join(output)


class TestValidationSeverity(unittest.TestCase):
    """Tests for ValidationSeverity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        self.assertEqual(ValidationSeverity.INFO.value, "info")
        self.assertEqual(ValidationSeverity.WARNING.value, "warning")
        self.assertEqual(ValidationSeverity.ERROR.value, "error")
        self.assertEqual(ValidationSeverity.CRITICAL.value, "critical")


class TestValidationIssue(unittest.TestCase):
    """Tests for ValidationIssue dataclass."""

    def test_validation_issue_creation(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Test error",
            category="test_category",
            details="Error details",
            suggestion="Fix this way",
        )
        self.assertEqual(issue.severity, ValidationSeverity.ERROR)
        self.assertEqual(issue.message, "Test error")
        self.assertEqual(issue.category, "test_category")
        self.assertEqual(issue.details, "Error details")
        self.assertEqual(issue.suggestion, "Fix this way")

    def test_validation_issue_str_with_all_fields(self):
        """Test string representation with all fields."""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message="Test warning",
            category="test_category",
            details="Warning details",
            suggestion="Consider this",
        )
        result = str(issue)
        self.assertIn("[WARNING]", result)
        self.assertIn("test_category", result)
        self.assertIn("Test warning", result)
        self.assertIn("Details: Warning details", result)
        self.assertIn("Suggestion: Consider this", result)

    def test_validation_issue_str_minimal(self):
        """Test string representation with minimal fields."""
        issue = ValidationIssue(
            severity=ValidationSeverity.INFO,
            message="Info message",
            category="info_category",
        )
        result = str(issue)
        self.assertIn("[INFO]", result)
        self.assertIn("info_category", result)
        self.assertIn("Info message", result)
        self.assertNotIn("Details:", result)
        self.assertNotIn("Suggestion:", result)


class TestValidationResult(unittest.TestCase):
    """Tests for ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating a validation result."""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Error 1",
                category="category1",
            ),
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Warning 1",
                category="category2",
            ),
        ]
        result = ValidationResult(
            is_valid=False, issues=issues, tested_features=["feature1", "feature2"]
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.issues), 2)
        self.assertEqual(result.tested_features, ["feature1", "feature2"])

    def test_has_errors_property(self):
        """Test has_errors property."""
        # With errors
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Error",
                category="cat",
            ),
        ]
        result = ValidationResult(is_valid=False, issues=issues, tested_features=[])
        self.assertTrue(result.has_errors)

        # With critical
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message="Critical",
                category="cat",
            ),
        ]
        result = ValidationResult(is_valid=False, issues=issues, tested_features=[])
        self.assertTrue(result.has_errors)

        # Without errors
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Warning",
                category="cat",
            ),
        ]
        result = ValidationResult(is_valid=True, issues=issues, tested_features=[])
        self.assertFalse(result.has_errors)

    def test_has_warnings_property(self):
        """Test has_warnings property."""
        # With warnings
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Warning",
                category="cat",
            ),
        ]
        result = ValidationResult(is_valid=True, issues=issues, tested_features=[])
        self.assertTrue(result.has_warnings)

        # Without warnings
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Error",
                category="cat",
            ),
        ]
        result = ValidationResult(is_valid=False, issues=issues, tested_features=[])
        self.assertFalse(result.has_warnings)

    def test_get_issues_by_severity(self):
        """Test getting issues by severity."""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR, message="Error 1", category="cat"
            ),
            ValidationIssue(
                severity=ValidationSeverity.ERROR, message="Error 2", category="cat"
            ),
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Warning 1",
                category="cat",
            ),
            ValidationIssue(
                severity=ValidationSeverity.INFO, message="Info 1", category="cat"
            ),
        ]
        result = ValidationResult(is_valid=False, issues=issues, tested_features=[])

        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        self.assertEqual(len(errors), 2)

        warnings = result.get_issues_by_severity(ValidationSeverity.WARNING)
        self.assertEqual(len(warnings), 1)

        infos = result.get_issues_by_severity(ValidationSeverity.INFO)
        self.assertEqual(len(infos), 1)

        criticals = result.get_issues_by_severity(ValidationSeverity.CRITICAL)
        self.assertEqual(len(criticals), 0)

    def test_validation_result_str(self):
        """Test string representation of validation result."""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Error message",
                category="cat",
            ),
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Warning message",
                category="cat",
            ),
        ]
        result = ValidationResult(
            is_valid=False, issues=issues, tested_features=["feature1"]
        )
        output = str(result)
        self.assertIn("Validation Result: FAIL", output)
        self.assertIn("Issues found: 2", output)
        self.assertIn("Error: 1", output)
        self.assertIn("Warning: 1", output)
        self.assertIn("Error message", output)
        self.assertIn("Warning message", output)


class TestRoundTripTestResult(unittest.TestCase):
    """Tests for RoundTripTestResult dataclass."""

    def test_round_trip_result_creation(self):
        """Test creating a round trip test result."""
        result = RoundTripTestResult(
            success=True,
            original_content="original",
            serialized_content="serialized",
            reparsed_content="reparsed",
            content_matches=True,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.original_content, "original")
        self.assertEqual(result.serialized_content, "serialized")
        self.assertEqual(result.reparsed_content, "reparsed")
        self.assertTrue(result.content_matches)

    def test_round_trip_result_str_success(self):
        """Test string representation of successful round trip."""
        result = RoundTripTestResult(
            success=True,
            original_content="orig",
            serialized_content="serial",
            content_matches=True,
        )
        output = str(result)
        self.assertIn("Round-trip Test: PASS", output)
        self.assertIn("Content matches: True", output)

    def test_round_trip_result_str_failure(self):
        """Test string representation of failed round trip."""
        result = RoundTripTestResult(
            success=False,
            original_content="orig",
            serialized_content="serial",
            error_message="Something went wrong",
            content_matches=False,
        )
        output = str(result)
        self.assertIn("Round-trip Test: FAIL", output)
        self.assertIn("Error: Something went wrong", output)
        self.assertIn("Content matches: False", output)


class MockBaseReader(BaseReader):
    """Mock reader for testing."""

    def __init__(self):
        super().__init__()

    def load_data(self, file_path):
        """Mock load_data method."""
        return DoclingDocument(
            name="test",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="a" * 64,
                filename="test.txt",
            ),
            furniture=GroupItem(self_ref="#/furniture"),
            body=GroupItem(self_ref="#/body"),
        )

    def detect_format(self, file_path):
        """Mock detect_format method."""
        return True


class MockCustomReader(BaseReader):
    """Mock custom reader for testing - inherits from BaseReader instead of CustomReaderBase."""

    @property
    def supported_extensions(self):
        return [".txt", ".json"]

    @property
    def format_name(self):
        return "mock_format"
    
    @property
    def capabilities(self):
        """Mock capabilities property."""
        return {"supports_tables": True}
    
    @property
    def version(self):
        """Mock version property."""
        return "1.0.0"

    def load_data(self, file_path):
        """Mock load_data method."""
        return DoclingDocument(
            name="test",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="a" * 64,
                filename="test.txt",
            ),
            furniture=GroupItem(self_ref="#/furniture"),
            body=GroupItem(self_ref="#/body"),
        )

    def detect_format(self, file_path):
        """Mock detect_format method."""
        return True


class BrokenReader(BaseReader):
    """Broken reader for testing failures."""

    def __init__(self):
        raise ValueError("Cannot instantiate")


class InvalidExtensionReader(BaseReader):
    """Reader with invalid extensions."""

    @property
    def supported_extensions(self):
        return ["txt", 123]  # Invalid formats

    @property
    def format_name(self):
        return ""  # Empty format name

    def load_data(self, file_path):
        return None

    def detect_format(self, file_path):
        return "not_a_bool"  # Should return bool


class TestFormatValidator(unittest.TestCase):
    """Tests for FormatValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FormatValidator()

    def test_validate_reader_valid(self):
        """Test validating a valid reader."""
        result = self.validator.validate_reader(MockBaseReader)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)
        self.assertIn("class_hierarchy", result.tested_features)
        self.assertIn("instantiation", result.tested_features)
        self.assertIn("required_methods", result.tested_features)

    def test_validate_reader_invalid_hierarchy(self):
        """Test validating reader with invalid hierarchy."""

        class NotAReader:
            pass

        result = self.validator.validate_reader(NotAReader)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_errors)
        issues = result.get_issues_by_severity(ValidationSeverity.CRITICAL)
        self.assertTrue(any("must extend BaseReader" in issue.message for issue in issues))

    def test_validate_reader_instantiation_failure(self):
        """Test validating reader that fails instantiation."""
        result = self.validator.validate_reader(BrokenReader)
        self.assertFalse(result.is_valid)
        issues = result.get_issues_by_severity(ValidationSeverity.CRITICAL)
        self.assertTrue(any("Failed to instantiate" in issue.message for issue in issues))

    def test_validate_reader_missing_methods(self):
        """Test validating reader with missing methods."""

        class IncompleteReader(BaseReader):
            pass  # Missing load_data and detect_format

        result = self.validator.validate_reader(IncompleteReader)
        self.assertFalse(result.is_valid)
        issues = result.get_issues_by_severity(ValidationSeverity.CRITICAL)
        self.assertTrue(
            any("Missing required method" in issue.message for issue in issues)
        )

    def test_validate_custom_reader_valid(self):
        """Test validating a valid custom reader."""
        # Patch isinstance to make MockCustomReader appear as CustomReaderBase
        with patch('docpivot.io.validation.isinstance') as mock_isinstance:
            # Set up the mock to return True for CustomReaderBase check
            def isinstance_side_effect(obj, cls):
                if cls == CustomReaderBase:
                    return True
                return isinstance.__wrapped__(obj, cls)
            
            mock_isinstance.side_effect = isinstance_side_effect
            
            result = self.validator.validate_reader(MockCustomReader)
        
        self.assertTrue(result.is_valid)
        self.assertIn("custom_reader_properties", result.tested_features)

    def test_validate_custom_reader_invalid_extensions(self):
        """Test validating custom reader with invalid extensions."""
        # Patch isinstance to make InvalidExtensionReader appear as CustomReaderBase
        with patch('docpivot.io.validation.isinstance') as mock_isinstance:
            def isinstance_side_effect(obj, cls):
                if cls == CustomReaderBase:
                    return True
                return isinstance.__wrapped__(obj, cls)
            
            mock_isinstance.side_effect = isinstance_side_effect
            
            result = self.validator.validate_reader(InvalidExtensionReader)
        
        self.assertFalse(result.is_valid)
        # Check for invalid extension format errors
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        self.assertTrue(
            any("Invalid extension format" in issue.message for issue in errors)
        )
        # Check for empty format name
        self.assertTrue(
            any("format_name must be a non-empty string" in issue.message for issue in errors)
        )

    def test_validate_reader_detect_format_behavior(self):
        """Test validation of detect_format behavior."""
        # Patch isinstance to make InvalidExtensionReader appear as CustomReaderBase
        with patch('docpivot.io.validation.isinstance') as mock_isinstance:
            def isinstance_side_effect(obj, cls):
                if cls == CustomReaderBase:
                    return True
                return isinstance.__wrapped__(obj, cls)
            
            mock_isinstance.side_effect = isinstance_side_effect
            
            result = self.validator.validate_reader(InvalidExtensionReader)
        
        # Should have error about detect_format not returning boolean
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        self.assertTrue(
            any("detect_format must return a boolean" in issue.message for issue in errors)
        )

    def test_validate_serializer_valid(self):
        """Test validating a valid serializer."""
        result = self.validator.validate_serializer(ConcreteTestSerializer)
        self.assertTrue(result.is_valid)
        self.assertIn("class_hierarchy", result.tested_features)
        self.assertIn("instantiation", result.tested_features)
        self.assertIn("serialize_behavior", result.tested_features)

    def test_validate_serializer_invalid_hierarchy(self):
        """Test validating serializer with invalid hierarchy."""

        class NotASerializer:
            pass

        result = self.validator.validate_serializer(NotASerializer)
        self.assertFalse(result.is_valid)
        issues = result.get_issues_by_severity(ValidationSeverity.CRITICAL)
        self.assertTrue(
            any("must extend BaseDocSerializer" in issue.message for issue in issues)
        )

    def test_validate_serializer_instantiation_failure(self):
        """Test validating serializer that fails instantiation."""

        class BrokenSerializer(BaseDocSerializer):
            def __init__(self, doc):
                raise ValueError("Cannot instantiate")

        result = self.validator.validate_serializer(BrokenSerializer)
        self.assertFalse(result.is_valid)
        issues = result.get_issues_by_severity(ValidationSeverity.CRITICAL)
        self.assertTrue(any("Failed to instantiate" in issue.message for issue in issues))

    def test_validate_serializer_missing_serialize(self):
        """Test validating serializer missing serialize method."""

        class IncompleteSerializer(ConcreteTestSerializer):
            def __init__(self, doc):
                self.doc = doc
            
            # Remove serialize to test missing method
            serialize = None

        result = self.validator.validate_serializer(IncompleteSerializer)
        self.assertFalse(result.is_valid)
        issues = result.get_issues_by_severity(ValidationSeverity.CRITICAL)
        self.assertTrue(
            any("Missing required method: serialize" in issue.message for issue in issues)
        )

    def test_validate_serializer_not_implemented(self):
        """Test validating serializer with NotImplementedError."""

        class NotImplementedSerializer(ConcreteTestSerializer):
            def serialize(self):
                raise NotImplementedError("Not implemented")

        result = self.validator.validate_serializer(NotImplementedSerializer)
        self.assertFalse(result.is_valid)
        issues = result.get_issues_by_severity(ValidationSeverity.CRITICAL)
        self.assertTrue(
            any("serialize() method not implemented" in issue.message for issue in issues)
        )

    def test_validate_serializer_invalid_result(self):
        """Test validating serializer with invalid serialize result."""

        class InvalidResultSerializer(ConcreteTestSerializer):
            def serialize(self):
                return "invalid"  # Should return object with text attribute

        result = self.validator.validate_serializer(InvalidResultSerializer)
        self.assertFalse(result.is_valid)
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        self.assertTrue(
            any("must return an object with 'text' attribute" in issue.message for issue in errors)
        )

    def test_validate_custom_serializer(self):
        """Test validating custom serializer."""

        class MockCustomSerializer(ConcreteTestSerializer, CustomSerializerBase):
            def __init__(self, doc):
                super().__init__(doc)

            @property
            def output_format(self):
                return "custom"

            @property
            def file_extension(self):
                return ".custom"

            def serialize(self):
                return SerializationResult(text="custom serialized")

        result = self.validator.validate_serializer(MockCustomSerializer)
        self.assertTrue(result.is_valid)
        self.assertIn("custom_serializer_properties", result.tested_features)

    def test_validate_custom_serializer_invalid_properties(self):
        """Test validating custom serializer with invalid properties."""

        class InvalidCustomSerializer(ConcreteTestSerializer, CustomSerializerBase):
            def __init__(self, doc):
                super().__init__(doc)

            @property
            def output_format(self):
                return ""  # Empty format

            @property
            def file_extension(self):
                return "custom"  # Missing dot

            def serialize(self):
                return SerializationResult(text="serialized")

        result = self.validator.validate_serializer(InvalidCustomSerializer)
        self.assertFalse(result.is_valid)
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        self.assertTrue(
            any("output_format must be a non-empty string" in issue.message for issue in errors)
        )
        self.assertTrue(
            any("file_extension must be a string starting with '.'" in issue.message for issue in errors)
        )

    def test_test_round_trip_with_file(self):
        """Test round trip testing with a file."""
        reader = MockBaseReader()
        
        empty_doc = DoclingDocument(
            name="test",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="a" * 64,
                filename="test.txt",
            ),
            furniture=GroupItem(self_ref="#/furniture"),
            body=GroupItem(self_ref="#/body"),
        )
        serializer = ConcreteTestSerializer(doc=empty_doc)
        
        with patch("builtins.open", unittest.mock.mock_open(read_data="test content")):
            result = self.validator.test_round_trip(reader, serializer, "test.txt")
        
        self.assertTrue(result.success)
        self.assertEqual(result.original_content, "test content")
        self.assertEqual(result.serialized_content, "serialized content")

    def test_test_round_trip_without_file(self):
        """Test round trip testing without a file (creates test doc)."""
        reader = MockBaseReader()
        
        empty_doc = DoclingDocument(
            name="test",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="a" * 64,
                filename="test.txt",
            ),
            furniture=GroupItem(self_ref="#/furniture"),
            body=GroupItem(self_ref="#/body"),
        )
        
        class TestSerializer(ConcreteTestSerializer):
            def serialize(self):
                return SerializationResult(text="serialized test content")
        
        serializer = TestSerializer(doc=empty_doc)
        
        result = self.validator.test_round_trip(reader, serializer)
        
        self.assertTrue(result.success)
        self.assertEqual(result.original_content, "Test content for round-trip validation")
        self.assertEqual(result.serialized_content, "serialized test content")

    def test_test_round_trip_exception(self):
        """Test round trip testing with exception."""
        reader = MockBaseReader()
        
        empty_doc = DoclingDocument(
            name="test",
            origin=DocumentOrigin(
                mimetype="text/plain",
                binary_hash="a" * 64,
                filename="test.txt",
            ),
            furniture=GroupItem(self_ref="#/furniture"),
            body=GroupItem(self_ref="#/body"),
        )
        
        class ExceptionSerializer(ConcreteTestSerializer):
            def serialize(self):
                raise RuntimeError("Serialization failed")

        serializer = ExceptionSerializer(doc=empty_doc)
        
        result = self.validator.test_round_trip(reader, serializer)
        
        self.assertFalse(result.success)
        self.assertIn("Round-trip test failed", result.error_message)
        self.assertIn("Serialization failed", result.error_message)

    def test_validate_format_pair_valid(self):
        """Test validating a valid reader/serializer pair."""
        results = self.validator.validate_format_pair(MockBaseReader, ConcreteTestSerializer)
        
        self.assertIn("reader_validation", results)
        self.assertIn("serializer_validation", results)
        self.assertIn("round_trip_test", results)
        self.assertIn("compatibility_issues", results)
        
        self.assertTrue(results["reader_validation"].is_valid)
        self.assertTrue(results["serializer_validation"].is_valid)
        self.assertIsNotNone(results["round_trip_test"])

    def test_validate_format_pair_invalid_reader(self):
        """Test validating pair with invalid reader."""
        results = self.validator.validate_format_pair(BrokenReader, ConcreteTestSerializer)
        
        self.assertFalse(results["reader_validation"].is_valid)
        self.assertTrue(results["serializer_validation"].is_valid)
        self.assertIsNone(results["round_trip_test"])  # Skipped due to invalid reader

    def test_validate_format_pair_exception_in_round_trip(self):
        """Test validate format pair with exception during round trip setup."""
        
        class ExceptionOnInit(BaseDocSerializer):
            def __init__(self, doc):
                raise RuntimeError("Cannot create serializer")

        results = self.validator.validate_format_pair(MockBaseReader, ExceptionOnInit)
        
        # Validation should fail due to instantiation error
        self.assertFalse(results["serializer_validation"].is_valid)

    def test_get_validation_report(self):
        """Test generating validation report."""
        results = self.validator.validate_format_pair(MockBaseReader, ConcreteTestSerializer)
        report = self.validator.get_validation_report(results)
        
        self.assertIn("Format Validation Report", report)
        self.assertIn("Reader Validation: PASS", report)
        self.assertIn("Serializer Validation: PASS", report)
        self.assertIn("Round-trip Test: PASS", report)
        
    def test_get_validation_report_with_issues(self):
        """Test generating report with validation issues."""
        results = {
            "reader_validation": ValidationResult(
                is_valid=False,
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message="Reader error",
                        category="test"
                    )
                ],
                tested_features=[]
            ),
            "serializer_validation": ValidationResult(
                is_valid=True,
                issues=[],
                tested_features=[]
            ),
            "round_trip_test": RoundTripTestResult(
                success=False,
                original_content="",
                serialized_content="",
                error_message="Test failed"
            ),
            "compatibility_issues": ["Issue 1", "Issue 2"]
        }
        
        report = self.validator.get_validation_report(results)
        
        self.assertIn("Reader Validation: FAIL", report)
        self.assertIn("Reader error", report)
        self.assertIn("Serializer Validation: PASS", report)
        self.assertIn("Round-trip Test: FAIL", report)
        self.assertIn("Test failed", report)
        self.assertIn("Compatibility Issues:", report)
        self.assertIn("Issue 1", report)
        self.assertIn("Issue 2", report)

    def test_get_validation_report_skipped_round_trip(self):
        """Test report when round trip test is skipped."""
        results = {
            "reader_validation": ValidationResult(
                is_valid=False,
                issues=[],
                tested_features=[]
            ),
            "serializer_validation": ValidationResult(
                is_valid=True,
                issues=[],
                tested_features=[]
            ),
            "round_trip_test": None,
            "compatibility_issues": []
        }
        
        report = self.validator.get_validation_report(results)
        self.assertIn("Round-trip Test: SKIPPED", report)


if __name__ == "__main__":
    unittest.main()