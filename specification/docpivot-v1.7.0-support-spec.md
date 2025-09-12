# Feature Specification: DoclingDocument v1.7.0 Support in docpivot

## Executive Summary
Add support for DoclingDocument version 1.7.0 to docpivot, ensuring backward compatibility with existing versions (1.2.0, 1.3.0, 1.4.0) while properly handling structural changes in the new format that are causing text segment corruption during masking operations.

## Problem Statement
When processing DoclingDocument v1.7.0 files, the cloakpivot masking engine corrupts the document structure:
- 22 text segments collapse into 1 malformed segment
- Masking positions are miscalculated, creating overlapping placeholders like `[N[NAME]DA[EMAIL]E]`
- Provenance information (bounding boxes, page positions) is lost
- Document size reduces by 47% (abnormal for masking operation)

## Current Failure Mode
```
WARNING - docpivot.validation - DoclingDocument version '1.7.0' is not in supported versions {'1.4.0', '1.2.0', '1.3.0'}
```
Despite the warning, processing continues and produces corrupted output.

## Technical Analysis

### Key Structural Elements in v1.7.0

#### 1. Text Segments Structure (Appears Unchanged)
```json
{
  "text": "actual text content",
  "prov": [{
    "page_no": 1,
    "bbox": {"l": 72.0, "t": 717.556, "r": 254.57, "b": 707.839, "coord_origin": "BOTTOMLEFT"},
    "charspan": [0, 39]  // Local to this segment, not global
  }],
  "orig": "original text",
  "self_ref": "#/texts/0",
  "children": [],
  "parent": null,
  "content_layer": "default",
  "label": "text"
}
```

#### 2. Critical Observation: Charspan is Segment-Local
- Each text segment has `charspan` starting at 0
- This is **NOT** a global document offset
- v1.7.0 appears to use segment-local offsets consistently

#### 3. Pages Structure Change
- **v1.7.0**: Pages stored as object with string keys `{"1": {...}, "2": {...}}`
- **Earlier**: Likely stored as array `[{...}, {...}]`

#### 4. Tables Structure
Tables contain:
- `data`: Cell content array
- `prov`: Provenance information
- `annotations`, `captions`, `footnotes`, `references`: Additional metadata
- No `grid` field with structured cell data (or it's null)

## Required Changes in docpivot

### 1. Version Detection and Validation
**File**: `docpivot/validation.py` (or equivalent)
```python
SUPPORTED_VERSIONS = {'1.2.0', '1.3.0', '1.4.0', '1.7.0'}  # Add 1.7.0

# Add version-specific handling logic
def get_version_handler(version: str):
    if version in ['1.2.0', '1.3.0', '1.4.0']:
        return LegacyDoclingHandler()
    elif version == '1.7.0':
        return V17DoclingHandler()
    else:
        logger.warning(f"Unknown version {version}, attempting v1.7.0 handler")
        return V17DoclingHandler()
```

### 2. Text Extraction Fix
**File**: `cloakpivot/text_extractor.py` or similar
**Problem**: Current code likely assumes charspan provides global document offsets
**Solution**: Calculate global offsets by accumulating segment positions

```python
def extract_text_segments_v17(self, document):
    segments = []
    global_offset = 0
    
    for idx, text_item in enumerate(document.texts):
        segment_text = text_item.get('text', '')
        
        # Create segment with GLOBAL offsets
        segment = TextSegment(
            text=segment_text,
            start_offset=global_offset,  # Global position
            end_offset=global_offset + len(segment_text),
            segment_index=idx,
            provenance=text_item.get('prov', [])
        )
        segments.append(segment)
        
        # Update global offset for next segment
        global_offset += len(segment_text)
        # Add separator if segments are meant to be joined
        if idx < len(document.texts) - 1:
            global_offset += 1  # Account for space/newline between segments
    
    return segments
```

### 3. Masking Engine Offset Calculation
**File**: `cloakpivot/masking_engine.py` or similar
**Problem**: Entity positions from Presidio are global, but applied to local segments
**Solution**: Correctly map global positions back to segments

```python
def apply_masks_v17(self, document, entities, segments):
    # Build segment offset map
    segment_map = []
    current_pos = 0
    for seg in segments:
        segment_map.append({
            'start': current_pos,
            'end': current_pos + len(seg.text),
            'segment': seg
        })
        current_pos = segment_map[-1]['end'] + 1  # +1 for separator
    
    # Group entities by segment
    for entity in entities:
        segment_idx = find_segment_for_position(entity.start, segment_map)
        if segment_idx is not None:
            # Convert global position to segment-local position
            local_start = entity.start - segment_map[segment_idx]['start']
            local_end = entity.end - segment_map[segment_idx]['start']
            apply_mask_to_segment(segment_idx, local_start, local_end, mask_text)
```

### 4. Document Reconstruction
**File**: `cloakpivot/document_builder.py` or similar
**Problem**: Masked segments not properly reconstructed into document structure
**Solution**: Preserve all metadata during reconstruction

```python
def rebuild_document_v17(self, original_doc, masked_segments):
    masked_doc = copy.deepcopy(original_doc)
    
    # Preserve the texts array structure
    for idx, segment in enumerate(masked_segments):
        if idx < len(masked_doc['texts']):
            # Update only the text content, preserve all metadata
            masked_doc['texts'][idx]['text'] = segment.masked_text
            # Update prov charspan if text length changed
            if masked_doc['texts'][idx].get('prov'):
                masked_doc['texts'][idx]['prov'][0]['charspan'] = [0, len(segment.masked_text)]
    
    return masked_doc
```

### 5. Pages Object Handling
**File**: `docpivot/io/readers/doclingjsonreader.py`
```python
def parse_pages(self, pages_data):
    if isinstance(pages_data, dict):
        # v1.7.0 format: object with string keys
        return {int(k): v for k, v in pages_data.items()}
    elif isinstance(pages_data, list):
        # Legacy format: array
        return {i+1: page for i, page in enumerate(pages_data)}
```

## Testing Requirements

### Test Case 1: Segment Boundary Preservation
```python
def test_v17_segment_boundaries():
    doc = load_v17_document("test_email.docling.json")
    segments = extractor.extract_text_segments(doc)
    
    assert len(segments) == 22  # All segments preserved
    assert segments[0].text == "---------- Forwarded message ----------"
    assert segments[1].text == "From: Cameron MacIntyre <cameron@example.com>"
    
    # Verify global offsets
    full_text = extractor.extract_full_text(doc)
    for seg in segments:
        assert full_text[seg.start_offset:seg.end_offset] == seg.text
```

### Test Case 2: Masking Position Accuracy
```python
def test_v17_masking_positions():
    # Mask "cameron@example.com" in second segment
    entities = [RecognizerResult(
        entity_type="EMAIL",
        start=65,  # Global position
        end=84,
        score=1.0
    )]
    
    result = masking_engine.mask_document(doc, entities, policy)
    masked_texts = result.masked_document['texts']
    
    assert masked_texts[1]['text'] == "From: Cameron MacIntyre <[EMAIL]>"
    assert len(masked_texts) == 22  # No segment collapse
```

### Test Case 3: Provenance Preservation
```python
def test_v17_provenance_preserved():
    result = masking_engine.mask_document(doc, entities, policy)
    
    for original, masked in zip(doc['texts'], result.masked_document['texts']):
        assert masked.get('prov') is not None
        assert masked['prov'][0]['page_no'] == original['prov'][0]['page_no']
        assert masked['prov'][0]['bbox'] == original['prov'][0]['bbox']
```

## Implementation Priority

1. **Critical** - Fix text segment offset calculation (prevents corruption)
2. **Critical** - Fix masking position mapping (ensures correct redaction)
3. **High** - Add v1.7.0 to supported versions
4. **High** - Preserve document structure during reconstruction
5. **Medium** - Handle pages object vs array format
6. **Low** - Add comprehensive v1.7.0 test suite

## Success Criteria

1. ✅ No warning about unsupported version when processing v1.7.0
2. ✅ All 22 text segments preserved after masking (not collapsed to 1)
3. ✅ Masked text shows `[EMAIL]`, `[NAME]`, etc. at correct positions
4. ✅ No overlapping or malformed masks like `[N[NAME]DA[EMAIL]E]`
5. ✅ Document size remains ~17KB (not reduced to 9KB)
6. ✅ Provenance information retained in masked document
7. ✅ Backward compatibility maintained for v1.2.0, v1.3.0, v1.4.0

## Configuration Considerations

Consider adding a version-specific configuration:
```python
VERSION_CONFIGS = {
    '1.7.0': {
        'segment_separator': '\n',  # How to join segments for full text
        'charspan_type': 'local',   # 'local' vs 'global' offsets
        'pages_format': 'object',   # 'object' vs 'array'
        'preserve_empty_segments': True
    }
}
```

## Notes for Implementation

- The core issue is **offset calculation** - v1.7.0 uses segment-local charspans, not global
- TextExtractor must track global positions when building segments
- MaskingEngine must map global entity positions back to segment-local coordinates
- Document reconstruction must preserve the original structure exactly
- Consider adding debug logging for offset calculations to aid troubleshooting

## Questions to Resolve During Implementation

1. Should segments be joined with `\n`, space, or no separator for full text extraction?
2. How should empty segments be handled during masking?
3. Should we auto-detect version if not specified in the document?
4. What's the behavior if a mask spans multiple segments?

This specification provides the complete context and technical details needed to implement v1.7.0 support. The key insight is that the charspan offsets are segment-local, not global, which is causing the position calculation errors during masking.