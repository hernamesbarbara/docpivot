"""Optimized LexicalDocSerializer with performance enhancements for large documents."""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Protocol, Callable, Generator
from io import StringIO
import gc
from contextlib import contextmanager

from docling_core.transforms.serializer.base import SerializationResult
from docling_core.types import DoclingDocument
from docling_core.types.doc.document import (
    GroupItem, OrderedList, SectionHeaderItem, TextItem, TableItem,
    UnorderedList, PictureItem,
)

from .lexicaldocserializer import LexicalParams, ComponentSerializer, ImageSerializer
from ..readers.exceptions import ValidationError, TransformationError, ConfigurationError
from docpivot.validation import validate_docling_document
from docpivot.logging_config import get_logger, PerformanceLogger, log_exception_with_context
from docpivot.performance import PerformanceConfig

logger = get_logger(__name__)
perf_logger = PerformanceLogger(logger)

# Type aliases
TextItemType = Union[SectionHeaderItem, TextItem]
GroupItemType = Union[OrderedList, UnorderedList, GroupItem]

# Performance optimization constants
BATCH_SIZE = 1000  # Process elements in batches
STREAMING_THRESHOLD_ELEMENTS = 5000  # Use streaming for documents with >5000 elements
MEMORY_EFFICIENT_THRESHOLD_MB = 200  # Switch to memory-efficient mode above this
JSON_BUFFER_SIZE = 64 * 1024  # 64KB buffer for JSON generation

# Lexical constants from original
LEXICAL_VERSION = 1
DEFAULT_DETAIL = 0
DEFAULT_FORMAT = 0
DEFAULT_INDENT = 0
HEADER_STATE_VALUE = 1
MIN_HEADING_LEVEL = 1
MAX_HEADING_LEVEL = 6
DEFAULT_HEADING_TAG = "h1"
TEXT_DIRECTION_LTR = "ltr"
DEFAULT_MODE = "normal"
DEFAULT_STYLE = ""
JSON_INDENT_SIZE = 2

# Node types
NODE_TYPE_ROOT = "root"
NODE_TYPE_TEXT = "text"
NODE_TYPE_HEADING = "heading"
NODE_TYPE_PARAGRAPH = "paragraph"
NODE_TYPE_TABLE = "table"
NODE_TYPE_TABLE_ROW = "tablerow"
NODE_TYPE_TABLE_CELL = "tablecell"
NODE_TYPE_LIST = "list"
NODE_TYPE_LIST_ITEM = "listitem"
NODE_TYPE_LINK = "link"
NODE_TYPE_IMAGE = "image"

# List types
LIST_TYPE_ORDERED = "ordered"
LIST_TYPE_UNORDERED = "unordered"
LIST_TAG_ORDERED = "ol"
LIST_TAG_UNORDERED = "ul"

# Reference parsing
MIN_REF_PARTS = 3
REF_ELEMENT_TYPE_INDEX = 1
REF_ELEMENT_INDEX = 2
ELEMENT_TYPE_TEXTS = "texts"
ELEMENT_TYPE_TABLES = "tables"
ELEMENT_TYPE_GROUPS = "groups"
ELEMENT_TYPE_PICTURES = "pictures"

# Text formatting
FORMAT_BOLD = 1
FORMAT_ITALIC = 2
FORMAT_UNDERLINE = 4
FORMAT_STRIKETHROUGH = 8


@dataclass
class OptimizedLexicalParams(LexicalParams):
    """Extended parameters for optimized Lexical serialization."""
    
    # Memory optimization options
    enable_streaming: bool = False  # Force streaming mode
    batch_size: int = BATCH_SIZE  # Elements per batch
    memory_efficient_mode: bool = False  # Reduce memory usage
    
    # Performance tuning
    use_fast_json: bool = True  # Use fast JSON libraries
    buffer_size: int = JSON_BUFFER_SIZE  # JSON generation buffer size
    parallel_processing: bool = False  # Use parallel processing for large docs
    max_workers: int = 4  # Worker threads for parallel processing
    
    # Optimization toggles
    skip_validation: bool = False  # Skip document validation for performance
    optimize_text_formatting: bool = True  # Use optimized text processing
    cache_node_creation: bool = False  # Cache frequently created nodes
    
    # Progress tracking
    progress_callback: Optional[Callable[[float], None]] = None  # Progress updates


class OptimizedLexicalDocSerializer:
    """Performance-optimized serializer for converting DoclingDocument to Lexical JSON.
    
    Features:
    - Streaming serialization for large documents
    - Memory-efficient processing with batching
    - Fast JSON library selection
    - Parallel processing support
    - Progress callbacks
    - Memory usage monitoring
    - Node creation caching
    """

    def __init__(
        self,
        doc: DoclingDocument,
        params: Optional[OptimizedLexicalParams] = None,
        image_serializer: Optional[ComponentSerializer] = None,
        table_serializer: Optional[ComponentSerializer] = None,
        performance_config: Optional[PerformanceConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize optimized serializer.

        Args:
            doc: The DoclingDocument to serialize
            params: Optional optimization parameters
            image_serializer: Optional custom image serializer
            table_serializer: Optional custom table serializer
            performance_config: Performance configuration
            **kwargs: Additional parameters
        """
        self.doc = doc
        self.params = params or OptimizedLexicalParams()
        self.image_serializer = image_serializer or ImageSerializer()
        self.table_serializer = table_serializer
        self.performance_config = performance_config or PerformanceConfig()
        
        # Select JSON encoder
        self._json_encoder = self._select_json_encoder()
        
        # Node creation cache
        self._node_cache: Dict[str, Any] = {} if self.params.cache_node_creation else None
        
        # Performance metrics
        self._elements_processed = 0
        self._start_time = 0.0
        
        logger.debug(f"OptimizedLexicalDocSerializer initialized with {self._json_encoder.__name__}")

    def serialize(self) -> SerializationResult:
        """Serialize DoclingDocument to Lexical JSON with optimizations.

        Returns:
            SerializationResult: The serialization result

        Raises:
            ValidationError: If document structure is invalid
            TransformationError: If conversion fails
            ConfigurationError: If parameters are invalid
        """
        self._start_time = time.time()
        logger.info("Starting optimized Lexical JSON serialization")

        try:
            # Validate input if not skipped
            if not self.params.skip_validation:
                validate_docling_document(self.doc)
                logger.debug("Document validation passed")

            # Validate serializer parameters
            self._validate_serializer_params()

            # Determine processing strategy
            total_elements = self._count_total_elements()
            use_streaming = (
                self.params.enable_streaming or 
                total_elements > STREAMING_THRESHOLD_ELEMENTS
            )
            
            logger.debug(f"Processing {total_elements} elements, streaming: {use_streaming}")
            
            # Initialize progress tracking
            if self.params.progress_callback:
                self.params.progress_callback(0.0)

            # Choose serialization method based on strategy
            if use_streaming:
                json_text = self._serialize_streaming()
            elif self.params.parallel_processing and total_elements > 1000:
                json_text = self._serialize_parallel()
            else:
                json_text = self._serialize_optimized()

            # Log performance metrics
            duration = (time.time() - self._start_time) * 1000
            perf_logger.log_operation_time(
                "optimized_lexical_serialization",
                duration,
                {
                    "elements_processed": self._elements_processed,
                    "output_size_chars": len(json_text),
                    "streaming": use_streaming,
                    "parallel": self.params.parallel_processing,
                    "json_encoder": self._json_encoder.__name__
                }
            )
            
            logger.info(f"Optimized serialization complete: {duration:.2f}ms, {len(json_text)} chars")
            
            # Final progress update
            if self.params.progress_callback:
                self.params.progress_callback(1.0)

            return SerializationResult(text=json_text)

        except (ValidationError, TransformationError, ConfigurationError):
            # Re-raise custom exceptions
            duration = (time.time() - self._start_time) * 1000
            logger.error(f"Optimized serialization failed after {duration:.2f}ms")
            raise
        except Exception as e:
            # Handle unexpected errors
            duration = (time.time() - self._start_time) * 1000
            context = {
                "operation": "optimized_serialize",
                "duration_ms": duration,
                "elements_processed": self._elements_processed
            }
            log_exception_with_context(logger, e, "Optimized Lexical serialization", context)
            
            raise TransformationError(
                f"Unexpected error during optimized serialization: {e}",
                transformation_type="optimized_lexical",
                context=context,
                cause=e
            ) from e

    def _serialize_streaming(self) -> str:
        """Serialize using streaming approach for large documents."""
        logger.debug("Using streaming serialization")
        
        try:
            # Build root structure
            root_data = self._build_root_structure_streaming()
            
            # Serialize to JSON with streaming
            return self._encode_json_streaming(root_data)
            
        except Exception as e:
            raise TransformationError(
                f"Streaming serialization failed: {e}",
                transformation_type="streaming_lexical",
                context={"elements_processed": self._elements_processed},
                cause=e
            ) from e

    def _serialize_parallel(self) -> str:
        """Serialize using parallel processing for large documents."""
        logger.debug("Using parallel serialization")
        
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            # Split body children into chunks
            chunks = self._split_body_children_into_chunks()
            
            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=self.params.max_workers) as executor:
                futures = [
                    executor.submit(self._process_body_children_chunk, chunk)
                    for chunk in chunks
                ]
                
                lexical_children = []
                for future in as_completed(futures):
                    chunk_result = future.result()
                    lexical_children.extend(chunk_result)
            
            # Update progress
            if self.params.progress_callback:
                self.params.progress_callback(0.8)
            
            # Build final structure
            lexical_data = self._build_final_structure(lexical_children)
            
            # Serialize to JSON
            return self._encode_json(lexical_data)
            
        except Exception as e:
            raise TransformationError(
                f"Parallel serialization failed: {e}",
                transformation_type="parallel_lexical",
                context={"elements_processed": self._elements_processed},
                cause=e
            ) from e

    def _serialize_optimized(self) -> str:
        """Serialize using optimized standard approach."""
        logger.debug("Using optimized standard serialization")
        
        try:
            # Process body children with optimizations
            lexical_children = self._process_body_children_optimized()
            
            # Update progress
            if self.params.progress_callback:
                self.params.progress_callback(0.8)
            
            # Build final structure
            lexical_data = self._build_final_structure(lexical_children)
            
            # Serialize to JSON
            return self._encode_json(lexical_data)
            
        except Exception as e:
            raise TransformationError(
                f"Optimized serialization failed: {e}",
                transformation_type="optimized_lexical",
                context={"elements_processed": self._elements_processed},
                cause=e
            ) from e

    def _build_root_structure_streaming(self) -> Dict[str, Any]:
        """Build root structure using streaming approach."""
        # Process children in batches
        children_generator = self._process_body_children_generator()
        lexical_children = list(children_generator)
        
        return self._build_final_structure(lexical_children)

    def _process_body_children_generator(self) -> Generator[Dict[str, Any], None, None]:
        """Generator that yields processed body children."""
        batch = []
        batch_count = 0
        
        for i, child_ref in enumerate(self.doc.body.children):
            try:
                if not child_ref.cref:
                    continue

                lexical_node = self._process_single_child_ref(child_ref)
                if lexical_node:
                    batch.append(lexical_node)
                    batch_count += 1
                    self._elements_processed += 1

                # Process batch when full
                if batch_count >= self.params.batch_size:
                    for node in batch:
                        yield node
                    batch.clear()
                    batch_count = 0
                    
                    # Update progress
                    if self.params.progress_callback:
                        progress = min(0.7, i / len(self.doc.body.children) * 0.7)
                        self.params.progress_callback(progress)
                    
                    # Force garbage collection for memory management
                    if self.params.memory_efficient_mode:
                        gc.collect()

            except Exception as e:
                logger.warning(f"Failed to process child ref {i}: {e}")
                continue

        # Yield remaining items
        for node in batch:
            yield node

    def _process_body_children_optimized(self) -> List[Dict[str, Any]]:
        """Process body children with standard optimizations."""
        lexical_nodes = []
        
        for i, child_ref in enumerate(self.doc.body.children):
            try:
                if not child_ref.cref:
                    continue

                lexical_node = self._process_single_child_ref(child_ref)
                if lexical_node:
                    lexical_nodes.append(lexical_node)
                    self._elements_processed += 1

                # Update progress periodically
                if self.params.progress_callback and i % 100 == 0:
                    progress = min(0.7, i / len(self.doc.body.children) * 0.7)
                    self.params.progress_callback(progress)

                # Memory management for large documents
                if self.params.memory_efficient_mode and i % self.params.batch_size == 0:
                    gc.collect()

            except Exception as e:
                logger.warning(f"Failed to process child ref {i}: {e}")
                continue

        return lexical_nodes

    def _split_body_children_into_chunks(self) -> List[List]:
        """Split body children into chunks for parallel processing."""
        children = self.doc.body.children
        chunk_size = max(1, len(children) // self.params.max_workers)
        
        chunks = []
        for i in range(0, len(children), chunk_size):
            chunk = children[i:i + chunk_size]
            chunks.append(chunk)
        
        logger.debug(f"Split {len(children)} children into {len(chunks)} chunks")
        return chunks

    def _process_body_children_chunk(self, children_chunk: List) -> List[Dict[str, Any]]:
        """Process a chunk of body children."""
        lexical_nodes = []
        
        for child_ref in children_chunk:
            try:
                if not child_ref.cref:
                    continue

                lexical_node = self._process_single_child_ref(child_ref)
                if lexical_node:
                    lexical_nodes.append(lexical_node)
                    self._elements_processed += 1

            except Exception as e:
                logger.warning(f"Failed to process child ref in chunk: {e}")
                continue

        return lexical_nodes

    def _process_single_child_ref(self, child_ref) -> Optional[Dict[str, Any]]:
        """Process a single child reference optimally."""
        # Parse reference
        ref_parts = child_ref.cref.split("/")
        if len(ref_parts) < MIN_REF_PARTS:
            return None

        element_type = ref_parts[REF_ELEMENT_TYPE_INDEX]

        # Parse element index with error handling
        try:
            element_index = int(ref_parts[REF_ELEMENT_INDEX])
        except ValueError:
            return None

        # Process based on element type with bounds checking
        if element_type == ELEMENT_TYPE_TEXTS:
            if element_index >= len(self.doc.texts):
                return None
            text_item = self.doc.texts[element_index]
            return self._create_text_node_optimized(text_item)

        elif element_type == ELEMENT_TYPE_TABLES:
            if element_index >= len(self.doc.tables):
                return None
            table_item = self.doc.tables[element_index]
            if self.table_serializer:
                return self.table_serializer.serialize(table_item, self.params)
            else:
                return self._create_table_node_optimized(table_item)

        elif element_type == ELEMENT_TYPE_GROUPS:
            if element_index >= len(self.doc.groups):
                return None
            group_item = self.doc.groups[element_index]
            return self._create_group_node_optimized(group_item)

        elif element_type == ELEMENT_TYPE_PICTURES:
            if hasattr(self.doc, "pictures") and element_index < len(self.doc.pictures):
                picture_item = self.doc.pictures[element_index]
                return self.image_serializer.serialize(picture_item, self.params)

        return None

    def _create_text_node_optimized(self, text_item: TextItemType) -> Optional[Dict[str, Any]]:
        """Create optimized text node."""
        if text_item.label == "section_header":
            return self._create_heading_node_optimized(text_item)
        else:
            return self._create_paragraph_node_optimized(text_item)

    def _create_heading_node_optimized(self, text_item: SectionHeaderItem) -> Dict[str, Any]:
        """Create optimized heading node."""
        # Check cache first
        if self._node_cache is not None:
            cache_key = f"heading_{text_item.text}_{getattr(text_item, 'level', 1)}"
            if cache_key in self._node_cache:
                return self._node_cache[cache_key].copy()

        try:
            level = getattr(text_item, "level", MIN_HEADING_LEVEL)
            tag = f"h{min(max(level, MIN_HEADING_LEVEL), MAX_HEADING_LEVEL)}"
            text_content = getattr(text_item, "text", "") or ""

            # Optimized text processing
            if self.params.optimize_text_formatting:
                format_types = self._detect_text_formatting_fast(text_content, text_item)
            else:
                format_types = []

            text_node = self._create_formatted_text_node_optimized(text_content, format_types)

            node = {
                "children": [text_node],
                "direction": TEXT_DIRECTION_LTR,
                "format": DEFAULT_STYLE,
                "indent": DEFAULT_INDENT,
                "tag": tag,
                "type": NODE_TYPE_HEADING,
                "version": self.params.version,
            }

            # Cache result
            if self._node_cache is not None:
                cache_key = f"heading_{text_item.text}_{level}"
                self._node_cache[cache_key] = node.copy()

            return node

        except (AttributeError, TypeError):
            # Return default heading for malformed items
            return self._create_default_heading_node()

    def _create_paragraph_node_optimized(self, text_item: TextItem) -> Dict[str, Any]:
        """Create optimized paragraph node."""
        text_content = getattr(text_item, "text", "") or ""

        # Optimized link processing
        if self.params.optimize_text_formatting:
            children = self._process_text_with_links_fast(text_content, text_item)
        else:
            children = [self._create_formatted_text_node_optimized(text_content, [])]

        return {
            "children": children,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_PARAGRAPH,
            "version": self.params.version,
        }

    def _create_table_node_optimized(self, table_item: TableItem) -> Dict[str, Any]:
        """Create optimized table node."""
        rows: List[Dict[str, Any]] = []

        try:
            if table_item.data and table_item.data.grid:
                for row in table_item.data.grid:
                    try:
                        lexical_row = {
                            "children": [],
                            "direction": TEXT_DIRECTION_LTR,
                            "format": DEFAULT_STYLE,
                            "indent": DEFAULT_INDENT,
                            "type": NODE_TYPE_TABLE_ROW,
                            "version": self.params.version,
                        }

                        # Process cells in batch
                        cells = []
                        for cell in row:
                            try:
                                cell_text = getattr(cell, "text", "") or ""
                                lexical_cell = {
                                    "children": [
                                        self._create_formatted_text_node_optimized(cell_text, [])
                                    ],
                                    "direction": TEXT_DIRECTION_LTR,
                                    "format": DEFAULT_STYLE,
                                    "indent": DEFAULT_INDENT,
                                    "type": NODE_TYPE_TABLE_CELL,
                                    "version": self.params.version,
                                }

                                # Add header state efficiently
                                if hasattr(cell, "column_header") and cell.column_header:
                                    lexical_cell["headerState"] = HEADER_STATE_VALUE

                                cells.append(lexical_cell)
                            except (AttributeError, TypeError):
                                continue

                        lexical_row["children"] = cells
                        if cells:  # Only add rows with cells
                            rows.append(lexical_row)

                    except (AttributeError, TypeError):
                        continue

        except (AttributeError, TypeError):
            pass

        # Calculate dimensions efficiently
        num_rows = len(rows)
        num_cols = len(rows[0]["children"]) if rows else 0

        return {
            "children": rows,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_TABLE,
            "version": self.params.version,
            "rows": num_rows,
            "columns": num_cols,
        }

    def _create_group_node_optimized(self, group_item: GroupItemType) -> Dict[str, Any]:
        """Create optimized group/list node."""
        # Determine list type efficiently
        list_type = LIST_TYPE_UNORDERED
        try:
            if group_item.children and group_item.children[0].cref and "texts" in group_item.children[0].cref:
                ref_parts = group_item.children[0].cref.split("/")
                if len(ref_parts) >= 3 and ref_parts[1] == "texts":
                    try:
                        text_index = int(ref_parts[2])
                        if text_index < len(self.doc.texts):
                            first_text = getattr(self.doc.texts[text_index], "text", "") or ""
                            if first_text and ". " in first_text:
                                prefix = first_text.split(". ", 1)[0].strip()
                                if prefix.isdigit():
                                    list_type = LIST_TYPE_ORDERED
                    except (ValueError, IndexError, AttributeError):
                        pass
        except (AttributeError, TypeError):
            pass

        tag = LIST_TAG_ORDERED if list_type == LIST_TYPE_ORDERED else LIST_TAG_UNORDERED
        list_items = []

        # Process list items in batch
        for child_ref in group_item.children:
            try:
                if not child_ref.cref:
                    continue

                ref_parts = child_ref.cref.split("/")
                if len(ref_parts) >= 3 and ref_parts[1] == "texts":
                    text_index = int(ref_parts[2])
                    if text_index < len(self.doc.texts):
                        text_item = self.doc.texts[text_index]
                        text_content = text_item.text

                        # Remove list markers efficiently
                        if text_content.startswith("● "):
                            text_content = text_content[2:]
                        elif text_content.startswith("• "):
                            text_content = text_content[2:]
                        elif ". " in text_content:
                            parts = text_content.split(". ", 1)
                            if parts[0].isdigit():
                                text_content = parts[1]

                        # Process text optimally
                        if self.params.optimize_text_formatting:
                            children = self._process_text_with_links_fast(text_content, text_item)
                        else:
                            children = [self._create_formatted_text_node_optimized(text_content, [])]

                        list_item = {
                            "children": children,
                            "direction": TEXT_DIRECTION_LTR,
                            "format": DEFAULT_STYLE,
                            "indent": DEFAULT_INDENT,
                            "type": NODE_TYPE_LIST_ITEM,
                            "value": 1,
                            "version": self.params.version,
                        }

                        list_items.append(list_item)
            except (ValueError, IndexError, AttributeError):
                continue

        return {
            "children": list_items,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "listType": list_type,
            "start": 1,
            "tag": tag,
            "type": NODE_TYPE_LIST,
            "version": self.params.version,
        }

    def _detect_text_formatting_fast(self, text_content: str, text_item: Optional[TextItemType] = None) -> List[str]:
        """Fast text formatting detection with minimal overhead."""
        format_types = []
        
        if not text_content or not self.params.preserve_formatting:
            return format_types

        # Quick heuristic checks (faster than detailed analysis)
        lower_text = text_content.lower()
        
        if (text_content.isupper() or 
            "important" in lower_text or 
            text_content.startswith("**")):
            format_types.append("bold")
        elif ("italic" in lower_text or 
              text_content.startswith("*")):
            format_types.append("italic")

        return format_types

    def _process_text_with_links_fast(self, text_content: str, text_item: Optional[TextItemType] = None) -> List[Dict[str, Any]]:
        """Fast link processing with minimal regex overhead."""
        # Quick check for URLs to avoid regex if not needed
        if "http" not in text_content and "www." not in text_content:
            format_types = self._detect_text_formatting_fast(text_content, text_item)
            return [self._create_formatted_text_node_optimized(text_content, format_types)]

        # Use simplified URL detection
        import re
        url_pattern = r'https?://\S+|www\.\S+'
        urls = list(re.finditer(url_pattern, text_content))

        if not urls:
            format_types = self._detect_text_formatting_fast(text_content, text_item)
            return [self._create_formatted_text_node_optimized(text_content, format_types)]

        # Process URLs (simplified version of original logic)
        nodes = []
        last_end = 0

        for url_match in urls:
            # Add text before URL
            if url_match.start() > last_end:
                before_text = text_content[last_end:url_match.start()]
                if before_text.strip():
                    format_types = self._detect_text_formatting_fast(before_text, text_item)
                    nodes.append(self._create_formatted_text_node_optimized(before_text, format_types))

            # Add link node
            url = url_match.group()
            if not url.startswith('http'):
                url = 'https://' + url
            nodes.append(self._create_link_node_optimized(url_match.group(), url))
            last_end = url_match.end()

        # Add remaining text
        if last_end < len(text_content):
            after_text = text_content[last_end:]
            if after_text.strip():
                format_types = self._detect_text_formatting_fast(after_text, text_item)
                nodes.append(self._create_formatted_text_node_optimized(after_text, format_types))

        return nodes

    def _create_formatted_text_node_optimized(self, text_content: str, format_types: List[str]) -> Dict[str, Any]:
        """Create optimized formatted text node."""
        # Calculate format bitmask efficiently
        format_value = 0
        for fmt in format_types:
            if fmt == "bold":
                format_value |= FORMAT_BOLD
            elif fmt == "italic":
                format_value |= FORMAT_ITALIC
            elif fmt == "underline":
                format_value |= FORMAT_UNDERLINE
            elif fmt == "strikethrough":
                format_value |= FORMAT_STRIKETHROUGH

        return {
            "detail": DEFAULT_DETAIL,
            "format": format_value,
            "mode": DEFAULT_MODE,
            "style": DEFAULT_STYLE,
            "text": text_content,
            "type": NODE_TYPE_TEXT,
            "version": self.params.version,
        }

    def _create_link_node_optimized(self, text_content: str, url: str) -> Dict[str, Any]:
        """Create optimized link node."""
        return {
            "children": [
                {
                    "detail": DEFAULT_DETAIL,
                    "format": DEFAULT_FORMAT,
                    "mode": DEFAULT_MODE,
                    "style": DEFAULT_STYLE,
                    "text": text_content,
                    "type": NODE_TYPE_TEXT,
                    "version": self.params.version,
                }
            ],
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_LINK,
            "url": url,
            "version": self.params.version,
        }

    def _create_default_heading_node(self) -> Dict[str, Any]:
        """Create default heading node for error cases."""
        return {
            "children": [self._create_formatted_text_node_optimized("", [])],
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "tag": DEFAULT_HEADING_TAG,
            "type": NODE_TYPE_HEADING,
            "version": self.params.version,
        }

    def _build_final_structure(self, lexical_children: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build final Lexical structure with metadata."""
        root_node = {
            "children": lexical_children,
            "direction": TEXT_DIRECTION_LTR,
            "format": DEFAULT_STYLE,
            "indent": DEFAULT_INDENT,
            "type": NODE_TYPE_ROOT,
            "version": self.params.version,
        }

        # Add custom root attributes
        if self.params.custom_root_attributes:
            try:
                root_node.update(self.params.custom_root_attributes)
            except Exception as e:
                logger.warning(f"Failed to add custom root attributes: {e}")

        lexical_data = {"root": root_node}

        # Add metadata efficiently
        if self.params.include_metadata:
            try:
                metadata = {}
                if hasattr(self.doc, "name") and self.doc.name:
                    metadata["document_name"] = self.doc.name
                    metadata["version"] = getattr(self.doc, "version", "1.0.0")

                # Handle origin efficiently
                if hasattr(self.doc, "origin") and self.doc.origin:
                    origin = self.doc.origin
                    metadata["origin"] = {
                        "mimetype": getattr(origin, "mimetype", ""),
                        "filename": getattr(origin, "filename", ""),
                        "binary_hash": getattr(origin, "binary_hash", 0),
                        "uri": getattr(origin, "uri", None),
                    }

                if metadata:
                    lexical_data["metadata"] = metadata

            except Exception as e:
                logger.warning(f"Failed to include metadata: {e}")

        return lexical_data

    def _select_json_encoder(self):
        """Select fastest available JSON encoder."""
        if not self.params.use_fast_json:
            return json

        # Try fast JSON libraries
        try:
            import orjson
            logger.debug("Using orjson for JSON encoding")
            return orjson
        except ImportError:
            pass

        try:
            import ujson
            logger.debug("Using ujson for JSON encoding")
            return ujson
        except ImportError:
            pass

        logger.debug("Using standard json library")
        return json

    def _encode_json(self, data: Dict[str, Any]) -> str:
        """Encode data to JSON using selected encoder."""
        try:
            if self._json_encoder == json:
                # Standard library json
                indent = JSON_INDENT_SIZE if self.params.indent_json else None
                return json.dumps(data, indent=indent, ensure_ascii=False)
            
            elif hasattr(self._json_encoder, '__name__') and self._json_encoder.__name__ == 'orjson':
                # orjson
                options = 0
                if self.params.indent_json:
                    options |= self._json_encoder.OPT_INDENT_2
                return self._json_encoder.dumps(data, option=options).decode('utf-8')
            
            elif hasattr(self._json_encoder, 'dumps'):
                # ujson and other libraries
                try:
                    if self.params.indent_json:
                        # Try with all parameters
                        return self._json_encoder.dumps(data, indent=JSON_INDENT_SIZE, ensure_ascii=False)
                    else:
                        return self._json_encoder.dumps(data, ensure_ascii=False)
                except TypeError:
                    # Fallback if ensure_ascii not supported
                    if self.params.indent_json:
                        return self._json_encoder.dumps(data, indent=JSON_INDENT_SIZE)
                    else:
                        return self._json_encoder.dumps(data)
            
            else:
                # Ultimate fallback to standard json
                indent = JSON_INDENT_SIZE if self.params.indent_json else None
                return json.dumps(data, indent=indent, ensure_ascii=False)
                
        except Exception as e:
            raise TransformationError(
                f"JSON encoding failed: {e}",
                transformation_type="json_encoding",
                cause=e
            ) from e

    def _encode_json_streaming(self, data: Dict[str, Any]) -> str:
        """Encode JSON using streaming approach for large data."""
        try:
            # Use fast encoder with memory-efficient approach
            return self._encode_json(data)
        except Exception as e:
            raise TransformationError(
                f"Streaming JSON encoding failed: {e}",
                transformation_type="streaming_json_encoding",
                cause=e
            ) from e

    def _count_total_elements(self) -> int:
        """Count total elements in document for strategy selection."""
        return (
            len(self.doc.body.children) +
            len(self.doc.texts) +
            len(getattr(self.doc, 'tables', [])) +
            len(getattr(self.doc, 'groups', [])) +
            len(getattr(self.doc, 'pictures', []))
        )

    def _validate_serializer_params(self) -> None:
        """Validate optimized serializer parameters."""
        if not isinstance(self.params, OptimizedLexicalParams):
            raise ConfigurationError(
                f"Invalid parameters: expected OptimizedLexicalParams, got {type(self.params).__name__}",
                context={"actual_type": type(self.params).__name__}
            )

        # Validate batch size
        if self.params.batch_size <= 0:
            raise ConfigurationError(
                f"Invalid batch_size: {self.params.batch_size}. Must be positive.",
                invalid_parameters=["batch_size"]
            )

        # Validate worker count
        if self.params.max_workers <= 0:
            raise ConfigurationError(
                f"Invalid max_workers: {self.params.max_workers}. Must be positive.",
                invalid_parameters=["max_workers"]
            )

        logger.debug("Optimized serializer parameters validated successfully")

    @contextmanager
    def performance_monitoring(self, operation_name: str = "optimized_serialization"):
        """Context manager for performance monitoring."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - start_memory
            
            perf_logger.log_operation_time(
                operation_name,
                duration_ms,
                {
                    "elements_processed": self._elements_processed,
                    "memory_delta_mb": memory_delta,
                    "json_encoder": self._json_encoder.__name__,
                    "streaming": self.params.enable_streaming,
                    "parallel": self.params.parallel_processing,
                    "batch_size": self.params.batch_size
                }
            )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        duration = (time.time() - self._start_time) * 1000 if self._start_time > 0 else 0
        
        return {
            "elements_processed": self._elements_processed,
            "duration_ms": duration,
            "elements_per_second": (self._elements_processed / (duration / 1000)) if duration > 0 else 0,
            "json_encoder": self._json_encoder.__name__,
            "cache_size": len(self._node_cache) if self._node_cache else 0,
            "configuration": {
                "streaming": self.params.enable_streaming,
                "parallel": self.params.parallel_processing,
                "batch_size": self.params.batch_size,
                "memory_efficient": self.params.memory_efficient_mode
            }
        }