# DocPivot Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using DocPivot.

## Common Issues

### 1. File Loading Issues

#### "UnsupportedFormatError" when loading files

**Problem**: DocPivot cannot determine the file format or no reader supports it.

**Symptoms**:
```
UnsupportedFormatError: Unsupported file format: .json (mydocument.json)
```

**Solutions**:

1. **Check file extension**: Ensure your file has the correct extension:
   - Use `.docling.json` for Docling JSON files
   - Use `.lexical.json` for Lexical JSON files
   - Avoid generic `.json` extensions

2. **Verify file content**: Make sure the file content matches the expected format:
   ```python
   # Check if it's a valid Docling JSON file
   import json
   with open("myfile.json", 'r') as f:
       data = json.load(f)
       print(data.get("schema_name"))  # Should be "DoclingDocument"
   ```

3. **Use explicit reader selection**:
   ```python
   from docpivot.io.readers import DoclingJsonReader, LexicalJsonReader
   
   # Try specific readers
   try:
       reader = DoclingJsonReader()
       if reader.detect_format("myfile.json"):
           doc = reader.load_data("myfile.json")
   except:
       reader = LexicalJsonReader()
       doc = reader.load_data("myfile.json")
   ```

#### "FileNotFoundError" or path issues

**Problem**: DocPivot cannot find the specified file.

**Solutions**:

1. **Verify file paths**: Use absolute paths or ensure correct relative paths:
   ```python
   from pathlib import Path
   
   # Use absolute path
   file_path = Path("/full/path/to/document.docling.json").resolve()
   
   # Verify file exists
   if not file_path.exists():
       print(f"File not found: {file_path}")
   ```

2. **Check current working directory**:
   ```python
   import os
   print(f"Current directory: {os.getcwd()}")
   print(f"Files in directory: {os.listdir('.')}")
   ```

### 2. Serialization Issues

#### "Invalid JSON output" from Lexical serializer

**Problem**: LexicalDocSerializer produces malformed JSON.

**Diagnosis**:
```python
import json
from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer

serializer = LexicalDocSerializer(doc=doc)
result = serializer.serialize()

# Validate JSON
try:
    parsed = json.loads(result.text)
    print("✓ Valid JSON")
except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON: {e}")
    print(f"Error at position {e.pos}")
    print(f"Context: {result.text[max(0, e.pos-50):e.pos+50]}")
```

**Solutions**:

1. **Use indented output for debugging**:
   ```python
   from docpivot.io.serializers.lexicaldocserializer import LexicalParams
   
   params = LexicalParams(indent_json=True)
   serializer = LexicalDocSerializer(doc=doc, params=params)
   result = serializer.serialize()
   ```

2. **Check document structure**:
   ```python
   print(f"Document texts: {len(doc.texts)}")
   print(f"Document tables: {len(doc.tables)}")
   print(f"Document pictures: {len(doc.pictures)}")
   
   # Check for empty or malformed content
   for i, text in enumerate(doc.texts):
       if not text.text or not text.text.strip():
           print(f"Warning: Empty text at index {i}")
   ```

#### Serialization produces empty or minimal output

**Problem**: Output is much smaller than expected or contains minimal content.

**Diagnosis**:
```python
# Check document content before serialization
def diagnose_document(doc):
    print(f"Document name: {doc.name}")
    print(f"Total text items: {len(doc.texts)}")
    print(f"Total characters: {sum(len(t.text) for t in doc.texts)}")
    
    if doc.texts:
        print(f"First text sample: {doc.texts[0].text[:100]}...")
    
    # Check for structured content
    print(f"Tables: {len(doc.tables)}")
    print(f"Pictures: {len(doc.pictures)}")
    print(f"Groups: {len(doc.groups)}")

diagnose_document(doc)
```

**Solutions**:

1. **Verify source document quality**: Ensure the input document contains meaningful content
2. **Check serializer configuration**: Some serializers filter content based on parameters
3. **Try different serialization formats** to compare outputs

### 3. Performance Issues

#### Slow document loading

**Problem**: Document loading takes excessive time.

**Solutions**:

1. **Profile the loading process**:
   ```python
   import time
   
   start_time = time.time()
   doc = load_document("large_file.docling.json")
   duration = time.time() - start_time
   print(f"Loading took: {duration:.2f} seconds")
   ```

2. **Check file size and complexity**:
   ```python
   from pathlib import Path
   
   file_path = Path("large_file.docling.json")
   size_mb = file_path.stat().st_size / (1024 * 1024)
   print(f"File size: {size_mb:.2f} MB")
   ```

3. **Use streaming approach for very large files**: See [performance optimization example](../examples/advanced_usage/performance_optimization.py)

#### High memory usage

**Problem**: DocPivot uses more memory than expected.

**Solutions**:

1. **Monitor memory usage**:
   ```python
   import psutil
   import os
   
   process = psutil.Process(os.getpid())
   memory_mb = process.memory_info().rss / (1024 * 1024)
   print(f"Memory usage: {memory_mb:.2f} MB")
   ```

2. **Use compact serialization options**:
   ```python
   from docpivot.io.serializers.lexicaldocserializer import LexicalParams
   
   # Memory-efficient configuration
   params = LexicalParams(
       indent_json=False,
       include_metadata=False,
       preserve_formatting=False
   )
   ```

3. **Clean up objects explicitly**:
   ```python
   import gc
   
   # After processing
   del doc
   del serializer
   del result
   gc.collect()
   ```

### 4. Import and Installation Issues

#### "ModuleNotFoundError" for docling-core

**Problem**: DocPivot dependencies are not properly installed.

**Solutions**:

1. **Verify installation**:
   ```bash
   pip show docpivot
   pip show docling-core
   ```

2. **Reinstall with dependencies**:
   ```bash
   pip uninstall docpivot docling-core
   pip install docpivot
   ```

3. **Check Python environment**:
   ```python
   import sys
   print(f"Python version: {sys.version}")
   print(f"Python path: {sys.executable}")
   ```

#### Version compatibility issues

**Problem**: Incompatible versions of DocPivot and docling-core.

**Solutions**:

1. **Check version compatibility**:
   ```python
   import docpivot
   import docling_core
   
   print(f"DocPivot version: {docpivot.__version__}")
   print(f"Docling-core version: {docling_core.__version__}")
   ```

2. **Update to latest compatible versions**:
   ```bash
   pip install --upgrade docpivot
   ```

### 5. Configuration and Parameter Issues

#### "ConfigurationError" with serializer parameters

**Problem**: Invalid parameters passed to serializers.

**Diagnosis**:
```python
# Check supported parameters for a serializer
from docpivot.io.serializers import SerializerProvider

provider = SerializerProvider()
try:
    serializer = provider.get_serializer(
        "markdown",
        doc=doc,
        invalid_param="value"
    )
except Exception as e:
    print(f"Configuration error: {e}")
```

**Solutions**:

1. **Check parameter documentation**: Refer to class docstrings for valid parameters
2. **Use parameter objects**: Use structured parameter classes where available:
   ```python
   from docling_core.transforms.serializer.markdown import MarkdownParams
   
   params = MarkdownParams(image_placeholder="[Image]")
   serializer = MarkdownDocSerializer(doc=doc, params=params)
   ```

## Debugging Techniques

### 1. Enable Logging

```python
import logging
from docpivot.logging_config import get_logger

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = get_logger(__name__)

# Your DocPivot operations here
doc = load_document("file.docling.json")
```

### 2. Step-by-step Debugging

```python
# Break down the workflow for debugging
try:
    # Step 1: Load document
    print("Loading document...")
    doc = load_document("file.docling.json")
    print(f"✓ Document loaded: {doc.name}")
    
    # Step 2: Get serializer
    print("Getting serializer...")
    from docpivot.io.serializers import SerializerProvider
    provider = SerializerProvider()
    serializer = provider.get_serializer("markdown", doc=doc)
    print(f"✓ Serializer created: {type(serializer).__name__}")
    
    # Step 3: Serialize
    print("Serializing...")
    result = serializer.serialize()
    print(f"✓ Serialization complete: {len(result.text)} characters")
    
except Exception as e:
    print(f"❌ Error at step: {e}")
    import traceback
    traceback.print_exc()
```

### 3. Document Structure Analysis

```python
def analyze_document_structure(doc):
    """Analyze document structure for debugging."""
    print("=== Document Structure Analysis ===")
    print(f"Name: {doc.name}")
    print(f"Origin: {getattr(doc, 'origin', 'Unknown')}")
    
    # Text analysis
    print(f"\nText Items: {len(doc.texts)}")
    if doc.texts:
        total_chars = sum(len(text.text) for text in doc.texts)
        avg_chars = total_chars / len(doc.texts)
        print(f"  Total characters: {total_chars}")
        print(f"  Average per item: {avg_chars:.1f}")
        
        # Show samples
        for i, text in enumerate(doc.texts[:3]):
            preview = text.text[:100] + "..." if len(text.text) > 100 else text.text
            print(f"  Text {i}: {preview}")
    
    # Structure analysis
    print(f"\nStructural Elements:")
    print(f"  Tables: {len(doc.tables)}")
    print(f"  Pictures: {len(doc.pictures)}")
    print(f"  Groups: {len(doc.groups)}")
    
    return doc

# Usage
doc = load_document("file.docling.json")
analyze_document_structure(doc)
```

## Performance Optimization Tips

### 1. Document Caching

```python
# Load once, serialize multiple times
doc = load_document("large_file.docling.json")

formats = ["markdown", "html", "lexical"]
for fmt in formats:
    serializer = provider.get_serializer(fmt, doc=doc)
    result = serializer.serialize()
    # Process result...
```

### 2. Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor

def process_file(file_path):
    return load_and_serialize(file_path, "markdown")

files = ["file1.docling.json", "file2.docling.json"]

# Process in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_file, files))
```

### 3. Memory Management

```python
import gc

# Process large batch with explicit cleanup
for file_path in large_file_list:
    doc = load_document(file_path)
    result = serialize_document(doc)
    
    # Process result...
    
    # Clean up
    del doc
    del result
    gc.collect()
```

## Getting Help

If you continue to experience issues:

1. **Check the logs**: Enable debug logging to get detailed error information
2. **Review examples**: Look at working examples in the `examples/` directory
3. **Simplify the problem**: Try with minimal test cases
4. **Check versions**: Ensure you're using compatible versions of all dependencies
5. **Report bugs**: If you find a reproducible bug, please report it with:
   - DocPivot version
   - Python version and platform
   - Complete error messages
   - Minimal code example that reproduces the issue
   - Sample input files (if possible)

## Diagnostic Script

Use this script to collect diagnostic information:

```python
#!/usr/bin/env python3
"""DocPivot diagnostic script."""

import sys
import platform
import traceback

def collect_diagnostics():
    """Collect system and environment diagnostics."""
    print("=== DocPivot Diagnostics ===")
    
    # System information
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    
    # Package versions
    try:
        import docpivot
        print(f"DocPivot version: {docpivot.__version__}")
    except ImportError as e:
        print(f"DocPivot import error: {e}")
    
    try:
        import docling_core
        print(f"Docling-core version: {getattr(docling_core, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"Docling-core import error: {e}")
    
    # Test basic functionality
    print("\n=== Basic Functionality Test ===")
    try:
        from docpivot import load_document
        print("✓ DocPivot imports successful")
        
        # Test with a simple document if available
        test_files = [
            "data/json/2025-07-03-Test-PDF-Styles.docling.json",
            "sample.docling.json"
        ]
        
        for test_file in test_files:
            try:
                doc = load_document(test_file)
                print(f"✓ Successfully loaded: {test_file}")
                break
            except FileNotFoundError:
                print(f"Test file not found: {test_file}")
            except Exception as e:
                print(f"Error loading {test_file}: {e}")
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    collect_diagnostics()
```

Save this as `diagnostics.py` and run it to collect system information for troubleshooting.