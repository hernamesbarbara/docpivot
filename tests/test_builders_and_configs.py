"""Tests for builders, configurations, and defaults."""

from docpivot import (
    DocPivotEngine,
    DocPivotEngineBuilder,
    get_debug_config,
    get_default_lexical_config,
    get_full_config,
    get_minimal_config,
    get_performance_config,
    get_web_config,
)


class TestConfigurationPresets:
    """Test configuration preset functions."""

    def test_default_config_structure(self):
        """Test default config has expected structure."""
        config = get_default_lexical_config()

        # Check required keys
        assert "pretty" in config
        assert "indent" in config
        assert "handle_tables" in config
        assert "handle_lists" in config
        assert "handle_images" in config
        assert "include_metadata" in config

        # Check default values
        assert config["pretty"] is False
        assert config["indent"] == 2
        assert config["handle_tables"] is True

    def test_performance_config_optimized(self):
        """Test performance config is optimized for speed."""
        config = get_performance_config()

        # Performance mode should disable expensive features
        assert config["pretty"] is False
        assert config["include_metadata"] is False
        assert config["handle_images"] is False

    def test_debug_config_verbose(self):
        """Test debug config provides maximum information."""
        config = get_debug_config()

        # Debug mode should enable all features
        assert config["pretty"] is True
        assert config["indent"] == 4
        assert config["include_metadata"] is True
        assert config["handle_images"] is True

    def test_minimal_config(self):
        """Test minimal config for smallest output."""
        config = get_minimal_config()

        # Should disable most features
        assert config["pretty"] is False
        assert config["include_metadata"] is False
        assert config["handle_images"] is False

    def test_full_config(self):
        """Test full config includes everything."""
        config = get_full_config()

        # Should enable most features
        assert config["include_metadata"] is True
        assert config["handle_images"] is True
        assert config["handle_tables"] is True

    def test_web_config(self):
        """Test web config optimized for web applications."""
        config = get_web_config()

        # Web mode should have sensible defaults
        assert "pretty" in config
        assert "handle_tables" in config
        assert "handle_lists" in config


class TestDocPivotEngineBuilder:
    """Test the builder pattern implementation."""

    def test_builder_creates_engine(self):
        """Test builder creates DocPivotEngine instance."""
        builder = DocPivotEngineBuilder()
        engine = builder.build()
        assert isinstance(engine, DocPivotEngine)

    def test_builder_fluent_interface(self):
        """Test builder methods return self for chaining."""
        builder = DocPivotEngineBuilder()

        result = builder.with_pretty_print()
        assert result is builder

        result = builder.with_images()
        assert result is builder

        result = builder.with_metadata()
        assert result is builder

    def test_builder_with_pretty_print(self):
        """Test pretty print configuration."""
        engine = DocPivotEngineBuilder().with_pretty_print(indent=3).build()

        assert engine.lexical_config["pretty"] is True
        assert engine.lexical_config["indent"] == 3

    def test_builder_with_images(self):
        """Test image handling configuration."""
        # Test enabling images
        engine = DocPivotEngineBuilder().with_images(include=True).build()
        assert engine.lexical_config["handle_images"] is True

        # Test disabling images
        engine = DocPivotEngineBuilder().with_images(include=False).build()
        assert engine.lexical_config["handle_images"] is False

    def test_builder_with_metadata(self):
        """Test metadata inclusion configuration."""
        # Test enabling metadata
        engine = DocPivotEngineBuilder().with_metadata(include=True).build()
        assert engine.lexical_config["include_metadata"] is True

        # Test disabling metadata
        engine = DocPivotEngineBuilder().with_metadata(include=False).build()
        assert engine.lexical_config["include_metadata"] is False

    def test_builder_with_default_format(self):
        """Test setting default output format."""
        engine = DocPivotEngineBuilder().with_default_format("lexical").build()
        assert engine.default_format == "lexical"

        engine = DocPivotEngineBuilder().with_default_format("json").build()
        assert engine.default_format == "json"

    def test_builder_performance_mode(self):
        """Test performance mode applies correct config."""
        engine = DocPivotEngineBuilder().with_performance_mode().build()

        # Should use performance config
        assert engine.lexical_config["pretty"] is False
        assert engine.lexical_config["include_metadata"] is False

    def test_builder_debug_mode(self):
        """Test debug mode applies correct config."""
        engine = DocPivotEngineBuilder().with_debug_mode().build()

        # Should use debug config
        assert engine.lexical_config["pretty"] is True
        assert engine.lexical_config["include_metadata"] is True

    def test_builder_with_custom_config(self):
        """Test builder with completely custom config."""
        custom_config = {"pretty": True, "indent": 8, "custom_field": "custom_value"}

        engine = DocPivotEngineBuilder().with_lexical_config(custom_config).build()

        assert engine.lexical_config["pretty"] is True
        assert engine.lexical_config["indent"] == 8
        assert engine.lexical_config.get("custom_field") == "custom_value"

    def test_builder_chaining_complex(self):
        """Test complex chaining of builder methods."""
        engine = (
            DocPivotEngineBuilder()
            .with_performance_mode()  # Start with performance
            .with_pretty_print()  # Override pretty print
            .with_images(False)  # Explicitly disable images
            .with_metadata(True)  # Enable metadata
            .with_default_format("lexical")
            .build()
        )

        # Pretty should be True (overridden)
        assert engine.lexical_config["pretty"] is True
        # Images should be False (explicit)
        assert engine.lexical_config["handle_images"] is False
        # Metadata should be True (overridden)
        assert engine.lexical_config["include_metadata"] is True
        # Format should be lexical
        assert engine.default_format == "lexical"

    def test_builder_static_method_access(self):
        """Test accessing builder via DocPivotEngine.builder()."""
        engine = DocPivotEngine.builder().build()
        assert isinstance(engine, DocPivotEngine)

        # Test with configuration
        engine = DocPivotEngine.builder().with_pretty_print().build()
        assert engine.lexical_config["pretty"] is True
