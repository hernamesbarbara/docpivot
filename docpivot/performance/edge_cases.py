"""Edge case handling for performance optimization scenarios."""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Callable
from dataclasses import dataclass
from contextlib import contextmanager

from docling_core.types import DoclingDocument

from ..logging_config import get_logger
from .monitor import PerformanceConfig

logger = get_logger(__name__)

# Edge case thresholds
EMPTY_FILE_SIZE = 0
MINIMAL_FILE_SIZE = 10  # bytes
SMALL_FILE_SIZE = 1024  # 1KB
LARGE_FILE_SIZE = 100 * 1024 * 1024  # 100MB
EXTREME_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
MAX_MEMORY_USAGE_MB = 2048  # 2GB
MAX_PROCESSING_TIME_SEC = 300  # 5 minutes


@dataclass
class EdgeCaseConfig:
    """Configuration for edge case handling."""
    
    max_file_size_bytes: int = EXTREME_FILE_SIZE
    max_memory_usage_mb: int = MAX_MEMORY_USAGE_MB
    max_processing_time_sec: int = MAX_PROCESSING_TIME_SEC
    enable_recovery: bool = True
    enable_partial_processing: bool = True
    enable_fallback_modes: bool = True
    strict_validation: bool = False
    timeout_callback: Optional[Callable[[str], None]] = None
    memory_warning_callback: Optional[Callable[[float], None]] = None


class EdgeCaseHandler:
    """Handler for edge cases in performance optimization scenarios."""
    
    def __init__(self, config: Optional[EdgeCaseConfig] = None):
        """Initialize edge case handler.
        
        Args:
            config: Edge case configuration
        """
        self.config = config or EdgeCaseConfig()
        self._processing_start_time = 0.0
        
    @contextmanager
    def handle_file_processing(self, file_path: Union[str, Path], operation: str = "file_processing"):
        """Context manager for file processing edge cases.
        
        Args:
            file_path: Path to file being processed
            operation: Name of the operation for logging
        """
        file_path = Path(file_path)
        self._processing_start_time = time.time()
        
        try:
            # Pre-processing validation
            self._validate_file_preconditions(file_path, operation)
            
            # Start monitoring
            with self._monitor_processing_limits(operation):
                yield
                
        except Exception as e:
            # Handle processing errors
            self._handle_processing_error(e, file_path, operation)
            raise
        finally:
            # Reset timing
            self._processing_start_time = 0.0
    
    def handle_empty_document(self, file_path: Union[str, Path]) -> DoclingDocument:
        """Handle empty or minimal documents gracefully.
        
        Args:
            file_path: Path to the empty document
            
        Returns:
            Minimal valid DoclingDocument
        """
        logger.warning(f"Creating minimal document for empty file: {file_path}")
        
        # Create minimal valid DoclingDocument structure
        minimal_doc = {
            "schema_name": "DoclingDocument",
            "version": "1.4.0", 
            "name": f"empty_document_{Path(file_path).stem}",
            "texts": [],
            "tables": [],
            "groups": [],
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified",
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified",
            },
            "origin": {
                "mimetype": "application/json",
                "filename": Path(file_path).name,
                "binary_hash": 0,
                "uri": None
            },
            "pictures": [],
            "key_value_items": [],
            "pages": {}
        }
        
        try:
            return DoclingDocument.model_validate(minimal_doc)
        except Exception as e:
            logger.error(f"Failed to create minimal document: {e}")
            raise
    
    def handle_malformed_json(self, content: str, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Attempt to recover from malformed JSON.
        
        Args:
            content: Raw file content
            file_path: Path to the file
            
        Returns:
            Recovered JSON data or raises exception
            
        Raises:
            ValueError: If recovery is not possible
        """
        if not self.config.enable_recovery:
            raise ValueError(f"Malformed JSON in {file_path} - recovery disabled")
        
        logger.warning(f"Attempting to recover malformed JSON from {file_path}")
        
        # Strategy 1: Try to fix common JSON issues
        try:
            recovered_content = self._attempt_json_repair(content)
            return json.loads(recovered_content)
        except Exception as e:
            logger.debug(f"JSON repair failed: {e}")
        
        # Strategy 2: Try to extract valid JSON subset
        if self.config.enable_partial_processing:
            try:
                partial_data = self._extract_partial_json(content, file_path)
                if partial_data:
                    logger.info(f"Recovered partial JSON from {file_path}")
                    return partial_data
            except Exception as e:
                logger.debug(f"Partial JSON extraction failed: {e}")
        
        # Strategy 3: Create minimal structure if possible
        try:
            return self._create_minimal_json_structure(file_path)
        except Exception as e:
            logger.debug(f"Minimal structure creation failed: {e}")
        
        raise ValueError(f"Unable to recover JSON from {file_path}")
    
    def handle_memory_exhaustion(self, operation: str, memory_usage_mb: float):
        """Handle memory exhaustion scenarios.
        
        Args:
            operation: Current operation name
            memory_usage_mb: Current memory usage in MB
        """
        logger.critical(f"Memory exhaustion detected in {operation}: {memory_usage_mb:.2f} MB")
        
        if self.config.memory_warning_callback:
            self.config.memory_warning_callback(memory_usage_mb)
        
        if not self.config.enable_recovery:
            raise MemoryError(f"Memory exhaustion in {operation}")
        
        # Attempt memory recovery
        logger.info("Attempting memory recovery...")
        
        try:
            import gc
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")
            
            # Check if memory usage improved
            current_memory = self._get_current_memory_usage()
            if current_memory < memory_usage_mb * 0.8:  # 20% improvement
                logger.info(f"Memory recovery successful: {current_memory:.2f} MB")
                return
            
        except Exception as e:
            logger.warning(f"Memory recovery attempt failed: {e}")
        
        # If recovery doesn't help, raise error
        raise MemoryError(f"Unable to recover from memory exhaustion in {operation}")
    
    def handle_processing_timeout(self, operation: str, elapsed_sec: float):
        """Handle processing timeout scenarios.
        
        Args:
            operation: Current operation name  
            elapsed_sec: Time elapsed in seconds
        """
        logger.error(f"Processing timeout in {operation}: {elapsed_sec:.2f} seconds")
        
        if self.config.timeout_callback:
            self.config.timeout_callback(operation)
        
        if not self.config.enable_recovery:
            raise TimeoutError(f"Processing timeout in {operation}")
        
        # Check if we can enable fallback mode
        if self.config.enable_fallback_modes:
            logger.info(f"Attempting fallback processing for {operation}")
            # Return a signal that fallback should be attempted
            raise TimeoutError(f"FALLBACK_REQUIRED:{operation}")
        
        raise TimeoutError(f"Processing timeout in {operation}: {elapsed_sec:.2f}s")
    
    def handle_deeply_nested_structure(self, data: Dict[str, Any], max_depth: int = 100) -> Dict[str, Any]:
        """Handle deeply nested document structures.
        
        Args:
            data: Document data to check
            max_depth: Maximum allowed nesting depth
            
        Returns:
            Flattened or truncated data structure
        """
        try:
            depth = self._calculate_nesting_depth(data)
            if depth <= max_depth:
                return data
            
            logger.warning(f"Deep nesting detected (depth: {depth}), flattening structure")
            
            if self.config.enable_recovery:
                return self._flatten_nested_structure(data, max_depth)
            else:
                raise ValueError(f"Structure too deeply nested: {depth} > {max_depth}")
                
        except RecursionError:
            logger.error("Recursion limit exceeded in nested structure")
            if self.config.enable_recovery:
                return self._create_minimal_json_structure("deeply_nested_document")
            raise
    
    def handle_extremely_large_file(self, file_path: Path, size_bytes: int) -> Dict[str, Any]:
        """Handle extremely large files that exceed normal processing limits.
        
        Args:
            file_path: Path to the large file
            size_bytes: File size in bytes
            
        Returns:
            Processing strategy information
        """
        logger.warning(f"Extremely large file detected: {file_path} ({size_bytes:,} bytes)")
        
        if size_bytes > self.config.max_file_size_bytes:
            if not self.config.enable_recovery:
                raise ValueError(f"File too large: {size_bytes} > {self.config.max_file_size_bytes}")
            
            logger.info("Enabling extreme file processing mode")
            
            # Suggest chunked processing strategy
            return {
                "strategy": "chunked_processing",
                "chunk_size": min(50 * 1024 * 1024, self.config.max_file_size_bytes // 10),  # 50MB or 1/10th max
                "estimated_chunks": size_bytes // (50 * 1024 * 1024) + 1,
                "use_streaming": True,
                "use_memory_mapping": True,
                "enable_progress_tracking": True
            }
        
        # Large but manageable - suggest optimizations
        return {
            "strategy": "optimized_processing",
            "use_streaming": size_bytes > 100 * 1024 * 1024,  # 100MB
            "use_memory_mapping": size_bytes > 50 * 1024 * 1024,  # 50MB  
            "batch_size": max(100, 10000 - (size_bytes // (10 * 1024 * 1024))),  # Reduce batch size for larger files
            "enable_progress_tracking": size_bytes > 10 * 1024 * 1024  # 10MB
        }
    
    def handle_corrupted_document_structure(self, data: Dict[str, Any], file_path: Union[str, Path]) -> Dict[str, Any]:
        """Handle corrupted or invalid document structures.
        
        Args:
            data: Document data to validate and repair
            file_path: Path to the document
            
        Returns:
            Repaired document structure
        """
        logger.warning(f"Attempting to repair corrupted document structure from {file_path}")
        
        if not self.config.enable_recovery:
            raise ValueError(f"Corrupted document structure in {file_path}")
        
        # Create repaired structure
        repaired = {
            "schema_name": data.get("schema_name", "DoclingDocument"),
            "version": data.get("version", "1.4.0"),
            "name": data.get("name", f"repaired_document_{Path(file_path).stem}"),
            "texts": [],
            "tables": [],
            "groups": [],
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified",
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified",
            },
            "pictures": [],
            "key_value_items": [],
            "pages": {}
        }
        
        # Try to salvage texts
        try:
            texts = data.get("texts", [])
            if isinstance(texts, list):
                repaired["texts"] = [
                    text for text in texts 
                    if isinstance(text, dict) and text.get("text")
                ]
            logger.info(f"Salvaged {len(repaired['texts'])} text items")
        except Exception as e:
            logger.warning(f"Failed to salvage texts: {e}")
        
        # Try to salvage tables
        try:
            tables = data.get("tables", [])
            if isinstance(tables, list):
                repaired["tables"] = [
                    table for table in tables
                    if isinstance(table, dict) and table.get("data")
                ]
            logger.info(f"Salvaged {len(repaired['tables'])} table items")
        except Exception as e:
            logger.warning(f"Failed to salvage tables: {e}")
        
        # Try to repair body structure
        try:
            body = data.get("body", {})
            if isinstance(body, dict) and "children" in body:
                children = body.get("children", [])
                if isinstance(children, list):
                    # Validate and repair child references
                    valid_children = []
                    for i, child in enumerate(children):
                        if isinstance(child, dict) and child.get("cref"):
                            # Basic validation of cref format
                            cref = child["cref"]
                            if isinstance(cref, str) and cref.startswith("#/"):
                                valid_children.append(child)
                    
                    repaired["body"]["children"] = valid_children
                    logger.info(f"Repaired body with {len(valid_children)} valid children")
        except Exception as e:
            logger.warning(f"Failed to repair body structure: {e}")
        
        # Add origin if missing
        if "origin" not in repaired:
            repaired["origin"] = {
                "mimetype": "application/json",
                "filename": Path(file_path).name,
                "binary_hash": 0,
                "uri": None
            }
        
        return repaired
    
    def _validate_file_preconditions(self, file_path: Path, operation: str):
        """Validate file preconditions before processing."""
        # Check file existence
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size
        size_bytes = file_path.stat().st_size
        
        if size_bytes == EMPTY_FILE_SIZE:
            logger.warning(f"Empty file detected: {file_path}")
            if not self.config.enable_recovery:
                raise ValueError(f"Empty file: {file_path}")
        
        elif size_bytes > self.config.max_file_size_bytes:
            logger.warning(f"File exceeds size limit: {size_bytes} > {self.config.max_file_size_bytes}")
            if not self.config.enable_recovery:
                raise ValueError(f"File too large: {file_path}")
        
        # Check file permissions
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"No read permission for file: {file_path}")
    
    @contextmanager
    def _monitor_processing_limits(self, operation: str):
        """Monitor processing limits during operation."""
        try:
            yield
        except Exception as e:
            # Check if this is a timeout or memory error
            elapsed = time.time() - self._processing_start_time
            
            if elapsed > self.config.max_processing_time_sec:
                self.handle_processing_timeout(operation, elapsed)
            
            current_memory = self._get_current_memory_usage()
            if current_memory > self.config.max_memory_usage_mb:
                self.handle_memory_exhaustion(operation, current_memory)
            
            raise
    
    def _handle_processing_error(self, error: Exception, file_path: Path, operation: str):
        """Handle processing errors with context."""
        error_type = type(error).__name__
        logger.error(f"Processing error in {operation} for {file_path}: {error_type}: {error}")
        
        # Add contextual information
        elapsed = time.time() - self._processing_start_time
        current_memory = self._get_current_memory_usage()
        
        context = {
            "operation": operation,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "elapsed_time_sec": elapsed,
            "memory_usage_mb": current_memory,
            "error_type": error_type,
            "recovery_enabled": self.config.enable_recovery
        }
        
        logger.debug(f"Error context: {context}")
    
    def _attempt_json_repair(self, content: str) -> str:
        """Attempt basic JSON repairs."""
        # Remove common JSON issues
        repaired = content.strip()
        
        # Fix trailing commas
        import re
        repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
        
        # Ensure proper string quoting (basic)
        repaired = re.sub(r'([{\[,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', repaired)
        
        # Fix missing closing brackets (very basic)
        open_braces = repaired.count('{')
        close_braces = repaired.count('}')
        if open_braces > close_braces:
            repaired += '}' * (open_braces - close_braces)
        
        open_brackets = repaired.count('[')
        close_brackets = repaired.count(']')
        if open_brackets > close_brackets:
            repaired += ']' * (open_brackets - close_brackets)
        
        return repaired
    
    def _extract_partial_json(self, content: str, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Extract partial valid JSON from corrupted content."""
        try:
            # Find the largest valid JSON object
            for end_pos in range(len(content) - 1, 0, -100):  # Check every 100 chars backward
                try:
                    partial_content = content[:end_pos]
                    # Try to balance brackets
                    balanced = self._balance_json_brackets(partial_content)
                    return json.loads(balanced)
                except:
                    continue
        except Exception:
            pass
        
        return None
    
    def _balance_json_brackets(self, content: str) -> str:
        """Balance JSON brackets and braces."""
        # Count unmatched brackets
        brace_count = 0
        bracket_count = 0
        
        for char in content:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
        
        # Add missing closing brackets
        result = content
        if brace_count > 0:
            result += '}' * brace_count
        if bracket_count > 0:
            result += ']' * bracket_count
        
        return result
    
    def _create_minimal_json_structure(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Create minimal valid JSON structure."""
        return {
            "schema_name": "DoclingDocument",
            "version": "1.4.0",
            "name": f"recovered_document_{Path(file_path).stem}",
            "texts": [],
            "tables": [],
            "groups": [],
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified",
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified",
            },
            "origin": {
                "mimetype": "application/json",
                "filename": Path(file_path).name,
                "binary_hash": 0,
                "uri": None
            },
            "pictures": [],
            "key_value_items": [],
            "pages": {}
        }
    
    def _calculate_nesting_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth of an object."""
        if current_depth > 1000:  # Prevent infinite recursion
            return current_depth
        
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._calculate_nesting_depth(value, current_depth + 1)
                for value in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._calculate_nesting_depth(item, current_depth + 1)
                for item in obj
            )
        else:
            return current_depth
    
    def _flatten_nested_structure(self, data: Dict[str, Any], max_depth: int) -> Dict[str, Any]:
        """Flatten deeply nested structure to specified max depth."""
        def _flatten_recursive(obj: Any, depth: int) -> Any:
            if depth >= max_depth:
                # Convert to string representation at max depth
                if isinstance(obj, (dict, list)):
                    return f"<truncated at depth {max_depth}>"
                return obj
            
            if isinstance(obj, dict):
                return {
                    key: _flatten_recursive(value, depth + 1)
                    for key, value in obj.items()
                }
            elif isinstance(obj, list):
                return [
                    _flatten_recursive(item, depth + 1)
                    for item in obj
                ]
            else:
                return obj
        
        return _flatten_recursive(data, 0)
    
    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0