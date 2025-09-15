"""IO module containing readers and serializers with extensibility support."""

# Import extensibility components for easy access
from .format_registry import FormatRegistry, get_format_registry
from .validation import FormatValidator, ValidationResult, RoundTripTestResult
from .testing import CustomFormatTestBase, FormatTestSuite

# Import base classes for custom formats
from .readers.custom_reader_base import CustomReaderBase
from .serializers.custom_serializer_base import (
    CustomSerializerBase,
    CustomSerializerParams,
)

__all__ = [
    # Registry and plugin system
    "FormatRegistry",
    "get_format_registry",
    # Validation and testing
    "FormatValidator",
    "ValidationResult",
    "RoundTripTestResult",
    "CustomFormatTestBase",
    "FormatTestSuite",
    # Base classes for custom formats
    "CustomReaderBase",
    "CustomSerializerBase",
    "CustomSerializerParams",
]
