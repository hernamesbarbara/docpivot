"""Smart defaults for DocPivot operations."""

from typing import Any


def get_default_lexical_config() -> dict[str, Any]:
    """Get default configuration for Lexical JSON serialization.

    Returns configuration that handles 90% of use cases.

    Returns:
        Dict containing default Lexical serialization options
    """
    return {
        "pretty": False,  # Compact by default
        "indent": 2,      # If pretty=True
        "include_metadata": True,
        "preserve_formatting": True,
        "handle_tables": True,
        "handle_lists": True,
        "handle_images": False,  # Skip images by default for smaller output
        "include_headers": True,
        "include_paragraphs": True,
    }


def get_performance_config() -> dict[str, Any]:
    """Get configuration optimized for performance.

    Minimizes output size and processing overhead.

    Returns:
        Dict containing performance-optimized configuration
    """
    return {
        "pretty": False,
        "include_metadata": False,
        "handle_images": False,
        "include_debug_info": False,
        "validate_output": False,
    }


def get_debug_config() -> dict[str, Any]:
    """Get configuration for debugging/development.

    Maximizes information output for troubleshooting.

    Returns:
        Dict containing debug-friendly configuration
    """
    return {
        "pretty": True,
        "indent": 4,
        "include_metadata": True,
        "include_debug_info": True,
        "validate_output": True,
        "handle_images": True,
        "include_raw_text": True,
    }


def get_minimal_config() -> dict[str, Any]:
    """Get minimal configuration for text-only output.

    Returns:
        Dict containing minimal configuration options
    """
    return {
        "pretty": False,
        "include_metadata": False,
        "handle_images": False,
        "handle_tables": False,
        "handle_lists": True,
        "include_headers": True,
        "include_paragraphs": True,
    }


def get_full_config() -> dict[str, Any]:
    """Get configuration with all features enabled.

    Returns:
        Dict containing full-featured configuration
    """
    return {
        "pretty": True,
        "indent": 2,
        "include_metadata": True,
        "preserve_formatting": True,
        "handle_tables": True,
        "handle_lists": True,
        "handle_images": True,
        "include_headers": True,
        "include_paragraphs": True,
        "include_footnotes": True,
        "include_raw_text": True,
    }


def get_web_config() -> dict[str, Any]:
    """Get configuration optimized for web display.

    Returns:
        Dict containing web-optimized configuration
    """
    return {
        "pretty": False,  # Minimize size for transfer
        "include_metadata": True,
        "handle_tables": True,
        "handle_lists": True,
        "handle_images": True,  # Include for rich display
        "include_headers": True,
        "include_paragraphs": True,
        "sanitize_html": True,  # Safety for web display
    }


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries.

    Later configs override earlier ones.

    Args:
        *configs: Variable number of configuration dicts to merge

    Returns:
        Merged configuration dictionary
    """
    result = {}
    for config in configs:
        result.update(config)
    return result
