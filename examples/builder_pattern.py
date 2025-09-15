#!/usr/bin/env python3
"""Builder pattern examples for DocPivot v2.0.0

This example demonstrates the fluent builder API for creating
DocPivotEngine instances with various configurations.
"""

from pathlib import Path
from docpivot import DocPivotEngine, DocPivotEngineBuilder

# Optional imports
try:
    from docling_core.types import DoclingDocument
    HAS_DOCLING_CORE = True
except ImportError:
    HAS_DOCLING_CORE = False


def example_1_basic_builder():
    """Example 1: Basic builder usage."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Builder")
    print("=" * 60)

    # Build with defaults
    engine = DocPivotEngine.builder().build()

    print("✓ Created engine with builder (defaults)")
    print(f"  Default format: {engine.default_format}")
    print(f"  Pretty printing: {engine.lexical_config['pretty']}")


def example_2_pretty_print_builder():
    """Example 2: Builder with pretty printing."""
    print("\n" + "=" * 60)
    print("Example 2: Pretty Print Configuration")
    print("=" * 60)

    # Build with pretty printing
    engine = (DocPivotEngine.builder()
              .with_pretty_print(indent=4)
              .build())

    print("✓ Created engine with pretty printing:")
    print(f"  Pretty: {engine.lexical_config['pretty']}")
    print(f"  Indent: {engine.lexical_config['indent']} spaces")

    if HAS_DOCLING_CORE:
        doc = DoclingDocument(name="pretty_example")
        result = engine.convert_to_lexical(doc)
        print("\nSample output (first 200 chars):")
        print("-" * 40)
        print(result.content[:200])


def example_3_performance_builder():
    """Example 3: Performance-optimized configuration."""
    print("\n" + "=" * 60)
    print("Example 3: Performance Mode")
    print("=" * 60)

    # Build for performance
    engine = (DocPivotEngine.builder()
              .with_performance_mode()
              .build())

    print("✓ Created engine optimized for performance:")
    print(f"  Pretty printing: {engine.lexical_config['pretty']}")
    print(f"  Include metadata: {engine.lexical_config['include_metadata']}")
    print(f"  Handle images: {engine.lexical_config['handle_images']}")
    print("  → Minimal processing for maximum speed")


def example_4_debug_builder():
    """Example 4: Debug mode configuration."""
    print("\n" + "=" * 60)
    print("Example 4: Debug Mode")
    print("=" * 60)

    # Build for debugging
    engine = (DocPivotEngine.builder()
              .with_debug_mode()
              .build())

    print("✓ Created engine in debug mode:")
    print(f"  Pretty printing: {engine.lexical_config['pretty']}")
    print(f"  Include metadata: {engine.lexical_config['include_metadata']}")
    print(f"  Indent: {engine.lexical_config['indent']} spaces")
    print("  → Maximum information for troubleshooting")


def example_5_custom_builder():
    """Example 5: Custom configuration with builder."""
    print("\n" + "=" * 60)
    print("Example 5: Custom Configuration")
    print("=" * 60)

    # Build with specific features
    engine = (DocPivotEngine.builder()
              .with_images(include=True)
              .with_metadata(include=False)
              .with_default_format("lexical")
              .build())

    print("✓ Created engine with custom features:")
    print(f"  Images: {engine.lexical_config['handle_images']}")
    print(f"  Metadata: {engine.lexical_config['include_metadata']}")
    print(f"  Default format: {engine.default_format}")


def example_6_chained_builder():
    """Example 6: Complex chained configuration."""
    print("\n" + "=" * 60)
    print("Example 6: Chained Configuration")
    print("=" * 60)

    # Chain multiple configurations
    engine = (DocPivotEngine.builder()
              .with_pretty_print(indent=2)        # Pretty with 2-space indent
              .with_images(include=True)          # Include images
              .with_metadata(include=True)        # Include metadata
              .with_default_format("lexical")     # Set default format
              .build())

    print("✓ Created engine with chained configuration")
    print("\nConfiguration summary:")
    for key, value in engine.lexical_config.items():
        print(f"  {key}: {value}")


def example_7_preset_configurations():
    """Example 7: Using preset configurations."""
    print("\n" + "=" * 60)
    print("Example 7: Preset Configurations")
    print("=" * 60)

    from docpivot import (
        get_default_lexical_config,
        get_performance_config,
        get_debug_config,
        get_minimal_config,
        get_full_config,
        get_web_config
    )

    # Show available presets
    presets = {
        "Default": get_default_lexical_config(),
        "Performance": get_performance_config(),
        "Debug": get_debug_config(),
        "Minimal": get_minimal_config(),
        "Full": get_full_config(),
        "Web": get_web_config()
    }

    print("Available preset configurations:\n")
    for name, config in presets.items():
        print(f"{name} preset:")
        print(f"  Pretty: {config.get('pretty', False)}")
        print(f"  Metadata: {config.get('include_metadata', True)}")
        print(f"  Images: {config.get('handle_images', True)}")
        print()

    # Use a preset with builder
    engine = (DocPivotEngine.builder()
              .with_lexical_config(get_web_config())
              .with_pretty_print()  # Override specific setting
              .build())

    print("✓ Created engine with web preset + pretty printing")


def example_8_builder_vs_direct():
    """Example 8: Compare builder vs direct instantiation."""
    print("\n" + "=" * 60)
    print("Example 8: Builder vs Direct Instantiation")
    print("=" * 60)

    # Method 1: Direct instantiation with config dict
    engine1 = DocPivotEngine(
        lexical_config={
            "pretty": True,
            "indent": 4,
            "include_metadata": True
        }
    )
    print("Method 1 - Direct instantiation:")
    print("  engine = DocPivotEngine(lexical_config={...})")

    # Method 2: Builder pattern
    engine2 = (DocPivotEngine.builder()
               .with_pretty_print(indent=4)
               .with_metadata(include=True)
               .build())
    print("\nMethod 2 - Builder pattern:")
    print("  engine = DocPivotEngine.builder()")
    print("           .with_pretty_print(indent=4)")
    print("           .with_metadata(include=True)")
    print("           .build()")

    print("\n✓ Both methods create equivalent engines")
    print("  Builder provides better IDE support and discoverability")


def example_9_conditional_builder():
    """Example 9: Conditional configuration with builder."""
    print("\n" + "=" * 60)
    print("Example 9: Conditional Configuration")
    print("=" * 60)

    # Build configuration based on conditions
    is_development = True
    needs_images = False
    output_format = "lexical"

    # Start builder
    builder = DocPivotEngine.builder()

    # Apply conditional configuration
    if is_development:
        builder = builder.with_debug_mode()
        print("✓ Debug mode enabled (development)")

    if needs_images:
        builder = builder.with_images(include=True)
        print("✓ Image handling enabled")
    else:
        builder = builder.with_images(include=False)
        print("✓ Image handling disabled")

    # Set format
    builder = builder.with_default_format(output_format)

    # Build the engine
    engine = builder.build()

    print(f"\n✓ Built engine with conditional config:")
    print(f"  Debug: {is_development}")
    print(f"  Images: {needs_images}")
    print(f"  Format: {output_format}")


def main():
    """Run all builder examples."""
    print("\n" + "=" * 60)
    print("DocPivot v2.0.0 - Builder Pattern Examples")
    print("=" * 60)

    example_1_basic_builder()
    example_2_pretty_print_builder()
    example_3_performance_builder()
    example_4_debug_builder()
    example_5_custom_builder()
    example_6_chained_builder()
    example_7_preset_configurations()
    example_8_builder_vs_direct()
    example_9_conditional_builder()

    print("\n" + "=" * 60)
    print("Builder Pattern Benefits:")
    print("=" * 60)
    print("• Fluent API for readable configuration")
    print("• IDE autocomplete support")
    print("• Chainable method calls")
    print("• Type-safe configuration")
    print("• Easy preset configurations")
    print("• Conditional configuration support")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()