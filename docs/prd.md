Instructions: Write a python package called `docpivot` for converting rich text documents to/from a variety of input and output file formats. Intelligently detect input format. Leverage design patterns, APIs, function names, etc. from Docling. 

Following are specifications on how the package should be built and designed. 

# DocPivot

*What is it?*

Docpivot is a lightweight bridge between [Docling](https://docling.io/) and other text‑centric formats that are not natively supported by Docling out of the box. Such formats include other Json dialects besides Docling Json (e.g. Lexical Json), other flavors or dialects of Markdown or Yaml that Docling doesn't support natively, etc.

DocPivot is a mini‑SDK that makes it trivial to **load**, **transform**, and
**serialize** rich‑text documents that originate in any of the natively supported document types that Docling can handle out of the box as well as other rich-text data formats that Docling does not natively support. 

Because Docling has is an impressively powerful toolset with wildly simple to use APIs, Docpivot aims to extend Docling rather than replicate its functionality. For instance, Docpivot will, to the maximum extent, adopt and use Docling's abstractions, patterns, classes and subclasses, function and method names, etc. rather than rewriting or crafting entirely distinct implementation approaches. 

## Background 

### Key Docling Concepts, Abstractions, and Design Patterns

Docling can parse various documents formats into a unified representation (Docling Document).

#### Docling Input formats

Docling can read, parse, and load files from a variety of input filetypes, including: PDF, DOCX, XLSX, PPTX, Markdown, AsciiDoc, HTML, XHTML, CSV, PNG, JPG, TIFF, BMP, WEBP. Input files are converted by Docling into Docling Documents. 

#### Docling Output formats

A Docling Document can be exported natively by Docling into a variety of output filetypes, including: HTML, Markdown, JSON, Text, Doctags. 

#### Docling Limitations and Docpivot's goals to extend Docling's IO capabilities

While Docling supports Markdown and Json, it is important to note that there are many flavors and dialects of both Markdown and Json. Docling's native support for exporting to each is limited to only one flavor or dialect. In the case of Json, Docling's `export_to_dict()` method is used to "serialize" (i.e. export a DoclingDocument to some export format, in this case Docling flavored Json). 

Similarly, Docling's `export_to_markdown()` method is handy and powerful. But it does not export to valid Lexical Json suitable for use with React's browser based rich text editor, Lexical. 


##### Docling Serializers

A document serializer (AKA simply serializer) is a Docling abstraction that is initialized with a given DoclingDocument and returns a textual representation for that document.

Besides the document serializer, Docling defines similar abstractions for several document subcomponents, for example: text serializer, table serializer, picture serializer, list serializer, inline serializer, and more.

Last but not least, a serializer provider is a wrapper that abstracts the document serialization strategy from the document instance.

To enable both flexibility for downstream applications and out-of-the-box utility, Docling defines a serialization class hierarchy, providing:

base types for the above abstractions: BaseDocSerializer, as well as BaseTextSerializer, BaseTableSerializer etc, and BaseSerializerProvider, and
specific subclasses for the above-mentioned base types, e.g. MarkdownDocSerializer.
You can review all methods required to define the above base classes here.

From a client perspective, the most relevant is BaseDocSerializer.serialize(), which returns the textual representation, as well as relevant metadata on which document components contributed to that serialization.


Use in DoclingDocument export methods
Docling provides predefined serializers for Markdown, HTML, and DocTags.

The respective DoclingDocument export methods (e.g. export_to_markdown()) are provided as user shorthands — internally directly instantiating and delegating to respective serializers.


*Creating a custom serializer*

Let's now assume we want to define a custom serialization logic, e.g. we would like picture serialization to include any available picture description (captioning) annotations.

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionVlmOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions(
    do_picture_description=True,
    picture_description_options=PictureDescriptionVlmOptions(
        repo_id="HuggingFaceTB/SmolVLM-256M-Instruct",
        prompt="Describe this picture in three to five sentences. Be precise and concise.",
    ),
    generate_picture_images=True,
    images_scale=2,
)

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
doc = converter.convert(source=DOC_SOURCE).document
```

We can then define our custom picture serializer:

```python
from typing import Any, Optional

from docling_core.transforms.serializer.base import (
    BaseDocSerializer,
    SerializationResult,
)
from docling_core.transforms.serializer.common import create_ser_result
from docling_core.transforms.serializer.markdown import (
    MarkdownParams,
    MarkdownPictureSerializer,
)
from docling_core.types.doc.document import (
    DoclingDocument,
    ImageRefMode,
    PictureDescriptionData,
    PictureItem,
)
from typing_extensions import override


class AnnotationPictureSerializer(MarkdownPictureSerializer):
    @override
    def serialize(
        self,
        *,
        item: PictureItem,
        doc_serializer: BaseDocSerializer,
        doc: DoclingDocument,
        separator: Optional[str] = None,
        **kwargs: Any,
    ) -> SerializationResult:
        text_parts: list[str] = []

        # reusing the existing result:
        parent_res = super().serialize(
            item=item,
            doc_serializer=doc_serializer,
            doc=doc,
            **kwargs,
        )
        text_parts.append(parent_res.text)

        # appending annotations:
        for annotation in item.annotations:
            if isinstance(annotation, PictureDescriptionData):
                text_parts.append(f"")

        text_res = (separator or "\n").join(text_parts)
        return create_ser_result(text=text_res, span_source=item)

```

Last but not least, we define a new doc serializer which leverages our custom picture serializer.



```python
serializer = MarkdownDocSerializer(
    doc=doc,
    picture_serializer=AnnotationPictureSerializer(),
    params=MarkdownParams(
        image_mode=ImageRefMode.PLACEHOLDER,
        image_placeholder="",
    ),
)
ser_result = serializer.serialize()
ser_text = ser_result.text

print_in_console(ser_text[ser_text.find(start_cue) : ser_text.find(stop_cue)])

```





### Extending Docling with Docpivot

Docpivot should wrap Docling’s powerful `DoclingDocument` model with:

| Capability                              | Module / Class                         | Status |
|-----------------------------------------|----------------------------------------|--------|
| Read *.docling.json* → `DoclingDocument`| `DoclingJsonReader`                    | ✅ Stable |
| Read *.lexical.json* → `DoclingDocument`| `LexicalJsonReader` → (converter stub) | 🚧 Planned |
| Serialize to **Markdown**               | `DocumentSerializer` (built‑in export) | ✅ |
| Serialize to **DocTags**                | `DocumentSerializer` (built‑in export) | ✅ |
| Serialize to **Lexical JSON**           | `LexicalDocSerializer`                 | ⚠️ Prototype (placeholder output) |


### Key Docpivot Concepts

| Term                              | Meaning                                                                               |
|-----------------------------------|---------------------------------------------------------------------------------------|
| DoclingDocument                   | Rich Python model (from docling‑core) that preserves hierarchy, styling, tables, etc. |
| Reader                            | Loads bytes → `DoclingDocument`. Inherits from `BaseReader`.                          |
| Serializer                        | Converts a DoclingDocument into another representation (string + optional spans).     |
| SerializerProvider                | Factory that hands you the right serializer for "markdown", "doctags" or "lexical".   |


## Desired End-user developer experience for Docpivot APIs

Below is the essence of what `example.py` does:

```python
from pathlib import Path
from docpivot.io.readers import DoclingJsonReader
from docpivot.io.serializers import MySerializerProvider

# 1) Load a Docling JSON file
doc = DoclingJsonReader().load_data("data/json/2025-07-03-Test-PDF-Styles.docling.json")

# 2) Serialize to Markdown
provider      = MySerializerProvider()
md_serializer = provider.get_serializer("markdown")
markdown_out  = md_serializer.serialize(doc).text

# 3) Write to disk
Path("my_doc.md").write_text(markdown_out, encoding="utf‑8")

```


### Handling Lexical JSON 


```python
from docpivot.io.readers import LexicalJsonReader
try:
    doc = LexicalJsonReader().load_data("path/to/file.lexical.json")
except NotImplementedError as e:
    print("⚠️  Converter not ready yet:", e)

```

### Extending DocPivot

Drop `my_fancy_reader.py` into `io/readers/` and import it where needed.


```python
from docpivot.io.readers.basereader import BaseReader
class MyFancyReader(BaseReader):
    def load_data(self, file_path, **kw):
        raw = ...            # read your custom format
        return DoclingDocument.model_validate(raw)


```


Or add a new serializer:

```python
from docling_core.transforms.serializer.base import SerializationResult
class HtmlSerializer:
    def serialize(self, doc, **kw):
        html = doc.export_to_html()   # hypothetical
        return SerializationResult(text=html, spans=[])

...

provider.register_serializer("html", HtmlSerializer)


```
