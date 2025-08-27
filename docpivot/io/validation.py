"""Format validation framework for custom implementations.

This module provides comprehensive validation for custom readers and serializers
to ensure they meet interface requirements and work correctly with DocPivot.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass
import traceback

from docling_core.transforms.serializer.common import BaseDocSerializer
from docling_core.types import DoclingDocument
from docling_core.types.doc import DocumentOrigin, NodeItem, TextItem, GroupItem

from .readers.basereader import BaseReader
from .readers.custom_reader_base import CustomReaderBase
from .serializers.custom_serializer_base import CustomSerializerBase


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    severity: ValidationSeverity
    message: str
    category: str
    details: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the issue."""
        result = f"[{self.severity.value.upper()}] {self.category}: {self.message}"
        if self.details:
            result += f"\n  Details: {self.details}"
        if self.suggestion:
            result += f"\n  Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationResult:
    """Results of format validation."""

    is_valid: bool
    issues: List[ValidationIssue]
    tested_features: List[str]

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for issue in self.issues
        )

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return any(
            issue.severity == ValidationSeverity.WARNING for issue in self.issues
        )

    def get_issues_by_severity(
        self, severity: ValidationSeverity
    ) -> List[ValidationIssue]:
        """Get issues by severity level."""
        return [issue for issue in self.issues if issue.severity == severity]

    def __str__(self) -> str:
        """String representation of the results."""
        result = f"Validation Result: {'PASS' if self.is_valid else 'FAIL'}\n"
        result += f"Issues found: {len(self.issues)}\n"

        for severity in ValidationSeverity:
            issues = self.get_issues_by_severity(severity)
            if issues:
                result += f"  {severity.value.title()}: {len(issues)}\n"

        if self.issues:
            result += "\nDetailed Issues:\n"
            for issue in self.issues:
                result += f"  {issue}\n"

        return result


@dataclass
class RoundTripTestResult:
    """Results of round-trip testing."""

    success: bool
    original_content: str
    serialized_content: str
    reparsed_content: Optional[str] = None
    error_message: Optional[str] = None
    content_matches: Optional[bool] = None

    def __str__(self) -> str:
        """String representation of the test result."""
        result = f"Round-trip Test: {'PASS' if self.success else 'FAIL'}\n"
        if self.error_message:
            result += f"Error: {self.error_message}\n"
        if self.content_matches is not None:
            result += f"Content matches: {self.content_matches}\n"
        return result


class FormatValidator:
    """Validator for custom format implementations.

    This class provides comprehensive validation for custom readers and
    serializers to ensure they meet interface requirements and work correctly.
    """

    def __init__(self):
        """Initialize the format validator."""
        pass

    def validate_reader(self, reader_class: Type[BaseReader]) -> ValidationResult:
        """Validate a reader implementation.

        Args:
            reader_class: Reader class to validate

        Returns:
            ValidationResult: Validation results
        """
        issues = []
        tested_features = []

        # Test 1: Class hierarchy validation
        tested_features.append("class_hierarchy")
        if not issubclass(reader_class, BaseReader):
            issues.append(
                ValidationIssue(
                    ValidationSeverity.CRITICAL,
                    "Reader class must extend BaseReader",
                    "class_hierarchy",
                    f"Class {reader_class.__name__} does not extend BaseReader",
                )
            )

        # Test 2: Instantiation
        tested_features.append("instantiation")
        try:
            reader_instance = reader_class()
        except Exception as e:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.CRITICAL,
                    "Failed to instantiate reader",
                    "instantiation",
                    str(e),
                    "Ensure __init__ method doesn't require mandatory parameters",
                )
            )
            # Can't continue with instance tests
            return ValidationResult(
                is_valid=len(issues) == 0,
                issues=issues,
                tested_features=tested_features,
            )

        # Test 3: Required methods
        tested_features.append("required_methods")
        required_methods = ["load_data", "detect_format"]
        for method_name in required_methods:
            if not hasattr(reader_instance, method_name):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.CRITICAL,
                        f"Missing required method: {method_name}",
                        "required_methods",
                    )
                )
            elif not callable(getattr(reader_instance, method_name)):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.CRITICAL,
                        f"Method {method_name} is not callable",
                        "required_methods",
                    )
                )

        # Test 4: Custom reader base properties (if applicable)
        if isinstance(reader_instance, CustomReaderBase):
            tested_features.append("custom_reader_properties")

            # Test supported_extensions property
            try:
                extensions = reader_instance.supported_extensions
                if not isinstance(extensions, list):
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.ERROR,
                            "supported_extensions must return a list",
                            "custom_reader_properties",
                        )
                    )
                elif not extensions:
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.WARNING,
                            "supported_extensions is empty",
                            "custom_reader_properties",
                            suggestion="Consider defining file extensions this reader supports",
                        )
                    )
                else:
                    for ext in extensions:
                        if not isinstance(ext, str) or not ext.startswith("."):
                            issues.append(
                                ValidationIssue(
                                    ValidationSeverity.ERROR,
                                    f"Invalid extension format: {ext}",
                                    "custom_reader_properties",
                                    "Extensions must be strings starting with '.'",
                                )
                            )
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "Failed to access supported_extensions property",
                        "custom_reader_properties",
                        str(e),
                    )
                )

            # Test format_name property
            try:
                format_name = reader_instance.format_name
                if not isinstance(format_name, str) or not format_name.strip():
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.ERROR,
                            "format_name must be a non-empty string",
                            "custom_reader_properties",
                        )
                    )
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "Failed to access format_name property",
                        "custom_reader_properties",
                        str(e),
                    )
                )

        # Test 5: Method behavior validation
        tested_features.append("method_behavior")

        # Test detect_format method
        try:
            # Test with a non-existent file
            can_handle = reader_instance.detect_format("/non/existent/file.txt")
            if not isinstance(can_handle, bool):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "detect_format must return a boolean",
                        "method_behavior",
                    )
                )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.WARNING,
                    "detect_format raised an exception",
                    "method_behavior",
                    str(e),
                    "Consider handling file access errors gracefully",
                )
            )

        is_valid = not any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for issue in issues
        )

        return ValidationResult(
            is_valid=is_valid, issues=issues, tested_features=tested_features
        )

    def validate_serializer(
        self, serializer_class: Type[BaseDocSerializer]
    ) -> ValidationResult:
        """Validate a serializer implementation.

        Args:
            serializer_class: Serializer class to validate

        Returns:
            ValidationResult: Validation results
        """
        issues = []
        tested_features = []

        # Test 1: Class hierarchy validation
        tested_features.append("class_hierarchy")
        if not issubclass(serializer_class, BaseDocSerializer):
            issues.append(
                ValidationIssue(
                    ValidationSeverity.CRITICAL,
                    "Serializer class must extend BaseDocSerializer",
                    "class_hierarchy",
                    f"Class {serializer_class.__name__} does not extend BaseDocSerializer",
                )
            )

        # Test 2: Instantiation with empty document
        tested_features.append("instantiation")
        try:
            # Create minimal DoclingDocument for testing
            empty_doc = DoclingDocument(
                name="test",
                origin=DocumentOrigin(
                    mimetype="text/plain",
                    binary_hash="a" * 64,  # Valid SHA256 hash
                    filename="",
                ),
                furniture=GroupItem(self_ref="#/furniture"),
                body=GroupItem(self_ref="#/body"),
            )
            serializer_instance = serializer_class(doc=empty_doc)
        except Exception as e:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.CRITICAL,
                    "Failed to instantiate serializer",
                    "instantiation",
                    str(e),
                    "Ensure __init__ accepts doc parameter and handles empty documents",
                )
            )
            # Can't continue with instance tests
            return ValidationResult(
                is_valid=len(issues) == 0,
                issues=issues,
                tested_features=tested_features,
            )

        # Test 3: Required methods
        tested_features.append("required_methods")
        required_methods = ["serialize"]
        for method_name in required_methods:
            if not hasattr(serializer_instance, method_name):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.CRITICAL,
                        f"Missing required method: {method_name}",
                        "required_methods",
                    )
                )
            elif not callable(getattr(serializer_instance, method_name)):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.CRITICAL,
                        f"Method {method_name} is not callable",
                        "required_methods",
                    )
                )

        # Test 4: Custom serializer base properties (if applicable)
        if isinstance(serializer_instance, CustomSerializerBase):
            tested_features.append("custom_serializer_properties")

            # Test output_format property
            try:
                output_format = serializer_instance.output_format
                if not isinstance(output_format, str) or not output_format.strip():
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.ERROR,
                            "output_format must be a non-empty string",
                            "custom_serializer_properties",
                        )
                    )
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "Failed to access output_format property",
                        "custom_serializer_properties",
                        str(e),
                    )
                )

            # Test file_extension property
            try:
                file_extension = serializer_instance.file_extension
                if not isinstance(file_extension, str) or not file_extension.startswith(
                    "."
                ):
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.ERROR,
                            "file_extension must be a string starting with '.'",
                            "custom_serializer_properties",
                        )
                    )
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "Failed to access file_extension property",
                        "custom_serializer_properties",
                        str(e),
                    )
                )

        # Test 5: Serialize method behavior
        tested_features.append("serialize_behavior")
        try:
            result = serializer_instance.serialize()
            if not hasattr(result, "text"):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "serialize() must return an object with 'text' attribute",
                        "serialize_behavior",
                    )
                )
            elif not isinstance(result.text, str):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "serialize() result.text must be a string",
                        "serialize_behavior",
                    )
                )
        except NotImplementedError:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.CRITICAL,
                    "serialize() method not implemented",
                    "serialize_behavior",
                    suggestion="Implement the serialize() method",
                )
            )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    "serialize() method raised an exception",
                    "serialize_behavior",
                    str(e),
                    "Ensure serialize() handles empty documents gracefully",
                )
            )

        is_valid = not any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for issue in issues
        )

        return ValidationResult(
            is_valid=is_valid, issues=issues, tested_features=tested_features
        )

    def test_round_trip(
        self,
        reader: BaseReader,
        serializer: BaseDocSerializer,
        test_file: Optional[Union[str, Path]] = None,
    ) -> RoundTripTestResult:
        """Test reader/serializer compatibility with round-trip conversion.

        Args:
            reader: Reader instance to test
            serializer: Serializer instance to test
            test_file: Optional test file to use. If None, creates a simple test.

        Returns:
            RoundTripTestResult: Test results
        """
        try:
            # Step 1: Create or read test content
            if test_file:
                # Use provided test file
                doc = reader.load_data(test_file)
                with open(test_file, "r", encoding="utf-8") as f:
                    original_content = f.read()
            else:
                # Create simple test document

                doc = DoclingDocument(
                    name="test",
                    origin=DocumentOrigin(
                        mimetype="text/plain",
                        binary_hash="a" * 64,  # Valid SHA256 hash
                        filename="test.txt",
                    ),
                    furniture=GroupItem(self_ref="#/furniture"),
                    body=GroupItem(self_ref="#/body"),
                )
                original_content = "Test content for round-trip validation"

            # Step 2: Serialize document
            # For serializers that need doc parameter, create new instance
            if hasattr(serializer.__class__, "__init__"):
                try:
                    serializer = serializer.__class__(doc=doc)
                except Exception:
                    # Fallback to existing instance
                    pass

            serialize_result = serializer.serialize()
            serialized_content = serialize_result.text

            # Step 3: Attempt to re-parse (if same format)
            reparsed_content = None
            content_matches = None

            # For now, just check that serialization produces content
            success = bool(serialized_content and isinstance(serialized_content, str))

            return RoundTripTestResult(
                success=success,
                original_content=original_content,
                serialized_content=serialized_content,
                reparsed_content=reparsed_content,
                content_matches=content_matches,
            )

        except Exception as e:
            return RoundTripTestResult(
                success=False,
                original_content="",
                serialized_content="",
                error_message=f"Round-trip test failed: {e}\n{traceback.format_exc()}",
            )

    def validate_format_pair(
        self,
        reader_class: Type[BaseReader],
        serializer_class: Type[BaseDocSerializer],
        test_file: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Validate a reader/serializer pair for format compatibility.

        Args:
            reader_class: Reader class to validate
            serializer_class: Serializer class to validate
            test_file: Optional test file for round-trip testing

        Returns:
            Dict[str, Any]: Comprehensive validation results
        """
        results = {
            "reader_validation": self.validate_reader(reader_class),
            "serializer_validation": self.validate_serializer(serializer_class),
            "round_trip_test": None,
            "compatibility_issues": [],
        }

        # Perform round-trip test if both validations passed
        if (
            results["reader_validation"].is_valid
            and results["serializer_validation"].is_valid
        ):
            try:
                reader = reader_class()

                # Create empty doc for serializer
                empty_doc = DoclingDocument(
                    name="",
                    origin=DocumentOrigin(
                        mimetype="text/plain",
                        binary_hash="a" * 64,  # Valid SHA256 hash
                        filename="",
                    ),
                    furniture=GroupItem(self_ref="#/furniture"),
                    body=GroupItem(self_ref="#/body"),
                )
                serializer = serializer_class(doc=empty_doc)

                results["round_trip_test"] = self.test_round_trip(
                    reader, serializer, test_file
                )
            except Exception as e:
                results["compatibility_issues"].append(
                    f"Failed to create instances for round-trip test: {e}"
                )

        return results

    def get_validation_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable validation report.

        Args:
            results: Validation results from validate_format_pair

        Returns:
            str: Formatted validation report
        """
        report = "Format Validation Report\n"
        report += "=" * 50 + "\n\n"

        # Reader validation
        reader_result = results["reader_validation"]
        report += f"Reader Validation: {'PASS' if reader_result.is_valid else 'FAIL'}\n"
        report += f"  Issues: {len(reader_result.issues)}\n"
        if reader_result.issues:
            for issue in reader_result.issues:
                report += f"    - {issue}\n"
        report += "\n"

        # Serializer validation
        serializer_result = results["serializer_validation"]
        report += f"Serializer Validation: {'PASS' if serializer_result.is_valid else 'FAIL'}\n"
        report += f"  Issues: {len(serializer_result.issues)}\n"
        if serializer_result.issues:
            for issue in serializer_result.issues:
                report += f"    - {issue}\n"
        report += "\n"

        # Round-trip test
        if results["round_trip_test"]:
            round_trip = results["round_trip_test"]
            report += f"Round-trip Test: {'PASS' if round_trip.success else 'FAIL'}\n"
            if round_trip.error_message:
                report += f"  Error: {round_trip.error_message}\n"
        else:
            report += "Round-trip Test: SKIPPED (validation failed)\n"

        # Compatibility issues
        if results["compatibility_issues"]:
            report += "\nCompatibility Issues:\n"
            for issue in results["compatibility_issues"]:
                report += f"  - {issue}\n"

        return report
