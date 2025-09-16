"""Integration tests for DocPivot with real files."""

import json
from pathlib import Path

import pytest

from docpivot import ConversionResult, DocPivotEngine


class TestIntegrationWithRealFiles:
    """Test with real data files from data/ directory."""

    def test_convert_docling_json_file(self, sample_docling_json_path):
        """Test converting real Docling JSON file."""
        if not sample_docling_json_path or not sample_docling_json_path.exists():
            pytest.skip("No sample Docling JSON file available")

        engine = DocPivotEngine()
        result = engine.convert_file(sample_docling_json_path)

        assert isinstance(result, ConversionResult)
        assert result.format == "lexical"
        assert result.content
        assert "root" in json.loads(result.content)

    def test_round_trip_conversion(self, sample_docling_json_path, temp_output_dir):
        """Test converting Docling JSON to Lexical and saving."""
        if not sample_docling_json_path or not sample_docling_json_path.exists():
            pytest.skip("No sample Docling JSON file available")

        engine = DocPivotEngine()
        output_path = temp_output_dir / "output.lexical.json"

        # Convert and save
        result = engine.convert_file(sample_docling_json_path, output_path=output_path)

        assert output_path.exists()
        assert result.metadata.get("output_path") == str(output_path)

        # Verify saved content is valid JSON
        with Path(output_path).open() as f:
            lexical_data = json.load(f)
            assert "root" in lexical_data

    @pytest.mark.skipif(not Path("data/pdf").exists(), reason="PDF test data not available")
    def test_pdf_conversion_requires_docling(self, sample_pdf_path):
        """Test PDF conversion (requires optional docling package)."""
        if not sample_pdf_path or not sample_pdf_path.exists():
            pytest.skip("No sample PDF file available")

        engine = DocPivotEngine()

        try:
            import docling  # noqa: F401

            # If docling is available, test conversion
            result = engine.convert_pdf(sample_pdf_path)
            assert isinstance(result, ConversionResult)
            assert result.format == "lexical"
        except ImportError:
            # If docling not available, should raise informative error
            with pytest.raises(ImportError, match="docling"):
                engine.convert_pdf(sample_pdf_path)


class TestEndToEndWorkflows:
    """Test complete workflows."""

    def test_batch_processing(self, test_data_dir, temp_output_dir):
        """Test batch processing multiple files."""
        json_dir = test_data_dir / "json"
        if not json_dir.exists():
            pytest.skip("No test data directory")

        docling_files = list(json_dir.glob("*.docling.json"))
        if not docling_files:
            pytest.skip("No Docling JSON files to process")

        engine = DocPivotEngine()
        results = []

        for input_file in docling_files[:2]:  # Process max 2 files for speed
            output_file = temp_output_dir / f"{input_file.stem}.lexical.json"
            result = engine.convert_file(input_file, output_path=output_file)
            results.append(result)
            assert output_file.exists()

        assert len(results) > 0
        assert all(r.format == "lexical" for r in results)

    def test_different_configs_same_file(self, sample_docling_json_path):
        """Test converting same file with different configurations."""
        if not sample_docling_json_path or not sample_docling_json_path.exists():
            pytest.skip("No sample Docling JSON file available")

        # Performance mode - minimal output
        perf_engine = DocPivotEngine.builder().with_performance_mode().build()
        perf_result = perf_engine.convert_file(sample_docling_json_path)

        # Debug mode - full output
        debug_engine = DocPivotEngine.builder().with_debug_mode().build()
        debug_result = debug_engine.convert_file(sample_docling_json_path)

        # Debug output should be larger (due to pretty printing and metadata)
        assert len(debug_result.content) >= len(perf_result.content)

        # Both should be valid JSON
        json.loads(perf_result.content)
        json.loads(debug_result.content)
